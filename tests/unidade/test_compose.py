"""Testes do docker-compose.yml do MinIO local (T-15; ADR-002, RNF-09, RNF-10).

Lê o compose com `yaml.safe_load`; não usa rede nem Docker.
"""

from pathlib import Path
import re

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[2]
COMPOSE = RAIZ / "docker-compose.yml"
MAKEFILE = RAIZ / "Makefile"
IMAGEM = "ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z"


@pytest.fixture(scope="module")
def texto():
    return COMPOSE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def compose(texto):
    return yaml.safe_load(texto)


@pytest.fixture(scope="module")
def minio(compose):
    assert list(compose["services"]) == ["minio"]
    return compose["services"]["minio"]


def test_imagem_com_tag_fixada(minio, texto):
    assert minio["image"] == IMAGEM
    assert "latest" not in texto


def test_portas_9000_e_9001(minio):
    assert sorted(minio["ports"]) == ["9000:9000", "9001:9001"]
    assert '--console-address ":9001"' in minio["command"]


def test_volume_nomeado(compose, minio):
    assert minio["volumes"] == ["minio_dados:/data"]
    origem = minio["volumes"][0].split(":")[0]
    assert not origem.startswith((".", "/", "~")), "bind mount não é permitido"
    assert origem in compose["volumes"]


def test_healthcheck_mc_ready_local(minio):
    hc = minio["healthcheck"]
    assert hc["test"] == ["CMD", "mc", "ready", "local"]
    assert hc["retries"] > 0


def test_credenciais_vindas_de_variaveis(minio):
    env = minio["environment"]
    def padrao(var):
        return r"\$\{" + var + r":\?[^}]*\}"

    assert re.fullmatch(padrao("MINIO_ACCESS_KEY"), env["MINIO_ROOT_USER"])
    assert re.fullmatch(padrao("MINIO_SECRET_KEY"), env["MINIO_ROOT_PASSWORD"])
    assert set(env) == {"MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD"}


def test_alvo_make_up():
    texto = MAKEFILE.read_text(encoding="utf-8")
    assert re.search(r"^\.PHONY:.*\bup\b", texto, re.M)
    assert re.search(r"^up:\n\tdocker compose up -d --wait$", texto, re.M)
