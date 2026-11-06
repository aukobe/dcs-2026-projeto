-- dim_acabamento (RF-10): acabamentos distintos presentes no fato.
SELECT DISTINCT acabamento
FROM fato_preco_diario
ORDER BY acabamento
