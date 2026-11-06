-- dim_colecao (RF-10): uma linha por coleção, lida de todas as silvers aprovadas (curinga ou lista; T-32).
-- hive_partitioning = false: group_id vem da coluna do contrato, não do caminho (ADR-003, nota da T-24).
SELECT group_id, nome, sigla, data_lancamento, responsavel
FROM read_parquet({arquivos_colecao},
                  union_by_name = true, hive_partitioning = false)
ORDER BY group_id
