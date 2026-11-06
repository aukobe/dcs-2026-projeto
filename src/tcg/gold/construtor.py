"""Construtor da gold e Escritor da gold (T-32; RF-10, RF-22; ADR-003, ADR-004).

Uso: `make gold` (ou `python -m tcg.gold.construtor`, com as variáveis do
`.env` no ambiente).

1. Descoberta (somente leitura, pelo SDK): lista `silver/colecao/`,
   `silver/produto/` e `silver/preco_diario/` de todas as coleções e agrupa
   os Parquets pelo `group_id=<id>` do caminho.
2. Conferência do contrato por coleção: `DESCRIBE` de cada Parquet, com
   `hive_partitioning = false`, contra `CONTRATO` da silver. Colunas extras
   são permitidas (specs/spec.md, Contratos); coluna ausente, tipo diferente ou
   tabela faltando tiram a coleção da gold, com aviso no log (group_id e
   motivo). A silver da DRI (inclusive `cambio_diario` e `cdi_diario`) é
   obrigatória: ausente ou fora do contrato, a gold aborta.
3. Montagem: `montar_estrela` (T-30, T-31) só com os arquivos aprovados.
4. Escritor da gold: cada tabela vai para `gold/group_id=24269/<tabela>.parquet`
   por `gravar_parquet`, que passa pela Guarda de prefixo antes do `COPY`.
   Nenhum objeto de outra coleção é escrito; a gold sobrescreve as próprias
   chaves determinísticas e não apaga nada (ADR-004).

Códigos de saída: 0 = gold gravada; 2 = configuração ausente ou inválida;
3 = silver da DRI ausente ou fora do contrato.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import logging
import re
import sys

import duckdb

from tcg.config import ConfiguracaoError, ler_colecao, ler_config_minio
from tcg.gold.sql import CURINGAS, montar_estrela
from tcg.lake.cliente import criar_cliente, existe
from tcg.lake.duckdb import caminho_s3, conectar, gravar_parquet
from tcg.lake.guarda_prefixo import GROUP_ID_DRI
from tcg.log import configurar_log
from tcg.silver.construtor import CONTRATO, chave_silver

log = logging.getLogger(__name__)

SUCESSO = 0
ERRO_CONFIG = 2
ERRO_SILVER_DRI = 3

PREFIXO_GOLD = f"gold/group_id={GROUP_ID_DRI}"
TABELAS_COLECAO = tuple(CURINGAS)  # colecao, produto, preco_diario
TABELAS_SO_DRI = ("cambio_diario", "cdi_diario")
_GRUPO = re.compile(r"group_id=(\d+)")


class SilverDriInvalidaError(RuntimeError):
    """A silver da DRI está ausente ou fora do contrato; a gold não é gerada."""


@dataclass
class ResultadoGold:
    incluidas: list[int] = field(default_factory=list)
    ignoradas: dict[int, str] = field(default_factory=dict)
    linhas: dict[str, int] = field(default_factory=dict)
    chaves: list[str] = field(default_factory=list)


def chave_gold(tabela: str) -> str:
    """Caminho de cada tabela da gold (relativo ao bucket)."""
    return f"{PREFIXO_GOLD}/{tabela}.parquet"


# ---------------------------------------------------------------- descoberta


def descobrir_silvers(cliente, bucket: str) -> dict[int, dict[str, list[str]]]:
    """{group_id: {tabela: [chaves .parquet]}} das três tabelas lidas de todas as coleções."""
    encontrados: dict[int, dict[str, list[str]]] = {}
    for tabela in TABELAS_COLECAO:
        for objeto in cliente.list_objects(bucket_name=bucket, prefix=f"silver/{tabela}/", recursive=True):
            chave = objeto.object_name
            partes = chave.split("/")
            casamento = _GRUPO.fullmatch(partes[2]) if len(partes) > 3 else None
            if casamento is None or not chave.endswith(".parquet"):
                log.warning("objeto da silver ignorado (fora do layout do contrato): %s", chave)
                continue
            grupo = encontrados.setdefault(int(casamento[1]), {})
            grupo.setdefault(tabela, []).append(chave)
    for grupo in encontrados.values():
        for chaves in grupo.values():
            chaves.sort()
    return encontrados


# ---------------------------------------------------------------- contrato


def _esquema(con: duckdb.DuckDBPyConnection, caminho: str) -> dict[str, str]:
    literal = "'" + caminho.replace("'", "''") + "'"
    linhas = con.execute(
        f"DESCRIBE SELECT * FROM read_parquet({literal}, hive_partitioning = false)"
    ).fetchall()
    return {nome: tipo for nome, tipo, *_ in linhas}


def motivo_fora_do_contrato(
    con: duckdb.DuckDBPyConnection, bucket: str, tabela: str, chaves: list[str]
) -> str | None:
    """Primeiro desvio do contrato nos Parquets da tabela, ou None se todos seguem o contrato."""
    if not chaves:
        return f"{tabela}: tabela ausente"
    for chave in chaves:
        try:
            esquema = _esquema(con, caminho_s3(bucket, chave))
        except duckdb.Error as erro:
            return f"{tabela}: Parquet ilegível em {chave} ({type(erro).__name__})"
        for coluna, tipo in CONTRATO[tabela]:
            if coluna not in esquema:
                return f"{tabela}: coluna {coluna} ausente em {chave}"
            if esquema[coluna] != tipo:
                return f"{tabela}: {coluna} {esquema[coluna]} (contrato: {tipo}) em {chave}"
    return None


def selecionar_colecoes(
    cliente, con: duckdb.DuckDBPyConnection, bucket: str, silvers: dict[int, dict[str, list[str]]]
) -> tuple[dict[str, list[str]], ResultadoGold]:
    """Arquivos aprovados por tabela e o resultado com coleções incluídas e ignoradas."""
    r = ResultadoGold()
    arquivos: dict[str, list[str]] = {t: [] for t in TABELAS_COLECAO}

    dri = silvers.get(GROUP_ID_DRI, {})
    for tabela in TABELAS_COLECAO:
        motivo = motivo_fora_do_contrato(con, bucket, tabela, dri.get(tabela, []))
        if motivo:
            raise SilverDriInvalidaError(f"silver da DRI (group_id={GROUP_ID_DRI}) inválida: {motivo}")
    for tabela in TABELAS_SO_DRI:
        chave = chave_silver(tabela)
        motivo = motivo_fora_do_contrato(con, bucket, tabela, [chave] if existe(cliente, bucket, chave) else [])
        if motivo:
            raise SilverDriInvalidaError(f"silver da DRI (group_id={GROUP_ID_DRI}) inválida: {motivo}")

    for group_id in sorted(silvers):
        grupo = silvers[group_id]
        motivo = None
        if group_id != GROUP_ID_DRI:
            for tabela in TABELAS_COLECAO:
                motivo = motivo_fora_do_contrato(con, bucket, tabela, grupo.get(tabela, []))
                if motivo:
                    break
        if motivo:
            r.ignoradas[group_id] = motivo
            log.warning("silver ignorada: group_id=%d motivo=%s", group_id, motivo)
            continue
        r.incluidas.append(group_id)
        for tabela in TABELAS_COLECAO:
            arquivos[tabela].extend(caminho_s3(bucket, c) for c in grupo[tabela])
    return arquivos, r


# ---------------------------------------------------------------- construção


def construir_gold(cliente, con: duckdb.DuckDBPyConnection, bucket: str) -> ResultadoGold:
    """Confere as silvers, monta a estrela e grava a gold da DRI pela Guarda de prefixo."""
    silvers = descobrir_silvers(cliente, bucket)
    arquivos, r = selecionar_colecoes(cliente, con, bucket, silvers)
    if r.incluidas == [GROUP_ID_DRI]:
        log.info("nenhuma outra coleção disponível: gold só com a DRI (RF-22)")
    log.info("coleções na gold: %s", ", ".join(str(g) for g in r.incluidas))

    tabelas = montar_estrela(con, f"s3://{bucket}", arquivos)
    for tabela in tabelas:
        chave = chave_gold(tabela)
        gravar_parquet(con, bucket, f"SELECT * FROM {tabela}", chave)
        r.linhas[tabela] = con.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0]
        r.chaves.append(chave)
    log.info("linhas gravadas por tabela: %s", ", ".join(f"{t}: {n}" for t, n in r.linhas.items()))
    return r


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tcg.gold.construtor", description=__doc__.splitlines()[0]
    )
    parser.parse_args(argv)
    configurar_log()
    try:
        colecao = ler_colecao()
        config = ler_config_minio(colecao)
    except ConfiguracaoError as erro:
        log.error("%s", erro)
        return ERRO_CONFIG
    con = conectar(config)
    try:
        construir_gold(criar_cliente(config), con, config.bucket)
    except SilverDriInvalidaError as erro:
        log.error("%s; gold não gerada", erro)
        return ERRO_SILVER_DRI
    finally:
        con.close()
    return SUCESSO


if __name__ == "__main__":
    sys.exit(main())
