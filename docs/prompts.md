# Registro de prompts

Histórico dos prompts usados com agentes de IA em cada etapa do projeto e do resultado da revisão humana.

| data | etapa | prompt | resultado da revisão |
|------|-------|--------|----------------------|
| 2026-11-02 | 0 – Esqueleto | texto completo em [Prompt da etapa 0 – Esqueleto](#prompt-da-etapa-0--esqueleto) | aprovado sem alterações |
| 2026-11-02 | 1 – Persona | texto completo em [Prompt da etapa 1 – Persona](#prompt-da-etapa-1--persona) | aprovado com ajustes (nome da persona, pergunta 3 sem turma, coleção = DRI inteira, lacunas revisadas, escopo de leitura de outras coleções) |

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
