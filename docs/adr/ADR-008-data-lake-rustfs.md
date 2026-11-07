# ADR-008: Data lake da turma no RustFS

## Status

Aceito em 2026-11-07. Substitui partes do ADR-001 e do ADR-002:
- ADR-001: deixam de valer o destino do Sincronizador (MinIO local), a força "Escopo de escrita", o descarte da alternativa "Gravar direto no MinIO da turma", a tática "Limitar exposição" na forma "o workflow não usa nenhum secret", a consequência positiva "Nenhum secret no agendador" e a evidência "nenhum `secrets.`" do teste do workflow. Continuam valendo a branch `dados-raw` como fonte de verdade do bruto, o commit `dados(coleta)` e o push só nessa branch.
- ADR-002: deixa de valer o papel do MinIO local como ambiente de trabalho de silver, gold e painel, inclusive o cenário do RF-05 em `localhost:9000`. Continuam valendo a imagem, a tag fixada, o healthcheck e o uso da mesma imagem nos testes de integração.

## Contexto e forças

O bucket `tcg` da turma passou a ser servido por um RustFS compatível com S3, em `https://s3.afonsolelis.tech` (região `us-east-1`, endereçamento por caminho), acessado por uma única credencial compartilhada pela turma, com permissão de administrador. A condição de revisão do ADR-001 ("se for disponibilizado o endpoint da API S3 ... reavaliar") foi atingida. Em 2026-11-07, o autor apontou o `.env` para o RustFS e rodou `make sync` com o mesmo código e as mesmas variáveis: 16 arquivos enviados, 0 recusados, 0 fora do escopo, 0 falhas (`docs/evidencias/T-58_primeira_sync_rustfs.txt`).

Forças em jogo:
- **Outras coleções** (RF-10, RF-17, RF-22, RF-28, RES-13): as silvers e a gold_turma dos colegas só existem no bucket da turma; no MinIO local, P3 a P5 e o placar ficam sempre no aviso de falta de dados.
- **Publicação da gold_turma** (RF-26): o contrato existe para ser lido pela turma.
- **Bruto atualizado sem intervenção** (RNF-13, OBJ-01): hoje o lake só recebe o bruto quando o autor roda `make sync`.
- **Segredos fora do Git** (RNF-08, RES-06): a credencial é compartilhada e de administrador; um vazamento atinge a turma inteira.
- **Escrita isolada** (RNF-03, RES-08): a credencial não restringe prefixo; o isolamento depende só do código.
- **Bruto imutável** (RF-02, RF-05) e **testabilidade** (RNF-07): os testes não podem tocar o lake da turma.
- **Custo zero** (RNF-09): o servidor é da turma, sem custo para o projeto.

## Requisitos e cenários relacionados

| Requisito | Cenário que esta decisão precisa atender |
|---|---|
| RF-05 | Depois do push do dia na `dados-raw`, o passo de sincronização envia ao RustFS os arquivos ausentes e recusa as chaves existentes; uma nova execução só registra recusas. |
| RF-10, RF-22, RF-28 | A gold e o placar leem silvers e gold_turma de outras coleções no bucket da turma, somente para leitura; sem elas, aparece o aviso. |
| RF-26 | A gold_turma da DRI fica em `gold_turma/carteira/group_id=24269/` no bucket da turma. |
| RNF-03 | Nenhuma chave fora dos prefixos com `group_id=24269` é criada, alterada ou apagada no bucket da turma. |
| RNF-07 | Os testes de integração sobem um MinIO descartável com a imagem do ADR-002 e não tocam o RustFS nem o MinIO local. |
| RNF-08 | Endpoint e credenciais ficam só no `.env` e em secrets do GitHub; o workflow os lê só no `env` do passo de sincronização, sem `echo`; a busca no histórico e nos logs não encontra nada. |
| RNF-13 | Em cada ciclo em que a coleta termina com código 0 ou 1, o bruto do dia chega ao RustFS no mesmo job, sem intervenção. |

## Alternativas consideradas

| Alternativa | Por que foi descartada |
|---|---|
| Manter só o `make sync` manual | O lake fica atrás da branch até o autor rodar o comando; a gold e os colegas leem um bruto incompleto; volta a depender do autor todo dia, o que o ADR-001 evitou para a coleta (RNF-13). Continua disponível como recuperação. |
| Workflow gravando direto no RustFS, sem a branch | O bruto passaria a existir só num servidor de terceiros com credencial de administrador compartilhada: um erro de qualquer colega o apagaria sem cópia para reconstruir. A guarda de duplicidade passaria a depender do lake no momento da coleta, e uma indisponibilidade do RustFS perderia o dia do TCGCSV, que não se recupera (DRV-01). |
| Continuar no MinIO local | As outras coleções não existem nele (RF-17, RF-22, RF-28 sempre no aviso); a gold_turma não chega à turma (RF-26); o volume some com o Codespace. |
| Renomear as variáveis para `S3_*` | Muda configuração, compose, DuckDB, testes, secrets e o `.env` já preenchido, sem ganho funcional. Os nomes `MINIO_*` ficam e passam a significar "qualquer servidor compatível com S3". |
| Credencial própria restrita ao prefixo `group_id=24269` | Seria a melhor proteção, mas não está disponível: a turma recebeu uma única credencial. Fica como condição de revisão. |

## Decisão e táticas

O bucket `tcg` do RustFS da turma (`https://s3.afonsolelis.tech`, `us-east-1`, endereçamento por caminho, TLS) passa a ser o armazenamento oficial de bruto, silver, gold e gold_turma. A branch `dados-raw` continua como fonte de verdade do bruto: o Coletor diário grava só nela, e o lake recebe uma cópia sem sobrescrita.

O workflow da coleta ganha o passo "sincronizar com o data lake da turma", depois do commit e do push na `dados-raw`. Ele roda o mesmo Sincronizador do `make sync` (`python -m tcg.sync.sincronizador --repo ../dados`) sempre que o coletor termina com código 0 ou 1, com ou sem arquivo novo, e só se o passo de publicação tiver dado certo. `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY` e `MINIO_SECRET_KEY` vêm de secrets do repositório, criados pelo autor no site do GitHub, e aparecem só no `env` desse passo; `MINIO_SECURE=true`, `MINIO_BUCKET=tcg` e `GROUP_ID=24269` são literais. Uma falha no passo marca o job como falho; o push já feito na `dados-raw` não é desfeito, e o ciclo seguinte reenvia o que faltar.

No Codespace, `make sync`, `make silver` e `make gold` usam o `.env` apontado para o RustFS. O MinIO local (ADR-002) passa a ser só desenvolvimento, apontado pelo `.env`; os testes de integração seguem com o MinIO descartável da mesma imagem. As variáveis `MINIO_*` mantêm o nome e apontam para qualquer servidor compatível com S3; o código (SDK `minio`; DuckDB com httpfs, endereçamento por caminho, região `us-east-1` e SSL conforme `MINIO_SECURE`) não muda.

| Tática | Atributo de qualidade | Como aparece |
|---|---|---|
| Vínculo em tempo de configuração | Modificabilidade | Trocar entre MinIO local e RustFS muda só o `.env` ou os secrets, sem código (primeira sync). |
| Limitar exposição | Segurança | Secrets só no `env` de um passo, nunca interpolados em `run`, sem `echo` e sem `set -x`; coletor e push não recebem a credencial; o mascaramento do Actions é uma segunda camada. |
| Validação de chave antes da escrita | Integridade | O Sincronizador recusa chave fora de `raw/<fonte>/group_id=24269/` antes do SDK; silver e gold gravam só pela Guarda de prefixo, que é também a única função de exclusão. |
| Verificação de existência antes da gravação | Integridade | `stat_object` antes do `put_object`; hash conferido depois do envio. |
| Fonte de verdade fora do lake | Recuperabilidade | A branch reconstrói o bruto no lake por `make sync` ou pelo passo do dia seguinte. |
| Reexecução idempotente | Disponibilidade | O passo roda mesmo sem arquivo novo; a falha de um dia se corrige no ciclo seguinte. |
| Isolamento de falhas | Disponibilidade | O passo vem depois do push; uma falha do lake não impede a coleta nem o versionamento do bruto. |

## Consequências positivas

- O bruto chega ao lake da turma todo dia, sem intervenção do autor.
- A gold lê outras coleções reais, e a gold_turma da DRI fica visível para a turma.
- Nenhuma mudança no código Python: só workflow, `.env.example` e documentação.
- O lake não depende do Codespace ligado nem do volume local.
- Os testes continuam isolados do lake da turma.

## Consequências negativas

- O workflow deixa de ser livre de secrets; o pior vazamento possível passa a ser a credencial de administrador da turma, não só o `GITHUB_TOKEN` efêmero.
- Dependência de um servidor de terceiro: disponibilidade, TLS, versão do RustFS e compatibilidade S3. Com o SDK `minio`, confirmada na primeira sync e no passo do workflow; com o httpfs do DuckDB, validada em 2026-11-07 na primeira silver e gold contra o RustFS (`docs/evidencias/T-58_silver_gold_rustfs.txt`).
- O bruto continua em dois lugares, e o lake pode ficar um ciclo atrás quando o passo falha.
- O job pode ficar vermelho por causa do lake com a coleta perfeita; a conferência do RNF-13 precisa olhar o passo da coleta separado do passo da sincronização.
- No lake, a imutabilidade do nosso bruto depende de todos os colegas: qualquer um com a mesma credencial pode alterar ou apagar objetos do nosso prefixo. O Sincronizador recria o que estiver ausente, mas não detecta alteração.
- O mesmo `.env` serve a desenvolvimento e produção: esquecer o endpoint apontado para o RustFS grava resultados de desenvolvimento no lake (ainda que só no prefixo da DRI).

## Riscos

| Risco | Mitigação |
|---|---|
| A credencial é compartilhada e de administrador; a guarda de prefixo é a única proteção dos dados dos colegas. Um erro de prefixo apaga ou sobrescreve dados de outra coleção. | Guarda de prefixo como único ponto de escrita e exclusão fora de `raw/`, com testes de recusa (RNF-03); o Sincronizador valida a chave antes do SDK; o agente é proibido de excluir e de usar a credencial; `make reprocessar` só pelo autor; pipeline completo testado contra MinIO descartável (T-34). |
| O workflow passa a usar secrets: vazamento por log, por passo novo, por action de terceiro ou por pull request. | Secrets só no `env` de um passo, nunca dentro de `run`, conferido pelo teste do workflow; sem gatilho `pull_request`; só actions oficiais; mascaramento do GitHub. Vazamento: parar, avisar o autor e pedir a rotação da chave ao responsável pelo lake. |
| Rotação da chave da turma. | O passo falha e o job fica vermelho; o autor atualiza o `.env` e os secrets; o ciclo seguinte reenvia o que faltar. |
| RustFS fora do ar ou lento. | O passo vem depois do push; o bruto fica na branch; o ciclo seguinte ou um `make sync` completam o lake. |
| Um terceiro altera ou apaga o nosso bruto no lake. | A branch é a fonte de verdade; `make sync` recria o que falta; detecção de alteração na condição de revisão. |
| Silver ou gold de desenvolvimento gravadas no lake por engano. | Prefixos só da DRI, chaves determinísticas, reconstruídas por `make silver` e `make gold`; o README explica como apontar o `.env` para o MinIO local. |
| Diferenças de compatibilidade S3 do RustFS (região, endereçamento, listagem). | Região e endereçamento por caminho fixados; primeira sync com hashes conferidos; evidência da primeira silver e gold contra o RustFS. |

## Evidência necessária

- Primeira sincronização manual com o RustFS: 16 enviados, 0 falhas (`docs/evidencias/T-58_primeira_sync_rustfs.txt`).
- Teste do workflow (T-58): passo depois do push, condição 0 ou 1 e publicação bem-sucedida, secrets só no `env` desse passo e nunca em `run`, `MINIO_SECURE=true`, nenhum `continue-on-error`, nenhum `echo` de `MINIO_*` nem `set -x`.
- Suíte completa (`docs/evidencias/T-58_suite.txt`).
- Sincronização pelo workflow: validada em 2026-11-07 na execução coleta #10 (disparo manual), com o passo de sincronização concluído e enviados=0, recusados=16, falhas=0 (`docs/evidencias/T-58_sync_actions.txt`).
- Silver e gold pelo DuckDB no RustFS: validadas em 2026-11-07 com `make silver` (1784 preços, 281 produtos, quarentena 0) e `make gold` (4 dias, só a DRI), executados pelo autor (`docs/evidencias/T-58_silver_gold_rustfs.txt`).
- Busca de credenciais no histórico e nos logs do Actions incluindo a chave da turma (T-51).

## Condição de revisão

- Se a turma receber credenciais individuais restritas ao prefixo.
- Se o RustFS ficar indisponível com frequência a ponto de deixar o lake mais de um ciclo atrás da branch.
- Se aparecer alteração do nosso bruto no lake: acrescentar ao Sincronizador a conferência de hash das chaves existentes.
