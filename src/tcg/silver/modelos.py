"""Modelos pydantic das cinco tabelas da silver (T-25; RF-07, RF-08, RF-09).

Cada modelo tem os nomes de coluna do contrato de `specs/spec.md`. As funções
`*_do_bruto` convertem uma linha do bruto, no formato real registrado em
`docs/evidencias/T-05_endpoints_bcb.md` e `docs/evidencias/T-13_hipoteses.md`,
num modelo validado.

- Linha inválida levanta `pydantic.ValidationError`; capturar o erro e gravar
  a quarentena com motivo é papel de `quarentena.py` (T-26).
- Boletim da PTAX diferente de `Fechamento` não é inválido: `cambio_do_bruto`
  devolve `None` (descarte por regra, RF-07).
- Preço ausente ou nulo vira `None`; nada é copiado de outro dia (RF-08).
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, StrictFloat, StrictInt

from tcg.config import Colecao as ColecaoConfig

BOLETIM_FECHAMENTO = "Fechamento"
RARIDADE_CODE_CARD = "Code Card"
MOEDA_TCGCSV = "USD"
FONTE_TCGCSV = "tcgcsv"

TipoProduto = Literal["carta", "selado"]


class _Modelo(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Colecao(_Modelo):
    group_id: StrictInt
    nome: str
    sigla: str
    data_lancamento: dt.date
    responsavel: str


class Produto(_Modelo):
    product_id: StrictInt
    group_id: StrictInt
    nome: str
    tipo_produto: TipoProduto
    raridade: str | None
    numero: str | None
    image_url: str | None
    url: str | None


class PrecoDiario(_Modelo):
    data: dt.date
    product_id: StrictInt
    group_id: StrictInt
    acabamento: str
    market_price: float | None
    low_price: float | None
    mid_price: float | None
    high_price: float | None
    moeda: str
    fonte: str
    chave_raw: str


class CambioDiario(_Modelo):
    data: dt.date
    cotacao_compra: float
    cotacao_venda: float
    data_hora_cotacao: dt.datetime
    boletim: Literal["Fechamento"]
    chave_raw: str


class CdiDiario(_Modelo):
    data: dt.date
    taxa_dia: StrictFloat
    chave_raw: str


def campo_estendido(item: dict[str, Any], nome: str) -> str | None:
    """Valor de um campo de `extendedData`; ausente ou vazio vira `None`."""
    for campo in item.get("extendedData") or []:
        if campo.get("name") == nome:
            valor = campo.get("value")
            return None if valor in (None, "") else valor
    return None


def classificar_tipo_produto(numero: str | None, raridade: str | None) -> TipoProduto:
    """Regra validada no T-13: sem número é selado; Code Card é sempre carta."""
    if raridade == RARIDADE_CODE_CARD:
        return "carta"
    return "selado" if numero is None else "carta"


def colecao_da_config(colecao: ColecaoConfig) -> Colecao:
    return Colecao(
        group_id=colecao.group_id,
        nome=colecao.nome,
        sigla=colecao.sigla,
        data_lancamento=colecao.data_lancamento,
        responsavel=colecao.responsavel,
    )


def produto_do_bruto(item: dict[str, Any]) -> Produto:
    """Um item de `results` de `products.json`."""
    numero = campo_estendido(item, "Number")
    raridade = campo_estendido(item, "Rarity")
    return Produto(
        product_id=item.get("productId"),
        group_id=item.get("groupId"),
        nome=item.get("name"),
        tipo_produto=classificar_tipo_produto(numero, raridade),
        raridade=raridade,
        numero=numero,
        image_url=item.get("imageUrl") or None,
        url=item.get("url") or None,
    )


def preco_do_bruto(
    linha: dict[str, Any], data: dt.date, group_id: int, chave_raw: str
) -> PrecoDiario:
    """Uma linha de `results` de `prices.json`; `acabamento` = `subTypeName`."""
    return PrecoDiario(
        data=data,
        product_id=linha.get("productId"),
        group_id=group_id,
        acabamento=linha.get("subTypeName"),
        market_price=linha.get("marketPrice"),
        low_price=linha.get("lowPrice"),
        mid_price=linha.get("midPrice"),
        high_price=linha.get("highPrice"),
        moeda=MOEDA_TCGCSV,
        fonte=FONTE_TCGCSV,
        chave_raw=chave_raw,
    )


def cambio_do_bruto(item: dict[str, Any], chave_raw: str) -> CambioDiario | None:
    """Um item de `value` de `cotacao.json`.

    Devolve `None` para boletins diferentes de `Fechamento` (descarte por
    regra, sem erro). A data do boletim sai de `dataHoraCotacao`
    (`AAAA-MM-DD HH:MM:SS.ffffff`, sem fuso).
    """
    if item.get("tipoBoletim") != BOLETIM_FECHAMENTO:
        return None
    texto = item.get("dataHoraCotacao")
    data_hora = dt.datetime.fromisoformat(texto) if isinstance(texto, str) else texto
    return CambioDiario(
        data=data_hora.date() if isinstance(data_hora, dt.datetime) else None,
        cotacao_compra=item.get("cotacaoCompra"),
        cotacao_venda=item.get("cotacaoVenda"),
        data_hora_cotacao=data_hora,
        boletim=BOLETIM_FECHAMENTO,
        chave_raw=chave_raw,
    )


def _texto_para_float(valor: Any) -> Any:
    """`"0.050788"` (texto com ponto decimal, como publicado) vira float.

    Texto que não é número decimal continua texto e falha na validação.
    """
    if isinstance(valor, str):
        try:
            return float(valor)
        except ValueError:
            return valor
    return valor


def _texto_para_data_br(valor: Any) -> Any:
    if isinstance(valor, str):
        try:
            return dt.datetime.strptime(valor, "%d/%m/%Y").date()
        except ValueError:
            return valor
    return valor


def cdi_do_bruto(item: dict[str, Any], chave_raw: str) -> CdiDiario:
    """Um item de `cdi.json`: `{"data": "DD/MM/AAAA", "valor": "<texto>"}`."""
    return CdiDiario(
        data=_texto_para_data_br(item.get("data")),
        taxa_dia=_texto_para_float(item.get("valor")),
        chave_raw=chave_raw,
    )
