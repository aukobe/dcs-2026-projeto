"""Gravador do bruto (specs/plan.md, seção 4; RF-02, RES-08).

Grava o corpo HTTP byte a byte no checkout da Branch dados-raw, em modo de
criação exclusiva: se o arquivo já existir, a gravação é recusada, o arquivo
original fica intacto e a recusa vai para o log.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

log = logging.getLogger(__name__)


class ArquivoExistenteError(FileExistsError):
    """O arquivo do bruto já existe; nada foi sobrescrito (RF-02)."""


def gravar(caminho: Path, corpo: bytes) -> str:
    """Grava `corpo` sem alteração em `caminho` e devolve o sha256 do arquivo."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    try:
        with caminho.open("xb") as arquivo:
            arquivo.write(corpo)
    except FileExistsError:
        log.error("gravação recusada: arquivo já existe no bruto, nada sobrescrito: %s", caminho)
        raise ArquivoExistenteError(f"arquivo já existe no bruto: {caminho}") from None
    sha256 = hashlib.sha256(caminho.read_bytes()).hexdigest()
    log.info("bruto gravado: %s bytes=%d sha256=%s", caminho, len(corpo), sha256)
    return sha256
