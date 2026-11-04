"""Leitor da branch (specs/plan.md, seção 4; RF-05, ADR-001).

Faz `git fetch` da Branch dados-raw e lê os arquivos de `raw/` pelos blobs
(`git ls-tree` e `git cat-file`), sem checkout e sem conversão de fim de
linha: a saída do git é lida sempre como bytes, nunca como texto.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import subprocess

log = logging.getLogger(__name__)

BRANCH = "dados-raw"
REMOTO = "origin"
PREFIXO = "raw/"


class LeitorBranchError(RuntimeError):
    """Falha do git ao buscar, listar ou ler a Branch dados-raw."""


@dataclass(frozen=True)
class ArquivoBranch:
    """Arquivo de `raw/` na branch: chave (caminho idêntico à chave do bruto) e sha do blob."""

    chave: str
    blob: str


def _git(repo: Path, *args: str) -> bytes:
    processo = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        check=False,
    )
    if processo.returncode != 0:
        erro = processo.stderr.decode("utf-8", errors="replace").strip()
        log.error("git %s falhou: %s", args[0], erro)
        raise LeitorBranchError(f"git {' '.join(args)} falhou: {erro}")
    return processo.stdout


def buscar(repo: Path, remoto: str = REMOTO, branch: str = BRANCH) -> None:
    """Atualiza só a ref remota da branch; HEAD, índice e árvore de trabalho não mudam."""
    _git(repo, "fetch", "--quiet", remoto, f"+refs/heads/{branch}:refs/remotes/{remoto}/{branch}")
    log.info("branch buscada: %s/%s", remoto, branch)


def listar(repo: Path, ref: str = f"{REMOTO}/{BRANCH}") -> list[ArquivoBranch]:
    """Lista, em ordem de chave, os blobs de `raw/` na árvore de `ref`."""
    saida = _git(repo, "ls-tree", "-r", "-z", "--full-tree", ref, "--", PREFIXO)
    arquivos = []
    for entrada in saida.split(b"\0"):
        if not entrada:
            continue
        meta, caminho = entrada.split(b"\t", 1)
        _modo, tipo, blob = meta.split(b" ")
        chave = caminho.decode("utf-8")
        if tipo == b"blob" and chave.startswith(PREFIXO):
            arquivos.append(ArquivoBranch(chave=chave, blob=blob.decode("ascii")))
    arquivos.sort(key=lambda a: a.chave)
    log.info("arquivos em %s:%s: %d", ref, PREFIXO, len(arquivos))
    return arquivos


def ler(repo: Path, blob: str) -> bytes:
    """Devolve os bytes exatos do blob, sem filtro nem conversão de fim de linha."""
    return _git(repo, "cat-file", "blob", blob)
