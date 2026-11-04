"""Cliente MinIO (specs/plan.md, seção 4; RF-02, RF-05, RNF-08).

SDK `minio`, com credenciais lidas só das variáveis de ambiente pelo Leitor
de configuração. Nenhuma função recebe credencial por argumento de linha de
comando nem a registra no log.

Este módulo não tem nenhuma função de exclusão (AGENTS.md).
"""

from __future__ import annotations

import logging

from minio import Minio
from minio.error import S3Error

from tcg.config import ConfigMinio, ler_config_minio

log = logging.getLogger(__name__)

CODIGOS_AUSENTE = frozenset({"NoSuchKey", "NotFound", "NoSuchObject"})
CODIGOS_BUCKET_JA_EXISTE = frozenset({"BucketAlreadyOwnedByYou", "BucketAlreadyExists"})


def criar_cliente(config: ConfigMinio | None = None) -> Minio:
    """Cliente do SDK apontado para o MinIO local; credenciais só do ambiente."""
    config = config or ler_config_minio()
    log.info("cliente MinIO: endpoint=%s bucket=%s secure=%s", config.endpoint, config.bucket, config.secure)
    return Minio(
        config.endpoint,
        access_key=config.access_key,
        secret_key=config.secret_key,
        secure=config.secure,
    )


def existe(cliente, bucket: str, chave: str) -> bool:
    """`stat_object` na chave: True se existe, False se ausente; outros erros sobem."""
    try:
        cliente.stat_object(bucket_name=bucket, object_name=chave)
    except S3Error as erro:
        if erro.code in CODIGOS_AUSENTE:
            return False
        raise
    return True


def garantir_bucket(cliente, bucket: str) -> bool:
    """Cria o bucket se ele não existir, de forma idempotente (AGENTS.md).

    Devolve True se o bucket foi criado nesta chamada e False se já existia.
    """
    if cliente.bucket_exists(bucket_name=bucket):
        log.info("bucket já existe, não recriado: %s", bucket)
        return False
    try:
        cliente.make_bucket(bucket_name=bucket)
    except S3Error as erro:
        if erro.code in CODIGOS_BUCKET_JA_EXISTE:
            log.info("bucket já existe, não recriado: %s", bucket)
            return False
        raise
    log.info("bucket criado: %s", bucket)
    return True
