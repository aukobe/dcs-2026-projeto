"""Composição das cinco carteiras com dados do primeiro dia (T-41; RF-23; ADR-005, ADR-006).

Funções puras: `ler_primeiro_dia` é o único ponto que lê o DuckDB e devolve só os
dados do primeiro dia; as funções `compor_*` recebem esses dados e nada mais, de
modo que dias posteriores não podem alterar a composição (OBJ-05). A saída volta
ao DuckDB por `registrar_composicao`.

Regras comuns (RF-23 e Definições da spec):
- preço de compra = market_price (US$) × PTAX de venda aplicada no primeiro dia,
  sem taxa na compra (limite declarado);
- unidades inteiras = floor(valor alocado / preço de compra); o que sobra de cada
  item fica em caixa, e o caixa da carteira é a soma das sobras e do valor não
  alocado;
- item "com preço" = market_price não nulo e maior que zero;
- desempate total: maior preço, depois menor `product_id`, depois `acabamento`
  em ordem alfabética.

Carteiras:
- selado (ADR-006): booster box (nome com "Booster Box", sem "Case" nem "Half");
  fallback para o selado de maior market_price só quando o booster box não tem
  preço; acima do orçamento fica com zero unidades e o fallback não é acionado.
  Mais de um `product_id` casando com a regra do nome é pendência (erro); o mesmo
  `product_id` com mais de um acabamento com preço escolhe o acabamento em ordem
  alfabética.
- cesta_raras (RF-23): R$ 100 em cada um dos dez itens de carta (sem Code Card)
  de maior market_price.
- propria (ADR-005): R$ 500 no selado de maior preço de compra ≤ R$ 500 e R$ 100
  em cada uma das cinco Illustration Rare (sem Code Card) de maior market_price;
  sem a regra (`regra_propria=False`), status "regra pendente" e sem composição.
- dolar: R$ 1.000 ÷ PTAX de venda aplicada no primeiro dia.
- cdi: R$ 1.000 em caixa.

Liquidação diária, métricas e gold_turma ficam fora deste módulo (T-42 a T-44).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import datetime as dt
import math

import duckdb

ORCAMENTO = 1000.0
VALOR_POR_CARTA = 100.0
N_CESTA_RARAS = 10
ORCAMENTO_PROPRIA_SELADO = 500.0
N_PROPRIA_CARTAS = 5
RARIDADE_PROPRIA = "Illustration Rare"
CARTEIRAS = ("selado", "cesta_raras", "propria", "dolar", "cdi")
STATUS_CALCULADA = "calculada"
STATUS_REGRA_PENDENTE = "regra pendente"
_TOLERANCIA = 1e-9


class PendenciaBoosterBox(ValueError):
    """Mais de um `product_id` casa com a regra do nome do booster box (ADR-006)."""


@dataclass(frozen=True)
class Item:
    """Item (produto × acabamento) com o preço do primeiro dia."""

    product_id: int
    acabamento: str
    nome: str
    tipo_produto: str
    raridade: str | None
    market_price: float | None

    @property
    def com_preco(self) -> bool:
        return self.market_price is not None and self.market_price > 0


@dataclass(frozen=True)
class DadosPrimeiroDia:
    """Tudo o que a composição pode usar: data, PTAX de venda e itens do primeiro dia."""

    data: dt.date
    ptax_venda: float
    itens: tuple[Item, ...]


@dataclass(frozen=True)
class Posicao:
    """Compra de um item: unidades inteiras e sobra em caixa do valor alocado."""

    product_id: int
    acabamento: str
    nome: str
    market_price: float
    preco_compra_brl: float
    valor_alocado_brl: float
    unidades: int
    custo_brl: float
    sobra_brl: float


@dataclass(frozen=True)
class Composicao:
    """Composição de uma carteira no dia de montagem."""

    carteira: str
    status: str
    data_montagem: dt.date
    ptax_venda: float
    posicoes: tuple[Posicao, ...] = ()
    caixa_brl: float = 0.0
    usd: float = 0.0
    fallback: bool = field(default=False)


def _chave(item: Item) -> tuple:
    """Ordem total: maior market_price, menor product_id, acabamento alfabético."""
    return (-item.market_price, item.product_id, item.acabamento)


def _comprar(item: Item, valor: float, ptax_venda: float) -> Posicao:
    preco_compra = item.market_price * ptax_venda
    unidades = math.floor(valor / preco_compra + _TOLERANCIA)
    custo = unidades * preco_compra
    return Posicao(
        product_id=item.product_id,
        acabamento=item.acabamento,
        nome=item.nome,
        market_price=item.market_price,
        preco_compra_brl=preco_compra,
        valor_alocado_brl=valor,
        unidades=unidades,
        custo_brl=custo,
        sobra_brl=valor - custo,
    )


def _caixa(orcamento: float, posicoes: tuple[Posicao, ...]) -> float:
    return orcamento - sum(p.custo_brl for p in posicoes)


# Primeiro dia: menor `data` do fato de preços da coleção. Equivale à definição da
# spec (menor `data` com bruto do TCGCSV da coleção) porque a silver grava uma
# linha por item válido de cada `prices.json`, inclusive com market_price nulo, e
# o fato não filtra preço nulo. Só divergiria se o `prices.json` do primeiro dia
# não tivesse nenhuma linha válida. Diferente de `perguntas.py`, aqui não se
# exige market_price não nulo para definir o primeiro dia.
SQL_PRIMEIRO_DIA = "SELECT min(data) FROM {fato} WHERE group_id = $group_id"

SQL_ITENS = """
SELECT f.product_id, f.acabamento, p.nome, p.tipo_produto, p.raridade, f.market_price
FROM {fato} AS f
JOIN {dim_produto} AS p USING (group_id, product_id)
WHERE f.group_id = $group_id AND f.data = $data
ORDER BY f.product_id, f.acabamento
"""

SQL_PTAX = "SELECT cotacao_venda FROM {fato_cambio} WHERE data = $data"


def ler_primeiro_dia(
    con: duckdb.DuckDBPyConnection,
    fato: str,
    dim_produto: str,
    fato_cambio: str,
    group_id: int = 24269,
) -> DadosPrimeiroDia:
    """Lê do DuckDB só o primeiro dia da coleção: data, PTAX de venda aplicada e itens.

    `fato_cambio` tem um dia de calendário por linha com a PTAX já aplicada
    (último boletim Fechamento com data ≤ dia). Sem PTAX aplicada no primeiro dia,
    a composição não é calculada (erro), e nenhum câmbio é inventado.
    """
    data = con.execute(SQL_PRIMEIRO_DIA.format(fato=fato), {"group_id": group_id}).fetchone()[0]
    if data is None:
        raise ValueError(f"sem preços no fato para o group_id {group_id}")
    linha = con.execute(SQL_PTAX.format(fato_cambio=fato_cambio), {"data": data}).fetchone()
    if linha is None or linha[0] is None or not linha[0] > 0:
        raise ValueError(f"sem PTAX de venda aplicada no primeiro dia {data}")
    itens = tuple(
        Item(*r)
        for r in con.execute(
            SQL_ITENS.format(fato=fato, dim_produto=dim_produto),
            {"group_id": group_id, "data": data},
        ).fetchall()
    )
    return DadosPrimeiroDia(data=data, ptax_venda=float(linha[0]), itens=itens)


def eh_booster_box(item: Item) -> bool:
    """Regra do RF-23 (validada no T-13): "Booster Box" sem "Case" nem "Half"."""
    nome = item.nome or ""
    return (
        item.tipo_produto == "selado"
        and "Booster Box" in nome
        and "Case" not in nome
        and "Half" not in nome
    )


def compor_selado(dados: DadosPrimeiroDia) -> Composicao:
    """Carteira selado (RF-23, ADR-006)."""
    boxes = [i for i in dados.itens if eh_booster_box(i)]
    ids = sorted({i.product_id for i in boxes})
    if len(ids) > 1:
        raise PendenciaBoosterBox(
            f"mais de um product_id casa com a regra do booster box: {ids}"
        )
    box_com_preco = sorted((i for i in boxes if i.com_preco), key=lambda i: i.acabamento)
    fallback = not box_com_preco
    if box_com_preco:
        escolhido = box_com_preco[0]
    else:
        selados = sorted(
            (i for i in dados.itens if i.tipo_produto == "selado" and i.com_preco), key=_chave
        )
        escolhido = selados[0] if selados else None
    posicoes = () if escolhido is None else (_comprar(escolhido, ORCAMENTO, dados.ptax_venda),)
    return Composicao(
        carteira="selado",
        status=STATUS_CALCULADA,
        data_montagem=dados.data,
        ptax_venda=dados.ptax_venda,
        posicoes=posicoes,
        caixa_brl=_caixa(ORCAMENTO, posicoes),
        fallback=fallback,
    )


def _cartas(dados: DadosPrimeiroDia, raridade: str | None = None) -> list[Item]:
    return sorted(
        (
            i for i in dados.itens
            if i.tipo_produto == "carta"
            and i.raridade != "Code Card"
            and i.com_preco
            and (raridade is None or i.raridade == raridade)
        ),
        key=_chave,
    )


def compor_cesta_raras(dados: DadosPrimeiroDia) -> Composicao:
    """Carteira cesta_raras (RF-23): R$ 100 nos dez itens de carta de maior market_price."""
    escolhidos = _cartas(dados)[:N_CESTA_RARAS]
    posicoes = tuple(_comprar(i, VALOR_POR_CARTA, dados.ptax_venda) for i in escolhidos)
    return Composicao(
        carteira="cesta_raras",
        status=STATUS_CALCULADA,
        data_montagem=dados.data,
        ptax_venda=dados.ptax_venda,
        posicoes=posicoes,
        caixa_brl=_caixa(ORCAMENTO, posicoes),
    )


def compor_propria(dados: DadosPrimeiroDia, regra_propria: bool = True) -> Composicao:
    """Carteira propria (ADR-005); sem a regra, "regra pendente" e sem composição."""
    if not regra_propria:
        return Composicao(
            carteira="propria",
            status=STATUS_REGRA_PENDENTE,
            data_montagem=dados.data,
            ptax_venda=dados.ptax_venda,
        )
    limite = ORCAMENTO_PROPRIA_SELADO + _TOLERANCIA
    selados = sorted(
        (
            i for i in dados.itens
            if i.tipo_produto == "selado"
            and i.com_preco
            and i.market_price * dados.ptax_venda <= limite
        ),
        key=_chave,
    )
    posicoes = []
    if selados:
        posicoes.append(_comprar(selados[0], ORCAMENTO_PROPRIA_SELADO, dados.ptax_venda))
    for item in _cartas(dados, RARIDADE_PROPRIA)[:N_PROPRIA_CARTAS]:
        posicoes.append(_comprar(item, VALOR_POR_CARTA, dados.ptax_venda))
    posicoes = tuple(posicoes)
    return Composicao(
        carteira="propria",
        status=STATUS_CALCULADA,
        data_montagem=dados.data,
        ptax_venda=dados.ptax_venda,
        posicoes=posicoes,
        caixa_brl=_caixa(ORCAMENTO, posicoes),
    )


def compor_dolar(dados: DadosPrimeiroDia) -> Composicao:
    """Carteira dolar: R$ 1.000 ÷ PTAX de venda aplicada no primeiro dia."""
    return Composicao(
        carteira="dolar",
        status=STATUS_CALCULADA,
        data_montagem=dados.data,
        ptax_venda=dados.ptax_venda,
        usd=ORCAMENTO / dados.ptax_venda,
    )


def compor_cdi(dados: DadosPrimeiroDia) -> Composicao:
    """Carteira cdi: R$ 1.000 em caixa."""
    return Composicao(
        carteira="cdi",
        status=STATUS_CALCULADA,
        data_montagem=dados.data,
        ptax_venda=dados.ptax_venda,
        caixa_brl=ORCAMENTO,
    )


def compor_carteiras(
    dados: DadosPrimeiroDia, regra_propria: bool = True
) -> tuple[Composicao, ...]:
    """As cinco carteiras, na ordem de `CARTEIRAS`."""
    return (
        compor_selado(dados),
        compor_cesta_raras(dados),
        compor_propria(dados, regra_propria),
        compor_dolar(dados),
        compor_cdi(dados),
    )


def registrar_composicao(
    con: duckdb.DuckDBPyConnection,
    composicoes: tuple[Composicao, ...],
    nome: str = "composicao_carteira",
) -> duckdb.DuckDBPyRelation:
    """Grava a composição numa tabela DuckDB: uma linha por posição e uma de caixa por carteira.

    Linha de caixa: `product_id` e `acabamento` nulos, `caixa_brl` e `usd` da
    carteira. Carteira com "regra pendente" tem só a linha de caixa, com valores
    nulos.
    """
    con.execute(
        f"CREATE OR REPLACE TABLE {nome} ("
        "carteira VARCHAR, status VARCHAR, data_montagem DATE, ptax_venda DOUBLE, "
        "product_id INTEGER, acabamento VARCHAR, market_price DOUBLE, preco_compra_brl DOUBLE, "
        "valor_alocado_brl DOUBLE, unidades INTEGER, custo_brl DOUBLE, sobra_brl DOUBLE, "
        "caixa_brl DOUBLE, usd DOUBLE, fallback BOOLEAN)"
    )
    linhas = []
    for c in composicoes:
        base = [c.carteira, c.status, c.data_montagem, c.ptax_venda]
        for p in c.posicoes:
            linhas.append(base + [
                p.product_id, p.acabamento, p.market_price, p.preco_compra_brl,
                p.valor_alocado_brl, p.unidades, p.custo_brl, p.sobra_brl,
                None, None, c.fallback,
            ])
        pendente = c.status == STATUS_REGRA_PENDENTE
        linhas.append(base + [None] * 8 + [
            None if pendente else c.caixa_brl,
            None if pendente else c.usd,
            c.fallback,
        ])
    if linhas:
        con.executemany(f"INSERT INTO {nome} VALUES ({', '.join('?' * 15)})", linhas)
    return con.table(nome)
