"""Testes da quarentena da silver (T-26; RF-07)."""

import datetime as dt
import json

import pytest

from tcg.silver.modelos import (
    CambioDiario,
    CdiDiario,
    PrecoDiario,
    cambio_do_bruto,
    cdi_do_bruto,
    preco_do_bruto,
)
from tcg.silver.quarentena import (
    MOTIVO_DIVERGENTE,
    LinhaQuarentena,
    contar_por_tabela,
    deduplicar_por_data,
    formatar_contagem,
    validar,
)

DIA = dt.date(2026, 11, 3)
CHAVE_PRECOS = "raw/tcgplayer/group_id=24269/data=2026-11-03/prices.json"


def _chave_ptax(dia):
    return f"raw/bcb_ptax/group_id=24269/data={dia}/cotacao.json"


def _chave_cdi(dia):
    return f"raw/bcb_cdi/group_id=24269/data={dia}/cdi.json"


def _ptax(venda=5.4321, boletim="Fechamento", data_hora="2026-10-30 13:09:27.123"):
    item = {
        "cotacaoCompra": 5.4315,
        "cotacaoVenda": venda,
        "dataHoraCotacao": data_hora,
        "tipoBoletim": boletim,
    }
    if venda is None:
        del item["cotacaoVenda"]
    return item


def _preco(product_id=600001):
    linha = {"subTypeName": "Normal", "marketPrice": 1.5, "lowPrice": 1.0,
             "midPrice": 1.4, "highPrice": 3.0}
    if product_id is not None:
        linha["productId"] = product_id
    return linha


def test_preco_valido_passa_sem_quarentena():
    r = validar("preco_diario", preco_do_bruto, _preco(), CHAVE_PRECOS, DIA, 24269, CHAVE_PRECOS)
    assert isinstance(r, PrecoDiario)


def test_preco_sem_product_id_vai_para_quarentena_com_motivo_e_chave_raw():
    item = _preco(product_id=None)
    r = validar("preco_diario", preco_do_bruto, item, CHAVE_PRECOS, DIA, 24269, CHAVE_PRECOS)
    assert isinstance(r, LinhaQuarentena)
    assert r.tabela == "preco_diario"
    assert r.chave_raw == CHAVE_PRECOS
    assert r.motivo.startswith("product_id:")
    assert json.loads(r.conteudo) == item


def test_fechamento_sem_cotacao_venda_vai_para_quarentena():
    chave = _chave_ptax("2026-11-03")
    r = validar("cambio_diario", cambio_do_bruto, _ptax(venda=None), chave, chave)
    assert isinstance(r, LinhaQuarentena)
    assert r.tabela == "cambio_diario"
    assert "cotacao_venda" in r.motivo
    assert r.chave_raw == chave


def test_data_hora_invalida_vai_para_quarentena_sem_excecao():
    chave = _chave_ptax("2026-11-03")
    r = validar("cambio_diario", cambio_do_bruto, _ptax(data_hora="ontem"), chave, chave)
    assert isinstance(r, LinhaQuarentena)
    assert r.motivo


def test_boletim_intermediario_descartado_fora_da_quarentena():
    chave = _chave_ptax("2026-11-03")
    r = validar("cambio_diario", cambio_do_bruto, _ptax(boletim="Intermediário"), chave, chave)
    assert r is None


def test_tabela_desconhecida_recusada():
    with pytest.raises(ValueError):
        validar("outra", preco_do_bruto, _preco(), CHAVE_PRECOS, DIA, 24269, CHAVE_PRECOS)


def _cambio(chave, venda=5.4321):
    return cambio_do_bruto(_ptax(venda=venda), chave)


def _cdi(chave, valor="0.050788", data="30/10/2026"):
    return cdi_do_bruto({"data": data, "valor": valor}, chave)


def test_ptax_igual_em_dois_brutos_gera_uma_linha_do_bruto_mais_antigo():
    a, b = _chave_ptax("2026-11-03"), _chave_ptax("2026-11-02")
    validos, quarentena = deduplicar_por_data("cambio_diario", [_cambio(a), _cambio(b)])
    assert quarentena == []
    assert len(validos) == 1
    assert isinstance(validos[0], CambioDiario)
    assert validos[0].chave_raw == b


def test_cdi_igual_em_tres_brutos_gera_uma_linha_por_data():
    chaves = [_chave_cdi(f"2026-11-0{d}") for d in (1, 2, 3)]
    registros = [_cdi(c, data=d) for c in chaves for d in ("29/10/2026", "30/10/2026")]
    validos, quarentena = deduplicar_por_data("cdi_diario", registros)
    assert quarentena == []
    assert [r.data for r in validos] == [dt.date(2026, 10, 29), dt.date(2026, 10, 30)]
    assert all(isinstance(r, CdiDiario) and r.chave_raw == chaves[0] for r in validos)


def test_ptax_divergente_vai_para_quarentena_uma_linha_por_bruto():
    a, b = _chave_ptax("2026-11-02"), _chave_ptax("2026-11-03")
    validos, quarentena = deduplicar_por_data(
        "cambio_diario", [_cambio(a, 5.4321), _cambio(b, 5.4400)]
    )
    assert validos == []
    assert len(quarentena) == 2
    assert {q.chave_raw for q in quarentena} == {a, b}
    assert all(q.motivo == MOTIVO_DIVERGENTE for q in quarentena)
    assert all(q.tabela == "cambio_diario" for q in quarentena)
    assert {json.loads(q.conteudo)["cotacao_venda"] for q in quarentena} == {5.4321, 5.44}


def test_cdi_divergente_so_tira_a_data_divergente():
    a, b = _chave_cdi("2026-11-02"), _chave_cdi("2026-11-03")
    registros = [
        _cdi(a, data="29/10/2026"), _cdi(b, data="29/10/2026"),
        _cdi(a, data="30/10/2026"), _cdi(b, valor="0.055131", data="30/10/2026"),
    ]
    validos, quarentena = deduplicar_por_data("cdi_diario", registros)
    assert [r.data for r in validos] == [dt.date(2026, 10, 29)]
    assert len(quarentena) == 2
    assert all(q.motivo == "valor divergente entre brutos" for q in quarentena)


def test_contagem_por_tabela_no_cenario_do_rf07():
    chave = _chave_ptax("2026-11-03")
    resultados = [
        validar("preco_diario", preco_do_bruto, _preco(None), CHAVE_PRECOS, DIA, 24269, CHAVE_PRECOS),
        validar("preco_diario", preco_do_bruto, _preco(), CHAVE_PRECOS, DIA, 24269, CHAVE_PRECOS),
        validar("cambio_diario", cambio_do_bruto, _ptax(venda=None), chave, chave),
        validar("cambio_diario", cambio_do_bruto, _ptax(boletim="Intermediário"), chave, chave),
    ]
    linhas = [r for r in resultados if isinstance(r, LinhaQuarentena)]
    contagem = contar_por_tabela(linhas)
    assert contagem == {"colecao": 0, "produto": 0, "preco_diario": 1,
                        "cambio_diario": 1, "cdi_diario": 0}
    assert formatar_contagem(contagem) == "preco_diario: 1, cambio_diario: 1, demais: 0"


def test_contagem_soma_divergencias_em_demais():
    a, b = _chave_cdi("2026-11-02"), _chave_cdi("2026-11-03")
    _, quarentena = deduplicar_por_data("cdi_diario", [_cdi(a), _cdi(b, valor="0.06")])
    contagem = contar_por_tabela(quarentena)
    assert contagem["cdi_diario"] == 2
    assert formatar_contagem(contagem) == "preco_diario: 0, cambio_diario: 0, demais: 2"
