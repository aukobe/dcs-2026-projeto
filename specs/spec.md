# Especificação

Requisitos derivados de `docs/00_persona.md` e `docs/01_objetivos_negocio.md`. Cada requisito cita a origem (OBJ, DRV ou RES). Escolhas de implementação ficam para `specs/plan.md`.

## Definições e decisões

- **Item**: par produto × acabamento (`product_id`, `acabamento`). É o grão de todo o projeto. Uma carta em Holofoil e a mesma carta em Reverse Holofoil são itens distintos, inclusive na cesta_raras, na P5 e no "um exemplar de cada carta" da P3 e da P4.
- **Primeiro dia**: menor `data` com bruto do TCGCSV da coleção. **Último dia**: maior `data` com esse bruto.
- **Data da coleta**: data UTC do momento da coleta.
- **PTAX aplicada no dia D**: a cotação de boletim `Fechamento` com a maior `data` ≤ D. Nunca uma de data posterior.
- **tipo_produto** (hipótese: validação pendente na primeira coleta): produto sem número de carta é `selado`; os demais são `carta`. Exceção: raridade "Code Card" é sempre `carta`.
- **Raridades "Double Rare em diante"** (hipótese: validação pendente na primeira coleta), em ordem: Double Rare, Ultra Rare, Illustration Rare, Special Illustration Rare, Hyper Rare. Uma raridade que a fonte trouxer fora da lista entra como pendência na primeira coleta.
- **Limites declarados**: as carteiras de cartas e selados compram pela PTAX de venda, sem taxa na compra; a carteira dolar compra pela PTAX de venda e vende pela PTAX de compra, sem spread nem IOF (RES-12).

## Grão de cada pergunta

| Pergunta | Grão | Período |
|---|---|---|
| P1 | item (carta), com preço no primeiro e no último dia | primeiro → último dia |
| P2 | dia × grupo (selados; cartas Double Rare em diante) | todos os dias com preço |
| P3 | dia × coleção | todos os dias com preço |
| P4 | raridade × coleção | último dia |
| P5 | item (carta) | primeiro → último dia |
| Carteiras | dia de calendário × carteira | primeiro → último dia |

## Contratos

Os nomes e tipos de colunas abaixo são obrigatórios. Colunas extras são permitidas; mudar o nome ou o tipo de uma coluna, não.

**Bruto** (bucket `tcg`):
- `raw/tcgplayer/group_id=24269/data=AAAA-MM-DD/products.json`
- `raw/tcgplayer/group_id=24269/data=AAAA-MM-DD/prices.json`
- `raw/bcb_ptax/group_id=24269/data=AAAA-MM-DD/cotacao.json`
- `raw/bcb_cdi/group_id=24269/data=AAAA-MM-DD/cdi.json`

**Silver**:

| Tabela | Colunas | Caminho |
|---|---|---|
| colecao | group_id INTEGER, nome VARCHAR, sigla VARCHAR, data_lancamento DATE, responsavel VARCHAR | `silver/colecao/group_id=24269/colecao.parquet` |
| produto | product_id INTEGER, group_id INTEGER, nome VARCHAR, tipo_produto VARCHAR ('carta' ou 'selado'), raridade VARCHAR, numero VARCHAR, image_url VARCHAR, url VARCHAR | `silver/produto/group_id=24269/produto.parquet` |
| preco_diario (produto, acabamento, dia) | data DATE, product_id INTEGER, group_id INTEGER, acabamento VARCHAR, market_price DOUBLE, low_price DOUBLE, mid_price DOUBLE, high_price DOUBLE, moeda VARCHAR, fonte VARCHAR, chave_raw VARCHAR | `silver/preco_diario/group_id=24269/data=AAAA-MM-DD/preco.parquet` |
| cambio_diario (dia útil) | data DATE, cotacao_compra DOUBLE, cotacao_venda DOUBLE, data_hora_cotacao TIMESTAMP, boletim VARCHAR ('Fechamento'), chave_raw VARCHAR | `silver/cambio_diario/group_id=24269/cambio.parquet` |
| cdi_diario (dia útil) | data DATE, taxa_dia DOUBLE (% ao dia, como publicada), chave_raw VARCHAR | `silver/cdi_diario/group_id=24269/cdi.parquet` |

**Gold** (`gold/group_id=24269/`):
- Fatos: `fato_preco_diario` (item × dia: market, low, mid, high, market_price_brl, cotação aplicada, data_ptax) e `fato_cambio_diario` (dia de calendário, RF-12).
- Dimensões: `dim_produto`, `dim_colecao`, `dim_data`, `dim_acabamento`. Dias desde o lançamento são calculados na consulta.

**gold_turma**: `gold_turma/carteira/group_id=24269/carteira.parquet` com data DATE, group_id INTEGER, carteira VARCHAR (selado, cesta_raras, propria, dolar, cdi), valor_brl DOUBLE, retorno_acumulado DOUBLE, taxa_venda DOUBLE.

## Requisitos funcionais

### RF-01: coleta diária de TCGCSV, PTAX e CDI
Uma vez por dia, depois das 20h UTC, a coleta busca `products` e `prices` do groupId 24269 no TCGCSV e uma janela recente da PTAX e do CDI. A janela existe porque o CDI de um dia útil só é publicado na manhã seguinte e para que um dia útil não coletado não fique sem PTAX. Tamanho da janela: 10 dias corridos para os dois, parâmetro configurável (hipótese: validação pendente). As quatro respostas são gravadas inteiras.
- Origem: OBJ-01, DRV-01, DRV-03, RES-01, RES-03, RES-05
- Critério de aceite:
  - Dado um dia sem bruto gravado e o relógio depois das 20h UTC
  - Quando a coleta for executada
  - Então existem as quatro chaves do dia no bruto, e `cotacao.json` e `cdi.json` correspondem à consulta dos 10 dias corridos até a data da coleta

### RF-02: grava a resposta do dia no bruto sem sobrescrever
A resposta original de cada fonte é gravada sem alteração na chave do dia da coleção.
- Origem: OBJ-01, RES-08
- Critério de aceite:
  - Dado que a chave `tcg/raw/tcgplayer/group_id=24269/data=2026-11-02/prices.json` já existe
  - Quando a gravação do mesmo dia for executada de novo
  - Então a gravação é recusada, o objeto original continua igual (mesmo hash) e a recusa aparece no log
  - E, dado um corpo HTTP gravado, o hash do objeto no bruto é igual ao hash desse corpo

### RF-03: User-Agent, pausa e repetição com espera crescente
Falhas transitórias são repetidas com espera crescente. Tentativas e esperas são parâmetros configuráveis (hipótese: validação pendente), com valores iniciais de 3 tentativas e espera de 2, 4 e 8 segundos.
- Origem: RES-03
- Critério de aceite:
  - Dado um servidor simulado que registra as requisições e falha com 503 nas duas primeiras
  - Quando a coleta do TCGCSV for executada
  - Então toda requisição leva o User-Agent de `TCG_USER_AGENT`, o intervalo entre chamadas é de pelo menos 100 ms, as esperas entre tentativas crescem (2, 4 s) e a terceira tentativa grava o bruto
  - E, se todas as tentativas falharem, nada é gravado e o erro aparece no log

### RF-04: recusa coleta fora da janela permitida
- Origem: RES-03
- Critério de aceite:
  - Dado o relógio às 19h59 UTC, ou um bruto do TCGCSV já gravado no dia
  - Quando a coleta for executada
  - Então nenhuma requisição é enviada ao TCGCSV e o motivo aparece no log

### RF-05: sincroniza o bruto para o MinIO local sem sobrescrever
Um comando local copia os arquivos da branch `dados-raw` para o MinIO local.
- Origem: OBJ-06, RES-07, RES-08
- Critério de aceite:
  - Dado um arquivo que já existe no MinIO com a mesma chave
  - Quando a sincronização for executada
  - Então o objeto não é regravado, o hash continua igual e a recusa aparece no log; os arquivos novos são copiados com o hash do arquivo de origem

### RF-06: constrói a silver no contrato comum
- Origem: OBJ-01, OBJ-02, RES-08
- Critério de aceite:
  - Dado o bruto de três dias
  - Quando a silver for construída
  - Então existem as cinco tabelas nos caminhos do contrato, com os nomes e tipos de coluna do contrato, e cada linha de preço, câmbio e CDI traz a `chave_raw` de origem
  - E a tabela `colecao` vem de um arquivo de configuração versionado, declarado pelo autor: nome "SV10: Destined Rivals", sigla "DRI", data_lancamento 2025-05-30, responsavel "Augusto"

### RF-07: valida por modelo e põe em quarentena com motivo
Cada tabela tem um modelo de validação. Linhas inválidas vão para `silver/quarentena/group_id=24269/`, com o motivo e a `chave_raw`. Boletins da PTAX diferentes de `Fechamento` não são inválidos: são descartados por regra e não vão para a quarentena. A contagem de linhas em quarentena por tabela aparece no log de cada execução.
- Origem: OBJ-01, DRV-06
- Critério de aceite:
  - Dado um bruto com uma linha de preço sem `productId`, uma PTAX de boletim `Fechamento` com `cotacao_venda` ausente e uma PTAX de boletim intermediário
  - Quando a silver for construída
  - Então as duas primeiras linhas estão na quarentena, cada uma com o seu motivo, e não aparecem nas tabelas da silver; o boletim intermediário não aparece nem na silver nem na quarentena
  - E o log da execução mostra a contagem de linhas em quarentena por tabela (preco_diario: 1, cambio_diario: 1, demais: 0)
  - E, dado uma PTAX ou um CDI de mesma data com valores diferentes em dois brutos, essa data vai para a quarentena com o motivo "valor divergente entre brutos"; valores iguais geram uma única linha

### RF-08: preço ausente é nulo
- Origem: OBJ-01
- Critério de aceite:
  - Dado um item com `marketPrice` ausente ou nulo na resposta
  - Quando a silver for construída
  - Então `market_price` é nulo, a linha existe, e nenhum valor de outro dia é copiado

### RF-09: classifica o tipo de produto
- Origem: OBJ-03, OBJ-05
- Critério de aceite:
  - Dado um produto sem número, uma carta com número e um produto de raridade "Code Card" sem número
  - Quando a silver for construída
  - Então os tipos são, respectivamente, `selado`, `carta` e `carta`

### RF-10: gold em esquema estrela sobre todas as coleções disponíveis
A gold é construída sobre a silver da DRI e as silvers de outras coleções disponíveis no bucket, lidas somente para leitura. A escrita acontece só em `gold/group_id=24269/`.
- Origem: OBJ-03, OBJ-04, RES-08, RES-13
- Critério de aceite:
  - Dado a silver da DRI e a silver de uma segunda coleção
  - Quando a gold for construída
  - Então os fatos e dimensões do contrato existem, `dim_colecao` tem as duas coleções e nenhum objeto fora de `gold/group_id=24269/` é criado ou alterado

### RF-11: converte para reais pela PTAX aplicada
`market_price_brl` = `market_price` × PTAX aplicada no dia (cotação de venda). O fato guarda a cotação usada e a `data_ptax`.
- Origem: OBJ-02, RES-04
- Critério de aceite:
  - Dado um preço de US$ 10,00 em 10/10/2026 (sábado) e a PTAX de venda de 09/10 igual a 5,0000
  - Quando a gold for construída
  - Então `market_price_brl` = 50,00, a cotação aplicada é 5,0000 e `data_ptax` = 2026-10-09

### RF-12: fato de câmbio por dia de calendário
- Origem: OBJ-02, OBJ-05, RES-04, RES-05
- Critério de aceite:
  - Dado a PTAX e o CDI de sexta-feira, 09/10/2026
  - Quando a gold for construída
  - Então os dias 10/10 e 11/10 existem, com a PTAX de 09/10, `data` do boletim = 2026-10-09 e CDI do dia = 0

### RF-13: reprocessamento com um único comando
- Origem: OBJ-06, DRV-06
- Critério de aceite:
  - Dado silver e gold já construídas
  - Quando o comando de reprocessamento for executado duas vezes
  - Então silver e gold são reconstruídas a partir do bruto, a contagem de linhas é igual à de uma única execução e não há chave de grão duplicada

### RF-14: reais por padrão, opção em dólar e filtro de preço mínimo
- Origem: OBJ-02, OBJ-03, DRV-02
- Critério de aceite:
  - Dado o painel aberto
  - Quando o usuário escolher "dólar" e preço mínimo de US$ 5
  - Então os valores aparecem em dólar e somem os itens com market_price abaixo de US$ 5 no primeiro dia; sem escolha, os valores estão em reais e o filtro tem o padrão da pergunta (US$ 1 na P1, US$ 5 na P5)

### RF-15: P1, rankings de alta e queda com decomposição
Variação % em reais entre o primeiro e o último dia, por item, decomposta em carta (r_usd), câmbio (r_cambio) e cruzado (r_usd × r_cambio). Só cartas acima de US$ 1 no primeiro dia, sem Code Card.
- Origem: OBJ-02, OBJ-03
- Critério de aceite:
  - Dado itens com preço no primeiro e no último dia, um deles Code Card e outro de US$ 0,90 no primeiro dia
  - Quando a P1 for calculada
  - Então há dois rankings de até dez itens, cada um com imagem e preço inicial e atual em reais; o Code Card e o item de US$ 0,90 não aparecem; carta + câmbio + cruzado = r_brl

### RF-16: P2, selados contra cartas Double Rare em diante
Índice base 100 no primeiro dia: média do preço dos selados contra a soma do preço das cartas das raridades da lista "Double Rare em diante"; gráfico de linhas.
- Origem: OBJ-03
- Critério de aceite:
  - Dado preços de três dias para selados e cartas
  - Quando a P2 for calculada
  - Então as duas séries valem 100 no primeiro dia, e uma carta de raridade Rare não entra na soma

### RF-17: P3, valor da coleção em índice base 100
Valor da coleção no dia em reais (soma do `market_price_brl` de um exemplar de cada item de carta, sem Code Card), em índice base 100 por coleção, com a PTAX em índice base 100 no mesmo gráfico e a DRI destacada. A data base é o primeiro dia comum a todas as coleções exibidas.
- Origem: OBJ-04, DRV-02
- Critério de aceite:
  - Dado a gold com a DRI a partir de 01/11 e outra coleção a partir de 03/11
  - Quando a P3 for calculada
  - Então há uma série por coleção mais a série da PTAX, todas com 100 em 03/11, e a série da DRI tem destaque visual

### RF-18: P4, concentração do valor
No último dia, participação de cada raridade no valor total e número de itens que somam 80% do valor; barras empilhadas a 100% por coleção, sem Code Card.
- Origem: OBJ-03, OBJ-04
- Critério de aceite:
  - Dado cinco itens de R$ 50, 20, 15, 10 e 5
  - Quando a P4 for calculada
  - Então o número de itens que somam 80% é 3, e as participações por raridade somam 100%

### RF-19: P5, retorno contra volatilidade
Retorno no período contra o desvio-padrão dos retornos diários, só cartas acima de US$ 5; dispersão com cor por coleção e imagem ao passar o cursor. Só contam retornos entre dias consecutivos com preço; os que atravessam uma lacuna são descartados.
- Origem: OBJ-04
- Critério de aceite:
  - Dado um item com preços 10, 11 e 9,9 em três dias consecutivos
  - Quando a P5 for calculada
  - Então o retorno é −1% e a volatilidade é o desvio-padrão de (+10%, −10%)
  - E, dado preços em 01/11, 02/11 e 04/11 (03/11 sem coleta), só o retorno 01/11 → 02/11 entra na volatilidade

### RF-20: imagem e link do produto
- Origem: OBJ-03, DRV-05
- Critério de aceite:
  - Dado uma carta citada em P1 ou P5
  - Quando ela for exibida
  - Então aparecem a imagem de `image_url` e o link de `url`; se o campo vier nulo, aparece o aviso "imagem indisponível" ou "link indisponível"

### RF-21: lacunas visíveis e aviso de período
- Origem: OBJ-01, RES-10
- Critério de aceite:
  - Dado um dia sem coleta no meio do período
  - Quando os gráficos de série forem exibidos
  - Então a linha é interrompida nesse dia, sem ponto interpolado, e o painel exibe o aviso de que o período é curto e não sustenta previsão

### RF-22: ausência de outras coleções informada
- Origem: OBJ-04, RES-13
- Critério de aceite:
  - Dado um bucket sem silver de outras coleções
  - Quando P3, P4 e P5 forem exibidas
  - Então cada uma mostra o aviso explícito de que faltam dados de outras coleções e exibe só a DRI, sem gráfico vazio e sem valor inventado

### RF-23: monta as cinco carteiras com dados do primeiro dia
Custo de compra = unidades × market_price × PTAX de venda aplicada no primeiro dia, sem taxa na compra (limite declarado). Unidades inteiras; o que sobra fica em caixa.
- **selado**: booster box da coleção, identificado pelo nome contendo "Booster Box" e não "Case" (hipótese: validação pendente na primeira coleta); se ele não tiver preço, o selado de maior preço com preço (escolha em ADR).
- **cesta_raras**: R$ 100 em cada um dos dez itens de carta (sem Code Card e sem selados) de maior market_price; desempate pelo menor `product_id`, e depois por `acabamento` em ordem alfabética.
- **propria**: regra do autor em ADR; sem ADR, a carteira não é calculada e o painel mostra "regra pendente".
- **dolar**: R$ 1.000 ÷ PTAX de venda aplicada no primeiro dia.
- **cdi**: R$ 1.000.
- Origem: OBJ-05
- Critério de aceite:
  - Dado o bruto do primeiro dia, com dois itens empatados na décima posição
  - Quando a composição for calculada com o primeiro dia e, de novo, com dez dias a mais
  - Então as duas composições são idênticas e entra o item de menor `product_id`

### RF-24: valor de liquidação diário
Valor diário de selado, cesta_raras e propria = Σ unidades × market_price × (1 − taxa_venda) × PTAX de compra aplicada + caixa. A taxa_venda é um parâmetro, com 15% como hipótese declarada. A carteira dolar vale USD × PTAX de compra aplicada; a carteira cdi e o caixa rendem (1 + taxa_dia/100) em cada dia útil e não rendem em fim de semana nem feriado. Item sem preço no dia usa o último preço observado só nesta avaliação, com marcação no painel, sem gravar na silver.
- Origem: OBJ-05, RES-12
- Critério de aceite:
  - Dado 1 unidade de US$ 100, PTAX de compra 5,00, taxa 15% e caixa de R$ 10
  - Quando o valor for calculado
  - Então valor_brl = 435,00
  - E, dado um item sem preço no dia 3, o dia 3 usa o preço do dia 2, aparece marcado no painel e a silver continua sem linha estimada
  - E a mudança da taxa de 15% para 10% altera valor_brl

### RF-25: métricas da carteira
Retorno acumulado (valor no último dia / 1000 − 1), excesso sobre o CDI, perda máxima (maior queda % entre um pico e o ponto mais baixo depois dele) e dias com preço carregado. O painel mostra o resultado de cada carteira com a taxa de venda do parâmetro e sem ela (taxa 0), lado a lado.
- Origem: OBJ-05
- Critério de aceite:
  - Dado a série 1000, 1200, 900, 1100
  - Quando as métricas forem calculadas
  - Então o retorno acumulado é 10% e a perda máxima é 25%
  - E, dado as cinco carteiras calculadas com taxa 15%, o painel mostra cada uma com taxa 15% e com taxa 0; a diferença entre as duas versões aparece para selado, cesta_raras e propria e é zero para dolar e cdi

### RF-26: grava o resultado no contrato gold_turma
- Origem: OBJ-05, RES-08
- Critério de aceite:
  - Dado as carteiras calculadas
  - Quando a gold for construída
  - Então `gold_turma/carteira/group_id=24269/carteira.parquet` tem as colunas e tipos do contrato, uma linha por dia de calendário × carteira, retorno_acumulado = valor_brl / 1000 − 1 e taxa_venda = 0 nas carteiras dolar e cdi

### RF-27: cobertura do período e dias sem coleta
- Origem: OBJ-01, DRV-01
- Critério de aceite:
  - Dado o bruto e a tabela "Dias sem coleta" do README
  - Quando a verificação de cobertura for executada
  - Então ela termina com sucesso só se cada data entre o primeiro e o último dia tiver os quatro arquivos do bruto ou uma linha na tabela, com motivo; caso contrário, lista as datas faltantes

### RF-28: placar da turma
O painel lê `gold_turma/carteira/` de todas as coleções disponíveis, somente para leitura, e mostra em quantas coleções a carteira selado superou a cdi, em quantas a cesta_raras superou a dolar (pelo retorno acumulado no último dia) e qual coleção teve a menor perda máxima.
- Origem: OBJ-04, OBJ-05, RES-13
- Critério de aceite:
  - Dado gold_turma de três coleções, com o selado acima do CDI em duas e a cesta_raras acima do dólar em uma
  - Quando o placar for exibido
  - Então ele mostra "2 de 3", "1 de 3" e a coleção de menor perda máxima, e nenhum objeto de outra coleção é criado ou alterado
  - E, dado um bucket só com a gold_turma da DRI, o placar mostra o aviso explícito de que faltam dados de outras coleções e exibe só a DRI

## Requisitos não funcionais

### RNF-01: conversão nunca usa cotação posterior
- Atributo: correção dos dados
- Origem: OBJ-02, RES-04
- Critério de aceite:
  - Dado preços de 10/10/2026 (sábado), 11/10 (domingo) e 12/10 (feriado) e PTAX de 09/10 e 13/10
  - Quando a conversão for executada
  - Então os três dias usam a PTAX de 09/10 e nenhum usa a de 13/10

### RNF-02: identidade da decomposição
- Atributo: correção dos dados
- Origem: OBJ-02
- Critério de aceite:
  - Dado qualquer item com preço e PTAX no primeiro e no último dia
  - Quando a decomposição for calculada
  - Então |(1 + r_brl) − (1 + r_usd) × (1 + r_cambio)| ≤ 1e-9

### RNF-03: bruto imutável e escrita isolada
- Atributo: integridade
- Origem: RES-08
- Critério de aceite:
  - Dado o pipeline completo (coleta, sincronização, silver, gold) contra um MinIO de teste
  - Quando ele for executado
  - Então nenhuma chave fora dos prefixos com `group_id=24269` é criada ou alterada, nenhum objeto do bruto muda de hash e o código não tem chamadas de exclusão

### RNF-04: idempotência
- Atributo: confiabilidade
- Origem: OBJ-06
- Critério de aceite:
  - Dado o mesmo bruto
  - Quando silver e gold forem reconstruídas duas vezes
  - Então os conteúdos das tabelas são iguais nas duas execuções

### RNF-05: testes de unidade sem rede
- Atributo: testabilidade
- Origem: OBJ-06
- Critério de aceite:
  - Dado a rede bloqueada
  - Quando os testes de unidade forem executados com pytest
  - Então todos passam

### RNF-06: integração com respostas HTTP gravadas
- Atributo: testabilidade
- Origem: OBJ-06, RES-03
- Critério de aceite:
  - Dado respostas reais do TCGCSV gravadas no repositório de testes
  - Quando o teste de integração da coleta e da silver for executado sem rede
  - Então ele passa e nenhuma requisição sai para a internet

### RNF-07: integração com MinIO descartável
- Atributo: testabilidade
- Origem: OBJ-06, RES-07
- Critério de aceite:
  - Dado um MinIO em contêiner criado para o teste
  - Quando os testes de gravação, sincronização e recusa de sobrescrita forem executados
  - Então eles passam e o contêiner é descartado no final, sem tocar no MinIO local de trabalho

### RNF-08: segredos fora do Git
- Atributo: segurança
- Origem: OBJ-06, RES-06
- Critério de aceite:
  - Dado o histórico completo do repositório e os logs de execução
  - Quando uma busca por credenciais for executada
  - Então nada é encontrado, e o código lê credenciais só de variáveis de ambiente

### RNF-09: custo zero
- Atributo: custo
- Origem: OBJ-06, RES-02
- Critério de aceite:
  - Dado a lista de serviços usados documentada no README
  - Quando ela for revisada
  - Então todos são gratuitos no uso do projeto

### RNF-10: reprodução a partir de clone limpo
- Atributo: reprodutibilidade
- Origem: OBJ-06, DRV-06
- Critério de aceite:
  - Dado um clone limpo, com `.env` preenchido a partir do `.env.example`
  - Quando os passos do README forem seguidos
  - Então os testes passam e silver, gold e painel são reconstruídos a partir do bruto

### RNF-11: rastreabilidade até o bruto
- Atributo: auditabilidade
- Origem: DRV-06
- Critério de aceite:
  - Dado uma linha qualquer de `fato_preco_diario`
  - Quando a `chave_raw` dela for seguida
  - Então o objeto existe no bruto e contém o produto e o preço da linha

### RNF-12: limite de requisições
- Atributo: uso responsável da fonte
- Origem: RES-03
- Critério de aceite:
  - Dado o log de requisições de um dia de coleta
  - Quando ele for contado
  - Então há no máximo 10.000 requisições ao TCGCSV

### RNF-13: execução agendada
A coleta roda todo dia depois das 20h UTC sem intervenção manual, com credenciais só em variáveis de ambiente e secrets.
- Atributo: operabilidade
- Origem: OBJ-01, DRV-01, RES-06, RES-07
- Critério de aceite:
  - Dado o período entre o primeiro e o último dia de coleta
  - Quando o histórico de execuções do agendador for consultado
  - Então há uma execução por dia, depois das 20h UTC, e cada dia sem execução bem-sucedida aparece na tabela "Dias sem coleta" do README, com o motivo

## Fora do escopo

| Item | Motivo |
|---|---|
| Previsão de preço e recomendação de compra | RES-10 |
| Coleta ou gravação de outras coleções ou groupIds | AGENTS.md; RES-13 (outras coleções são só lidas) |
| Streaming ou atualização em tempo real | O preço muda uma vez por dia (DRV-03) |
| Preço de carta graduada (PSA, CGC etc.) | Fora da fonte acompanhada |
| Scraping de sites que bloqueiam acesso automatizado | RES-01, RES-03 |
| Frete, IOF, taxas do comprador e spread bancário | RES-11, RES-12 |
| Outras moedas ou investimentos além de dólar e CDI | DRV-04 |
| Preencher lacunas na silver ou na gold por interpolação, cópia ou estimativa | OBJ-01 (o último preço carregado só existe na avaliação da carteira, RF-24) |

## Perguntas abertas

Nenhuma pergunta pendente nesta revisão. Continuam como hipótese, a validar na primeira coleta:
- regra do `tipo_produto` e lista de raridades "Double Rare em diante" (Definições);
- identificação do booster box (RF-23);
- presença de imagem e link em todos os produtos (RF-20);
- existência de preço próprio para os selados (RF-16, RF-23);
- tamanho da janela de PTAX e CDI (RF-01) e parâmetros de repetição (RF-03).
