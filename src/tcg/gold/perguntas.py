"""Métricas das perguntas da persona sobre a gold (T-35; RF-15, RNF-02; ADR-003).

Decomposição da variação em reais de um item entre o primeiro e o último dia:

- r_usd = usd_final / usd_inicial − 1 (parcela da carta);
- r_cambio = cotacao_final / cotacao_inicial − 1 (parcela do câmbio);
- r_cruzado = r_usd × r_cambio (efeito cruzado);
- r_brl = (usd_final × cotacao_final) / (usd_inicial × cotacao_inicial) − 1.

Identidades garantidas (RNF-02): r_usd + r_cambio + r_cruzado = r_brl e
(1 + r_brl) = (1 + r_usd) × (1 + r_cambio), com tolerância de 1e-9.

Os filtros e rankings da P1 (Code Card, preço mínimo de US$ 1) ficam na T-36.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt

import duckdb


@dataclass(frozen=True)
class Decomposicao:
    """Variação em reais e suas três parcelas, em fração (0,10 = 10%)."""

    r_brl: float
    r_usd: float
    r_cambio: float
    r_cruzado: float


def decompor(
    usd_inicial: float,
    usd_final: float,
    cotacao_inicial: float,
    cotacao_final: float,
) -> Decomposicao:
    """Decompõe a variação em reais em carta, câmbio e cruzado."""
    for nome, valor in (
        ("usd_inicial", usd_inicial),
        ("usd_final", usd_final),
        ("cotacao_inicial", cotacao_inicial),
        ("cotacao_final", cotacao_final),
    ):
        if not valor > 0:
            raise ValueError(f"{nome} deve ser maior que zero: {valor!r}")
    r_usd = usd_final / usd_inicial - 1
    r_cambio = cotacao_final / cotacao_inicial - 1
    r_brl = (usd_final * cotacao_final) / (usd_inicial * cotacao_inicial) - 1
    return Decomposicao(r_brl=r_brl, r_usd=r_usd, r_cambio=r_cambio, r_cruzado=r_usd * r_cambio)


SQL_DECOMPOSICAO = """
WITH ini AS (
    SELECT group_id, product_id, acabamento, market_price, cotacao_aplicada, market_price_brl
    FROM {fato} WHERE data = $data_inicial
),
fim AS (
    SELECT group_id, product_id, acabamento, market_price, cotacao_aplicada, market_price_brl
    FROM {fato} WHERE data = $data_final
),
par AS (
    SELECT
        ini.group_id, ini.product_id, ini.acabamento,
        ini.market_price AS usd_inicial, fim.market_price AS usd_final,
        ini.cotacao_aplicada AS cotacao_inicial, fim.cotacao_aplicada AS cotacao_final,
        ini.market_price_brl AS brl_inicial, fim.market_price_brl AS brl_final
    FROM ini
    JOIN fim USING (group_id, product_id, acabamento)
    WHERE ini.market_price > 0 AND fim.market_price > 0
      AND ini.cotacao_aplicada > 0 AND fim.cotacao_aplicada > 0
)
SELECT
    group_id, product_id, acabamento,
    usd_inicial, usd_final, cotacao_inicial, cotacao_final, brl_inicial, brl_final,
    (usd_final * cotacao_final) / (usd_inicial * cotacao_inicial) - 1 AS r_brl,
    usd_final / usd_inicial - 1 AS r_usd,
    cotacao_final / cotacao_inicial - 1 AS r_cambio,
    (usd_final / usd_inicial - 1) * (cotacao_final / cotacao_inicial - 1) AS r_cruzado
FROM par
ORDER BY group_id, product_id, acabamento
"""


def decomposicao_por_item(
    con: duckdb.DuckDBPyConnection,
    fato: str,
    data_inicial: dt.date,
    data_final: dt.date,
) -> duckdb.DuckDBPyRelation:
    """Decomposição por produto × acabamento entre duas datas do `fato_preco_diario`.

    `fato` é o nome de uma tabela ou view com as colunas do fato (ou uma
    expressão como `read_parquet('...')`). Só entram itens com preço nos dois
    dias; lacunas não são preenchidas (RF-21).
    """
    return con.sql(
        SQL_DECOMPOSICAO.format(fato=fato),
        params={"data_inicial": data_inicial, "data_final": data_final},
    )
