"""Valor de liquidação diário das cinco carteiras (T-42; RF-24; ADR-005, ADR-006).

Parte da composição da T-41 (`carteiras.compor_carteiras`), sem recompor a
carteira. `ler_dados_diarios` é o único ponto que lê o DuckDB, e só com SELECT;
`liquidar` e `liquidar_carteiras` são funções puras; `registrar_liquidacao`
devolve o resultado ao DuckDB em tabelas próprias. Nada é gravado no fato nem na
silver.

Regras (RF-24):
- selado, cesta_raras e propria: Σ unidades × market_price × (1 − taxa_venda) ×
  PTAX de compra aplicada no dia + caixa do dia;
- dolar: usd × PTAX de compra aplicada no dia (sem taxa);
- cdi e caixa: juros compostos com `cdi_taxa_dia` do `fato_cambio_diario`, em
  percentual ao dia como publicado (fator 1 + taxa/100). A taxa do dia útil d
  remunera de d até o próximo dia útil, logo
      valor(D) = valor inicial × Π (1 + cdi_taxa_dia(d)/100), primeiro dia ≤ d < D.
  No primeiro dia o valor é exatamente o inicial; fim de semana e feriado têm
  taxa 0 no fato (RF-12) e não acrescentam juros;
- `cdi_pendente` da linha: algum dia d < D usado no produto é dia útil sem CDI
  publicado (`cdi_pendente` do fato); a taxa entra como 0, sem estimativa;
- preço ausente (sem linha no dia, nulo ou ≤ 0, inclusive em dia sem coleta):
  usa o último market_price > 0 observado desde o primeiro dia, só neste
  cálculo, e marca o item e o dia como "preço carregado";
- propria com "regra pendente": uma linha por dia com valor nulo.

A taxa_venda é argumento: quem chama passa `ler_parametros().taxa_venda`, e
`registrar_liquidacao` calcula por padrão também com taxa 0, para o painel
mostrar com e sem taxa. Métricas e gold_turma ficam nas T-43 e T-44.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt

import duckdb

from tcg.gold.carteiras import STATUS_REGRA_PENDENTE, Composicao


@dataclass(frozen=True)
class CambioDia:
    """Uma linha do `fato_cambio_diario` usada na liquidação."""

    data: dt.date
    cotacao_compra: float
    cdi_taxa_dia: float
    cdi_pendente: bool


@dataclass(frozen=True)
class DadosDiarios:
    """Dias do período (primeiro ao último dia da coleção) e preços dos itens comprados."""

    dias: tuple[CambioDia, ...]
    precos: dict[tuple[int, str], dict[dt.date, float | None]]


@dataclass(frozen=True)
class LinhaCarteira:
    data: dt.date
    carteira: str
    status: str
    taxa_venda: float
    valor_brl: float | None
    valor_itens_brl: float | None
    caixa_brl: float | None
    preco_carregado: bool
    n_itens_carregados: int
    cdi_pendente: bool


@dataclass(frozen=True)
class LinhaItem:
    data: dt.date
    carteira: str
    taxa_venda: float
    product_id: int
    acabamento: str
    unidades: int
    market_price_usado: float
    data_preco: dt.date
    preco_carregado: bool
    valor_brl: float


SQL_ULTIMO_DIA = "SELECT max(data) FROM {fato} WHERE group_id = $group_id"

SQL_CAMBIO = """
SELECT data, cotacao_compra, cdi_taxa_dia, cdi_pendente
FROM {fato_cambio}
WHERE data BETWEEN $inicio AND $fim
ORDER BY data
"""

SQL_PRECOS = """
SELECT product_id, acabamento, data, market_price
FROM {fato}
WHERE group_id = $group_id AND data BETWEEN $inicio AND $fim
"""


def ler_dados_diarios(
    con: duckdb.DuckDBPyConnection,
    fato: str,
    fato_cambio: str,
    composicoes: tuple[Composicao, ...],
    group_id: int = 24269,
) -> DadosDiarios:
    """Lê câmbio, CDI e preços de todos os dias de calendário do período.

    Período: do dia de montagem (primeiro dia) ao último dia com preço da
    coleção. Dia sem `cotacao_compra` aplicada é erro: nenhum câmbio é inventado.
    """
    inicio = composicoes[0].data_montagem
    fim = con.execute(SQL_ULTIMO_DIA.format(fato=fato), {"group_id": group_id}).fetchone()[0]
    if fim is None or fim < inicio:
        raise ValueError(f"sem preços no fato para o group_id {group_id} a partir de {inicio}")
    linhas = {
        r[0]: r
        for r in con.execute(
            SQL_CAMBIO.format(fato_cambio=fato_cambio), {"inicio": inicio, "fim": fim}
        ).fetchall()
    }
    dias = []
    for k in range((fim - inicio).days + 1):
        data = inicio + dt.timedelta(days=k)
        r = linhas.get(data)
        if r is None or r[1] is None or not r[1] > 0:
            raise ValueError(f"sem PTAX de compra aplicada em {data}")
        dias.append(CambioDia(data, float(r[1]), float(r[2] or 0.0), bool(r[3])))
    itens = {(p.product_id, p.acabamento) for c in composicoes for p in c.posicoes}
    precos: dict[tuple[int, str], dict[dt.date, float | None]] = {i: {} for i in itens}
    for pid, acab, data, preco in con.execute(
        SQL_PRECOS.format(fato=fato), {"group_id": group_id, "inicio": inicio, "fim": fim}
    ).fetchall():
        if (pid, acab) in precos:
            precos[(pid, acab)][data] = preco
    return DadosDiarios(dias=tuple(dias), precos=precos)


def _fatores_cdi(dias: tuple[CambioDia, ...]) -> list[tuple[float, bool]]:
    """Fator acumulado e marca de pendência por dia: taxas de d < D, desde o primeiro dia."""
    fatores = []
    fator, pendente = 1.0, False
    for dia in dias:
        fatores.append((fator, pendente))
        fator *= 1 + dia.cdi_taxa_dia / 100
        pendente = pendente or dia.cdi_pendente
    return fatores


def liquidar(
    composicao: Composicao, dados: DadosDiarios, taxa_venda: float
) -> tuple[list[LinhaCarteira], list[LinhaItem]]:
    """Valor de liquidação de uma carteira em cada dia do período (função pura)."""
    linhas: list[LinhaCarteira] = []
    itens: list[LinhaItem] = []
    ultimo: dict[tuple[int, str], tuple[float, dt.date]] = {}
    pendente_regra = composicao.status == STATUS_REGRA_PENDENTE
    for dia, (fator, cdi_pendente) in zip(dados.dias, _fatores_cdi(dados.dias)):
        if pendente_regra:
            linhas.append(LinhaCarteira(
                dia.data, composicao.carteira, composicao.status, taxa_venda,
                None, None, None, False, 0, cdi_pendente,
            ))
            continue
        valor_itens = 0.0
        carregados = 0
        for p in composicao.posicoes:
            chave = (p.product_id, p.acabamento)
            preco = dados.precos.get(chave, {}).get(dia.data)
            if preco is not None and preco > 0:
                ultimo[chave] = (preco, dia.data)
            if chave not in ultimo:
                raise ValueError(f"item {chave} sem preço observado até {dia.data}")
            usado, data_preco = ultimo[chave]
            carregado = data_preco != dia.data
            carregados += carregado
            valor = p.unidades * usado * (1 - taxa_venda) * dia.cotacao_compra
            valor_itens += valor
            itens.append(LinhaItem(
                dia.data, composicao.carteira, taxa_venda, p.product_id, p.acabamento,
                p.unidades, usado, data_preco, carregado, valor,
            ))
        caixa = composicao.caixa_brl * fator
        valor_usd = composicao.usd * dia.cotacao_compra
        linhas.append(LinhaCarteira(
            dia.data, composicao.carteira, composicao.status, taxa_venda,
            valor_itens + caixa + valor_usd, valor_itens, caixa,
            carregados > 0, carregados, cdi_pendente,
        ))
    return linhas, itens


def liquidar_carteiras(
    composicoes: tuple[Composicao, ...], dados: DadosDiarios, taxas: tuple[float, ...]
) -> tuple[list[LinhaCarteira], list[LinhaItem]]:
    """Todas as carteiras para cada taxa de venda pedida."""
    linhas: list[LinhaCarteira] = []
    itens: list[LinhaItem] = []
    for taxa in taxas:
        for c in composicoes:
            lc, li = liquidar(c, dados, taxa)
            linhas += lc
            itens += li
    return linhas, itens


def registrar_liquidacao(
    con: duckdb.DuckDBPyConnection,
    composicoes: tuple[Composicao, ...],
    dados: DadosDiarios,
    taxa_venda: float,
    nome_carteira: str = "liquidacao_carteira",
    nome_item: str = "liquidacao_item",
) -> tuple[duckdb.DuckDBPyRelation, duckdb.DuckDBPyRelation]:
    """Grava a liquidação com a taxa do parâmetro e com taxa 0 em duas tabelas DuckDB."""
    taxas = (taxa_venda,) if taxa_venda == 0 else (taxa_venda, 0.0)
    linhas, itens = liquidar_carteiras(composicoes, dados, taxas)
    con.execute(
        f"CREATE OR REPLACE TABLE {nome_carteira} ("
        "data DATE, carteira VARCHAR, status VARCHAR, taxa_venda DOUBLE, valor_brl DOUBLE, "
        "valor_itens_brl DOUBLE, caixa_brl DOUBLE, preco_carregado BOOLEAN, "
        "n_itens_carregados INTEGER, cdi_pendente BOOLEAN)"
    )
    con.execute(
        f"CREATE OR REPLACE TABLE {nome_item} ("
        "data DATE, carteira VARCHAR, taxa_venda DOUBLE, product_id INTEGER, acabamento VARCHAR, "
        "unidades INTEGER, market_price_usado DOUBLE, data_preco DATE, preco_carregado BOOLEAN, "
        "valor_brl DOUBLE)"
    )
    if linhas:
        con.executemany(
            f"INSERT INTO {nome_carteira} VALUES ({', '.join('?' * 10)})",
            [list(vars(l).values()) for l in linhas],
        )
    if itens:
        con.executemany(
            f"INSERT INTO {nome_item} VALUES ({', '.join('?' * 10)})",
            [list(vars(i).values()) for i in itens],
        )
    return con.table(nome_carteira), con.table(nome_item)
