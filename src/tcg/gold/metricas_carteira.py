"""Métricas das carteiras (T-43; RF-25; ADR-005, ADR-006).

Parte da liquidação diária da T-42 (`liquidacao.LinhaCarteira`), sem recalcular
valores. `calcular_metricas` é função pura; `registrar_metricas` devolve o
resultado ao DuckDB numa tabela própria.

Métricas, por carteira e por taxa de venda (a do parâmetro e a taxa 0):
- retorno acumulado: valor de liquidação no último dia ÷ R$ 1.000,00 − 1;
- excesso sobre o CDI: retorno acumulado da carteira − retorno acumulado da
  carteira cdi com a mesma taxa;
- perda máxima: maior queda percentual entre um pico e o ponto mais baixo
  seguinte da série diária de valor de liquidação, (pico − vale) ÷ pico;
  0 se a série nunca cai;
- dias com preço carregado: dias em que algum item usou o último preço
  observado (`preco_carregado` da linha);
- propria com "regra pendente": métricas nulas, sem erro.

Gravação no contrato gold_turma e painel ficam nas T-44 e T-47.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import datetime as dt

import duckdb

from tcg.gold.carteiras import ORCAMENTO, STATUS_REGRA_PENDENTE
from tcg.gold.liquidacao import LinhaCarteira

CARTEIRA_CDI = "cdi"


@dataclass(frozen=True)
class MetricasCarteira:
    carteira: str
    status: str
    taxa_venda: float
    data_final: dt.date
    n_dias: int
    valor_final_brl: float | None
    retorno_acumulado: float | None
    excesso_cdi: float | None
    perda_maxima: float | None
    dias_preco_carregado: int | None


def retorno_acumulado(valor_final: float) -> float:
    """Valor de liquidação no último dia ÷ R$ 1.000,00 − 1."""
    return valor_final / ORCAMENTO - 1


def perda_maxima(valores: Sequence[float]) -> float:
    """Maior (pico − vale) ÷ pico, com o vale depois do pico; 0 se a série nunca cai."""
    perda = 0.0
    pico = None
    for v in valores:
        if pico is None or v > pico:
            pico = v
        elif pico > 0:
            perda = max(perda, (pico - v) / pico)
    return perda


def _agrupar(linhas: Iterable[LinhaCarteira]) -> dict[tuple[float, str], list[LinhaCarteira]]:
    grupos: dict[tuple[float, str], list[LinhaCarteira]] = {}
    for linha in linhas:
        grupos.setdefault((linha.taxa_venda, linha.carteira), []).append(linha)
    for serie in grupos.values():
        serie.sort(key=lambda l: l.data)
    return grupos


def calcular_metricas(linhas: Iterable[LinhaCarteira]) -> list[MetricasCarteira]:
    """Métricas de cada carteira × taxa de venda, na ordem de chegada dos grupos."""
    grupos = _agrupar(linhas)
    retorno_cdi: dict[float, float] = {}
    for (taxa, carteira), serie in grupos.items():
        if carteira == CARTEIRA_CDI:
            retorno_cdi[taxa] = retorno_acumulado(serie[-1].valor_brl)
    resultado = []
    for (taxa, carteira), serie in grupos.items():
        ultima = serie[-1]
        status = ultima.status
        if status == STATUS_REGRA_PENDENTE:
            resultado.append(MetricasCarteira(
                carteira, status, taxa, ultima.data, len(serie), None, None, None, None, None,
            ))
            continue
        if taxa not in retorno_cdi:
            raise ValueError(f"sem a carteira cdi para a taxa de venda {taxa}")
        valores = [l.valor_brl for l in serie]
        if any(v is None for v in valores):
            raise ValueError(f"carteira {carteira} calculada com valor nulo (taxa {taxa})")
        retorno = retorno_acumulado(valores[-1])
        resultado.append(MetricasCarteira(
            carteira=carteira,
            status=status,
            taxa_venda=taxa,
            data_final=ultima.data,
            n_dias=len(serie),
            valor_final_brl=valores[-1],
            retorno_acumulado=retorno,
            excesso_cdi=retorno - retorno_cdi[taxa],
            perda_maxima=perda_maxima(valores),
            dias_preco_carregado=sum(1 for l in serie if l.preco_carregado),
        ))
    return resultado


def registrar_metricas(
    con: duckdb.DuckDBPyConnection,
    linhas: Iterable[LinhaCarteira],
    nome: str = "metricas_carteira",
) -> duckdb.DuckDBPyRelation:
    """Grava as métricas numa tabela DuckDB: uma linha por carteira × taxa de venda."""
    metricas = calcular_metricas(linhas)
    con.execute(
        f"CREATE OR REPLACE TABLE {nome} ("
        "carteira VARCHAR, status VARCHAR, taxa_venda DOUBLE, data_final DATE, n_dias INTEGER, "
        "valor_final_brl DOUBLE, retorno_acumulado DOUBLE, excesso_cdi DOUBLE, "
        "perda_maxima DOUBLE, dias_preco_carregado INTEGER)"
    )
    if metricas:
        con.executemany(
            f"INSERT INTO {nome} VALUES ({', '.join('?' * 10)})",
            [list(vars(m).values()) for m in metricas],
        )
    return con.table(nome)
