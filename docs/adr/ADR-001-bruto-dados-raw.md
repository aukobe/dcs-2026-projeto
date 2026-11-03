# ADR-001: Bruto versionado na branch dados-raw com sincronização para o MinIO local

## Status

Aceito em 2026-11-03.

## Contexto e forças

A coleção DRI (groupId 24269) precisa de uma série diária contínua de preços. Um dia sem coleta não se recupera depois, porque o TCGCSV só devolve o preço do dia (DRV-01). Por isso a coleta tem de rodar todo dia depois das 20h UTC, sem depender de alguém ligar uma máquina (RNF-13).

Forças em jogo:
- **Custo zero** (RES-02, RNF-09): nenhum serviço pago, nem por trial.
- **Segredos fora do Git** (RES-06, RNF-08): o repositório é público; quanto menos credenciais o agendador tiver, menor a exposição.
- **Bruto imutável e byte a byte** (RES-08, RF-02, RNF-03): nada em `raw/` é sobrescrito, apagado ou convertido.
- **Execução no Codespace com MinIO local** (RES-07): silver, gold e painel rodam a partir do MinIO local, que só existe enquanto o Codespace está ligado e pode perder o volume.
- **Rastreabilidade** (DRV-06): cada número do painel precisa voltar até a resposta original.
- **Escopo de escrita**: o projeto não tem acesso à API S3 do MinIO da turma, e a orientação recebida foi usar o MinIO local.

## Requisitos e cenários relacionados

| Requisito | Cenário que esta decisão precisa atender |
|---|---|
| RF-01 | Depois das 20h UTC, a coleta grava as quatro respostas do dia (`products`, `prices`, `cotacao`, `cdi`). |
| RF-02 | Gravar de novo a chave do dia é recusado; o hash do bruto é igual ao hash do corpo HTTP. |
| RF-04 | Antes das 20h UTC, ou com o bruto do TCGCSV já gravado no dia, nenhuma requisição sai. |
| RF-05 | A sincronização não regrava chave existente no MinIO e copia os arquivos novos com o hash da origem. |
| RNF-03 | O pipeline completo não cria nem altera chave fora de `group_id=24269` e não muda o hash de nenhum objeto do bruto. |
| RNF-08 | Busca por credenciais no histórico e nos logs não encontra nada. |
| RNF-09 | Todos os serviços listados no README são gratuitos no uso do projeto. |
| RNF-13 | Há uma execução por dia depois das 20h UTC; cada dia sem execução bem-sucedida está na tabela "Dias sem coleta" do README. |

## Alternativas consideradas

| Alternativa | Por que foi descartada |
|---|---|
| MinIO publicado no Railway | O trial tem crédito único de US$ 5 por 30 dias e o plano gratuito não sustenta um serviço ligado o tempo todo (RES-02); o volume é apagado após o fim dos créditos. Além disso, o workflow precisaria de credencial do MinIO em secret (RNF-08). |
| Gravar direto no MinIO da turma | O endpoint da API S3 não está disponível para o projeto, e a orientação recebida foi usar o MinIO local. |
| Armazenamento S3 gratuito de terceiros | Exige conta externa e credencial guardada em secret do Actions, o que aumenta a superfície de vazamento (RNF-08) e acrescenta um serviço a manter. |
| Agendador no computador do autor | Depende da máquina ligada e conectada todo dia depois das 20h UTC; um dia perdido não se recupera (DRV-01, RNF-13). |
| Artifacts do GitHub Actions | Expiram depois do prazo de retenção e não têm chave fixa: cada execução gera um artifact novo, sem caminho estável para o sincronizador ler. |
| Bruto na branch `main` | Mistura dados e código: o histórico da `main` cresce a cada dia, os commits automáticos poluem a revisão do código e o coletor precisaria de push na branch do código. |

## Decisão e táticas

O Coletor diário roda no GitHub Actions (cron `30 20 * * *` e `workflow_dispatch`) e grava cada resposta original como arquivo na branch órfã `dados-raw`, no caminho idêntico à chave do bruto (`raw/<fonte>/group_id=24269/data=AAAA-MM-DD/<arquivo>`). O commit usa `dados(coleta): AAAA-MM-DD [RF-01]` e o push vai só para essa branch. No Codespace, `make sync` lê a branch e envia ao bucket `tcg` do MinIO local cada arquivo ainda ausente, com a mesma chave.

| Tática | Atributo de qualidade | Como aparece |
|---|---|---|
| Limitar exposição | Segurança | O workflow não usa nenhum secret; tem só `contents: write` do `GITHUB_TOKEN`; `TCG_USER_AGENT` vem de `vars`. A credencial do MinIO fica só no `.env` do Codespace. |
| Persistência em armazenamento versionado | Durabilidade | Cada dia é um commit na `dados-raw`; o histórico do Git guarda o bruto fora do Codespace. |
| Verificação de existência antes da gravação | Integridade | O coletor confere o arquivo do dia antes de qualquer requisição (RF-04) e grava com criação exclusiva; o sincronizador faz `stat_object` antes do `put_object` (RF-05). |
| Preservação do formato original | Integridade | `.gitattributes` com `* -text` na branch; o sincronizador lê os blobs por `git cat-file`, sem checkout, e confere o hash. |
| Separação de dados e código | Modificabilidade | Branch órfã, sem histórico da `main`; criada uma única vez pelo autor. |
| Isolamento de falhas por fonte | Disponibilidade | TCGCSV, PTAX e CDI são verificados e gravados de forma independente; a falha de uma não descarta as outras. |
| Controle de concorrência | Integridade | Grupo de concorrência no workflow impede dois pushes simultâneos na branch. |
| Reconstrução a partir da fonte de verdade | Recuperabilidade | Se o volume do MinIO local se perder, `make sync` reconstrói o bruto a partir da branch. |

## Consequências positivas

- Custo zero: Actions e repositório público no GitHub, sem serviço pago (RNF-09).
- Nenhum secret no agendador; o pior vazamento possível do workflow é o `GITHUB_TOKEN` efêmero do job (RNF-08).
- O bruto sobrevive à perda do Codespace e do volume do MinIO local.
- Cada arquivo do bruto tem commit, data e mensagem rastreável até o RF-01 (DRV-06).
- O verificador de cobertura lê a branch, que é a fonte de verdade, e não o MinIO, que pode estar desatualizado.

## Consequências negativas

- O bruto existe em dois lugares (branch `dados-raw` e MinIO local) e o MinIO só fica atualizado depois de `make sync`; silver e gold rodadas sem sincronizar usam um bruto incompleto.
- Dependência do GitHub (disponibilidade do Actions e do repositório) e do horário do agendador, que pode atrasar ou descartar execuções em horário de carga.
- O repositório cresce a cada dia de coleta. Tamanho diário: hipótese: validação pendente na primeira coleta.
- A imutabilidade na branch é garantida pelo código e pelo processo, não pelo Git: um push manual na `dados-raw` poderia alterar o bruto. O sincronizador recusa sobrescrever o que já está no MinIO, mas não detecta a alteração sozinho.
- Agendamento no Actions só roda a partir da branch padrão, e o workflow fica na `main` enquanto os dados ficam na `dados-raw`: dois checkouts no mesmo job.

## Riscos

| Risco | Mitigação |
|---|---|
| Atraso ou falha do cron (se passar da meia-noite UTC, a data da coleta muda e o dia anterior se perde) | Disparo manual (`workflow_dispatch`) no mesmo dia, antes de 23h59 UTC; a reexecução busca só as fontes sem arquivo do dia; dia perdido vai para "Dias sem coleta". |
| Push concorrente na branch `dados-raw` | Grupo de concorrência no workflow; criação exclusiva de arquivo. |
| Alteração de bytes por conversão de fim de linha | `.gitattributes` com `* -text`; leitura pelos blobs; teste com `\r\n` e conferência de hash. |
| Workflow agendado desativado por inatividade do repositório | Workflow na `main`; o prazo (12/12/2026) é menor que o período de inatividade; conferir o histórico de execuções. |
| Perda do volume do MinIO local | `make sync` a partir da branch e `make reprocessar` para silver e gold. |

## Evidência necessária

- Branch publicada só com `.gitattributes` e `README.md`: `git ls-tree origin/dados-raw` (T-09).
- Teste do workflow: cron, disparo manual, concorrência, só `contents: write`, nenhum `secrets.` e push restrito à `dados-raw` (T-10).
- Primeira execução no Actions com os quatro arquivos do dia na branch e o commit no formato `dados(coleta): AAAA-MM-DD [RF-01]` (T-12).
- Tamanho dos arquivos do primeiro dia, para substituir a hipótese de crescimento (T-12/T-13).
- Leitor da branch devolvendo bytes idênticos, inclusive com `\r\n` (T-17); sincronizador recusando chave existente e enviando arquivo novo com o hash da origem (T-18, T-19).
- Busca por credenciais no histórico e nos logs sem resultado (RNF-08).

## Condição de revisão

- Se for disponibilizado o endpoint da API S3 do MinIO da turma, reavaliar a gravação direta nele.
- Reavaliar também se o crescimento medido do repositório se aproximar dos limites de tamanho do GitHub, ou se o agendador perder dias com frequência suficiente para comprometer o OBJ-01.
