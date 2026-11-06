-- dim_colecao (RF-10): uma linha por coleção, lida de todas as silvers por curinga.
-- hive_partitioning = false: group_id vem da coluna do contrato, não do caminho (ADR-003, nota da T-24).
SELECT group_id, nome, sigla, data_lancamento, responsavel
FROM read_parquet({base} || '/silver/colecao/*/*.parquet',
                  union_by_name = true, hive_partitioning = false)
ORDER BY group_id
