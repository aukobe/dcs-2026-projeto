"""Configuração comum dos testes.

Bloqueio de rede nos testes de unidade (RNF-05): todo teste em `tests/unidade/`
roda com `socket.socket` e `socket.getaddrinfo` substituídos por versões que
falham com `RedeBloqueadaError`. Os testes de `tests/integracao/` não são
afetados (usam cassetes e MinIO descartável).
"""

from pathlib import Path
import socket

import pytest

PASTA_UNIDADE = Path(__file__).parent / "unidade"


class RedeBloqueadaError(RuntimeError):
    """Tentativa de acesso à rede num teste de unidade.

    Herda de RuntimeError, e não de OSError, para que bibliotecas como
    requests/urllib3 e socket.create_connection não a capturem nem tentem
    de novo: a falha chega explícita ao teste.
    """


def _mensagem(operacao: str, detalhe: object) -> str:
    return f"rede bloqueada nos testes de unidade (RNF-05): tentativa de {operacao} {detalhe!r}"


class _SocketBloqueado:
    def __init__(self, *args, **kwargs):
        raise RedeBloqueadaError(_mensagem("abrir socket", args))


def _getaddrinfo_bloqueado(host, *args, **kwargs):
    raise RedeBloqueadaError(_mensagem("resolver DNS de", host))


def _eh_teste_de_unidade(caminho: Path) -> bool:
    return caminho.resolve().is_relative_to(PASTA_UNIDADE.resolve())


@pytest.fixture(autouse=True)
def bloquear_rede(request, monkeypatch):
    """Bloqueia a rede em todo teste de `tests/unidade/` (RNF-05)."""
    if _eh_teste_de_unidade(request.node.path):
        monkeypatch.setattr(socket, "socket", _SocketBloqueado)
        monkeypatch.setattr(socket, "getaddrinfo", _getaddrinfo_bloqueado)
    yield
