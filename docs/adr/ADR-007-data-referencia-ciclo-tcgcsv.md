# ADR-007: Data de referência pelo ciclo do TCGCSV e agendamento redundante

## Status

Aceito em 2026-11-04. Substitui a mitigação do risco "Atraso ou falha do cron" do ADR-001 e o R-01 do plan.md.

## Contexto e forças

O TCGCSV atualiza o preço uma vez por dia, por volta das 20h UTC, e só devolve o preço vigente (DRV-01, DRV-03). Até aqui, a data da coleta era a data UTC do momento, e a guarda recusava qualquer execução antes das 20h UTC. As execuções agendadas #2 e #3 (cron `30 20 * * *`) começaram com 4h17min e 4h29min de atraso, já depois da meia-noite UTC (2026-11-04T00:46Z e 2026-11-05T00:59Z). As duas foram recusadas por horário, com código 2, e a data 2026-11-04 ficou sem bruto (`docs/evidencias/T-57_diagnostico.txt`). A mitigação anterior era um disparo manual antes de 23h59 UTC e dependia do autor estar disponível à noite.

Forças em jogo:
- **Série contínua** (OBJ-01, DRV-01): um dia perdido não se recupera.
- **Uso responsável da fonte** (RES-03): no máximo uma coleta por ciclo, sempre depois da atualização das 20h UTC.
- **Correção do dado**: a `data` gravada tem de corresponder ao preço que a fonte publicou para aquele dia.
- **Custo zero e nenhum secret** (RNF-08, RNF-09): a solução continua só no GitHub Actions.
- **Bruto imutável** (RES-08): o que foi gravado não se corrige depois; o erro precisa ser evitado antes da gravação.

## Requisitos e cenários relacionados

| Requisito | Cenário que esta decisão precisa atender |
|---|---|
| RF-01 | Uma coleta às 2026-11-05T00:59Z grava as quatro chaves com `data=2026-11-04` e a janela da PTAX e do CDI termina em 2026-11-04. |
| RF-04 | Com os arquivos da data de referência já gravados, nenhuma requisição sai, em qualquer horário. |
| RNF-12 | A reserva não aumenta as requisições: arquivo existente é pulado antes de requisitar. |
| RNF-13 | Cada data de referência tem ao menos uma execução bem-sucedida dentro do seu ciclo, mesmo com atraso de mais de 4 h do agendador. |

## Alternativas consideradas

| Alternativa | Por que foi descartada |
|---|---|
| Manter a regra atual e depender do disparo manual antes de 23h59 UTC | Falhou em dois dias seguidos; depende de o autor estar disponível à noite. |
| Antecipar o cron para perto das 20h00 UTC | Só reduz a chance de passar da meia-noite; um atraso de mais de 4 h continua perdendo o dia, e cresce o risco de coletar antes da atualização da fonte. |
| Regra condicional: aceitar a coleta antes das 20h só para recuperar o dia anterior que estiver faltando | Duas regras de data, mais difíceis de testar e de auditar; a regra do ciclo é uma só e vale para qualquer execução. |
| Agendador externo disparando `workflow_dispatch` | Exige token pessoal guardado num serviço de terceiro (RNF-08) e mais um serviço a manter. |
| Cron de hora em hora | Muitas execuções vazias poluem o histórico; dois horários bem separados cobrem os atrasos observados. |
| Consultar a data de atualização da fonte antes de gravar | Uma requisição a mais por execução, sem contrato especificado; fica como condição de revisão. |

## Decisão e táticas

A data de referência é calculada por uma única função pura: até 19h59min59s UTC, ela é a data UTC do momento menos um dia; a partir das 20h00 UTC, é a data UTC do momento. A hora de virada (20) é o parâmetro `hora_virada_ciclo_utc` de `config/parametros.toml`. A recusa por horário deixa de existir, e o código 2 fica só para destino inexistente. A guarda de duplicidade por arquivo continua igual e é conferida antes de qualquer requisição. A janela da PTAX e do CDI termina na data de referência. O workflow tem dois crons: `30 20 * * *` (principal, 30 min depois da atualização da fonte) e `30 6 * * *` (reserva, 10 h depois do principal e 13h30min antes do fim do ciclo).

| Tática | Atributo de qualidade | Como aparece |
|---|---|---|
| Redundância de agendamento | Disponibilidade | Duas execuções por ciclo; a reserva cobre atraso ou descarte da principal. |
| Ponto único de cálculo da data | Correção, testabilidade | Uma função pura com testes de fronteira (19h59, 20h00, 00h59). |
| Verificação de existência antes da requisição | Uso responsável da fonte | A segunda execução do ciclo termina com zero requisições. |
| Margem depois da atualização da fonte | Correção | O principal fica às 20h30, não às 20h00. |
| Controle de concorrência | Integridade | O grupo de concorrência existente serializa principal e reserva. |

## Consequências positivas

- Um atraso de até cerca de 23 h da execução principal não perde o dia.
- Um disparo manual pode recuperar a data de referência até as 20h UTC do dia seguinte.
- Nenhum serviço, secret ou requisição a mais em ciclo já coletado.

## Consequências negativas

- A `data` deixa de ser a data do calendário UTC da execução: o commit da `dados-raw` pode ter carimbo de D+1 com `data=D`, e quem lê o bruto precisa conhecer a regra das Definições.
- Um disparo manual entre 00h e 20h UTC grava a data do dia anterior, o que pode surpreender quem dispara.
- O histórico do Actions tem duas execuções por dia, e a conferência do RNF-13 precisa agrupar por ciclo.

## Riscos

| Risco | Mitigação |
|---|---|
| Uma coleta logo depois das 20h UTC, antes de a fonte de fato atualizar, grava o preço do ciclo anterior como `data=D`. A guarda impede uma recoleta, e o bruto não é corrigido. | Principal às 20h30; disparo manual só a partir das 20h30 UTC. Horário real de atualização da fonte: hipótese: validação pendente (comparar `prices.json` de dias seguidos; preços idênticos em todos os itens indicam coleta antiga, registrada como pendência). |
| Principal e reserva atrasam até depois das 20h UTC de D+1 | O dia vai para "Dias sem coleta", com o motivo. |
| Principal e reserva rodam ao mesmo tempo | Grupo de concorrência e criação exclusiva de arquivo; a segunda execução sai com zero requisições. |

## Evidência necessária

- Diagnóstico das execuções #2 e #3 (`docs/evidencias/T-57_diagnostico.txt`).
- Testes de unidade: 2026-11-05T00:59Z, 2026-11-04T20:30Z e 2026-11-05T19:59Z → `data=2026-11-04`; 2026-11-05T20:00Z → `data=2026-11-05`; arquivos da data de referência existentes → zero requisições; janela da PTAX e do CDI até a data de referência (T-57).
- Teste do workflow com os dois crons (T-57).
- Histórico do agendador com execuções da reserva (T-52).

## Condição de revisão

- Se principal e reserva atrasarem com frequência a ponto de perder ciclos.
- Se o horário de atualização do TCGCSV mudar, ou se a validação mostrar preço antigo em coletas das 20h30.
