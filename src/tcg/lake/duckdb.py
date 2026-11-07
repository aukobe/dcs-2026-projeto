"""Conexão DuckDB com httpfs para o servidor S3 de `MINIO_ENDPOINT` (specs/plan.md, seções 4 e 6; RF-06, RF-10, R-08).

O servidor é o data lake da turma (RustFS) ou, em desenvolvimento, o MinIO
local (ADR-008); as variáveis `MINIO_*` valem para qualquer servidor S3.

- A extensão `httpfs` é instalada na preparação do ambiente (`make setup`);
  este módulo nunca a baixa: o auto-install fica desligado e só há `LOAD`.
- Segredo S3 temporário (só em memória): estilo de caminho, SSL conforme
  `MINIO_SECURE` (true no data lake da turma, false no MinIO local) e credenciais lidas do ambiente pelo
  Leitor de configuração. Nenhuma credencial vai para o log (RNF-08).
- Toda gravação de Parquet passa por `gravar_parquet`, que valida a chave na
  Guarda de prefixo **antes** do `COPY` (RNF-03, ADR-004).
"""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb

from tcg.config import ConfigMinio, ler_config_minio
from tcg.lake.guarda_prefixo import validar_chave

log = logging.getLogger(__name__)

REGIAO = "us-east-1"
NOME_SEGREDO = "minio_local"


class ExtensaoAusenteError(RuntimeError):
    """A extensão httpfs não está instalada; rode `make setup`."""


def _literal(valor: str) -> str:
    """Literal SQL entre aspas simples, com aspas internas duplicadas."""
    return "'" + str(valor).replace("'", "''") + "'"


def conectar(
    config: ConfigMinio | None = None,
    diretorio_extensoes: Path | None = None,
) -> duckdb.DuckDBPyConnection:
    """Conexão em memória com httpfs carregado e segredo S3 apontado para o MinIO."""
    config = config or ler_config_minio()
    opcoes = {"autoinstall_known_extensions": False, "autoload_known_extensions": False}
    if diretorio_extensoes is not None:
        opcoes["extension_directory"] = str(diretorio_extensoes)
    con = duckdb.connect(config=opcoes)
    try:
        con.execute("LOAD httpfs")
    except duckdb.Error as erro:
        con.close()
        raise ExtensaoAusenteError(
            "extensão httpfs do DuckDB não instalada; rode `make setup` (o código não baixa extensões)"
        ) from erro
    con.execute(
        f"""
        CREATE OR REPLACE TEMPORARY SECRET {NOME_SEGREDO} (
            TYPE s3,
            KEY_ID {_literal(config.access_key)},
            SECRET {_literal(config.secret_key)},
            ENDPOINT {_literal(config.endpoint)},
            REGION {_literal(REGIAO)},
            URL_STYLE 'path',
            USE_SSL {"true" if config.secure else "false"}
        )
        """
    )
    log.info(
        "DuckDB conectado ao MinIO: endpoint=%s bucket=%s secure=%s url_style=path",
        config.endpoint, config.bucket, config.secure,
    )
    return con


def caminho_s3(bucket: str, chave: str) -> str:
    """`s3://<bucket>/<chave>`, para leitura com `read_parquet`."""
    return f"s3://{bucket}/{chave.lstrip('/')}"


def gravar_parquet(con: duckdb.DuckDBPyConnection, bucket: str, consulta: str, chave: str) -> str:
    """Grava o resultado da consulta como Parquet na chave, depois da Guarda de prefixo."""
    validar_chave(chave)
    destino = caminho_s3(bucket, chave)
    con.execute(f"COPY ({consulta}) TO {_literal(destino)} (FORMAT parquet)")
    log.info("Parquet gravado: %s", destino)
    return destino
