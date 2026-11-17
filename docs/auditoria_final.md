# Auditoria final

- **Tarefa:** T-56 de `specs/tasks.md` (prompt 11.1 do enunciado da Aula 08).
- **Data:** 2026-11-17.
- **Executor:** agente, como auditor. Nada foi corrigido. Este é o único arquivo criado ou alterado.
- **Commit auditado:** `99d0f97` (`main`, árvore limpa no início da auditoria).
- **Fontes:** arquivos do repositório, histórico do git (`main` e a ref local `origin/dados-raw`), saída do pytest e evidências em `docs/evidencias/`. Lacunas que já estão em `docs/pendencias_aula08.md` citam o número P-xx.
- **Fora das fontes, por regra do `AGENTS.md`:** data lake da turma (RustFS), MinIO local e `.env`. Ver "Suposições" e "Comandos não executados".

## Resultado dos 14 itens

| # | Item | Estado | Evidência | Lacuna |
|---|------|--------|-----------|--------|
| 1 | Artefatos SDD | cumprido | `AGENTS.md`, `docs/00_persona.md` e `docs/01_objetivos_negocio.md` existem e estão versionados; `specs/spec.md:58-62` (RF-01 com Dado/Quando/Então; o mesmo formato vale de RF-01 a RF-28 e de RNF-01 a RNF-13, linhas 55-394); `specs/plan.md:26-28`, `:47-49` e `:94-96` (C4 níveis 1, 2 e 3 em blocos `mermaid`); `specs/tasks.md` (T-01 a T-58, com a coluna de verificação); `docs/atam.md:69` e `:256-258` (cenários ligados a RNF e ADR); `docs/adr/ADR-001` a `ADR-008`; `docs/rastreabilidade.md` (41 linhas, uma por RF/RNF); `docs/prompts.md:57-70` (registro por tarefa) | nenhuma |
| 2 | Coleta | cumprido | `.github/workflows/coleta.yml:13-14` (cron diário 20h30 UTC e reserva 06h30 UTC); `coleta.yml:29` (`TCG_USER_AGENT` vindo de `vars`); `src/tcg/coleta/http.py:50` (User-Agent na sessão, em toda requisição); `http.py:57-63` e `config/parametros.toml:13` (pausa mínima de 100 ms, inclusive entre repetições); `http.py:105-112` e `parametros.toml:7-10` (até 3 repetições, esperas de 2, 4 e 8 s); testes `tests/unidade/test_http.py:81`, `:99` e `:115`; 29 execuções agendadas em `docs/evidencias/T-52_agendador.md` | os parâmetros de repetição são hipótese, sem falha real observada (P-12); aviso de Node.js 20 obsoleto nas ações do workflow (P-03) |
| 3 | Bruto | cumprido | `src/tcg/coleta/guarda.py:55-60` (chave `raw/<fonte>/group_id=<id>/data=AAAA-MM-DD/<arquivo>`, que vira `tcg/raw/tcgplayer/group_id=24269/data=…/` no bucket `tcg`); `src/tcg/coleta/gravador.py:26` (`open("xb")`, criação exclusiva na branch); `src/tcg/lake/cliente.py:37-45` (`stat_object` antes de gravar) e `src/tcg/sync/sincronizador.py:99-102` (chave existente é recusada, sem `put_object`); testes `tests/unidade/test_coletor.py:196` (recusa com hash original intacto), `tests/unidade/test_sincronizador.py:93` e `tests/integracao/test_minio.py:176` (recusa num MinIO descartável, com etag, data e tamanho iguais) | sem backup do prefixo raw fora do repositório (P-02); a verificação `stat_object` + `put_object` não é atômica (ver lacuna L-08, não registrada) |
| 4 | Silver | cumprido | `src/tcg/silver/construtor.py:84-107` (`CONTRATO` com nomes e tipos de `colecao`, `produto`, `preco_diario`, `cambio_diario`, `cdi_diario` e `quarentena`, iguais a `specs/spec.md:41-45`); `src/tcg/silver/modelos.py:36-81` (um modelo Pydantic por tabela, `extra="forbid"`); `src/tcg/silver/quarentena.py:14-15` e `:36` (quarentena com `motivo` e `chave_raw`); `modelos.py:60` e `:135` (`market_price: float \| None`, lido direto de `marketPrice`, sem cópia de outro dia); testes `tests/unidade/test_construtor_silver.py:140` e `tests/integracao/test_coleta_silver.py:156` (DESCRIBE dos tipos), `tests/unidade/test_modelos.py:139` (preço ausente vira nulo), `tests/unidade/test_construtor_silver.py:218` (quarentena com motivo e contagem no log); silver real reconstruída em `docs/evidencias/T-50_clone_limpo.md:58` | nenhuma no código; o DESCRIBE sobre a silver real não foi rodado (ver "Suposições") |
| 5 | Gold | cumprido | `src/tcg/gold/sql/fato_preco_diario.sql:1-33`, `dim_produto.sql`, `dim_colecao.sql`, `dim_data.sql` e `dim_acabamento.sql`; `src/tcg/gold/construtor.py:103` (lista `silver/<tabela>/` de todas as coleções, só leitura); `fato_preco_diario.sql:9-10` (preço de todas as coleções por curinga); `docs/adr/ADR-003-estrela-outras-colecoes.md`; teste `tests/unidade/test_estrela.py:131` (`dim_colecao` com duas coleções); gold real com DRI e 24541 em `docs/evidencias/T-50_clone_limpo.md:66-67` | nenhuma |
| 6 | Reprocessamento | cumprido | `Makefile:42-44` (`make reprocessar`, com `CONFIRMAR`); `src/tcg/reprocessar.py`; `src/tcg/lake/guarda_prefixo.py:85-97` (única exclusão, só nos três prefixos derivados da DRI); testes `tests/integracao/test_reprocessar_integracao.py:182` (duas execuções com as mesmas chaves, contagens e conteúdo) e `:197` (nenhuma chave de grão duplicada); `docs/evidencias/T-33_reprocessar.txt` | nenhuma; o comando não foi executado nesta auditoria (proibido ao agente) |
| 7 | Dashboard | cumprido | `dashboard/app.py:108` (uma aba por pergunta, P1 a P5); `app.py:602`, `:625`, `:653`, `:687` e `:733` (seções P1 a P5); `app.py:443-455` e `:609-611` (ranking da P1 com `ImageColumn` e `LinkColumn`); `app.py:541-546` e `:93-94` (imagem e link, com "imagem indisponível" e "link indisponível"); `app.py:775` (imagem no tooltip da P5); testes `tests/unidade/test_painel_perguntas.py` e `docs/evidencias/T-46_painel_perguntas.txt`; observações do autor em `docs/evidencias/T-53_observacoes_painel.md` | a P3 usa outra definição de "primeiro dia": `src/tcg/gold/perguntas.py:270-275` contra `specs/spec.md:8` (P-06); a mensagem da P5 não diz a coleção (P-08); falta aviso na P3 com um só dia comum (P-09) |
| 8 | Testes | cumprido | `tests/conftest.py:1-40` e `tests/unidade/test_bloqueio_rede.py:13-28` (rede bloqueada nos testes de unidade); `tests/integracao/test_coleta_cassetes.py:22` e `:61` (vcrpy, `record_mode="none"`, com cassete real de 2026-11-03); `tests/integracao/test_minio.py:35` e `:110` (`MinioContainer` do testcontainers, mesma imagem do compose); `.venv/bin/python -m pytest -q` nesta auditoria: `463 passed in 63.89s` | a senha gerada para o MinIO descartável aparece no traceback quando um teste falha (P-07) |
| 9 | Rastreabilidade | parcial | `docs/rastreabilidade.md`: 40 linhas `atendido` e 1 `parcial` (RNF-13, linha 62); nenhuma linha `atendido` sem evidência; todos os testes `arquivo::função`, as evidências e os 45 commits citados existem (conferido por script, ver "Fatos de verificação"); `git log --oneline`: 82 de 84 commits seguem `tipo(T-xx): descrição` | `10b6b13 chore (T-00): esqueleto SDD do projeto final` tem espaço antes do parêntese, e `bed3e94 Initial commit` não segue a convenção (L-11, não registrada); 12 commits sem `[RF/RNF]`, todos de T-00, T-01 e T-18, o que o `AGENTS.md` permite ("omitir quando não houver") |
| 10 | Ordem SDD | cumprido | `git log --follow -- specs/spec.md`: primeiro commit `7000c99` (2026-11-02T14:45Z); `git log --follow -- specs/tasks.md`: primeiro commit `ee0f1b2` (2026-11-03T16:35Z); primeiro commit com código em `src/`: `2f41e6e` (2026-11-03T16:43Z), porque `10b6b13` só criou `src/.gitkeep`; script sobre todo o histórico: em nenhum commit que altera `src/`, `dashboard/` ou `tests/` a tarefa citada ou os RF/RNF citados deixam de existir em um commit anterior de `specs/tasks.md` e `specs/spec.md` (T-57 entra em `7c7f1ae` e T-58 em `45ccedf`, antes do código delas) | nenhuma |
| 11 | Segredos | cumprido | histórico completo (`git log --all -p`): o único `.env*` já versionado é `.env.example`, com `MINIO_ACCESS_KEY` e `MINIO_SECRET_KEY` vazios (`.env.example:7-8`); nenhuma URL com usuário e senha, chave AWS, chave privada ou token do GitHub; a única ocorrência do padrão `MINIO_*=<valor>` está em `docs/evidencias/T-15_compose.txt` (commit `7f693b5`) e o valor é o texto fictício "ficticio", usado para testar o compose; `.github/workflows/coleta.yml:94-97` (secrets só no `env` do passo de sincronização); `docs/evidencias/T-51_busca_credenciais.md` | P-07 (senha descartável no traceback); a palavra "turma" aparece mascarada nos logs do Actions (P-15) |
| 12 | Lacunas da série | cumprido | `README.md:192-199` (tabela "Dias sem coleta", vazia, com observação sobre 2026-11-04, recuperada dentro do ciclo); `git ls-tree origin/dados-raw`: 13 datas, de 2026-11-03 a 2026-11-15, cada uma com os quatro arquivos (26 `tcgplayer`, 13 `bcb_ptax`, 13 `bcb_cdi`); `docs/evidencias/T-50_clone_limpo.md:86-88` (`make cobertura`: 13 datas, 0 faltantes) | 2026-11-16 em diante não conferido (ver "Suposições"); 03/11 e 04/11 gravados por execução manual, RNF-13 `parcial` (P-13) |
| 13 | Câmbio | cumprido | `src/tcg/coleta/guarda.py:27-32` (quatro arquivos por data, entre eles `bcb_ptax/cotacao.json` e `bcb_cdi/cdi.json`); `src/tcg/coleta/bcb.py:21-26` (Olinda PTAX e SGS 12); 13 `cotacao.json` e 13 `cdi.json` na `dados-raw`; `specs/spec.md:11` (Fechamento com a maior data ≤ D); `src/tcg/silver/modelos.py:145-150` (boletim diferente de `Fechamento` descartado); `src/tcg/gold/sql/fato_preco_diario.sql:31-32` (`ASOF LEFT JOIN … ON p.data >= c.data_ptax`); testes `tests/unidade/test_estrela.py:108-119` (sábado 10/10, domingo 11/10 e feriado 12/10 usam a PTAX de 09/10, nunca a de 13/10, e nenhuma linha com `data_ptax > data`) e `tests/unidade/test_fato_cambio.py:98` e `:119` | a janela de 10 dias da PTAX e do CDI é hipótese (P-11) |
| 14 | Desafio | cumprido | `src/tcg/gold/carteiras.py:11` e `:121` (unidades inteiras por `math.floor`, sobra em caixa); `carteiras.py:156` (compra pela `cotacao_venda`); `src/tcg/gold/liquidacao.py:180` e `:187` (venda pela `cotacao_compra`, com `(1 - taxa_venda)`); `config/parametros.toml:23` (`taxa_venda = 0.15`, parâmetro); `carteiras.py:3` e `:159` (`ler_primeiro_dia`, único ponto de leitura da composição); `docs/adr/ADR-005-carteira-propria.md` e `ADR-006-fallback-selado.md`; `src/tcg/gold/construtor.py:238` (`taxa_venda` 0 em dolar e cdi); `specs/spec.md:51` (contrato gold_turma); testes `tests/unidade/test_composicao.py:93` (mesma composição com o primeiro dia e com dez dias a mais), `:118` (cinco carteiras, unidades inteiras), `tests/unidade/test_liquidacao.py:221` (435,00 e efeito da taxa de 10%), `tests/unidade/test_carteiras_gold.py:107` e `tests/integracao/test_gold_turma.py:151` (colunas e tipos do contrato) | nenhuma |

## Lacunas por impacto

Ordem: primeiro o que pode acionar limitador (pipeline que não roda, segredo versionado, silver fora do contrato, dado inventado, código sem especificação prévia), depois entrega, funcional, documentação e cosmético. A classificação de impacto das P-xx é a de `docs/pendencias_aula08.md`. As lacunas marcadas "não registrada" são achados desta auditoria.

### Limitador

- **Fato:** nenhum limitador foi encontrado no repositório. O pipeline roda pelo README (`docs/evidencias/T-50_clone_limpo.md`, 463 testes também nesta auditoria); não há segredo versionado (item 11); a silver segue o contrato da spec (item 4); a tabela "Dias sem coleta" está vazia e a `dados-raw` tem os quatro arquivos de cada data (item 12), sem sinal de dado inventado; nenhum commit de código precede a sua tarefa ou o seu requisito (item 10).
- **L-01 (P-01), lacuna:** o commit de fechamento, a tag `entrega-final` e o envio do formulário ainda não foram feitos. Prazo: 12/12/2026. Perder o prazo deixa o projeto sem entrega.

### Entrega

- **L-02 (P-04 e P-05), lacuna:** a rodada final (`make sync`, `make silver`, `make gold`, `make cobertura`) e a atualização das conclusões e dos prints ainda não foram feitas. A última silver e gold registradas são de 16/11 (`T-50_clone_limpo.md:58` e `:67`).
- **L-03 (P-02), lacuna:** não há backup do prefixo raw da DRI fora do repositório. A `dados-raw` continua sendo a fonte da verdade, mas a credencial da turma é de administrador (RS-04 e RS-09 em `docs/atam.md`).

### Funcional

- **L-04 (P-06), lacuna:** `src/tcg/gold/perguntas.py:270-275` define o primeiro dia da P3 como a menor `data` com `market_price` não nulo; `specs/spec.md:8` o define como a menor `data` com bruto. Sem efeito nos dados de 03/11 a 15/11, mas é código que diverge da especificação.
- **L-05 (P-03), lacuna:** `actions/checkout@v4` (`coleta.yml:32` e `:39`) e `actions/setup-python@v5` (`coleta.yml:45`) geram o aviso de Node.js 20 obsoleto.
- **L-06 (P-08), lacuna:** a mensagem "fica fora do gráfico" da P5 não diz a coleção do item.
- **L-07 (P-09), lacuna:** a P3 não avisa quando há um único dia comum entre as coleções.
- **L-08 (não registrada), lacuna:** `src/tcg/sync/sincronizador.py:99-115` confere a existência (`stat_object`) e depois grava (`put_object`) em duas chamadas, sem gravação condicional. Duas sincronizações simultâneas sobre a mesma chave poderiam passar as duas pela verificação. O `concurrency` do workflow (`coleta.yml:20-22`) evita isso entre execuções do Actions, mas não entre o Actions e um `make sync` manual. Ver também a suposição S-06.
- **L-09 (P-07), lacuna:** a senha gerada pelo fixture `minio_descartavel` aparece no traceback do pytest quando um teste de integração falha. É credencial de um contêiner descartável, não a da turma.

### Documentação

- **L-10 (P-10, P-11, P-12 e P-13), lacuna:** continuam como hipótese o horário de atualização do TCGCSV (ADR-007), a janela de 10 dias da PTAX e do CDI (`config/parametros.toml:4`) e as esperas de repetição (`parametros.toml:7-10`). O RNF-13 continua `parcial` por causa das execuções manuais de 03/11 e 04/11 (`docs/rastreabilidade.md:62`).

### Cosmético

- **L-11 (não registrada), lacuna:** dois commits fora da convenção: `10b6b13` (`chore (T-00)`, com espaço) e `bed3e94` (`Initial commit`, criado pelo GitHub). Os dois são anteriores a qualquer código e não podem ser reescritos sem `push --force`, que o `AGENTS.md` proíbe.
- **L-12 (P-14 e P-15), lacuna:** o log do sincronizador diz "MinIO" para o data lake e mostra o logger `__main__`, e o nome do passo do workflow aparece com `***` nos logs.

## Fatos de verificação

Comandos executados nesta auditoria, com a saída resumida:

| Comando | Saída |
|---|---|
| `.venv/bin/python -m pytest -q` | `463 passed in 63.89s (0:01:03)` |
| script sobre `docs/rastreabilidade.md` (testes `arquivo::função`, arquivos de `docs/evidencias/`, hashes de commit e linhas `atendido` sem evidência) | `41 linhas; atendido sem evidência: []`; `testes inexistentes: set()`; `evidências inexistentes: set()`; `45 commits citados; inexistentes: []` |
| `git log --oneline` filtrado pela convenção `tipo(T-xx): descrição` | só `10b6b13` e `bed3e94` fora do formato, em 84 commits |
| script sobre todo o histórico (`git show <commit>:specs/tasks.md` e `:specs/spec.md` em cada commit, comparado com os commits que alteram `src/`, `dashboard/` ou `tests/`) | `commits de código com problema de ordem: []` |
| `git log --follow` em `specs/spec.md` e `specs/tasks.md`, e `git log --reverse -- src/` | `7000c99` (spec), `ee0f1b2` (tasks) e `2f41e6e` (primeiro código), nessa ordem |
| `git log --all --name-only --diff-filter=A` filtrado por `.env` | só `.env.example` |
| `git log --all -p` filtrado por chaves MinIO/AWS, URL com usuário e senha, chave privada, token do GitHub e `password/senha/secret` com valor | uma ocorrência: `7f693b5`, `docs/evidencias/T-15_compose.txt`, valor fictício "ficticio" (o valor foi conferido mascarado e não é reproduzido aqui) |
| `git ls-tree -r --name-only origin/dados-raw` | 13 datas, de 2026-11-03 a 2026-11-15; 26 arquivos `tcgplayer`, 13 `bcb_ptax` e 13 `bcb_cdi` |

## Suposições

- **S-01, DESCRIBE sobre a silver real não rodado.** O enunciado autoriza a leitura da própria partição e o DESCRIBE no DuckDB sobre a silver, mas o `AGENTS.md` proíbe o agente de acessar o data lake da turma e de ler o `.env`, e o complemento da T-56 manda que ele prevaleça. No lugar do DESCRIBE, a auditoria usou: o teste `tests/integracao/test_coleta_silver.py:156`, que faz DESCRIBE sobre a silver gravada num MinIO descartável a partir do bruto real de 2026-11-03 (passou nesta auditoria); o teste `tests/unidade/test_construtor_silver.py:140`; e as contagens da silver real em `docs/evidencias/T-50_clone_limpo.md:58` e `T-58_silver_gold_rustfs.txt`. Supõe-se que a silver no data lake foi gravada pelo mesmo código, na versão auditada ou anterior sem mudança no `CONTRATO`.
- **S-02, contrato comum.** O texto do enunciado com o contrato comum da turma não está no repositório. A auditoria supõe que as tabelas de `specs/spec.md:41-51` reproduzem esse contrato e comparou o código com a spec.
- **S-03, datas depois de 15/11.** A ref local `origin/dados-raw` termina em 2026-11-15 (`85d9995`). Não foi feito `git fetch`, porque o `AGENTS.md` proíbe acesso à rede fora de uma tarefa que o peça. A coleta de 2026-11-16 (ciclo até 2026-11-17T20:00Z) não foi conferida. Também não foi rodado `make cobertura`, que faz `git fetch`; vale o resultado de 16/11 em `T-50_clone_limpo.md:86-88`.
- **S-04, execução agendada.** A frequência real das execuções do workflow foi conferida só por evidência (`docs/evidencias/T-52_agendador.md`, 29 execuções). A auditoria não consultou o GitHub Actions, por ser acesso à rede.
- **S-05, painel.** O painel não foi aberto nesta auditoria. O item 7 se apoia no código, nos testes de `tests/unidade/test_painel_*.py` e nas observações do autor em `docs/evidencias/T-53_observacoes_painel.md`.
- **S-06, atomicidade no data lake.** Não foi verificado se o RustFS aceita gravação condicional (`If-None-Match`). A L-08 supõe que não há proteção do lado do servidor, porque o código não a pede.
- **S-07, reprocessamento.** O critério do item 6 foi julgado pelo teste com MinIO descartável e pela evidência T-33. `make reprocessar` apaga objetos e é proibido ao agente, então não foi executado.

## Comandos não executados

| Comando | Motivo |
|---|---|
| DESCRIBE no DuckDB sobre a silver real e qualquer leitura da partição no data lake da turma | `AGENTS.md`: o agente não acessa o data lake da turma nem lê o `.env` (S-01) |
| `git fetch` e `make cobertura` | acesso à rede fora de uma tarefa que o peça (S-03) |
| `make sync`, `make silver`, `make gold`, `make painel` | gravam no data lake ou dependem do `.env` |
| `make reprocessar` | exclusão, proibida ao agente mesmo nos prefixos da DRI (S-07) |
| `gh run list` | acesso à rede (S-04) |
