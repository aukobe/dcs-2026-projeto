"""Testes do Cliente HTTP (T-04; RF-03, RNF-12).

Servidor simulado por um adaptador `requests` que registra as requisições e
devolve respostas roteirizadas; relógio simulado, sem espera real nem rede.
"""

from dataclasses import replace
import logging

import pytest
import requests
from requests.adapters import BaseAdapter

from tcg.coleta.http import ClienteHttp, FalhaRequisicaoError, LimiteRequisicoesError
from tcg.config import ler_parametros

URL = "https://tcgcsv.com/tcgplayer/3/24269/prices"
UA = "tcg-dri-teste/0.1"


class ServidorSimulado(BaseAdapter):
    def __init__(self, relogio, roteiro):
        super().__init__()
        self.relogio = relogio
        self.roteiro = list(roteiro)
        self.recebidas = []  # (instante, PreparedRequest)

    def send(self, request, **kwargs):
        self.recebidas.append((self.relogio.agora, request))
        item = self.roteiro.pop(0) if self.roteiro else (200, b"ok")
        if isinstance(item, Exception):
            raise item
        status, corpo = item
        resposta = requests.Response()
        resposta.status_code = status
        resposta._content = corpo
        resposta.request = request
        resposta.url = request.url
        return resposta

    def close(self):
        pass


class Relogio:
    def __init__(self):
        self.agora = 1000.0
        self.esperas = []

    def __call__(self):
        return self.agora

    def dormir(self, segundos):
        self.esperas.append(segundos)
        self.agora += segundos

    def avancar(self, segundos):
        self.agora += segundos


@pytest.fixture
def relogio():
    return Relogio()


def criar(relogio, roteiro, **mudancas):
    parametros = replace(ler_parametros(), **mudancas)
    servidor = ServidorSimulado(relogio, roteiro)
    sessao = requests.Session()
    sessao.mount("https://", servidor)
    cliente = ClienteHttp(
        parametros=parametros,
        user_agent=UA,
        sessao=sessao,
        relogio=relogio,
        dormir=relogio.dormir,
    )
    return cliente, servidor


def test_user_agent_em_toda_requisicao(relogio):
    cliente, servidor = criar(relogio, [(503, b""), (200, b"a"), (200, b"b")])
    cliente.get(URL, fonte="tcgcsv")
    cliente.get(URL, fonte="tcgcsv")
    assert len(servidor.recebidas) == 3
    assert all(r.headers["User-Agent"] == UA for _, r in servidor.recebidas)


def test_user_agent_lido_de_tcg_user_agent(relogio, monkeypatch):
    monkeypatch.setenv("TCG_USER_AGENT", "ua-do-ambiente/1.0")
    servidor = ServidorSimulado(relogio, [(200, b"x")])
    sessao = requests.Session()
    sessao.mount("https://", servidor)
    cliente = ClienteHttp(sessao=sessao, relogio=relogio, dormir=relogio.dormir)
    cliente.get(URL)
    assert servidor.recebidas[0][1].headers["User-Agent"] == "ua-do-ambiente/1.0"


def test_pausa_minima_100ms(relogio):
    cliente, servidor = criar(relogio, [(200, b"")] * 4)
    for _ in range(3):
        cliente.get(URL)
        relogio.avancar(0.03)  # o chamador volta antes de 100 ms
    instantes = [t for t, _ in servidor.recebidas]
    intervalos = [b - a for a, b in zip(instantes, instantes[1:])]
    assert all(i >= 0.1 - 1e-9 for i in intervalos)
    assert relogio.esperas == pytest.approx([0.07, 0.07])

    relogio.avancar(5)  # já passou da pausa: não dorme
    relogio.esperas.clear()
    cliente.get(URL)
    assert relogio.esperas == []


def test_dois_503_esperas_2_e_4_sucesso_na_terceira(relogio, caplog):
    corpo = b'{"results": [{"productId": 1}]}\r\n'
    cliente, servidor = criar(relogio, [(503, b""), (503, b""), (200, corpo)])
    with caplog.at_level(logging.INFO, logger="tcg.coleta.http"):
        recebido = cliente.get(URL, fonte="tcgcsv")
    assert recebido == corpo
    assert len(servidor.recebidas) == 3
    assert relogio.esperas == [2, 4]
    assert "tentativa=3/4" in caplog.text


def test_falha_total_levanta_erro_e_registra_no_log(relogio, caplog):
    roteiro = [(503, b""), requests.ConnectionError("x"), (502, b""), (503, b"")]
    cliente, servidor = criar(relogio, roteiro)
    with caplog.at_level(logging.INFO, logger="tcg.coleta.http"):
        with pytest.raises(FalhaRequisicaoError):
            cliente.get(URL, fonte="tcgcsv")
    assert len(servidor.recebidas) == 4
    assert relogio.esperas == [2, 4, 8]
    erros = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(erros) == 1 and "após 4 tentativas" in erros[0].getMessage()


def test_erro_nao_transitorio_nao_repete(relogio, caplog):
    cliente, servidor = criar(relogio, [(404, b"")])
    with caplog.at_level(logging.INFO, logger="tcg.coleta.http"):
        with pytest.raises(FalhaRequisicaoError):
            cliente.get(URL)
    assert len(servidor.recebidas) == 1
    assert relogio.esperas == []
    assert "status=404" in caplog.text


def test_requisicao_alem_do_limite_e_recusada(relogio, caplog):
    cliente, servidor = criar(relogio, [(200, b"")] * 3, limite_requisicoes_dia=2)
    cliente.get(URL)
    cliente.get(URL)
    with caplog.at_level(logging.ERROR, logger="tcg.coleta.http"):
        with pytest.raises(LimiteRequisicoesError):
            cliente.get(URL)
    assert len(servidor.recebidas) == 2
    assert cliente.requisicoes == 2
    assert "limite diário" in caplog.text


def test_repeticoes_contam_no_limite(relogio):
    cliente, servidor = criar(relogio, [(503, b""), (503, b""), (200, b"")], limite_requisicoes_dia=2)
    with pytest.raises(LimiteRequisicoesError):
        cliente.get(URL)
    assert len(servidor.recebidas) == 2
