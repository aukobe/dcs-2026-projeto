# Objetivos de negócio

Documento derivado de `docs/00_persona.md`. Traduz a dor de Rafael, colecionador da coleção Destined Rivals (DRI, groupId 24269), em objetivos mensuráveis, drivers, restrições e limites de escopo. Não contém requisitos técnicos nem escolhas de implementação, que ficam para `specs/spec.md` e `specs/plan.md`.

## Objetivos

| ID | Descrição | Métrica de sucesso | Origem |
|---|---|---|---|
| OBJ-01 | Série diária contínua de preços da coleção DRI, sem nenhum dia inventado. | Toda data entre o primeiro e o último dia de coleta tem os arquivos brutos do dia ou aparece na tabela "Dias sem coleta" do README, com o motivo; zero dias preenchidos por estimativa. Verificação: uma checagem que compara o calendário do período com os arquivos brutos e com a tabela do README e não aponta nenhuma data sem uma das duas coisas. | Persona: "não tem histórico de preço próprio" |
| OBJ-02 | Valores em reais com o efeito da carta separado do efeito do câmbio. | Para cada carta e cada selado, a variação em reais desde o primeiro dia aparece decomposta em três partes: efeito da carta (variação em dólar), efeito do câmbio (variação da PTAX) e efeito cruzado, pela identidade (1 + r_brl) = (1 + r_usd) × (1 + r_cambio). Um teste confere essa identidade com tolerância de arredondamento. Outro teste confere que, em fim de semana e feriado, vale a PTAX do último dia útil anterior, nunca a de um dia posterior. | Persona: "não consegue separar quanto da valorização veio da carta e quanto veio da alta do dólar" |
| OBJ-03 | Responder às perguntas 1, 2 e 4 da persona para a coleção DRI. | Por observação no painel, com a data de corte visível: (P1) ranking das cartas que mais valorizaram e mais desvalorizaram em reais desde o primeiro dia, só com cartas acima de US$ 1 no primeiro dia e sem raridade Code Card; (P2) comparação da variação dos selados com a das cartas avulsas; (P4) concentração do valor da coleção (soma de um exemplar de cada carta avulsa, sem Code Card). Cada carta mostra a imagem e o link para a página do produto. O painel exibe o aviso de que o período é curto e não serve como previsão. | Persona: perguntas 1, 2 e 4; "O que precisa ver para decidir" |
| OBJ-04 | Comparar a DRI com outras coleções recentes (perguntas 3, 4 e 5) quando os dados delas estiverem disponíveis. | Resultado parcial aceito. Com dados de terceiros disponíveis: o painel responde à P3 (valorização por coleção, sem Code Card), à P4 para cada coleção (concentração de valor, sem Code Card) e à P5 (retorno em relação à oscilação, só cartas acima de US$ 5). Sem esses dados: o painel informa explicitamente a ausência, sem gráfico vazio nem valor inventado. Um teste executa os dois cenários, com e sem dados de outras coleções. "Coleções recentes" são as coleções principais do Pokémon TCG lançadas a partir de 2024. | Persona: perguntas 3, 4 e 5; AGENTS.md (escopo: leitura de outras coleções) |
| OBJ-05 | Comparar uma carteira hipotética de R$ 1.000 em cartas avulsas e em selados com deixar o dinheiro em dólar ou no CDI. | Cinco carteiras, todas partindo de R$ 1.000 no primeiro dia de coleta, cada uma com série diária de valor: **selado** (unidades inteiras do booster box da coleção; se ele não tiver preço no primeiro dia, o selado de maior preço que tiver, com a escolha registrada em ADR); **cesta_raras** (R$ 100 em cada uma das dez cartas de maior market price no primeiro dia, em unidades inteiras); **propria** (regra definida pelo autor e registrada em ADR antes do primeiro cálculo); **dolar** (R$ 1.000 convertidos pela PTAX de venda do primeiro dia e guardados em dólar); **cdi** (R$ 1.000 corrigidos pelo CDI de cada dia útil, com juros compostos). Valor de liquidação diário das carteiras de cartas e selados = unidades × market price × (1 − taxa de venda) × PTAX de compra, mais a sobra em caixa, que rende CDI. A taxa de venda é um parâmetro, com 15% como hipótese declarada. A composição usa só dados do primeiro dia; um teste confirma que acrescentar dias posteriores não muda a composição. | Persona: "imagina uma carteira hipotética de R$ 1.000 montada no primeiro dia e compara cartas avulsas, selados, dólar e CDI" |
| OBJ-06 | Projeto reprodutível e auditável a partir de um clone limpo do repositório, sem custo e sem segredo versionado. | A partir de um clone limpo, com o `.env` preenchido a partir do `.env.example`, os passos descritos no README reconstroem silver, gold e painel a partir da raw, e os testes passam. Uma busca por credenciais no histórico do repositório não encontra nenhuma. Custo total: R$ 0. Comandos exatos de verificação: hipótese: validação pendente; serão definidos no `specs/plan.md`. | Decisão do autor; AGENTS.md (política de segredos) |

## Drivers de negócio

| ID | Driver | Origem |
|---|---|---|
| DRV-01 | Um dia sem coleta não se recupera depois, porque a fonte só devolve o preço do dia. | Contexto do projeto |
| DRV-02 | A persona compra em dólar e mede o patrimônio em reais; sem separar câmbio e carta, a valorização percebida é enganosa. | Persona: "Dor atual" |
| DRV-03 | O preço muda uma vez por dia e a persona consulta o painel diariamente, inclusive em fins de semana. | Persona: "Frequência de consulta"; contexto do projeto |
| DRV-04 | A decisão da persona é de alocação: colecionar só faz sentido se render mais que deixar em dólar ou no CDI. | Persona: "Decisão que toma" |
| DRV-05 | Para reconhecer uma carta, a persona precisa ver a imagem e abrir a página do produto. | Persona: "Fatos" |
| DRV-06 | O projeto é avaliado na disciplina, então cada número precisa ser rastreável até a resposta original da fonte. | Contexto do projeto |

## Restrições

| ID | Restrição | Tipo | Origem |
|---|---|---|---|
| RES-01 | Dados coletados só do TCGCSV (groupId 24269) e do Banco Central do Brasil (PTAX e CDI). | técnica | AGENTS.md |
| RES-02 | Custo zero: nenhum serviço pago. | financeira | Decisão do autor |
| RES-03 | TCGCSV: User-Agent próprio, pausa mínima de 100 ms entre chamadas, no máximo 10.000 requisições por dia e no máximo uma coleta por dia, sempre depois das 20h UTC (a fonte atualiza por volta desse horário). | legal | Contexto do projeto |
| RES-04 | PTAX de fechamento só existe em dia útil; em fim de semana e feriado vale a última PTAX de dia útil anterior, nunca uma posterior. | técnica | Contexto do projeto; decisão do autor |
| RES-05 | CDI é série diária publicada só em dia útil. | técnica | Contexto do projeto |
| RES-06 | Repositório público no GitHub; credenciais só no `.env` (fora do versionamento) e em secrets. | legal | Contexto do projeto; AGENTS.md |
| RES-07 | Execução no GitHub Codespaces com MinIO local; coleta diária agendada no GitHub Actions (detalhes no `specs/plan.md`). | técnica | Decisão do autor |
| RES-08 | Camada raw imutável (nenhum objeto sobrescrito ou apagado) e escrita só em prefixos com `group_id=24269`. | técnica | AGENTS.md |
| RES-09 | Prazo de entrega: 12/12/2026, 23h59. | prazo | Contexto do projeto |
| RES-10 | O período observado é de algumas semanas e não sustenta previsão. | técnica | Contexto do projeto |
| RES-11 | Limite declarado: o market price não inclui frete, taxas do marketplace, IOF nem condição da carta. | técnica | Persona: "Fatos" |
| RES-12 | Limite declarado: na carteira dolar, o dólar é comprado pela PTAX de venda e vendido pela PTAX de compra, sem spread bancário nem IOF. | técnica | Decisão do autor |
| RES-13 | Dados de outras coleções são só lidos, quando produzidos por terceiros; a ausência deles não é falha do pipeline. | técnica | AGENTS.md (escopo) |

## Fora do escopo

| Item | Motivo |
|---|---|
| Previsão de preço e recomendação de compra | O período de algumas semanas não sustenta previsão (RES-10); o painel mostra evidência do período. |
| Coleta ou gravação de dados de outras coleções ou groupIds | AGENTS.md: o projeto só coleta a DRI; outras coleções são apenas lidas (RES-13). |
| Streaming ou atualização em tempo real | A fonte muda o preço uma vez por dia (DRV-03). |
| Preço de carta graduada (PSA, CGC etc.) | A fonte acompanhada traz o market price de cartas não graduadas. |
| Scraping de sites que bloqueiam acesso automatizado | Restrição legal e de escopo das fontes (RES-01, RES-03). |
| Custos reais de importação (frete, IOF, taxas do comprador, spread bancário) | Limites declarados (RES-11, RES-12). |
| Outras moedas ou investimentos além de dólar e CDI | A persona compara só essas alternativas (DRV-04). |
| Preencher lacunas por interpolação, cópia ou estimativa | Dia sem coleta vai para a tabela "Dias sem coleta" do README (OBJ-01). |

## Perguntas abertas

| # | Pergunta | Encaminhamento |
|---|---|---|
| 1 | cesta_raras: a seleção das dez cartas de maior market price exclui a raridade Code Card e os selados? Como se desempata o décimo lugar quando duas cartas têm o mesmo preço? | Sim: exclui Code Card e selados (só cartas avulsas). O critério de desempate fica para o `specs/spec.md`. |
| 2 | Primeiro dia: se o primeiro dia de coleta cair em fim de semana ou feriado, a PTAX de venda usada na montagem é a do dia útil anterior? | Sim: vale a PTAX de dia útil anterior, pela mesma regra do OBJ-02. |
| 3 | Fonte das outras coleções: onde e em que formato os dados de terceiros estarão disponíveis para leitura (OBJ-04)? | Fica para o `specs/plan.md`. |
| 4 | Imagem e link do produto (OBJ-03): a fonte traz esses campos para todas as cartas e selados? | Fica como hipótese: validação pendente até a primeira coleta. |
| 5 | Selados com preço próprio: a fonte traz os selados com preço? Isso condiciona a P2 e a carteira selado. | Continua pendente, a validar na primeira coleta. |
