"""Testes da composição das cinco carteiras (T-41; RF-23; ADR-005, ADR-006).

DuckDB local em memória; rede bloqueada (conftest). PTAX de venda 5,00 no
primeiro dia, então preço de compra em reais = 5 × market_price em US$.
"""

import datetime as dt

import duckdb
import pytest

from tcg.gold.carteiras import (
    CARTEIRAS,
    STATUS_REGRA_PENDENTE,
    PendenciaBoosterBox,
    compor_carteiras,
    compor_cesta_raras,
    compor_propria,
    compor_selado,
    ler_primeiro_dia,
    registrar_composicao,
)

GID = 24269
D1 = dt.date(2026, 11, 3)
DIAS_A_MAIS = [D1 + dt.timedelta(days=k) for k in range(1, 11)]
PTAX = 5.0
TOL = 1e-9
BOX = 624679


def _con():
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE fato (data DATE, product_id INTEGER, group_id INTEGER, "
        "acabamento VARCHAR, market_price DOUBLE)"
    )
    con.execute(
        "CREATE TABLE dim_produto (group_id INTEGER, product_id INTEGER, nome VARCHAR, "
        "tipo_produto VARCHAR, raridade VARCHAR, numero VARCHAR, image_url VARCHAR, url VARCHAR)"
    )
    con.execute("CREATE TABLE fato_cambio (data DATE, cotacao_venda DOUBLE)")
    con.execute("INSERT INTO fato_cambio VALUES (?, ?)", [D1, PTAX])
    for k, dia in enumerate(DIAS_A_MAIS, start=1):
        con.execute("INSERT INTO fato_cambio VALUES (?, ?)", [dia, PTAX + 0.1 * k])
    return con


def _produto(con, pid, nome=None, tipo="carta", raridade="Special Illustration Rare"):
    if tipo == "selado":
        raridade = None
    con.execute(
        "INSERT INTO dim_produto VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [GID, pid, nome or f"Produto {pid}", tipo, raridade, None, None, None],
    )


def _preco(con, pid, usd, acabamento="Normal", dia=D1):
    con.execute("INSERT INTO fato VALUES (?, ?, ?, ?, ?)", [dia, pid, GID, acabamento, usd])


def _item(con, pid, usd, nome=None, tipo="carta", raridade="Special Illustration Rare",
          acabamento="Normal"):
    _produto(con, pid, nome, tipo, raridade)
    _preco(con, pid, usd, acabamento)


def _dados(con):
    return ler_primeiro_dia(con, "fato", "dim_produto", "fato_cambio", GID)


def _cenario_base(con):
    """Booster box, Case, Half, ETB, 12 SIR, 6 IR e um Code Card caro."""
    _item(con, BOX, 150.0, "Destined Rivals Booster Box", "selado")          # R$ 750
    _item(con, 700, 900.0, "Destined Rivals Booster Box Case", "selado")     # mais caro, ignorado
    _item(con, 701, 80.0, "Destined Rivals Half Booster Box", "selado")      # R$ 400
    _item(con, 702, 60.0, "Destined Rivals Elite Trainer Box", "selado")     # R$ 300
    for pid in range(1, 13):  # SIR US$ 11 a 22 → R$ 55 a 110
        _item(con, pid, 10.0 + pid, acabamento="Holofoil")
    for pid in range(21, 27):  # IR US$ 1,50 a 9 → R$ 7,50 a 45, abaixo das SIR
        _item(con, pid, 1.5 * (pid - 20), raridade="Illustration Rare", acabamento="Holofoil")
    _item(con, 99, 500.0, raridade="Code Card")


def _ids(comp):
    return [(p.product_id, p.acabamento) for p in comp.posicoes]


# ---------------------------------------------------------------- sem informação do futuro


@pytest.mark.parametrize("regra_propria", [True, False])
def test_composicao_identica_com_primeiro_dia_e_com_dez_dias_a_mais(regra_propria):
    con = _con()
    _cenario_base(con)
    antes = compor_carteiras(_dados(con), regra_propria)

    # Dez dias depois com preços muito diferentes, booster box sem preço e um
    # selado novo caro: nada disso pode mudar a composição.
    _produto(con, 800, "Destined Rivals Booster Bundle", "selado")
    for k, dia in enumerate(DIAS_A_MAIS, start=1):
        for pid, in con.execute("SELECT product_id FROM dim_produto").fetchall():
            if pid == BOX:
                _preco(con, pid, None, dia=dia)
            else:
                _preco(con, pid, 1.0 + k * (pid % 7), "Holofoil", dia=dia)
        _preco(con, 800, 190.0, dia=dia)
    depois = compor_carteiras(_dados(con), regra_propria)

    assert [c.carteira for c in antes] == list(CARTEIRAS)
    assert antes == depois
    assert all(c.data_montagem == D1 and c.ptax_venda == PTAX for c in depois)


# ---------------------------------------------------------------- números das cinco carteiras


def test_cinco_carteiras_unidades_inteiras_e_sobra_em_caixa():
    con = _con()
    _cenario_base(con)
    selado, cesta, propria, dolar, cdi = compor_carteiras(_dados(con))

    # selado: booster box R$ 750 → 1 unidade, R$ 250 em caixa
    assert _ids(selado) == [(BOX, "Normal")] and not selado.fallback
    (box,) = selado.posicoes
    assert box.unidades == 1 and abs(box.preco_compra_brl - 750.0) < TOL
    assert abs(selado.caixa_brl - 250.0) < TOL

    # cesta_raras: dez SIR de maior preço (12 a 3); Code Card fora;
    # as de R$ 105 e R$ 110 não compram unidade e os R$ 100 de cada viram caixa
    assert [pid for pid, _ in _ids(cesta)] == list(range(12, 2, -1))
    por_id = {p.product_id: p for p in cesta.posicoes}
    assert por_id[12].unidades == 0 and abs(por_id[12].sobra_brl - 100.0) < TOL
    assert por_id[3].unidades == 1 and abs(por_id[3].sobra_brl - 35.0) < TOL  # R$ 65
    assert all(p.valor_alocado_brl == 100.0 for p in cesta.posicoes)
    custo = sum(5.0 * (10.0 + pid) for pid in range(3, 11))  # pids 11 e 12 passam de R$ 100
    assert abs(custo - 660.0) < TOL
    assert abs(cesta.caixa_brl - (1000.0 - custo)) < TOL
    assert abs(cesta.caixa_brl - 340.0) < TOL
    assert abs(cesta.caixa_brl - sum(p.sobra_brl for p in cesta.posicoes)) < TOL

    # propria: Half R$ 400 (maior ≤ R$ 500) e as cinco IR de maior preço
    assert _ids(propria)[0] == (701, "Normal")
    assert [pid for pid, _ in _ids(propria)[1:]] == [26, 25, 24, 23, 22]
    unidades = {p.product_id: p.unidades for p in propria.posicoes}
    assert unidades == {701: 1, 26: 2, 25: 2, 24: 3, 23: 4, 22: 6}  # R$ 45, 37,5, 30, 22,5, 15
    custo = 400.0 + 90.0 + 75.0 + 90.0 + 90.0 + 90.0
    assert abs(propria.caixa_brl - (1000.0 - custo)) < TOL

    # dolar e cdi
    assert abs(dolar.usd - 200.0) < TOL and dolar.caixa_brl == 0.0 and dolar.posicoes == ()
    assert cdi.caixa_brl == 1000.0 and cdi.usd == 0.0 and cdi.posicoes == ()


def test_unidades_exatas_sem_erro_de_ponto_flutuante():
    con = duckdb.connect()
    con.execute("CREATE TABLE fato (data DATE, product_id INTEGER, group_id INTEGER, "
                "acabamento VARCHAR, market_price DOUBLE)")
    con.execute("CREATE TABLE dim_produto (group_id INTEGER, product_id INTEGER, nome VARCHAR, "
                "tipo_produto VARCHAR, raridade VARCHAR, numero VARCHAR, image_url VARCHAR, "
                "url VARCHAR)")
    con.execute("CREATE TABLE fato_cambio (data DATE, cotacao_venda DOUBLE)")
    con.execute("INSERT INTO fato_cambio VALUES (?, ?)", [D1, 3.0])
    _item(con, 1, 0.1 / 3 * 100)  # R$ 10,000… por unidade, caberia 10 vezes em R$ 100
    (pos,) = compor_cesta_raras(_dados(con)).posicoes
    assert pos.unidades == 10


# ---------------------------------------------------------------- cesta_raras (RF-23)


def _nove_caras(con):
    for pid in range(201, 210):
        _item(con, pid, 100.0 + pid)


def test_cesta_raras_empate_na_decima_entra_menor_product_id():
    con = _con()
    _nove_caras(con)
    _item(con, 50, 20.0)
    _item(con, 40, 20.0)
    _item(con, 999, 1000.0, "Booster", "selado")      # selado fora
    _item(con, 998, 1000.0, raridade="Code Card")     # Code Card fora
    cesta = compor_cesta_raras(_dados(con))
    ids = [pid for pid, _ in _ids(cesta)]
    assert len(ids) == 10 and ids[-1] == 40 and 50 not in ids
    assert not {998, 999} & set(ids)


def test_cesta_raras_mesmo_product_id_empatado_entra_acabamento_alfabetico():
    con = _con()
    _nove_caras(con)
    _produto(con, 40)
    _preco(con, 40, 20.0, "Reverse Holofoil")
    _preco(con, 40, 20.0, "Holofoil")
    assert _ids(compor_cesta_raras(_dados(con)))[-1] == (40, "Holofoil")


def test_cesta_raras_com_menos_de_dez_itens_valor_restante_em_caixa():
    con = _con()
    _item(con, 1, 10.0)               # R$ 50 → 2 unidades
    _item(con, 2, None)               # sem preço, fora
    cesta = compor_cesta_raras(_dados(con))
    assert _ids(cesta) == [(1, "Normal")]
    assert abs(cesta.caixa_brl - 900.0) < TOL


# ---------------------------------------------------------------- selado (ADR-006)


def test_selado_booster_box_com_preco_mesmo_com_selado_mais_caro():
    con = _con()
    _item(con, BOX, 150.0, "Destined Rivals Booster Box", "selado")
    _item(con, 703, 190.0, "Destined Rivals Premium Collection", "selado")
    selado = compor_selado(_dados(con))
    assert _ids(selado) == [(BOX, "Normal")] and not selado.fallback


@pytest.mark.parametrize("box_no_dia", [True, False], ids=["preco_nulo", "ausente_no_dia"])
def test_selado_booster_box_sem_preco_aciona_fallback(box_no_dia):
    con = _con()
    if box_no_dia:
        _item(con, BOX, None, "Destined Rivals Booster Box", "selado")
    else:
        _produto(con, BOX, "Destined Rivals Booster Box", "selado")
    _item(con, 703, 190.0, "Destined Rivals Premium Collection", "selado")  # R$ 950
    _item(con, 704, 60.0, "Destined Rivals Elite Trainer Box", "selado")
    _item(con, 1, 500.0)  # carta mais cara não entra no selado
    selado = compor_selado(_dados(con))
    assert selado.fallback and _ids(selado) == [(703, "Normal")]
    assert selado.posicoes[0].unidades == 1 and abs(selado.caixa_brl - 50.0) < TOL


def test_selado_fallback_empate_por_product_id_e_depois_acabamento():
    con = _con()
    _item(con, BOX, None, "Destined Rivals Booster Box", "selado")
    _item(con, 720, 100.0, "Selado B", "selado")
    _produto(con, 710, "Selado A", "selado")
    _preco(con, 710, 100.0, "Unopened")
    _preco(con, 710, 100.0, "Normal")
    assert _ids(compor_selado(_dados(con))) == [(710, "Normal")]


def test_selado_booster_box_acima_do_orcamento_zero_unidades_sem_fallback():
    con = _con()
    _item(con, BOX, 250.0, "Destined Rivals Booster Box", "selado")  # R$ 1.250
    _item(con, 704, 60.0, "Destined Rivals Elite Trainer Box", "selado")
    selado = compor_selado(_dados(con))
    assert not selado.fallback
    (pos,) = selado.posicoes
    assert pos.product_id == BOX and pos.unidades == 0 and pos.custo_brl == 0.0
    assert selado.caixa_brl == 1000.0


def test_selado_case_e_half_nao_sao_booster_box():
    con = _con()
    _item(con, 700, 90.0, "Destined Rivals Booster Box Case", "selado")
    _item(con, 701, 80.0, "Destined Rivals Half Booster Box", "selado")
    _item(con, 704, 60.0, "Destined Rivals Elite Trainer Box", "selado")
    selado = compor_selado(_dados(con))
    assert selado.fallback and _ids(selado) == [(700, "Normal")]  # maior selado, via fallback


def test_selado_dois_product_id_na_regra_do_nome_e_pendencia():
    con = _con()
    _item(con, BOX, 150.0, "Destined Rivals Booster Box", "selado")
    _item(con, 705, 140.0, "Destined Rivals Booster Box (Enhanced)", "selado")
    with pytest.raises(PendenciaBoosterBox, match="624679"):
        compor_selado(_dados(con))


def test_selado_mesmo_product_id_com_dois_acabamentos_escolhe_alfabetico():
    con = _con()
    _produto(con, BOX, "Destined Rivals Booster Box", "selado")
    _preco(con, BOX, 160.0, "Unopened")
    _preco(con, BOX, 150.0, "Normal")
    selado = compor_selado(_dados(con))
    assert _ids(selado) == [(BOX, "Normal")] and not selado.fallback


def test_selado_sem_nenhum_selado_com_preco_fica_todo_em_caixa():
    con = _con()
    _item(con, BOX, None, "Destined Rivals Booster Box", "selado")
    _item(con, 1, 10.0)
    selado = compor_selado(_dados(con))
    assert selado.fallback and selado.posicoes == () and selado.caixa_brl == 1000.0


# ---------------------------------------------------------------- propria (ADR-005)


def _cinco_ir(con, inicio=301, n=4):
    for pid in range(inicio, inicio + n):
        _item(con, pid, 10.0 + pid / 100, raridade="Illustration Rare")


def test_propria_empate_na_quinta_illustration_rare_por_product_id():
    con = _con()
    _cinco_ir(con)
    _item(con, 60, 5.0, raridade="Illustration Rare")
    _item(con, 50, 5.0, raridade="Illustration Rare")
    _item(con, 1, 50.0)  # SIR fora da parte de cartas
    cartas = [pid for pid, _ in _ids(compor_propria(_dados(con)))]
    assert cartas == [304, 303, 302, 301, 50]


def test_propria_empate_na_quinta_illustration_rare_por_acabamento():
    con = _con()
    _cinco_ir(con)
    _produto(con, 50, raridade="Illustration Rare")
    _preco(con, 50, 5.0, "Reverse Holofoil")
    _preco(con, 50, 5.0, "Holofoil")
    assert _ids(compor_propria(_dados(con)))[-1] == (50, "Holofoil")


def test_propria_selados_empatados_por_product_id_e_depois_acabamento():
    con = _con()
    _item(con, 720, 80.0, "Selado B", "selado")
    _produto(con, 710, "Selado A", "selado")
    _preco(con, 710, 80.0, "Unopened")
    _preco(con, 710, 80.0, "Normal")
    _item(con, 730, 101.0, "Selado caro", "selado")  # R$ 505 > R$ 500, fora
    propria = compor_propria(_dados(con))
    assert _ids(propria) == [(710, "Normal")]
    assert propria.posicoes[0].unidades == 1  # R$ 400


def test_propria_nenhum_selado_ate_500_deixa_500_em_caixa():
    con = _con()
    _item(con, BOX, 150.0, "Destined Rivals Booster Box", "selado")  # R$ 750
    _cinco_ir(con, n=5)
    propria = compor_propria(_dados(con))
    assert all(p.product_id != BOX for p in propria.posicoes)
    custo_cartas = sum(p.custo_brl for p in propria.posicoes)
    assert abs(propria.caixa_brl - (500.0 + 500.0 - custo_cartas)) < TOL


def test_propria_so_tres_illustration_rare_deixa_200_em_caixa():
    con = _con()
    _item(con, 710, 100.0, "Selado A", "selado")  # R$ 500, cabe exato: 1 unidade
    for pid in (41, 42, 43):
        _item(con, pid, 20.0, raridade="Illustration Rare")  # R$ 100: 1 unidade cada
    _item(con, 44, 20.0, raridade="Code Card")
    propria = compor_propria(_dados(con))
    assert [p.unidades for p in propria.posicoes] == [1, 1, 1, 1]
    assert abs(propria.caixa_brl - 200.0) < TOL


def test_propria_sem_regra_fica_regra_pendente():
    con = _con()
    _cenario_base(con)
    propria = compor_carteiras(_dados(con), regra_propria=False)[2]
    assert propria.carteira == "propria" and propria.status == STATUS_REGRA_PENDENTE
    assert propria.posicoes == ()


# ---------------------------------------------------------------- leitura e saída


def test_sem_ptax_aplicada_no_primeiro_dia_e_erro():
    con = _con()
    _item(con, 1, 10.0)
    _preco(con, 1, 10.0, dia=D1 - dt.timedelta(days=1))  # dia sem PTAX vira o primeiro dia
    with pytest.raises(ValueError, match="sem PTAX"):
        _dados(con)


def test_registrar_composicao_no_duckdb():
    con = _con()
    _cenario_base(con)
    comps = compor_carteiras(_dados(con), regra_propria=False)
    rel = registrar_composicao(con, comps)
    linhas = con.sql(
        "SELECT carteira, count(*) FILTER (WHERE product_id IS NOT NULL), "
        "max(caixa_brl), max(usd) FROM composicao_carteira GROUP BY carteira ORDER BY carteira"
    ).fetchall()
    assert rel.columns[0] == "carteira"
    assert linhas == [
        ("cdi", 0, 1000.0, 0.0),
        ("cesta_raras", 10, pytest.approx(comps[1].caixa_brl), 0.0),
        ("dolar", 0, 0.0, pytest.approx(200.0)),
        ("propria", 0, None, None),
        ("selado", 1, pytest.approx(250.0), 0.0),
    ]
