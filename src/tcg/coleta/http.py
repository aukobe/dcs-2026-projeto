"""Cliente HTTP (specs/plan.md, seção 5; RF-03, RNF-12).

- Sessão `requests` com o User-Agent de `TCG_USER_AGENT` em toda requisição.
- Pausa mínima (`pausa_minima_ms`) entre o início de duas requisições
  consecutivas, inclusive entre repetições.
- Falha transitória (429, 5xx de gateway/servidor, erro de conexão ou tempo
  esgotado) é repetida até `tentativas` vezes após a primeira chamada, com as
  esperas de `esperas_s` (2, 4 e 8 s): no máximo 4 requisições.
- Contador de requisições enviadas, repetições incluídas; a requisição que
  passaria de `limite_requisicoes_dia` é recusada antes do envio.
- O log registra fonte, URL, status, tentativa e espera; nunca credenciais.
"""

from __future__ import annotations

from collections.abc import Callable
import logging
import time

import requests

from tcg.config import Parametros, ler_parametros, ler_user_agent

log = logging.getLogger(__name__)

STATUS_TRANSITORIOS = frozenset({429, 500, 502, 503, 504})
TIMEOUT_PADRAO_S = 30.0


class FalhaRequisicaoError(RuntimeError):
    """Todas as tentativas falharam ou a resposta não é transitória nem 2xx."""


class LimiteRequisicoesError(RuntimeError):
    """A requisição passaria do limite diário (RNF-12)."""


class ClienteHttp:
    def __init__(
        self,
        parametros: Parametros | None = None,
        user_agent: str | None = None,
        sessao: requests.Session | None = None,
        relogio: Callable[[], float] = time.monotonic,
        dormir: Callable[[float], None] = time.sleep,
        timeout_s: float = TIMEOUT_PADRAO_S,
    ) -> None:
        self._parametros = parametros or ler_parametros()
        self._sessao = sessao or requests.Session()
        self._sessao.headers["User-Agent"] = user_agent or ler_user_agent()
        self._relogio = relogio
        self._dormir = dormir
        self._timeout_s = timeout_s
        self._ultimo_envio: float | None = None
        self.requisicoes = 0

    def _respeitar_pausa(self) -> None:
        if self._ultimo_envio is None:
            return
        pausa_s = self._parametros.pausa_minima_ms / 1000
        falta = pausa_s - (self._relogio() - self._ultimo_envio)
        if falta > 0:
            self._dormir(falta)

    def _enviar(self, url: str, params: dict | None) -> requests.Response:
        if self.requisicoes >= self._parametros.limite_requisicoes_dia:
            log.error(
                "requisição recusada: limite diário de %d atingido; url=%s",
                self._parametros.limite_requisicoes_dia,
                url,
            )
            raise LimiteRequisicoesError(
                f"limite diário de {self._parametros.limite_requisicoes_dia} requisições atingido"
            )
        self._respeitar_pausa()
        self._ultimo_envio = self._relogio()
        self.requisicoes += 1
        return self._sessao.get(url, params=params, timeout=self._timeout_s)

    def get(self, url: str, params: dict | None = None, fonte: str = "") -> bytes:
        """Faz GET com pausa, repetição e limite; devolve o corpo sem alteração."""
        esperas = self._parametros.esperas_s
        total = 1 + self._parametros.tentativas
        for tentativa in range(1, total + 1):
            try:
                resposta = self._enviar(url, params)
            except (requests.ConnectionError, requests.Timeout) as erro:
                motivo = f"{type(erro).__name__}"
                status = None
            else:
                status = resposta.status_code
                if 200 <= status < 300:
                    log.info(
                        "requisição ok: fonte=%s url=%s status=%d tentativa=%d/%d",
                        fonte, url, status, tentativa, total,
                    )
                    return resposta.content
                if status not in STATUS_TRANSITORIOS:
                    log.error(
                        "requisição falhou sem repetição: fonte=%s url=%s status=%d tentativa=%d/%d",
                        fonte, url, status, tentativa, total,
                    )
                    raise FalhaRequisicaoError(f"{fonte} {url}: status {status}")
                motivo = f"status {status}"
            if tentativa == total:
                break
            espera = esperas[tentativa - 1]
            log.warning(
                "falha transitória: fonte=%s url=%s %s tentativa=%d/%d espera=%ss",
                fonte, url, motivo, tentativa, total, espera,
            )
            self._dormir(espera)
        log.error(
            "requisição falhou após %d tentativas: fonte=%s url=%s último erro=%s",
            total, fonte, url, motivo,
        )
        raise FalhaRequisicaoError(f"{fonte} {url}: {motivo} após {total} tentativas")
