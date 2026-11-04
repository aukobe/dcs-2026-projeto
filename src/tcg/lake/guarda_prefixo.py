"""Guarda de prefixo (specs/plan.md, seções 4 e 7; RNF-03, RF-13, ADR-004).

Único ponto de escrita do código fora de `raw/` e única função de exclusão.
Cada chave (relativa ao bucket) é validada **antes** de qualquer chamada ao
SDK. São aceitos só os três prefixos derivados da DRI:

- `silver/<tabela>/group_id=24269/<objeto>`
- `gold/group_id=24269/<objeto>`
- `gold_turma/carteira/group_id=24269/<objeto>`

`<objeto>` pode conter subpastas (ex.: `data=2026-11-03/preco.parquet`).
Recusa: `raw/`, outro group_id, partes vazias, `.`, `..`, `\\`, barra inicial
e chave que seja só o prefixo.

O group_id é fixo neste módulo, e não lido do ambiente, para que nenhuma
configuração amplie o alcance da exclusão.
"""

from __future__ import annotations

from collections.abc import Iterable
import io
import logging
import re

log = logging.getLogger(__name__)

GROUP_ID_DRI = 24269
_PARTICAO = f"group_id={GROUP_ID_DRI}"
_NOME = re.compile(r"[a-z0-9_]+")


class PrefixoProibidoError(ValueError):
    """Chave fora dos prefixos derivados do group_id 24269 (RNF-03)."""


def chave_permitida(chave: str) -> bool:
    """True só para chaves com objeto dentro dos três prefixos derivados da DRI."""
    if not isinstance(chave, str) or not chave or "\\" in chave:
        return False
    partes = chave.split("/")
    if any(p in ("", ".", "..") for p in partes):
        return False
    if partes[0] == "silver":
        prefixo = 3
        ok = len(partes) > prefixo and _NOME.fullmatch(partes[1]) is not None and partes[2] == _PARTICAO
    elif partes[0] == "gold":
        prefixo = 2
        ok = len(partes) > prefixo and partes[1] == _PARTICAO
    elif partes[0] == "gold_turma":
        prefixo = 3
        ok = len(partes) > prefixo and partes[1] == "carteira" and partes[2] == _PARTICAO
    else:
        return False
    return ok


def validar_chave(chave: str) -> None:
    """Levanta `PrefixoProibidoError` (e registra no log) se a chave não for permitida."""
    if not chave_permitida(chave):
        motivo = f"chave recusada pela Guarda de prefixo, nenhuma chamada ao SDK: {chave!r}"
        log.error(motivo)
        raise PrefixoProibidoError(motivo)


def gravar(
    cliente,
    bucket: str,
    chave: str,
    dados: bytes,
    content_type: str = "application/octet-stream",
) -> None:
    """Valida a chave e só então grava os bytes com `put_object`."""
    validar_chave(chave)
    cliente.put_object(
        bucket_name=bucket,
        object_name=chave,
        data=io.BytesIO(dados),
        length=len(dados),
        content_type=content_type,
    )
    log.info("objeto gravado: %s/%s (%d bytes)", bucket, chave, len(dados))


def apagar(cliente, bucket: str, chaves: Iterable[str]) -> list[str]:
    """Única exclusão do código: valida todas as chaves e só então apaga.

    Se qualquer chave do lote for recusada, nenhuma é apagada.
    Devolve as chaves apagadas, na ordem recebida.
    """
    lote = list(chaves)
    for chave in lote:
        validar_chave(chave)
    for chave in lote:
        cliente.remove_object(bucket_name=bucket, object_name=chave)
        log.info("objeto apagado: %s/%s", bucket, chave)
    return lote
