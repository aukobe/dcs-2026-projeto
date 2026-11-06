"""Construtor da gold contra MinIO descartável (T-32; RF-10, RF-22; ADR-003) [contêiner].

Reaproveita o fixture `minio_descartavel` da T-19 (mesma imagem do compose,
porta aleatória, credenciais geradas na hora; o `.env` não é lido e o MinIO
local de trabalho não é tocado). Cada cenário usa um bucket próprio:

- `tcg-gold`: DRI (24269), gravada pela Guarda de prefixo; segunda coleção
  (99999) no contrato, com uma coluna extra; terceira coleção (88888) com
  `market_price` VARCHAR, fora do contrato. As duas últimas simulam silvers de
  terceiros e por isso são gravadas com `put_object` direto, só neste teste.
- `tcg-gold-so-dri`: só a DRI (RF-22).
- `tcg-gold-sem-dri`: só a segunda coleção; a gold aborta.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import logging
from pathlib import Path

import duckdb
import pytest

from tcg.config import ConfigMinio
from tcg.gold.construtor import (
    PREFIXO_GOLD,
    SilverDriInvalidaError,
    chave_gold,
    construir_gold,
)
from tcg.gold.sql import TABELAS
from tcg.lake.cliente import garantir_bucket
from tcg.lake.duckdb import caminho_s3, conectar
from tcg.lake.guarda_prefixo import gravar

from test_minio import minio_descartavel  # noqa: F401  (fixture da T-19)

DRI = 24269
OUTRA = 99999
FORA = 88888
D = dt.date

DDL = {
    "colecao": "group_id INTEGER, nome VARCHAR, sigla VARCHAR, data_lancamento DATE, responsavel VARCHAR",
    "produto": (
        "product_id INTEGER, group_id INTEGER, nome VARCHAR, tipo_produto VARCHAR, raridade VARCHAR, "
        "numero VARCHAR, image_url VARCHAR, url VARCHAR"
    ),
    "preco_diario": (
        "data DATE, product_id INTEGER, group_id INTEGER, acabamento VARCHAR, market_price DOUBLE, "
        "low_price DOUBLE, mid_price DOUBLE, high_price DOUBLE, moeda VARCHAR, fonte VARCHAR, chave_raw VARCHAR"
    ),
    "cambio_diario": (
        "data DATE, cotacao_compra DOUBLE, cotacao_venda DOUBLE, data_hora_cotacao TIMESTAMP, "
        "boletim VARCHAR, chave_raw VARCHAR"
    ),
    "cdi_diario": "data DATE, taxa_dia DOUBLE, chave_raw VARCHAR",
}


def _parquet(tmp: Path, ddl: str, linhas: list[tuple]) -> bytes:
    """Bytes de um Parquet com os tipos do DDL, gerado num DuckDB local."""
    destino = tmp / "t.parquet"
    with duckdb.connect() as con:
        con.execute(f"CREATE TABLE t ({ddl})")
        if linhas:
            con.executemany(f"INSERT INTO t VALUES ({', '.join('?' * len(linhas[0]))})", linhas)
        con.execute(f"COPY t TO '{destino}' (FORMAT parquet)")
    dados = destino.read_bytes()
    destino.unlink()
    return dados


def _preco(data, product_id, group_id, acabamento, market):
    chave = f"raw/tcgplayer/group_id={group_id}/data={data}/prices.json"
    return (data, product_id, group_id, acabamento, market, market, market, market, "USD", "tcgcsv", chave)


def _gravar_dri(cliente, bucket: str, tmp: Path) -> None:
    """Silver da DRI no layout do contrato, pela Guarda de prefixo."""
    base = f"silver/{{}}/group_id={DRI}"
    objetos = {
        f"{base.format('colecao')}/colecao.parquet": _parquet(
            tmp, DDL["colecao"], [(DRI, "Destined Rivals", "DRI", D(2025, 5, 30), "autor")]),
        f"{base.format('produto')}/produto.parquet": _parquet(
            tmp, DDL["produto"], [(1, DRI, "Carta A", "carta", "Double Rare", "001/182", None, None)]),
        f"{base.format('cambio_diario')}/cambio.parquet": _parquet(tmp, DDL["cambio_diario"], [
            (D(2026, 10, 9), 4.999, 5.0, dt.datetime(2026, 10, 9, 13, 5), "Fechamento", "raw/bcb_ptax/a")]),
        f"{base.format('cdi_diario')}/cdi.parquet": _parquet(
            tmp, DDL["cdi_diario"], [(D(2026, 10, 9), 0.055131, "raw/bcb_cdi/a")]),
    }
    for dia in (10, 11):
        data = D(2026, 10, dia)
        objetos[f"{base.format('preco_diario')}/data={data}/preco.parquet"] = _parquet(
            tmp, DDL["preco_diario"], [_preco(data, 1, DRI, "Normal", 10.0)])
    for chave, dados in objetos.items():
        gravar(cliente, bucket, chave, dados, content_type="application/vnd.apache.parquet")


def _gravar_terceiro(cliente, bucket: str, tmp: Path, group_id: int, market_tipo: str = "DOUBLE",
                     extra: bool = False) -> None:
    """Silver de outra coleção, como um terceiro a publicaria (só neste teste)."""
    ddl_preco = DDL["preco_diario"].replace("market_price DOUBLE", f"market_price {market_tipo}")
    linha_preco = list(_preco(D(2026, 10, 10), 1, group_id, "Holofoil", 20.0))
    if market_tipo == "VARCHAR":
        linha_preco[4] = "20.0"
    ddl_colecao, linha_colecao = DDL["colecao"], (group_id, f"Coleção {group_id}", "OUT", D(2025, 3, 28), "terceiro")
    if extra:
        ddl_colecao += ", observacao VARCHAR"
        linha_colecao += ("coluna extra",)
    objetos = {
        f"silver/colecao/group_id={group_id}/colecao.parquet": _parquet(tmp, ddl_colecao, [linha_colecao]),
        f"silver/produto/group_id={group_id}/produto.parquet": _parquet(
            tmp, DDL["produto"], [(1, group_id, "Carta X", "carta", "Ultra Rare", "010/100", None, None)]),
        f"silver/preco_diario/group_id={group_id}/data=2026-10-10/preco.parquet": _parquet(
            tmp, ddl_preco, [tuple(linha_preco)]),
    }
    for chave, dados in objetos.items():
        cliente.put_object(bucket, chave, io.BytesIO(dados), len(dados))


def _hashes(cliente, bucket: str) -> dict[str, str]:
    """SHA-256 de todos os objetos do bucket."""
    resultado = {}
    for objeto in cliente.list_objects(bucket, recursive=True):
        resposta = cliente.get_object(bucket, objeto.object_name)
        try:
            resultado[objeto.object_name] = hashlib.sha256(resposta.read()).hexdigest()
        finally:
            resposta.close()
            resposta.release_conn()
    return resultado


class _Coletor(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.registros: list[logging.LogRecord] = []

    def emit(self, record):
        self.registros.append(record)


def _config(minio, bucket: str) -> ConfigMinio:
    return ConfigMinio(minio["endpoint"], bucket, False, DRI, minio["usuario"], minio["senha"])


def _executar(minio, bucket: str):
    """Roda o construtor e devolve (resultado ou exceção, hashes antes, hashes depois, logs)."""
    cliente = minio["cliente"]
    antes = _hashes(cliente, bucket)
    coletor = _Coletor()
    raiz = logging.getLogger("tcg")
    nivel = raiz.level
    raiz.addHandler(coletor)
    raiz.setLevel(logging.DEBUG)
    con = conectar(_config(minio, bucket))
    try:
        try:
            resultado = construir_gold(cliente, con, bucket)
        except SilverDriInvalidaError as erro:
            resultado = erro
    finally:
        con.close()
        raiz.removeHandler(coletor)
        raiz.setLevel(nivel)
    return resultado, antes, _hashes(cliente, bucket), coletor.registros


@pytest.fixture(scope="module")
def com_tres_colecoes(minio_descartavel, tmp_path_factory):  # noqa: F811
    bucket = "tcg-gold"
    cliente = minio_descartavel["cliente"]
    garantir_bucket(cliente, bucket)
    tmp = tmp_path_factory.mktemp("gold")
    _gravar_dri(cliente, bucket, tmp)
    _gravar_terceiro(cliente, bucket, tmp, OUTRA, extra=True)
    _gravar_terceiro(cliente, bucket, tmp, FORA, market_tipo="VARCHAR")
    return bucket, *_executar(minio_descartavel, bucket)


def _ler_gold(minio, bucket: str, tabela: str, consulta: str):
    con = conectar(_config(minio, bucket))
    try:
        origem = f"read_parquet('{caminho_s3(bucket, chave_gold(tabela))}', hive_partitioning = false)"
        return con.execute(consulta.format(t=origem)).fetchall()
    finally:
        con.close()


def test_gold_so_no_prefixo_da_dri(com_tres_colecoes):
    _, resultado, antes, depois, _ = com_tres_colecoes
    assert not isinstance(resultado, Exception), resultado
    novas = sorted(set(depois) - set(antes))
    assert novas == sorted(chave_gold(t) for t in TABELAS)
    assert all(c.startswith(PREFIXO_GOLD + "/") for c in novas)
    assert len(novas) == 6
    # nenhum objeto que já existia mudou: silvers da DRI e dos terceiros com o mesmo hash
    assert {c: depois[c] for c in antes} == antes
    terceiros = [c for c in antes if f"group_id={OUTRA}" in c or f"group_id={FORA}" in c]
    assert len(terceiros) == 6


def test_dim_colecao_e_fatos(com_tres_colecoes, minio_descartavel):  # noqa: F811
    bucket, resultado, *_ = com_tres_colecoes
    assert resultado.incluidas == [DRI, OUTRA]
    assert _ler_gold(minio_descartavel, bucket, "dim_colecao", "SELECT group_id FROM {t} ORDER BY 1") == [
        (DRI,), (OUTRA,)]
    fato = _ler_gold(minio_descartavel, bucket, "fato_preco_diario",
                     "SELECT group_id, data, market_price_brl, data_ptax FROM {t} ORDER BY 1, 2")
    assert fato == [
        (DRI, D(2026, 10, 10), pytest.approx(50.0), D(2026, 10, 9)),
        (DRI, D(2026, 10, 11), pytest.approx(50.0), D(2026, 10, 9)),
        (OUTRA, D(2026, 10, 10), pytest.approx(100.0), D(2026, 10, 9)),
    ]
    cambio = _ler_gold(minio_descartavel, bucket, "fato_cambio_diario",
                       "SELECT data, data_ptax, cdi_taxa_dia FROM {t} ORDER BY 1")
    assert cambio == [(D(2026, 10, 10), D(2026, 10, 9), 0.0), (D(2026, 10, 11), D(2026, 10, 9), 0.0)]
    assert resultado.linhas["fato_preco_diario"] == 3


def test_silver_fora_do_contrato_ignorada_com_aviso(com_tres_colecoes):
    _, resultado, _, _, registros = com_tres_colecoes
    assert set(resultado.ignoradas) == {FORA}
    assert "market_price VARCHAR (contrato: DOUBLE)" in resultado.ignoradas[FORA]
    avisos = [r.getMessage() for r in registros if r.levelno == logging.WARNING]
    assert any(f"group_id={FORA}" in m and "market_price VARCHAR" in m for m in avisos), avisos
    assert not any(f"group_id={OUTRA}" in m for m in avisos), "coluna extra não tira a coleção"


def test_sem_outras_colecoes_gera_so_a_dri(minio_descartavel, tmp_path):  # noqa: F811
    bucket = "tcg-gold-so-dri"
    cliente = minio_descartavel["cliente"]
    garantir_bucket(cliente, bucket)
    _gravar_dri(cliente, bucket, tmp_path)
    resultado, antes, depois, registros = _executar(minio_descartavel, bucket)
    assert not isinstance(resultado, Exception), resultado
    assert resultado.incluidas == [DRI] and resultado.ignoradas == {}
    assert sorted(set(depois) - set(antes)) == sorted(chave_gold(t) for t in TABELAS)
    assert _ler_gold(minio_descartavel, bucket, "dim_colecao", "SELECT group_id FROM {t}") == [(DRI,)]
    assert any("gold só com a DRI" in r.getMessage() for r in registros)


def test_silver_da_dri_ausente_aborta(minio_descartavel, tmp_path):  # noqa: F811
    bucket = "tcg-gold-sem-dri"
    cliente = minio_descartavel["cliente"]
    garantir_bucket(cliente, bucket)
    _gravar_terceiro(cliente, bucket, tmp_path, OUTRA)
    resultado, antes, depois, _ = _executar(minio_descartavel, bucket)
    assert isinstance(resultado, SilverDriInvalidaError)
    assert "colecao: tabela ausente" in str(resultado)
    assert depois == antes
    assert not any(c.startswith("gold/") for c in depois)
