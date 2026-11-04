"""Conexão DuckDB com httpfs contra MinIO descartável (T-24; RF-06, RF-10) [contêiner].

Reaproveita o fixture `minio_descartavel` da T-19 (mesma imagem do compose,
porta aleatória, credenciais geradas na hora; o `.env` não é lido).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
import logging

import pytest

from tcg.config import ConfigMinio
from tcg.lake.cliente import existe, garantir_bucket
from tcg.lake.duckdb import ExtensaoAusenteError, caminho_s3, conectar, gravar_parquet
from tcg.lake.guarda_prefixo import PrefixoProibidoError

from test_minio import minio_descartavel  # noqa: F401  (fixture da T-19)

BUCKET = "tcg-duckdb"
CHAVE = "silver/teste_t24/group_id=24269/data=2026-11-03/teste.parquet"

CONSULTA = """
SELECT * FROM (VALUES
    (CAST(1 AS BIGINT), 'Booster Box', CAST(149.99 AS DOUBLE), CAST(5.3412 AS DECIMAL(18,4)),
     DATE '2026-11-03', TIMESTAMP '2026-11-03 20:30:00'),
    (CAST(2 AS BIGINT), NULL, NULL, NULL, DATE '2026-11-04', NULL)
) AS t(product_id, nome, market_price, ptax, data, coletado_em)
"""

ESQUEMA = [
    ("product_id", "BIGINT"),
    ("nome", "VARCHAR"),
    ("market_price", "DOUBLE"),
    ("ptax", "DECIMAL(18,4)"),
    ("data", "DATE"),
    ("coletado_em", "TIMESTAMP"),
]


def _config(minio) -> ConfigMinio:
    return ConfigMinio(
        endpoint=minio["endpoint"],
        bucket=BUCKET,
        secure=False,
        group_id=24269,
        access_key=minio["usuario"],
        secret_key=minio["senha"],
    )


def _esquema(con, origem: str):
    return [(linha[0], linha[1]) for linha in con.execute(f"DESCRIBE SELECT * FROM {origem}").fetchall()]


@pytest.fixture(scope="module")
def conexao(minio_descartavel):  # noqa: F811
    garantir_bucket(minio_descartavel["cliente"], BUCKET)
    con = conectar(_config(minio_descartavel))
    yield con
    con.close()


def test_parquet_gravado_e_lido_com_os_mesmos_tipos(conexao, minio_descartavel):  # noqa: F811
    destino = gravar_parquet(conexao, BUCKET, CONSULTA, CHAVE)
    assert destino == f"s3://{BUCKET}/{CHAVE}"

    # Sem particionamento Hive: só as colunas gravadas no arquivo.
    leitura = f"read_parquet({caminho_s3(BUCKET, CHAVE)!r}, hive_partitioning = false)"
    assert _esquema(conexao, f"({CONSULTA}) AS origem") == ESQUEMA
    assert _esquema(conexao, leitura) == ESQUEMA

    # Comportamento padrão registrado: `group_id=24269/` no caminho vira coluna Hive.
    padrao = _esquema(conexao, f"read_parquet({caminho_s3(BUCKET, CHAVE)!r})")
    assert ("group_id", "BIGINT") in padrao

    linhas = conexao.execute(f"SELECT * FROM {leitura} ORDER BY product_id").fetchall()
    assert linhas == [
        (1, "Booster Box", 149.99, Decimal("5.3412"), dt.date(2026, 11, 3), dt.datetime(2026, 11, 3, 20, 30)),
        (2, None, None, None, dt.date(2026, 11, 4), None),
    ]


def test_objeto_existe_no_bucket_pelo_sdk(conexao, minio_descartavel):  # noqa: F811
    gravar_parquet(conexao, BUCKET, CONSULTA, CHAVE)
    assert existe(minio_descartavel["cliente"], BUCKET, CHAVE)


def test_chave_fora_da_guarda_nao_grava_nada(conexao, minio_descartavel):  # noqa: F811
    proibida = "raw/tcgplayer/group_id=24269/data=2026-11-03/teste.parquet"
    with pytest.raises(PrefixoProibidoError):
        gravar_parquet(conexao, BUCKET, CONSULTA, proibida)
    assert not existe(minio_descartavel["cliente"], BUCKET, proibida)
    chaves = [o.object_name for o in minio_descartavel["cliente"].list_objects(BUCKET, prefix="raw/", recursive=True)]
    assert chaves == []


def test_credenciais_fora_do_log(minio_descartavel, caplog):  # noqa: F811
    with caplog.at_level(logging.DEBUG):
        con = conectar(_config(minio_descartavel))
        con.close()
    assert "DuckDB conectado ao MinIO" in caplog.text
    assert minio_descartavel["usuario"] not in caplog.text
    assert minio_descartavel["senha"] not in caplog.text


def test_sem_httpfs_instalado_falha_apontando_make_setup(tmp_path):
    config = ConfigMinio("localhost:1", BUCKET, False, 24269, "x", "y")
    with pytest.raises(ExtensaoAusenteError, match="make setup"):
        conectar(config, diretorio_extensoes=tmp_path)
