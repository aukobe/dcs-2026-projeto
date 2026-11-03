"""Testes da configuração do logging (T-03; RNF-08)."""

import io
import logging
import re
import time

import pytest

from tcg.log import configurar_log

CHAVE_FICTICIA = "chave-ficticia-AKIA123"
SEGREDO_FICTICIO = "segredo-ficticio-xyz789"


@pytest.fixture
def saida(monkeypatch):
    monkeypatch.setenv("MINIO_ACCESS_KEY", CHAVE_FICTICIA)
    monkeypatch.setenv("MINIO_SECRET_KEY", SEGREDO_FICTICIO)
    fluxo = io.StringIO()
    handler = configurar_log(fluxo=fluxo)
    yield fluxo
    logging.getLogger().removeHandler(handler)


def test_formato_utc_nivel_e_componente(saida, monkeypatch):
    monkeypatch.setenv("TZ", "America/Sao_Paulo")
    time.tzset()
    try:
        # 2026-11-03 20:30:00 UTC = 17:30 em São Paulo
        monkeypatch.setattr(time, "time", lambda: 1793737800.0)
        monkeypatch.setattr(time, "time_ns", lambda: 1793737800 * 10**9)
        logging.getLogger("tcg.coleta").info("coleta iniciada")
    finally:
        monkeypatch.delenv("TZ")
        time.tzset()
    linha = saida.getvalue().strip()
    assert linha == "2026-11-03T20:30:00Z INFO tcg.coleta: coleta iniciada"


def test_formato_geral(saida):
    logging.getLogger("tcg.sync").warning("chave existente recusada")
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z WARNING tcg\.sync: chave existente recusada\n",
        saida.getvalue(),
    )


def test_credenciais_nao_aparecem_no_log(saida):
    log = logging.getLogger("tcg.lake")
    log.info("conectando com %s e %s", CHAVE_FICTICIA, SEGREDO_FICTICIO)
    log.error(f"falha: secret={SEGREDO_FICTICIO}")
    try:
        raise RuntimeError(f"erro com {CHAVE_FICTICIA}")
    except RuntimeError:
        log.exception("exceção capturada")
    texto = saida.getvalue()
    assert CHAVE_FICTICIA not in texto
    assert SEGREDO_FICTICIO not in texto
    assert texto.count("***") == 4
    assert "RuntimeError" in texto


def test_sem_credenciais_no_ambiente_mensagem_intacta(monkeypatch):
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
    fluxo = io.StringIO()
    handler = configurar_log(fluxo=fluxo)
    try:
        logging.getLogger("tcg").info("total %d", 3)
    finally:
        logging.getLogger().removeHandler(handler)
    assert fluxo.getvalue().endswith("INFO tcg: total 3\n")
