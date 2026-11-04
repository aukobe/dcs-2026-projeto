"""Sincronizador: Gravador sem sobrescrita (specs/plan.md, seção 4; RF-05, RNF-03, ADR-001).

Uso: `make sync` (ou `python -m tcg.sync.sincronizador`, com as variáveis do
`.env` no ambiente).

Para cada arquivo de `raw/` da Branch dados-raw:
1. recusa, antes de qualquer chamada ao SDK, a chave fora de
   `raw/<fonte>/group_id=<GROUP_ID>/`;
2. `stat_object` na chave; se existir, recusa a sobrescrita e registra no log;
3. lê o blob e confere o sha1 do Git com o id do blob;
4. `put_object` com os bytes exatos e confere o sha256 do objeto gravado com
   o da origem.

Códigos de saída: 0 = todos enviados ou recusados por já existirem;
1 = alguma chave fora do escopo, blob corrompido ou hash divergente;
2 = configuração ausente ou falha do git.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
import hashlib
import io
import logging
from pathlib import Path
import re
import sys

from tcg.config import ConfiguracaoError, ler_config_minio
from tcg.lake.cliente import criar_cliente, existe, garantir_bucket
from tcg.log import configurar_log
from tcg.sync import leitor_branch
from tcg.sync.leitor_branch import ArquivoBranch, LeitorBranchError

log = logging.getLogger(__name__)

SUCESSO = 0
FALHA = 1
ERRO_CONFIG = 2

RAIZ_REPO = Path(__file__).resolve().parents[3]


@dataclass
class Resumo:
    enviados: list[str] = field(default_factory=list)
    recusados: list[str] = field(default_factory=list)
    fora_do_escopo: list[str] = field(default_factory=list)
    falhas: list[str] = field(default_factory=list)

    @property
    def codigo_saida(self) -> int:
        return FALHA if self.fora_do_escopo or self.falhas else SUCESSO


def chave_permitida(chave: str, group_id: int) -> bool:
    """Aceita só `raw/<fonte>/group_id=<group_id>/<resto>`, sem `..`, `.` nem partes vazias."""
    partes = chave.split("/")
    if len(partes) < 4 or any(p in ("", ".", "..") for p in partes):
        return False
    return (
        partes[0] == "raw"
        and re.fullmatch(r"[a-z0-9_]+", partes[1]) is not None
        and partes[2] == f"group_id={group_id}"
    )


def sha1_blob(conteudo: bytes) -> str:
    """Id do blob no Git para estes bytes (`blob <tamanho>\\0` + conteúdo)."""
    return hashlib.sha1(b"blob %d\0" % len(conteudo) + conteudo).hexdigest()


def _ler_objeto(cliente, bucket: str, chave: str) -> bytes:
    resposta = cliente.get_object(bucket_name=bucket, object_name=chave)
    try:
        return resposta.read()
    finally:
        resposta.close()
        resposta.release_conn()


def sincronizar(
    cliente,
    bucket: str,
    group_id: int,
    arquivos: Iterable[ArquivoBranch],
    ler: Callable[[str], bytes],
) -> Resumo:
    """Envia ao bucket cada arquivo ainda ausente; nunca regrava chave existente."""
    resumo = Resumo()
    for arquivo in arquivos:
        chave = arquivo.chave
        if not chave_permitida(chave, group_id):
            log.error("chave fora do escopo recusada, nada gravado: %s", chave)
            resumo.fora_do_escopo.append(chave)
            continue
        if existe(cliente, bucket, chave):
            log.warning("recusa de sobrescrita: chave já existe no MinIO, não regravada: %s", chave)
            resumo.recusados.append(chave)
            continue
        conteudo = ler(arquivo.blob)
        if sha1_blob(conteudo) != arquivo.blob:
            log.error("blob corrompido, nada gravado: %s (blob %s)", chave, arquivo.blob)
            resumo.falhas.append(chave)
            continue
        hash_origem = hashlib.sha256(conteudo).hexdigest()
        cliente.put_object(
            bucket_name=bucket,
            object_name=chave,
            data=io.BytesIO(conteudo),
            length=len(conteudo),
            content_type="application/json",
        )
        hash_destino = hashlib.sha256(_ler_objeto(cliente, bucket, chave)).hexdigest()
        if hash_destino != hash_origem:
            log.error(
                "hash divergente após envio: %s origem=%s destino=%s", chave, hash_origem, hash_destino
            )
            resumo.falhas.append(chave)
            continue
        log.info("enviado: %s sha256=%s bytes=%d", chave, hash_origem, len(conteudo))
        resumo.enviados.append(chave)

    log.info(
        "sincronização encerrada: enviados=%d recusados=%d fora_do_escopo=%d falhas=%d",
        len(resumo.enviados), len(resumo.recusados), len(resumo.fora_do_escopo), len(resumo.falhas),
    )
    return resumo


def executar(repo: Path = RAIZ_REPO, cliente=None) -> int:
    try:
        config = ler_config_minio()
    except ConfiguracaoError as erro:
        log.error("sincronização recusada: %s", erro)
        return ERRO_CONFIG
    cliente = cliente or criar_cliente(config)
    try:
        leitor_branch.buscar(repo)
        arquivos = leitor_branch.listar(repo)
    except LeitorBranchError:
        return ERRO_CONFIG
    garantir_bucket(cliente, config.bucket)
    resumo = sincronizar(
        cliente, config.bucket, config.group_id, arquivos, lambda blob: leitor_branch.ler(repo, blob)
    )
    return resumo.codigo_saida


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tcg.sync.sincronizador", description=__doc__.splitlines()[0]
    )
    parser.add_argument("--repo", type=Path, default=RAIZ_REPO, help="clone com o remoto origin")
    args = parser.parse_args(argv)
    configurar_log()
    return executar(args.repo)


if __name__ == "__main__":
    sys.exit(main())
