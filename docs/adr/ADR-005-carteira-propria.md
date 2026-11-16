# ADR-005: Regra da carteira propria

## Status

Aceito em 2026-11-16. Decisão do autor, registrada antes do primeiro cálculo da carteira (RF-23, T-41).

## Contexto e forças

A spec define cinco carteiras de R$ 1.000,00 montadas com dados do primeiro dia (RF-23) e deixa a regra da carteira propria ao autor: sem este ADR, a carteira não é calculada e o painel mostra "regra pendente". As outras carteiras de mercado já cobrem dois extremos. A selado compra o booster box da coleção. A cesta_raras compra os dez itens de carta de maior market_price.

Forças em jogo:
- **Sem informação do futuro** (OBJ-05): a composição só pode usar o que se sabia no dia da compra; recompor ou escolher olhando dias posteriores invalida a comparação.
- **Diferenciação**: uma carteira que repete a cesta_raras ou a selado não acrescenta nada ao placar.
- **Exposição real a selado**: em unidades inteiras, a carteira selado pode ficar sem nenhuma unidade se o booster box custar mais que o orçamento; a propria deve garantir alguma exposição a selado sempre que houver um que caiba.
- **Reprodutibilidade**: a mesma silver tem de produzir sempre a mesma composição, com desempate explícito.
- **Mesmas regras de avaliação**: a propria precisa ser comparável às outras, com custo de compra, liquidação, caixa e preço ausente idênticos (RF-23, RF-24).

## Requisitos e cenários relacionados

| Requisito | Cenário que esta decisão precisa atender |
|---|---|
| RF-23 | Com o primeiro dia e, de novo, com dez dias a mais de preço, a composição da propria é idêntica. |
| RF-23 | Dois itens Illustration Rare empatados na quinta posição: entra o de menor `product_id`; persistindo o empate, o de `acabamento` alfabeticamente menor. |
| RF-23 | Dois selados com o mesmo preço de compra: entra o de menor `product_id`; persistindo o empate, o de `acabamento` alfabeticamente menor. |
| RF-23 | Nenhum selado com preço de compra ≤ R$ 500,00: os R$ 500,00 ficam em caixa. |
| RF-23 | Só três Illustration Rare elegíveis: R$ 200,00 ficam em caixa. |
| RF-24 | A propria é avaliada como selado e cesta_raras: liquidação com PTAX de compra, taxa de venda do parâmetro, caixa rendendo CDI de dia útil e último preço observado marcado. |

## Alternativas consideradas

| Alternativa | Por que foi descartada |
|---|---|
| Momento: comprar as cartas que mais subiram | Exige mais de um dia de preço; no dia de montagem não há histórico, e usar dias posteriores seria informação do futuro. |
| Menor volatilidade | Exige uma série de preços para medir a volatilidade; pelo mesmo motivo, usaria informação do futuro. |
| Cartas mais caras | Repete a cesta_raras, que já compra os itens de maior market_price. |

## Decisão e táticas

**Dia de montagem**: o primeiro dia, conforme as Definições da spec (menor `data` com bruto do TCGCSV da coleção), o mesmo das carteiras selado e cesta_raras. Só preços desse dia entram na composição.

**Preço de compra**: market_price em US$ do dia de montagem × PTAX de venda aplicada no mesmo dia, como nas demais carteiras; sem taxa na compra.

**Parte selada (R$ 500,00)**: entre os produtos com `tipo_produto = 'selado'`, com preço no dia de montagem e preço de compra ≤ R$ 500,00, escolhe-se o de maior preço e compra-se o máximo de unidades inteiras que caibam em R$ 500,00. Empate: menor `product_id`, depois `acabamento` em ordem alfabética. Se nenhum selado couber, os R$ 500,00 ficam em caixa.

**Parte de cartas (R$ 500,00)**: entre os itens (produto × acabamento) com `tipo_produto = 'carta'`, raridade "Illustration Rare", sem Code Card e com preço no dia de montagem, escolhem-se os cinco de maior market_price; cada um recebe R$ 100,00 em unidades inteiras. Empate: menor `product_id`, depois `acabamento` em ordem alfabética. Com menos de cinco elegíveis, o valor dos que faltam fica em caixa.

**Sobra**: todo valor não aplicado fica em caixa, rendendo CDI em dia útil, como nas demais carteiras.

**Avaliação diária e preço ausente**: as mesmas regras das carteiras selado e cesta_raras (RF-24): valor de liquidação com PTAX de compra aplicada, taxa_venda do parâmetro (15% como hipótese declarada) e, para item sem preço no dia, o último preço observado só na avaliação, marcado no painel, sem gravar na silver.

| Tática | Atributo de qualidade | Como aparece |
|---|---|---|
| Entrada restrita ao dia de montagem | Correção, auditabilidade | A função de composição recebe só os preços do primeiro dia; dias posteriores não mudam o resultado. |
| Desempate total e explícito | Reprodutibilidade, testabilidade | Ordem por preço, `product_id` e `acabamento`; a mesma silver gera a mesma composição. |
| Orçamento dividido em partes fixas | Legibilidade | Duas metades independentes, cada uma com sua sobra em caixa. |
| Reuso das regras das outras carteiras | Comparabilidade | Custo de compra, liquidação, caixa e preço ausente são as mesmas funções da selado e da cesta_raras. |

## Consequências positivas

- A composição usa só informação disponível no primeiro dia.
- Diferencia-se da cesta_raras, que tende a concentrar Special Illustration Rare, testando a raridade imediatamente abaixo (Illustration Rare).
- Dá exposição real a selado quando a carteira selado fica sem unidade porque o booster box custa mais que o orçamento em unidades inteiras.
- Reaproveita as funções de compra, liquidação e caixa das carteiras já especificadas.

## Consequências negativas

- O selado escolhido é o de maior preço que cabe em R$ 500,00, não necessariamente o booster box; a propria pode ficar exposta a um produto selado menos representativo da coleção.
- Cinco cartas de uma só raridade concentram o risco; uma queda generalizada das Illustration Rare pesa em metade da carteira.
- Com R$ 100,00 por carta, um item com preço de compra acima disso não recebe unidade e o valor vai para o caixa.

## Riscos

| Risco | Mitigação |
|---|---|
| Menos de cinco Illustration Rare com preço no dia de montagem | A sobra vai para o caixa, como a regra prevê; o painel mostra a composição efetiva. |
| Uma Illustration Rare de preço de compra acima de R$ 100,00 entra entre as cinco e não compra unidade | A regra é mantida como decidida; o valor fica em caixa e aparece na composição. |
| A raridade "Illustration Rare" vir com outro nome numa coleta | A lista de raridades da spec, validada no T-13, trata raridade fora da lista como pendência. |
| Cálculo da carteira antes do commit deste ADR | Este ADR é commitado antes da T-41; o `git log` comprova a ordem. |

## Evidência necessária

- `git log --oneline -- docs/adr/ADR-005-carteira-propria.md` mostrando o commit deste ADR antes do primeiro commit da T-41 (`src/tcg/gold/carteiras.py`).
- Teste da T-41 (`tests/unidade/test_composicao.py`): a composição da propria com o primeiro dia é idêntica à composição com dez dias a mais; empates nas duas partes; nenhum selado elegível; menos de cinco cartas elegíveis.

## Condição de revisão

- Se a raridade "Illustration Rare" deixar de existir na fonte ou mudar de nome.
- Se a spec mudar o orçamento das carteiras, a regra do custo de compra ou a regra de avaliação (RF-23, RF-24).
- Qualquer mudança da regra depois do primeiro cálculo é um novo ADR que substitui este, nunca uma edição deste.
