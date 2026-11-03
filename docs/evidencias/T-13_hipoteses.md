# T-13: hipóteses da spec contra o primeiro bruto

- Bruto analisado: branch `origin/dados-raw`, commit `65c413a dados(coleta): 2026-11-03 [RF-01]`, data `2026-11-03` (quatro arquivos).
- Leitura só por `git show origin/dados-raw:<caminho>` (um `git fetch`, sem checkout, sem requisição às fontes).
- Contagens geradas por `scripts/hipoteses_bruto.py` (funções testadas em `tests/unidade/test_hipoteses_bruto.py`).
- A spec **não** foi alterada; as correções propostas estão no fim, para decisão do autor.

## Resumo

| Hipótese (Perguntas abertas da spec) | Resultado |
|---|---|
| Regra do `tipo_produto` (sem número = selado; Code Card = carta) | **confirmada** |
| Lista de raridades "Double Rare em diante" | **confirmada** |
| Identificação do booster box ("Booster Box" e não "Case") | **refutada**: a regra pega dois produtos |
| Imagem e link em todos os produtos | **confirmada** |
| Preço próprio dos selados | **confirmada** |
| Janela de 10 dias corridos para PTAX e CDI | **consistente** com o primeiro dia; validação completa depende de mais coletas |
| Parâmetros de repetição (RF-03) | **não validável pelo bruto** |

## Números tirados do bruto

### Produtos e preços
- `products.json`: `totalItems` = 281 e 281 itens em `results`.
- `prices.json`: 446 linhas de preço, por `subTypeName`: Normal 184, Reverse Holofoil 165, Holofoil 97.
- Todo produto tem ao menos uma linha de preço (0 produtos sem linha).
- `marketPrice` nulo: 1 linha (productId 637654, "Code Card - Destined Rivals Premium Checklane Blister [Skeledirge]", Normal).

### Regra do `tipo_produto`: confirmada
- Produtos sem `Number` no `extendedData`: 37.
- Desses, 12 são Code Card (raridade "Code Card"; todos os Code Cards da coleção estão sem número) e viram `carta` pela exceção.
- Os outros 25 são selados (booster box, bundles, blisters, ETBs, cases etc.); nenhuma carta numerada ficou sem raridade.
- Resultado da regra: 25 `selado` e 256 `carta` (244 cartas numeradas, com 244 números distintos, mais 12 Code Cards).
- O conjunto dos 25 sem raridade é exatamente o conjunto dos 25 selados.
- Itens de carta (linhas de preço de produtos `carta`): 421.

### Raridades: confirmada
| Raridade | Produtos |
|---|---|
| Common | 85 |
| Uncommon | 62 |
| Rare | 18 |
| Double Rare | 17 |
| Ultra Rare | 22 |
| Illustration Rare | 23 |
| Special Illustration Rare | 11 |
| Hyper Rare | 6 |
| Code Card | 12 |
| (sem raridade: selados) | 25 |

- As cinco raridades da lista existem com o nome exato da spec.
- Fora da lista só aparecem Common, Uncommon, Rare e Code Card, que ficam abaixo de Double Rare ou fora das análises. Não há raridade nova a registrar como pendência.

### Booster box: refutada
- Produtos cujo nome contém "Booster Box" e não "Case": **2**.
  - 624679 `Destined Rivals Booster Box`: marketPrice US$ 381,38 (Normal).
  - 624681 `Destined Rivals Half Booster Box`: marketPrice US$ 316,15 (Normal).
- A regra precisa excluir também "Half". O nome exato do booster box é `Destined Rivals Booster Box`, e ele **tem preço**.
- Para o ADR-006: o selado de maior preço é o `Destined Rivals Booster Box Case` (US$ 2.482,24). No primeiro dia o fallback não seria acionado.

### Preço dos selados: confirmada
- 25 selados, 25 com `marketPrice` preenchido, 0 sem preço.
- Cada selado tem uma única linha, sempre com `subTypeName` = Normal.

### Imagem e link: confirmada
- `imageUrl` preenchido: 281 de 281.
- `url` preenchido: 281 de 281.
- O aviso "imagem indisponível"/"link indisponível" do RF-20 continua necessário para dias futuros, mas não é acionado neste bruto.

### PTAX (`cotacao.json`)
- Janela pedida: 25/10/2026 a 03/11/2026 (10 dias corridos).
- 30 boletins: Abertura 6, Intermediário 18, Fechamento 6.
- Datas com boletim `Fechamento` (compra / venda):
  - 2026-10-26: 5,4998 / 5,5007
  - 2026-10-27: 5,3340 / 5,3346
  - 2026-10-28: 5,3414 / 5,3420
  - 2026-10-29: 5,3738 / 5,3744
  - 2026-10-30: 5,4206 / 5,4212
  - 2026-11-03: 5,4929 / 5,4935
- Sem boletim: 25/10 (domingo), 31/10 e 01/11 (fim de semana) e 02/11 (Finados). O Fechamento de 03/11 já estava disponível na coleta das 20h44 UTC.
- 24 boletins intermediários e de abertura serão descartados por regra (RF-07/T-25).

### CDI (`cdi.json`)
- 5 dias: 26/10, 27/10, 28/10, 29/10 e 30/10/2026, todos com valor 0,050788.
- 03/11 ainda não veio. Isso confirma a razão da janela no RF-01: o CDI do dia útil só sai na manhã seguinte.

### Janela e repetição
- Janela de 10 dias: cobriu 6 dias úteis de PTAX e 5 de CDI, com folga sobre a maior lacuna observada (30/10 → 03/11). A hipótese se mantém, mas só fica validada com coletas em dias seguidos (a sobreposição precisa trazer o CDI de 03/11).
- Repetição (RF-03): o bruto não registra tentativas. O log do T-12 mostra só `tentativa=1/4` nas quatro requisições, sem nenhuma falha transitória. Fica como hipótese.

## Correções propostas na spec (não aplicadas)

1. RF-23: excluir o "Half Booster Box" da identificação do booster box.

```diff
--- a/specs/spec.md
+++ b/specs/spec.md
@@ RF-23
-- **selado**: booster box da coleção, identificado pelo nome contendo "Booster Box" e não "Case" (hipótese: validação pendente na primeira coleta); se ele não tiver preço, o selado de maior preço com preço (escolha em ADR).
+- **selado**: booster box da coleção, identificado pelo nome contendo "Booster Box" e não contendo "Case" nem "Half" (na DRI, `Destined Rivals Booster Box`, productId 624679, validado no T-13); se ele não tiver preço, o selado de maior preço com preço (escolha em ADR).
```

2. Hipóteses confirmadas: retirar a marca de hipótese (opcional, a critério do autor).

```diff
@@ Definições e decisões
-- **tipo_produto** (hipótese: validação pendente na primeira coleta): produto sem número de carta é `selado`; os demais são `carta`. Exceção: raridade "Code Card" é sempre `carta`.
-- **Raridades "Double Rare em diante"** (hipótese: validação pendente na primeira coleta), em ordem: Double Rare, Ultra Rare, Illustration Rare, Special Illustration Rare, Hyper Rare. Uma raridade que a fonte trouxer fora da lista entra como pendência na primeira coleta.
+- **tipo_produto** (validado no T-13): produto sem número de carta é `selado`; os demais são `carta`. Exceção: raridade "Code Card" é sempre `carta`.
+- **Raridades "Double Rare em diante"** (validado no T-13), em ordem: Double Rare, Ultra Rare, Illustration Rare, Special Illustration Rare, Hyper Rare. Uma raridade que a fonte trouxer fora da lista entra como pendência.
@@ Perguntas abertas
-Nenhuma pergunta pendente nesta revisão. Continuam como hipótese, a validar na primeira coleta:
-- regra do `tipo_produto` e lista de raridades "Double Rare em diante" (Definições);
-- identificação do booster box (RF-23);
-- presença de imagem e link em todos os produtos (RF-20);
-- existência de preço próprio para os selados (RF-16, RF-23);
-- tamanho da janela de PTAX e CDI (RF-01) e parâmetros de repetição (RF-03).
+Nenhuma pergunta pendente nesta revisão. Regra do `tipo_produto`, raridades, booster box, imagem e link e preço dos selados foram validados no T-13 (`docs/evidencias/T-13_hipoteses.md`). Continuam como hipótese:
+- tamanho da janela de PTAX e CDI (RF-01), a confirmar com coletas em dias seguidos;
+- parâmetros de repetição (RF-03), sem falha transitória observada até agora.
```

## Saída real dos comandos

```
$ .venv/bin/python -m pytest tests/unidade/test_hipoteses_bruto.py -v
tests/unidade/test_hipoteses_bruto.py::test_tipo_produto_sem_numero_selado_e_code_card_carta PASSED [ 16%]
tests/unidade/test_hipoteses_bruto.py::test_booster_box_exclui_case PASSED [ 33%]
tests/unidade/test_hipoteses_bruto.py::test_analisar_produtos_conta_raridades_numero_imagem_e_link PASSED [ 50%]
tests/unidade/test_hipoteses_bruto.py::test_analisar_precos_preco_nulo_conta_como_sem_preco PASSED [ 66%]
tests/unidade/test_hipoteses_bruto.py::test_analisar_ptax_agrupa_boletins_por_tipo PASSED [ 83%]
tests/unidade/test_hipoteses_bruto.py::test_analisar_cdi_conta_dias PASSED [100%]
6 passed in 0.06s
```

```
$ git show origin/dados-raw:raw/tcgplayer/group_id=24269/data=$(git ls-tree --name-only origin/dados-raw:raw/tcgplayer/group_id=24269/ | head -1 | cut -d= -f2)/products.json | python -m json.tool > /dev/null && test -s docs/evidencias/T-13_hipoteses.md; echo "código de saída: $?"
código de saída: 0

$ python -m pytest -q
79 passed in 1.16s
```

## Decisão do autor

- 2026-11-03: o autor aceitou a correção 1 (RF-23: excluir também "Half"), que foi **aplicada** em `specs/spec.md`. A correção 2 não foi pedida nesse momento.
- 2026-11-03: o autor pediu também a correção 2, que foi **aplicada** em `specs/spec.md`: `tipo_produto`, lista de raridades e identificação do booster box passam a citar "validado no T-13 (docs/evidencias/T-13_hipoteses.md)"; em "Perguntas abertas", as cinco hipóteses confirmadas (incluindo imagem e link e preço dos selados, que só tinham marca nessa seção) aparecem como validadas, e continuam como hipótese só a janela de PTAX e CDI (RF-01) e os parâmetros de repetição (RF-03). O script `scripts/hipoteses_bruto.py` mantém a regra antiga do booster box, de propósito, por registrar a hipótese testada.
