# Registro de prompts

Histórico dos prompts usados com agentes de IA em cada etapa do projeto e do resultado da revisão humana.

| data | etapa | prompt | resultado da revisão |
|------|-------|--------|----------------------|
| 2026-11-02 | 0 – Esqueleto | texto completo em [Prompt da etapa 0 – Esqueleto](#prompt-da-etapa-0--esqueleto) | aprovado sem alterações |
| 2026-11-02 | 1 – Persona | texto completo em [Prompt da etapa 1 – Persona](#prompt-da-etapa-1--persona) | aprovado com ajustes (nome da persona, pergunta 3 sem turma, coleção = DRI inteira, lacunas revisadas, escopo de leitura de outras coleções) |
| 2026-11-02 | 2 – Objetivos | texto completo em [Prompt da etapa 2 – Objetivos](#prompt-da-etapa-2--objetivos) | aprovado com ajustes (OBJ-02 com decomposição em três efeitos, OBJ-05 com cinco carteiras e fórmula de liquidação, P4 das outras coleções no OBJ-04, coleções recentes = lançadas a partir de 2024, câmbio da carteira dolar como limite declarado, encaminhamento das perguntas abertas) |

## Prompt da etapa 0 – Esqueleto

```text
[C] Personagem
Você é um engenheiro de dados que prepara repositórios para Spec-Driven Development. Nesta etapa você só cria a estrutura de pastas e os arquivos de regras e configuração. Você não escreve código de coleta, não escolhe bibliotecas e não executa comandos que acessem a rede ou o MinIO.

[R] Pedido
Crie o esqueleto do projeto final da disciplina Data Collection and Storage na raiz deste repositório. O projeto é individual: um pipeline diário que coleta produtos e preços da coleção Pokémon TCG "SV10: Destined Rivals" (sigla DRI, groupId 24269) pelo TCGCSV, a PTAX e o CDI do Banco Central, grava a resposta original num MinIO local rodando no GitHub Codespaces (localhost:9000, bucket tcg), constrói silver e gold e alimenta um dashboard em Python.
Crie:
1. Pastas: docs/adr/, docs/evidencias/, specs/, src/, tests/unidade/, tests/integracao/, dashboard/ (com .gitkeep nas vazias).
2. README.md com: título, coleção escolhida (DRI, groupId 24269), resumo de uma linha do projeto, seção "Como rodar" com o texto "a definir nas próximas etapas" e seção "Dias sem coleta" com uma tabela vazia (data | motivo).
3. .gitignore cobrindo pelo menos: .env, .venv/, __pycache__/, *.pyc, .pytest_cache/, backup_raw/, dados_locais/.
4. .env.example só com nomes de variáveis e valores vazios ou fictícios: MINIO_ENDPOINT=localhost:9000, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET=tcg, MINIO_SECURE=false, GROUP_ID=24269, TCG_USER_AGENT=colecao-dri/1.0.
5. AGENTS.md com as seções: Escopo; Ambiente; Arquitetura prevista; Regras de escrita no data lake; Comandos permitidos e proibidos; Política de segredos; Ordem SDD e gates por etapa; Convenção de commits.
6. CLAUDE.md contendo apenas a linha @AGENTS.md.
7. docs/prompts.md com um cabeçalho e uma tabela vazia (data | etapa | prompt | resultado da revisão).

[E] Exemplos
Trecho bem escrito do AGENTS.md:
## Regras de escrita no data lake
- Escreva somente em prefixos com group_id=24269 (tcg/raw/*/group_id=24269/, tcg/silver/*/group_id=24269/, tcg/gold/group_id=24269/, tcg/gold_turma/carteira/group_id=24269/).
- Nenhum objeto em tcg/raw/ é sobrescrito ou apagado; antes de gravar, confira se a chave já existe.

Trecho mal escrito (não faça assim):
## Regras
- Tome cuidado com os dados.

[A] Ajustes
- A credencial do MinIO local fica só no .env. O AGENTS.md deve proibir: ler ou imprimir o .env; escrever qualquer credencial em arquivo, log, evidência ou mensagem de commit; comandos de exclusão no MinIO (mc rm, mc rb, remove_object, remove_bucket ou equivalentes); git push --force.
- Na seção "Ambiente", registre: desenvolvimento e execução local no GitHub Codespaces, com Docker e Python; MinIO local por docker compose (a criar numa tarefa futura).
- Na seção "Arquitetura prevista", descreva em até cinco linhas, marcando como "a confirmar no plan.md": coleta diária no GitHub Actions, depois das 20h UTC, gravando as respostas originais numa branch dados-raw do repositório; um comando local sincroniza esses arquivos para o MinIO local, recusando sobrescrita; silver, gold e dashboard rodam a partir do MinIO local.
- Ordem SDD obrigatória no AGENTS.md: AGENTS.md → docs/00_persona.md → docs/01_objetivos_negocio.md → specs/spec.md → specs/plan.md → specs/tasks.md → implementação (uma tarefa por vez, com teste) → validação ATAM. Nenhum código em src/ antes de specs/tasks.md existir.
- Gate de cada etapa: o artefato foi revisado por mim e commitado antes da etapa seguinte.
- Convenção de commits: tipo(T-xx): descrição [RF-yy]; nesta etapa use chore(T-00): esqueleto SDD do projeto final.
- Idioma de todos os arquivos: português do Brasil.
- Não crie docs/00_persona.md, specs/spec.md nem nenhum outro artefato além dos listados.
- Não execute git commit nem git push; apenas proponha a mensagem.

[T] Tipo de saída
Os arquivos e pastas listados, em Markdown onde couber. Antes de criar, mostre a árvore de pastas e o sumário do AGENTS.md e espere minha confirmação. Ao final, mostre a saída de git status --short.

[E] Extras
Leia antes o que já existe na raiz do repositório (provavelmente só README.md) e preserve o que fizer sentido.
Fonte de dados: TCGCSV (https://tcgcsv.com/tcgplayer/3/24269/products e /prices), pede User-Agent próprio, pausa mínima de 100 ms entre chamadas e no máximo uma coleta por dia, depois das 20h UTC.
Se faltar informação, pergunte. Pare ao final.
```

## Prompt da etapa 1 – Persona

```text
[C] Personagem
Você é um analista de requisitos de engenharia de dados. Nesta etapa você só descreve pessoas e problemas. Você não propõe tecnologia, não escreve código e não executa comandos além de ler arquivos.

[R] Pedido
Preencha docs/00_persona.md com a persona principal do projeto: um colecionador de cartas Pokémon que mora no Brasil, compra cartas avulsas e produtos selados (booster box, elite trainer box, booster bundle) da coleção Destined Rivals para guardar, e quer saber onde o dinheiro dele rende mais.
Use esta estrutura:
1. Tabela da persona com as linhas: Nome e papel; Contexto; Decisão que toma; Frequência de consulta; Como decide hoje; Dor atual; O que precisa ver para decidir; Como mede sucesso.
2. Seção "Perguntas que a persona quer responder", com as cinco perguntas listadas em Extras, na linguagem dela.
3. Tabela "Fatos, lacunas e suposições" (tipo | conteúdo | origem), com pelo menos três fatos, duas lacunas e duas suposições.

[E] Exemplos
Linha bem escrita:
| Dor atual | Compra em dólar e mede o patrimônio em reais, mas não consegue separar quanto da valorização veio da carta e quanto veio da alta do dólar; também não tem histórico de preço próprio, só o preço do dia. |
Linha mal escrita (não faça assim):
| Dor atual | Precisa de um dashboard moderno com dados em tempo real. |

[A] Ajustes
- Use somente as informações deste prompt, do AGENTS.md e dos fatos listados em Extras.
- Não invente números (orçamento, quantidade de cartas, retorno esperado, tempo). Valor ausente = "hipótese: validação pendente".
- Não cite tecnologia (MinIO, DuckDB, Streamlit, GitHub Actions, Parquet) nas linhas de dor, necessidade e sucesso; a persona fala do problema dela.
- Cada fato na tabela de fatos tem origem.
- Não crie nem altere outros arquivos.

[T] Tipo de saída
Somente docs/00_persona.md, em Markdown, com no máximo uma página e meia. Antes de editar, mostre em tópicos o que vai escrever e espere minha confirmação.

[E] Extras
Leia antes: AGENTS.md.
Fatos do contexto (origem: contexto do projeto):
- o colecionador compra no marketplace TCGplayer, em dólar, e mede o patrimônio em reais;
- o preço de referência (market price) vem de vendas recentes nos Estados Unidos; não inclui frete, taxas do marketplace, IOF nem a condição da carta;
- a fonte publica o preço do dia uma vez por dia, inclusive fins de semana; o câmbio de referência (PTAX) só existe em dia útil;
- o colecionador consulta os preços uma vez por dia;
- o histórico de preço só existe a partir do primeiro dia de coleta; um dia não coletado não pode ser recuperado depois;
- para reconhecer uma carta ele precisa ver a imagem dela e poder abrir a página do produto;
- as alternativas ao colecionismo que ele compara são deixar o dinheiro em dólar ou aplicar no CDI;
- o período observado é de algumas semanas e não sustenta previsão de preço nem recomendação de compra.
As cinco perguntas:
1. Quais cartas da minha coleção mais valorizaram e quais mais desvalorizaram desde o início da coleta?
2. Na minha coleção, o produto selado guardou valor melhor que as cartas avulsas?
3. Qual coleção da turma valorizou mais no período?
4. Onde está concentrado o valor de cada coleção?
5. Quais cartas deram mais retorno para o risco assumido?
Se faltar informação para uma linha, pergunte antes de supor. Ao terminar, liste as perguntas abertas e pare.
```

### Ajustes da revisão

#### Ajuste 1 – respostas às perguntas abertas

Arquivo alterado: `docs/00_persona.md` (criado).

```text
Respostas:
1. Pode dar um nome fictício: "Rafael, colecionador de Pokémon TCG".
2. Deixe "Como decide hoje" como hipótese: validação pendente.
3. A persona não é aluno. Ela compara a Destined Rivals com outras coleções recentes do Pokémon TCG. Reescreva a pergunta 3 como "Qual coleção recente valorizou mais no período?", sem mencionar turma.
4. "Coleção" é a coleção DRI inteira (o conjunto de cartas e selados lançados), não uma lista pessoal com quantidades e preço pago. O valor da coleção é a soma de um exemplar de cada carta. Para medir quanto o dinheiro renderia, a persona pensa numa carteira hipotética de R$ 1.000 montada no primeiro dia. Ajuste o contexto e retire essa lacuna.
5. Ajustes nas lacunas e suposições:
   - "Qual câmbio usar no fim de semana" não é lacuna: no fim de semana e em feriado vale a última cotação de dia útil anterior, nunca uma posterior. Mova para fatos.
   - "Como medir risco" e "como as coleções ficam comparáveis" são decisões de especificação, não da persona. Retire daqui.
   - Mantenha as três suposições.
   - Acrescente como lacuna: "a persona aceita que o dashboard mostre evidência do período e não recomendação de compra?".
Pode escrever o arquivo.
```

#### Ajuste 2 – respostas à segunda rodada de perguntas abertas

Arquivos alterados: `docs/00_persona.md` e `docs/prompts.md` (diff do `AGENTS.md` só proposto).

```text
Respostas:
1. Mantenha a lacuna. Não reformule a pergunta 3. Corrija o AGENTS.md: coletar ou gravar dados de outras coleções continua fora do escopo; ler dados de outras coleções produzidos por terceiros, quando estiverem disponíveis, está dentro do escopo, somente leitura. Na persona, a origem desses dados fica como lacuna: dependem de outros coletores e podem não estar disponíveis.
2. Os selados ficam fora da soma. O valor da coleção é a soma de um exemplar de cada carta avulsa. Os selados entram só na pergunta 2, comparados com as cartas.
3. A divisão da carteira fica para a especificação. Na persona, basta dizer que ela compara cartas avulsas, selados, dólar e CDI.
4. Mantenha "cada coleção", porque a pergunta 4 também vale para as outras coleções quando os dados existirem.
5. Sim. Agora registre em docs/prompts.md a etapa "1 – Persona", com a data de hoje, o texto completo do prompt que eu enviei e o resultado da revisão: "aprovado com ajustes (nome da persona, pergunta 3 sem turma, coleção = DRI inteira, lacunas revisadas, escopo de leitura de outras coleções)". Não registre o Prompt 0 de novo se ele já estiver lá.

Arquivos que você pode alterar agora: docs/00_persona.md, AGENTS.md e docs/prompts.md. Mostre o diff do AGENTS.md antes de salvar.
```

#### Ajuste 3 – aprovação do diff do AGENTS.md

Arquivo alterado: `AGENTS.md`.

```text
Aprovado com a troca para "qualquer dado coletado que não venha das fontes acima". Pode salvar o AGENTS.md.
```

#### Ajuste 4 – troca para "perguntas 3, 4 e 5"

Arquivo alterado: `docs/00_persona.md`.

```text
Na lacuna sobre a origem dos dados das outras coleções, troque "(perguntas 3 e 4)" por "(perguntas 3, 4 e 5)". Não altere mais nada.
```

## Prompt da etapa 2 – Objetivos

```text
[C] Personagem
Você é um product owner técnico de uma equipe de dados. Você traduz a dor da persona em objetivos de negócio mensuráveis, drivers e restrições. Você não escreve requisitos técnicos, não escolhe bibliotecas e não escreve código.

[R] Pedido
Preencha docs/01_objetivos_negocio.md a partir de docs/00_persona.md. Escreva exatamente estes seis objetivos, cada um com descrição, métrica de sucesso verificável e origem:
OBJ-01 série diária contínua de preços da coleção DRI, sem nenhum dia inventado;
OBJ-02 valores em reais com o efeito da carta separado do efeito do câmbio;
OBJ-03 responder às perguntas 1, 2 e 4 da persona para a coleção DRI;
OBJ-04 comparar a DRI com outras coleções recentes (perguntas 3 e 5) quando os dados delas estiverem disponíveis;
OBJ-05 comparar uma carteira hipotética de R$ 1.000 em cartas avulsas e em selados com deixar o dinheiro em dólar ou no CDI;
OBJ-06 projeto reprodutível e auditável a partir de um clone limpo do repositório, sem custo e sem segredo versionado.
Liste também: drivers de negócio (DRV-xx), restrições (RES-xx, com tipo e origem) e o que fica fora do escopo.

[E] Exemplos
| OBJ-01 | Série diária contínua de preços da coleção DRI, sem nenhum dia inventado. | Toda data entre o primeiro e o último dia de coleta tem os arquivos brutos do dia ou aparece na tabela "Dias sem coleta" do README, com o motivo; zero dias preenchidos por estimativa. | Persona: "não tem histórico de preço próprio" |
| DRV-01 | Um dia sem coleta não se recupera depois, porque a fonte só devolve o preço do dia. | Contexto do projeto |
| RES-02 | Custo zero: nenhum serviço pago | financeira | Decisão do autor |

[A] Ajustes
- Cada objetivo precisa de uma métrica verificável por um comando, um teste ou uma observação concreta. Se o valor não estiver nos fatos de Extras, escreva "hipótese: validação pendente" e diga como medir.
- Para OBJ-04, a métrica deve aceitar o resultado parcial: quando os dados de outras coleções não existirem, o painel informa a ausência em vez de mostrar dado vazio ou inventado.
- Restrições têm tipo (técnica, financeira, legal, prazo) e origem.
- Fora do escopo, inclua pelo menos: previsão de preço e recomendação de compra; coleta ou gravação de outras coleções; streaming em tempo real; preço de carta graduada (PSA, CGC); scraping de sites que bloqueiam acesso automatizado.
- Não altere docs/00_persona.md.
- Não escolha tecnologia além das que estão nas restrições.

[T] Tipo de saída
Somente docs/01_objetivos_negocio.md, em Markdown, com tabelas para objetivos, drivers, restrições e fora do escopo. Mostre o plano antes de editar e espere minha confirmação.

[E] Extras
Leia antes: AGENTS.md e docs/00_persona.md.
Fatos e restrições (origem: contexto do projeto, salvo indicação):
- Fonte de preços: TCGCSV, sem chave; pede User-Agent próprio, pausa mínima de 100 ms entre chamadas e no máximo 10.000 requisições por dia; atualiza por volta das 20h UTC; o preço muda uma vez por dia.
- Câmbio: PTAX de fechamento do Banco Central, só em dia útil; no fim de semana e em feriado vale a última PTAX de dia útil anterior, nunca uma posterior.
- CDI: série diária do Banco Central, só em dia útil.
- Filtros de relevância: na pergunta 1, só cartas acima de US$ 1 no primeiro dia; na pergunta 5, só cartas acima de US$ 5; cartas de código digital (raridade Code Card) ficam fora das perguntas 1, 3 e 4.
- Carteira: valor de liquidação diário, unidades inteiras, taxa de venda como parâmetro com 15% como hipótese declarada.
- Repositório público no GitHub; credenciais só no .env e em secrets.
- Execução: GitHub Codespaces com MinIO local; coleta diária agendada no GitHub Actions (decisão do autor; detalhes no plan.md).
- Custo zero (decisão do autor).
- Prazo de entrega: 12/12/2026, 23h59.
- O período observado é de algumas semanas e não sustenta previsão.
Se faltar informação, pergunte. Ao terminar, liste perguntas abertas e pare.
```

### Ajustes da revisão

#### Ajuste 1 – aprovação do plano com ajustes

Arquivo alterado: `docs/01_objetivos_negocio.md` (criado).

```text
Plano aprovado com estes ajustes:

OBJ-02: a variação em reais se decompõe em três partes, não duas: efeito da carta, efeito do câmbio e efeito cruzado, pela identidade (1 + r_brl) = (1 + r_usd) × (1 + r_cambio). A métrica deve dizer que um teste confere essa identidade, com tolerância de arredondamento.

OBJ-05: são cinco carteiras, todas partindo de R$ 1.000 no primeiro dia de coleta:
- selado: unidades inteiras do booster box da coleção; se ele não tiver preço no primeiro dia, o selado de maior preço que tiver preço (escolha registrada em ADR);
- cesta_raras: R$ 100 em cada uma das dez cartas de maior market price no primeiro dia, em unidades inteiras;
- propria: regra definida pelo autor, registrada em ADR antes do primeiro cálculo;
- dolar: R$ 1.000 convertidos pela PTAX de venda do primeiro dia e guardados em dólar;
- cdi: R$ 1.000 corrigidos pelo CDI de cada dia útil, com juros compostos.
A métrica deve incluir: valor de liquidação diário = unidades × market price × (1 − taxa de venda) × PTAX de compra, mais a sobra em caixa, que rende CDI; a composição usa só dados do primeiro dia, e um teste confirma que acrescentar dias posteriores não muda a composição.

Respostas às perguntas abertas:
1. Respondida acima.
2. Sim: dólar comprado pela PTAX de venda e vendido pela PTAX de compra, sem spread nem IOF. Registre como limite declarado.
3. Sim, inclua a P4 das outras coleções no OBJ-04.
4. Coleções recentes = coleções principais do Pokémon TCG lançadas a partir de 2024.

Pode escrever o arquivo.
```

#### Ajuste 2 – encaminhamento das perguntas abertas e registro da etapa

Arquivos alterados: `docs/01_objetivos_negocio.md` e `docs/prompts.md`.

```text
RES-03 pode ficar como "legal".

Na seção de perguntas abertas, registre o encaminhamento de cada uma:
1. cesta_raras: sim, excluem Code Card e selados (só cartas avulsas). O critério de desempate fica para o spec.md.
2. Sim: se o primeiro dia cair em fim de semana ou feriado, vale a PTAX de dia útil anterior, pela mesma regra do OBJ-02.
3. Fica para o plan.md.
4. Fica como hipótese até a primeira coleta.
5. Continua pendente, a validar na primeira coleta.

Depois registre em docs/prompts.md a etapa "2 – Objetivos", com o prompt original e, na subseção "Ajustes da revisão", as minhas mensagens de ajuste desta etapa (a de aprovação do plano e esta), anotando qual arquivo cada uma mudou. Não altere outros arquivos.
```
