# ADR-003: Esquema estrela na gold e leitura de outras coleções

## Status

Aceito em 2026-11-06.

## Contexto e forças

A silver da DRI (groupId 24269) tem cinco tabelas: `colecao`, `produto`, `preco_diario` (produto × acabamento × dia, em dólar), `cambio_diario` e `cdi_diario` (só dias úteis). O painel precisa responder às cinco perguntas da persona e montar as carteiras em reais, comparando a DRI com outras coleções recentes. Essas outras coleções não são coletadas por este projeto. Quando existem, estão no mesmo bucket, em silvers de terceiros com o mesmo contrato, em `silver/<tabela>/group_id=<id>/` (RES-13). A gold é a camada que junta preço, câmbio e coleção, num formato que o painel consulta todo dia sem refazer as junções.

Cada pergunta é uma agregação do fato por alguma dimensão:

| Pergunta | RF | Agregação |
|---|---|---|
| P1: cartas que mais valorizaram e desvalorizaram | RF-15 | `fato_preco_diario` no primeiro e no último dia (`dim_data`) por produto × acabamento, filtrado por `dim_produto` (carta, sem Code Card, acima de US$ 1); a decomposição usa `market_price`, `market_price_brl` e `cotacao_aplicada` guardados no fato. |
| P2: selado contra cartas Double Rare em diante | RF-16 | Média e soma do fato por `dim_data` × `dim_produto.tipo_produto` e `raridade`, na DRI. |
| P3: coleção que mais valorizou | RF-17 | Soma de `market_price_brl` por `dim_colecao` × `dim_data`; a PTAX vem de `fato_cambio_diario` pela mesma `dim_data`. |
| P4: concentração do valor | RF-18 | Soma do fato no último dia por `dim_colecao` × `dim_produto.raridade`. |
| P5: retorno contra risco | RF-19 | Retornos diários do fato por produto × acabamento, ordenados por `dim_data`, com cor por `dim_colecao`. |
| Carteiras | RF-23 a RF-26 | Composição pelo fato no primeiro dia; valor diário pelo fato e por `fato_cambio_diario` (PTAX de compra e venda, CDI do dia) por dia de calendário. O placar (RF-28) lê `gold_turma/carteira/`, fora da estrela. |

Forças em jogo:
- **Consultabilidade**: as perguntas são agregações diferentes dos mesmos preços, e o painel não deve repetir junções a cada consulta.
- **Correção da conversão** (RNF-01, RES-04): nenhum preço é convertido com cotação posterior à data dele.
- **Escrita isolada** (RES-08): escrita só em `gold/group_id=24269/`; silvers de outras coleções são só lidas.
- **Ausência tolerada** (RES-13, RF-22): sem outras coleções, a gold sai só com a DRI, sem falha.
- **Custo zero** (RES-02): nenhum serviço sempre ligado.
- **Auditabilidade** (RNF-11): cada valor em reais mostra a cotação e o boletim de onde veio.

## Requisitos e cenários relacionados

| Requisito | Cenário que esta decisão precisa atender |
|---|---|
| RF-10 | Com a silver da DRI e a de uma segunda coleção, a gold tem os fatos e as dimensões do contrato, `dim_colecao` tem as duas coleções e nada fora de `gold/group_id=24269/` é criado ou alterado. |
| RF-11 | US$ 10,00 em 10/10/2026 com PTAX de venda de 09/10 = 5,0000 resulta em `market_price_brl` = 50,00, `cotacao_aplicada` = 5,0000 e `data_ptax` = 2026-10-09. |
| RF-12 | 10/10 e 11/10 existem em `fato_cambio_diario`, com a PTAX de 09/10, `data` do boletim = 2026-10-09 e CDI = 0. |
| RNF-01 | 10/10, 11/10 e 12/10 usam a PTAX de 09/10, nunca a de 13/10. |
| RF-17, RF-18, RF-19 | P3, P4 e P5 agregam por `dim_colecao` sem código específico por coleção. |
| RF-22, RF-28 | Sem silver ou gold_turma de outras coleções, a gold e o placar saem só com a DRI e o painel mostra o aviso. |

## Alternativas consideradas

| Alternativa | Por que foi descartada |
|---|---|
| Tabela única larga | Repete nome, raridade, tipo, imagem, link e atributos da coleção em cada linha de cada dia; uma correção num atributo de produto teria de ser aplicada em todas as linhas. |
| Snowflake (raridade, tipo de produto e coleção em tabelas próprias ligadas a `dim_produto`) | Normaliza mais sem ganho para as perguntas: todas filtram por atributos que cabem numa só dimensão, e cada pergunta ganharia junções a mais. |
| Servidor analítico (ClickHouse ou Postgres) | Exige um serviço sempre ligado, contra o custo zero (RES-02), e mais um componente para subir, proteger e reproduzir. |
| Views sem materialização | O painel recalcularia o ASOF JOIN e a leitura de todas as silvers a cada consulta, e o resultado mudaria com a silver no meio de uma sessão. |
| Copiar as silvers de outras coleções para o nosso prefixo | Grava dados de outros groupIds no prefixo da DRI, contra a regra de escrita só em `group_id=24269` (RES-08), e cria uma cópia que fica desatualizada. |
| Lista fixa de group_ids em configuração | Precisa de manutenção a cada coleção nova, e um group_id listado sem silver vira falha em vez de ausência tolerada. |

## Decisão e táticas

A gold é um **esquema estrela materializado em Parquet** e calculado em SQL no DuckDB, gravado só em `gold/group_id=24269/`:

- `fato_preco_diario`, com grão produto × acabamento × dia (`data`, `product_id`, `group_id`, `acabamento`): `market_price`, `low_price`, `mid_price`, `high_price`, `market_price_brl`, `cotacao_aplicada` (a cotação de venda usada na conversão) e a `data_ptax` do boletim usado, mais a `chave_raw` de origem.
- `fato_cambio_diario`, com um dia de calendário por linha: PTAX de compra e de venda aplicadas, `data` do boletim e CDI do dia (0 em fim de semana e feriado).
- `dim_produto`, `dim_colecao`, `dim_data` (calendário do período) e `dim_acabamento`.

Decisões de modelagem:
- A conversão usa ASOF JOIN da `data` do preço com a `cambio_diario` da DRI, pegando o último boletim com data menor ou igual à do preço, nunca um posterior (RNF-01). O fato guarda `market_price_brl` = `market_price` × `cotacao_aplicada` e a `data_ptax`.
- Os dias desde o lançamento são calculados na consulta, a partir de `dim_data` e de `dim_colecao.data_lancamento`, sem coluna guardada.
- `preco_diario`, `produto` e `colecao` são lidas de todas as coleções por curinga (`silver/<tabela>/group_id=*/...`) com `union_by_name`. Câmbio e CDI vêm só da silver da DRI.
- A leitura usa `hive_partitioning = false`. Como `group_id` já é coluna do contrato, a coluna derivada do caminho seria duplicada e poderia entrar em conflito (nota da T-24).
- Antes da união, as colunas e os tipos de cada coleção são conferidos. Uma silver fora do contrato é ignorada com aviso no log (group_id e motivo), e as demais seguem.

| Tática | Atributo de qualidade | Como aparece |
|---|---|---|
| Modelo dimensional | Consultabilidade, modificabilidade | Cada pergunta é uma agregação do fato por uma dimensão; um atributo novo de produto muda só `dim_produto`. |
| Leitura por curinga | Extensibilidade | Uma coleção nova no bucket entra na gold sem mudança de código nem de configuração. |
| Isolamento de falhas por coleção | Disponibilidade | Uma silver de terceiro fora do contrato é descartada sozinha, e a gold da DRI continua sendo gerada. |
| Fato com a cotação aplicada e a data do boletim | Auditabilidade, correção | Cada `market_price_brl` mostra `cotacao_aplicada` e `data_ptax`, e o teste confere que nenhum boletim é posterior. |
| Materialização em Parquet | Desempenho do painel | O ASOF JOIN e a união das coleções rodam uma vez por `make gold`, não a cada consulta. |
| Escrita só pela Guarda de prefixo | Integridade | Toda gravação passa pela Guarda (ADR-004), que aceita só `gold/group_id=24269/`. |

## Consequências positivas

- As cinco perguntas e as carteiras saem das mesmas seis tabelas, com junções simples e previsíveis.
- Outras coleções entram e saem da análise só pela presença no bucket.
- A conversão em reais pode ser auditada linha a linha, sem refazer o cálculo.
- Sem servidor: DuckDB embutido e Parquet no MinIO local.

## Consequências negativas

- A gold depende de outras silvers seguirem o contrato. Uma coleção com nome ou tipo de coluna diferente fica de fora, e o único sinal é o aviso no log.
- A gold é refeita inteira a cada execução, e o tempo cresce com o número de dias e de coleções. Tempo por execução: hipótese: validação pendente.
- As perguntas 3 e 5 ficam parciais enquanto não houver outras coleções: o painel mostra só a DRI, com o aviso do RF-22. A P4 também perde a comparação entre coleções.
- Todas as coleções são convertidas pela PTAX da DRI. Isso é correto para o câmbio, mas acopla as outras coleções à cobertura de dias da nossa silver.
- `dim_data` cobre o calendário do período e, por isso, tem dias sem linha no fato. As consultas precisam tratar a lacuna (RF-21) e não podem preenchê-la.

## Riscos

| Risco | Mitigação |
|---|---|
| Silver de terceiro com colunas ou tipos diferentes do contrato | Conferência por coleção antes da união; a coleção é ignorada com aviso; teste com uma silver fora do contrato. |
| Ativar o particionamento Hive por engano e duplicar `group_id` | `hive_partitioning = false` explícito em toda leitura da silver; teste com duas coleções. |
| ASOF JOIN pegar cotação posterior | Condição `data_ptax <= data` no SQL; teste com 10/10, 11/10 e 12/10 contra PTAX de 09/10 e 13/10 (T-30). |
| `product_id` repetido entre coleções | O grão do fato inclui `group_id`; teste sem chave de grão duplicada (T-33). |
| Silver de terceiro alterada durante `make gold` | Leitura única por execução; a próxima execução corrige; nenhum objeto de terceiro é escrito. |

## Evidência necessária

- Teste do esquema estrela com Parquets locais: US$ 10 em 10/10 com PTAX de 5,0000 de 09/10 dá R$ 50,00, `cotacao_aplicada` = 5,0000 e `data_ptax` = 2026-10-09; 10/10 a 12/10 nunca usam a PTAX de 13/10; `dim_colecao` tem as duas coleções (T-30).
- Teste do `fato_cambio_diario` com fim de semana: PTAX de 09/10 e CDI = 0 em 10/10 e 11/10 (T-31).
- Teste do construtor contra MinIO descartável: gold só em `gold/group_id=24269/`, objetos da segunda coleção com o mesmo hash, silver fora do contrato ignorada com aviso, cenário sem outras coleções gerando só a DRI (T-32).
- Tempo de `make gold` com o bruto acumulado, para substituir a hipótese acima.

## Condição de revisão

- Se o tempo de `make gold` ficar inviável para o uso diário, avaliar construção incremental do fato.
- Se o contrato comum da silver mudar, ou se outras coleções passarem a publicar uma gold própria para leitura.
- Se uma pergunta nova exigir um grão diferente de produto × acabamento × dia.
