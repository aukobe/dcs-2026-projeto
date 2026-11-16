# T-50 – Reprodução a partir de clone limpo, seguindo só o README [RNF-10]

- **Executor:** autor
- **Data e hora:** 2026-11-16, das 23h05 às 23h10 UTC (horários dos logs: make sync às 23:05:13Z, make cobertura às 23:09:37Z)
- **Clone:** /tmp/clone-limpo, clone novo deste repositório
- **Saída completa:** /tmp/t50.txt (fora do repositório); abaixo, só as linhas relevantes, copiadas sem alteração. Arquivo conferido antes da cópia: nenhum usuário, senha ou chave na saída.

## Roteiro seguido (seção "Como rodar" do README, na ordem)

1. make setup
2. cp .env.example .env e preenchimento das variáveis
3. make up (opcional no README; executado para conferir o MinIO local)
4. make sync
5. make silver
6. make gold
7. make test
8. make cobertura
9. make painel (conferido pelo autor no navegador)

## Observação sobre o .env

O .env do clone foi copiado do .env do autor, com o mesmo conteúdo que o README manda preencher a partir do .env.example (data lake da turma, MINIO_SECURE=true, chave da turma). O conteúdo do .env não aparece nesta evidência.

## make setup (fim da saída)

```text
.venv/bin/python -m pip install -q -e ".[dev]"
# Extensão httpfs do DuckDB, baixada só aqui (R-08); o código nunca a baixa
.venv/bin/python -c "import duckdb; duckdb.connect().install_extension('httpfs')"
```

Resultado: ambiente virtual criado com /usr/local/python/3.13.8/bin/python3.13, pacote instalado e extensão httpfs baixada, sem erro (só o aviso de versão nova do pip).

## make up

```text
docker compose up -d --wait
 Container clone-limpo-minio-1 Started 
 Container clone-limpo-minio-1 Waiting 
 Container clone-limpo-minio-1 Healthy 
```

Resultado: contêiner do MinIO local saudável pelo healthcheck.

## make sync (linha final)

```text
2026-11-16T23:05:14Z INFO tcg.sync.leitor_branch: arquivos em origin/dados-raw:raw/: 52
2026-11-16T23:05:20Z INFO __main__: sincronização encerrada: enviados=0 recusados=52 fora_do_escopo=0 falhas=0
```

Resultado: as 52 chaves da dados-raw (03/11 a 15/11) já estavam no data lake da turma e foram recusadas sem sobrescrita; nenhuma falha.

## make silver (linhas gravadas por tabela)

```text
2026-11-16T23:06:04Z INFO __main__: quarentena por tabela: preco_diario: 0, cambio_diario: 0, demais: 0
2026-11-16T23:06:10Z INFO __main__: linhas gravadas por tabela: colecao: 1, produto: 281, cambio_diario: 14, cdi_diario: 13, preco_diario: 5798, quarentena: 0
```

Resultado: silver da DRI gravada, com preco_diario em 13 partições (data=2026-11-03 a data=2026-11-15) e quarentena vazia.

## make gold (linhas gravadas por tabela)

```text
2026-11-16T23:06:29Z INFO __main__: coleções na gold: 24269, 24541
2026-11-16T23:06:33Z INFO __main__: linhas gravadas por tabela: dim_colecao: 2, dim_produto: 901, fato_preco_diario: 7114, dim_data: 13, dim_acabamento: 3, fato_cambio_diario: 13
2026-11-16T23:06:36Z INFO tcg.lake.duckdb: Parquet gravado: s3://tcg/gold_turma/carteira/group_id=24269/carteira.parquet
2026-11-16T23:06:36Z INFO __main__: carteiras gravadas (taxa_venda=0.15, propria=calculada): composicao_carteira: 22, liquidacao_carteira: 130, liquidacao_item: 442, metricas_carteira: 10, gold_turma_carteira: 65
```

Resultado: gold com a DRI e uma outra coleção disponível (groupId 24541, lida só para leitura); carteiras e gold_turma gravadas só em prefixos com group_id=24269.

## make test (linha final)

```text
collecting ... collected 463 items
======================== 463 passed in 69.00s (0:01:09) ========================
```

Resultado: suíte completa (unidade e integração com MinIO descartável) sem falha.

## make cobertura (resumo)

```text
2026-11-16T23:09:37Z INFO __main__: cobertura: 13 datas, 0 faltantes
periodo: 2026-11-03 a 2026-11-15 (13 datas)
resumo: 13 datas, 13 com bruto, 0 registradas, 0 faltantes
```

Resultado: todas as datas do período com os quatro arquivos na dados-raw; tabela "Dias sem coleta" sem linhas.

## make painel

Conferido pelo autor: o painel abriu no navegador com as oito abas.

## Conclusão

Todos os comandos do README terminaram com sucesso num clone novo, e o painel abriu com make painel (RNF-10).
