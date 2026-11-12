"""Métricas das perguntas da persona sobre a gold (T-35; RF-15, RNF-02; ADR-003).

Decomposição da variação em reais de um item entre o primeiro e o último dia:

- r_usd = usd_final / usd_inicial − 1 (parcela da carta);
- r_cambio = cotacao_final / cotacao_inicial − 1 (parcela do câmbio);
- r_cruzado = r_usd × r_cambio (efeito cruzado);
- r_brl = (usd_final × cotacao_final) / (usd_inicial × cotacao_inicial) − 1.

Identidades garantidas (RNF-02): r_usd + r_cambio + r_cruzado = r_brl e
(1 + r_brl) = (1 + r_usd) × (1 + r_cambio), com tolerância de 1e-9.

P1 (T-36; RF-15): rankings de alta (r_brl > 0) e de queda (r_brl < 0), até dez
itens cada, só cartas sem Code Card e com preço estritamente acima do mínimo
(padrão US$ 1) no primeiro dia.

P2 (T-36; RF-16): índice base 100 no primeiro dia da média dos selados contra a
soma das cartas Double Rare em diante, com cestas fixas: só entram os itens com
preço em todos os dias do período; nada é preenchido.
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


RARIDADES_DOUBLE_RARE_EM_DIANTE = (
    "Double Rare",
    "Ultra Rare",
    "Illustration Rare",
    "Special Illustration Rare",
    "Hyper Rare",
)

COLUNAS_PRECO_P2 = ("market_price_brl", "market_price")

SQL_P1 = """
WITH dias AS (
    SELECT min(data) AS data_inicial, max(data) AS data_final
    FROM {fato} WHERE group_id = $group_id
),
dec AS (
    {decomposicao}
),
base AS (
    SELECT
        dec.group_id, dec.product_id, dec.acabamento,
        p.nome, p.raridade, p.image_url, p.url,
        dec.usd_inicial, dec.usd_final, dec.brl_inicial, dec.brl_final,
        dec.cotacao_inicial, dec.cotacao_final,
        dec.r_brl, dec.r_usd, dec.r_cambio, dec.r_cruzado
    FROM dec
    JOIN {dim_produto} AS p USING (group_id, product_id)
    WHERE dec.group_id = $group_id
      AND p.tipo_produto = 'carta'
      AND p.raridade IS DISTINCT FROM 'Code Card'
      AND dec.usd_inicial > $preco_minimo
)
SELECT * FROM base
WHERE {condicao}
ORDER BY r_brl {ordem}, product_id, acabamento
LIMIT $limite
"""

SQL_P2 = """
WITH precos AS (
    SELECT f.data, f.product_id, f.acabamento, f.{coluna} AS preco,
           CASE WHEN p.tipo_produto = 'selado' THEN 'selado'
                WHEN p.tipo_produto = 'carta'
                     AND p.raridade IN (SELECT unnest($raridades)) THEN 'double_rare_mais'
           END AS cesta
    FROM {fato} AS f
    JOIN {dim_produto} AS p USING (group_id, product_id)
    WHERE f.group_id = $group_id
),
dias AS (
    SELECT DISTINCT data FROM {fato}
    WHERE group_id = $group_id AND market_price IS NOT NULL
),
completos AS (
    SELECT product_id, acabamento, cesta
    FROM precos
    WHERE cesta IS NOT NULL AND preco IS NOT NULL
    GROUP BY product_id, acabamento, cesta
    HAVING count(DISTINCT data) = (SELECT count(*) FROM dias)
),
serie AS (
    SELECT d.data,
           avg(pr.preco) FILTER (WHERE c.cesta = 'selado') AS media_selados,
           sum(pr.preco) FILTER (WHERE c.cesta = 'double_rare_mais') AS soma_double_rare_mais
    FROM dias AS d
    LEFT JOIN precos AS pr ON pr.data = d.data
    LEFT JOIN completos AS c USING (product_id, acabamento, cesta)
    GROUP BY d.data
)
SELECT
    data,
    media_selados,
    soma_double_rare_mais,
    100 * media_selados / first(media_selados ORDER BY data) OVER () AS indice_selados,
    100 * soma_double_rare_mais / first(soma_double_rare_mais ORDER BY data) OVER ()
        AS indice_double_rare_mais,
    (SELECT count(*) FROM completos WHERE cesta = 'selado') AS itens_selados,
    (SELECT count(*) FROM completos WHERE cesta = 'double_rare_mais') AS itens_double_rare_mais
FROM serie
ORDER BY data
"""


def p1_rankings(
    con: duckdb.DuckDBPyConnection,
    fato: str,
    dim_produto: str,
    group_id: int = 24269,
    preco_minimo_usd: float = 1.0,
    limite: int = 10,
) -> tuple[duckdb.DuckDBPyRelation, duckdb.DuckDBPyRelation]:
    """Rankings da P1 (RF-15): (alta, queda) entre o primeiro e o último dia da coleção.

    Só cartas sem Code Card com `market_price` estritamente acima de
    `preco_minimo_usd` no primeiro dia e com preço nos dois dias. A alta tem só
    r_brl > 0 (decrescente) e a queda só r_brl < 0 (crescente), até `limite`
    itens cada; desempate por `product_id` e `acabamento`.
    """
    decomposicao = (
        SQL_DECOMPOSICAO.format(fato=fato)
        .replace("$data_inicial", "(SELECT data_inicial FROM dias)")
        .replace("$data_final", "(SELECT data_final FROM dias)")
    )
    params = {"group_id": group_id, "preco_minimo": float(preco_minimo_usd), "limite": int(limite)}
    rankings = []
    for condicao, ordem in (("r_brl > 0", "DESC"), ("r_brl < 0", "ASC")):
        sql = SQL_P1.format(
            fato=fato, dim_produto=dim_produto, decomposicao=decomposicao,
            condicao=condicao, ordem=ordem,
        )
        rankings.append(con.sql(sql, params=params))
    return rankings[0], rankings[1]


def p2_indice(
    con: duckdb.DuckDBPyConnection,
    fato: str,
    dim_produto: str,
    group_id: int = 24269,
    coluna: str = "market_price_brl",
) -> duckdb.DuckDBPyRelation:
    """Índice base 100 da P2 (RF-16), uma linha por dia com preço da coleção.

    Cestas fixas: selados e cartas Double Rare em diante com `coluna` não nula
    em todos os dias do período; quem falta em algum dia sai da cesta inteira.
    `coluna` é `market_price_brl` (reais, padrão) ou `market_price` (dólar).
    Devolve também `itens_selados` e `itens_double_rare_mais`.
    """
    if coluna not in COLUNAS_PRECO_P2:
        raise ValueError(f"coluna deve ser uma de {COLUNAS_PRECO_P2}: {coluna!r}")
    sql = SQL_P2.format(fato=fato, dim_produto=dim_produto, coluna=coluna)
    return con.sql(
        sql, params={"group_id": group_id, "raridades": list(RARIDADES_DOUBLE_RARE_EM_DIANTE)}
    )
