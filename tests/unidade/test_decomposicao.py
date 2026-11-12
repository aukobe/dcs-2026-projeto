"""Testes da decomposição da variação em reais (T-35; RF-15, RNF-02).

Funções puras e DuckDB local em memória; rede bloqueada (conftest).
"""

import datetime as dt
import random

import duckdb
import pytest

from tcg.gold.perguntas import decompor, decomposicao_por_item

TOL = 1e-9
D = dt.date


def _identidades(r_brl, r_usd, r_cambio, r_cruzado):
    assert abs((r_usd + r_cambio + r_cruzado) - r_brl) <= TOL
    assert abs((1 + r_brl) - (1 + r_usd) * (1 + r_cambio)) <= TOL


def test_caso_conhecido_10_para_12_ptax_5_para_5_50():
    d = decompor(10.0, 12.0, 5.00, 5.50)
    assert d.r_usd == pytest.approx(0.20, abs=TOL)
    assert d.r_cambio == pytest.approx(0.10, abs=TOL)
    assert d.r_cruzado == pytest.approx(0.02, abs=TOL)
    assert d.r_brl == pytest.approx(0.32, abs=TOL)


def test_caso_100_para_110_ptax_5_para_5_25():
    d = decompor(100.0, 110.0, 5.00, 5.25)
    assert d.r_usd == pytest.approx(0.10, abs=TOL)
    assert d.r_cambio == pytest.approx(0.05, abs=TOL)
    assert d.r_cruzado == pytest.approx(0.005, abs=TOL)
    assert d.r_brl == pytest.approx(0.155, abs=TOL)
    _identidades(d.r_brl, d.r_usd, d.r_cambio, d.r_cruzado)


def test_identidades_em_casos_gerados():
    rng = random.Random(35)
    for _ in range(1000):
        usd_i = rng.uniform(0.01, 5000.0)
        usd_f = rng.uniform(0.01, 5000.0)
        cot_i = rng.uniform(3.0, 8.0)
        cot_f = rng.uniform(3.0, 8.0)
        d = decompor(usd_i, usd_f, cot_i, cot_f)
        _identidades(d.r_brl, d.r_usd, d.r_cambio, d.r_cruzado)


@pytest.mark.parametrize(
    "args",
    [(0.0, 1.0, 5.0, 5.0), (1.0, -1.0, 5.0, 5.0), (1.0, 1.0, 0.0, 5.0), (1.0, 1.0, 5.0, -5.0)],
)
def test_preco_ou_cotacao_nao_positivos_levantam_erro(args):
    with pytest.raises(ValueError):
        decompor(*args)


def test_sql_sobre_fato_em_memoria():
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE fato (data DATE, product_id INTEGER, group_id INTEGER, acabamento VARCHAR, "
        "market_price DOUBLE, cotacao_aplicada DOUBLE, market_price_brl DOUBLE)"
    )
    rng = random.Random(3535)
    ini, meio, fim = D(2026, 11, 1), D(2026, 11, 2), D(2026, 11, 3)
    cot = {ini: 5.00, meio: 5.10, fim: 5.25}
    linhas = []
    esperados = {}
    for pid in range(1, 51):
        usd_i, usd_f = rng.uniform(0.5, 500), rng.uniform(0.5, 500)
        for dia, usd in ((ini, usd_i), (meio, (usd_i + usd_f) / 2), (fim, usd_f)):
            linhas.append((dia, pid, 24269, "Normal", usd, cot[dia], usd * cot[dia]))
        esperados[pid] = decompor(usd_i, usd_f, cot[ini], cot[fim])
    linhas.append((ini, 900, 24269, "Holofoil", 10.0, cot[ini], 50.0))  # sem último dia
    linhas.append((fim, 901, 24269, "Holofoil", 10.0, cot[fim], 52.5))  # sem primeiro dia
    con.executemany("INSERT INTO fato VALUES (?, ?, ?, ?, ?, ?, ?)", linhas)

    rel = decomposicao_por_item(con, "fato", ini, fim)
    cols = rel.columns
    res = [dict(zip(cols, r)) for r in rel.fetchall()]

    assert {r["product_id"] for r in res} == set(range(1, 51))
    for r in res:
        _identidades(r["r_brl"], r["r_usd"], r["r_cambio"], r["r_cruzado"])
        e = esperados[r["product_id"]]
        assert r["r_brl"] == pytest.approx(e.r_brl, abs=TOL)
        assert r["r_usd"] == pytest.approx(e.r_usd, abs=TOL)
        assert r["r_cambio"] == pytest.approx(e.r_cambio, abs=TOL)
        assert r["r_cruzado"] == pytest.approx(e.r_cruzado, abs=TOL)
        assert r["brl_final"] / r["brl_inicial"] - 1 == pytest.approx(r["r_brl"], abs=TOL)
