-- dim_data (RF-10): calendário do período, do primeiro ao último dia com preço.
-- Dias sem linha no fato continuam aqui; nenhuma lacuna é preenchida (RF-21).
SELECT
    CAST(d.data AS DATE)              AS data,
    year(d.data)                      AS ano,
    month(d.data)                     AS mes,
    day(d.data)                       AS dia,
    isodow(d.data)                    AS dia_semana,      -- 1 = segunda ... 7 = domingo
    isodow(d.data) IN (6, 7)          AS fim_de_semana
FROM (
    SELECT unnest(generate_series(min(data), max(data), INTERVAL 1 DAY)) AS data
    FROM fato_preco_diario
) AS d
ORDER BY data
