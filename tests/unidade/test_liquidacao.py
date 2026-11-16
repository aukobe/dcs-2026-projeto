"""Testes do valor de liquidação diário (T-42; RF-24; ADR-005, ADR-006).

DuckDB em memória; rede bloqueada (conftest). Composição montada pela T-41
(`ler_primeiro_dia` + `compor_carteiras`) com PTAX de venda 5,00 no primeiro dia:

    booster box 624679  US$ 150 → R$ 750   ETB 702 US$ 60 → R$ 300
    SIR 1 US$ 19 → R$ 95   SIR 2 US$ 15 → R$ 75   IR 21 US$ 8 → R$ 40

    selado       1 × box                     custo 750  caixa 250
    cesta_raras  1 × SIR1, 1 × SIR2, 2 × IR21 custo 250  caixa 750
    propria      1 × ETB, 2 × IR21           custo 380  caixa 620
    dolar        1000 / 5,00 = 200 USD
    cdi          caixa 1000

Período: qui 05/11/2026 (primeiro dia) a qua 11/11/2026, PTAX de compra 4,90
(5,10 na segunda 09/11). CDI (% ao dia): qui 0,05; sex 0,05; sáb 0; dom 0;
seg 0,05; ter pendente (0); qua 0,05. A taxa do dia d remunera de d ao próximo
dia útil: valor(D) = inicial × Π (1 + taxa(d)/100), primeiro dia ≤ d < D.
"""

import datetime as dt

import duckdb
import pytest

from tcg.gold.carteiras import (
    STATUS_REGRA_PENDENTE,
    Composicao,
    Posicao,
    compor_carteiras,
    ler_primeiro_dia,
)
from tcg.gold.liquidacao import (
    CambioDia,
    DadosDiarios,
    ler_dados_diarios,
    liquidar,
    registrar_liquidacao,
)

GID = 24269
D1 = dt.date(2026, 11, 5)  # quinta
DIAS = [D1 + dt.timedelta(days=k) for k in range(7)]  # qui 05 a qua 11
QUI, SEX, SAB, DOM, SEG, TER, QUA = DIAS
BOX = 624679

CAMBIO = {
    #     compra venda  cdi    pendente
    QUI: (4.90, 5.00, 0.05, False),
    SEX: (4.90, 5.00, 0.05, False),
    SAB: (4.90, 5.00, 0.0, False),
    DOM: (4.90, 5.00, 0.0, False),
    SEG: (5.10, 5.20, 0.05, False),
    TER: (4.90, 5.00, 0.0, True),
    QUA: (4.90, 5.00, 0.05, False),
}

ITENS = [
    # pid, nome, tipo, raridade, preço US$
    (BOX, "Destined Rivals Booster Box", "selado", None, 150.0),
    (702, "Destined Rivals Elite Trainer Box", "selado", None, 60.0),
    (1, "SIR 1", "carta", "Special Illustration Rare", 19.0),
    (2, "SIR 2", "carta", "Special Illustration Rare", 15.0),
    (21, "IR 21", "carta", "Illustration Rare", 8.0),
]


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
    con.execute(
        "CREATE TABLE fato_cambio (data DATE, cotacao_compra DOUBLE, cotacao_venda DOUBLE, "
        "cdi_taxa_dia DOUBLE, cdi_pendente BOOLEAN)"
    )
    for dia, (compra, venda, cdi, pend) in CAMBIO.items():
        con.execute("INSERT INTO fato_cambio VALUES (?, ?, ?, ?, ?)", [dia, compra, venda, cdi, pend])
    for pid, nome, tipo, raridade, usd in ITENS:
        con.execute(
            "INSERT INTO dim_produto VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [GID, pid, nome, tipo, raridade, None, None, None],
        )
        for dia in DIAS:
            preco = usd
            if pid == 1 and dia == SAB:
                continue  # SIR 1 sem linha no sábado
            if pid == 1 and dia != QUI:
                preco = 20.0  # SIR 1 sobe para US$ 20 a partir de sexta
            con.execute("INSERT INTO fato VALUES (?, ?, ?, ?, ?)", [dia, pid, GID, "Normal", preco])
    return con


def _montar(con, regra_propria=True):
    dados1 = ler_primeiro_dia(con, "fato", "dim_produto", "fato_cambio", GID)
    comps = compor_carteiras(dados1, regra_propria)
    dados = ler_dados_diarios(con, "fato", "fato_cambio", comps, GID)
    return {c.carteira: c for c in comps}, dados


def _valores(comp, dados, taxa):
    linhas, _ = liquidar(comp, dados, taxa)
    return {l.data: l for l in linhas}


def test_composicao_da_fixture():
    comps, _ = _montar(_con())
    assert comps["selado"].caixa_brl == pytest.approx(250.0)
    assert comps["cesta_raras"].caixa_brl == pytest.approx(750.0)
    assert comps["propria"].caixa_brl == pytest.approx(620.0)
    assert comps["dolar"].usd == pytest.approx(200.0)
    assert comps["cdi"].caixa_brl == pytest.approx(1000.0)


def test_primeiro_dia_custo_liquidado_e_cdi_exata():
    # 0,85 × 4,90 = 4,165
    # selado: 150 × 4,165 = 624,75 + 250 = 874,75
    # cesta:  (19 + 15 + 2×8) = 50 × 4,165 = 208,25 + 750 = 958,25
    # propria: (60 + 2×8) = 76 × 4,165 = 316,54 + 620 = 936,54
    # dolar: 200 × 4,90 = 980,00; cdi: 1000,00 exatos
    comps, dados = _montar(_con())
    esperado = {
        "selado": 874.75, "cesta_raras": 958.25, "propria": 936.54,
        "dolar": 980.00,
    }
    for carteira, valor in esperado.items():
        v = _valores(comps[carteira], dados, 0.15)[QUI].valor_brl
        assert v == pytest.approx(valor)
        assert v < 1000.0
    assert _valores(comps["cdi"], dados, 0.15)[QUI].valor_brl == 1000.0


def test_cdi_so_em_dia_util_com_taxa_da_vespera():
    # cdi: qui 1000; sex 1000 × 1,0005 = 1000,5; sáb 1000,5 × 1,0005 = 1001,00025
    # (taxa de sexta); dom e seg iguais (taxas de sáb e dom = 0);
    # ter 1001,00025 × 1,0005 = 1001,500750125; qua igual (taxa de ter pendente → 0).
    # caixa da selado (250): sex 250,125; sáb 250,2500625; dom e seg iguais;
    # ter 250,2500625 + 0,12512503125 = 250,37518753125; qua igual.
    comps, dados = _montar(_con())
    cdi = _valores(comps["cdi"], dados, 0.15)
    esperado_cdi = {
        QUI: 1000.0, SEX: 1000.5, SAB: 1001.00025, DOM: 1001.00025,
        SEG: 1001.00025, TER: 1001.500750125, QUA: 1001.500750125,
    }
    for dia, valor in esperado_cdi.items():
        assert cdi[dia].valor_brl == pytest.approx(valor, abs=1e-9)
    # o fim de semana não altera: sáb = dom = seg
    assert cdi[SAB].valor_brl == cdi[DOM].valor_brl == cdi[SEG].valor_brl

    selado = _valores(comps["selado"], dados, 0.15)
    esperado_caixa = {
        QUI: 250.0, SEX: 250.125, SAB: 250.2500625, DOM: 250.2500625,
        SEG: 250.2500625, TER: 250.37518753125, QUA: 250.37518753125,
    }
    for dia, valor in esperado_caixa.items():
        assert selado[dia].caixa_brl == pytest.approx(valor, abs=1e-9)
    assert selado[SAB].caixa_brl == selado[DOM].caixa_brl == selado[SEG].caixa_brl

    # cdi_pendente: só a quarta usa a taxa de terça, que falta
    assert [d for d, l in cdi.items() if l.cdi_pendente] == [QUA]


def test_preco_ausente_usa_ultimo_observado_e_marca():
    # sáb: SIR 1 sem linha → usa US$ 20 de sexta.
    # cesta sáb (taxa 15%, compra 4,90): (20 + 15 + 16) = 51 × 4,165 = 212,415
    # caixa 750 × 1,0005² = 750,7501875 → total 963,1651875; SIR 1: 20 × 4,165 = 83,30
    con = _con()
    linhas_fato = con.execute("SELECT count(*) FROM fato").fetchone()[0]
    comps, dados = _montar(con)
    linhas, itens = liquidar(comps["cesta_raras"], dados, 0.15)
    por_dia = {l.data: l for l in linhas}
    assert por_dia[SAB].preco_carregado is True
    assert por_dia[SAB].n_itens_carregados == 1
    assert por_dia[SAB].valor_brl == pytest.approx(963.1651875)
    assert [d for d, l in por_dia.items() if l.preco_carregado] == [SAB]

    sir1 = {i.data: i for i in itens if i.product_id == 1}
    assert sir1[SAB].preco_carregado is True
    assert sir1[SAB].market_price_usado == 20.0
    assert sir1[SAB].data_preco == SEX
    assert sir1[SAB].valor_brl == pytest.approx(83.30)
    assert sir1[DOM].preco_carregado is False
    # nada gravado no fato (silver intacta)
    registrar_liquidacao(con, tuple(comps.values()), dados, 0.15)
    assert con.execute("SELECT count(*) FROM fato").fetchone()[0] == linhas_fato
    assert con.execute(
        "SELECT count(*) FROM fato WHERE product_id = 1 AND data = ?", [SAB]
    ).fetchone()[0] == 0


def test_taxa_zero_contra_15_so_muda_cartas_e_selados():
    # diferença no primeiro dia = 0,15 × itens × 4,90:
    # selado 0,15 × 735 = 110,25; cesta 0,15 × 245 = 36,75; propria 0,15 × 372,4 = 55,86
    comps, dados = _montar(_con())
    esperado = {"selado": 110.25, "cesta_raras": 36.75, "propria": 55.86,
                "dolar": 0.0, "cdi": 0.0}
    for carteira, dif in esperado.items():
        com = _valores(comps[carteira], dados, 0.15)
        sem = _valores(comps[carteira], dados, 0.0)
        assert sem[QUI].valor_brl - com[QUI].valor_brl == pytest.approx(dif, abs=1e-9)
        for dia in DIAS:
            assert sem[dia].caixa_brl == pytest.approx(com[dia].caixa_brl)
    assert _valores(comps["selado"], dados, 0.0)[QUI].valor_brl == pytest.approx(985.0)
    assert _valores(comps["cesta_raras"], dados, 0.0)[QUI].valor_brl == pytest.approx(995.0)
    assert _valores(comps["propria"], dados, 0.0)[QUI].valor_brl == pytest.approx(992.40)


def test_dolar_com_ptax_de_compra():
    # seg: compra 5,10 (venda 5,20 ignorada) → 200 × 5,10 = 1020,00
    comps, dados = _montar(_con())
    dolar = _valores(comps["dolar"], dados, 0.15)
    assert dolar[SEG].valor_brl == pytest.approx(1020.0)
    assert _valores(comps["dolar"], dados, 0.0)[SEG].valor_brl == pytest.approx(1020.0)


def test_criterio_da_tarefa_435_e_taxa_10():
    # 1 × 100 × 0,85 × 5,00 + 10 = 435,00; com 10%: 1 × 100 × 0,90 × 5,00 + 10 = 460,00
    pos = Posicao(1, "Normal", "Carta", 100.0, 500.0, 510.0, 1, 500.0, 10.0)
    comp = Composicao("cesta_raras", "calculada", D1, 5.0, (pos,), caixa_brl=10.0)
    dados = DadosDiarios(
        dias=(CambioDia(D1, 5.0, 0.0, False),),
        precos={(1, "Normal"): {D1: 100.0}},
    )
    v15 = liquidar(comp, dados, 0.15)[0][0].valor_brl
    v10 = liquidar(comp, dados, 0.10)[0][0].valor_brl
    assert v15 == pytest.approx(435.0)
    assert v10 == pytest.approx(460.0)
    assert v10 != v15


def test_uma_linha_por_carteira_dia_e_taxa():
    # 5 carteiras × 7 dias × 2 taxas = 70 linhas
    con = _con()
    comps, dados = _montar(con)
    registrar_liquidacao(con, tuple(comps.values()), dados, 0.15)
    assert con.execute("SELECT count(*) FROM liquidacao_carteira").fetchone()[0] == 70
    assert con.execute(
        "SELECT count(*) FROM (SELECT DISTINCT data, carteira, taxa_venda FROM liquidacao_carteira)"
    ).fetchone()[0] == 70
    assert sorted(r[0] for r in con.execute(
        "SELECT DISTINCT taxa_venda FROM liquidacao_carteira").fetchall()) == [0.0, 0.15]


def test_propria_regra_pendente_tem_linha_com_valor_nulo():
    comps, dados = _montar(_con(), regra_propria=False)
    linhas = _valores(comps["propria"], dados, 0.15)
    assert len(linhas) == 7
    assert all(l.status == STATUS_REGRA_PENDENTE and l.valor_brl is None for l in linhas.values())


def test_sem_ptax_de_compra_no_periodo_e_erro():
    con = _con()
    con.execute("UPDATE fato_cambio SET cotacao_compra = NULL WHERE data = ?", [DOM])
    with pytest.raises(ValueError, match="PTAX de compra"):
        _montar(con)
