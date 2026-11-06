-- dim_produto (RF-10): produtos de todas as coleções; a chave é (group_id, product_id).
SELECT group_id, product_id, nome, tipo_produto, raridade, numero, image_url, url
FROM read_parquet({arquivos_produto},
                  union_by_name = true, hive_partitioning = false)
ORDER BY group_id, product_id
