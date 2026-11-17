# Avaliação ATAM

- **Avaliador:** autor, com apoio do agente na redação
- **Data:** 2026-11-16
- **Base:** só o que está no repositório: `AGENTS.md`, `docs/00_persona.md`, `docs/01_objetivos_negocio.md`, `specs/spec.md`, `specs/plan.md`, `specs/tasks.md`, `docs/adr/`, `docs/evidencias/`, `docs/prompts.md`, testes e histórico de commits. Nenhum código foi alterado nesta avaliação.
- **Regra de evidência:** cada afirmação aponta para uma evidência existente (arquivo de `docs/evidencias/`, ADR, teste ou commit). Quando não há evidência gravada, o texto diz que é **hipótese** ou **pendência**.

## 1. Objetivo e escopo

O objetivo desta avaliação é conferir se a arquitetura descrita em `specs/plan.md` e nos ADR-001 a ADR-008 atende aos requisitos não funcionais RNF-01 a RNF-13 de `specs/spec.md`, com base no que aconteceu de fato entre 2026-11-03 e 2026-11-16. Também se registram os pontos de sensibilidade, os tradeoffs, os riscos e os não riscos que aparecem nessa conferência.

Dentro do escopo:
- o Coletor diário no GitHub Actions, a branch `dados-raw` e o Sincronizador (ADR-001, ADR-007, ADR-008);
- o data lake da turma (RustFS) como armazenamento oficial e o MinIO local e descartável (ADR-002, ADR-008);
- silver, gold, gold_turma, reprocessamento e Guarda de prefixo (ADR-003, ADR-004);
- as carteiras (ADR-005, ADR-006) e o painel;
- a leitura das silvers e da gold_turma de outras coleções, sempre somente leitura (RES-13).

Fora do escopo: desempenho do painel e tempo de reprocessamento, que continuam como hipótese nos ADR-003 e ADR-004, e a qualidade dos dados de terceiros, que este projeto só lê.

## 2. Atributos de qualidade e drivers

| Atributo | Objetivos e drivers | Restrições | RNF |
|---|---|---|---|
| Disponibilidade da coleta (operabilidade) | OBJ-01, DRV-01, DRV-03 | RES-03, RES-07 | RNF-13 |
| Uso responsável da fonte | OBJ-01 | RES-03 | RNF-12 |
| Correção dos dados | OBJ-02, DRV-02 | RES-04 | RNF-01, RNF-02 |
| Integridade do bruto e escrita isolada | OBJ-01, DRV-06 | RES-08, RES-13 | RNF-03 |
| Confiabilidade do reprocessamento | OBJ-06 | RES-08 | RNF-04 |
| Testabilidade | OBJ-06 | RES-03, RES-07 | RNF-05, RNF-06, RNF-07 |
| Segurança (segredos) | OBJ-06 | RES-06 | RNF-08 |
| Custo | OBJ-06 | RES-02 | RNF-09 |
| Reprodutibilidade | OBJ-06, DRV-06 | — | RNF-10 |
| Auditabilidade | DRV-06 | — | RNF-11 |
| Comparabilidade com outras coleções | OBJ-04, OBJ-05 | RES-13 | RNF-03 (só leitura); sem RNF próprio, ligado a RF-10, RF-17, RF-19, RF-22 e RF-28 |

## 3. Árvore de utilidade

Prioridade no formato (importância para o negócio, dificuldade de atender): A = alta, M = média, B = baixa.

```text
Utilidade
├── Disponibilidade da coleta
│   └── C-01 atraso de até 10 h da execução principal sem perder a data ............ (A, A)
├── Uso responsável da fonte
│   └── C-02 segunda execução do ciclo sem nenhuma requisição ......................... (A, B)
├── Correção dos dados
│   ├── C-03 fim de semana e feriado nunca usam PTAX posterior ......................... (A, M)
│   └── C-04 identidade carta × câmbio × cruzado ................................... (A, B)
├── Integridade
│   └── C-05 chave fora do prefixo recusada antes do SDK, bruto com o mesmo hash ....... (A, M)
├── Confiabilidade
│   └── C-06 reprocessamento duas vezes com o mesmo conteúdo ........................... (M, M)
├── Testabilidade
│   ├── C-07 testes de unidade e de integração sem rede ................................ (M, B)
│   └── C-08 integração com MinIO descartável .......................................... (M, M)
├── Segurança
│   └── C-09 troca de endpoint e credenciais sem vazamento nem mudança de código ....... (A, M)
├── Custo
│   └── C-10 todos os serviços gratuitos ............................................... (M, B)
├── Reprodutibilidade
│   └── C-11 clone limpo reconstrói silver, gold e painel .............................. (A, M)
├── Auditabilidade
│   └── C-12 linha do fato rastreável até o objeto bruto ............................... (A, B)
└── Comparabilidade com outras coleções
    └── C-13 silver de terceiro com histórico curto ou ausente ......................... (M, A)
```

## 4. Cenários

Cada cenário tem seis partes: fonte, estímulo, artefato, ambiente, resposta e medida. Depois vêm a situação observada e a evidência.

### C-01: continuidade da série (RNF-13)

| Parte | Conteúdo |
|---|---|
| Fonte | Agendador do GitHub Actions |
| Estímulo | A execução das 20h30 UTC atrasa cerca de 10 horas, ou é recusada. |
| Artefato | Coletor diário e branch `dados-raw` |
| Ambiente | Operação normal, coleta diária agendada |
| Resposta | A reserva das 06h30 UTC, ou um disparo manual dentro do ciclo, grava a data de referência D, porque o ciclo vai das 20h UTC de D às 20h UTC de D+1 (ADR-007). |
| Medida | Nenhuma data sem bruto no período: `make cobertura` com 0 faltantes, e cada data com pelo menos uma execução bem-sucedida dentro do ciclo. |

Situação: **atendido, com ressalva**.
- Atrasos observados nas 25 execuções agendadas de 03/11 a 16/11: média de 6h14min47s e máximo de 10h15min30s (reserva 42657979297). A principal atrasou em média 4h20min05s e no máximo 6h20min41s. Nenhum dos 26 horários agendados ficou sem execução (`docs/evidencias/T-52_agendador.md`).
- `make cobertura`: 13 datas, de 2026-11-03 a 2026-11-15, todas com bruto e 0 faltantes. A tabela "Dias sem coleta" do README está vazia (`docs/evidencias/T-52_agendador.md`, `docs/evidencias/T-50_clone_limpo.md`).
- Ressalva: o RNF-13 pede coleta "sem intervenção manual". As datas 03/11 e 04/11 foram gravadas por execuções manuais: 41715282582, a primeira coleta (`docs/evidencias/T-12_primeira_coleta.txt`), e 41949048376, a recuperação da T-57 (`docs/evidencias/T-57_recuperacao.txt`). As agendadas desses ciclos foram recusadas pela regra de horário anterior ao ADR-007 (`docs/evidencias/T-57_diagnostico.txt`). De 05/11 a 15/11, todas as datas foram gravadas por execuções agendadas.
- Testes: `tests/unidade/test_workflow.py::test_cron_principal_20h30_e_reserva_06h30_utc` e os testes de fronteira da data de referência da T-57 (`docs/evidencias/T-57_suite.txt`).

### C-02: limite de requisições ao TCGCSV (RNF-12)

| Parte | Conteúdo |
|---|---|
| Fonte | Agendador (principal e reserva) ou disparo manual |
| Estímulo | Duas ou mais execuções no mesmo ciclo |
| Artefato | Guarda de data de referência e duplicidade; Cliente HTTP |
| Ambiente | Operação normal |
| Resposta | Um arquivo da data de referência que já existe é pulado antes de qualquer requisição. O Cliente HTTP recusa a requisição que passar do limite diário. |
| Medida | No máximo 10.000 requisições ao TCGCSV por dia (`limite_requisicoes_dia` em `config/parametros.toml`). |

Situação: **atendido**. No período houve 26 requisições ao TCGCSV, no máximo 4 num dia civil UTC (07/11) e 2 por data de referência. Nas 13 execuções com o ciclo já coletado, nenhuma requisição foi enviada (`docs/evidencias/T-52_agendador.md`). Testes: `tests/unidade/test_http.py::test_requisicao_alem_do_limite_e_recusada` e `test_repeticoes_contam_no_limite` (`docs/evidencias/T-04_cliente_http.txt`).

### C-03: nenhuma cotação posterior (RNF-01)

| Parte | Conteúdo |
|---|---|
| Fonte | BCB (PTAX só em dia útil) |
| Estímulo | Preço de sábado, domingo ou feriado |
| Artefato | ASOF JOIN da PTAX aplicada na gold |
| Ambiente | Construção da gold |
| Resposta | O preço usa a PTAX de maior `data` ≤ dia, e o fato guarda `cotacao_aplicada` e `data_ptax` (ADR-003). |
| Medida | Nenhuma linha usa um boletim de data posterior. |

Situação: **atendido**. Testes: `tests/unidade/test_estrela.py::test_nunca_usa_ptax_posterior` (`docs/evidencias/T-30_estrela.txt`) e `tests/unidade/test_fato_cambio.py::test_feriado_nunca_usa_ptax_posterior` (`docs/evidencias/T-31_fato_cambio.txt`).

### C-04: identidade da decomposição (RNF-02)

| Parte | Conteúdo |
|---|---|
| Fonte | Persona (P1) |
| Estímulo | Pedido da variação em reais de um item, separada em carta, câmbio e cruzado |
| Artefato | `src/tcg/gold/perguntas.py` |
| Ambiente | Painel com a gold construída |
| Resposta | r_brl é decomposto em r_usd, r_cambio e r_usd × r_cambio. |
| Medida | \|(1 + r_brl) − (1 + r_usd) × (1 + r_cambio)\| ≤ 1e-9 |

Situação: **atendido**. Teste: `tests/unidade/test_decomposicao.py::test_identidades_em_casos_gerados` (`docs/evidencias/T-35_decomposicao.txt`).

### C-05: escrita isolada e bruto imutável (RNF-03)

| Parte | Conteúdo |
|---|---|
| Fonte | Erro de programação ou de operação |
| Estímulo | Tentativa de gravar ou apagar uma chave em `raw/`, de outro group_id ou com `..` |
| Artefato | Guarda de prefixo; Sincronizador; bucket `tcg` da turma |
| Ambiente | Credencial de administrador compartilhada pela turma (ADR-008) |
| Resposta | A chave é recusada antes da chamada ao SDK. O Sincronizador valida a chave e faz `stat_object` antes do `put_object` (ADR-001, ADR-004, ADR-008). |
| Medida | Nenhuma chave fora dos prefixos com `group_id=24269` é criada, alterada ou apagada, e nenhum objeto do bruto muda de hash. |

Situação: **atendido nos testes**. Testes: `tests/unidade/test_guarda_prefixo.py::test_escrita_recusada_antes_do_sdk` e `test_exclusao_recusada_antes_do_sdk` (`docs/evidencias/T-23_guarda_prefixo.txt`), `tests/unidade/test_sincronizador.py::test_chave_fora_do_escopo_nunca_chega_ao_sdk` e `tests/integracao/test_reprocessar_integracao.py::test_raw_e_terceiros_mantem_o_hash` (`docs/evidencias/T-33_reprocessar.txt`, `docs/evidencias/T-34_pipeline.txt`). No lake da turma, as sincronizações registram as chaves existentes como recusadas, por exemplo 0/52/0 em 16/11 (`docs/evidencias/T-52_agendador.md`).

### C-06: reprocessamento idempotente (RNF-04)

| Parte | Conteúdo |
|---|---|
| Fonte | Autor |
| Estímulo | `make reprocessar` executado duas vezes seguidas |
| Artefato | Silver, gold e gold_turma da DRI |
| Ambiente | MinIO descartável (teste) |
| Resposta | Apaga só os prefixos derivados da DRI e reconstrói tudo a partir do bruto (ADR-004). |
| Medida | Mesmas chaves, contagens e conteúdo nas duas execuções, sem chave de grão duplicada. |

Situação: **atendido nos testes**. Testes: `tests/integracao/test_reprocessar_integracao.py::test_duas_execucoes_mesmas_chaves_contagens_e_conteudo` e `test_nenhuma_chave_de_grao_duplicada` (`docs/evidencias/T-33_reprocessar.txt`). O comando é executado só pelo autor (`AGENTS.md`).

### C-07: testes sem rede (RNF-05, RNF-06)

| Parte | Conteúdo |
|---|---|
| Fonte | Desenvolvedor rodando `make test` |
| Estímulo | Um teste tenta abrir uma conexão de rede |
| Artefato | Fixture de `tests/conftest.py`; cassetes vcrpy |
| Ambiente | Codespace sem acesso às fontes |
| Resposta | A conexão falha com erro explícito. A integração da coleta e da silver usa respostas reais gravadas. |
| Medida | Todos os testes passam, e nenhuma requisição sai para a internet. |

Situação: **atendido**. Testes: `tests/unidade/test_bloqueio_rede.py` (`docs/evidencias/T-02_bloqueio_rede.txt`), `tests/integracao/test_coleta_cassetes.py::test_requisicao_fora_do_cassete_falha_sem_sair_para_a_rede` e `test_coleta_grava_os_quatro_arquivos_com_hash_do_bruto_real` (`docs/evidencias/T-20_cassetes.txt`).

### C-08: integração com MinIO descartável (RNF-07)

| Parte | Conteúdo |
|---|---|
| Fonte | `make test` |
| Estímulo | Testes de gravação, sincronização e recusa de sobrescrita |
| Artefato | testcontainers com a imagem do ADR-002 |
| Ambiente | Codespace com Docker |
| Resposta | Um contêiner novo é criado para o teste e descartado no fim (ADR-002). |
| Medida | Os testes passam sem tocar o data lake da turma nem o MinIO local. |

Situação: **atendido**. Testes: `tests/integracao/test_minio.py::test_imagem_igual_a_do_compose` e `test_sincronizacao_da_branch_duas_vezes` (`docs/evidencias/T-19_minio_descartavel.txt`, `docs/evidencias/T-58_suite.txt`).

### C-09: troca de endpoint e credenciais do data lake (RNF-08)

| Parte | Conteúdo |
|---|---|
| Fonte | Responsável pelo data lake da turma |
| Estímulo | Em 15/11, troca do endpoint e das credenciais sem aviso prévio ao job agendado |
| Artefato | Passo de sincronização do workflow; `.env`; secrets do repositório |
| Ambiente | Operação normal, com a coleta agendada |
| Resposta | O passo de sincronização falha, e o push do bruto na `dados-raw` permanece. O autor atualiza só o `.env` e os secrets, sem mudar código (vínculo em tempo de configuração, ADR-008, revisão de 15/11). A sincronização seguinte completa o lake. |
| Medida | Nenhuma credencial no histórico, nos arquivos ou nos logs; nenhuma linha de código alterada; nenhuma data de bruto perdida. |

Situação: **atendido**.
- A execução 43656334396 (15/11, 00:04 UTC) gravou e publicou o bruto de 14/11. O sync falhou com `InvalidAccessKeyId`, sem nenhum valor de credencial no log (`docs/evidencias/T-52_agendador.md`).
- Depois da troca, `make sync` local e a execução coleta #26 terminaram com 0 enviados, 48 recusados e 0 falhas (`docs/evidencias/T-58_troca_endpoint.txt`). O commit da troca (`9e59390`) só mexe em documentação e no `.env.example`.
- A busca de credenciais no histórico completo, nos arquivos e no log do run agendado teve 0 ocorrências (`docs/evidencias/T-51_busca_credenciais.md`). Nos 29 logs do agendador, os secrets aparecem só como `***` (`docs/evidencias/T-52_agendador.md`).
- Testes: `tests/unidade/test_workflow.py::test_secrets_so_no_env_do_passo_de_sincronizacao`, `test_secrets_nunca_em_run_echo_ou_set_x`, `test_sem_gatilho_de_pull_request` (`docs/evidencias/T-58_suite.txt`), `tests/unidade/test_log.py::test_credenciais_nao_aparecem_no_log` e `tests/unidade/test_config.py::test_erro_nao_expoe_valor_de_credencial` (`docs/evidencias/T-03_config_log.txt`).

### C-10: custo zero (RNF-09)

| Parte | Conteúdo |
|---|---|
| Fonte | Avaliador da disciplina |
| Estímulo | Revisão da lista de serviços do README |
| Artefato | README, seção de serviços |
| Ambiente | Uso do projeto durante o período |
| Resposta | GitHub (repositório público, Actions, Codespaces), data lake da turma e fontes públicas, sem serviço pago (ADR-001, ADR-008). |
| Medida | Todos os serviços listados são gratuitos no uso do projeto. |

Situação: **atendido**. Testes: `tests/unidade/test_readme.py::test_todo_servico_da_tabela_e_gratuito` (`docs/evidencias/T-49_readme.txt`).

### C-11: reprodução a partir de clone limpo (RNF-10)

| Parte | Conteúdo |
|---|---|
| Fonte | Avaliador ou novo desenvolvedor |
| Estímulo | Clone limpo, com o `.env` preenchido a partir do `.env.example` |
| Artefato | README, Makefile, `pyproject.toml` |
| Ambiente | Codespace novo |
| Resposta | `make setup`, `make sync`, `make silver`, `make gold`, `make test` e `make painel` reconstroem tudo a partir do bruto. |
| Medida | Testes passam; silver, gold e painel reconstruídos. |

Situação: **atendido**. Num clone em `/tmp/clone-limpo` (16/11, 23h05 a 23h10 UTC): 52 chaves recusadas na sincronização, silver com 5798 preços em 13 datas e quarentena vazia, gold com a DRI e a coleção 24541, `make test` com 463 passed e `make cobertura` com 0 faltantes (`docs/evidencias/T-50_clone_limpo.md`).

### C-12: rastreabilidade até o bruto (RNF-11)

| Parte | Conteúdo |
|---|---|
| Fonte | Avaliador |
| Estímulo | Escolhe uma linha qualquer de `fato_preco_diario` |
| Artefato | Coluna `chave_raw` na silver e na gold |
| Ambiente | Pipeline completo contra MinIO descartável |
| Resposta | A `chave_raw` aponta para o objeto do bruto que contém o produto e o preço. |
| Medida | O objeto existe e contém o produto e o preço da linha. |

Situação: **atendido nos testes**. Testes: `tests/integracao/test_pipeline.py::test_toda_chave_raw_da_dri_existe_no_bruto` e `test_chave_raw_de_linha_sorteada_rastreavel`, com uma linha sorteada (semente 34) seguida até `raw/tcgplayer/group_id=24269/data=2026-11-03/prices.json` (`docs/evidencias/T-34_pipeline.txt`).

### C-13: dependência das silvers de outras coleções (RNF-03; RF-10, RF-17, RF-19, RF-22, RF-28)

| Parte | Conteúdo |
|---|---|
| Fonte | Outros coletores da turma |
| Estímulo | Na troca de endpoint de 15/11, a coleção 24541 ficou só com os dias mais recentes no data lake novo. |
| Artefato | Construtor da gold (leitura por curinga), P3, P5 e placar do painel |
| Ambiente | Data lake da turma, somente leitura fora do prefixo da DRI |
| Resposta | A gold lê o que existe, sem copiar nem gravar fora de `group_id=24269` (ADR-003). A P3 usa como base o primeiro dia comum às coleções exibidas, com cesta fixa (RF-17). A P5 usa a janela de cada coleção (RF-19). O placar lê a gold_turma que existir (RF-28). Sem nenhuma outra coleção, o painel mostra o aviso do RF-22. |
| Medida | Nenhuma escrita fora do prefixo da DRI, nenhum valor inventado, e o período comparado fica visível. |

Situação: **atendido para a escrita isolada; comparação limitada**.
- A gold de 16/11 tem a DRI e a 24541: `dim_colecao: 2` e `fato_preco_diario: 7114` (`docs/evidencias/T-50_clone_limpo.md`). Dessas 7114 linhas, 5798 são da DRI (13 datas). As 1316 restantes são 2 dias da 24541, com 658 linhas por dia (`docs/evidencias/T-53_observacoes_painel.md`).
- No placar da turma, a coleção ASC aparece com período de 14/11 a 15/11 e com o aviso de período diferente. O placar fica "selado acima da cdi: 0 de 2" e "cesta_raras acima da dolar: 1 de 2" (`docs/evidencias/T-53_observacoes_painel.md`).
- Efeito: a P3 tem a base comum no primeiro dia da outra coleção, só com 2 dias de comparação. A P5 dessa coleção tem no máximo um retorno diário por item, portanto sem volatilidade amostral. O placar compara carteiras de 13 dias com carteiras de 2 dias. As três respostas dependem de dados que o projeto não controla.
- Testes do comportamento sem outras coleções e com silver fora do contrato: `tests/unidade/test_painel_perguntas.py::test_sem_outras_colecoes_p3_p4_p5_avisam_e_mostram_so_a_dri` (`docs/evidencias/T-47_painel_carteiras.txt`) e `tests/integracao/test_construtor_gold.py::test_silver_fora_do_contrato_ignorada_com_aviso` (`docs/evidencias/T-58_suite.txt`).

## 5. Abordagens arquiteturais e ADRs por cenário

| Cenário | RNF | Abordagens e táticas | ADR |
|---|---|---|---|
| C-01 | RNF-13 | Redundância de agendamento (20h30 e 06h30 UTC); data de referência pelo ciclo; disparo manual dentro do ciclo; verificador de cobertura sobre a branch | ADR-007, ADR-001 |
| C-02 | RNF-12 | Verificação de existência antes da requisição; contador com limite no Cliente HTTP; grupo de concorrência | ADR-007, ADR-001 |
| C-03 | RNF-01 | ASOF JOIN pela maior `data` ≤ dia; fato com a cotação aplicada e a `data_ptax` | ADR-003 |
| C-04 | RNF-02 | Decomposição multiplicativa num único módulo com teste de identidade | — (`specs/plan.md`, seção 4) |
| C-05 | RNF-03 | Guarda de prefixo como ponto único de escrita e exclusão; validação de chave antes do SDK; `stat_object` antes do `put_object` | ADR-004, ADR-008, ADR-001 |
| C-06 | RNF-04 | Camadas derivadas reconstruídas do bruto; caminhos determinísticos | ADR-004 |
| C-07 | RNF-05, RNF-06 | Bloqueio de socket por fixture; respostas HTTP reais gravadas | — (`specs/plan.md`, seção 6) |
| C-08 | RNF-07 | Imagem com tag fixada, a mesma do compose, em contêiner descartável | ADR-002 |
| C-09 | RNF-08 | Limitar exposição (secrets só no `env` de um passo); vínculo em tempo de configuração; isolamento de falhas (sync depois do push) | ADR-008, ADR-001 |
| C-10 | RNF-09 | Só serviços gratuitos: GitHub, data lake da turma e fontes públicas | ADR-001, ADR-008 |
| C-11 | RNF-10 | Makefile como ponto de entrada único; versões fixadas; README com "Como rodar" | ADR-002, ADR-004 |
| C-12 | RNF-11 | `chave_raw` em cada linha da silver e da gold; bruto byte a byte com hash | ADR-001, ADR-003 |
| C-13 | RNF-03 | Leitura por curinga; isolamento de falhas por coleção; cestas fixas e base comum; aviso de ausência | ADR-003 |

## 6. Pontos de sensibilidade

| # | Parâmetro ou decisão | Atributo afetado | Observação | Evidência |
|---|---|---|---|---|
| S-01 | Taxa de venda de 15% (`taxa_venda` em `config/parametros.toml`, hipótese declarada no RF-24) | Validade da comparação entre carteiras (OBJ-05) | Na propria, o retorno acumulado foi de −12,49% com a taxa e de −3,49% sem ela: a taxa sozinha muda o resultado em 9,01 pontos percentuais. O painel mostra as duas versões lado a lado (RF-25). | Testes: `tests/unidade/test_liquidacao.py::test_criterio_da_tarefa_435_e_taxa_10` e `test_taxa_zero_contra_15_so_muda_cartas_e_selados` (`docs/evidencias/T-42_liquidacao.txt`). Valores do painel de 16/11: propria com R$ 875,05, −12,49% com taxa e −3,49% sem taxa, diferença de −9,01 p.p. (`docs/evidencias/T-53_observacoes_painel.md`). |
| S-02 | Unidades inteiras com R$ 1.000,00 no selado e R$ 100,00 por carta (RF-23, ADR-005, ADR-006) | Validade da comparação entre carteiras; leitura do placar (RF-28) | Na DRI, a selado e a cesta_raras ficaram 100% em caixa: o booster box custa mais que R$ 1.000,00, e cada uma das dez cartas mais caras custa mais que R$ 100,00. Só a propria teve exposição real a mercado. Selado e cesta_raras da DRI medem o caixa rendendo CDI. | Composição do painel de 16/11: booster box a R$ 2.095,11, carta mais barata da cesta_raras a R$ 132,12, selado e cesta_raras com R$ 1.004,07 (0,41%), igual à cdi (`docs/evidencias/T-53_observacoes_painel.md`); registro da conferência com dados reais na T-47 (`docs/prompts.md`, "Observação para o ATAM"); consequência prevista no ADR-006; commit `fcf0f80`. |
| S-03 | Hora de virada do ciclo (20h UTC) e horário da principal (20h30 UTC) | Correção dos dados; disponibilidade da coleta | Uma coleta antes de a fonte atualizar gravaria o preço do ciclo anterior como `data=D`, sem correção possível. O horário real de atualização do TCGCSV continua **hipótese** (ADR-007, Riscos). | ADR-007; `config/parametros.toml` (`hora_virada_ciclo_utc`) |
| S-04 | Janela de 10 dias da PTAX e do CDI | Correção dos dados (RNF-01) | Define até quantos dias úteis sem coleta ainda se recuperam na PTAX e no CDI. Continua **hipótese** (`specs/spec.md`, Perguntas abertas). | `config/parametros.toml` (`janela_dias`) |
| S-05 | Cesta fixa e base comum da P2 e da P3 | Comparabilidade (C-13) | Um item sem preço em algum dia sai da cesta inteira, e a base da P3 é o primeiro dia comum. A coleção com o histórico mais curto define o período de toda a P3. | RF-16, RF-17; `docs/evidencias/T-37_p3_p4.txt` |
| S-06 | Filtros de preço mínimo (US$ 1 na P1, US$ 5 na P5, estritamente acima) | Correção das respostas | Um item com exatamente US$ 1 ou US$ 5 no primeiro dia fica de fora. | RF-14; `docs/evidencias/T-36_p1_p2.txt`, `docs/evidencias/T-38_p5.txt` |

## 7. Tradeoffs

| # | Decisão | Ganha | Perde | ADR |
|---|---|---|---|---|
| TR-01 | O bruto na branch `dados-raw` é a fonte da verdade; o data lake da turma é o armazenamento oficial. | Durabilidade e recuperabilidade: o bruto não depende de um servidor de terceiros com credencial de administrador compartilhada, e a coleta não perde o dia se o lake estiver fora do ar. O verificador de cobertura lê a branch. | O bruto existe em dois lugares, e o lake pode ficar um ciclo atrás. O job pode ficar vermelho com a coleta perfeita, como na execução 43656334396, e a conferência do RNF-13 precisa separar o passo da coleta do passo da sincronização. A imutabilidade no lake depende dos colegas. | ADR-001, ADR-008 |
| TR-02 | Dois horários agendados e data pelo ciclo | Disponibilidade: atrasos de até 10h15min30s não perderam nenhuma data (C-01). | A `data` deixa de ser a data civil da execução, o histórico tem duas execuções por dia, e 13 das 29 execuções não fizeram nenhuma requisição (`docs/evidencias/T-52_agendador.md`). | ADR-007 |
| TR-03 | Secrets do data lake no workflow | Disponibilidade do lake sem o autor: o bruto chega todos os dias. | Segurança: o pior vazamento possível passa a ser a credencial de administrador da turma. | ADR-008 |
| TR-04 | Leitura das outras coleções por curinga | Extensibilidade: uma coleção nova entra na gold sem mudar código. | Comparabilidade: P3, P5 e placar dependem da disponibilidade e do histórico de terceiros (C-13). | ADR-003 |
| TR-05 | Regra literal de unidades inteiras e orçamento por item | Fidelidade à spec e reprodutibilidade | Na DRI, duas das cinco carteiras não medem o que o nome sugere (S-02). | ADR-005, ADR-006 |
| TR-06 | Reconstrução total de silver e gold a cada execução | Idempotência e simplicidade (C-06) | O tempo cresce com os dias e as coleções; o tempo por execução continua **hipótese**. | ADR-004 |

## 8. Riscos

| # | Risco | Efeito | Mitigação | Nível |
|---|---|---|---|---|
| RS-01 | Principal e reserva atrasam até depois das 20h UTC de D+1 (R-01). O máximo observado foi de 10h15min30s. | Data sem bruto, sem recuperação (DRV-01). | Reserva das 06h30 UTC; disparo manual dentro do ciclo, descrito no README; registro em "Dias sem coleta" (ADR-007). | médio |
| RS-02 | A continuidade dependeu de intervenção manual em 03/11 e 04/11 (ressalva do RNF-13). | O critério "sem intervenção manual" não vale para todo o período. | Correção do ADR-007 (T-57); de 05/11 a 15/11, todas as datas foram gravadas por execuções agendadas (`docs/evidencias/T-52_agendador.md`). | baixo |
| RS-03 | Dependência das silvers dos colegas: a 24541 ficou só com os dias mais recentes no data lake novo depois da troca de endpoint de 15/11. | P3, P5 e placar comparam períodos curtos ou diferentes, e o resultado muda conforme terceiros publicam ou apagam dados. | Leitura somente leitura, cestas fixas e base comum, janela por coleção e aviso do RF-22 sem dados (ADR-003). Na gold de 16/11, a 24541 tem 2 dias (1316 linhas, 658 por dia), e no placar a ASC aparece de 14/11 a 15/11, com aviso de período diferente (`docs/evidencias/T-53_observacoes_painel.md`). | médio |
| RS-04 | Credencial de administrador compartilhada: a Guarda de prefixo é a única proteção dos dados dos colegas (R-13). | Um erro de prefixo apagaria ou sobrescreveria dados de outra coleção. | Guarda de prefixo única com testes de recusa (C-05); agente proibido de excluir e de usar a credencial (`AGENTS.md`). | médio |
| RS-05 | Leitura errada das carteiras e do placar: selado e cesta_raras da DRI ficaram 100% em caixa (S-02). | O placar (RF-28) usa comparação estrita (`dashboard/app.py`, `placar_turma`: empate não conta). A selado da DRI vale o mesmo que a cdi (R$ 1.004,07, 0,41%) e aparece como "não" acima da cdi por empate, o que entra no "0 de 2" (`docs/evidencias/T-53_observacoes_painel.md`). O leitor pode interpretar esse "não" como desempenho ruim da selado, quando ela ficou 100% em caixa e não teve exposição a mercado. | Aviso no painel quando todas as cartas ficam com 0 unidades (commit `fcf0f80`); consequência registrada no ADR-006. | médio |
| RS-06 | Divergência registrada sobre "primeiro dia": `src/tcg/gold/perguntas.py` usa a menor `data` com `market_price` não nulo, e a spec define a menor `data` com bruto do TCGCSV. | As duas definições só divergem se o primeiro dia tiver todos os preços nulos, o que não aconteceu no período (13 datas com bruto e quarentena vazia, `docs/evidencias/T-50_clone_limpo.md`). | Registrada como pendência para a T-55 e a T-56 (`docs/prompts.md`, registro da T-39); o comentário em `carteiras.py` registra a equivalência no caso normal. | baixo |
| RS-07 | Horário real de atualização do TCGCSV não validado (S-03). | Preço do ciclo anterior gravado como `data=D`. | Principal às 20h30 UTC; comparação de `prices.json` de dias seguidos continua **pendência** (ADR-007). | baixo |
| RS-08 | Workflow agendado desativado por inatividade (R-02). | A coleta para sem aviso. | Workflow na `main`; agendamento ativo em 16/11, com a última agendada 43905874560 às 16:17 UTC (`docs/evidencias/T-52_agendador.md`); prazo de 12/12/2026. | baixo |
| RS-09 | Um terceiro altera um objeto do nosso bruto no lake. O Sincronizador recria o que falta, mas não detecta alteração. | Silver construída sobre um bruto diferente do da branch. | Branch como fonte da verdade (TR-01); conferência de hash das chaves existentes como condição de revisão do ADR-008. | baixo |

## 9. Não riscos

| # | Ponto | Por que não é risco | Evidência |
|---|---|---|---|
| NR-01 | Limite de requisições do TCGCSV | Máximo de 4 por dia contra o limite de 10.000. A segunda execução do ciclo não faz requisição. | `docs/evidencias/T-52_agendador.md`; `config/parametros.toml` |
| NR-02 | Vazamento de credenciais pelo repositório ou pelos logs | 0 ocorrências no histórico, nos arquivos e no log; secrets mascarados nos 29 logs. | `docs/evidencias/T-51_busca_credenciais.md`; `docs/evidencias/T-52_agendador.md` |
| NR-03 | Troca de servidor S3 | A troca de endpoint e de credenciais de 15/11 não exigiu mudança de código. | ADR-008 (Revisões); `docs/evidencias/T-58_troca_endpoint.txt` |
| NR-04 | Cotação posterior na conversão | ASOF JOIN testado para fim de semana e feriado. | `docs/evidencias/T-30_estrela.txt`; `docs/evidencias/T-31_fato_cambio.txt` |
| NR-05 | Escrita fora do prefixo pelo código | Toda escrita e exclusão fora de `raw/` passa pela Guarda de prefixo, com testes de recusa. | `docs/evidencias/T-23_guarda_prefixo.txt`; `docs/evidencias/T-33_reprocessar.txt` |
| NR-06 | Custo | Só serviços gratuitos. | `docs/evidencias/T-49_readme.txt` |
| NR-07 | Reprodução | Clone limpo reconstruído seguindo só o README, com 463 testes passando. | `docs/evidencias/T-50_clone_limpo.md` |
| NR-08 | Falha parcial de uma fonte | Fontes gravadas de forma independente: a falha do CDI em 08/11 foi completada pela reserva sem nova requisição ao TCGCSV. | `docs/evidencias/T-52_agendador.md`; ADR-001 |

## 10. Pendências desta avaliação

- Validar o horário real de atualização do TCGCSV (S-03, RS-07).
- Validar a janela de 10 dias e os parâmetros de repetição, que continuam como hipótese (`specs/spec.md`, Perguntas abertas).
- Encaminhar a divergência de "primeiro dia" (RS-06) no registro de pendências (T-55).

## 11. Rastreabilidade

A ligação de cada RF e RNF com tarefa, teste e commit fica em [docs/rastreabilidade.md](rastreabilidade.md), criada na T-54.
