"""Testes das métricas P3 e P4 (T-37; RF-17, RF-18).

DuckDB local em memória; rede bloqueada (conftest).
"""

import datetime as dt

import duckdb
import pytest

from tcg.gold.perguntas import p3_indice, p4_concentracao

TOL = 1e-9
D1, D2, D3, D4, D5 = (dt.date(2026, 11, d) for d in range(1, 6))
COT = {D1: 5.00, D2: 5.10, D3: 5.20, D4: 5.40, D5: 5.30}
GID, OUTRA = 24269, 99999


def _con():
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE fato (data DATE, product_id INTEGER, group_id INTEGER, acabamento VARCHAR, "
        "market_price DOUBLE, cotacao_aplicada DOUBLE, market_price_brl DOUBLE)"
    )
    con.execute(
        "CREATE TABLE dim_produto (group_id INTEGER, product_id INTEGER, nome VARCHAR, "
        "tipo_produto VARCHAR, raridade VARCHAR)"
    )
    con.execute(
        "CREATE TABLE fato_cambio (data DATE, cotacao_compra DOUBLE, cotacao_venda DOUBLE, "
        "data_ptax DATE, cdi_taxa_dia DOUBLE, cdi_pendente BOOLEAN)"
    )
    for dia, cot in COT.items():
        con.execute(
            "INSERT INTO fato_cambio VALUES (?, ?, ?, ?, 0.0, false)", [dia, cot - 0.01, cot, dia]
        )
    return con


def _produto(con, pid, tipo="carta", raridade="Rare", group_id=GID):
    con.execute(
        "INSERT INTO dim_produto VALUES (?, ?, ?, ?, ?)",
        [group_id, pid, f"Produto {pid}", tipo, raridade],
    )


def _precos(con, pid, por_dia, acabamento="Normal", group_id=GID):
    for dia, usd in por_dia.items():
        con.execute(
            "INSERT INTO fato VALUES (?, ?, ?, ?, ?, ?, ?)",
            [dia, pid, group_id, acabamento, usd, COT[dia], usd * COT[dia]],
        )


def _linhas(rel):
    return [dict(zip(rel.columns, r)) for r in rel.fetchall()]


def _serie(linhas, serie):
    return [r for r in linhas if r["serie"] == serie]


# ---------------------------------------------------------------- P3


def _cenario_rf17(con):
    """DRI a partir de 01/11 (até 04/11); outra coleção a partir de 03/11 (até 05/11)."""
    _produto(con, 1)
    _precos(con, 1, {D1: 10.0, D2: 11.0, D3: 12.0, D4: 13.0})
    _produto(con, 2, raridade="Ultra Rare")
    _precos(con, 2, {D1: 20.0, D2: 20.0, D3: 22.0, D4: 24.0}, acabamento="Holofoil")
    _produto(con, 3, raridade="Code Card")  # fora
    _precos(con, 3, {D1: 1.0, D2: 1.0, D3: 500.0, D4: 1.0})
    _produto(con, 4, tipo="selado", raridade=None)  # fora
    _precos(con, 4, {D1: 100.0, D2: 100.0, D3: 100.0, D4: 900.0})
    _produto(con, 1, group_id=OUTRA)  # mesmo product_id em outra coleção
    _precos(con, 1, {D3: 5.0, D4: 6.0, D5: 7.0}, group_id=OUTRA)


def test_p3_todas_as_series_valem_100_no_primeiro_dia_comum_e_dri_destacada():
    con = _con()
    _cenario_rf17(con)

    linhas = _linhas(p3_indice(con, "fato", "dim_produto", "fato_cambio"))

    assert {r["serie"] for r in linhas} == {str(GID), str(OUTRA), "PTAX"}
    assert min(r["data"] for r in linhas) == D3
    for serie in (str(GID), str(OUTRA), "PTAX"):
        primeira = _serie(linhas, serie)[0]
        assert primeira["data"] == D3
        assert primeira["indice"] == pytest.approx(100, abs=TOL)

    dri = _serie(linhas, str(GID))
    assert [r["data"] for r in dri] == [D3, D4]
    assert dri[1]["valor"] == pytest.approx((13.0 + 24.0) * COT[D4], abs=TOL)
    assert dri[1]["indice"] == pytest.approx(
        100 * (37.0 * COT[D4]) / (34.0 * COT[D3]), abs=TOL)
    assert all(r["itens_cesta"] == 2 and r["destaque"] for r in dri)

    outra = _serie(linhas, str(OUTRA))
    assert [r["data"] for r in outra] == [D3, D4, D5]
    assert outra[2]["indice"] == pytest.approx(100 * 7.0 * COT[D5] / (5.0 * COT[D3]), abs=TOL)
    assert all(r["itens_cesta"] == 1 and not r["destaque"] for r in outra)

    ptax = _serie(linhas, "PTAX")
    assert [r["data"] for r in ptax] == [D3, D4, D5]
    assert [r["indice"] for r in ptax] == pytest.approx(
        [100, 100 * COT[D4] / COT[D3], 100 * COT[D5] / COT[D3]])
    assert all(r["group_id"] is None and r["itens_cesta"] is None and not r["destaque"]
               for r in ptax)


def test_p3_cesta_fixa_por_colecao_no_periodo_comparado():
    con = _con()
    _cenario_rf17(con)
    _produto(con, 5, raridade="Hyper Rare")  # cara, sem preço em 04/11: sai da cesta
    _precos(con, 5, {D1: 900.0, D2: 900.0, D3: 1000.0})
    _produto(con, 6)  # sem preço em 01/11 e 02/11, antes da data base: entra
    _precos(con, 6, {D3: 2.0, D4: 3.0})
    _produto(con, 2, group_id=OUTRA)  # sem preço em 05/11 na outra coleção: sai
    _precos(con, 2, {D3: 50.0, D4: 60.0}, group_id=OUTRA)

    linhas = _linhas(p3_indice(con, "fato", "dim_produto", "fato_cambio", coluna="market_price"))

    dri = _serie(linhas, str(GID))
    assert [r["valor"] for r in dri] == pytest.approx([36.0, 40.0])
    assert [r["indice"] for r in dri] == pytest.approx([100, 100 * 40 / 36])
    assert all(r["itens_cesta"] == 3 for r in dri)
    outra = _serie(linhas, str(OUTRA))
    assert [r["valor"] for r in outra] == pytest.approx([5.0, 6.0, 7.0])
    assert all(r["itens_cesta"] == 1 for r in outra)


def test_p3_so_com_a_dri():
    con = _con()
    _produto(con, 1)
    _precos(con, 1, {D1: 10.0, D2: 12.0})

    linhas = _linhas(p3_indice(con, "fato", "dim_produto", "fato_cambio"))

    assert {r["serie"] for r in linhas} == {str(GID), "PTAX"}
    assert [r["indice"] for r in _serie(linhas, str(GID))] == pytest.approx(
        [100, 100 * 12 * COT[D2] / (10 * COT[D1])])
    assert [r["data"] for r in _serie(linhas, "PTAX")] == [D1, D2]


def test_p3_coluna_invalida():
    con = _con()
    with pytest.raises(ValueError):
        p3_indice(con, "fato", "dim_produto", "fato_cambio", coluna="low_price")


# ---------------------------------------------------------------- P4


def _cenario_rf18(con, group_id=GID):
    """No último dia (02/11), cinco cartas de R$ 50, 20, 15, 10 e 5."""
    itens = (
        (1, "Special Illustration Rare", 50.0),
        (2, "Ultra Rare", 20.0),
        (3, "Ultra Rare", 15.0),
        (4, "Rare", 10.0),
        (5, None, 5.0),
    )
    for pid, raridade, brl in itens:
        _produto(con, pid, raridade=raridade, group_id=group_id)
        _precos(con, pid, {D1: 1.0, D2: brl / COT[D2]}, group_id=group_id)
    _produto(con, 6, raridade="Code Card", group_id=group_id)  # fora
    _precos(con, 6, {D2: 1000.0}, group_id=group_id)
    _produto(con, 7, tipo="selado", raridade=None, group_id=group_id)  # fora
    _precos(con, 7, {D2: 1000.0}, group_id=group_id)
    _produto(con, 8, group_id=group_id)  # só no primeiro dia: fora
    _precos(con, 8, {D1: 1000.0}, group_id=group_id)


def test_p4_tres_itens_somam_80_e_participacoes_somam_100():
    con = _con()
    _cenario_rf18(con)

    participacao, concentracao = map(_linhas, p4_concentracao(con, "fato", "dim_produto"))

    assert concentracao == [pytest.approx({
        "group_id": GID, "data": D2, "valor_total": 100.0, "itens_total": 5, "itens_80": 3,
    })]
    assert sum(r["participacao"] for r in participacao) == pytest.approx(1, abs=TOL)
    assert {r["raridade"]: r["participacao"] for r in participacao} == pytest.approx({
        "Special Illustration Rare": 0.50, "Ultra Rare": 0.35, "Rare": 0.10, "Sem raridade": 0.05,
    })
    assert {r["raridade"]: r["itens"] for r in participacao}["Ultra Rare"] == 2
    assert all(r["data"] == D2 for r in participacao)


def test_p4_ultimo_dia_de_cada_colecao_calculado_separadamente():
    con = _con()
    _cenario_rf18(con)
    _produto(con, 1, raridade="Rare", group_id=OUTRA)
    _precos(con, 1, {D3: 10.0, D4: 70.0}, group_id=OUTRA)
    _produto(con, 2, raridade="Rare", group_id=OUTRA)
    _precos(con, 2, {D3: 90.0, D4: 30.0}, group_id=OUTRA)

    participacao, concentracao = map(_linhas, p4_concentracao(con, "fato", "dim_produto"))

    por_colecao = {r["group_id"]: r for r in concentracao}
    assert por_colecao[GID]["data"] == D2 and por_colecao[GID]["itens_80"] == 3
    assert por_colecao[OUTRA]["data"] == D4
    assert por_colecao[OUTRA]["valor_total"] == pytest.approx(100 * COT[D4])
    assert por_colecao[OUTRA]["itens_80"] == 2  # 70% não chega a 80%; 70% + 30% sim
    for gid in (GID, OUTRA):
        assert sum(r["participacao"] for r in participacao if r["group_id"] == gid) == \
            pytest.approx(1, abs=TOL)
