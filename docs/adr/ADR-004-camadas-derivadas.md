# ADR-004: Camadas derivadas e reprocessamento

## Status

Aceito em 2026-11-04.

## Contexto e forças

O bruto da DRI (groupId 24269) é imutável e tem duas cópias: a Branch dados-raw, que é a fonte de verdade, e o MinIO local, preenchido por `make sync` (ADR-001). Silver, gold e gold_turma são calculadas a partir dele. Uma correção de regra (classificação do `tipo_produto`, quarentena, ASOF JOIN da PTAX, composição das carteiras) muda resultados de todos os dias já processados, não só do dia seguinte. O MinIO local também pode perder o volume junto com o Codespace (R-11). Por isso as camadas derivadas precisam ser refeitas inteiras, do mesmo jeito, com um único comando (RF-13).

Forças em jogo:
- **Bruto intocável** (RES-08, RNF-03): nenhuma reconstrução pode criar, alterar ou apagar objeto em `raw/`.
- **Escrita isolada** (RNF-03): o bucket `tcg` pode ter silvers e gold_turma de outras coleções, lidas só para leitura; nada fora do prefixo `group_id=24269` pode mudar.
- **Idempotência** (RNF-04): o mesmo bruto tem de produzir as mesmas tabelas, sem linha duplicada.
- **Rastreabilidade** (RNF-11): cada linha derivada mantém a `chave_raw` de origem, que continua existindo depois de qualquer reconstrução.
- **Exclusão sob controle** (AGENTS.md): apagar é proibido por padrão; o agente nunca apaga nada, e a única exceção é `make reprocessar`, executado pelo autor.
- **Simplicidade**: a escala é de uma coleção, um arquivo por fonte por dia, no prazo da disciplina.

## Requisitos e cenários relacionados

| Requisito | Cenário que esta decisão precisa atender |
|---|---|
| RF-13 | Com silver e gold já construídas, o reprocessamento executado duas vezes reconstrói tudo a partir do bruto, com a mesma contagem de linhas de uma execução e sem chave de grão duplicada. |
| RNF-03 | O pipeline completo contra um MinIO de teste não cria nem altera chave fora de `group_id=24269` e não muda o hash de nenhum objeto do bruto; a única exclusão do código aceita só os três prefixos derivados e recusa `raw/` e outros group_ids, com teste. |
| RNF-04 | Duas reconstruções a partir do mesmo bruto geram tabelas com conteúdo igual. |
| RNF-11 | A `chave_raw` de uma linha qualquer de `fato_preco_diario` aponta para um objeto que existe no bruto e contém o produto e o preço da linha. |

## Alternativas consideradas

| Alternativa | Por que foi descartada |
|---|---|
| Sobrescrever as chaves sem apagar | Uma partição que deixa de existir (data que vai para a quarentena, produto reclassificado, tabela renomeada) fica no bucket como objeto órfão, e silver e gold passam a misturar o resultado antigo com o novo. |
| Versionar cada execução no caminho (ex.: `execucao=<id>/`) | Muda os caminhos do contrato comum da silver e da gold_turma, que outras coleções leem por curinga; exigiria também um ponteiro para a "versão atual" e limpeza das versões antigas. |
| Processamento incremental com merge | Mais complexo (detectar o que mudou, chaves de merge por tabela) e com risco de duplicar linhas quando um mesmo dia é reprocessado; não atende uma correção de regra que muda o histórico inteiro. |
| Formato de tabela transacional (Delta Lake ou Apache Iceberg) | Fora da stack escolhida (DuckDB com Parquet no MinIO, plan.md, seção 6) e do escopo do projeto; acrescenta catálogo e dependências para um volume que não precisa disso. |

## Decisão e táticas

Silver, gold e gold_turma da DRI são **camadas derivadas**: podem ser apagadas e reconstruídas a qualquer momento a partir do bruto. `make reprocessar` apaga somente os objetos de `silver/*/group_id=24269/` (inclusive a quarentena), `gold/group_id=24269/` e `gold_turma/carteira/group_id=24269/` e, em seguida, roda `make silver` e `make gold`. Toda exclusão do código passa por uma única função da Guarda de prefixo (`src/tcg/lake/guarda_prefixo.py`), que valida cada chave contra esses três prefixos **antes** de chamar o SDK e recusa qualquer chave em `raw/`, de outro group_id ou com `..`. O reprocessamento é executado só pelo autor; o agente implementa e testa contra MinIO descartável, mas nunca o executa.

| Tática | Atributo de qualidade | Como aparece |
|---|---|---|
| Reconstrução a partir da fonte de verdade | Recuperabilidade | Silver e gold saem só do bruto; perdido o MinIO, `make sync` e `make reprocessar` refazem tudo a partir da Branch dados-raw. |
| Operação idempotente | Confiabilidade | Apagar e reconstruir do zero, com caminhos determinísticos, faz duas execuções seguidas produzirem as mesmas tabelas, sem duplicar linhas (RNF-04). |
| Ponto único de exclusão com guarda de prefixo | Integridade e segurança | Uma só função apaga, e só nos três prefixos derivados do `group_id=24269`; `raw/` e outros group_ids são recusados antes de qualquer chamada ao SDK, com teste (RNF-03). |
| Separação entre camada imutável e camadas derivadas | Modificabilidade | Uma regra nova da silver ou da gold muda só código e se aplica a todo o histórico com um comando, sem tocar no bruto. |

## Consequências positivas

- Uma correção de regra vale para todo o histórico com um comando, sem migração manual.
- Nenhum objeto órfão: depois do reprocessamento, os prefixos derivados contêm só o resultado da execução atual.
- O bruto e os dados de outras coleções ficam fora do alcance da única exclusão do código, e isso é testado (RNF-03).
- A perda do volume do MinIO local deixa de ser grave: o estado inteiro se refaz a partir da Branch dados-raw.
- Os caminhos do contrato não mudam, e quem lê por curinga continua lendo os mesmos caminhos.

## Consequências negativas

- O tempo de reprocessamento cresce com o número de dias do bruto, porque tudo é refeito a cada execução. Tempo por execução: hipótese: validação pendente.
- Durante o reprocessamento, silver e gold ficam incompletas; o painel não deve ser consultado nesse intervalo, e uma falha no meio deixa as camadas derivadas vazias até a próxima execução bem-sucedida.
- O código passa a ter uma operação de exclusão, ainda que restrita a uma função e a três prefixos; um erro nela tem efeito destrutivo.
- `make silver` e `make gold` sozinhos sobrescrevem as chaves sem apagar; se uma partição deixar de existir, só `make reprocessar` remove o objeto antigo.

## Riscos

| Risco | Mitigação |
|---|---|
| Exclusão fora do prefixo por erro na guarda (R-10) | Função única; validação de cada chave antes do SDK; testes de recusa para `raw/`, outro group_id e `..`; o bruto também está na Branch dados-raw. |
| Reprocessamento interrompido no meio | Rodar `make reprocessar` de novo: como é idempotente, a reexecução termina o trabalho. |
| Painel consultado durante o reprocessamento | Rodar o reprocessamento com o painel fechado; o log registra início, fim e as chaves apagadas. |
| Silver ou gold de outra coleção apagada por engano | A guarda aceita só `group_id=24269`; o pipeline completo confere que nenhuma chave fora desse prefixo muda. |
| Execução de exclusão pelo agente | Proibida pelo AGENTS.md; os testes de exclusão rodam só contra MinIO descartável e o teste do reprocessamento é executado pelo autor. |

## Evidência necessária

- Teste da Guarda de prefixo: escrita e exclusão aceitas nos três prefixos; chaves em `raw/`, de outro group_id ou com `..` recusadas antes de qualquer chamada ao SDK (T-23).
- Teste do reprocessamento contra MinIO descartável: duas execuções seguidas com a mesma contagem de linhas, o mesmo conteúdo e nenhuma chave de grão duplicada; nenhum objeto de `raw/` muda de hash (T-33, executado pelo autor).
- Pipeline completo contra MinIO de teste: lista de chaves antes e depois só difere nos prefixos permitidos, e a `chave_raw` de uma linha sorteada existe no bruto (T-34).
- Tempo de um reprocessamento com o bruto acumulado, para substituir a hipótese acima.

## Condição de revisão

- Se o tempo de reprocessamento ficar inviável para o uso diário, avaliar processamento incremental.
- Reavaliar também se o projeto passar a gravar silver ou gold fora do MinIO local, ou se o contrato comum passar a prever versões no caminho.
