"""Reprocessamento com bucket falso em memória (T-33; RF-13, RNF-03, ADR-004).

Sem rede e sem MinIO: os construtores da silver e da gold são substituídos por
dublês que só registram a chamada. Confere a trava de confirmação, que só as
chaves derivadas da DRI chegam ao `remove_object` e que a exclusão vem antes
da reconstrução.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import pytest

from tcg import reprocessar as modulo
from tcg.config import ler_colecao
from tcg.lake.guarda_prefixo import chave_permitida

BUCKET = "tcg"
ENDPOINT = "minio.exemplo:9000"
RAIZ = Path(__file__).resolve().parents[2]

DERIVADAS_DRI = [
    "silver/preco_diario/group_id=24269/data=2026-11-03/preco.parquet",
    "silver/preco_diario/group_id=24269/data=2020-01-01/preco.parquet",  # órfã
    "silver/produto/group_id=24269/produto.parquet",
    "silver/quarentena/group_id=24269/quarentena.parquet",
    "gold/group_id=24269/fato_preco_diario.parquet",
    "gold/group_id=24269/tabela_antiga.parquet",  # órfã
    "gold_turma/carteira/group_id=24269/carteira.parquet",
]
INTOCAVEIS = [
    "raw/tcgplayer/group_id=24269/data=2026-11-03/prices.json",
    "raw/bcb_ptax/group_id=24269/data=2026-11-03/cotacao.json",
    "silver/preco_diario/group_id=99999/data=2026-11-03/preco.parquet",
    "silver/preco_diario/group_id=242690/preco.parquet",
    "gold/group_id=99999/fato_preco_diario.parquet",
    "gold_turma/carteira/group_id=99999/carteira.parquet",
    "gold_turma/outra/group_id=24269/carteira.parquet",
]


class _Objeto:
    def __init__(self, nome):
        self.object_name = nome


class BucketFalso:
    """Imita list_objects e remove_object do SDK e registra a ordem das chamadas."""

    def __init__(self, chaves, eventos):
        self.objetos = set(chaves)
        self.eventos = eventos
        self.removidas: list[str] = []

    def list_objects(self, bucket_name, prefix="", recursive=False):
        assert bucket_name == BUCKET and recursive
        return [_Objeto(k) for k in sorted(self.objetos) if k.startswith(prefix)]

    def remove_object(self, bucket_name, object_name):
        assert bucket_name == BUCKET
        self.eventos.append(("remove_object", object_name))
        self.removidas.append(object_name)
        self.objetos.discard(object_name)


class ConexaoFalsa:
    def __init__(self, eventos):
        self.eventos = eventos

    def close(self):
        self.eventos.append(("duckdb_fechado", None))


@pytest.fixture
def cenario(monkeypatch):
    eventos: list[tuple[str, str | None]] = []
    bucket = BucketFalso(DERIVADAS_DRI + INTOCAVEIS, eventos)
    monkeypatch.setattr(modulo, "construir_silver", lambda c, b, col: eventos.append(("silver", None)) or "S")
    monkeypatch.setattr(modulo, "construir_gold", lambda c, con, b: eventos.append(("gold", None)) or "G")

    def abrir_duckdb():
        eventos.append(("duckdb_aberto", None))
        return ConexaoFalsa(eventos)

    def executar(confirmacao):
        return modulo.reprocessar(bucket, BUCKET, ler_colecao(), confirmacao, ENDPOINT, abrir_duckdb)

    return bucket, eventos, executar


def test_listar_derivados_so_traz_prefixos_da_dri(cenario):
    bucket, _, _ = cenario
    alvos = modulo.listar_derivados(bucket, BUCKET)
    assert alvos == {
        "silver/*/group_id=24269/": sorted(DERIVADAS_DRI[:4]),
        "gold/group_id=24269/": sorted(DERIVADAS_DRI[4:6]),
        "gold_turma/carteira/group_id=24269/": [DERIVADAS_DRI[6]],
    }
    assert all(not chave_permitida(c) for c in INTOCAVEIS)


@pytest.mark.parametrize("confirmacao", [None, "", "   ", "sim", "99999", "242690", "2426", "24269x"])
def test_sem_confirmacao_valida_nada_e_apagado(cenario, caplog, confirmacao):
    bucket, eventos, executar = cenario
    antes = set(bucket.objetos)
    with caplog.at_level(logging.WARNING, logger="tcg.reprocessar"):
        r = executar(confirmacao)

    assert r.confirmado is False and r.apagadas == []
    assert eventos == [], "sem confirmação: nenhum remove_object, construtor ou DuckDB"
    assert bucket.objetos == antes and bucket.removidas == []
    texto = caplog.text
    assert "nada foi apagado" in texto
    assert f"endpoint={ENDPOINT} bucket={BUCKET}" in texto
    assert "apagaria 4 chave(s) em silver/*/group_id=24269/" in texto
    assert "apagaria 2 chave(s) em gold/group_id=24269/" in texto
    assert "apagaria 1 chave(s) em gold_turma/carteira/group_id=24269/" in texto
    assert "total que seria apagado: 7 chave(s)" in texto


def test_main_sem_confirmacao_sai_com_codigo_4(monkeypatch):
    eventos: list = []
    bucket = BucketFalso(DERIVADAS_DRI + INTOCAVEIS, eventos)
    for nome, valor in {
        "GROUP_ID": "24269", "MINIO_SECURE": "false", "MINIO_ENDPOINT": ENDPOINT,
        "MINIO_BUCKET": BUCKET, "MINIO_ACCESS_KEY": "ficticio", "MINIO_SECRET_KEY": "ficticio",
    }.items():
        monkeypatch.setenv(nome, valor)
    monkeypatch.setenv("CONFIRMAR", "99999")
    monkeypatch.setattr(modulo, "criar_cliente", lambda config: bucket)
    monkeypatch.setattr(modulo, "conectar", lambda config: pytest.fail("DuckDB aberto sem confirmação"))

    assert modulo.main([]) == modulo.SEM_CONFIRMACAO
    assert bucket.removidas == [] and eventos == []


def test_com_confirmacao_apaga_so_derivadas_e_reconstroi(cenario, caplog):
    bucket, eventos, executar = cenario
    with caplog.at_level(logging.INFO):
        r = executar("24269")

    assert r.confirmado is True
    assert sorted(r.apagadas) == sorted(DERIVADAS_DRI)
    assert sorted(bucket.removidas) == sorted(DERIVADAS_DRI)
    assert bucket.objetos == set(INTOCAVEIS), "raw/ e outros group_ids continuam lá"
    # exclusão inteira antes da reconstrução; silver antes da gold; DuckDB fechado no fim
    nomes = [e for e, _ in eventos]
    assert nomes == ["remove_object"] * 7 + ["silver", "duckdb_aberto", "gold", "duckdb_fechado"]
    assert (r.silver, r.gold) == ("S", "G")
    texto = caplog.text
    assert "reprocessamento iniciado" in texto and "reprocessamento concluído" in texto
    for chave in DERIVADAS_DRI:
        assert f"objeto apagado: {BUCKET}/{chave}" in texto


def test_confirmacao_com_espacos_e_aceita(cenario):
    _, _, executar = cenario
    assert executar(" 24269 ").confirmado is True


def test_makefile_passa_confirmar_depois_do_env():
    receita = subprocess.run(
        ["make", "-n", "reprocessar", "CONFIRMAR=24269"], cwd=RAIZ, capture_output=True, text=True,
    )
    # -n só imprime a receita; o .env não é lido nem executado
    linha = [l for l in receita.stdout.splitlines() if "tcg.reprocessar" in l]
    if receita.returncode != 0 and not linha:
        pytest.skip("make -n indisponível neste ambiente")
    assert len(linha) == 1
    assert linha[0].index(". ./.env") < linha[0].index('CONFIRMAR="24269"') < linha[0].index("-m tcg.reprocessar")
