"""Testes da métrica P5: retorno contra volatilidade (T-38; RF-19).

DuckDB local em memória; rede bloqueada (conftest).
"""

import datetime as dt
import statistics

import duckdb
import pytest

from tcg.gold.perguntas import p5_retorno_volatilidade

TOL = 1e-9
D1, D2, D3, D4, D5 = (dt.date(2026, 11, d) for d in range(1, 6))
GID, OUTRA = 24269, 99999


def _con():
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE fato (data DATE, product_id INTEGER, group_id INTEGER, acabamento VARCHAR, "
        "market_price DOUBLE, cotacao_aplicada DOUBLE, market_price_brl DOUBLE)"
    )
    con.execute(
        "CREATE TABLE dim_produto (group_id INTEGER, product_id INTEGER, nome VARCHAR, "
        "tipo_produto VARCHAR, raridade VARCHAR, image_url VARCHAR, url VARCHAR)"
    )
    return con


def _produto(con, pid, tipo="carta", raridade="Rare", group_id=GID):
    con.execute(
        "INSERT INTO dim_produto VALUES (?, ?, ?, ?, ?, ?, ?)",
        [group_id, pid, f"Produto {pid}", tipo, raridade, None, None],
    )


def _precos(con, pid, por_dia, acabamento="Normal", group_id=GID, cotacao=5.0):
    for dia, usd in por_dia.items():
        con.execute(
            "INSERT INTO fato VALUES (?, ?, ?, ?, ?, ?, ?)",
            [dia, pid, group_id, acabamento, usd, cotacao, usd * cotacao],
        )


def _linhas(rel):
    return {(r[0], r[1], r[2]): dict(zip(rel.columns, r)) for r in rel.fetchall()}


@pytest.mark.parametrize("coluna", ["market_price", "market_price_brl"])
def test_p5_retorno_e_volatilidade_tres_dias_seguidos(coluna):
    con = _con()
    _produto(con, 1)
    _precos(con, 1, {D1: 10.0, D2: 11.0, D3: 9.9})

    linhas = _linhas(p5_retorno_volatilidade(con, "fato", "dim_produto", coluna=coluna))

    item = linhas[(GID, 1, "Normal")]
    assert item["retorno"] == pytest.approx(-0.01, abs=TOL)
    assert item["volatilidade"] == pytest.approx(statistics.stdev([0.10, -0.10]), abs=TOL)
    assert item["n_retornos"] == 2
    assert (item["data_inicial"], item["data_final"]) == (D1, D3)


def test_p5_descarta_retorno_que_atravessa_lacuna():
    con = _con()
    # 03/11 sem coleta; janela da coleção de 01/11 a 04/11.
    _produto(con, 1)
    _precos(con, 1, {D1: 10.0, D2: 11.0, D4: 9.9})
    # Item com lacuna própria em 03/11 (a coleção tem 03/11 por causa do item 3).
    _produto(con, 2)
    _precos(con, 2, {D1: 10.0, D2: 12.0, D4: 6.0, D5: 6.6})
    _produto(con, 3)
    _precos(con, 3, {D1: 10.0, D2: 10.0, D3: 10.0, D4: 10.0, D5: 10.0})

    linhas = _linhas(p5_retorno_volatilidade(con, "fato", "dim_produto", coluna="market_price"))

    # A janela da coleção vai a 05/11: o item 1 não tem preço no último dia e fica fora.
    assert (GID, 1, "Normal") not in linhas
    item2 = linhas[(GID, 2, "Normal")]
    assert item2["n_retornos"] == 2  # 01→02 e 04→05; 02→04 atravessa a lacuna
    assert item2["volatilidade"] == pytest.approx(statistics.stdev([0.20, 0.10]), abs=TOL)
    assert item2["retorno"] == pytest.approx(6.6 / 10.0 - 1, abs=TOL)
    assert (item2["data_inicial"], item2["data_final"]) == (D1, D5)


def test_p5_lacuna_de_coleta_so_conta_o_retorno_antes_dela():
    con = _con()
    # Critério do RF-19: 01/11, 02/11 e 04/11, com 03/11 sem coleta.
    _produto(con, 1)
    _precos(con, 1, {D1: 10.0, D2: 11.0, D4: 9.9})

    item = _linhas(p5_retorno_volatilidade(con, "fato", "dim_produto", coluna="market_price"))[
        (GID, 1, "Normal")
    ]

    assert item["n_retornos"] == 1  # só 01/11 → 02/11
    assert item["volatilidade"] is None  # desvio-padrão amostral de um retorno
    assert item["retorno"] == pytest.approx(-0.01, abs=TOL)


def test_p5_item_sem_preco_no_ultimo_dia_da_colecao_fica_fora():
    con = _con()
    _produto(con, 1)
    _precos(con, 1, {D1: 10.0, D2: 11.0, D3: 12.0})
    _produto(con, 2)
    _precos(con, 2, {D1: 10.0, D2: 11.0})  # sem preço em 03/11, último dia da coleção
    _produto(con, 3)
    _precos(con, 3, {D2: 10.0, D3: 11.0})  # sem preço em 01/11, primeiro dia da coleção

    linhas = _linhas(p5_retorno_volatilidade(con, "fato", "dim_produto"))

    assert set(linhas) == {(GID, 1, "Normal")}


def test_p5_filtro_estrito_no_primeiro_dia_e_sem_code_card():
    con = _con()
    _produto(con, 1)
    _precos(con, 1, {D1: 5.00, D2: 6.0})  # igual ao mínimo: fora
    _produto(con, 2)
    _precos(con, 2, {D1: 5.01, D2: 4.0})  # acima no primeiro dia: entra
    _produto(con, 3)
    _precos(con, 3, {D1: 4.0, D2: 50.0})  # abaixo no primeiro dia: fora
    _produto(con, 4, raridade="Code Card")
    _precos(con, 4, {D1: 50.0, D2: 60.0})
    _produto(con, 5, tipo="selado", raridade=None)
    _precos(con, 5, {D1: 150.0, D2: 160.0})

    linhas = _linhas(p5_retorno_volatilidade(con, "fato", "dim_produto"))

    assert set(linhas) == {(GID, 2, "Normal")}
    assert linhas[(GID, 2, "Normal")]["usd_inicial"] == pytest.approx(5.01)
    assert set(linhas) == set(
        _linhas(p5_retorno_volatilidade(con, "fato", "dim_produto", preco_minimo_usd=5))
    )


def test_p5_todas_as_colecoes_com_janela_propria_e_group_id():
    con = _con()
    _produto(con, 1)
    _precos(con, 1, {D1: 10.0, D2: 11.0})
    _produto(con, 1, group_id=OUTRA)  # mesmo product_id em outra coleção
    _precos(con, 1, {D3: 20.0, D4: 22.0, D5: 24.2}, group_id=OUTRA)
    _produto(con, 2)
    _precos(con, 2, {D1: 10.0, D2: 10.0}, acabamento="Holofoil")

    linhas = _linhas(p5_retorno_volatilidade(con, "fato", "dim_produto", coluna="market_price"))

    assert set(linhas) == {(GID, 1, "Normal"), (OUTRA, 1, "Normal"), (GID, 2, "Holofoil")}
    outra = linhas[(OUTRA, 1, "Normal")]
    assert (outra["data_inicial"], outra["data_final"]) == (D3, D5)
    assert outra["retorno"] == pytest.approx(0.21, abs=TOL)
    assert outra["volatilidade"] == pytest.approx(0.0, abs=TOL)


def test_p5_coluna_invalida():
    with pytest.raises(ValueError):
        p5_retorno_volatilidade(_con(), "fato", "dim_produto", coluna="low_price")
