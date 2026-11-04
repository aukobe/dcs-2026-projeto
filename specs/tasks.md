# Tarefas

Documento derivado de `specs/spec.md` e `specs/plan.md`. Cada tarefa cabe num único prompt de implementação, toca poucos arquivos e traz o teste junto. A ordem segue os blocos de prioridade: primeiro a coleta no ar, porque um dia sem coleta não se recupera.

## Convenções

- **Executor**: `agente` implementa e roda a verificação; `autor` executa a tarefa manual (GitHub, `.env`, disparo do workflow, decisões que a spec atribui a ele). O agente nunca faz commit, push nem exclusão (`AGENTS.md`).
- **Marcas** na coluna Tarefa: **[rede]** exige acesso à internet; **[contêiner]** exige Docker. Tarefa sem marca roda sem rede e sem contêiner.
- **Gate**: cada tarefa é revisada e commitada pelo autor antes da seguinte, com a mensagem `tipo(T-xx): descrição [RF-yy]`. Cada ADR é revisado e commitado antes da primeira tarefa de código que ele orienta.
- **Status**: `[ ]` pendente, `[x]` concluída.
- Arquivos de teste ficam em `tests/unidade/` (sem rede, RNF-05) ou `tests/integracao/` (cassetes e MinIO descartável).

## Bloco A: coleta no ar

| ID | Tarefa | Requisitos | Verificação (comando) | Evidência esperada | Depende de | Executor | Status |
|---|---|---|---|---|---|---|---|
| T-01 | Estrutura do pacote `src/tcg/` e `pyproject.toml` com Python 3.13 e dependências em versões fixadas; Makefile com o alvo `test`; teste de importação do pacote **[rede: só PyPI]** | RNF-10 | `make test` | `tests/unidade/test_pacote.py` passa; `pip install -e .` instala sem erro | — | agente | [x] |
| T-02 | Fixture em `tests/conftest.py` que substitui `socket.socket` e bloqueia a rede nos testes de unidade, mais um teste que prova o bloqueio | RNF-05 | `pytest tests/unidade/test_bloqueio_rede.py` | uma tentativa de conexão dentro de um teste de unidade falha com erro explícito | T-01 | agente | [x] |
| T-03 | `config/colecao.toml`, `config/parametros.toml` (valores da seção 8 do plano), `src/tcg/config.py` (lê os TOMLs com `tomllib` e as variáveis de ambiente) e `src/tcg/log.py` (formato UTC, sem credenciais) | RF-01, RF-03, RF-06, RF-24, RNF-08 | `pytest tests/unidade/test_config.py tests/unidade/test_log.py` | parâmetros e coleção lidos com os valores da spec; variável ausente gera erro claro; os valores de `MINIO_ACCESS_KEY` e `MINIO_SECRET_KEY` não aparecem na saída do log | T-01 | agente | [x] |
| T-04 | Cliente HTTP (`src/tcg/coleta/http.py`): sessão `requests` com User-Agent de `TCG_USER_AGENT`, pausa mínima de 100 ms, repetição em falha transitória com esperas de 2, 4 e 8 s, contador de requisições com limite diário | RF-03, RNF-12 | `pytest tests/unidade/test_http.py` | com servidor e relógio simulados: User-Agent em toda requisição, intervalo ≥ 100 ms, esperas 2 e 4 s e sucesso na terceira tentativa após dois 503; falha total levanta erro e registra no log; requisição além do limite é recusada | T-02, T-03 | agente | [x] |
| T-05 | Clientes TCGCSV (`products` e `prices` do groupId 24269) e BCB (PTAX Olinda `CotacaoMoedaPeriodo` USD e CDI SGS série 12, janela de 10 dias corridos). Os endpoints e o formato do BCB são confirmados por uma consulta real ao BCB; o TCGCSV não é chamado nesta tarefa **[rede]** | RF-01 | `pytest tests/unidade/test_clientes.py` | URLs e parâmetros montados corretamente para a data da coleta; corpo devolvido sem alteração; `docs/evidencias/T-05_endpoints_bcb.md` registra os endpoints confirmados e um exemplo de resposta | T-04 | agente | [x] |
| T-06 | Coletor (`guarda.py`, `gravador.py`, `__main__.py`): recusa antes das 20h UTC; para cada fonte, verifica o arquivo do dia antes de qualquer requisição; grava o corpo byte a byte em modo de criação exclusiva no diretório da branch `dados-raw`; fontes independentes; sai com código de falha se alguma fonte falhar | RF-01, RF-02, RF-04 | `pytest tests/unidade/test_coletor.py` | testes de recusa por horário (19h59), recusa por arquivo existente (zero requisições), recusa de sobrescrita com hash original intacto, hash do arquivo igual ao corpo e falha de uma fonte sem afetar as outras passam | T-05 | agente | [x] |
| T-07 | ADR-001: bruto versionado na branch `dados-raw` com sincronização para o MinIO local (`docs/adr/ADR-001-bruto-dados-raw.md`) | RF-01, RF-02, RF-05, RNF-08, RNF-09 | `git log --oneline -- docs/adr/ADR-001-bruto-dados-raw.md` | o ADR tem contexto, decisão, alternativas e consequências, revisado e commitado pelo autor antes do T-08 | — | agente | [x] |
| T-08 | Script `scripts/criar_branch_dados_raw.sh` que cria localmente a branch órfã `dados-raw` com `.gitattributes` (`* -text`) e um README curto, sem push; teste que roda o script num repositório temporário | RF-02 | `pytest tests/unidade/test_criar_branch.py` | no repositório temporário, a branch órfã tem só os dois arquivos, nenhum histórico da `main`, e o script não faz push | T-07 | agente | [x] |
| T-09 | Executar o script do T-08 no repositório e publicar a branch `dados-raw` **[rede]** | RF-02 | `git ls-tree origin/dados-raw` | a branch existe no GitHub com `.gitattributes` e `README.md` | T-08 | autor | [x] |
| T-10 | Workflow `.github/workflows/coleta.yml`: cron `30 20 * * *` e `workflow_dispatch`, Python 3.13, checkout da `main` e da `dados-raw` em diretórios separados, grupo de concorrência, só `contents: write`, nenhum secret, `TCG_USER_AGENT` de `vars`, commit `dados(coleta): AAAA-MM-DD [RF-01]` e push só na `dados-raw`; o workflow faz commit e push dos arquivos gravados mesmo quando o coletor sai com código 1 (falha parcial) e só depois marca o job como falho; com código 2 não há nada a commitar | RF-01, RNF-08, RNF-13 | `pytest tests/unidade/test_workflow.py` | o teste lê o YAML e confirma cron, disparo manual, concorrência, permissões mínimas, ausência de `secrets.` e push restrito à `dados-raw` | T-06, T-07 | agente | [x] |
| T-11 | Criar a variável de repositório `TCG_USER_AGENT` (em `vars`, não em secret) no GitHub **[rede]** | RF-03, RNF-13 | `gh variable list` | `TCG_USER_AGENT` aparece na lista de variáveis do repositório | — | autor | [x] |
| T-12 | Commitar o workflow na `main`, dispará-lo manualmente depois das 20h UTC e conferir a branch **[rede]** | RF-01, RF-02, RNF-12, RNF-13 | `gh workflow run coleta.yml && gh run watch && git fetch origin dados-raw && git ls-tree -r --name-only origin/dados-raw` | execução com sucesso no Actions; os quatro arquivos do dia em `raw/...` na `dados-raw`, com commit `dados(coleta): AAAA-MM-DD [RF-01]`; o log mostra a contagem de requisições | T-09, T-10, T-11 | autor | [x] |
| T-13 | Validar as hipóteses da spec sobre o primeiro bruto: regra do `tipo_produto`, lista de raridades "Double Rare em diante", identificação e preço do booster box, preço dos selados, presença de `imageUrl` e `url`. Registrar os resultados e propor os ajustes da spec, para revisão do autor **[rede: só git fetch]** | RF-09, RF-16, RF-20, RF-23 | `git show origin/dados-raw:raw/tcgplayer/group_id=24269/data=$(git ls-tree --name-only origin/dados-raw:raw/tcgplayer/group_id=24269/ \| head -1 \| cut -d= -f2)/products.json \| python -m json.tool > /dev/null && test -s docs/evidencias/T-13_hipoteses.md` | `docs/evidencias/T-13_hipoteses.md` lista cada hipótese como confirmada ou refutada, com contagens tiradas do bruto | T-12 | agente | [x] |

## Bloco B: armazenamento local

| ID | Tarefa | Requisitos | Verificação (comando) | Evidência esperada | Depende de | Executor | Status |
|---|---|---|---|---|---|---|---|
| T-14 | ADR-002: imagem do MinIO com tag fixada (`docs/adr/ADR-002-imagem-minio.md`) | RNF-09, RNF-10 | `git log --oneline -- docs/adr/ADR-002-imagem-minio.md` | ADR revisado e commitado pelo autor antes do T-15 | — | agente | [x] |
| T-15 | `docker-compose.yml` do MinIO (`ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z`, portas 9000 e 9001, volume nomeado, healthcheck, credenciais do `.env`) e alvo `make up`; confirmar que o healthcheck funciona nessa imagem **[rede: só ghcr.io]** **[contêiner]** | RNF-09, RNF-10 | `pytest tests/unidade/test_compose.py && docker compose config --quiet` | o teste confirma a tag fixada (sem `latest`), o healthcheck, o volume nomeado e as credenciais vindas de variáveis | T-14 | agente | [x] |
| T-16 | Preencher o `.env` a partir do `.env.example` e subir o MinIO local **[contêiner]** | RNF-08, RNF-10 | `make up && docker compose ps` | o serviço MinIO aparece como `healthy`; `git status` não mostra o `.env` | T-15 | autor | [x] |
| T-17 | Leitor da branch (`src/tcg/sync/leitor_branch.py`): `git fetch` e leitura dos arquivos de `raw/` pelos blobs (`git ls-tree` e `git cat-file`), sem checkout | RF-05 | `pytest tests/unidade/test_leitor_branch.py` | num repositório temporário, lista as chaves de `raw/` e devolve bytes idênticos aos gravados, inclusive com `\r\n` | T-02 | agente | [x] |
| T-18 | Cliente MinIO (`src/tcg/lake/cliente.py`, credenciais só do ambiente) e sincronizador (`src/tcg/sync/sincronizador.py`): `stat_object` antes do `put_object`, recusa registrada no log, hash conferido com o do blob; alvo `make sync` | RF-05, RNF-03, RNF-08 | `pytest tests/unidade/test_sincronizador.py` | com cliente falso: chave existente não é regravada e a recusa aparece no log; arquivo novo é enviado com o hash da origem; nenhuma chave fora de `raw/*/group_id=24269/` é gravada | T-03, T-17 | agente | [x] |
| T-19 | Testes de integração com MinIO descartável (testcontainers): gravação, sincronização e recusa de sobrescrita, com o contêiner descartado no final **[contêiner]** | RNF-07, RF-02, RF-05 | `pytest tests/integracao/test_minio.py` | os testes passam; o contêiner de teste é removido no final e o MinIO local de trabalho não é tocado | T-15, T-18 | agente | [x] |
| T-20 | Cassetes vcrpy em `tests/integracao/cassetes/`, montados a partir do bruto real da branch `dados-raw`, sem nova requisição ao TCGCSV; teste de integração da coleta com os cassetes e sem rede | RNF-06, RF-01 | `pytest tests/integracao/test_coleta_cassetes.py` | a coleta grava os quatro arquivos com hash igual ao do bruto real; nenhuma requisição sai para a internet | T-06, T-13 | agente | [x] |
| T-21 | Primeira sincronização real da branch `dados-raw` para o MinIO local, executada duas vezes **[contêiner]** | RF-05 | `make sync && make sync` | a primeira execução copia os arquivos; a segunda só registra recusas; os hashes no MinIO são iguais aos dos blobs | T-12, T-16, T-18 | autor | [x] |

## Bloco C: lakehouse

| ID | Tarefa | Requisitos | Verificação (comando) | Evidência esperada | Depende de | Executor | Status |
|---|---|---|---|---|---|---|---|
| T-22 | ADR-004: camadas derivadas e reprocessamento (`docs/adr/ADR-004-camadas-derivadas.md`) | RF-13, RNF-03, RNF-04 | `git log --oneline -- docs/adr/ADR-004-camadas-derivadas.md` | ADR revisado e commitado pelo autor antes do T-23 | — | agente | [x] |
| T-23 | Guarda de prefixo (`src/tcg/lake/guarda_prefixo.py`): único ponto de escrita fora de `raw/` e única função de exclusão do código; aceita só `silver/*/group_id=24269/`, `gold/group_id=24269/` e `gold_turma/carteira/group_id=24269/` | RNF-03, RF-13 | `pytest tests/unidade/test_guarda_prefixo.py` | com cliente falso: escrita e exclusão nos três prefixos são aceitas; chaves em `raw/`, de outro group_id ou com `..` são recusadas antes de qualquer chamada ao SDK | T-18, T-22 | agente | [x] |
| T-24 | Conexão DuckDB com httpfs para o MinIO (`src/tcg/lake/duckdb.py`): estilo de caminho, sem SSL, credenciais do ambiente; teste de leitura e gravação de Parquet **[contêiner]** **[rede: só extensões do DuckDB]** | RF-06, RF-10 | `pytest tests/integracao/test_duckdb_minio.py` | um Parquet gravado no MinIO descartável é lido de volta com os mesmos tipos | T-03, T-15 | agente | [x] |
| T-25 | Modelos pydantic (`src/tcg/silver/modelos.py`) das cinco tabelas: `tipo_produto` com a exceção do Code Card, preço ausente como nulo, descarte por regra dos boletins da PTAX que não são `Fechamento` | RF-07, RF-08, RF-09 | `pytest tests/unidade/test_modelos.py` | selado/carta/carta para os três casos do RF-09; `market_price` nulo sem cópia de outro dia; linha sem `productId` inválida; boletim intermediário descartado sem erro | T-03, T-13 | agente | [x] |
| T-26 | Quarentena (`src/tcg/silver/quarentena.py`): linha inválida com motivo e `chave_raw`; deduplicação de PTAX e CDI vindos de brutos de dias diferentes; data com valores divergentes vai para a quarentena com o motivo "valor divergente entre brutos" | RF-07 | `pytest tests/unidade/test_quarentena.py` | valores iguais geram uma linha; valores divergentes vão para a quarentena com o motivo; contagem por tabela correta | T-25 | agente | [ ] |
| T-27 | Construtor da silver (`src/tcg/silver/construtor.py`): lê o bruto da DRI, grava as cinco tabelas nos caminhos e tipos do contrato e a quarentena pela Guarda de prefixo, `colecao` a partir de `config/colecao.toml`, contagem de quarentena no log; alvo `make silver`. Nota (T-24): por padrão o `read_parquet` liga o particionamento Hive e cria a coluna `group_id` a partir do caminho (`group_id=24269/`); decidir explicitamente se a leitura usa `hive_partitioning = false` ou aproveita essa coluna. | RF-06, RF-07, RNF-11 | `pytest tests/unidade/test_construtor_silver.py` | com o bruto de três dias: as cinco tabelas têm os nomes e tipos do contrato; cada linha de preço, câmbio e CDI traz a `chave_raw`; o log mostra `preco_diario: 1, cambio_diario: 1, demais: 0` no cenário do RF-07 | T-23, T-24, T-26 | agente | [ ] |
| T-28 | Integração coleta → silver com os cassetes, sem rede | RNF-06 | `pytest tests/integracao/test_coleta_silver.py` | a silver construída a partir dos cassetes passa no teste de contrato; nenhuma requisição sai para a internet | T-20, T-27 | agente | [ ] |
| T-29 | ADR-003: esquema estrela na gold e leitura de outras coleções (`docs/adr/ADR-003-estrela-outras-colecoes.md`) | RF-10, RF-17, RF-22, RF-28 | `git log --oneline -- docs/adr/ADR-003-estrela-outras-colecoes.md` | ADR revisado e commitado pelo autor antes do T-30 | — | agente | [ ] |
| T-30 | SQL do esquema estrela (`src/tcg/gold/sql/`): `dim_produto`, `dim_colecao`, `dim_data`, `dim_acabamento` e `fato_preco_diario`, com ASOF JOIN da PTAX de venda aplicada; leitura das silvers de todas as coleções por curinga, união por nome de coluna. Nota (T-24): por padrão o `read_parquet` liga o particionamento Hive e cria a coluna `group_id` a partir do caminho (`group_id=24269/`); decidir explicitamente se a leitura usa `hive_partitioning = false` ou aproveita essa coluna. | RF-10, RF-11, RNF-01 | `pytest tests/unidade/test_estrela.py` | com Parquets locais: US$ 10 em 10/10 com PTAX de 09/10 = 5,0000 dá R$ 50,00 e `data_ptax` = 2026-10-09; 10/10, 11/10 e 12/10 usam a PTAX de 09/10, nunca a de 13/10; `dim_colecao` tem as duas coleções | T-27, T-29 | agente | [ ] |
| T-31 | `fato_cambio_diario` por dia de calendário, com PTAX aplicada, data do boletim e CDI do dia (0 em fim de semana e feriado) | RF-12 | `pytest tests/unidade/test_fato_cambio.py` | 10/10 e 11/10 existem com a PTAX de 09/10, `data` do boletim = 2026-10-09 e CDI = 0 | T-30 | agente | [ ] |
| T-32 | Construtor da gold (`src/tcg/gold/construtor.py`): grava fatos e dimensões em `gold/group_id=24269/` pela Guarda de prefixo; silver de outra coleção fora do contrato é ignorada com aviso no log; funciona sem outras coleções; alvo `make gold` **[contêiner]** | RF-10, RF-22 | `pytest tests/integracao/test_construtor_gold.py` | com MinIO descartável: gold criada só em `gold/group_id=24269/`; objetos da segunda coleção inalterados (mesmo hash); cenário sem outras coleções gera só a DRI | T-23, T-31 | agente | [ ] |
| T-33 | Reprocessamento (`src/tcg/reprocessar.py`, alvo `make reprocessar`): apaga pela Guarda de prefixo só silver, gold e gold_turma do group_id 24269 e reconstrói a partir do bruto. O agente implementa; o teste apaga objetos no MinIO descartável e por isso é executado pelo autor **[contêiner]** | RF-13, RNF-04 | `pytest tests/integracao/test_reprocessar.py` | duas execuções seguidas produzem a mesma contagem de linhas, conteúdo igual e nenhuma chave de grão duplicada; nenhum objeto de `raw/` muda de hash | T-32 | agente | [ ] |
| T-34 | Pipeline completo (coleta com cassetes, sincronização, silver, gold) contra MinIO descartável: nenhuma chave fora dos prefixos com `group_id=24269`, nenhum hash do bruto alterado e `chave_raw` rastreável até o bruto **[contêiner]** | RNF-03, RNF-11 | `pytest tests/integracao/test_pipeline.py` | lista de chaves antes e depois só difere nos prefixos permitidos; para uma linha sorteada de `fato_preco_diario`, o objeto de `chave_raw` existe e contém o produto e o preço | T-19, T-28, T-32 | agente | [ ] |

## Bloco D: análise

| ID | Tarefa | Requisitos | Verificação (comando) | Evidência esperada | Depende de | Executor | Status |
|---|---|---|---|---|---|---|---|
| T-35 | Decomposição da variação em reais em carta (r_usd), câmbio (r_cambio) e cruzado (r_usd × r_cambio), em `src/tcg/gold/perguntas.py` | RF-15, RNF-02 | `pytest tests/unidade/test_decomposicao.py` | carta + câmbio + cruzado = r_brl; \|(1 + r_brl) − (1 + r_usd)(1 + r_cambio)\| ≤ 1e-9 em casos gerados | T-30 | agente | [ ] |
| T-36 | Métricas P1 (rankings de alta e queda, filtro de US$ 1 no primeiro dia, sem Code Card) e P2 (índice base 100 de selados contra cartas Double Rare em diante) | RF-15, RF-16 | `pytest tests/unidade/test_p1_p2.py` | dois rankings de até dez itens sem o Code Card e sem o item de US$ 0,90; as duas séries da P2 valem 100 no primeiro dia e a carta Rare fica fora da soma | T-35 | agente | [ ] |
| T-37 | Métricas P3 (valor da coleção e PTAX em índice base 100, data base no primeiro dia comum) e P4 (participação por raridade no último dia e número de itens que somam 80%) | RF-17, RF-18 | `pytest tests/unidade/test_p3_p4.py` | todas as séries valem 100 em 03/11 no cenário do RF-17; 3 itens para os valores 50, 20, 15, 10 e 5; participações somam 100% | T-30 | agente | [ ] |
| T-38 | Métrica P5: retorno no período contra o desvio-padrão dos retornos diários, só cartas acima de US$ 5, descartando retornos que atravessam lacuna | RF-19 | `pytest tests/unidade/test_p5.py` | preços 10, 11 e 9,9 dão retorno −1% e volatilidade = desvio-padrão de (+10%, −10%); com 03/11 ausente, só 01/11 → 02/11 entra | T-30 | agente | [ ] |
| T-39 | Decidir a regra da carteira propria e registrá-la no ADR-005 (`docs/adr/ADR-005-carteira-propria.md`) | RF-23 | `git log --oneline -- docs/adr/ADR-005-carteira-propria.md` | ADR com a regra do autor, commitado antes do T-41 | — | autor | [ ] |
| T-40 | ADR-006: fallback do selado, com base no resultado do T-13 sobre o preço do booster box (`docs/adr/ADR-006-fallback-selado.md`) | RF-23 | `git log --oneline -- docs/adr/ADR-006-fallback-selado.md` | ADR revisado e commitado pelo autor antes do T-41, citando a evidência do T-13 | T-13 | agente | [ ] |
| T-41 | Composição das cinco carteiras (`src/tcg/gold/carteiras.py`, funções puras) só com dados do primeiro dia: selado com fallback do ADR-006, cesta_raras com desempate por `product_id` e `acabamento`, propria pela regra do ADR-005 ("regra pendente" sem ADR), dolar e cdi | RF-23 | `pytest tests/unidade/test_composicao.py` | composição idêntica com o primeiro dia e com dez dias a mais; no empate da décima posição entra o menor `product_id`; unidades inteiras e sobra em caixa | T-30, T-39, T-40 | agente | [ ] |
| T-42 | Valor de liquidação diário: taxa_venda do parâmetro, PTAX de compra aplicada, caixa e carteira cdi rendendo só em dia útil, último preço observado só na avaliação, com marcação | RF-24 | `pytest tests/unidade/test_liquidacao.py` | 1 × US$ 100, PTAX 5,00, taxa 15% e caixa R$ 10 dão R$ 435,00; o dia 3 sem preço usa o do dia 2 e sai marcado; a silver não ganha linha; mudar a taxa para 10% altera o valor | T-41 | agente | [ ] |
| T-43 | Métricas das carteiras: retorno acumulado, excesso sobre o CDI, perda máxima e dias com preço carregado, calculadas com a taxa do parâmetro e com taxa 0 | RF-25 | `pytest tests/unidade/test_metricas_carteira.py` | série 1000, 1200, 900, 1100 dá retorno de 10% e perda máxima de 25%; a diferença entre taxa 15% e taxa 0 é zero para dolar e cdi | T-42 | agente | [ ] |
| T-44 | Gravação de `gold_turma/carteira/group_id=24269/carteira.parquet` no contrato, pela Guarda de prefixo, dentro do `make gold` **[contêiner]** | RF-26 | `pytest tests/integracao/test_gold_turma.py` | colunas e tipos do contrato; uma linha por dia de calendário × carteira; retorno_acumulado = valor_brl / 1000 − 1; taxa_venda = 0 em dolar e cdi | T-32, T-43 | agente | [ ] |

## Bloco E: painel e operação

| ID | Tarefa | Requisitos | Verificação (comando) | Evidência esperada | Depende de | Executor | Status |
|---|---|---|---|---|---|---|---|
| T-45 | Base do painel (`dashboard/app.py`, Streamlit): reais por padrão e opção em dólar, filtro de preço mínimo com padrões por pergunta, aviso de período curto, séries interrompidas nas lacunas, imagem e link com avisos de indisponível; alvo `make painel` | RF-14, RF-20, RF-21 | `pytest tests/unidade/test_painel_base.py` | com `streamlit.testing` e dados locais: "dólar" e US$ 5 trocam a moeda e removem os itens abaixo do mínimo; o dia sem coleta fica sem ponto; aparecem "imagem indisponível" e "link indisponível" quando os campos são nulos | T-32 | agente | [ ] |
| T-46 | Painel das perguntas P1 a P5, com o aviso de falta de outras coleções em P3, P4 e P5 | RF-15, RF-16, RF-17, RF-18, RF-19, RF-22 | `pytest tests/unidade/test_painel_perguntas.py` | as cinco seções renderizam sem erro; sem outras coleções, P3, P4 e P5 mostram o aviso e só a DRI, sem gráfico vazio; a DRI fica destacada na P3 | T-36, T-37, T-38, T-45 | agente | [ ] |
| T-47 | Painel das carteiras (com a taxa do parâmetro e com taxa 0, lado a lado, preço carregado marcado, "regra pendente" para a propria sem ADR) e placar da turma lendo `gold_turma/carteira/` de todas as coleções, somente leitura | RF-24, RF-25, RF-28 | `pytest tests/unidade/test_painel_carteiras.py` | com três coleções: placar "2 de 3", "1 de 3" e a coleção de menor perda máxima; só com a DRI, aviso explícito; nenhum objeto é gravado | T-43, T-44, T-46 | agente | [ ] |
| T-48 | Verificador de cobertura (`src/tcg/cobertura/verificador.py`, alvo `make cobertura`): compara cada data entre o primeiro e o último dia com os quatro arquivos na branch `dados-raw` e a tabela "Dias sem coleta" do README | RF-27 | `pytest tests/unidade/test_cobertura.py` | sucesso quando toda data tem os quatro arquivos ou uma linha com motivo; falha listando as datas faltantes caso contrário; linha sem motivo não conta | T-17 | agente | [ ] |
| T-49 | README completo: visão geral, serviços usados e custo zero, "Como rodar" a partir de clone limpo, disparo manual antes das 23h59 UTC (R-01), prazo dos workflows agendados (R-02), tabela "Dias sem coleta" mantida | RNF-09, RNF-10, RNF-13 | `pytest tests/unidade/test_readme.py` | o teste confirma as seções obrigatórias, a lista de serviços e a tabela "Dias sem coleta" no formato que o verificador lê | T-47, T-48 | agente | [ ] |
| T-50 | Reprodução a partir de clone limpo, seguindo só o README **[rede, contêiner]** | RNF-10 | `make up && make sync && make silver && make gold && make test` | todos os comandos terminam com sucesso num clone novo; o painel abre com `make painel`; resultado registrado em `docs/evidencias/T-50_clone_limpo.md` | T-49 | autor | [ ] |
| T-51 | Busca de credenciais no histórico completo do repositório e nos logs de execução | RNF-08 | `git log -p --all \| grep -F -e "<valor da chave>" -e "<valor do segredo>"`, executado pelo autor com os valores do `.env` | nenhuma ocorrência; resultado registrado sem os valores em `docs/evidencias/T-51_busca_credenciais.md` | T-49 | autor | [ ] |

## Bloco F: validação

| ID | Tarefa | Requisitos | Verificação (comando) | Evidência esperada | Depende de | Executor | Status |
|---|---|---|---|---|---|---|---|
| T-52 | Conferir o histórico de execuções do agendador e a tabela "Dias sem coleta" no período, e contar as requisições ao TCGCSV nos logs **[rede]** | RNF-12, RNF-13 | `gh run list --workflow coleta.yml --limit 100 && make cobertura` | uma execução por dia depois das 20h UTC ou o dia registrado com motivo; no máximo 10.000 requisições por dia; registro em `docs/evidencias/T-52_agendador.md` | T-48, T-49 | autor | [ ] |
| T-53 | Avaliação ATAM (`docs/atam.md`): cenários de qualidade a partir dos RNF, pontos de sensibilidade, trade-offs, riscos e não riscos, ligados aos ADRs | RNF-01 a RNF-13 | `test -s docs/atam.md && grep -c "RNF-" docs/atam.md` | cada RNF aparece em ao menos um cenário, com resposta e medida | T-50, T-51, T-52 | agente | [ ] |
| T-54 | Matriz de rastreabilidade (`docs/rastreabilidade.md`) gerada com o prompt 11.2 do enunciado da Aula 08: RF/RNF → tarefa → teste → commit | RF-01 a RF-28, RNF-01 a RNF-13 | `for r in $(seq -f "RF-%02g" 1 28) $(seq -f "RNF-%02g" 1 13); do grep -q "$r" docs/rastreabilidade.md \|\| echo "falta $r"; done` | nenhuma linha "falta"; cada requisito aponta para tarefa, teste e commit | T-53 | agente | [ ] |
| T-55 | Registro de pendências (`docs/pendencias_aula08.md`): hipóteses ainda abertas, requisitos parcialmente atendidos, riscos aceitos e dias sem coleta | — | `test -s docs/pendencias_aula08.md` | cada pendência tem descrição, origem (RF, RNF, risco ou tarefa) e encaminhamento | T-54 | agente | [ ] |
| T-56 | Autoauditoria final com o prompt 11.1 do enunciado da Aula 08, gravada em `docs/auditoria_final.md`, sem corrigir nada | — | `test -s docs/auditoria_final.md && git diff --stat -- . ':!docs/auditoria_final.md'` | o arquivo de auditoria existe; o `git diff` não mostra nenhum outro arquivo alterado pela tarefa | T-55 | agente | [ ] |

## Requisitos sem tarefa

Nenhum. Todo RF e RNF de `specs/spec.md` é atendido por pelo menos uma tarefa (ver "Cobertura").

## Cobertura

| Requisito | Tarefas |
|---|---|
| RF-01 | T-03, T-05, T-06, T-07, T-10, T-12, T-20 |
| RF-02 | T-06, T-07, T-08, T-09, T-12, T-19 |
| RF-03 | T-03, T-04, T-11 |
| RF-04 | T-06 |
| RF-05 | T-07, T-17, T-18, T-19, T-21 |
| RF-06 | T-03, T-24, T-27 |
| RF-07 | T-25, T-26, T-27 |
| RF-08 | T-25 |
| RF-09 | T-13, T-25 |
| RF-10 | T-24, T-29, T-30, T-32 |
| RF-11 | T-30 |
| RF-12 | T-31 |
| RF-13 | T-22, T-23, T-33 |
| RF-14 | T-45 |
| RF-15 | T-35, T-36, T-46 |
| RF-16 | T-13, T-36, T-46 |
| RF-17 | T-29, T-37, T-46 |
| RF-18 | T-37, T-46 |
| RF-19 | T-38, T-46 |
| RF-20 | T-13, T-45 |
| RF-21 | T-45 |
| RF-22 | T-29, T-32, T-46 |
| RF-23 | T-13, T-39, T-40, T-41 |
| RF-24 | T-03, T-42, T-47 |
| RF-25 | T-43, T-47 |
| RF-26 | T-44 |
| RF-27 | T-48 |
| RF-28 | T-29, T-47 |
| RNF-01 | T-30 |
| RNF-02 | T-35 |
| RNF-03 | T-18, T-22, T-23, T-34 |
| RNF-04 | T-22, T-33 |
| RNF-05 | T-02 |
| RNF-06 | T-20, T-28 |
| RNF-07 | T-19 |
| RNF-08 | T-03, T-07, T-10, T-16, T-18, T-51 |
| RNF-09 | T-07, T-14, T-15, T-49 |
| RNF-10 | T-01, T-14, T-15, T-16, T-49, T-50 |
| RNF-11 | T-27, T-34 |
| RNF-12 | T-04, T-12, T-52 |
| RNF-13 | T-10, T-11, T-12, T-49, T-52 |
