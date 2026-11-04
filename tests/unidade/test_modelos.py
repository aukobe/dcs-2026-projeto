"""Testes dos modelos da silver (T-25; RF-07, RF-08, RF-09).

Os dados de entrada reproduzem o formato real do bruto, registrado em
`docs/evidencias/T-05_endpoints_bcb.md` e `docs/evidencias/T-13_hipoteses.md`.
"""

import datetime as dt
import json

from pydantic import ValidationError
import pytest

from tcg.config import ler_colecao
from tcg.silver.modelos import (
    CambioDiario,
    CdiDiario,
    Colecao,
    PrecoDiario,
    Produto,
    cambio_do_bruto,
    cdi_do_bruto,
    colecao_da_config,
    preco_do_bruto,
    produto_do_bruto,
)

CHAVE_PRECOS = "raw/tcgplayer/group_id=24269/data=2026-11-03/prices.json"
CHAVE_PTAX = "raw/bcb_ptax/group_id=24269/data=2026-11-03/cotacao.json"
CHAVE_CDI = "raw/bcb_cdi/group_id=24269/data=2026-11-03/cdi.json"
DIA = dt.date(2026, 11, 3)

# Resposta real do SGS (série 12) em 2026-11-03, copiada de T-05_endpoints_bcb.md.
RESPOSTA_CDI_REAL = (
    '[{"data":"26/10/2026","valor":"0.050788"},{"data":"27/10/2026","valor":"0.050788"},'
    '{"data":"28/10/2026","valor":"0.050788"},{"data":"29/10/2026","valor":"0.050788"},'
    '{"data":"30/10/2026","valor":"0.050788"}]'
)


def _produto(product_id, nome, numero=None, raridade=None):
    extended = [{"name": "CardText", "displayName": "Card Text", "value": "..."}]
    if numero is not None:
        extended.append({"name": "Number", "displayName": "Card Number", "value": numero})
    if raridade is not None:
        extended.append({"name": "Rarity", "displayName": "Rarity", "value": raridade})
    return {
        "productId": product_id,
        "name": nome,
        "cleanName": nome,
        "imageUrl": f"https://tcgplayer-cdn.tcgplayer.com/product/{product_id}_200w.jpg",
        "categoryId": 3,
        "groupId": 24269,
        "url": f"https://www.tcgplayer.com/product/{product_id}/x",
        "modifiedOn": "2025-05-30T04:10:27.47",
        "imageCount": 1,
        "presaleInfo": {"isPresale": False, "releasedOn": "2025-05-30T00:00:00", "note": None},
        "extendedData": extended,
    }


def _linha_preco(**mudancas):
    linha = {
        "productId": 624675,
        "lowPrice": 400.0,
        "midPrice": 561.24,
        "highPrice": 4998.0,
        "marketPrice": 403.76,
        "directLowPrice": None,
        "subTypeName": "Normal",
    }
    linha.update(mudancas)
    return linha


def _boletim(tipo, **mudancas):
    item = {
        "paridadeCompra": 1.0,
        "paridadeVenda": 1.0,
        "cotacaoCompra": 5.4998,
        "cotacaoVenda": 5.5007,
        "dataHoraCotacao": "2026-10-26 13:09:51.106105",
        "tipoBoletim": tipo,
    }
    item.update(mudancas)
    return item


# RF-09 ---------------------------------------------------------------------


def test_tipo_produto_rf09_selado_carta_e_code_card():
    selado = produto_do_bruto(_produto(624679, "Destined Rivals Booster Box"))
    carta = produto_do_bruto(_produto(624700, "Team Rocket's Mewtwo ex", "081/182", "Double Rare"))
    code_card = produto_do_bruto(
        _produto(637654, "Code Card - Destined Rivals Premium Checklane Blister", None, "Code Card")
    )

    assert [selado.tipo_produto, carta.tipo_produto, code_card.tipo_produto] == [
        "selado",
        "carta",
        "carta",
    ]
    assert carta.numero == "081/182" and carta.raridade == "Double Rare"
    assert selado.numero is None and selado.raridade is None
    assert isinstance(carta.product_id, int) and isinstance(carta.group_id, int)


def test_numero_vazio_conta_como_sem_numero():
    produto = produto_do_bruto(_produto(624681, "Destined Rivals Half Booster Box", numero=""))
    assert produto.numero is None
    assert produto.tipo_produto == "selado"


def test_produto_sem_product_id_invalido():
    item = _produto(1, "x")
    del item["productId"]
    with pytest.raises(ValidationError):
        produto_do_bruto(item)


# RF-08 e linha de preço ----------------------------------------------------


def test_preco_valido_tipos_e_acabamento_do_subtypename():
    for acabamento in ("Normal", "Holofoil", "Reverse Holofoil"):
        preco = preco_do_bruto(_linha_preco(subTypeName=acabamento), DIA, 24269, CHAVE_PRECOS)
        assert preco.acabamento == acabamento

    preco = preco_do_bruto(_linha_preco(), DIA, 24269, CHAVE_PRECOS)
    assert preco.data == DIA and type(preco.data) is dt.date
    assert type(preco.product_id) is int and type(preco.group_id) is int
    for valor in (preco.market_price, preco.low_price, preco.mid_price, preco.high_price):
        assert type(valor) is float
    assert preco.market_price == 403.76
    assert (preco.moeda, preco.fonte, preco.chave_raw) == ("USD", "tcgcsv", CHAVE_PRECOS)


@pytest.mark.parametrize("ausente", ["nulo", "sem_chave"])
def test_market_price_ausente_vira_nulo_sem_copia_de_outro_dia(ausente):
    ontem = preco_do_bruto(
        _linha_preco(productId=637654, marketPrice=1.23), DIA - dt.timedelta(days=1), 24269, "ontem"
    )
    assert ontem.market_price == 1.23

    linha = _linha_preco(productId=637654)
    if ausente == "nulo":
        linha["marketPrice"] = None
    else:
        del linha["marketPrice"]
    hoje = preco_do_bruto(linha, DIA, 24269, CHAVE_PRECOS)

    assert hoje.market_price is None
    assert hoje.product_id == 637654 and hoje.data == DIA
    assert hoje.low_price == 400.0


def test_linha_de_preco_sem_product_id_invalida():
    linha = _linha_preco()
    del linha["productId"]
    with pytest.raises(ValidationError) as erro:
        preco_do_bruto(linha, DIA, 24269, CHAVE_PRECOS)
    assert "product_id" in str(erro.value)


# RF-07: PTAX ---------------------------------------------------------------


@pytest.mark.parametrize("tipo", ["Abertura", "Intermediário"])
def test_boletim_intermediario_descartado_sem_erro(tipo):
    assert cambio_do_bruto(_boletim(tipo), CHAVE_PTAX) is None
    # descarte por regra mesmo com campo ausente: não é linha inválida
    assert cambio_do_bruto(_boletim(tipo, cotacaoVenda=None), CHAVE_PTAX) is None


def test_boletim_fechamento_valido_tipos_do_contrato():
    cambio = cambio_do_bruto(_boletim("Fechamento"), CHAVE_PTAX)

    assert cambio == CambioDiario(
        data=dt.date(2026, 10, 26),
        cotacao_compra=5.4998,
        cotacao_venda=5.5007,
        data_hora_cotacao=dt.datetime(2026, 10, 26, 13, 9, 51, 106105),
        boletim="Fechamento",
        chave_raw=CHAVE_PTAX,
    )
    assert type(cambio.cotacao_compra) is float and type(cambio.cotacao_venda) is float
    assert type(cambio.data) is dt.date and type(cambio.data_hora_cotacao) is dt.datetime


@pytest.mark.parametrize("ausente", ["nulo", "sem_chave"])
def test_fechamento_sem_cotacao_venda_invalido(ausente):
    item = _boletim("Fechamento")
    if ausente == "nulo":
        item["cotacaoVenda"] = None
    else:
        del item["cotacaoVenda"]
    with pytest.raises(ValidationError) as erro:
        cambio_do_bruto(item, CHAVE_PTAX)
    assert "cotacao_venda" in str(erro.value)


# CDI -----------------------------------------------------------------------


def test_cdi_resposta_real_texto_com_ponto_decimal_vira_float():
    itens = json.loads(RESPOSTA_CDI_REAL)
    cdis = [cdi_do_bruto(item, CHAVE_CDI) for item in itens]

    assert [c.data for c in cdis] == [dt.date(2026, 10, d) for d in range(26, 31)]
    assert all(type(c.taxa_dia) is float and c.taxa_dia == 0.050788 for c in cdis)
    assert all(c.chave_raw == CHAVE_CDI for c in cdis)


@pytest.mark.parametrize("valor", [None, "", "abc"])
def test_cdi_valor_ausente_ou_nao_numerico_invalido(valor):
    with pytest.raises(ValidationError):
        cdi_do_bruto({"data": "26/10/2026", "valor": valor}, CHAVE_CDI)


# Coleção -------------------------------------------------------------------


def test_colecao_vem_da_config_versionada():
    colecao = colecao_da_config(ler_colecao())
    assert colecao == Colecao(
        group_id=24269,
        nome="SV10: Destined Rivals",
        sigla="DRI",
        data_lancamento=dt.date(2025, 5, 30),
        responsavel="Augusto",
    )


def test_modelos_tem_as_colunas_do_contrato():
    assert list(Colecao.model_fields) == [
        "group_id", "nome", "sigla", "data_lancamento", "responsavel",
    ]
    assert list(Produto.model_fields) == [
        "product_id", "group_id", "nome", "tipo_produto", "raridade", "numero", "image_url", "url",
    ]
    assert list(PrecoDiario.model_fields) == [
        "data", "product_id", "group_id", "acabamento", "market_price", "low_price",
        "mid_price", "high_price", "moeda", "fonte", "chave_raw",
    ]
    assert list(CambioDiario.model_fields) == [
        "data", "cotacao_compra", "cotacao_venda", "data_hora_cotacao", "boletim", "chave_raw",
    ]
    assert list(CdiDiario.model_fields) == ["data", "taxa_dia", "chave_raw"]
