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
5. Carteiras (T-44; RF-23 a RF-26): `construir_carteiras` lê a gold da DRI
   recém-gravada (`fato_preco_diario`, `dim_produto`, `fato_cambio_diario`),
   compõe (T-41), liquida com a taxa do parâmetro e com taxa 0 (T-42) e calcula
   as métricas (T-43), sem recompor a carteira e sem ler nem gravar a silver.
   Grava, pela Guarda de prefixo:
   - `gold/group_id=24269/{composicao_carteira, liquidacao_carteira,
     liquidacao_item, metricas_carteira}.parquet` (para o painel, T-47);
   - `gold_turma/carteira/group_id=24269/carteira.parquet` no contrato da spec:
     uma linha por dia de calendário × carteira, só com a taxa do parâmetro
     (0 em dolar e cdi), retorno_acumulado = valor_brl / 1000 − 1.
   A propria só é calculada se o ADR-005 estiver aceito
   (`regra_propria_aceita`); senão, linhas com valor nulo ("regra pendente").
   Chaves fixas: um novo `make gold` substitui só os arquivos da DRI.

Códigos de saída: 0 = gold gravada; 2 = configuração ausente ou inválida;
3 = silver da DRI ausente ou fora do contrato; 4 = carteiras não calculadas
(ex.: sem PTAX aplicada em algum dia do período).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import logging
from pathlib import Path
import re
import sys

import duckdb

from tcg.config import ConfiguracaoError, ler_colecao, ler_config_minio, ler_parametros
from tcg.gold.carteiras import CARTEIRAS, ORCAMENTO, compor_carteiras, ler_primeiro_dia, registrar_composicao
from tcg.gold.liquidacao import LinhaCarteira, ler_dados_diarios, registrar_liquidacao
from tcg.gold.metricas_carteira import registrar_metricas
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
ERRO_CARTEIRAS = 4

PREFIXO_GOLD = f"gold/group_id={GROUP_ID_DRI}"
CHAVE_GOLD_TURMA = f"gold_turma/carteira/group_id={GROUP_ID_DRI}/carteira.parquet"
TABELAS_CARTEIRA = ("composicao_carteira", "liquidacao_carteira", "liquidacao_item", "metricas_carteira")
TABELA_GOLD_TURMA = "gold_turma_carteira"
CARTEIRAS_SEM_TAXA = ("dolar", "cdi")
ADR_PROPRIA = Path(__file__).resolve().parents[3] / "docs" / "adr" / "ADR-005-carteira-propria.md"
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


# ---------------------------------------------------------------- carteiras


@dataclass
class ResultadoCarteiras:
    regra_propria: bool
    taxa_venda: float
    linhas: dict[str, int] = field(default_factory=dict)
    chaves: list[str] = field(default_factory=list)


def regra_propria_aceita(caminho: Path | None = None) -> bool:
    """True só se o ADR-005 existe e a seção "## Status" começa com "Aceito" (RF-23)."""
    caminho = caminho or ADR_PROPRIA
    try:
        linhas = caminho.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return False
    for i, linha in enumerate(linhas):
        if linha.strip() == "## Status":
            seguintes = [l.strip() for l in linhas[i + 1:] if l.strip()]
            return bool(seguintes) and seguintes[0].startswith("Aceito")
    return False


SQL_GOLD_TURMA = """
CREATE OR REPLACE TABLE {destino} AS
SELECT
    data,
    CAST({group_id} AS INTEGER)                    AS group_id,
    carteira,
    CAST(valor_brl AS DOUBLE)                      AS valor_brl,
    CAST(valor_brl / {orcamento} - 1 AS DOUBLE)    AS retorno_acumulado,
    CAST(CASE WHEN carteira IN ({sem_taxa}) THEN 0 ELSE taxa_venda END AS DOUBLE) AS taxa_venda
FROM {liquidacao}
WHERE taxa_venda = $taxa
ORDER BY data, {ordem}
"""


def calcular_carteiras(
    con: duckdb.DuckDBPyConnection,
    fato: str,
    dim_produto: str,
    fato_cambio: str,
    taxa_venda: float,
    regra_propria: bool,
) -> dict[str, int]:
    """Registra no DuckDB as tabelas das carteiras e da gold_turma; devolve as linhas por tabela.

    Composição (T-41), liquidação com a taxa do parâmetro e com taxa 0 (T-42) e
    métricas (T-43) a partir das linhas da liquidação registrada, sem recalcular.
    """
    dados_d1 = ler_primeiro_dia(con, fato, dim_produto, fato_cambio, GROUP_ID_DRI)
    composicoes = compor_carteiras(dados_d1, regra_propria)
    registrar_composicao(con, composicoes, "composicao_carteira")
    dados = ler_dados_diarios(con, fato, fato_cambio, composicoes, GROUP_ID_DRI)
    registrar_liquidacao(con, composicoes, dados, taxa_venda, "liquidacao_carteira", "liquidacao_item")
    linhas = [LinhaCarteira(*r) for r in con.execute("SELECT * FROM liquidacao_carteira").fetchall()]
    registrar_metricas(con, linhas, "metricas_carteira")
    ordem = "CASE carteira " + " ".join(f"WHEN '{c}' THEN {i}" for i, c in enumerate(CARTEIRAS)) + " END"
    con.execute(
        SQL_GOLD_TURMA.format(
            destino=TABELA_GOLD_TURMA,
            group_id=GROUP_ID_DRI,
            orcamento=ORCAMENTO,
            sem_taxa=", ".join(f"'{c}'" for c in CARTEIRAS_SEM_TAXA),
            liquidacao="liquidacao_carteira",
            ordem=ordem,
        ),
        {"taxa": taxa_venda},
    )
    return {
        t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        for t in (*TABELAS_CARTEIRA, TABELA_GOLD_TURMA)
    }


def construir_carteiras(
    con: duckdb.DuckDBPyConnection, bucket: str, taxa_venda: float, regra_propria: bool
) -> ResultadoCarteiras:
    """Lê a gold da DRI, calcula as carteiras e grava gold e gold_turma pela Guarda de prefixo."""
    r = ResultadoCarteiras(regra_propria=regra_propria, taxa_venda=taxa_venda)
    if not regra_propria:
        log.warning("ADR-005 não aceito: carteira propria com \"regra pendente\" (RF-23)")
    for tabela in ("fato_preco_diario", "dim_produto", "fato_cambio_diario"):
        origem = caminho_s3(bucket, chave_gold(tabela)).replace("'", "''")
        con.execute(
            f"CREATE OR REPLACE TEMPORARY VIEW gold_{tabela} AS "
            f"SELECT * FROM read_parquet('{origem}', hive_partitioning = false)"
        )
    r.linhas = calcular_carteiras(
        con, "gold_fato_preco_diario", "gold_dim_produto", "gold_fato_cambio_diario",
        taxa_venda, regra_propria,
    )
    destinos = [(t, chave_gold(t)) for t in TABELAS_CARTEIRA] + [(TABELA_GOLD_TURMA, CHAVE_GOLD_TURMA)]
    for tabela, chave in destinos:
        gravar_parquet(con, bucket, f"SELECT * FROM {tabela}", chave)
        r.chaves.append(chave)
    log.info("carteiras gravadas (taxa_venda=%s, propria=%s): %s", taxa_venda,
             "calculada" if regra_propria else "regra pendente",
             ", ".join(f"{t}: {n}" for t, n in r.linhas.items()))
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
        parametros = ler_parametros()
    except ConfiguracaoError as erro:
        log.error("%s", erro)
        return ERRO_CONFIG
    con = conectar(config)
    try:
        construir_gold(criar_cliente(config), con, config.bucket)
        construir_carteiras(con, config.bucket, parametros.taxa_venda, regra_propria_aceita())
    except SilverDriInvalidaError as erro:
        log.error("%s; gold não gerada", erro)
        return ERRO_SILVER_DRI
    except ValueError as erro:
        log.error("carteiras não calculadas: %s", erro)
        return ERRO_CARTEIRAS
    finally:
        con.close()
    return SUCESSO


if __name__ == "__main__":
    sys.exit(main())
