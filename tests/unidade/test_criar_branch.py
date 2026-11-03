"""Testes do script que cria a branch órfã dados-raw (T-08, RF-02).

Cada teste roda o script num repositório temporário, com um remoto `origin`
local (repositório bare), sem rede e sem tocar no repositório do projeto.
"""

from pathlib import Path
import os
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "criar_branch_dados_raw.sh"
MENSAGEM = "chore(T-08): branch órfã dados-raw [RF-02]"


@pytest.fixture
def ambiente(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(home),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "Teste",
        "GIT_AUTHOR_EMAIL": "teste@example.invalid",
        "GIT_COMMITTER_NAME": "Teste",
        "GIT_COMMITTER_EMAIL": "teste@example.invalid",
    }
    return env


def _git(repo, *args, env, check=True):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        env=env, check=check, capture_output=True, text=True,
    )


@pytest.fixture
def repos(tmp_path, ambiente):
    """Repositório com um commit na main e um remoto origin bare vazio."""
    remoto = tmp_path / "remoto.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remoto)], env=ambiente, check=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], env=ambiente, check=True)
    (repo / "codigo.py").write_text("print('main')\n")
    _git(repo, "add", "codigo.py", env=ambiente)
    _git(repo, "commit", "-q", "-m", "inicial", env=ambiente)
    _git(repo, "remote", "add", "origin", str(remoto), env=ambiente)
    return repo, remoto


def _rodar_script(repo, env):
    return subprocess.run(
        ["bash", str(SCRIPT), str(repo)], env=env, capture_output=True, text=True,
    )


def test_branch_tem_so_os_dois_arquivos(repos, ambiente):
    repo, _ = repos
    assert _rodar_script(repo, ambiente).returncode == 0
    arquivos = _git(repo, "ls-tree", "-r", "--name-only", "dados-raw", env=ambiente).stdout.split()
    assert sorted(arquivos) == [".gitattributes", "README.md"]


def test_gitattributes_desliga_conversao(repos, ambiente):
    repo, _ = repos
    _rodar_script(repo, ambiente)
    conteudo = _git(repo, "show", "dados-raw:.gitattributes", env=ambiente).stdout
    assert conteudo == "* -text\n"
    readme = _git(repo, "show", "dados-raw:README.md", env=ambiente).stdout
    assert "group_id=24269" in readme


def test_branch_orfa_sem_historico_da_main(repos, ambiente):
    repo, _ = repos
    _rodar_script(repo, ambiente)
    commits = _git(repo, "rev-list", "--parents", "dados-raw", env=ambiente).stdout.splitlines()
    assert len(commits) == 1
    assert len(commits[0].split()) == 1  # só o hash, nenhum pai
    base = _git(repo, "merge-base", "main", "dados-raw", env=ambiente, check=False)
    assert base.returncode != 0 and base.stdout == ""
    assert _git(repo, "log", "-1", "--format=%s", "dados-raw", env=ambiente).stdout.strip() == MENSAGEM


def test_script_nao_faz_push(repos, ambiente):
    repo, remoto = repos
    resultado = _rodar_script(repo, ambiente)
    assert resultado.returncode == 0
    assert _git(remoto, "for-each-ref", env=ambiente).stdout == ""
    assert _git(repo, "branch", "-r", env=ambiente).stdout == ""


def test_main_e_arvore_de_trabalho_intactas(repos, ambiente):
    repo, _ = repos
    head_antes = _git(repo, "rev-parse", "HEAD", env=ambiente).stdout
    _rodar_script(repo, ambiente)
    assert _git(repo, "rev-parse", "HEAD", env=ambiente).stdout == head_antes
    assert _git(repo, "branch", "--show-current", env=ambiente).stdout.strip() == "main"
    assert _git(repo, "status", "--porcelain", env=ambiente).stdout == ""
    assert not (repo / ".gitattributes").exists()


def test_recusa_se_branch_ja_existe(repos, ambiente):
    repo, _ = repos
    assert _rodar_script(repo, ambiente).returncode == 0
    commit = _git(repo, "rev-parse", "dados-raw", env=ambiente).stdout
    segunda = _rodar_script(repo, ambiente)
    assert segunda.returncode != 0
    assert "já existe" in segunda.stderr
    assert _git(repo, "rev-parse", "dados-raw", env=ambiente).stdout == commit


def test_recusa_se_origin_dados_raw_existe(repos, ambiente):
    repo, _ = repos
    main = _git(repo, "rev-parse", "main", env=ambiente).stdout.strip()
    _git(repo, "update-ref", "refs/remotes/origin/dados-raw", main, env=ambiente)
    resultado = _rodar_script(repo, ambiente)
    assert resultado.returncode != 0
    assert "origin/dados-raw" in resultado.stderr
    assert _git(repo, "rev-parse", "--verify", "--quiet", "refs/heads/dados-raw",
                env=ambiente, check=False).returncode != 0
