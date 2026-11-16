# T-52 – Histórico do agendador, tabela "Dias sem coleta" e requisições ao TCGCSV [RNF-12, RNF-13]

- **Executor:** autor (coleta dos dados no GitHub); agente (análise e registro)
- **Data e hora da coleta dos dados:** 2026-11-16, por volta das 23h30 UTC
- **Local:** Codespace, em /workspaces/dcs-2026-projeto
- **Registro:** feito pelo agente a partir dos arquivos que o autor salvou em `/tmp/t52/`. O agente não executou `gh`, `git fetch` nem `make`, não leu o `.env` e não acessou a rede, o data lake nem o MinIO.

## Arquivos analisados

| arquivo | origem (comando executado pelo autor) |
|---|---|
| `runs.txt`, `runs.json` | `gh run list --workflow coleta.yml --limit 100` (29 execuções; o JSON tem databaseId, event, status, conclusion, createdAt, startedAt, updatedAt e displayTitle) |
| `log_<id>.txt` (29 arquivos) | `gh run view <id> --log`, um por execução |
| `cobertura.txt` | `make cobertura` |

## Conferência de credenciais nos logs

Antes de citar qualquer trecho, os 29 logs foram varridos com `grep -iE` por `MINIO_ACCESS`, `MINIO_SECRET`, `MINIO_ENDPOINT`, `access_key`, `secret`, `password`, `senha`, `token`, `authorization`, `AKIA` e `x-access-token`, por URLs com `usuário@host` e por sequências longas parecidas com chaves. Resultado: nenhum valor de credencial. Todas as ocorrências estão mascaradas:

| linha (sem o carimbo de hora) | ocorrências |
|---|---|
| `token: ***` | 87 |
| `AUTHORIZATION: basic ***` (extraheader do checkout) | 58 |
| `MINIO_ENDPOINT: ***`, `MINIO_ACCESS_KEY: ***`, `MINIO_SECRET_KEY: ***` | 20 cada |
| `cliente MinIO: endpoint=*** bucket=tcg secure=True` | 20 |

As sequências longas encontradas são SHAs de commits e de actions e hashes `sha256` dos arquivos do bruto. O traceback da execução 43656334396 (`InvalidAccessKeyId`) também não mostra nenhum valor.

## Critérios usados na tabela

- **Início (UTC):** `startedAt` do `runs.json` (igual a `createdAt` nas 29 execuções).
- **Horário agendado de referência:** o log e o `gh run list` não dizem qual cron disparou a execução. Foi usado o horário agendado (`30 20 * * *` ou `30 6 * * *`) imediatamente anterior ao início. O cron de reserva das 06h30 UTC existe desde a T-57 (commit `f61936f`, 2026-11-05T01:30Z); antes dele só havia o das 20h30 UTC.
- **Atraso:** início menos horário agendado, truncado em minutos.
- **Data de referência gravada:** valor de `data=` na linha `coleta iniciada` do log (ADR-007).
- **Arquivos novos:** linhas `bruto gravado`. **Pulados:** linhas `fonte pulada sem requisição` (arquivo da data de referência já existia na `dados-raw`).
- **Requisições ao TCGCSV:** linhas `requisição ok` ou `requisição falhou` com `fonte=tcgcsv_*`. O contador `requisicoes=` do coletor também inclui as requisições ao BCB; ele aparece na coluna "total do coletor".
- **Sync:** linha `sincronização encerrada: enviados=… recusados=… fora_do_escopo=… falhas=…`, no formato enviados/recusados/falhas (fora_do_escopo foi 0 em todas). "não consta" quando a linha não existe no log.

## Tabela de execuções

Em ordem cronológica. P = principal (20h30 UTC), R = reserva (06h30 UTC).

| # | id | evento | início (UTC) | agendado de referência | atraso | conclusão | data gravada | novos | pulados | req. TCGCSV | total do coletor | sync (env./rec./falhas) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 41715282582 | workflow_dispatch | 2026-11-03 20:44:07 | — | — | success | 2026-11-03 | 4 | 0 | 2 | 4 | não consta (passo ainda não existia) |
| 2 | 41749386966 | schedule | 2026-11-04 00:46:59 | P 03/11 20:30 | 4h16 | failure | não consta | 0 | 0 | 0 | não consta | não consta (passo ainda não existia) |
| 3 | 41945358536 | schedule | 2026-11-05 00:59:30 | P 04/11 20:30 | 4h29 | failure | não consta | 0 | 0 | 0 | não consta | não consta (passo ainda não existia) |
| 4 | 41949048376 | workflow_dispatch | 2026-11-05 01:31:03 | — | — | success | 2026-11-04 | 4 | 0 | 2 | 4 | não consta (passo ainda não existia) |
| 5 | 42049314709 | schedule | 2026-11-05 14:52:55 | R 05/11 06:30 | 8h22 | success | 2026-11-04 | 0 | 4 | 0 | 0 | não consta (passo ainda não existia) |
| 6 | 42141078908 | schedule | 2026-11-06 01:02:25 | P 05/11 20:30 | 4h32 | success | 2026-11-05 | 4 | 0 | 2 | 4 | não consta (passo ainda não existia) |
| 7 | 42234589115 | schedule | 2026-11-06 14:30:54 | R 06/11 06:30 | 8h00 | success | 2026-11-05 | 0 | 4 | 0 | 0 | não consta (passo ainda não existia) |
| 8 | 42316776975 | schedule | 2026-11-07 00:12:16 | P 06/11 20:30 | 3h42 | success | 2026-11-06 | 4 | 0 | 2 | 4 | não consta (passo ainda não existia) |
| 9 | 42376988567 | schedule | 2026-11-07 13:26:43 | R 07/11 06:30 | 6h56 | success | 2026-11-06 | 0 | 4 | 0 | 0 | não consta (passo ainda não existia) |
| 10 | 42393032552 | workflow_dispatch | 2026-11-07 16:47:11 | — | — | success | 2026-11-06 | 0 | 4 | 0 | 0 | 0/16/0 |
| 11 | 42426928440 | schedule | 2026-11-07 23:48:49 | P 07/11 20:30 | 3h18 | success | 2026-11-07 | 4 | 0 | 2 | 4 | 4/16/0 |
| 12 | 42486561591 | schedule | 2026-11-08 13:46:42 | R 08/11 06:30 | 7h16 | success | 2026-11-07 | 0 | 4 | 0 | 0 | 0/20/0 |
| 13 | 42537288925 | schedule | 2026-11-08 23:52:58 | P 08/11 20:30 | 3h22 | failure | 2026-11-08 | 3 | 0 | 2 | 4 | 3/20/0 |
| 14 | 42657979297 | schedule | 2026-11-09 16:45:30 | R 09/11 06:30 | 10h15 | success | 2026-11-08 | 1 | 3 | 0 | 1 | 1/23/0 |
| 15 | 42745500869 | schedule | 2026-11-10 02:50:41 | P 09/11 20:30 | 6h20 | success | 2026-11-09 | 4 | 0 | 2 | 4 | 4/24/0 |
| 16 | 42841325046 | schedule | 2026-11-10 15:08:56 | R 10/11 06:30 | 8h38 | success | 2026-11-09 | 0 | 4 | 0 | 0 | 0/28/0 |
| 17 | 42933962336 | schedule | 2026-11-11 00:46:23 | P 10/11 20:30 | 4h16 | success | 2026-11-10 | 4 | 0 | 2 | 4 | 4/28/0 |
| 18 | 43040562687 | schedule | 2026-11-11 14:39:24 | R 11/11 06:30 | 8h09 | success | 2026-11-10 | 0 | 4 | 0 | 0 | 0/32/0 |
| 19 | 43138059531 | schedule | 2026-11-12 01:57:47 | P 11/11 20:30 | 5h27 | success | 2026-11-11 | 4 | 0 | 2 | 4 | 4/32/0 |
| 20 | 43248744317 | schedule | 2026-11-12 15:31:39 | R 12/11 06:30 | 9h01 | success | 2026-11-11 | 0 | 4 | 0 | 0 | 0/36/0 |
| 21 | 43344165719 | schedule | 2026-11-13 01:20:24 | P 12/11 20:30 | 4h50 | success | 2026-11-12 | 4 | 0 | 2 | 4 | 4/36/0 |
| 22 | 43446451285 | schedule | 2026-11-13 14:49:39 | R 13/11 06:30 | 8h19 | success | 2026-11-12 | 0 | 4 | 0 | 0 | 0/40/0 |
| 23 | 43537637304 | schedule | 2026-11-14 00:58:23 | P 13/11 20:30 | 4h28 | success | 2026-11-13 | 4 | 0 | 2 | 4 | 4/40/0 |
| 24 | 43601254185 | schedule | 2026-11-14 13:44:15 | R 14/11 06:30 | 7h14 | success | 2026-11-13 | 0 | 4 | 0 | 0 | 0/44/0 |
| 25 | 43656334396 | schedule | 2026-11-15 00:04:12 | P 14/11 20:30 | 3h34 | failure | 2026-11-14 | 4 | 0 | 2 | 4 | não consta (falha `InvalidAccessKeyId` antes do envio) |
| 26 | 43722603998 | workflow_dispatch | 2026-11-15 14:07:19 | — | — | success | 2026-11-14 | 0 | 4 | 0 | 0 | 0/48/0 |
| 27 | 43723243198 | schedule | 2026-11-15 14:14:11 | R 15/11 06:30 | 7h44 | success | 2026-11-14 | 0 | 4 | 0 | 0 | 0/48/0 |
| 28 | 43778769235 | schedule | 2026-11-16 00:10:15 | P 15/11 20:30 | 3h40 | success | 2026-11-15 | 4 | 0 | 2 | 4 | 4/48/0 |
| 29 | 43905874560 | schedule | 2026-11-16 16:17:36 | R 16/11 06:30 | 9h47 | success | 2026-11-15 | 0 | 4 | 0 | 0 | 0/52/0 |

### Execuções com falha

| id | motivo no log | efeito |
|---|---|---|
| 41749386966, 41945358536 | `coleta recusada: … é antes de 20h UTC; nenhuma requisição enviada`, código 2. Era a guarda anterior à T-57, que exigia a mesma data civil depois das 20h UTC. | Nenhuma requisição, nada gravado nem publicado. Corrigido pela T-57 (data de referência pelo ciclo, ADR-007). |
| 42537288925 | `requisição falhou sem repetição: fonte=bcb_cdi … status=…` e `coleta encerrada com falha: 1 de 4 arquivos pendentes falharam (bcb_cdi/cdi.json)`, código 1. | Os 3 arquivos que deram certo foram publicados (`dados(coleta): 2026-11-08`) e enviados (3/20/0). O `cdi.json` de 08/11 foi gravado pela reserva 42657979297, com uma requisição ao BCB e nenhuma ao TCGCSV. |
| 43656334396 | No passo de sincronização: `minio.error.S3Error: … code: InvalidAccessKeyId`, código 1. Coletor com código 0. | O bruto de 14/11 foi gravado e publicado na `dados-raw` (`dados(coleta): 2026-11-14`). Foi a troca do endpoint e das credenciais do data lake da turma em 15/11 (`docs/evidencias/T-58_troca_endpoint.txt`). Nas execuções 43722603998 e 43723243198 o sync recusou as 48 chaves por já existirem. Os logs não mostram quem enviou os arquivos de 14/11 ao novo endpoint. Segundo o autor, ele rodou `make sync` em 15/11, antes das 14h04 UTC, mas a saída dessa execução não foi guardada, e o resultado dela não consta. |

## Totais

| medida | valor |
|---|---|
| execuções | 29 |
| schedule | 25 (13 principais, 12 reservas) |
| workflow_dispatch | 4 (41715282582: primeira coleta, T-12; 41949048376: recuperação de 04/11, T-57; 42393032552: primeiro sync no Actions, T-58; 43722603998: sync depois da troca de endpoint, T-58) |
| conclusão | 25 success, 4 failure |
| atraso das agendadas (25) | média 6h14min47s; máximo 10h15min30s (42657979297, reserva de 09/11); mínimo 3h18min49s (42426928440) |
| atraso das principais (13) | média 4h20min05s; máximo 6h20min41s (42745500869) |
| atraso das reservas (12) | média 8h19min02s; máximo 10h15min30s (42657979297) |
| horários agendados no período | 26 (13 das 20h30 UTC, de 03/11 a 15/11; 13 das 06h30 UTC, de 05/11 a 16/11), 25 executados. A reserva de 05/11 06:30 é a 42049314709, e nenhum horário ficou sem execução. |
| execuções sem nenhuma requisição | 15: 13 com todos os arquivos já presentes (11 reservas e as manuais 42393032552 e 43722603998; `coleta encerrada: todos os arquivos da data de referência já existem; requisicoes=0`) e 2 recusadas pela guarda antiga (41749386966 e 41945358536) |
| execuções sem requisição ao TCGCSV | 16: as 15 acima e a reserva 42657979297, que só fez 1 requisição ao BCB |
| execuções com requisição ao TCGCSV | 13, cada uma com exatamente 2 (products e prices, `status=200 tentativa=1/4`, sem repetição) |
| total de requisições ao TCGCSV | 26 (mais 27 ao BCB, total do coletor: 53) |
| máximo de requisições ao TCGCSV por data de referência | 2 (em cada uma das 13 datas) |
| máximo de requisições ao TCGCSV num dia civil UTC | 4, em 2026-11-07 (42316776975 às 00:12 e 42426928440 às 23:48, datas de referência 06/11 e 07/11) |
| limite (`config/parametros.toml`, `limite_requisicoes_dia`) | 10000. O máximo observado (4) é 0,04% do limite (RNF-12). |

## Conferência por data de referência (RNF-13)

`cobertura.txt` (saída de `make cobertura` executado pelo autor às 23:29 UTC de 16/11):

```text
2026-11-16T23:29:02Z INFO tcg.sync.leitor_branch: arquivos em origin/dados-raw:raw/: 52
2026-11-16T23:29:02Z INFO __main__: cobertura: 13 datas, 0 faltantes
periodo: 2026-11-03 a 2026-11-15 (13 datas)
resumo: 13 datas, 13 com bruto, 0 registradas, 0 faltantes
```

| data | execução(ões) que gravaram o bruto | execução bem-sucedida dentro do ciclo (das 20h UTC de D às 20h UTC de D+1) | cobertura.txt |
|---|---|---|---|
| 2026-11-03 | 41715282582 (manual, primeira coleta, T-12) | 41715282582 | bruto |
| 2026-11-04 | 41949048376 (manual, recuperação, T-57) | 41949048376; 42049314709 (reserva) | bruto |
| 2026-11-05 | 42141078908 | 42141078908; 42234589115 | bruto |
| 2026-11-06 | 42316776975 | 42316776975; 42376988567; 42393032552 | bruto |
| 2026-11-07 | 42426928440 | 42426928440; 42486561591 | bruto |
| 2026-11-08 | 42537288925 (3 arquivos) e 42657979297 (`cdi.json`) | 42657979297 | bruto |
| 2026-11-09 | 42745500869 | 42745500869; 42841325046 | bruto |
| 2026-11-10 | 42933962336 | 42933962336; 43040562687 | bruto |
| 2026-11-11 | 43138059531 | 43138059531; 43248744317 | bruto |
| 2026-11-12 | 43344165719 | 43344165719; 43446451285 | bruto |
| 2026-11-13 | 43537637304 | 43537637304; 43601254185 | bruto |
| 2026-11-14 | 43656334396 (bruto publicado, sync falhou) | 43722603998 (manual); 43723243198 (reserva) | bruto |
| 2026-11-15 | 43778769235 | 43778769235; 43905874560 | bruto |

Conclusões:

- Cada data de 03/11 a 15/11 tem pelo menos uma execução que gravou o bruto e pelo menos uma execução bem-sucedida dentro do seu ciclo. Isso bate com o `cobertura.txt` (13 datas, 13 com bruto, 0 faltantes; 52 arquivos = 13 × 4 na `dados-raw`) e com a tabela "Dias sem coleta" do README, que está vazia (0 registradas).
- 2026-11-04 foi recuperado pela execução manual 41949048376 (2026-11-05T01:31Z, dentro do ciclo), registrada na T-57 (`docs/evidencias/T-57_recuperacao.txt`). As agendadas do ciclo de 03/11 e 04/11 (41749386966 e 41945358536) foram recusadas pela guarda antiga, antes da T-57.
- Ressalva do RNF-13 ("sem intervenção manual"): 03/11 e 04/11 foram gravados por execuções manuais. De 05/11 a 15/11, todas as datas foram gravadas por execuções agendadas. As duas execuções manuais seguintes (42393032552 e 43722603998) não gravaram bruto: só testaram o sync.
- 2026-11-16 ainda não tinha sido coletado na hora da conferência (cerca de 23h30 UTC de 16/11). A execução principal desse ciclo (20h30 UTC de 16/11) ainda não tinha rodado. A última execução da lista (43905874560, 16:17 UTC) é a reserva do ciclo de 15/11. O atraso máximo das principais no período foi de 6h20min41s. O ciclo de 16/11 vai até as 20h UTC de 17/11, e a cobertura dessa data fica para uma conferência posterior.

## R-02: agendamento ativo

- Última execução agendada: 43905874560, evento `schedule`, início em 2026-11-16T16:17:36Z, concluída com `success` (reserva de 16/11 06:30 UTC).
- Na data da conferência (2026-11-16) o agendamento do workflow `coleta` estava ativo. Houve execuções `schedule` todos os dias de 04/11 a 16/11, e nenhum dos 26 horários agendados do período ficou sem execução.
- Prazo do projeto: 12/12/2026, menos de 60 dias depois da última atividade no repositório (README, R-02).

## Resultado

- RNF-12: atendido. No máximo 4 requisições ao TCGCSV num dia civil UTC e 2 por data de referência, contra o limite de 10000.
- RNF-13: cada data de referência de 03/11 a 15/11 tem execução bem-sucedida dentro do ciclo, e não há data sem bruto, por isso a tabela "Dias sem coleta" continua vazia. Ressalva: 03/11 e 04/11 dependeram de execução manual. A data de 16/11 ainda estava dentro do ciclo e não foi conferida.
