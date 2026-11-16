# ADR-006: Fallback do selado

## Status

Aceito em 2026-11-16. Decisão do autor, registrada antes do primeiro cálculo da carteira (RF-23, T-41), com base no resultado do T-13 (`docs/evidencias/T-13_hipoteses.md`).

## Contexto e forças

O RF-23 manda a carteira selado comprar o booster box da coleção com R$ 1.000,00, ao preço de compra do primeiro dia, em unidades inteiras e com a sobra em caixa. A spec identifica o booster box pelo nome: contém "Booster Box" e não contém "Case" nem "Half". Na DRI ele é o `Destined Rivals Booster Box`, productId 624679. Se o booster box não tiver preço, a spec manda usar "o selado de maior preço com preço" e deixa os detalhes para este ADR.

No T-13, a primeira regra ("Booster Box" sem "Case") foi refutada porque também pegava o `Destined Rivals Half Booster Box`, e a spec passou a excluir "Half". No mesmo bruto (2026-11-03, primeira coleta), o booster box tem market_price e os 25 selados têm preço próprio. Nesse bruto o fallback não seria acionado.

Forças em jogo:
- **Comparabilidade no placar da turma** (RF-26): a carteira selado de cada coleção precisa significar a mesma coisa para que "selado superou a cdi" seja comparável entre coleções.
- **Sem informação do futuro** (OBJ-05): a escolha do selado usa só o primeiro dia.
- **Reprodutibilidade**: a mesma silver produz sempre o mesmo selado, com desempate explícito.
- **Orçamento em unidades inteiras**: um selado mais caro que R$ 1.000,00 não compra nenhuma unidade.
- **Fidelidade à regra**: o fallback cobre só o caso que a spec prevê (ausência de preço), sem criar outros gatilhos.

## Requisitos e cenários relacionados

| Requisito | Cenário que esta decisão precisa atender |
|---|---|
| RF-23 | O booster box tem market_price no primeiro dia: a carteira selado compra o booster box (na DRI, productId 624679), mesmo que outro selado seja mais caro. |
| RF-23 | O booster box não tem market_price no primeiro dia: a carteira compra o produto `tipo_produto = 'selado'` de maior market_price entre os que têm preço nesse dia. |
| RF-23 | No fallback, dois selados empatados no maior market_price: entra o de menor `product_id`; persistindo o empate, o de `acabamento` alfabeticamente menor. |
| RF-23 | O booster box tem preço, mas o preço de compra passa de R$ 1.000,00: zero unidades, R$ 1.000,00 em caixa, e o fallback não é acionado. |
| RF-23 | Com o primeiro dia e, de novo, com dez dias a mais de preço, o selado escolhido e as unidades são idênticos. |
| RF-24 | O caixa da carteira selado rende CDI em dia útil, como nas demais carteiras. |

## Alternativas consideradas

| Alternativa | Por que foi descartada |
|---|---|
| Acionar o fallback também quando o booster box não cabe em R$ 1.000,00 | Mudaria o significado da carteira, que deixaria de ser booster box, e cada coleção acabaria com um selado diferente conforme o preço do seu booster box. A carteira selado deixaria de ser comparável entre as coleções da turma no placar. |
| Escolher o selado de fallback à mão | Não é reproduzível e depende de julgamento caso a caso. |
| Sem fallback: carteira toda em caixa quando o booster box não tem preço | A spec prevê um selado substituto; ficar em caixa transformaria a carteira na cdi sem que a regra diga isso. |
| Buscar o preço do booster box em outro dia | Usar dia posterior é informação do futuro (OBJ-05); copiar preço de outro dia contraria a regra de não preencher lacunas. |

## Decisão e táticas

**Selado principal**: o booster box da coleção, identificado pela regra validada no T-13 e registrada no RF-23 (nome contém "Booster Box", não contém "Case" nem "Half"). Na DRI, productId 624679.

**Gatilho do fallback**: só a ausência de market_price do booster box no primeiro dia (Definições da spec: menor `data` com bruto do TCGCSV da coleção). Preço acima do orçamento não aciona o fallback.

**Selado de fallback**: entre os produtos com `tipo_produto = 'selado'` e market_price no primeiro dia, o de maior market_price. Empate: menor `product_id`, depois `acabamento` em ordem alfabética.

**Orçamento e unidades**: a regra do RF-23 é seguida literalmente. Compra-se o máximo de unidades inteiras que caibam em R$ 1.000,00 ao preço de compra do primeiro dia (market_price × PTAX de venda aplicada, sem taxa na compra). Se o selado custar mais que o orçamento, a carteira fica com zero unidades e todo o valor fica em caixa, rendendo CDI de dia útil.

**Avaliação diária**: as mesmas regras das carteiras cesta_raras e propria (RF-24).

| Tática | Atributo de qualidade | Como aparece |
|---|---|---|
| Gatilho único e explícito (ausência de preço) | Comparabilidade, legibilidade | O fallback só roda quando o booster box não tem market_price no primeiro dia; não há outro caminho. |
| Desempate total | Reprodutibilidade, testabilidade | Ordem por market_price, `product_id` e `acabamento`; a mesma silver gera o mesmo selado. |
| Entrada restrita ao primeiro dia | Correção, auditabilidade | A composição recebe só os preços do primeiro dia; dias posteriores não mudam o resultado. |
| Regra literal de unidades inteiras | Fidelidade à spec | Zero unidades é um resultado válido, e a sobra vai para o caixa como em todas as carteiras. |

## Consequências positivas

- A carteira selado significa "booster box" em todas as coleções em que ele tem preço, o que mantém o placar da turma comparável.
- O fallback é previsível: depende só de haver ou não preço, não do valor do booster box.
- A composição usa só informação do primeiro dia e é reproduzível.
- Reaproveita as funções de compra, liquidação e caixa das demais carteiras.

## Consequências negativas

- Na DRI, com o booster box acima de R$ 1.000,00 no primeiro dia, a carteira selado tende a ficar com zero unidades e a se comportar como a carteira cdi. A exposição a selado do autor fica na carteira propria (ADR-005).
- Em qualquer coleção cujo booster box custe mais que o orçamento, a carteira selado não mede o desempenho do selado, só o do caixa.
- O selado de fallback, quando acionado, é o de maior preço, que pode ser um produto pouco representativo da coleção (por exemplo, uma caixa com vários booster boxes).

## Riscos

| Risco | Mitigação |
|---|---|
| O booster box ficar sem preço no primeiro dia de alguma coleção | O fallback desta decisão cobre o caso; o painel mostra o selado efetivamente comprado. |
| No fallback, o selado de maior preço passar do orçamento e a carteira ficar com zero unidades | A regra é mantida como decidida; o valor fica em caixa e aparece na composição. |
| Leitor do placar interpretar a selado com zero unidades como desempenho de selado | O painel mostra a composição (unidades e caixa) ao lado do retorno. |
| A regra do nome pegar outro produto numa coleta futura | A regra foi validada no T-13; um segundo produto que case com ela é tratado como pendência, e qualquer mudança da regra exige a revisão deste ADR. |
| Cálculo da carteira antes do commit deste ADR | Este ADR é commitado antes da T-41; o `git log` comprova a ordem. |

## Evidência necessária

- `docs/evidencias/T-13_hipoteses.md`: identificação do booster box (regra com exclusão de "Half"), booster box com market_price no bruto de 2026-11-03 e 25 de 25 selados com preço próprio.
- `git log --oneline -- docs/adr/ADR-006-fallback-selado.md` mostrando o commit deste ADR antes do primeiro commit da T-41 (`src/tcg/gold/carteiras.py`).
- Testes da T-41 (`tests/unidade/test_composicao.py`): booster box com preço é escolhido mesmo com selado mais caro; booster box sem preço aciona o fallback; empate no fallback por `product_id` e depois `acabamento`; booster box acima do orçamento resulta em zero unidades sem acionar o fallback; composição idêntica com o primeiro dia e com dez dias a mais.

## Condição de revisão

- Se a regra de identificação do booster box mudar na spec (RF-23) ou deixar de identificar um único produto.
- Se a spec mudar o orçamento das carteiras, a regra do custo de compra ou a regra de avaliação (RF-23, RF-24).
- Se o placar da turma (RF-26) passar a exigir uma carteira selado com exposição mínima a selado.
- Qualquer mudança da regra depois do primeiro cálculo é um novo ADR que substitui este, nunca uma edição deste.
