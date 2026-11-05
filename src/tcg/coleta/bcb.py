"""Cliente BCB (specs/plan.md, seção 4; RF-01, RES-04, RES-05).

- PTAX: Olinda, `CotacaoMoedaPeriodo` com moeda USD (traz o tipo de boletim).
- CDI: SGS, série 12 (% ao dia).
- Janela de `janela_dias` dias corridos até a data de referência da coleta
  (ADR-007), com os dois extremos incluídos: D − (janela_dias − 1) até D.

As URLs são montadas como texto completo (sem `params=`), para que as aspas e
os prefixos `@`/`$` do OData cheguem ao servidor como na documentação do BCB.
O corpo é devolvido sem alteração. Endpoints confirmados em
`docs/evidencias/T-05_endpoints_bcb.md`.
"""

from __future__ import annotations

import datetime as dt

from tcg.coleta.http import ClienteHttp
from tcg.config import Parametros, ler_parametros

URL_PTAX = (
    "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    "CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,"
    "dataFinalCotacao=@dataFinalCotacao)"
)
URL_CDI = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
MOEDA = "USD"


class ClienteBcb:
    def __init__(self, http: ClienteHttp, parametros: Parametros | None = None) -> None:
        self._http = http
        self._janela_dias = (parametros or ler_parametros()).janela_dias
        if self._janela_dias < 1:
            raise ValueError("janela_dias deve ser pelo menos 1")

    def janela(self, data_referencia: dt.date) -> tuple[dt.date, dt.date]:
        """(data inicial, data final) da janela, extremos incluídos."""
        return data_referencia - dt.timedelta(days=self._janela_dias - 1), data_referencia

    def url_ptax(self, data_referencia: dt.date) -> str:
        inicio, fim = self.janela(data_referencia)
        return (
            f"{URL_PTAX}?@moeda='{MOEDA}'"
            f"&@dataInicial='{inicio:%m-%d-%Y}'"
            f"&@dataFinalCotacao='{fim:%m-%d-%Y}'"
            "&$format=json"
        )

    def url_cdi(self, data_referencia: dt.date) -> str:
        inicio, fim = self.janela(data_referencia)
        return (
            f"{URL_CDI}?formato=json"
            f"&dataInicial={inicio:%d/%m/%Y}"
            f"&dataFinal={fim:%d/%m/%Y}"
        )

    def buscar_ptax(self, data_referencia: dt.date) -> bytes:
        return self._http.get(self.url_ptax(data_referencia), fonte="bcb_ptax")

    def buscar_cdi(self, data_referencia: dt.date) -> bytes:
        return self._http.get(self.url_cdi(data_referencia), fonte="bcb_cdi")
