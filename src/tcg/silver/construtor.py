"""Construtor da silver e Escritor Parquet (T-27; RF-06, RF-07, RNF-11).

Uso: `make silver` (ou `python -m tcg.silver.construtor`, com as variáveis do
`.env` no ambiente).

1. Lista pelo SDK todo o bruto da DRI em `raw/{tcgplayer,bcb_ptax,bcb_cdi}/
   group_id=24269/` e lê cada objeto com `get_object` (somente leitura).
2. Converte e valida cada linha com os modelos (T-25) e a quarentena (T-26):
   - `preco_diario`: `data` vem da partição `data=AAAA-MM-DD` da chave; um
     Parquet por data; chave de grão repetida no mesmo bruto vai à quarentena;
   - `produto`: o mesmo `product_id` aparece em vários dias; fica a linha do
     bruto mais recente;
   - `cambio_diario` e `cdi_diario`: deduplicados por data entre brutos;
   - `colecao`: de `config/colecao.toml`.
3. Escritor Parquet: DuckDB local em memória (sem httpfs) cria cada tabela com
   os tipos do contrato, exporta para um Parquet temporário e os bytes vão ao
   MinIO por `guarda_prefixo.gravar`, a única escrita do código fora de `raw/`.
4. Log: contagem de quarentena por tabela e linhas gravadas por tabela.

Leitura Hive (nota da T-24): este módulo não usa `read_parquet` (lê o bruto
JSON pelo SDK). Quem ler a silver deve usar `hive_partitioning = false`, porque
`group_id` já é coluna do contrato e a coluna derivada do caminho a duplicaria.

A silver não apaga nada: sobrescreve as chaves determinísticas (ADR-004).

Códigos de saída: 0 = silver gravada; 2 = configuração ausente ou inválida.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from dataclasses import dataclass, field
import datetime as dt
import json
import logging
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

import duckdb
from pydantic import BaseModel

from tcg.config import Colecao as ColecaoConfig
from tcg.config import ConfiguracaoError, ler_colecao, ler_config_minio
from tcg.lake.cliente import criar_cliente
from tcg.lake.guarda_prefixo import GROUP_ID_DRI, gravar
from tcg.log import configurar_log
from tcg.silver.modelos import (
    cambio_do_bruto,
    cdi_do_bruto,
    colecao_da_config,
    preco_do_bruto,
    produto_do_bruto,
)
from tcg.silver.quarentena import (
    LinhaQuarentena,
    contar_por_tabela,
    deduplicar_por_data,
    formatar_contagem,
    validar,
)

log = logging.getLogger(__name__)

SUCESSO = 0
ERRO_CONFIG = 2

_PARTICAO = f"group_id={GROUP_ID_DRI}"
FONTES = {
    # fonte do bruto -> (arquivo, tabela da silver)
    "tcgplayer/products.json": "produto",
    "tcgplayer/prices.json": "preco_diario",
    "bcb_ptax/cotacao.json": "cambio_diario",
    "bcb_cdi/cdi.json": "cdi_diario",
}
_CHAVE_BRUTO = re.compile(
    rf"raw/(?P<fonte>tcgplayer|bcb_ptax|bcb_cdi)/{_PARTICAO}/data=(?P<data>\d{{4}}-\d{{2}}-\d{{2}})/(?P<arquivo>[a-z]+\.json)"
)

# Colunas e tipos do contrato (specs/spec.md, seção de dados; RF-07 para a quarentena).
CONTRATO: dict[str, list[tuple[str, str]]] = {
    "colecao": [
        ("group_id", "INTEGER"), ("nome", "VARCHAR"), ("sigla", "VARCHAR"),
        ("data_lancamento", "DATE"), ("responsavel", "VARCHAR"),
    ],
    "produto": [
        ("product_id", "INTEGER"), ("group_id", "INTEGER"), ("nome", "VARCHAR"),
        ("tipo_produto", "VARCHAR"), ("raridade", "VARCHAR"), ("numero", "VARCHAR"),
        ("image_url", "VARCHAR"), ("url", "VARCHAR"),
    ],
    "preco_diario": [
        ("data", "DATE"), ("product_id", "INTEGER"), ("group_id", "INTEGER"),
        ("acabamento", "VARCHAR"), ("market_price", "DOUBLE"), ("low_price", "DOUBLE"),
        ("mid_price", "DOUBLE"), ("high_price", "DOUBLE"), ("moeda", "VARCHAR"),
        ("fonte", "VARCHAR"), ("chave_raw", "VARCHAR"),
    ],
    "cambio_diario": [
        ("data", "DATE"), ("cotacao_compra", "DOUBLE"), ("cotacao_venda", "DOUBLE"),
        ("data_hora_cotacao", "TIMESTAMP"), ("boletim", "VARCHAR"), ("chave_raw", "VARCHAR"),
    ],
    "cdi_diario": [("data", "DATE"), ("taxa_dia", "DOUBLE"), ("chave_raw", "VARCHAR")],
    "quarentena": [
        ("tabela", "VARCHAR"), ("motivo", "VARCHAR"), ("chave_raw", "VARCHAR"), ("conteudo", "VARCHAR"),
    ],
}
ORDEM = {
    "colecao": "group_id",
    "produto": "product_id",
    "preco_diario": "product_id, acabamento",
    "cambio_diario": "data",
    "cdi_diario": "data",
    "quarentena": "tabela, chave_raw, motivo, conteudo",
}
MOTIVO_GRAO_DUPLICADO = "chave de grão duplicada no mesmo bruto"


def chave_silver(tabela: str, data: dt.date | None = None) -> str:
    """Caminho do contrato de cada tabela (relativo ao bucket)."""
    base = f"silver/{tabela}/{_PARTICAO}"
    if tabela == "preco_diario":
        return f"{base}/data={data.isoformat()}/preco.parquet"
    arquivo = {"cambio_diario": "cambio", "cdi_diario": "cdi"}.get(tabela, tabela)
    return f"{base}/{arquivo}.parquet"


@dataclass
class ResultadoSilver:
    colecao: list[BaseModel] = field(default_factory=list)
    produto: list[BaseModel] = field(default_factory=list)
    preco_diario: list[BaseModel] = field(default_factory=list)
    cambio_diario: list[BaseModel] = field(default_factory=list)
    cdi_diario: list[BaseModel] = field(default_factory=list)
    quarentena: list[LinhaQuarentena] = field(default_factory=list)
    gravadas: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------- leitura


def _listar_bruto(cliente, bucket: str) -> list[tuple[str, str, dt.date]]:
    """(chave, tabela, data) de cada arquivo do bruto da DRI, em ordem de chave."""
    encontrados = []
    for fonte in ("tcgplayer", "bcb_ptax", "bcb_cdi"):
        prefixo = f"raw/{fonte}/{_PARTICAO}/"
        for objeto in cliente.list_objects(bucket_name=bucket, prefix=prefixo, recursive=True):
            chave = objeto.object_name
            casamento = _CHAVE_BRUTO.fullmatch(chave)
            tabela = casamento and FONTES.get(f"{casamento['fonte']}/{casamento['arquivo']}")
            if not tabela:
                log.warning("objeto do bruto ignorado (fora do contrato): %s", chave)
                continue
            encontrados.append((chave, tabela, dt.date.fromisoformat(casamento["data"])))
    return sorted(encontrados)


def _ler_json(cliente, bucket: str, chave: str) -> Any:
    resposta = cliente.get_object(bucket_name=bucket, object_name=chave)
    try:
        return json.loads(resposta.read())
    finally:
        resposta.close()
        resposta.release_conn()


def _itens(tabela: str, documento: Any) -> list:
    """Linhas de cada formato do bruto: `results` (TCGCSV), `value` (PTAX), lista (CDI)."""
    if tabela in ("produto", "preco_diario"):
        itens = documento.get("results") if isinstance(documento, dict) else None
    elif tabela == "cambio_diario":
        itens = documento.get("value") if isinstance(documento, dict) else None
    else:
        itens = documento
    if not isinstance(itens, list):
        raise ValueError(f"formato inesperado do bruto para {tabela}")
    return itens


# ---------------------------------------------------------------- montagem


def montar_silver(cliente, bucket: str, colecao: ColecaoConfig) -> ResultadoSilver:
    """Lê o bruto e monta as tabelas e a quarentena, sem gravar nada."""
    r = ResultadoSilver(colecao=[colecao_da_config(colecao)])
    produtos: dict[int, BaseModel] = {}
    cambios, cdis = [], []
    precos_por_grao: dict[tuple, list[BaseModel]] = {}

    def anotar(resultado):
        if isinstance(resultado, LinhaQuarentena):
            r.quarentena.append(resultado)
            return None
        return resultado

    for chave, tabela, data in _listar_bruto(cliente, bucket):
        try:
            itens = _itens(tabela, _ler_json(cliente, bucket, chave))
        except ValueError as erro:  # inclui json.JSONDecodeError
            r.quarentena.append(LinhaQuarentena(
                tabela=tabela, motivo=f"bruto ilegível: {erro}", chave_raw=chave, conteudo="",
            ))
            continue
        for item in itens:
            if tabela == "produto":
                modelo = anotar(validar(tabela, produto_do_bruto, item, chave))
                if modelo is not None:
                    produtos[modelo.product_id] = modelo  # bruto mais recente prevalece
            elif tabela == "preco_diario":
                modelo = anotar(validar(tabela, preco_do_bruto, item, chave, data, GROUP_ID_DRI, chave))
                if modelo is not None:
                    grao = (modelo.data, modelo.product_id, modelo.acabamento)
                    precos_por_grao.setdefault(grao, []).append(modelo)
            elif tabela == "cambio_diario":
                modelo = anotar(validar(tabela, cambio_do_bruto, item, chave, chave))
                if modelo is not None:
                    cambios.append(modelo)
            else:
                modelo = anotar(validar(tabela, cdi_do_bruto, item, chave, chave))
                if modelo is not None:
                    cdis.append(modelo)

    for grao in sorted(precos_por_grao):
        grupo = precos_por_grao[grao]
        if len(grupo) == 1:
            r.preco_diario.append(grupo[0])
            continue
        r.quarentena.extend(
            LinhaQuarentena(
                tabela="preco_diario", motivo=MOTIVO_GRAO_DUPLICADO, chave_raw=m.chave_raw,
                conteudo=json.dumps(m.model_dump(mode="json"), ensure_ascii=False, sort_keys=True),
            )
            for m in grupo
        )

    r.produto = [produtos[k] for k in sorted(produtos)]
    r.cambio_diario, q_cambio = deduplicar_por_data("cambio_diario", cambios)
    r.cdi_diario, q_cdi = deduplicar_por_data("cdi_diario", cdis)
    r.quarentena.extend(q_cambio + q_cdi)
    return r


# ---------------------------------------------------------------- escrita


def parquet_bytes(tabela: str, linhas: Iterable[BaseModel], pasta: Path) -> bytes:
    """Parquet com as colunas e tipos do contrato, gerado num DuckDB local."""
    colunas = CONTRATO[tabela]
    nomes = [nome for nome, _ in colunas]
    destino = pasta / f"{tabela}.parquet"
    with duckdb.connect(config={"autoinstall_known_extensions": False,
                                "autoload_known_extensions": False}) as con:
        con.execute(f"CREATE TABLE t ({', '.join(f'{n} {tipo}' for n, tipo in colunas)})")
        valores = [tuple(getattr(linha, n) for n in nomes) for linha in linhas]
        if valores:
            con.executemany(f"INSERT INTO t VALUES ({', '.join('?' * len(nomes))})", valores)
        con.execute(f"COPY (SELECT * FROM t ORDER BY {ORDEM[tabela]}) TO '{destino}' (FORMAT parquet)")
    dados = destino.read_bytes()
    destino.unlink()
    return dados


def gravar_silver(cliente, bucket: str, r: ResultadoSilver) -> dict[str, int]:
    """Grava as cinco tabelas e a quarentena pela Guarda de prefixo."""
    gravadas: dict[str, int] = {}
    with tempfile.TemporaryDirectory(prefix="tcg_silver_") as tmp:
        pasta = Path(tmp)

        def enviar(tabela: str, linhas: list, chave: str) -> None:
            gravar(cliente, bucket, chave, parquet_bytes(tabela, linhas, pasta),
                   content_type="application/vnd.apache.parquet")
            gravadas[tabela] = gravadas.get(tabela, 0) + len(linhas)

        for tabela in ("colecao", "produto", "cambio_diario", "cdi_diario"):
            enviar(tabela, getattr(r, tabela), chave_silver(tabela))
        por_data: dict[dt.date, list] = {}
        for preco in r.preco_diario:
            por_data.setdefault(preco.data, []).append(preco)
        gravadas["preco_diario"] = 0
        for data in sorted(por_data):
            enviar("preco_diario", por_data[data], chave_silver("preco_diario", data))
        enviar("quarentena", r.quarentena, chave_silver("quarentena"))
    return gravadas


def construir_silver(cliente, bucket: str, colecao: ColecaoConfig) -> ResultadoSilver:
    """Lê o bruto da DRI, grava a silver e a quarentena e registra as contagens."""
    if colecao.group_id != GROUP_ID_DRI:
        raise ConfiguracaoError(f"group_id {colecao.group_id} diferente da DRI ({GROUP_ID_DRI})")
    r = montar_silver(cliente, bucket, colecao)
    log.info("quarentena por tabela: %s", formatar_contagem(contar_por_tabela(r.quarentena)))
    r.gravadas = gravar_silver(cliente, bucket, r)
    log.info("linhas gravadas por tabela: %s",
             ", ".join(f"{t}: {n}" for t, n in r.gravadas.items()))
    return r


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tcg.silver.construtor", description=__doc__.splitlines()[0]
    )
    parser.parse_args(argv)
    configurar_log()
    try:
        colecao = ler_colecao()
        config = ler_config_minio(colecao)
    except ConfiguracaoError as erro:
        log.error("%s", erro)
        return ERRO_CONFIG
    construir_silver(criar_cliente(config), config.bucket, colecao)
    return SUCESSO


if __name__ == "__main__":
    sys.exit(main())
