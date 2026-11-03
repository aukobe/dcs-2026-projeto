"""Testes dos clientes TCGCSV e BCB (T-05; RF-01).

Cliente HTTP falso que registra URL e fonte e devolve bytes fixos; sem rede.
"""

from dataclasses import replace
import datetime as dt

import pytest

from tcg.coleta.bcb import ClienteBcb
from tcg.coleta.tcgcsv import ClienteTcgcsv
from tcg.config import ler_colecao, ler_parametros

# BOM, \r\n, byte não UTF-8 e espaço final: nada pode ser alterado.
CORPO = b"\xef\xbb\xbf{\"a\": 1,\r\n \"b\": \"\xff\"}\r\n "


class HttpFalso:
    def __init__(self, corpo=CORPO):
        self.corpo = corpo
        self.chamadas = []  # (url, params, fonte)

    def get(self, url, params=None, fonte=""):
        self.chamadas.append((url, params, fonte))
        return self.corpo


@pytest.fixture
def http():
    return HttpFalso()


def test_urls_tcgcsv_do_group_id_24269(http):
    cliente = ClienteTcgcsv(http, ler_colecao())
    assert cliente.url_products() == "https://tcgcsv.com/tcgplayer/3/24269/products"
    assert cliente.url_prices() == "https://tcgcsv.com/tcgplayer/3/24269/prices"


def test_url_ptax_janela_de_10_dias(http):
    cliente = ClienteBcb(http, ler_parametros())
    assert cliente.url_ptax(dt.date(2026, 11, 3)) == (
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        "CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,"
        "dataFinalCotacao=@dataFinalCotacao)"
        "?@moeda='USD'&@dataInicial='10-25-2026'&@dataFinalCotacao='11-03-2026'"
        "&$format=json"
    )


def test_url_cdi_janela_de_10_dias(http):
    cliente = ClienteBcb(http, ler_parametros())
    assert cliente.url_cdi(dt.date(2026, 11, 3)) == (
        "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
        "?formato=json&dataInicial=25/10/2026&dataFinal=03/11/2026"
    )


def test_janela_inclui_os_dois_extremos_e_tem_10_dias(http):
    inicio, fim = ClienteBcb(http, ler_parametros()).janela(dt.date(2026, 11, 3))
    assert (inicio, fim) == (dt.date(2026, 10, 25), dt.date(2026, 11, 3))
    assert (fim - inicio).days + 1 == 10


def test_janela_atravessa_virada_do_ano(http):
    cliente = ClienteBcb(http, ler_parametros())
    data = dt.date(2026, 1, 5)
    assert cliente.janela(data) == (dt.date(2025, 12, 27), data)
    assert "@dataInicial='12-27-2025'" in cliente.url_ptax(data)
    assert "dataInicial=27/12/2025&dataFinal=05/01/2026" in cliente.url_cdi(data)


def test_janela_segue_o_parametro(http):
    parametros = replace(ler_parametros(), janela_dias=5)
    cliente = ClienteBcb(http, parametros)
    assert cliente.janela(dt.date(2026, 11, 3)) == (dt.date(2026, 10, 30), dt.date(2026, 11, 3))


def test_janela_invalida_e_recusada(http):
    with pytest.raises(ValueError):
        ClienteBcb(http, replace(ler_parametros(), janela_dias=0))


def test_corpo_devolvido_sem_alteracao_nas_quatro_fontes(http):
    tcg = ClienteTcgcsv(http, ler_colecao())
    bcb = ClienteBcb(http, ler_parametros())
    data = dt.date(2026, 11, 3)
    corpos = [tcg.buscar_products(), tcg.buscar_prices(), bcb.buscar_ptax(data), bcb.buscar_cdi(data)]
    assert all(corpo is CORPO for corpo in corpos)


def test_cada_busca_faz_uma_chamada_com_url_e_fonte(http):
    tcg = ClienteTcgcsv(http, ler_colecao())
    bcb = ClienteBcb(http, ler_parametros())
    data = dt.date(2026, 11, 3)
    tcg.buscar_products()
    tcg.buscar_prices()
    bcb.buscar_ptax(data)
    bcb.buscar_cdi(data)
    assert http.chamadas == [
        (tcg.url_products(), None, "tcgcsv_products"),
        (tcg.url_prices(), None, "tcgcsv_prices"),
        (bcb.url_ptax(data), None, "bcb_ptax"),
        (bcb.url_cdi(data), None, "bcb_cdi"),
    ]


def test_url_montada_chega_intacta_a_requisicao_preparada():
    """O requests não recodifica aspas, @ e $ da URL da PTAX nem as barras do CDI."""
    import requests

    bcb = ClienteBcb(HttpFalso(), ler_parametros())
    data = dt.date(2026, 11, 3)
    for url in (bcb.url_ptax(data), bcb.url_cdi(data)):
        preparada = requests.Request("GET", url).prepare()
        assert preparada.url.replace("%27", "'") == url
