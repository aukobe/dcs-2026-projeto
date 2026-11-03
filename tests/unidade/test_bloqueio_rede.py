"""T-02: os testes de unidade rodam com a rede bloqueada (RNF-05)."""

import socket

import pytest
import requests

from conftest import RedeBloqueadaError

MENSAGEM = r"rede bloqueada nos testes de unidade \(RNF-05\)"


def test_socket_direto_falha():
    with pytest.raises(RedeBloqueadaError, match=MENSAGEM):
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def test_create_connection_falha():
    with pytest.raises(RedeBloqueadaError, match=MENSAGEM):
        socket.create_connection(("127.0.0.1", 9), timeout=1)


def test_requests_falha():
    with pytest.raises(RedeBloqueadaError, match=MENSAGEM):
        requests.get("http://127.0.0.1:9", timeout=1)


def test_resolucao_dns_falha():
    with pytest.raises(RedeBloqueadaError, match=MENSAGEM + r".*tcgcsv\.com"):
        socket.getaddrinfo("tcgcsv.com", 443)
