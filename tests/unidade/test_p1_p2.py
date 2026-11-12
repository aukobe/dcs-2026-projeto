"""Testes das métricas P1 e P2 (T-36; RF-15, RF-16).

DuckDB local em memória; rede bloqueada (conftest).
"""

import datetime as dt

import duckdb
import pytest

from tcg.gold.perguntas import p1_rankings, p2_indice

TOL = 1e-9
D1, D2, D3 = dt.date(2026, 11, 1), dt.date(2026, 11, 2), dt.date(2026, 11, 3)
COT = {D1: 5.00, D2: 5.10, D3: 5.25}
GID = 24269


def _con():
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE fato (data DATE, product_id INTEGER, group_id INTEGER, acabamento VARCHAR, "
        "market_price DOUBLE, cotacao_aplicada DOUBLE, market_price_brl DOUBLE)"
    )
    con.execute(
        "CREATE TABLE dim_produto (group_id INTEGER, product_id INTEGER, nome VARCHAR, "
        "tipo_produto VARCHAR, raridade VARCHAR, numero VARCHAR, image_url VARCHAR, url VARCHAR)"
    )
    return con


def _produto(con, pid, tipo="carta", raridade="Rare", group_id=GID):
    numero = None if tipo == "selado" else f"{pid:03d}/182"
    con.execute(
        "INSERT INTO dim_produto VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [group_id, pid, f"Produto {pid}", tipo, raridade, numero,
         f"https://img/{pid}.jpg", f"https://tcg/{pid}"],
    )


def _precos(con, pid, por_dia, acabamento="Normal", group_id=GID):
    for dia, usd in por_dia.items():
        con.execute(
            "INSERT INTO fato VALUES (?, ?, ?, ?, ?, ?, ?)",
            [dia, pid, group_id, acabamento, usd, COT[dia], usd * COT[dia]],
        )


def _linhas(rel):
    return [dict(zip(rel.columns, r)) for r in rel.fetchall()]


# ---------------------------------------------------------------- P1


def test_p1_dois_rankings_de_dez_sem_code_card_e_sem_item_de_90_centavos():
    con = _con()
    for pid in range(1, 15):  # 14 cartas que sobem
        _produto(con, pid)
        _precos(con, pid, {D1: 10.0, D2: 11.0, D3: 10.0 + pid})
    for pid in range(101, 114):  # 13 cartas que caem
        _produto(con, pid)
        _precos(con, pid, {D1: 50.0, D3: 50.0 - (pid - 100)})
    _produto(con, 500, raridade="Code Card")  # maior alta, mas Code Card
    _precos(con, 500, {D1: 2.0, D3: 200.0})
    _produto(con, 501)  # US$ 0,90 no primeiro dia, maior alta
    _precos(con, 501, {D1: 0.90, D3: 90.0})
    _produto(con, 502, tipo="selado", raridade=None)  # selado não entra na P1
    _precos(con, 502, {D1: 100.0, D3: 300.0})

    alta, queda = p1_rankings(con, "fato", "dim_produto")
    alta, queda = _linhas(alta), _linhas(queda)

    assert len(alta) == 10 and len(queda) == 10
    ids = {r["product_id"] for r in alta + queda}
    assert not ids & {500, 501, 502}
    assert [r["product_id"] for r in alta] == list(range(14, 4, -1))
    assert [r["product_id"] for r in queda] == list(range(113, 103, -1))
    assert all(r["r_brl"] > 0 for r in alta) and all(r["r_brl"] < 0 for r in queda)
    for r in alta + queda:
        assert r["image_url"] == f"https://img/{r['product_id']}.jpg"
        assert r["brl_inicial"] == pytest.approx(r["usd_inicial"] * COT[D1], abs=TOL)
        assert r["brl_final"] == pytest.approx(r["usd_final"] * COT[D3], abs=TOL)
        assert r["r_usd"] + r["r_cambio"] + r["r_cruzado"] == pytest.approx(r["r_brl"], abs=TOL)


def test_p1_menos_de_dez_itens_e_item_sem_ultimo_dia_fora():
    con = _con()
    _produto(con, 1)
    _precos(con, 1, {D1: 10.0, D3: 12.0})
    _produto(con, 2)
    _precos(con, 2, {D1: 10.0, D3: 8.0})
    _produto(con, 3)
    _precos(con, 3, {D1: 10.0, D2: 30.0})  # sem preço no último dia
    _produto(con, 4)  # r_brl > 0 só por câmbio: entra na alta
    _precos(con, 4, {D1: 10.0, D3: 10.0})

    alta, queda = map(_linhas, p1_rankings(con, "fato", "dim_produto"))

    assert [r["product_id"] for r in alta] == [1, 4]
    assert [r["product_id"] for r in queda] == [2]


def test_p1_preco_minimo_estritamente_maior():
    con = _con()
    for pid, usd in ((1, 1.00), (2, 1.01), (3, 5.00), (4, 5.01)):
        _produto(con, pid)
        _precos(con, pid, {D1: usd, D3: usd * 2})

    alta, _ = p1_rankings(con, "fato", "dim_produto")
    assert {r["product_id"] for r in _linhas(alta)} == {2, 3, 4}

    alta5, _ = p1_rankings(con, "fato", "dim_produto", preco_minimo_usd=5)
    assert {r["product_id"] for r in _linhas(alta5)} == {4}


def test_p1_so_a_colecao_pedida():
    con = _con()
    _produto(con, 1)
    _precos(con, 1, {D1: 10.0, D3: 20.0})
    _produto(con, 1, group_id=99999)
    _precos(con, 1, {D1: 10.0, D3: 40.0}, group_id=99999)

    alta, _ = p1_rankings(con, "fato", "dim_produto")
    linhas = _linhas(alta)
    assert [(r["group_id"], r["usd_final"]) for r in linhas] == [(GID, 20.0)]


# ---------------------------------------------------------------- P2


def _cenario_p2(con):
    _produto(con, 10, tipo="selado", raridade=None)
    _precos(con, 10, {D1: 100.0, D2: 110.0, D3: 120.0})
    _produto(con, 11, tipo="selado", raridade=None)
    _precos(con, 11, {D1: 200.0, D2: 200.0, D3: 180.0})
    _produto(con, 20, raridade="Double Rare")
    _precos(con, 20, {D1: 5.0, D2: 6.0, D3: 7.0})
    _produto(con, 21, raridade="Ultra Rare")
    _precos(con, 21, {D1: 15.0, D2: 14.0, D3: 13.0}, acabamento="Holofoil")
    _produto(con, 22, raridade="Special Illustration Rare")
    _precos(con, 22, {D1: 80.0, D2: 100.0, D3: 120.0})
    _produto(con, 30, raridade="Rare")  # fora da lista: não entra na soma
    _precos(con, 30, {D1: 1000.0, D2: 5000.0, D3: 1.0})
    _produto(con, 31, raridade="Code Card")
    _precos(con, 31, {D1: 0.5, D2: 0.5, D3: 0.5})


def test_p2_series_valem_100_no_primeiro_dia_e_rare_fica_fora():
    con = _con()
    _cenario_p2(con)

    linhas = _linhas(p2_indice(con, "fato", "dim_produto"))

    assert [r["data"] for r in linhas] == [D1, D2, D3]
    assert linhas[0]["indice_selados"] == pytest.approx(100, abs=TOL)
    assert linhas[0]["indice_double_rare_mais"] == pytest.approx(100, abs=TOL)

    medias = [150.0, 155.0, 150.0]
    somas = [100.0, 120.0, 140.0]
    for r, media, soma, dia in zip(linhas, medias, somas, (D1, D2, D3)):
        assert r["media_selados"] == pytest.approx(media * COT[dia], abs=TOL)
        assert r["soma_double_rare_mais"] == pytest.approx(soma * COT[dia], abs=TOL)
        assert r["indice_selados"] == pytest.approx(
            100 * media * COT[dia] / (150.0 * COT[D1]), abs=TOL)
        assert r["indice_double_rare_mais"] == pytest.approx(
            100 * soma * COT[dia] / (100.0 * COT[D1]), abs=TOL)
        assert r["itens_selados"] == 2
        assert r["itens_double_rare_mais"] == 3


def test_p2_em_dolar():
    con = _con()
    _cenario_p2(con)

    linhas = _linhas(p2_indice(con, "fato", "dim_produto", coluna="market_price"))

    assert [r["indice_selados"] for r in linhas] == pytest.approx([100, 155 / 1.5, 100])
    assert [r["indice_double_rare_mais"] for r in linhas] == pytest.approx([100, 120, 140])


def test_p2_double_rare_cara_sem_preco_no_dia_2_sai_da_cesta_e_nao_derruba_o_indice():
    con = _con()
    _cenario_p2(con)
    _produto(con, 23, raridade="Double Rare")
    _precos(con, 23, {D1: 900.0, D3: 950.0})  # sem preço no dia 2
    _produto(con, 12, tipo="selado", raridade=None)
    _precos(con, 12, {D2: 999.0, D3: 999.0})  # sem preço no dia 1

    linhas = _linhas(p2_indice(con, "fato", "dim_produto", coluna="market_price"))

    assert [r["indice_double_rare_mais"] for r in linhas] == pytest.approx([100, 120, 140])
    assert [r["indice_selados"] for r in linhas] == pytest.approx([100, 155 / 1.5, 100])
    assert all(r["itens_double_rare_mais"] == 3 for r in linhas)
    assert all(r["itens_selados"] == 2 for r in linhas)


def test_p2_coluna_invalida():
    con = _con()
    with pytest.raises(ValueError):
        p2_indice(con, "fato", "dim_produto", coluna="low_price")
