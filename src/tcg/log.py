"""Configuração do logging (specs/plan.md, seção 11).

Saída padrão, data e hora em UTC, nível e componente. Um filtro troca por
`***` qualquer ocorrência dos valores de `MINIO_ACCESS_KEY` e
`MINIO_SECRET_KEY` antes da formatação (RNF-08).
"""

from __future__ import annotations

import logging
import os
import sys
import time

VARIAVEIS_SECRETAS = ("MINIO_ACCESS_KEY", "MINIO_SECRET_KEY")
MASCARA = "***"
FORMATO = "%(asctime)s %(levelname)s %(name)s: %(message)s"
FORMATO_DATA = "%Y-%m-%dT%H:%M:%SZ"


class FormatadorUTC(logging.Formatter):
    converter = time.gmtime


class FiltroSegredos(logging.Filter):
    """Mascara os valores das credenciais na mensagem, nos argumentos e na exceção."""

    def _segredos(self) -> list[str]:
        valores = [os.environ.get(nome, "") for nome in VARIAVEIS_SECRETAS]
        return sorted({v for v in valores if v}, key=len, reverse=True)

    def _mascarar(self, texto: str, segredos: list[str]) -> str:
        for segredo in segredos:
            texto = texto.replace(segredo, MASCARA)
        return texto

    def filter(self, registro: logging.LogRecord) -> bool:
        segredos = self._segredos()
        if not segredos:
            return True
        mensagem = registro.getMessage()
        if registro.exc_info and not registro.exc_text:
            registro.exc_text = logging.Formatter().formatException(registro.exc_info)
        registro.msg = self._mascarar(mensagem, segredos)
        registro.args = None
        if registro.exc_text:
            registro.exc_text = self._mascarar(registro.exc_text, segredos)
        if registro.stack_info:
            registro.stack_info = self._mascarar(registro.stack_info, segredos)
        return True


def configurar_log(nivel: int = logging.INFO, fluxo=None) -> logging.Handler:
    """Instala no logger raiz um único handler na saída padrão."""
    handler = logging.StreamHandler(fluxo or sys.stdout)
    handler.setFormatter(FormatadorUTC(FORMATO, FORMATO_DATA))
    handler.addFilter(FiltroSegredos())
    raiz = logging.getLogger()
    for antigo in list(raiz.handlers):
        if getattr(antigo, "_tcg", False):
            raiz.removeHandler(antigo)
    handler._tcg = True
    raiz.addHandler(handler)
    raiz.setLevel(nivel)
    return handler
