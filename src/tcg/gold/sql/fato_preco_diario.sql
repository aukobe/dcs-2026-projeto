-- fato_preco_diario (RF-10, RF-11, RNF-01): grão data × group_id × product_id × acabamento.
-- Preço de todas as coleções por curinga; câmbio só da silver da DRI (ADR-003).
-- ASOF LEFT JOIN: último boletim Fechamento com data <= data do preço, nunca posterior.
-- Preço anterior ao primeiro boletim fica no fato com market_price_brl,
-- cotacao_aplicada e data_ptax nulos.
WITH preco AS (
    SELECT data, product_id, group_id, acabamento,
           market_price, low_price, mid_price, high_price, chave_raw
    FROM read_parquet({base} || '/silver/preco_diario/*/*/*.parquet',
                      union_by_name = true, hive_partitioning = false)
),
cambio AS (
    SELECT data AS data_ptax, cotacao_venda
    FROM read_parquet({base} || '/silver/cambio_diario/group_id=24269/cambio.parquet',
                      hive_partitioning = false)
)
SELECT
    p.data,
    p.product_id,
    p.group_id,
    p.acabamento,
    p.market_price,
    p.low_price,
    p.mid_price,
    p.high_price,
    p.market_price * c.cotacao_venda  AS market_price_brl,
    c.cotacao_venda                   AS cotacao_aplicada,
    c.data_ptax,
    p.chave_raw
FROM preco AS p
ASOF LEFT JOIN cambio AS c
    ON p.data >= c.data_ptax
ORDER BY p.data, p.group_id, p.product_id, p.acabamento
