"""Cliente TCGCSV (specs/plan.md, seção 4; RF-01).

Busca `products` e `prices` do groupId da coleção (24269, de
`config/colecao.toml`) pelo Cliente HTTP, que aplica User-Agent, pausa,
repetição e limite (RF-03, RNF-12). O corpo é devolvido sem alteração.
"""

from __future__ import annotations

from tcg.coleta.http import ClienteHttp
from tcg.config import Colecao, ler_colecao

URL_BASE = "https://tcgcsv.com/tcgplayer/3"


class ClienteTcgcsv:
    def __init__(self, http: ClienteHttp, colecao: Colecao | None = None) -> None:
        self._http = http
        self._group_id = (colecao or ler_colecao()).group_id

    def url_products(self) -> str:
        return f"{URL_BASE}/{self._group_id}/products"

    def url_prices(self) -> str:
        return f"{URL_BASE}/{self._group_id}/prices"

    def buscar_products(self) -> bytes:
        return self._http.get(self.url_products(), fonte="tcgcsv_products")

    def buscar_prices(self) -> bytes:
        return self._http.get(self.url_prices(), fonte="tcgcsv_prices")
