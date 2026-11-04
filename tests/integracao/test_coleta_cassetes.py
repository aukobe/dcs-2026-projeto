"""Integração da coleta com cassetes vcrpy, sem rede (T-20; RNF-06, RF-01).

O cassete `cassetes/coleta_2026-11-03.yaml` foi montado por
`scripts/montar_cassetes.py` a partir do bruto real de 2026-11-03 na branch
`dados-raw`, sem nenhuma requisição às fontes. O módulo inteiro roda com o
socket bloqueado e o vcrpy em `record_mode="none"`: qualquer requisição fora
do cassete falha.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
from pathlib import Path
import socket
import subprocess

import pytest
import requests
import vcr

from tcg.coleta import __main__ as coleta
from tcg.sync import leitor_branch
from tcg.sync.sincronizador import sha1_blob

RAIZ = Path(__file__).resolve().parents[2]
PASTA_CASSETES = Path(__file__).parent / "cassetes"
CASSETE = PASTA_CASSETES / "coleta_2026-11-03.yaml"
MANIFESTO = PASTA_CASSETES / "coleta_2026-11-03.hashes.json"
AGORA = dt.datetime(2026, 11, 3, 20, 30, tzinfo=dt.UTC)
REF = "origin/dados-raw"


class RedeBloqueadaError(RuntimeError):
    """Tentativa de acesso à rede no teste com cassetes."""


class _SocketBloqueado:
    def __init__(self, *args, **kwargs):
        raise RedeBloqueadaError(f"rede bloqueada no teste com cassetes: socket {args!r}")


def _getaddrinfo_bloqueado(host, *args, **kwargs):
    raise RedeBloqueadaError(f"rede bloqueada no teste com cassetes: DNS {host!r}")


@pytest.fixture(autouse=True)
def sem_rede(monkeypatch):
    monkeypatch.setattr(socket, "socket", _SocketBloqueado)
    monkeypatch.setattr(socket, "getaddrinfo", _getaddrinfo_bloqueado)


@pytest.fixture
def manifesto() -> dict:
    return json.loads(MANIFESTO.read_text(encoding="utf-8"))


def _cassete():
    return vcr.VCR(record_mode="none").use_cassette(str(CASSETE), allow_playback_repeats=False)


def test_coleta_grava_os_quatro_arquivos_com_hash_do_bruto_real(tmp_path, monkeypatch, manifesto, caplog):
    monkeypatch.setenv("TCG_USER_AGENT", "colecao-dri/teste")

    with _cassete() as cassete, caplog.at_level(logging.INFO):
        codigo = coleta.executar(tmp_path, agora=AGORA)

    assert codigo == coleta.SUCESSO
    assert cassete.all_played
    assert cassete.play_count == 4
    assert "coleta encerrada: 4 arquivos gravados; requisicoes=4" in caplog.text

    gravados = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file())
    assert gravados == sorted(manifesto)
    for chave, esperado in manifesto.items():
        corpo = (tmp_path / chave).read_bytes()
        assert hashlib.sha256(corpo).hexdigest() == esperado["sha256"], chave
        assert sha1_blob(corpo) == esperado["blob"], chave
        assert len(corpo) == esperado["bytes"], chave


def test_requisicao_fora_do_cassete_falha_sem_sair_para_a_rede(monkeypatch):
    monkeypatch.setenv("TCG_USER_AGENT", "colecao-dri/teste")

    with _cassete():
        with pytest.raises(vcr.errors.CannotOverwriteExistingCassetteException):
            requests.get("https://tcgcsv.com/tcgplayer/3/99999/prices", timeout=5)


def test_rede_bloqueada_no_modulo():
    with pytest.raises(RedeBloqueadaError):
        socket.create_connection(("tcgcsv.com", 443), timeout=1)


def _ref_existe() -> bool:
    processo = subprocess.run(
        ["git", "-C", str(RAIZ), "rev-parse", "--verify", "--quiet", f"{REF}^{{commit}}"],
        capture_output=True, check=False,
    )
    return processo.returncode == 0


def test_manifesto_igual_ao_bruto_da_branch(manifesto):
    if not _ref_existe():
        pytest.skip(f"ref {REF} ausente neste clone; conferência com o bruto real pulada")
    blobs = {a.chave: a.blob for a in leitor_branch.listar(RAIZ, REF)}

    for chave, esperado in manifesto.items():
        assert blobs[chave] == esperado["blob"], chave
        corpo = leitor_branch.ler(RAIZ, blobs[chave])
        assert hashlib.sha256(corpo).hexdigest() == esperado["sha256"], chave
