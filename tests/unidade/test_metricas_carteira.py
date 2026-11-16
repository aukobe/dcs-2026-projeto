"""Testes das métricas das carteiras (T-43; RF-25).

Séries montadas à mão; DuckDB em memória; rede bloqueada (conftest). As contas
de cada valor esperado estão no comentário do teste.
"""

import datetime as dt

import duckdb
import pytest

from tcg.gold.carteiras import STATUS_CALCULADA, STATUS_REGRA_PENDENTE, Composicao, Posicao
from tcg.gold.liquidacao import CambioDia, DadosDiarios, LinhaCarteira, liquidar_carteiras
from tcg.gold.metricas_carteira import (
    calcular_metricas,
    perda_maxima,
    registrar_metricas,
    retorno_acumulado,
)

D1 = dt.date(2026, 11, 5)


def _serie(carteira, valores, taxa=0.15, carregados=None, status=STATUS_CALCULADA):
    carregados = carregados or [False] * len(valores)
    return [
        LinhaCarteira(
            data=D1 + dt.timedelta(days=k),
            carteira=carteira,
            status=status,
            taxa_venda=taxa,
            valor_brl=v,
            valor_itens_brl=None,
            caixa_brl=None,
            preco_carregado=c,
            n_itens_carregados=int(c),
            cdi_pendente=False,
        )
        for k, (v, c) in enumerate(zip(valores, carregados))
    ]


def _por_chave(metricas):
    return {(m.carteira, m.taxa_venda): m for m in metricas}


def test_criterio_da_tarefa_retorno_10_e_perda_25():
    # retorno = 1100 / 1000 − 1 = 0,10; perda = (1200 − 900) / 1200 = 0,25
    linhas = _serie("selado", [1000, 1200, 900, 1100]) + _serie("cdi", [1000, 1000, 1000, 1000])
    m = _por_chave(calcular_metricas(linhas))[("selado", 0.15)]
    assert m.retorno_acumulado == pytest.approx(0.10)
    assert m.perda_maxima == pytest.approx(0.25)
    assert m.valor_final_brl == 1100
    assert m.n_dias == 4
    assert m.data_final == D1 + dt.timedelta(days=3)


def test_retorno_acumulado_e_excesso_sobre_cdi():
    # carteira: 1100 / 1000 − 1 = 0,10; cdi: 1002 / 1000 − 1 = 0,002
    # excesso = 0,10 − 0,002 = 0,098; o excesso da própria cdi é 0
    linhas = _serie("cesta_raras", [1000, 1050, 1100]) + _serie("cdi", [1000, 1001, 1002])
    m = _por_chave(calcular_metricas(linhas))
    assert retorno_acumulado(1100) == pytest.approx(0.10)
    assert m[("cesta_raras", 0.15)].retorno_acumulado == pytest.approx(0.10)
    assert m[("cdi", 0.15)].retorno_acumulado == pytest.approx(0.002)
    assert m[("cesta_raras", 0.15)].excesso_cdi == pytest.approx(0.098)
    assert m[("cdi", 0.15)].excesso_cdi == pytest.approx(0.0)


def test_perda_maxima_pico_relevante_nao_e_o_primeiro():
    # 1000, 1100, 990, 1200, 1000, 840, 900
    # quedas: 1100→990 = 110/1100 = 10%; 1200→840 = 360/1200 = 30%  → perda 0,30
    # armadilhas: primeiro pico 1100→840 = 23,6%; maior queda diária 1200→1000 = 16,7%
    serie = [1000, 1100, 990, 1200, 1000, 840, 900]
    assert perda_maxima(serie) == pytest.approx(0.30)
    m = _por_chave(calcular_metricas(_serie("selado", serie) + _serie("cdi", [1000] * 7)))
    assert m[("selado", 0.15)].perda_maxima == pytest.approx(0.30)


def test_perda_maxima_zero_em_serie_que_so_sobe():
    assert perda_maxima([1000, 1010, 1020]) == 0.0
    m = _por_chave(calcular_metricas(_serie("cdi", [1000, 1010, 1020])))
    assert m[("cdi", 0.15)].perda_maxima == 0.0


def test_dias_com_preco_carregado():
    # marcas F, T, T, F, T → 3 dias
    linhas = _serie(
        "cesta_raras", [1000] * 5, carregados=[False, True, True, False, True]
    ) + _serie("cdi", [1000] * 5)
    m = _por_chave(calcular_metricas(linhas))
    assert m[("cesta_raras", 0.15)].dias_preco_carregado == 3
    assert m[("cdi", 0.15)].dias_preco_carregado == 0


def test_taxa_zero_contra_15_so_muda_cartas_e_selados():
    # Composição à mão, liquidada pela T-42. PTAX de compra 5,00 nos dois dias;
    # CDI 0,05% no dia 1 (remunera o dia 2): fator 1,0005.
    # selado, dia 2: itens 1 × 160 × 5 = 800; caixa 250 × 1,0005 = 250,125
    #   taxa 0:   800 + 250,125 = 1050,125 → retorno 0,050125
    #   taxa 15%: 680 + 250,125 =  930,125 → retorno −0,069875
    #   diferença = 0,12 = 800 × 0,15 / 1000 (só a parte em selados)
    # dolar: 200 × 5 = 1000 → retorno 0 nas duas taxas
    # cdi: 1000 × 1,0005 = 1000,5 → retorno 0,0005 nas duas taxas
    # excesso do selado com taxa 0: 0,050125 − 0,0005 = 0,049625
    pos = Posicao(1, "Normal", "Box", 150.0, 750.0, 1000.0, 1, 750.0, 250.0)
    comps = (
        Composicao("selado", STATUS_CALCULADA, D1, 5.0, (pos,), caixa_brl=250.0),
        Composicao("dolar", STATUS_CALCULADA, D1, 5.0, usd=200.0),
        Composicao("cdi", STATUS_CALCULADA, D1, 5.0, caixa_brl=1000.0),
    )
    d2 = D1 + dt.timedelta(days=1)
    dados = DadosDiarios(
        dias=(CambioDia(D1, 5.0, 0.05, False), CambioDia(d2, 5.0, 0.0, False)),
        precos={(1, "Normal"): {D1: 150.0, d2: 160.0}},
    )
    linhas, _ = liquidar_carteiras(comps, dados, (0.15, 0.0))
    m = _por_chave(calcular_metricas(linhas))
    assert m[("selado", 0.0)].retorno_acumulado == pytest.approx(0.050125)
    assert m[("selado", 0.15)].retorno_acumulado == pytest.approx(-0.069875)
    assert (
        m[("selado", 0.0)].retorno_acumulado - m[("selado", 0.15)].retorno_acumulado
    ) == pytest.approx(0.12)
    assert m[("selado", 0.0)].excesso_cdi == pytest.approx(0.049625)
    for carteira, esperado in (("dolar", 0.0), ("cdi", 0.0005)):
        assert m[(carteira, 0.0)].retorno_acumulado == pytest.approx(esperado)
        assert m[(carteira, 0.15)].retorno_acumulado == pytest.approx(esperado)
        assert (
            m[(carteira, 0.0)].retorno_acumulado - m[(carteira, 0.15)].retorno_acumulado
        ) == pytest.approx(0.0, abs=1e-12)


def test_propria_pendente_tem_metricas_nulas():
    linhas = (
        _serie("propria", [None, None, None], status=STATUS_REGRA_PENDENTE)
        + _serie("selado", [1000, 900, 950])
        + _serie("cdi", [1000, 1000, 1000])
    )
    m = _por_chave(calcular_metricas(linhas))
    p = m[("propria", 0.15)]
    assert p.status == STATUS_REGRA_PENDENTE
    assert (p.valor_final_brl, p.retorno_acumulado, p.excesso_cdi, p.perda_maxima,
            p.dias_preco_carregado) == (None, None, None, None, None)
    # as demais continuam calculadas: (1000 − 900) / 1000 = 0,10; 950/1000 − 1 = −0,05
    assert m[("selado", 0.15)].perda_maxima == pytest.approx(0.10)
    assert m[("selado", 0.15)].retorno_acumulado == pytest.approx(-0.05)


def test_registrar_metricas_uma_linha_por_carteira_e_taxa():
    linhas = []
    for taxa in (0.15, 0.0):
        linhas += _serie("propria", [None, None], taxa=taxa, status=STATUS_REGRA_PENDENTE)
        linhas += _serie("selado", [1000, 1100], taxa=taxa)
        linhas += _serie("cdi", [1000, 1001], taxa=taxa)
    con = duckdb.connect()
    registrar_metricas(con, linhas)
    assert con.execute("SELECT count(*) FROM metricas_carteira").fetchone()[0] == 6
    assert con.execute(
        "SELECT count(*) FROM (SELECT DISTINCT carteira, taxa_venda FROM metricas_carteira)"
    ).fetchone()[0] == 6
    nulos = con.execute(
        "SELECT retorno_acumulado, perda_maxima FROM metricas_carteira WHERE carteira = 'propria'"
    ).fetchall()
    assert nulos == [(None, None), (None, None)]


def test_sem_carteira_cdi_e_erro():
    with pytest.raises(ValueError, match="cdi"):
        calcular_metricas(_serie("selado", [1000, 1100]))
