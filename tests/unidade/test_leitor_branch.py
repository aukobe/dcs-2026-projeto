"""Testes do Leitor da branch (T-17, RF-05).

Cada teste monta, num diretório temporário, um remoto bare com a branch
`dados-raw` e um clone que só tem a `main`; o leitor busca e lê a branch pelos
blobs, sem rede e sem tocar no repositório do projeto.
"""

from pathlib import Path
import hashlib
import os
import subprocess

import pytest

from tcg.sync import leitor_branch
from tcg.sync.leitor_branch import ArquivoBranch, LeitorBranchError

PRODUCTS = "raw/tcgplayer/group_id=24269/data=2026-11-03/products.json"
PRICES = "raw/tcgplayer/group_id=24269/data=2026-11-03/prices.json"
PTAX = "raw/bcb_ptax/group_id=24269/data=2026-11-03/cotacao.json"
CDI = "raw/bcb_cdi/group_id=24269/data=2026-11-03/cdi.json"
PRICES_DIA_2 = "raw/tcgplayer/group_id=24269/data=2026-11-04/prices.json"

CONTEUDOS = {
    PRODUCTS: b'{"results": [\r\n  {"productId": 1}\r\n]}\r\n',
    PRICES: b'{"results": []}\n\r\n\rfim sem quebra',
    PTAX: b'{"value": [{"cotacaoVenda": 5.3}]}\r\n\xff\xfe\x00bytes nao utf-8',
    CDI: b'[{"data": "03/11/2026", "valor": "0.055131"}]',
}


@pytest.fixture
def ambiente(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    valores = {
        "HOME": str(home),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "Teste",
        "GIT_AUTHOR_EMAIL": "teste@example.invalid",
        "GIT_COMMITTER_NAME": "Teste",
        "GIT_COMMITTER_EMAIL": "teste@example.invalid",
    }
    for nome, valor in valores.items():
        monkeypatch.setenv(nome, valor)
    return {**os.environ}


def _git(repo, *args, env):
    return subprocess.run(
        ["git", "-C", str(repo), *args], env=env, check=True, capture_output=True,
    ).stdout


def _gravar(repo: Path, chave: str, corpo: bytes) -> None:
    caminho = repo / chave
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(corpo)


@pytest.fixture
def repos(tmp_path, ambiente):
    """Remoto bare com `main` e `dados-raw`; clone `leitor` só com a `main`."""
    remoto = tmp_path / "remoto.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remoto)], env=ambiente, check=True)

    autor = tmp_path / "autor"
    subprocess.run(["git", "init", "-q", "-b", "main", str(autor)], env=ambiente, check=True)
    (autor / "codigo.py").write_text("print('main')\n")
    _git(autor, "add", "codigo.py", env=ambiente)
    _git(autor, "commit", "-q", "-m", "inicial", env=ambiente)
    _git(autor, "remote", "add", "origin", str(remoto), env=ambiente)
    _git(autor, "push", "-q", "origin", "main", env=ambiente)

    _git(autor, "checkout", "-q", "--orphan", "dados-raw", env=ambiente)
    _git(autor, "rm", "-rq", "--cached", ".", env=ambiente)
    (autor / "codigo.py").unlink()
    (autor / ".gitattributes").write_bytes(b"* -text\n")
    (autor / "README.md").write_bytes(b"# dados-raw\n")
    for chave, corpo in CONTEUDOS.items():
        _gravar(autor, chave, corpo)
    _git(autor, "add", "-A", env=ambiente)
    _git(autor, "commit", "-q", "-m", "dados(coleta): 2026-11-03 [RF-01]", env=ambiente)
    _git(autor, "push", "-q", "origin", "dados-raw", env=ambiente)

    leitor = tmp_path / "leitor"
    subprocess.run(
        ["git", "clone", "-q", "--single-branch", "-b", "main", str(remoto), str(leitor)],
        env=ambiente, check=True,
    )
    return autor, leitor


def test_lista_so_as_chaves_de_raw(repos):
    _, leitor = repos
    leitor_branch.buscar(leitor)

    arquivos = leitor_branch.listar(leitor)

    assert [a.chave for a in arquivos] == sorted(CONTEUDOS)
    assert all(isinstance(a, ArquivoBranch) and len(a.blob) == 40 for a in arquivos)


@pytest.mark.parametrize("autocrlf", ["false", "true"])
def test_bytes_identicos_inclusive_crlf(repos, ambiente, autocrlf):
    _, leitor = repos
    _git(leitor, "config", "core.autocrlf", autocrlf, env=ambiente)
    leitor_branch.buscar(leitor)

    lidos = {a.chave: leitor_branch.ler(leitor, a.blob) for a in leitor_branch.listar(leitor)}

    assert lidos == CONTEUDOS
    assert b"\r\n" in lidos[PRODUCTS]
    for chave, corpo in CONTEUDOS.items():
        assert hashlib.sha256(lidos[chave]).hexdigest() == hashlib.sha256(corpo).hexdigest()


def test_sem_checkout(repos, ambiente):
    _, leitor = repos
    head_antes = _git(leitor, "rev-parse", "HEAD", env=ambiente)
    branch_antes = _git(leitor, "branch", "--show-current", env=ambiente)
    arvore_antes = sorted(p.name for p in leitor.iterdir())

    leitor_branch.buscar(leitor)
    for arquivo in leitor_branch.listar(leitor):
        leitor_branch.ler(leitor, arquivo.blob)

    assert _git(leitor, "rev-parse", "HEAD", env=ambiente) == head_antes
    assert _git(leitor, "branch", "--show-current", env=ambiente) == branch_antes
    assert sorted(p.name for p in leitor.iterdir()) == arvore_antes
    assert not (leitor / "raw").exists()
    assert _git(leitor, "status", "--porcelain", env=ambiente) == b""


def test_fetch_traz_dia_novo(repos, ambiente):
    autor, leitor = repos
    leitor_branch.buscar(leitor)
    assert PRICES_DIA_2 not in [a.chave for a in leitor_branch.listar(leitor)]

    _gravar(autor, PRICES_DIA_2, b'{"results": [1]}\r\n')
    _git(autor, "add", "-A", env=ambiente)
    _git(autor, "commit", "-q", "-m", "dados(coleta): 2026-11-04 [RF-01]", env=ambiente)
    _git(autor, "push", "-q", "origin", "dados-raw", env=ambiente)

    assert PRICES_DIA_2 not in [a.chave for a in leitor_branch.listar(leitor)]
    leitor_branch.buscar(leitor)
    arquivos = {a.chave: a for a in leitor_branch.listar(leitor)}
    assert PRICES_DIA_2 in arquivos
    assert leitor_branch.ler(leitor, arquivos[PRICES_DIA_2].blob) == b'{"results": [1]}\r\n'


def test_ref_inexistente_gera_erro(repos):
    _, leitor = repos
    with pytest.raises(LeitorBranchError, match="ls-tree"):
        leitor_branch.listar(leitor)
