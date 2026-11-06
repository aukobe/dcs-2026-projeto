-- fato_cambio_diario (RF-12, RNF-01): um dia de calendário por linha, os mesmos dias de dim_data.
-- Câmbio e CDI só da silver da DRI (ADR-003); hive_partitioning = false (nota da T-24).
-- ASOF LEFT JOIN: último boletim Fechamento com data <= dia, nunca posterior; data_ptax é a data do boletim.
-- CDI do dia só quando há CDI na própria data; senão 0 (fim de semana, feriado ou CDI ausente).
-- cdi_pendente: há boletim de PTAX no próprio dia (dia útil) e não há CDI nessa data.
-- Dia anterior ao primeiro boletim: cotações e data_ptax nulas, CDI 0 e cdi_pendente falso.
WITH cambio AS (
    SELECT data AS data_ptax, cotacao_compra, cotacao_venda
    FROM read_parquet({base} || '/silver/cambio_diario/group_id=24269/cambio.parquet',
                      hive_partitioning = false)
),
cdi AS (
    SELECT data AS data_cdi, taxa_dia
    FROM read_parquet({base} || '/silver/cdi_diario/group_id=24269/cdi.parquet',
                      hive_partitioning = false)
)
SELECT
    d.data,
    c.cotacao_compra,
    c.cotacao_venda,
    c.data_ptax,
    coalesce(i.taxa_dia, 0.0)                               AS cdi_taxa_dia,
    coalesce(c.data_ptax = d.data AND i.data_cdi IS NULL, false) AS cdi_pendente
FROM dim_data AS d
ASOF LEFT JOIN cambio AS c
    ON d.data >= c.data_ptax
LEFT JOIN cdi AS i
    ON i.data_cdi = d.data
ORDER BY d.data
