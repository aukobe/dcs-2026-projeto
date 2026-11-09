# Registro de prompts

Histórico dos prompts usados com agentes de IA em cada etapa do projeto e do resultado da revisão humana.

| data | etapa | prompt | resultado da revisão |
|------|-------|--------|----------------------|
| 2026-11-02 | 0 – Esqueleto | texto completo em [Prompt da etapa 0 – Esqueleto](#prompt-da-etapa-0--esqueleto) | aprovado sem alterações |
| 2026-11-02 | 1 – Persona | texto completo em [Prompt da etapa 1 – Persona](#prompt-da-etapa-1--persona) | aprovado com ajustes (nome da persona, pergunta 3 sem turma, coleção = DRI inteira, lacunas revisadas, escopo de leitura de outras coleções) |
| 2026-11-02 | 2 – Objetivos | texto completo em [Prompt da etapa 2 – Objetivos](#prompt-da-etapa-2--objetivos) | aprovado com ajustes (OBJ-02 com decomposição em três efeitos, OBJ-05 com cinco carteiras e fórmula de liquidação, P4 das outras coleções no OBJ-04, coleções recentes = lançadas a partir de 2024, câmbio da carteira dolar como limite declarado, encaminhamento das perguntas abertas) |
| 2026-11-02 | 3 – Especificação | texto completo em [Prompt da etapa 3 – Especificação](#prompt-da-etapa-3--especificação) | aprovado com ajustes (PTAX descartada por regra, carteiras com e sem taxa, placar da turma, execução agendada) |
| 2026-11-02 | 4 – Plano | texto completo em [Prompt da etapa 4 – Plano](#prompt-da-etapa-4--plano) | aprovado com ajustes (exclusão restrita à guarda de prefixo no RNF-03 e exceção do make reprocessar no AGENTS.md, reprocessamento inclui gold_turma, gold lê produto e colecao de todas as coleções, fontes coletadas de forma independente, bloqueio de rede por fixture, carteiras em Python puro, cobertura pela branch dados-raw, criação da branch dados-raw pelo autor, mensagem do commit automático, TCG_USER_AGENT em vars, exceção da convenção de commits para o coletor no AGENTS.md) |
| 2026-11-03 | 5 – Tarefas | texto completo em [Prompt da etapa 5 – Tarefas](#prompt-da-etapa-5--tarefas) | aprovado com ajustes (ADRs antes do código que orientam, prompts 11.1 e 11.2 no Bloco F, autoauditoria e pendências) |
| 2026-11-03 | T-01 | "prompt de implementação padrão" (texto completo em [Prompt de implementação padrão (etapa 6)](#prompt-de-implementação-padrão-etapa-6)) | plano aprovado com ajustes (Python 3.13 em vez de 3.12, já instalado no Codespace; rede só para o PyPI; alvo `make setup` que acha o python3.13 no PATH ou em `/usr/local/python/3.13.8/bin`); `make setup` e `make test`: 3 passed; evidência em `docs/evidencias/T-01_pacote.txt` |
| 2026-11-03 | T-02 | "prompt de implementação padrão" | plano aprovado com ajuste (bloqueio também de `socket.getaddrinfo`, com o teste `test_resolucao_dns_falha`); `pytest tests/unidade/test_bloqueio_rede.py`: 4 passed; `make test`: 7 passed; evidência em `docs/evidencias/T-02_bloqueio_rede.txt` |
| 2026-11-03 | T-03 | "prompt de implementação padrão" | plano aprovado com ajuste (comentários de origem em `config/parametros.toml`: "hipótese: validação pendente" com RF-01, RF-03 e RF-24; RES-03, OBJ-03 e OBJ-04 nos demais); `pytest tests/unidade/test_config.py tests/unidade/test_log.py`: 18 passed; `make test`: 25 passed; evidência em `docs/evidencias/T-03_config_log.txt` |
| 2026-11-03 | T-04 | "prompt de implementação padrão" | plano aprovado com a leitura (A) de RF-03: `tentativas` = repetições após a primeira chamada (no máximo 4 requisições, esperas de 2, 4 e 8 s); RF-03 da spec e comentário de `config/parametros.toml` ajustados; teste de falha total confere 4 requisições; depois, `specs/plan.md` (seção 5, Cliente HTTP) e a mensagem de erro de `esperas_s` em `src/tcg/config.py` ajustados ao mesmo texto; `pytest tests/unidade/test_http.py`: 8 passed; `make test`: 33 passed; evidência em `docs/evidencias/T-04_cliente_http.txt` |
| 2026-11-03 | T-05 | "prompt de implementação padrão" | plano aprovado com a janela D−9 até D (10 dias corridos, extremos incluídos); `src/tcg/coleta/tcgcsv.py` e `src/tcg/coleta/bcb.py` com URL montada como texto; consulta real ao BCB (2 requisições, status 200; TCGCSV não chamado) confirmou Olinda `CotacaoMoedaPeriodo` e SGS série 12; `pytest tests/unidade/test_clientes.py`: 10 passed; `make test`: 43 passed; evidências em `docs/evidencias/T-05_clientes.txt` e `docs/evidencias/T-05_endpoints_bcb.md` |
| 2026-11-03 | T-06 | "prompt de implementação padrão" | plano aprovado com os códigos de saída 0 (tudo gravado ou já existente), 1 (falha de alguma fonte, demais gravadas) e 2 (recusa por horário ou destino inexistente); `guarda.py`, `gravador.py` (modo `xb`) e `__main__.py`; `products.json` e `prices.json` verificados um a um; a pedido do autor, a descrição do T-10 em `specs/tasks.md` passou a exigir commit e push dos arquivos gravados também com código 1, marcando o job como falho depois, e nada a commitar com código 2; `pytest tests/unidade/test_coletor.py`: 12 passed; `make test`: 55 passed; evidência em `docs/evidencias/T-06_coletor.txt` |
| 2026-11-03 | T-07 | texto completo em [Prompt da T-07 – ADR-001](#prompt-da-t-07--adr-001) | rascunho aprovado sem alterações de conteúdo; nome do arquivo seguiu o `specs/tasks.md` (`docs/adr/ADR-001-bruto-dados-raw.md`) em vez do nome do prompt (`ADR-001-bruto-branch-dados-raw.md`); ADR salvo, T-07 marcada como [x] |
| 2026-11-03 | T-08 | "prompt de implementação padrão" | plano aprovado; commits só nos repositórios temporários dos testes, autorizados pelo autor; mensagem do commit inicial `chore(T-08): branch órfã dados-raw [RF-02]`; script cria a branch órfã por `hash-object`, `mktree`, `commit-tree` e `branch`, sem checkout, sem rede e sem push, e recusa se `dados-raw` ou `origin/dados-raw` já existir; `pytest tests/unidade/test_criar_branch.py`: 7 passed; suíte completa (`pytest -q`): 62 passed; evidência em `docs/evidencias/T-08_criar_branch.txt` |
| 2026-11-03 | T-09 | executor: autor (tarefa manual, sem prompt) | o autor rodou `scripts/criar_branch_dados_raw.sh` e publicou a branch com `git push -u origin dados-raw`; `git ls-tree origin/dados-raw` lista só `.gitattributes` e `README.md`; evidência em `docs/evidencias/T-09_branch_publicada.txt` |
| 2026-11-03 | T-10 | "prompt de implementação padrão" | plano aprovado com as tags `actions/checkout@v4` e `actions/setup-python@v5` (sem SHA, tarefa sem rede) e `pyyaml==6.0.3` nas dependências de dev do `pyproject.toml`; ajuste do autor: o teste trata a chave `on:` lida como `True` pelo `yaml.safe_load`; checkout da `main` com `persist-credentials: false`, concorrência sem cancelamento, data do commit tirada dos caminhos `data=AAAA-MM-DD`, publicação com código 0 ou 1 e job marcado como falho depois; `pytest tests/unidade/test_workflow.py`: 11 passed; suíte completa (`pytest -q`): 73 passed; evidência em `docs/evidencias/T-10_workflow.txt` |
| 2026-11-03 | T-11 | executor: autor (tarefa manual, sem prompt) | o autor criou a variável de repositório `TCG_USER_AGENT` (em `vars`, não em secret) no GitHub, em Settings > Secrets and variables > Actions > Variables; evidência em `docs/evidencias/T-11_variavel_user_agent.txt` |
| 2026-11-03 | T-12 | executor: autor (tarefa manual, sem prompt) | o autor disparou o workflow `coleta.yml` manualmente depois das 20h UTC (execução coleta #1, sucesso em 56 s); `git ls-tree -r --name-only origin/dados-raw` lista os quatro arquivos do dia em `raw/.../data=2026-11-03/` (`cdi.json`, `cotacao.json`, `prices.json`, `products.json`) e `git log` mostra o commit `65c413a dados(coleta): 2026-11-03 [RF-01]`; pendência futura: atualizar `actions/checkout` para v5 e `actions/setup-python` para v6 em `.github/workflows/coleta.yml`, por causa do aviso de Node.js 20 descontinuado no GitHub Actions; evidência em `docs/evidencias/T-12_primeira_coleta.txt` |
| 2026-11-03 | T-13 | "prompt de implementação padrão" | plano aprovado com script `scripts/hipoteses_bruto.py` e teste `tests/unidade/test_hipoteses_bruto.py` (6 passed; suíte: 79 passed); bruto de 2026-11-03 lido por `git show`, sem requisição às fontes; confirmadas: `tipo_produto` (25 selados, 256 cartas, 12 Code Cards sem número), raridades, imagem e link (281/281), preço dos selados (25/25); refutada: booster box (a regra pega também `Destined Rivals Half Booster Box`); janela PTAX/CDI consistente (6 Fechamentos, 5 dias de CDI) e repetição não validável; correções da spec propostas com diff, não aplicadas; evidência em `docs/evidencias/T-13_hipoteses.md`; depois, o autor pediu: "Aceito o diff proposto para o RF-23 (excluir também "Half"). Aplique no specs/spec.md, mostre o diff final e acrescente na evidência T-13_hipoteses.md que a correção foi aplicada. Registre esta mensagem na linha da T-13 em docs/prompts.md. Não altere outros arquivos."; correção do RF-23 aplicada em `specs/spec.md` e registrada na evidência; por fim, o autor pediu: "Aplique também a correção 2: na spec, retire a marca de hipótese de tipo_produto, lista de raridades, identificação do booster box, imagem e link, e preço dos selados, citando "validado no T-13 (docs/evidencias/T-13_hipoteses.md)". Na seção "Perguntas abertas", deixe como hipótese só a janela de PTAX e CDI e os parâmetros de repetição. Mostre o diff, atualize a seção "Decisão do autor" da evidência e a linha da T-13 em docs/prompts.md. Mantenha o script com a regra antiga, como está."; correção 2 aplicada em `specs/spec.md`, evidência atualizada, script mantido |
| 2026-11-03 | T-14 | texto completo em [Prompt da T-14 – ADR-002](#prompt-da-t-14--adr-002) | rascunho aprovado com ajuste: mantidas as seis alternativas (as quatro do prompt mais bind mount e binário instalado à mão, da seção 6 do plan); decisão a mais do autor: "os testes de integração (RNF-07) usam a mesma imagem e a mesma tag (ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z), para que o teste rode o mesmo binário do ambiente de trabalho"; cenário do RNF-07 e seção Decisão ajustados; ADR salvo em `docs/adr/ADR-002-imagem-minio.md`, T-14 marcada como [x] |
| 2026-11-03 | T-15 | "prompt de implementação padrão" | plano aprovado com dois ajustes do autor: credenciais com `${VAR:?}` (sem `.env`, o compose recusa subir) e verificação do `docker compose config --quiet` sem variáveis (recusa) e com valores fictícios só na linha de comando (passa); autorizado baixar a imagem do ghcr.io e rodar um contêiner descartável, e T-15 marcada com [rede: só ghcr.io] e [contêiner]; criados `docker-compose.yml`, alvo `make up` (`docker compose up -d --wait`) e `tests/unidade/test_compose.py` (6 passed na 2ª execução; a 1ª falhou por erro de formatação no próprio teste; suíte: 85 passed); `mc ready local` confirmado na imagem fixada (R-07), que não tem curl nem wget; contêiner `minio-t15` removido ao final; evidência em `docs/evidencias/T-15_compose.txt` |
| 2026-11-03 | T-16 | executor: autor (tarefa manual, sem prompt) | o autor criou o `.env` a partir do `.env.example`, com a senha gerada por openssl e sem exibi-la, e subiu o MinIO local com `make up`; `docker compose ps` mostra `dcs-2026-projeto-minio-1` com a imagem `ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z` como `healthy`, nas portas 9000 e 9001; `git check-ignore .env` confirma que o `.env` é ignorado pelo Git; evidência em `docs/evidencias/T-16_minio_up.txt`, sem credencial |
| 2026-11-04 | T-17 | "prompt de implementação padrão" | plano aprovado sem ajustes; criados `src/tcg/sync/__init__.py`, `src/tcg/sync/leitor_branch.py` (`buscar` por `git fetch` só da ref remota, `listar` por `git ls-tree -r -z` restrito a `raw/`, `ler` por `git cat-file blob` em bytes, sem checkout) e `tests/unidade/test_leitor_branch.py` com repositório temporário e remoto bare local, sem rede (6 passed na 1ª execução; suíte: 91 passed); bytes idênticos com `\r\n`, `\r` solto e bytes não UTF-8, também com `core.autocrlf=true`; evidência em `docs/evidencias/T-17_leitor_branch.txt` |
| 2026-11-04 | T-18 | "prompt de implementação padrão" | plano aprovado com uma decisão do autor: o sincronizador cria o bucket `tcg` com `make_bucket` quando ausente, de forma idempotente e registrada no log (RNF-10), e o AGENTS.md ganhou a regra "Criar o bucket tcg quando ele não existir é permitido, de forma idempotente; apagar buckets continua proibido."; criados `src/tcg/lake/__init__.py`, `src/tcg/lake/cliente.py` (`criar_cliente` com credenciais só do ambiente, `existe` por `stat_object`, `garantir_bucket`), `src/tcg/sync/sincronizador.py` (chave fora de `raw/<fonte>/group_id=24269/` recusada antes do SDK, `stat_object` antes do `put_object`, recusa de sobrescrita no log, sha1 do blob conferido antes do envio e sha256 do objeto relido conferido com o da origem), alvo `make sync` e `tests/unidade/test_sincronizador.py` com cliente falso, sem rede (24 passed na 1ª execução; suíte: 115 passed); `make sync` não executado (T-21, autor); evidência em `docs/evidencias/T-18_sincronizador.txt` |
| 2026-11-04 | T-19 | "prompt de implementação padrão" | plano aprovado com o Ryuk do testcontainers desligado só neste módulo (evita baixar `testcontainers/ryuk` do Docker Hub); criado `tests/integracao/test_minio.py`: MinIO descartável com a imagem lida do `docker-compose.yml`, porta aleatória, credenciais geradas na hora (sem ler o `.env`) e label `tcg.teste=T-19`; testes de imagem igual à do compose, bucket criado uma vez, gravação com hash da origem, recusa de sobrescrita (ETag, `last_modified` e hash inalterados, recusa no log) e sincronização de uma branch `dados-raw` temporária executada duas vezes (4 enviados, depois 4 recusas, credenciais fora do log); o encerramento confere que o contêiner de teste foi removido e que o MinIO de trabalho manteve Id, StartedAt e RestartCount (5 passed na 1ª execução; suíte: 120 passed); evidência em `docs/evidencias/T-19_minio_descartavel.txt` |
| 2026-11-04 | T-20 | "prompt de implementação padrão" | plano aprovado sem ajustes; criados `scripts/montar_cassetes.py` (lê os quatro blobs de `data=2026-11-03` na ref local `origin/dados-raw` pelo leitor da T-17, sem `git fetch` nem requisição às fontes; URLs montadas pelos próprios clientes TCGCSV e BCB; recusa sobrescrever cassete existente), `tests/integracao/cassetes/coleta_2026-11-03.yaml` (4 interações, corpo igual ao blob, sem `Content-Encoding`), `tests/integracao/cassetes/coleta_2026-11-03.hashes.json` (blob e sha256 de cada arquivo) e `tests/integracao/test_coleta_cassetes.py` (socket bloqueado no módulo, vcrpy em `record_mode="none"`): a coleta de 2026-11-03T20:30Z grava os quatro arquivos com sha256 e id de blob iguais aos do bruto real, com 4 requisições tocadas do cassete (4 passed na 2ª execução; a 1ª falhou porque `allow_playback_repeats` foi passado ao `VCR()` em vez do `use_cassette`; suíte: 124 passed); evidência em `docs/evidencias/T-20_cassetes.txt` |
| 2026-11-04 | T-21 | executor: autor (tarefa manual, sem prompt) | o autor rodou `make sync` duas vezes contra o MinIO local; 1ª execução: bucket `tcg` criado e `enviados=4 recusados=0 fora_do_escopo=0 falhas=0` (os quatro arquivos de 2026-11-03); 2ª execução: bucket não recriado e `enviados=0 recusados=4 fora_do_escopo=0 falhas=0`, com uma recusa de sobrescrita no log por chave; os sha256 enviados são iguais aos dos blobs (manifesto da T-20) e a releitura no MinIO não acusou divergência; pendências futuras: (1) fixar o nome do logger do sincronizador (hoje aparece como `__main__` no log porque `make sync` roda o módulo com `-m`; usar `tcg.sync.sincronizador`), sem efeito no resultado; (2) ainda aberta desde a T-12: atualizar `actions/checkout` para v5 e `actions/setup-python` para v6 em `.github/workflows/coleta.yml`, por causa do aviso de Node.js 20 descontinuado no GitHub Actions; evidência em `docs/evidencias/T-21_primeira_sync.txt`, conferida pelo autor sem credencial |
| 2026-11-04 | T-22 | texto completo em [Prompt da T-22 – ADR-004](#prompt-da-t-22--adr-004) | rascunho aprovado com um ajuste: a citação do ADR-003 (ainda não escrito) nas alternativas foi trocada por "plan.md, seção 6"; mantidas, por decisão do autor, a consequência negativa de `make silver` e `make gold` sobrescreverem sem apagar e a segunda condição de revisão (gravação fora do MinIO local ou versões no caminho do contrato), ambas vindas da seção 7 do plan; números das tarefas de evidência conferidos no `specs/tasks.md` (T-23, T-33, T-34); tempo de reprocessamento registrado como "hipótese: validação pendente"; arquivo `docs/adr/ADR-004-camadas-derivadas.md` |
| 2026-11-04 | T-23 | "prompt de implementação padrão" | plano aprovado com um ajuste: `<objeto>` pode conter subpastas, com `silver/preco_diario/group_id=24269/data=2026-11-03/preco.parquet` e `gold/group_id=24269/fato_preco_diario/parte.parquet` nos testes de escrita e exclusão aceitas; criados `src/tcg/lake/guarda_prefixo.py` (group_id 24269 fixo no módulo; `gravar` valida e chama `put_object`; `apagar` é a única exclusão do código, valida o lote inteiro antes de qualquer `remove_object`) e `tests/unidade/test_guarda_prefixo.py` (cliente falso): escrita e exclusão aceitas nos três prefixos; 21 chaves recusadas (`raw/`, outro group_id, `..`, `.`, parte vazia, barra inicial, `tcg/`, `\`, chave só com prefixo) sem nenhuma chamada ao SDK; lote com uma chave proibida não apaga nada; varredura de `src/` sem `remove_object` fora da guarda (58 passed na 2ª execução; a 1ª falhou na coleta porque `pytest` global usava Python 3.14 sem o pacote; reexecutado com `.venv/bin/python -m pytest`); evidência em `docs/evidencias/T-23_guarda_prefixo.txt` |
| 2026-11-04 | T-24 | "prompt de implementação padrão" | plano aprovado com a opção (b): o autor autorizou baixar a extensão `httpfs` uma única vez, só de extensions.duckdb.org (instalada: `httpfs` 77392a7207); tarefa marcada com **[contêiner]** e **[rede: só extensões do DuckDB]**; `make setup` passa a instalar a `httpfs` para clone limpo; criado `src/tcg/lake/duckdb.py` (`conectar`: auto-install e auto-load desligados, só `LOAD httpfs`, falha com `ExtensaoAusenteError` apontando `make setup`; segredo S3 temporário com estilo de caminho, SSL de `MINIO_SECURE` e credenciais do ambiente, fora do log; `gravar_parquet` valida a chave na Guarda de prefixo antes do `COPY`, desenho confirmado pelo autor) e `tests/integracao/test_duckdb_minio.py` (reusa o fixture `minio_descartavel` da T-19): Parquet com BIGINT, VARCHAR, DOUBLE, DECIMAL(18,4), DATE, TIMESTAMP e nulos volta com os mesmos tipos e valores; objeto conferido pelo SDK; chave `raw/` recusada sem objeto criado; credenciais fora do log; sem `httpfs` a mensagem cita `make setup` (5 passed na 3ª execução: a 1ª falhou por `DESCRIBE read_parquet(...)` sem `SELECT`; a 2ª porque o `read_parquet` liga o particionamento Hive por padrão e acrescenta a coluna `group_id` do caminho, o que vale para as tarefas da silver e da gold; a leitura de ida e volta passou a usar `hive_partitioning = false` e o comportamento padrão ficou registrado numa asserção; os tracebacks das execuções com falha mostraram a credencial gerada na hora do MinIO descartável, já destruído, e não entraram na evidência; suíte: 187 passed); evidência em `docs/evidencias/T-24_duckdb_minio.txt`; pendência futura: evitar que credenciais geradas nos testes de integração apareçam na saída do pytest em caso de falha (hoje o traceback mostra o dicionário do fixture `minio_descartavel`) |
| 2026-11-04 | T-25 | "prompt de implementação padrão" | plano aprovado com três confirmações do autor: `acabamento` vem do `subTypeName` de cada linha de preço; preços, cotações e `taxa_dia` são float (DOUBLE), `group_id` e `product_id` int, `data` date e `data_hora_cotacao` datetime; o CDI é convertido no formato real de `docs/evidencias/T-05_endpoints_bcb.md` (texto com ponto decimal), com teste sobre a resposta real. Criados `src/tcg/silver/__init__.py`, `src/tcg/silver/modelos.py` (modelos `Colecao`, `Produto`, `PrecoDiario`, `CambioDiario`, `CdiDiario` com as colunas do contrato; `produto_do_bruto` com `tipo_produto` pela regra do T-13 e exceção do Code Card; `preco_do_bruto` com preço ausente ou nulo como `None`; `cambio_do_bruto` devolve `None` para boletim diferente de `Fechamento` e levanta `ValidationError` para `Fechamento` sem `cotacao_venda`; `cdi_do_bruto`; `colecao_da_config`) e `tests/unidade/test_modelos.py` (18 passed na 1ª execução; suíte de unidade: 191 passed); a captura do `ValidationError` com motivo fica para a quarentena (T-26); evidência em `docs/evidencias/T-25_modelos.txt` |
| 2026-11-04 | T-26 | "prompt de implementação padrão" | plano aprovado com duas confirmações do autor: esquema da quarentena com `tabela`, `motivo`, `chave_raw` e `conteudo` (linha original em JSON), registrado no RF-07 do `specs/spec.md`; na divergência entre brutos, uma linha de quarentena por bruto. Criados `src/tcg/silver/quarentena.py` (funções puras: `validar` captura o erro do conversor e devolve `LinhaQuarentena` com motivo `campo: mensagem`, ou `None` no descarte do boletim intermediário; `deduplicar_por_data` mantém uma linha por data com a menor `chave_raw` quando os valores são iguais e manda todas as linhas da data para a quarentena com o motivo "valor divergente entre brutos" quando divergem; `contar_por_tabela` e `formatar_contagem` para o log da T-27) e `tests/unidade/test_quarentena.py` (12 passed na 1ª execução; suíte de unidade: 203 passed); gravação no MinIO e log ficam para a T-27; evidência em `docs/evidencias/T-26_quarentena.txt` |
| 2026-11-04 | T-27 | "prompt de implementação padrão" | plano aprovado com uma decisão do autor: só teste de unidade com cliente MinIO falso em memória (o teste com MinIO real e bruto real fica para a T-28); `make silver` não foi executado. Criados `src/tcg/silver/construtor.py` (lista e lê pelo SDK só `raw/{tcgplayer,bcb_ptax,bcb_cdi}/group_id=24269/`; `preco_diario` com `data` da partição da chave e um Parquet por data, grão repetido no mesmo bruto vai à quarentena; `produto` com uma linha por `product_id`, do bruto mais recente; PTAX e CDI deduplicados por data; `colecao` de `config/colecao.toml`; bruto ilegível vai à quarentena; Escritor Parquet com DuckDB local em memória, sem httpfs, tipos do contrato e bytes enviados por `guarda_prefixo.gravar`; quarentena em `silver/quarentena/group_id=24269/quarentena.parquet`, gravada mesmo vazia; log com a contagem de quarentena e as linhas gravadas por tabela; nada é apagado), alvo `make silver` no `Makefile` (carrega o `.env` como o `sync`) e `tests/unidade/test_construtor_silver.py`. Nota da T-24 decidida: o construtor não usa `read_parquet`; quem lê a silver usa `hive_partitioning = false`, porque `group_id` já é coluna do contrato. 12 passed na 2ª execução (a 1ª falhou num teste porque o log era emitido na preparação do fixture e o `caplog.text` só mostra a fase de execução; o texto passou a ser guardado no fixture); suíte de unidade: 215 passed; evidência em `docs/evidencias/T-27_construtor_silver.txt` |
| 2026-11-04 | T-28 | "prompt de implementação padrão" | plano aprovado com uma decisão do autor: o prompt pedia o MinIO descartável da T-19, mas a T-28 não tem a marca [contêiner]; o autor escolheu o bucket em memória (rede e contêiner ausentes), e o MinIO real fica para a T-34. Criado só `tests/integracao/test_coleta_silver.py`, sem mudança em `src/`: coletor com o cassete da T-20 (vcrpy `record_mode="none"`, 4 interações) → bruto gravado com o hash do manifesto → `construir_silver` num bucket em memória → teste de contrato (caminhos e prefixo `group_id=24269`, nomes e tipos de `CONTRATO`, `chave_raw` apontando para o bruto) e contagens do T-13 (281 produtos: 25 selados e 256 cartas; 446 preços com o `market_price` nulo do 637654; 6 PTAX Fechamento; 5 CDI; quarentena vazia); `socket.socket` e `getaddrinfo` bloqueados no módulo, com contador de tentativas em 0. 7 passed na 1ª execução; suíte completa: 236 passed; evidência em `docs/evidencias/T-28_coleta_silver.txt`. Em 2026-11-06, a primeira silver real foi gerada pelo autor com `make silver` contra o MinIO local, a partir do bruto de 2026-11-03, 2026-11-04 e 2026-11-05: colecao 1, produto 281, cambio_diario 8, cdi_diario 7, preco_diario 1338 (446 por data, três partições), quarentena 0. Conferência de PTAX e CDI: cambio_diario 8 = dias úteis de 26/10 a 05/11 sem o feriado de 02/11 (26, 27, 28, 29, 30/10 e 03, 04, 05/11), resultado da deduplicação das janelas sobrepostas dos três brutos; cdi_diario 7 = as mesmas datas sem 05/11, porque o CDI de um dia útil só é publicado na manhã seguinte; evidência em `docs/evidencias/T-28_silver_real.txt` |
| 2026-11-04 | T-57 | texto completo em [Prompt da T-57 – Data de referência](#prompt-da-t-57--data-de-referência) | diagnóstico confirmado por `gh run view` das execuções #2 e #3 (atrasos de 4h17min e 4h29min, recusa por horário com código 2; evidência em `docs/evidencias/T-57_diagnostico.txt`); diffs do `specs/spec.md` (Definições, RF-01, RF-04, RNF-13), linha da T-57 e ADR-007 aprovados com um ajuste: Status "Aceito em 2026-11-04" (data local); decisões do autor aprovadas: plan.md atualizado (guarda, fluxo diário, cron, parâmetro, R-01, lista de ADRs), parâmetro `hora_minima_utc` renomeado para `hora_virada_ciclo_utc`, AGENTS.md esclarecido ("no máximo uma coleta por data de referência"); dois commits: primeiro os documentos, depois código, testes e workflow; `guarda.verificar_horario` e `ForaDoHorarioError` removidos, `data_referencia` criada; cron de reserva `30 6 * * *`; `make test`: 244 passed (evidência em `docs/evidencias/T-57_suite.txt`); nenhuma requisição ao TCGCSV ou ao BCB, `dados-raw` intocada; recuperação: depois do push da T-57, o autor disparou o workflow manualmente às 01h30 UTC de 2026-11-05 e a coleta gravou os quatro arquivos com `data=2026-11-04` (commit `8a50cea dados(coleta): 2026-11-04 [RF-01]` na `dados-raw`; evidência em `docs/evidencias/T-57_recuperacao.txt`), recuperando o dia; pendência futura: comparar o `prices.json` de 2026-11-03 e o de 2026-11-04 para confirmar que os preços mudaram entre os dias (risco de preço antigo do ADR-007) |
| 2026-11-06 | T-29 | texto completo em [Prompt da T-29 – ADR-003](#prompt-da-t-29--adr-003) | rascunho aprovado com um ajuste: o nome da coluna da cotação no fato foi fixado como `cotacao_aplicada` (a cotação de venda usada na conversão); mantidos, por decisão do autor, o acoplamento das outras coleções à PTAX da DRI nas consequências negativas e o placar (RF-28) fora da estrela, lendo `gold_turma/carteira/`. Criado `docs/adr/ADR-003-estrela-outras-colecoes.md`; tempo de `make gold` registrado como hipótese: validação pendente. |
| 2026-11-06 | T-30 | "prompt de implementação padrão" | plano aprovado com um acréscimo do autor: teste de preço anterior ao primeiro boletim de PTAX, que continua no fato com `market_price_brl`, `cotacao_aplicada` e `data_ptax` nulos. Criados `src/tcg/gold/__init__.py`, `src/tcg/gold/sql/` (`dim_colecao.sql`, `dim_produto.sql`, `fato_preco_diario.sql`, `dim_data.sql`, `dim_acabamento.sql` e `__init__.py` com `montar_estrela(con, base)`, que cria as tabelas em memória sem gravar nada) e `tests/unidade/test_estrela.py`; `pyproject.toml` com `package-data` para os `.sql`. Decisão da nota da T-24: toda leitura da silver usa `hive_partitioning = false` (group_id vem da coluna do contrato), com `union_by_name = true` por curinga; câmbio só da silver da DRI; `ASOF LEFT JOIN` com `p.data >= c.data_ptax`; `dim_data` vai do primeiro ao último dia com preço, sem preencher lacunas. `fato_cambio_diario` fica para a T-31 e a conferência do contrato por coleção para a T-32. 6 passed na 2ª execução (a 1ª falhou só por contagem errada no próprio teste, 9 em vez de 8 linhas da fixture); suíte de unidade: 229 passed; evidência em `docs/evidencias/T-30_estrela.txt` |
| 2026-11-06 | T-31 | "prompt de implementação padrão" | plano aprovado com `cdi_taxa_dia` e um acréscimo do autor: coluna `cdi_pendente` (BOOLEAN), verdadeira quando há boletim de PTAX com `data_ptax` igual ao próprio dia e não há CDI nessa data, falsa nos demais dias (fins de semana e feriados inclusive), com teste de 13/10 sem CDI (pendente) e 12/10 feriado (não pendente). Criados `src/tcg/gold/sql/fato_cambio_diario.sql` (um dia de `dim_data` por linha; ASOF LEFT JOIN com `d.data >= c.data_ptax` na `cambio_diario` da DRI; CDI só na data exata, senão 0) e `tests/unidade/test_fato_cambio.py`; `fato_cambio_diario` incluído em `TABELAS`. Ajuste no `tests/unidade/test_estrela.py`: conjunto de `TABELAS` atualizado e `cdi.parquet` vazio na fixture, porque o DuckDB não aceita glob sem arquivo (a silver real sempre grava as cinco tabelas). 6 passed na 1ª execução; suíte de unidade: 235 passed; evidência em `docs/evidencias/T-31_fato_cambio.txt` |
| 2026-11-06 | T-32 | "prompt de implementação padrão" | plano aprovado sem ajustes (`gold/group_id=24269/<tabela>.parquet` e código de saída 3). Criados `src/tcg/gold/construtor.py` (descoberta das silvers pelo SDK, só leitura; conferência de colunas e tipos por coleção contra o `CONTRATO` da silver, com colunas extras permitidas; coleção fora do contrato ou incompleta ignorada com aviso `silver ignorada: group_id=... motivo=...`; silver da DRI ausente ou fora do contrato aborta com `SilverDriInvalidaError`, código 3; seis tabelas gravadas por `gravar_parquet`, que passa pela Guarda de prefixo) e `tests/integracao/test_construtor_gold.py` (MinIO descartável da T-19; cenários com três coleções, só a DRI e sem a DRI); alvo `make gold` no `Makefile`. SQL alterado: curingas de `colecao`, `produto` e `preco_diario` viraram marcadores `{arquivos_<tabela>}`, e `montar_estrela` passou a aceitar a lista de arquivos aprovados (sem ela, mantém o curinga dos testes da T-30 e da T-31). 5 passed na 1ª execução; suíte completa: 261 passed; nenhum contêiner de teste restante; `make gold` não foi executado contra o MinIO de trabalho (primeira execução real fica para o autor); evidência em `docs/evidencias/T-32_construtor_gold.txt`; primeira gold real gerada pelo autor com `make gold` no MinIO local (silver de 2026-11-03, 04 e 05): só a DRI ("nenhuma outra coleção disponível"), seis Parquets em `gold/group_id=24269/`, linhas por tabela conferidas contra a silver (`dim_colecao`: 1, `dim_produto`: 281 = 281 produtos, `fato_preco_diario`: 1338 = 1338 preços, `dim_data`: 3 = 3 dias, `fato_cambio_diario`: 3, `dim_acabamento`: 3, os três `subTypeName` do T-13); evidência em `docs/evidencias/T-32_gold_real.txt` |
| 2026-11-07 | T-58 | texto completo em [Prompt da T-58 – Data lake da turma no RustFS](#prompt-da-t-58--data-lake-da-turma-no-rustfs) | proposta aprovada sem alterações de texto (ADR-008, diffs da spec, do plan e do AGENTS.md, linha da T-58 no Bloco B, renomeado para "Bloco B: armazenamento"), com quatro decisões do autor: 1) o passo de sincronização roda sempre que o coletor termina com 0 ou 1, mesmo sem arquivo novo, e só se o passo "publicar" tiver dado certo; 2) os secrets `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY` e `MINIO_SECRET_KEY` são criados pelo autor no site do GitHub; 3) as variáveis `MINIO_*` não são renomeadas; 4) ajustes também na RES-07 de `docs/01_objetivos_negocio.md` (a persona não menciona o MinIO) e na docstring de `src/tcg/lake/duckdb.py`; passo "sincronizar com o data lake da turma" no `.github/workflows/coleta.yml` (`python -m tcg.sync.sincronizador --repo ../dados`, secrets só no `env` do passo, `MINIO_SECURE=true`); `test_workflow.py` com 7 testes novos no lugar de `test_nenhum_secret` (18 passed; três mutações conferidas: secret no env do job, echo da chave e continue-on-error); `.env.example` com o endpoint do RustFS e `MINIO_SECURE=true`, sem credencial; seção "Data lake" no README; nenhum comando contra o RustFS ou o MinIO local; `make test`: 268 passed; evidências em `docs/evidencias/T-58_primeira_sync_rustfs.txt` (autor) e `docs/evidencias/T-58_suite.txt`; validação do autor no RustFS: (1) workflow disparado (coleta #10), passo de sincronização com enviados=0, recusados=16, falhas=0, evidência em `docs/evidencias/T-58_sync_actions.txt`; (2) `make silver` e `make gold` contra o RustFS, silver com 1784 preços, 281 produtos e quarentena 0, gold com 4 dias e só a DRI, evidência em `docs/evidencias/T-58_silver_gold_rustfs.txt` (conferida pelo autor, sem a senha); as duas hipóteses do ADR-008 (sincronização pelo workflow e silver e gold pelo DuckDB no RustFS) marcadas como validadas; pendências futuras: renomear o passo do workflow para não conter a palavra "turma", que o GitHub mascara por coincidir com o valor de um secret; trocar "MinIO" por "data lake" nas mensagens de log do sincronizador |
| 2026-11-09 | T-33 | "prompt de implementação padrão" | Criados pelo agente `src/tcg/reprocessar.py` (apaga pela Guarda de prefixo só `silver/*/group_id=24269/`, `gold/group_id=24269/` e `gold_turma/carteira/group_id=24269/` e reconstrói silver e gold a partir do bruto), `tests/unidade/test_reprocessar.py` e `tests/integracao/test_reprocessar.py`; alvo `make reprocessar` no `Makefile`. Teste de integração executado pelo autor contra o MinIO descartável (o agente não executa exclusões, conforme o AGENTS.md): 5 passed em 6,27 s; sem confirmação nada muda; a primeira execução apaga só os órfãos derivados da DRI; raw e prefixos de terceiros mantêm o hash; duas execuções seguidas com as mesmas chaves, contagens e conteúdo, 446 preços e 281 produtos na silver e 446 linhas em `fato_preco_diario` por execução (iguais ao bruto real da T-13 e da T-28, conferidas pelas asserções do teste, já que a saída do pytest não imprime as contagens); nenhuma chave de grão duplicada; evidência em `docs/evidencias/T-33_reprocessar.txt` |

## Prompt da etapa 0 – Esqueleto

```text
[C] Personagem
Você é um engenheiro de dados que prepara repositórios para Spec-Driven Development. Nesta etapa você só cria a estrutura de pastas e os arquivos de regras e configuração. Você não escreve código de coleta, não escolhe bibliotecas e não executa comandos que acessem a rede ou o MinIO.

[R] Pedido
Crie o esqueleto do projeto final da disciplina Data Collection and Storage na raiz deste repositório. O projeto é individual: um pipeline diário que coleta produtos e preços da coleção Pokémon TCG "SV10: Destined Rivals" (sigla DRI, groupId 24269) pelo TCGCSV, a PTAX e o CDI do Banco Central, grava a resposta original num MinIO local rodando no GitHub Codespaces (localhost:9000, bucket tcg), constrói silver e gold e alimenta um dashboard em Python.
Crie:
1. Pastas: docs/adr/, docs/evidencias/, specs/, src/, tests/unidade/, tests/integracao/, dashboard/ (com .gitkeep nas vazias).
2. README.md com: título, coleção escolhida (DRI, groupId 24269), resumo de uma linha do projeto, seção "Como rodar" com o texto "a definir nas próximas etapas" e seção "Dias sem coleta" com uma tabela vazia (data | motivo).
3. .gitignore cobrindo pelo menos: .env, .venv/, __pycache__/, *.pyc, .pytest_cache/, backup_raw/, dados_locais/.
4. .env.example só com nomes de variáveis e valores vazios ou fictícios: MINIO_ENDPOINT=localhost:9000, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET=tcg, MINIO_SECURE=false, GROUP_ID=24269, TCG_USER_AGENT=colecao-dri/1.0.
5. AGENTS.md com as seções: Escopo; Ambiente; Arquitetura prevista; Regras de escrita no data lake; Comandos permitidos e proibidos; Política de segredos; Ordem SDD e gates por etapa; Convenção de commits.
6. CLAUDE.md contendo apenas a linha @AGENTS.md.
7. docs/prompts.md com um cabeçalho e uma tabela vazia (data | etapa | prompt | resultado da revisão).

[E] Exemplos
Trecho bem escrito do AGENTS.md:
## Regras de escrita no data lake
- Escreva somente em prefixos com group_id=24269 (tcg/raw/*/group_id=24269/, tcg/silver/*/group_id=24269/, tcg/gold/group_id=24269/, tcg/gold_turma/carteira/group_id=24269/).
- Nenhum objeto em tcg/raw/ é sobrescrito ou apagado; antes de gravar, confira se a chave já existe.

Trecho mal escrito (não faça assim):
## Regras
- Tome cuidado com os dados.

[A] Ajustes
- A credencial do MinIO local fica só no .env. O AGENTS.md deve proibir: ler ou imprimir o .env; escrever qualquer credencial em arquivo, log, evidência ou mensagem de commit; comandos de exclusão no MinIO (mc rm, mc rb, remove_object, remove_bucket ou equivalentes); git push --force.
- Na seção "Ambiente", registre: desenvolvimento e execução local no GitHub Codespaces, com Docker e Python; MinIO local por docker compose (a criar numa tarefa futura).
- Na seção "Arquitetura prevista", descreva em até cinco linhas, marcando como "a confirmar no plan.md": coleta diária no GitHub Actions, depois das 20h UTC, gravando as respostas originais numa branch dados-raw do repositório; um comando local sincroniza esses arquivos para o MinIO local, recusando sobrescrita; silver, gold e dashboard rodam a partir do MinIO local.
- Ordem SDD obrigatória no AGENTS.md: AGENTS.md → docs/00_persona.md → docs/01_objetivos_negocio.md → specs/spec.md → specs/plan.md → specs/tasks.md → implementação (uma tarefa por vez, com teste) → validação ATAM. Nenhum código em src/ antes de specs/tasks.md existir.
- Gate de cada etapa: o artefato foi revisado por mim e commitado antes da etapa seguinte.
- Convenção de commits: tipo(T-xx): descrição [RF-yy]; nesta etapa use chore(T-00): esqueleto SDD do projeto final.
- Idioma de todos os arquivos: português do Brasil.
- Não crie docs/00_persona.md, specs/spec.md nem nenhum outro artefato além dos listados.
- Não execute git commit nem git push; apenas proponha a mensagem.

[T] Tipo de saída
Os arquivos e pastas listados, em Markdown onde couber. Antes de criar, mostre a árvore de pastas e o sumário do AGENTS.md e espere minha confirmação. Ao final, mostre a saída de git status --short.

[E] Extras
Leia antes o que já existe na raiz do repositório (provavelmente só README.md) e preserve o que fizer sentido.
Fonte de dados: TCGCSV (https://tcgcsv.com/tcgplayer/3/24269/products e /prices), pede User-Agent próprio, pausa mínima de 100 ms entre chamadas e no máximo uma coleta por dia, depois das 20h UTC.
Se faltar informação, pergunte. Pare ao final.
```

## Prompt da etapa 1 – Persona

```text
[C] Personagem
Você é um analista de requisitos de engenharia de dados. Nesta etapa você só descreve pessoas e problemas. Você não propõe tecnologia, não escreve código e não executa comandos além de ler arquivos.

[R] Pedido
Preencha docs/00_persona.md com a persona principal do projeto: um colecionador de cartas Pokémon que mora no Brasil, compra cartas avulsas e produtos selados (booster box, elite trainer box, booster bundle) da coleção Destined Rivals para guardar, e quer saber onde o dinheiro dele rende mais.
Use esta estrutura:
1. Tabela da persona com as linhas: Nome e papel; Contexto; Decisão que toma; Frequência de consulta; Como decide hoje; Dor atual; O que precisa ver para decidir; Como mede sucesso.
2. Seção "Perguntas que a persona quer responder", com as cinco perguntas listadas em Extras, na linguagem dela.
3. Tabela "Fatos, lacunas e suposições" (tipo | conteúdo | origem), com pelo menos três fatos, duas lacunas e duas suposições.

[E] Exemplos
Linha bem escrita:
| Dor atual | Compra em dólar e mede o patrimônio em reais, mas não consegue separar quanto da valorização veio da carta e quanto veio da alta do dólar; também não tem histórico de preço próprio, só o preço do dia. |
Linha mal escrita (não faça assim):
| Dor atual | Precisa de um dashboard moderno com dados em tempo real. |

[A] Ajustes
- Use somente as informações deste prompt, do AGENTS.md e dos fatos listados em Extras.
- Não invente números (orçamento, quantidade de cartas, retorno esperado, tempo). Valor ausente = "hipótese: validação pendente".
- Não cite tecnologia (MinIO, DuckDB, Streamlit, GitHub Actions, Parquet) nas linhas de dor, necessidade e sucesso; a persona fala do problema dela.
- Cada fato na tabela de fatos tem origem.
- Não crie nem altere outros arquivos.

[T] Tipo de saída
Somente docs/00_persona.md, em Markdown, com no máximo uma página e meia. Antes de editar, mostre em tópicos o que vai escrever e espere minha confirmação.

[E] Extras
Leia antes: AGENTS.md.
Fatos do contexto (origem: contexto do projeto):
- o colecionador compra no marketplace TCGplayer, em dólar, e mede o patrimônio em reais;
- o preço de referência (market price) vem de vendas recentes nos Estados Unidos; não inclui frete, taxas do marketplace, IOF nem a condição da carta;
- a fonte publica o preço do dia uma vez por dia, inclusive fins de semana; o câmbio de referência (PTAX) só existe em dia útil;
- o colecionador consulta os preços uma vez por dia;
- o histórico de preço só existe a partir do primeiro dia de coleta; um dia não coletado não pode ser recuperado depois;
- para reconhecer uma carta ele precisa ver a imagem dela e poder abrir a página do produto;
- as alternativas ao colecionismo que ele compara são deixar o dinheiro em dólar ou aplicar no CDI;
- o período observado é de algumas semanas e não sustenta previsão de preço nem recomendação de compra.
As cinco perguntas:
1. Quais cartas da minha coleção mais valorizaram e quais mais desvalorizaram desde o início da coleta?
2. Na minha coleção, o produto selado guardou valor melhor que as cartas avulsas?
3. Qual coleção da turma valorizou mais no período?
4. Onde está concentrado o valor de cada coleção?
5. Quais cartas deram mais retorno para o risco assumido?
Se faltar informação para uma linha, pergunte antes de supor. Ao terminar, liste as perguntas abertas e pare.
```

### Ajustes da revisão

#### Ajuste 1 – respostas às perguntas abertas

Arquivo alterado: `docs/00_persona.md` (criado).

```text
Respostas:
1. Pode dar um nome fictício: "Rafael, colecionador de Pokémon TCG".
2. Deixe "Como decide hoje" como hipótese: validação pendente.
3. A persona não é aluno. Ela compara a Destined Rivals com outras coleções recentes do Pokémon TCG. Reescreva a pergunta 3 como "Qual coleção recente valorizou mais no período?", sem mencionar turma.
4. "Coleção" é a coleção DRI inteira (o conjunto de cartas e selados lançados), não uma lista pessoal com quantidades e preço pago. O valor da coleção é a soma de um exemplar de cada carta. Para medir quanto o dinheiro renderia, a persona pensa numa carteira hipotética de R$ 1.000 montada no primeiro dia. Ajuste o contexto e retire essa lacuna.
5. Ajustes nas lacunas e suposições:
   - "Qual câmbio usar no fim de semana" não é lacuna: no fim de semana e em feriado vale a última cotação de dia útil anterior, nunca uma posterior. Mova para fatos.
   - "Como medir risco" e "como as coleções ficam comparáveis" são decisões de especificação, não da persona. Retire daqui.
   - Mantenha as três suposições.
   - Acrescente como lacuna: "a persona aceita que o dashboard mostre evidência do período e não recomendação de compra?".
Pode escrever o arquivo.
```

#### Ajuste 2 – respostas à segunda rodada de perguntas abertas

Arquivos alterados: `docs/00_persona.md` e `docs/prompts.md` (diff do `AGENTS.md` só proposto).

```text
Respostas:
1. Mantenha a lacuna. Não reformule a pergunta 3. Corrija o AGENTS.md: coletar ou gravar dados de outras coleções continua fora do escopo; ler dados de outras coleções produzidos por terceiros, quando estiverem disponíveis, está dentro do escopo, somente leitura. Na persona, a origem desses dados fica como lacuna: dependem de outros coletores e podem não estar disponíveis.
2. Os selados ficam fora da soma. O valor da coleção é a soma de um exemplar de cada carta avulsa. Os selados entram só na pergunta 2, comparados com as cartas.
3. A divisão da carteira fica para a especificação. Na persona, basta dizer que ela compara cartas avulsas, selados, dólar e CDI.
4. Mantenha "cada coleção", porque a pergunta 4 também vale para as outras coleções quando os dados existirem.
5. Sim. Agora registre em docs/prompts.md a etapa "1 – Persona", com a data de hoje, o texto completo do prompt que eu enviei e o resultado da revisão: "aprovado com ajustes (nome da persona, pergunta 3 sem turma, coleção = DRI inteira, lacunas revisadas, escopo de leitura de outras coleções)". Não registre o Prompt 0 de novo se ele já estiver lá.

Arquivos que você pode alterar agora: docs/00_persona.md, AGENTS.md e docs/prompts.md. Mostre o diff do AGENTS.md antes de salvar.
```

#### Ajuste 3 – aprovação do diff do AGENTS.md

Arquivo alterado: `AGENTS.md`.

```text
Aprovado com a troca para "qualquer dado coletado que não venha das fontes acima". Pode salvar o AGENTS.md.
```

#### Ajuste 4 – troca para "perguntas 3, 4 e 5"

Arquivo alterado: `docs/00_persona.md`.

```text
Na lacuna sobre a origem dos dados das outras coleções, troque "(perguntas 3 e 4)" por "(perguntas 3, 4 e 5)". Não altere mais nada.
```

## Prompt da etapa 2 – Objetivos

```text
[C] Personagem
Você é um product owner técnico de uma equipe de dados. Você traduz a dor da persona em objetivos de negócio mensuráveis, drivers e restrições. Você não escreve requisitos técnicos, não escolhe bibliotecas e não escreve código.

[R] Pedido
Preencha docs/01_objetivos_negocio.md a partir de docs/00_persona.md. Escreva exatamente estes seis objetivos, cada um com descrição, métrica de sucesso verificável e origem:
OBJ-01 série diária contínua de preços da coleção DRI, sem nenhum dia inventado;
OBJ-02 valores em reais com o efeito da carta separado do efeito do câmbio;
OBJ-03 responder às perguntas 1, 2 e 4 da persona para a coleção DRI;
OBJ-04 comparar a DRI com outras coleções recentes (perguntas 3 e 5) quando os dados delas estiverem disponíveis;
OBJ-05 comparar uma carteira hipotética de R$ 1.000 em cartas avulsas e em selados com deixar o dinheiro em dólar ou no CDI;
OBJ-06 projeto reprodutível e auditável a partir de um clone limpo do repositório, sem custo e sem segredo versionado.
Liste também: drivers de negócio (DRV-xx), restrições (RES-xx, com tipo e origem) e o que fica fora do escopo.

[E] Exemplos
| OBJ-01 | Série diária contínua de preços da coleção DRI, sem nenhum dia inventado. | Toda data entre o primeiro e o último dia de coleta tem os arquivos brutos do dia ou aparece na tabela "Dias sem coleta" do README, com o motivo; zero dias preenchidos por estimativa. | Persona: "não tem histórico de preço próprio" |
| DRV-01 | Um dia sem coleta não se recupera depois, porque a fonte só devolve o preço do dia. | Contexto do projeto |
| RES-02 | Custo zero: nenhum serviço pago | financeira | Decisão do autor |

[A] Ajustes
- Cada objetivo precisa de uma métrica verificável por um comando, um teste ou uma observação concreta. Se o valor não estiver nos fatos de Extras, escreva "hipótese: validação pendente" e diga como medir.
- Para OBJ-04, a métrica deve aceitar o resultado parcial: quando os dados de outras coleções não existirem, o painel informa a ausência em vez de mostrar dado vazio ou inventado.
- Restrições têm tipo (técnica, financeira, legal, prazo) e origem.
- Fora do escopo, inclua pelo menos: previsão de preço e recomendação de compra; coleta ou gravação de outras coleções; streaming em tempo real; preço de carta graduada (PSA, CGC); scraping de sites que bloqueiam acesso automatizado.
- Não altere docs/00_persona.md.
- Não escolha tecnologia além das que estão nas restrições.

[T] Tipo de saída
Somente docs/01_objetivos_negocio.md, em Markdown, com tabelas para objetivos, drivers, restrições e fora do escopo. Mostre o plano antes de editar e espere minha confirmação.

[E] Extras
Leia antes: AGENTS.md e docs/00_persona.md.
Fatos e restrições (origem: contexto do projeto, salvo indicação):
- Fonte de preços: TCGCSV, sem chave; pede User-Agent próprio, pausa mínima de 100 ms entre chamadas e no máximo 10.000 requisições por dia; atualiza por volta das 20h UTC; o preço muda uma vez por dia.
- Câmbio: PTAX de fechamento do Banco Central, só em dia útil; no fim de semana e em feriado vale a última PTAX de dia útil anterior, nunca uma posterior.
- CDI: série diária do Banco Central, só em dia útil.
- Filtros de relevância: na pergunta 1, só cartas acima de US$ 1 no primeiro dia; na pergunta 5, só cartas acima de US$ 5; cartas de código digital (raridade Code Card) ficam fora das perguntas 1, 3 e 4.
- Carteira: valor de liquidação diário, unidades inteiras, taxa de venda como parâmetro com 15% como hipótese declarada.
- Repositório público no GitHub; credenciais só no .env e em secrets.
- Execução: GitHub Codespaces com MinIO local; coleta diária agendada no GitHub Actions (decisão do autor; detalhes no plan.md).
- Custo zero (decisão do autor).
- Prazo de entrega: 12/12/2026, 23h59.
- O período observado é de algumas semanas e não sustenta previsão.
Se faltar informação, pergunte. Ao terminar, liste perguntas abertas e pare.
```

### Ajustes da revisão

#### Ajuste 1 – aprovação do plano com ajustes

Arquivo alterado: `docs/01_objetivos_negocio.md` (criado).

```text
Plano aprovado com estes ajustes:

OBJ-02: a variação em reais se decompõe em três partes, não duas: efeito da carta, efeito do câmbio e efeito cruzado, pela identidade (1 + r_brl) = (1 + r_usd) × (1 + r_cambio). A métrica deve dizer que um teste confere essa identidade, com tolerância de arredondamento.

OBJ-05: são cinco carteiras, todas partindo de R$ 1.000 no primeiro dia de coleta:
- selado: unidades inteiras do booster box da coleção; se ele não tiver preço no primeiro dia, o selado de maior preço que tiver preço (escolha registrada em ADR);
- cesta_raras: R$ 100 em cada uma das dez cartas de maior market price no primeiro dia, em unidades inteiras;
- propria: regra definida pelo autor, registrada em ADR antes do primeiro cálculo;
- dolar: R$ 1.000 convertidos pela PTAX de venda do primeiro dia e guardados em dólar;
- cdi: R$ 1.000 corrigidos pelo CDI de cada dia útil, com juros compostos.
A métrica deve incluir: valor de liquidação diário = unidades × market price × (1 − taxa de venda) × PTAX de compra, mais a sobra em caixa, que rende CDI; a composição usa só dados do primeiro dia, e um teste confirma que acrescentar dias posteriores não muda a composição.

Respostas às perguntas abertas:
1. Respondida acima.
2. Sim: dólar comprado pela PTAX de venda e vendido pela PTAX de compra, sem spread nem IOF. Registre como limite declarado.
3. Sim, inclua a P4 das outras coleções no OBJ-04.
4. Coleções recentes = coleções principais do Pokémon TCG lançadas a partir de 2024.

Pode escrever o arquivo.
```

#### Ajuste 2 – encaminhamento das perguntas abertas e registro da etapa

Arquivos alterados: `docs/01_objetivos_negocio.md` e `docs/prompts.md`.

```text
RES-03 pode ficar como "legal".

Na seção de perguntas abertas, registre o encaminhamento de cada uma:
1. cesta_raras: sim, excluem Code Card e selados (só cartas avulsas). O critério de desempate fica para o spec.md.
2. Sim: se o primeiro dia cair em fim de semana ou feriado, vale a PTAX de dia útil anterior, pela mesma regra do OBJ-02.
3. Fica para o plan.md.
4. Fica como hipótese até a primeira coleta.
5. Continua pendente, a validar na primeira coleta.

Depois registre em docs/prompts.md a etapa "2 – Objetivos", com o prompt original e, na subseção "Ajustes da revisão", as minhas mensagens de ajuste desta etapa (a de aprovação do plano e esta), anotando qual arquivo cada uma mudou. Não altere outros arquivos.
```

## Prompt da etapa 3 – Especificação

```text
[C] Personagem
Você é um engenheiro de requisitos de dados. Você escreve requisitos funcionais e não funcionais com critérios de aceite verificáveis. Você não escreve código e só cita tecnologia quando ela já é restrição em docs/01_objetivos_negocio.md ou contrato listado em Extras.

[R] Pedido
Escreva specs/spec.md derivando os requisitos de docs/00_persona.md e docs/01_objetivos_negocio.md. Cubra no mínimo:
1. Coleta diária de produtos e preços da coleção (TCGCSV), da PTAX e do CDI, uma vez por dia depois das 20h UTC, com User-Agent próprio, pausa entre chamadas e repetição com espera crescente.
2. Gravação da resposta original sem alteração, com chave por coleção e data, recusando sobrescrita (inclusive na sincronização para o MinIO local).
3. Silver nas cinco tabelas do contrato comum (Extras), com validação por modelo por tabela, quarentena com motivo e preço ausente gravado como nulo.
4. Gold em esquema estrela sobre a silver de todas as coleções disponíveis.
5. Conversão para reais pela última PTAX de fechamento conhecida no dia do preço, nunca posterior, guardando a cotação aplicada e a data do boletim.
6. Reprocessamento: silver e gold reconstruídas a partir do bruto com um único comando, sem duplicar linhas.
7. Dashboard com as cinco perguntas (métricas em Extras), valores em reais com opção de ver em dólar, filtros de preço mínimo em dólar, imagem das cartas citadas, link da página do produto, decomposição carta/câmbio/cruzado, lacunas visíveis sem interpolação e aviso de que o período não sustenta previsão.
8. Desafio das cinco carteiras (regras em docs/01_objetivos_negocio.md), com as métricas de Extras e resultado no contrato gold_turma.
9. Leitura somente leitura de outras coleções quando disponíveis, com aviso explícito quando ausentes.
10. Dias sem coleta declarados no README.
11. Testes: unidade sem rede; integração com respostas HTTP gravadas para o TCGCSV; integração com MinIO em contêiner descartável.
12. Segredos fora do Git, custo zero e reprodução a partir de clone limpo.

[E] Exemplos
### RF-02: grava a resposta do dia no bruto sem sobrescrever
A resposta original do TCGCSV é gravada sem alteração na chave do dia da coleção.
- Origem: OBJ-01, RES-08
- Critério de aceite:
  - Dado que a chave tcg/raw/tcgplayer/group_id=24269/data=2026-11-02/prices.json já existe
  - Quando a gravação do mesmo dia for executada de novo
  - Então a gravação é recusada, o objeto original continua igual (mesmo hash) e a recusa aparece no log

### RNF-04: conversão nunca usa cotação posterior
- Atributo: correção dos dados
- Origem: OBJ-02, RES-04
- Critério de aceite:
  - Dado preços de 10/10/2026 (sábado), 11/10 (domingo) e 12/10 (feriado) e PTAX de 09/10 e 13/10
  - Quando a conversão for executada
  - Então os três dias usam a PTAX de 09/10 e nenhum usa a de 13/10

[A] Ajustes
- Numere RF-01, RF-02... e RNF-01, RNF-02...; cada requisito tem origem (OBJ, DRV ou RES).
- Todo critério de aceite usa Dado/Quando/Então e pode ser verificado por um comando ou teste.
- Copie os nomes e tipos de colunas do contrato exatamente como em Extras; colunas extras são permitidas, mudar nome ou tipo não.
- Não invente números. Valor ausente = "hipótese: validação pendente". Hipóteses de docs/ continuam hipóteses.
- Resolva aqui as pendências encaminhadas ao spec: desempate da cesta_raras (sugestão: menor product_id) e o grão de cada pergunta.
- Inclua uma seção "Fora do escopo" coerente com docs/01_objetivos_negocio.md.
- Não altere outros arquivos.

[T] Tipo de saída
Somente specs/spec.md, em Markdown, com no máximo quatro páginas. Antes de escrever, mostre só a lista de títulos dos RF e RNF e espere minha confirmação.

[E] Extras
Leia antes: AGENTS.md, docs/00_persona.md, docs/01_objetivos_negocio.md.

Chaves do bruto (MinIO, bucket tcg):
raw/tcgplayer/group_id=24269/data=AAAA-MM-DD/products.json
raw/tcgplayer/group_id=24269/data=AAAA-MM-DD/prices.json
raw/bcb_ptax/group_id=24269/data=AAAA-MM-DD/cotacao.json
raw/bcb_cdi/group_id=24269/data=AAAA-MM-DD/cdi.json

Contrato comum da silver (colunas mínimas):
- colecao: group_id INTEGER, nome VARCHAR, sigla VARCHAR, data_lancamento DATE, responsavel VARCHAR
- produto: product_id INTEGER, group_id INTEGER, nome VARCHAR, tipo_produto VARCHAR ('carta' ou 'selado'), raridade VARCHAR, numero VARCHAR, image_url VARCHAR, url VARCHAR
- preco_diario (grão: produto, acabamento, dia): data DATE, product_id INTEGER, group_id INTEGER, acabamento VARCHAR, market_price DOUBLE, low_price DOUBLE, mid_price DOUBLE, high_price DOUBLE, moeda VARCHAR, fonte VARCHAR, chave_raw VARCHAR
- cambio_diario (dia útil): data DATE, cotacao_compra DOUBLE, cotacao_venda DOUBLE, data_hora_cotacao TIMESTAMP, boletim VARCHAR ('Fechamento'), chave_raw VARCHAR
- cdi_diario (dia útil): data DATE, taxa_dia DOUBLE (% ao dia, como publicada), chave_raw VARCHAR
Caminhos: silver/colecao/group_id=24269/colecao.parquet; silver/produto/group_id=24269/produto.parquet; silver/preco_diario/group_id=24269/data=AAAA-MM-DD/preco.parquet; silver/cambio_diario/group_id=24269/cambio.parquet; silver/cdi_diario/group_id=24269/cdi.parquet

Gold: fato_preco_diario (produto, acabamento, dia: market, low, mid, high, market_price_brl, cotação aplicada, data_ptax), dim_produto, dim_colecao, dim_data, dim_acabamento, fato_cambio_diario (dia de calendário: PTAX aplicada, data do boletim de origem, CDI do dia, zero em dia sem taxa). Dias desde o lançamento calculados na consulta.

Contrato gold_turma: gold_turma/carteira/group_id=24269/carteira.parquet com data DATE, group_id INTEGER, carteira VARCHAR (selado, cesta_raras, propria, dolar, cdi), valor_brl DOUBLE, retorno_acumulado DOUBLE, taxa_venda DOUBLE.

Métricas das perguntas:
- P1: variação % em reais entre o primeiro e o último dia, por carta e acabamento, decomposta em carta, câmbio e cruzado; só cartas acima de US$ 1 no primeiro dia; dois rankings de dez, com imagem e preço inicial e atual em reais.
- P2: índice base 100 no primeiro dia: média dos selados contra a soma do preço das cartas de raridade Double Rare em diante; gráfico de linhas.
- P3: valor da coleção no dia em reais (soma do market_price_brl de um exemplar de cada carta) em índice base 100, por coleção, com a PTAX em índice base 100 no mesmo gráfico; destaca a DRI.
- P4: participação de cada raridade no valor total no último dia e número de cartas que somam 80% do valor; barras empilhadas a 100% por coleção.
- P5: retorno no período contra volatilidade (desvio-padrão dos retornos diários), cartas acima de US$ 5; dispersão com cor por coleção e imagem ao passar o cursor.
- Code Card fora de P1, P3 e P4.

Métricas da carteira: retorno acumulado (valor no último dia / 1000 − 1); excesso sobre o CDI; perda máxima (maior queda % entre um pico e o ponto mais baixo depois dele); dias com preço carregado. Produto sem preço no dia usa o último preço observado só na avaliação da carteira, marcado no painel, sem gravar nada na silver. CDI não rende em fim de semana nem feriado.

Se faltar informação, pergunte. Ao terminar, liste perguntas abertas e pare.
```

### Ajustes da revisão

#### Ajuste 1 – aprovação dos títulos e respostas às perguntas

Arquivo alterado: `specs/spec.md` (criado).

```text
Confirme que existe o RF-15 (P1: rankings de alta e queda com a decomposição carta, câmbio e cruzado); na sua lista ele aparece cortado junto do RF-14.

Respostas:
1. Sim: arquivo de configuração versionado, declarado pelo autor, com nome "SV10: Destined Rivals", sigla "DRI", data_lancamento 2025-05-30 e responsavel "Augusto".
2. Sim: lista ordenada no spec, marcada como hipótese até a primeira coleta. Considere "Double Rare em diante" = Double Rare, Ultra Rare, Illustration Rare, Special Illustration Rare e Hyper Rare; se a fonte trouxer outra raridade, ela entra como pendência na primeira coleta.
3. Sim, como hipótese, com uma exceção: produto com raridade "Code Card" é carta (e fica fora de P1, P3 e P4), nunca selado.
4. Sim: o grão é o par produto × acabamento em todo o projeto. Uma carta em Holofoil e a mesma em Reverse Holofoil contam como itens distintos, inclusive na cesta_raras, na P5 e no "um exemplar de cada carta" da P3 e da P4. Registre essa decisão no spec.
5. Sim: parâmetro configurável, marcado como hipótese. Valores iniciais sugeridos: 3 tentativas, com espera de 2, 4 e 8 segundos.

Mais um detalhe no RF-01: o CDI de um dia útil só é publicado na manhã seguinte, então a coleta diária consulta uma janela recente do CDI (e não só o dia) e grava a resposta inteira.

Pode escrever o arquivo.
```

#### Ajuste 2 – respostas às perguntas abertas e diff do AGENTS.md

Arquivo alterado: `specs/spec.md` (diff do `AGENTS.md` só proposto).

```text
Tamanho: mantenha o formato atual (sem converter em tabelas) e só corte as repetições das seções "Contratos" e "Definições".

Respostas:
1. A gold persistida em tcg/gold/group_id=24269/ é construída sobre a silver de todas as coleções disponíveis: a DRI e as de terceiros, lidas somente para leitura. Isso não é gravar outras coleções: a escrita continua só no nosso prefixo. Ajuste o AGENTS.md: "a silver é derivada exclusivamente da raw da DRI; a gold é derivada da silver da DRI e das silvers de outras coleções disponíveis, lidas somente para leitura". Mostre o diff do AGENTS.md antes de salvar.
2. Sim: a PTAX também é coletada numa janela recente, como o CDI, e o arquivo continua sendo cotacao.json. Se dois brutos trouxerem valores diferentes para a mesma data, a data vai para a quarentena, com a mesma regra do CDI.
3. Sim: as carteiras de cartas e selados compram pela PTAX de venda, sem taxa na compra. Registre como limite declarado.
4. Sim: taxa_venda = 0 nas carteiras dolar e cdi.
5. Sim: o primeiro dia comum a todas as coleções exibidas.
6. Sim: descartar os retornos que atravessam uma lacuna; só contam retornos entre dias consecutivos com preço.
7. Sim, como hipótese a validar na primeira coleta.
8. 10 dias corridos para o CDI e para a PTAX, como parâmetro configurável e marcado como hipótese.

O desempate por acabamento em ordem alfabética está aprovado.

Arquivos que você pode alterar agora: specs/spec.md e AGENTS.md.
```

#### Ajuste 3 – aprovação do diff do AGENTS.md

Arquivo alterado: `AGENTS.md`.

```text
Pode salvar o AGENTS.md.
```

#### Ajuste 4 – quarentena, taxa lado a lado, placar da turma e execução agendada

Arquivos alterados: `specs/spec.md` e `docs/prompts.md`.

```text
Ajustes no specs/spec.md:

1. RF-07: boletins da PTAX diferentes de "Fechamento" são descartados por regra, não vão para a quarentena; troque o exemplo do critério por uma PTAX de fechamento com cotacao_venda ausente. Acrescente que a contagem de linhas em quarentena por tabela aparece no log de cada execução.

2. RF-24 ou RF-25: o painel mostra o resultado de cada carteira com a taxa de venda e sem ela (taxa 0), lado a lado. Critério: a diferença entre as duas versões aparece no painel para as carteiras selado, cesta_raras e propria, e é zero para dolar e cdi.

3. Novo RF-28, placar da turma: o painel lê gold_turma/carteira de todas as coleções disponíveis (somente leitura) e mostra em quantas coleções o selado superou o CDI, em quantas a cesta_raras superou o dólar e qual coleção teve a menor perda máxima. Sem dados de outras coleções, mostra o aviso explícito e só a DRI. Origem: OBJ-04, OBJ-05, RES-13.

4. Novo RNF-13, execução agendada: a coleta roda todo dia depois das 20h UTC sem intervenção manual, com credenciais só em variáveis e secrets. Critério: o histórico de execuções do agendador mostra uma execução por dia no período; dias sem execução bem-sucedida aparecem na tabela "Dias sem coleta". Origem: OBJ-01, DRV-01, RES-06, RES-07.

Não altere outros arquivos. Depois registre esta mensagem em docs/prompts.md, na subseção "Ajustes da revisão" da etapa 3.
```

## Prompt da etapa 4 – Plano

````text
[C] Personagem
Você é um arquiteto de software de dados. Você transforma a spec em arquitetura e justifica cada escolha por um requisito ou restrição. Você não escreve código nesta etapa.

[R] Pedido
Escreva specs/plan.md com:
1. C4 nível 1 (contexto), nível 2 (contêineres) e nível 3 (componentes do pipeline), em blocos Mermaid.
2. Fluxo diário, passo a passo, da coleta ao painel.
3. Tabela de escolhas técnicas: escolha | alternativas consideradas | RF/RNF/RES atendido | ADR previsto.
4. Estrutura de pastas do código e comandos de execução previstos.
5. Riscos técnicos iniciais e perguntas abertas.
O plano deve conter estas decisões, já tomadas pelo autor:
- Coleta no GitHub Actions: workflow agendado diariamente às 20h30 UTC, mais disparo manual (workflow_dispatch). O job usa Python 3.12, busca TCGCSV, PTAX e CDI e grava as respostas originais como arquivos na branch dados-raw, no caminho idêntico à chave do bruto (raw/tcgplayer/group_id=24269/data=AAAA-MM-DD/products.json etc.); recusa gravar se o arquivo do dia já existir; faz commit e push só na branch dados-raw. O job não precisa de credenciais do MinIO, porque não acessa o MinIO.
- MinIO local no Codespace por docker compose, imagem ghcr.io/coollabsio/minio com tag fixada RELEASE.2025-10-15T17-29-55Z (nunca latest), portas 9000 (API) e 9001 (console), volume nomeado e healthcheck com "mc ready local"; credenciais no .env.
- Sincronização: comando local que lê os arquivos da branch dados-raw e envia ao bucket tcg com a mesma chave, conferindo antes se a chave existe (recusa sobrescrita).
- Bibliotecas Python: requests para HTTP; minio (SDK oficial) para gravar e ler objetos; pydantic v2 para os modelos da silver; duckdb com a extensão httpfs para ler e gravar Parquet no MinIO, montar a gold e fazer o ASOF JOIN; streamlit para o painel; pytest, vcrpy (respostas HTTP gravadas) e testcontainers (MinIO descartável) para os testes.
- Silver em Python + pydantic; gold em SQL no DuckDB, lendo a silver de todas as coleções com curinga (s3://tcg/silver/preco_diario/*/*/*.parquet) e gravando só em gold/group_id=24269/ e gold_turma/carteira/group_id=24269/.
- Configuração da coleção em config/colecao.toml (nome, sigla, data_lancamento, responsavel, group_id) e parâmetros (janela de 10 dias, tentativas, esperas, taxa_venda) em config/parametros.toml.
- Comandos únicos por um Makefile: make up (sobe o MinIO), make sync, make silver, make gold, make reprocessar (apaga e reconstrói só silver e gold do nosso prefixo a partir do bruto), make painel, make test, make cobertura (RF-27).
- Logs no padrão logging do Python, na saída padrão, sem nenhum valor de credencial.

[E] Exemplos
```mermaid
flowchart LR
  gha["GitHub Actions: coletor diário"]
  br[("Branch dados-raw")]
  tcg["TCGCSV"]
  gha -->|"HTTPS, User-Agent próprio"| tcg
  gha -->|"commit dos arquivos do dia"| br
```

| Escolha | Alternativas | Requisito/restrição | ADR |
| Bruto versionado na branch dados-raw e sincronizado para o MinIO local | MinIO público pago no Railway; armazenamento S3 gratuito de terceiros; agendador no computador do autor | RF-01, RF-05, RNF-09, RNF-13, RES-02, RES-07 | ADR-001 |

[A] Ajustes
- Os nomes usados nos diagramas são exatamente os nomes usados no texto.
- Toda escolha técnica aponta para RF, RNF ou RES de specs/spec.md ou docs/01_objetivos_negocio.md; escolha sem origem fica marcada "sem requisito correspondente".
- Para cada decisão relevante, liste pelo menos duas alternativas descartadas e o motivo.
- Não acrescente componentes que a spec não pede (fila, orquestrador, banco relacional, ClickHouse, RabbitMQ).
- O comando de reprocessamento só apaga objetos de silver e gold do prefixo group_id=24269; isso precisa ficar explícito, porque o AGENTS.md proíbe exclusões no bruto e fora do nosso prefixo. Aponte se isso exige ajuste no AGENTS.md.
- Indique os ADRs previstos (numere a partir de ADR-001), sem escrevê-los.
- Não altere outros arquivos.

[T] Tipo de saída
Somente specs/plan.md, em Markdown com blocos ```mermaid. Mostre a lista de seções e a tabela de escolhas antes de escrever e espere minha confirmação.

[E] Extras
Leia antes: AGENTS.md, docs/00_persona.md, docs/01_objetivos_negocio.md, specs/spec.md.
Os ADRs serão escritos na etapa de validação; aqui só o número e o título previstos. Sugestão de ADRs: bruto na branch dados-raw com sincronização; imagem do MinIO com tag fixada; esquema estrela na gold; camadas derivadas e reprocessamento; regra da carteira propria; fallback do selado.
Se uma decisão acima contradisser a spec, aponte a contradição e pergunte. Pare ao final.
````

### Ajustes da revisão

#### Ajuste 1 – exclusão restrita, reprocessamento, curingas da gold e decisões não bloqueantes

Arquivo alterado: `specs/plan.md` (criado). Os diffs de `specs/spec.md` e `AGENTS.md` foram mostrados, sem salvar.

```text
Pontos:
1. Opção (a). Ajuste o RNF-03 para: "a única exclusão do código fica numa função que só aceita os prefixos silver/*/group_id=24269/, gold/group_id=24269/ e gold_turma/carteira/group_id=24269/ e recusa qualquer chave em raw/ ou de outro group_id; um teste confirma a recusa". No AGENTS.md, acrescente que make reprocessar, executado pelo autor, é a única exceção à proibição de exclusões, e que o agente continua proibido de executar qualquer exclusão. Mostre os diffs do spec e do AGENTS.md antes de salvar.
2. Sim, o reprocessamento também reconstrói gold_turma/carteira/group_id=24269/.
3. Sim, a gold também lê silver/produto/*/*.parquet e silver/colecao/*/*.parquet de todas as coleções, somente leitura. Câmbio e CDI vêm só da nossa silver.

Decisões para os itens não bloqueantes (entram no plano):
- Atraso do cron: aceito como risco; mitigação: disparo manual (workflow_dispatch) no mesmo dia, antes de 23h59 UTC. Documente no README.
- .gitattributes com "* -text" na branch dados-raw: sim.
- Dia parcial: cada fonte é verificada e gravada de forma independente. A reexecução no mesmo dia busca só as fontes cujo arquivo do dia ainda não existe (o TCGCSV continua no máximo uma vez por dia). Se uma fonte não for gravada no dia, o dia entra na tabela "Dias sem coleta" com o motivo; PTAX e CDI se recuperam pela janela de 10 dias.
- Bloqueio de rede nos testes de unidade: fixture no tests/conftest.py que substitui socket.socket e falha em qualquer conexão, sem biblioteca nova.
- Carteiras: composição e liquidação em funções Python puras, testáveis sem rede; os dados entram e saem pelo DuckDB.
- make cobertura lê a branch dados-raw, que é a fonte de verdade do bruto.
- Healthcheck: confirmar na tarefa de implementação do docker compose.

Arquivos que você pode alterar agora: specs/plan.md, specs/spec.md (só o RNF-03) e AGENTS.md (só a linha da exceção).
```

#### Ajuste 2 – aprovação dos diffs e respostas às perguntas da seção 14

Arquivos alterados: `specs/spec.md` (RNF-03), `AGENTS.md` (linha da exceção), `specs/plan.md` (seções 5, 6, 8, 9, 14 e 15) e `docs/prompts.md`.

```text
Aprovo os dois diffs; pode salvar o spec e o AGENTS.md e marcar os ajustes como aplicados na seção 15.

Respostas às perguntas da seção 14:
1. A branch dados-raw é criada uma única vez pelo autor, numa tarefa de implementação, como branch órfã contendo só o .gitattributes e um README curto; o agente prepara os comandos e o autor executa.
2. Mensagem do commit automático do coletor: "dados(coleta): AAAA-MM-DD [RF-01]".
3. TCG_USER_AGENT é variável do repositório (vars), não secret, porque não é sensível. O workflow do coletor não usa nenhum secret; ele precisa só de permissão contents: write para dar push na branch dados-raw.
Mova essas três da seção 14 para as decisões do plano.

Depois registre em docs/prompts.md a etapa "4 – Plano": o prompt original e, em "Ajustes da revisão", as minhas mensagens desta etapa, na ordem, com o arquivo que cada uma mudou, e o resultado "aprovado com ajustes". Não altere outros arquivos.
```

#### Ajuste 3 – exceção da convenção de commits para o coletor

Arquivos alterados: `AGENTS.md` (convenção de commits) e `docs/prompts.md`.

```text
Ajuste o AGENTS.md, na seção de convenção de commits, acrescentando: "Exceção: os commits automáticos do coletor, feitos só na branch dados-raw, usam o formato dados(coleta): AAAA-MM-DD [RF-01]; a convenção tipo(T-xx): descrição [RF-yy] vale para todos os commits na main." Mostre o diff e, se ficar só essa linha, pode salvar sem esperar. Depois acrescente esta mensagem em "Ajustes da revisão" da etapa 4 no docs/prompts.md.
```

## Prompt da etapa 5 – Tarefas

```text
[C] Personagem
Você é o líder técnico do projeto. Você quebra o plano em tarefas pequenas, cada uma com requisito, verificação executável e evidência esperada. Você não escreve código nesta etapa.

[R] Pedido
Escreva specs/tasks.md a partir de specs/spec.md e specs/plan.md, com uma tabela de tarefas e as colunas: ID | Tarefa | Requisitos | Verificação (comando) | Evidência esperada | Depende de | Executor | Status.
A ordem de execução segue esta prioridade, em blocos:
Bloco A, coleta no ar (prioridade máxima, porque um dia sem coleta não se recupera): estrutura do pacote Python e dependências; bloqueio de rede nos testes de unidade; arquivos de configuração e leitor; cliente HTTP com User-Agent, pausa e repetição; coletor das três fontes com guarda de horário e de duplicidade por arquivo e gravação dos arquivos do dia; criação da branch órfã dados-raw com .gitattributes; workflow do GitHub Actions com agendamento e disparo manual; primeira execução manual do workflow, conferida na branch.
Bloco B, armazenamento local: docker compose do MinIO com healthcheck; sincronizador com recusa de sobrescrita; testes de integração com MinIO descartável e com respostas HTTP gravadas.
Bloco C, lakehouse: modelos pydantic e silver com quarentena; função única de exclusão com guarda de prefixo; gold em estrela com ASOF JOIN e fato de câmbio; reprocessamento.
Bloco D, análise: decomposição carta/câmbio/cruzado; métricas das perguntas P1 a P5; composição, liquidação e métricas das carteiras; gravação em gold_turma.
Bloco E, painel e operação: painel com as cinco perguntas, carteiras e placar; verificação de cobertura; README completo.
Separe as tarefas manuais do autor (criar a branch dados-raw, criar a variável TCG_USER_AGENT no GitHub, disparar o workflow, preencher o .env) das tarefas do agente.

[E] Exemplos
| T-05 | Coletor das três fontes: verifica cada arquivo do dia antes de qualquer requisição, recusa antes das 20h UTC e grava as respostas originais em raw/... | RF-01, RF-02, RF-04 | pytest tests/unidade/test_coletor.py | testes de recusa por horário, recusa por arquivo existente e hash igual ao corpo passam | T-03, T-04 | agente | [ ] |
| T-07 | Criar a branch órfã dados-raw com .gitattributes ("* -text") e README curto | RF-02, ADR-001 | git ls-tree origin/dados-raw | a branch existe no GitHub com os dois arquivos | T-06 | autor | [ ] |

[A] Ajustes
- Cada tarefa cabe num único prompt de implementação e toca poucos arquivos, com o teste junto.
- Todo RF e RNF de specs/spec.md aparece em pelo menos uma tarefa; os que não couberem vão para uma seção "Requisitos sem tarefa", com o motivo.
- A verificação é um comando que o autor consegue executar e ver passar ou falhar.
- Marque as tarefas que exigem rede ou contêiner.
- A etapa de validação (ATAM, ADRs, matriz de rastreabilidade) entra como último bloco, com tarefas próprias.
- Todas as tarefas começam com status [ ].
- Não altere outros arquivos.

[T] Tipo de saída
Somente specs/tasks.md, em Markdown. Antes de escrever, mostre só a lista de tarefas (ID, título, requisitos e executor) e espere minha confirmação.

[E] Extras
Leia antes: AGENTS.md, specs/spec.md e specs/plan.md.
Ao final do arquivo, inclua uma seção "Cobertura" com a lista de RF e RNF e a tarefa que atende cada um.
Se faltar informação, pergunte. Pare ao final.
```

### Ajustes da revisão

#### Ajuste 1 – aprovação da lista com ajustes

Arquivo alterado: `specs/tasks.md` (criado).

```text
Lista aprovada, com as seis decisões, e estes ajustes:

1. Os ADRs saem do T-47 e vão para logo antes da primeira tarefa que orientam, cada um como tarefa própria do agente, revisada e commitada antes do código:
- ADR-001 (bruto na branch dados-raw com sincronização): antes do T-07.
- ADR-002 (imagem do MinIO com tag fixada): antes do T-13.
- ADR-003 (esquema estrela na gold e leitura de outras coleções): antes do T-26.
- ADR-004 (camadas derivadas e reprocessamento): antes do T-20.
- ADR-006 (fallback do selado): antes do T-36, depois do T-12, porque depende de saber se o booster box tem preço.
O ADR-005 continua no T-35. Renumere as tarefas.

2. Bloco F:
- A matriz de rastreabilidade usa o prompt 11.2 do enunciado da Aula 08.
- Acrescente uma tarefa final de autoauditoria com o prompt 11.1 do enunciado, gravando docs/auditoria_final.md, sem corrigir nada.
- Acrescente uma tarefa de registro de pendências em docs/pendencias_aula08.md.

Pode escrever o specs/tasks.md.
```

## Prompt de implementação padrão (etapa 6)

Usado em cada tarefa de `specs/tasks.md`, trocando apenas o identificador da tarefa (T-01 no texto abaixo).

```text
[C] Personagem
Você é um engenheiro de dados que implementa com disciplina de testes. Você executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente a tarefa T-01 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos que vai criar ou alterar, o teste que vai escrever e o comando de verificação;
2. espere minha confirmação;
3. crie ou altere os arquivos, com o teste junto;
4. execute a verificação indicada na tarefa e mostre a saída real;
5. se passou: salve a saída em docs/evidencias/T-xx_<nome>.txt, marque a tarefa como [x] em specs/tasks.md, acrescente em docs/prompts.md uma linha na tabela (data | T-xx | "prompt de implementação padrão" | resultado) e proponha a mensagem de commit no formato tipo(T-xx): descrição [RF-yy].

[E] Exemplos
Evidência bem registrada (docs/evidencias/T-04_cliente_http.txt):
$ pytest tests/unidade/test_cliente_http.py -v
tests/unidade/test_cliente_http.py::test_user_agent_em_toda_requisicao PASSED
tests/unidade/test_cliente_http.py::test_pausa_minima_100ms PASSED
tests/unidade/test_cliente_http.py::test_repeticao_com_espera_crescente PASSED
3 passed in 0.41s
Mensagem de commit: feat(T-04): cliente HTTP com User-Agent, pausa e repetição [RF-03]

[A] Ajustes
- Faça somente a tarefa pedida. Não adiante outras tarefas.
- Siga o AGENTS.md, specs/spec.md e specs/plan.md; se a tarefa contradisser algum deles, pare e pergunte.
- Não leia nem imprima o .env; não escreva credenciais em código, log, evidência ou commit.
- Não execute exclusões no MinIO nem git push --force; não faça git commit nem git push.
- Se a verificação falhar, mostre o erro e tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída real do comando.

[T] Tipo de saída
Os arquivos da tarefa, a evidência, specs/tasks.md e docs/prompts.md atualizados, e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia antes: AGENTS.md, specs/spec.md, specs/plan.md e specs/tasks.md.
Nesta primeira tarefa, registre também em docs/prompts.md o texto completo deste prompt numa seção "Prompt de implementação padrão (etapa 6)".
Pare ao final da tarefa.
```

## Prompt da T-07 – ADR-001

```text
[C] Personagem
Você é um arquiteto de software de dados. Você registra uma decisão já tomada pelo autor, com as alternativas descartadas e os custos dela. Você não escreve código nesta etapa.

[R] Pedido
Execute a tarefa T-07 de specs/tasks.md: escreva docs/adr/ADR-001-bruto-branch-dados-raw.md registrando a decisão de gravar o bruto como arquivos na branch órfã dados-raw, a partir do Coletor diário no GitHub Actions, e sincronizá-lo para o MinIO local no Codespace.
Use estas seções: Status (aceito, com a data de hoje); Contexto e forças; Requisitos e cenários relacionados; Alternativas consideradas; Decisão e táticas; Consequências positivas; Consequências negativas; Riscos; Evidência necessária; Condição de revisão.

[E] Exemplos
Trecho bem escrito:
## Alternativas consideradas
| Alternativa | Por que foi descartada |
| MinIO publicado no Railway | O trial tem crédito único de US$ 5 por 30 dias e o plano gratuito não sustenta um serviço ligado o tempo todo (RES-02); o volume é apagado após o fim dos créditos. |

Trecho mal escrito (não faça assim):
## Decisão
Usamos GitHub porque é melhor.

[A] Ajustes
- Alternativas obrigatórias, cada uma com o motivo do descarte: MinIO publicado no Railway; gravar direto no MinIO da turma (o endpoint da API não está disponível para o projeto e a orientação recebida foi usar o MinIO local); armazenamento S3 gratuito de terceiros (exige conta externa e credencial em secret); agendador no computador do autor (depende da máquina ligada todo dia); artifacts do GitHub Actions (expiram e não têm chave fixa); bruto na branch main (mistura dados e código).
- Cite táticas pelo nome e pelo atributo de qualidade que atendem (por exemplo: limitar exposição, para segurança, porque o workflow não usa nenhum secret; persistência em armazenamento versionado, para durabilidade; verificação de existência antes da gravação, para integridade).
- Consequências negativas reais, entre elas: o bruto existe em dois lugares (branch e MinIO local) e precisa da sincronização; dependência do GitHub e do horário do agendador, que pode atrasar; o repositório cresce a cada dia (tamanho diário: hipótese: validação pendente na primeira coleta).
- Riscos com mitigação: atraso ou falha do cron (disparo manual no mesmo dia, antes de 23h59 UTC); push concorrente na branch (concorrência no workflow); alteração de bytes por conversão de fim de linha (.gitattributes com "* -text").
- Condição de revisão: se for disponibilizado o endpoint da API S3 do MinIO da turma, reavaliar a gravação direta nele.
- Não invente números; use "hipótese: validação pendente" onde faltar valor.
- Escreva como decisão do autor, sem citar material de aula.
- Não altere nenhum outro arquivo além de, no final, specs/tasks.md (T-07 como [x]) e docs/prompts.md (uma linha na tabela, com este prompt registrado numa seção própria).

[T] Tipo de saída
Somente docs/adr/ADR-001-bruto-branch-dados-raw.md, em Markdown, com no máximo duas páginas. Mostre o rascunho completo antes de salvar e espere minha confirmação.

[E] Extras
Leia antes: AGENTS.md, docs/01_objetivos_negocio.md, specs/spec.md (RF-01, RF-02, RF-04, RF-05, RNF-03, RNF-08, RNF-09, RNF-13) e specs/plan.md (seções 5, 6 e 7).
Ao final, proponha a mensagem de commit docs(T-07): ADR-001 bruto na branch dados-raw [RF-01, RF-05]. Pare ao final.
```

## Prompt da T-14 – ADR-002

```text
[C] Personagem
Você é um arquiteto de software de dados. Você registra uma decisão já tomada pelo autor, com as alternativas descartadas e os custos dela. Você não escreve código nesta etapa.

[R] Pedido
Execute a tarefa T-14 de specs/tasks.md: escreva o ADR-002 registrando a decisão de rodar o MinIO local no Codespace por docker compose com a imagem ghcr.io/coollabsio/minio, tag fixada RELEASE.2025-10-15T17-29-55Z, portas 9000 (API) e 9001 (console), volume nomeado e healthcheck com "mc ready local". Use o nome de arquivo que está na T-14 do specs/tasks.md.
Use as mesmas seções do ADR-001: Status (aceito, com a data de hoje); Contexto e forças; Requisitos e cenários relacionados; Alternativas consideradas; Decisão e táticas; Consequências positivas; Consequências negativas; Riscos; Evidência necessária; Condição de revisão.

[E] Exemplos
Siga o formato e o nível de detalhe de docs/adr/ADR-001-bruto-dados-raw.md.

[A] Ajustes
- Fatos de contexto, a registrar como fatos: a edição comunitária do MinIO entrou em modo de manutenção em dezembro de 2025, o repositório foi arquivado em abril de 2026 e deixaram de ser publicadas imagens Docker oficiais; a imagem da coolLabs é construída a partir das releases oficiais e é a usada pelo template de MinIO do Railway; ela já traz o cliente mc e não traz curl nem wget, por isso o healthcheck usa "mc ready local".
- Alternativas obrigatórias, cada uma com o motivo do descarte: tag latest da coolLabs (cada execução poderia rodar um binário diferente, o que quebra a reprodução); imagem minio/minio antiga do Docker Hub (sem atualizações oficiais); compilar o MinIO a partir do código-fonte (tempo de build e manutenção sem ganho para o projeto); outro object storage compatível com S3, como o RustFS (o projeto já está desenhado sobre o MinIO e a troca não atende nenhum requisito a mais).
- Táticas pelo nome e atributo: vínculo em tempo de configuração (endpoint e credenciais no .env), para modificabilidade; versão fixada, para reprodutibilidade; monitoramento por healthcheck, para disponibilidade; separar estado (volume nomeado) da computação (contêiner), para durabilidade.
- Consequências negativas reais, entre elas: correções de segurança exigem trocar a tag manualmente; dependência de um mantenedor terceiro (coolLabs); o console na porta 9001 dá acesso total e não pode ter a porta encaminhada como pública no Codespace; o volume some se o Codespace for apagado (mitigado pela branch dados-raw, ADR-001).
- Condição de revisão: se a coolLabs deixar de publicar a imagem ou surgir falha de segurança na tag fixada.
- Não invente números; use "hipótese: validação pendente" onde faltar valor. O comportamento do healthcheck na imagem ainda será confirmado na T-15: registre como evidência necessária.
- Escreva como decisão do autor, sem citar material de aula.
- Não altere nenhum outro arquivo além de, no final, specs/tasks.md (T-14 como [x]) e docs/prompts.md (uma linha na tabela, com este prompt registrado numa seção própria).

[T] Tipo de saída
Somente o arquivo do ADR-002, em Markdown, com no máximo duas páginas. Mostre o rascunho completo antes de salvar e espere minha confirmação.

[E] Extras
Leia antes: AGENTS.md, docs/adr/ADR-001-bruto-dados-raw.md, specs/spec.md (RF-05, RNF-07, RNF-09, RNF-10) e specs/plan.md (seções 6, 8 e 9).
Ao final, proponha a mensagem de commit docs(T-14): ADR-002 imagem do MinIO com tag fixada [RNF-10]. Pare ao final.
```

## Prompt da T-22 – ADR-004

```text
[C] Personagem
Você é um arquiteto de software de dados. Você registra uma decisão já tomada pelo autor, com as alternativas descartadas e os custos dela. Você não escreve código nesta etapa.

[R] Pedido
Execute a tarefa T-22 de specs/tasks.md: escreva o ADR-004 registrando a decisão de tratar silver, gold e gold_turma como camadas derivadas, reconstruíveis a partir do bruto com um único comando (make reprocessar), que apaga e reconstrói só os objetos do nosso prefixo por meio de uma função única de exclusão com guarda de prefixo. Use o nome de arquivo que está na T-22 do specs/tasks.md.
Use as mesmas seções do ADR-001: Status (aceito, com a data de hoje); Contexto e forças; Requisitos e cenários relacionados; Alternativas consideradas; Decisão e táticas; Consequências positivas; Consequências negativas; Riscos; Evidência necessária; Condição de revisão.

[E] Exemplos
Siga o formato e o nível de detalhe de docs/adr/ADR-001-bruto-dados-raw.md.

[A] Ajustes
- A função de exclusão aceita só silver/*/group_id=24269/, gold/group_id=24269/ e gold_turma/carteira/group_id=24269/ e recusa qualquer chave em raw/ ou de outro group_id (RNF-03); o agente nunca executa o reprocessamento, só o autor (AGENTS.md).
- Alternativas obrigatórias, cada uma com o motivo do descarte: sobrescrever as chaves sem apagar (deixa objetos órfãos quando uma partição deixa de existir); versionar cada execução no caminho (muda o contrato comum da silver); processamento incremental com merge (mais complexo e com risco de duplicar linhas); formato de tabela transacional como Delta ou Iceberg (fora da stack escolhida e do escopo).
- Táticas pelo nome e atributo: reconstrução a partir da fonte de verdade, para recuperabilidade; operação idempotente, para confiabilidade; ponto único de exclusão com guarda de prefixo, para integridade e segurança; separação entre camada imutável e camadas derivadas, para modificabilidade.
- Consequências negativas reais, entre elas: o tempo de reprocessamento cresce com o número de dias (valor: hipótese: validação pendente); durante o reprocessamento a silver e a gold ficam incompletas, e o painel não deve ser consultado nesse intervalo; o código passa a ter uma operação de exclusão, mesmo que restrita.
- Evidência necessária: teste de recusa da função de exclusão para raw/ e outro group_id (T-23); teste de idempotência do reprocessamento (tarefa do make reprocessar); pipeline completo sem chave fora do prefixo (tarefa do pipeline contra MinIO de teste). Confira os números dessas tarefas no tasks.md.
- Condição de revisão: se o tempo de reprocessamento ficar inviável para o uso diário, avaliar processamento incremental.
- Não invente números; use "hipótese: validação pendente" onde faltar valor.
- Escreva como decisão do autor, sem citar material de aula.
- Não altere nenhum outro arquivo além de, no final, specs/tasks.md (T-22 como [x]) e docs/prompts.md (uma linha na tabela, com este prompt registrado numa seção própria).

[T] Tipo de saída
Somente o arquivo do ADR-004, em Markdown, com no máximo duas páginas. Mostre o rascunho completo antes de salvar e espere minha confirmação.

[E] Extras
Leia antes: AGENTS.md, docs/adr/ADR-001-bruto-dados-raw.md, specs/spec.md (RF-13, RNF-03, RNF-04, RNF-11) e specs/plan.md (seção de reprocessamento e exclusões).
Ao final, proponha a mensagem de commit docs(T-22): ADR-004 camadas derivadas e reprocessamento [RF-13, RNF-03]. Pare ao final.
```

## Prompt da T-57 – Data de referência

```text
[C] Personagem
Você é um engenheiro de dados que corrige um defeito em produção com disciplina SDD: primeiro especificação e decisão, depois código e teste.

[R] Pedido
As execuções agendadas coleta #2 e #3 do workflow rodaram com mais de 4 horas de atraso do GitHub, depois da meia-noite UTC, e o coletor recusou por horário (código 2), perdendo o dia 2026-11-04. Corrija com uma nova tarefa T-57, nesta ordem, parando para minha aprovação nos pontos indicados:
1. Confirme a causa pelos logs (gh run view das execuções #2 e #3) e registre a saída em docs/evidencias/T-57_diagnostico.txt.
2. Proponha o diff do specs/spec.md (Definições, RF-01, RF-04 e RNF-13): a "data da coleta" passa a ser a "data de referência" do ciclo do TCGCSV, ou seja, a coleta feita entre 20h UTC do dia D e 20h UTC do dia D+1 grava como data=D. A guarda de duplicidade por arquivo continua igual; a recusa por horário deixa de existir. Proponha também a linha da T-57 no specs/tasks.md e o ADR-007 (data de referência pelo ciclo do TCGCSV e agendamento redundante), com as seções dos ADRs anteriores, citando o atraso real do agendador como contexto e o risco de pegar o preço antigo se a coleta rodar logo depois das 20h UTC antes da atualização da fonte. PARE e espere minha aprovação.
3. Depois de aprovado: altere a guarda e o coletor, atualize os testes (casos mínimos: 2026-11-05T00:59Z grava data=2026-11-04; 2026-11-04T20:30Z grava data=2026-11-04; 2026-11-05T19:59Z grava data=2026-11-04; 2026-11-05T20:00Z grava data=2026-11-05; arquivos do dia de referência já existentes não geram requisição) e a janela de PTAX e CDI calculada a partir da data de referência.
4. No .github/workflows/coleta.yml, mantenha o cron 30 20 * * * e acrescente um segundo horário de reserva, 30 6 * * * (06h30 UTC), atualizando o teste do workflow.
5. Rode a suíte completa e mostre a saída real.

[E] Exemplos
Commit esperado ao final: fix(T-57): data de referência pelo ciclo do TCGCSV e agendamento de reserva [RF-01, RF-04, RNF-13]

[A] Ajustes
- Não faça nenhuma requisição ao TCGCSV nem ao Banco Central nesta tarefa.
- Não altere nada na branch dados-raw; não faça commit nem push.
- Não leia o .env.
- A coleta de 2026-11-03 já gravada continua válida e não deve ser tocada.
- Escreva o ADR como decisão do autor, sem citar material de aula.

[T] Tipo de saída
Primeiro: diagnóstico, diffs da spec e do tasks.md e rascunho do ADR-007, e pare. Depois da aprovação: código, testes, workflow, evidências, specs/tasks.md (T-57 como [x]) e docs/prompts.md atualizados, e o resumo com a mensagem de commit.

[E] Extras
Leia antes: AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md, docs/adr/ADR-001-bruto-dados-raw.md, src/tcg/coleta/ e .github/workflows/coleta.yml.
```

Resposta de aprovação do autor:

```text
Aprovo os diffs da spec, a linha da T-57 e o ADR-007, trocando a data do Status para "Aceito em 2026-11-04" (data local, como nos outros ADRs). Aprovo também as decisões 1, 2 e 3. Na decisão 4, faremos dois commits: primeiro os documentos (spec, tasks, plan, AGENTS e ADR-007), depois o código, os testes e o workflow. Pode seguir com as etapas 3 a 5 e, no resumo final, liste quais arquivos vão em cada um dos dois commits.
```

## Prompt da T-29 – ADR-003

```text
[C] Personagem
Você é um arquiteto de software de dados. Você registra uma decisão já tomada pelo autor, com as alternativas descartadas e os custos dela. Você não escreve código nesta etapa.

[R] Pedido
Execute a tarefa T-29 de specs/tasks.md: escreva o ADR-003 registrando a decisão de modelar a gold como esquema estrela no DuckDB, com fato_preco_diario (grão: produto × acabamento × dia), fato_cambio_diario (dia de calendário), dim_produto, dim_colecao, dim_data e dim_acabamento, construída sobre a silver da DRI e das outras coleções disponíveis, lidas por curinga e somente para leitura, com gravação só em gold/group_id=24269/. Use o nome de arquivo que está na T-29 do specs/tasks.md.
Use as mesmas seções dos ADRs anteriores: Status (aceito, com a data de hoje); Contexto e forças; Requisitos e cenários relacionados; Alternativas consideradas; Decisão e táticas; Consequências positivas; Consequências negativas; Riscos; Evidência necessária; Condição de revisão.

[E] Exemplos
Siga o formato e o nível de detalhe de docs/adr/ADR-004-camadas-derivadas.md e docs/adr/ADR-007-data-referencia-ciclo-tcgcsv.md.

[A] Ajustes
- No contexto ou nos requisitos, mostre como cada uma das cinco perguntas da persona (P1 a P5) e o desafio das carteiras é respondido como agregação do fato por alguma dimensão; cite os RF de cada pergunta.
- Registre as decisões de modelagem: o fato guarda market_price_brl, a cotação aplicada e data_ptax (ASOF JOIN, nunca cotação posterior); dias desde o lançamento são calculados na consulta, a partir da data do fato e da data de lançamento da coleção, sem coluna guardada; a leitura da silver usa hive_partitioning = false, porque group_id já é coluna do contrato (nota da T-24); uma silver de outra coleção fora do contrato é ignorada com aviso no log.
- Alternativas obrigatórias, cada uma com o motivo do descarte: tabela única larga (duplica atributos de produto e coleção a cada dia); snowflake (normalização a mais sem ganho para as perguntas); servidor analítico como ClickHouse ou Postgres (exige serviço sempre ligado, contra o custo zero); views sem materialização (recalcula tudo a cada consulta do painel); copiar as silvers de outras coleções para o nosso prefixo (viola a escrita só em group_id=24269); lista fixa de group_ids em configuração (precisa de manutenção a cada coleção nova).
- Táticas pelo nome e atributo, por exemplo: modelo dimensional, para consultabilidade e modificabilidade; leitura por curinga, para extensibilidade; isolamento de falhas por coleção, para disponibilidade; fato com a cotação aplicada e a data do boletim, para auditabilidade.
- Consequências negativas reais, entre elas: a gold depende de outras silvers seguirem o contrato; a gold é refeita inteira a cada execução (tempo: hipótese: validação pendente); as perguntas 3 e 5 ficam parciais enquanto não houver outras coleções.
- Não invente números; use "hipótese: validação pendente" onde faltar valor.
- Escreva como decisão do autor, sem citar material de aula.
- Não altere nenhum outro arquivo além de, no final, specs/tasks.md (T-29 como [x]) e docs/prompts.md (uma linha na tabela, com este prompt registrado numa seção própria).

[T] Tipo de saída
Somente o arquivo do ADR-003, em Markdown, com no máximo duas páginas e meia. Mostre o rascunho completo antes de salvar e espere minha confirmação.

[E] Extras
Leia antes: AGENTS.md, docs/adr/ADR-004-camadas-derivadas.md, specs/spec.md (RF-10 a RF-28) e specs/plan.md (seções 6 e 7).
Ao final, proponha a mensagem de commit docs(T-29): ADR-003 esquema estrela na gold [RF-10, RF-11, RF-12]. Pare ao final.
```

Resposta de aprovação do autor:

```text
Aprovado. Fixe o nome da coluna como cotacao_aplicada (a cotação de venda usada na conversão) no ADR, e mantenha o risco do acoplamento à PTAX da DRI e o placar fora da estrela. Pode salvar, marcar a T-29 e registrar o prompt.
```

## Prompt da T-58 – Data lake da turma no RustFS

```text
[C] Personagem
Você é um arquiteto e engenheiro de dados que conduz uma mudança de infraestrutura com disciplina SDD: primeiro decisão e especificação, depois código e teste.

[R] Pedido
O professor passou a usar como data lake da turma um RustFS compatível com S3, em https://s3.afonsolelis.tech (região us-east-1, endereçamento por caminho), bucket tcg, com uma credencial compartilhada da turma. O autor já apontou o .env para ele e rodou make sync, gravando o bruto da DRI em tcg/raw/*/group_id=24269/ (evidência em docs/evidencias/T-58_primeira_sync_rustfs.txt). Registre e conclua essa migração como a tarefa T-58, nesta ordem, parando para minha aprovação onde indicado:
1. Proponha, sem salvar:
   - o ADR-008 (data lake da turma no RustFS), com as seções dos ADRs anteriores, registrando: o RustFS passa a ser o armazenamento oficial de bruto, silver, gold e gold_turma; o MinIO local continua só para desenvolvimento e para os testes de integração (que seguem com a imagem do ADR-002); a branch dados-raw continua como fonte de verdade do bruto; e a decisão de acrescentar ao workflow da coleta um passo que sincroniza a branch com o RustFS todo dia, usando as credenciais em secrets do GitHub. Diga quais partes do ADR-001 e do ADR-002 ele substitui. Inclua entre as alternativas: manter só o make sync manual; o workflow gravar direto no RustFS sem a branch; continuar no MinIO local. Entre os riscos: a credencial é compartilhada e de administrador, então a guarda de prefixo é a única proteção dos dados dos colegas; o workflow passa a usar secrets.
   - os diffs do specs/spec.md, do specs/plan.md (diagramas C4, ambientes e fluxo diário) e do AGENTS.md (política de segredos cobrindo a chave da turma e os secrets do GitHub) que trocam "MinIO local" por "RustFS da turma" onde for o armazenamento oficial;
   - a linha da T-58 no specs/tasks.md.
   Pare e espere minha aprovação.
2. Depois de aprovado, implemente:
   - o passo de sincronização no .github/workflows/coleta.yml: roda depois do commit e do push na dados-raw, só quando houver arquivos novos ou quando o coletor terminar com 0 ou 1; lê MINIO_ENDPOINT, MINIO_ACCESS_KEY e MINIO_SECRET_KEY de secrets e MINIO_SECURE=true; uma falha nesse passo marca o job como falho, mas não desfaz o push na branch;
   - o teste do workflow cobrindo esse passo (secrets só nesse passo, nunca em echo ou log);
   - o .env.example com o endpoint do RustFS e MINIO_SECURE=true, sem nenhuma credencial;
   - a seção do README sobre o data lake (endereço do RustFS, que as credenciais vêm do canal da turma e ficam só no .env e nos secrets, e como apontar o .env para o MinIO local em desenvolvimento).
3. Rode a suíte completa e mostre a saída real.

[E] Exemplos
Commits esperados, na ordem: docs(T-58): ADR-008 data lake da turma no RustFS [RNF-13]; feat(T-58): workflow sincroniza a dados-raw com o RustFS [RF-05, RNF-13].

[A] Ajustes
- Não leia nem imprima o .env; a credencial da turma nunca aparece em arquivo, log, evidência, diff ou mensagem.
- Não execute make sync, make silver, make gold, exclusões nem qualquer comando contra o RustFS ou o MinIO local; não faça requisição às fontes.
- Mantenha os nomes das variáveis MINIO_* (registre no ADR que elas apontam para qualquer servidor S3); se achar que vale renomear, só proponha.
- Não faça commit nem push.
- Escreva os documentos como decisão do autor, sem citar material de aula.
- Responda em português do Brasil.

[T] Tipo de saída
Primeiro: rascunho do ADR-008, diffs da spec, do plan e do AGENTS.md e a linha da T-58, e pare. Depois da aprovação: workflow, teste, .env.example, README, evidência da suíte, specs/tasks.md (T-58 como [x]) e docs/prompts.md atualizados, e a lista de arquivos de cada um dos dois commits.

[E] Extras
Leia antes: AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md, docs/adr/ADR-001-bruto-dados-raw.md, docs/adr/ADR-002-imagem-minio.md, docs/adr/ADR-007-data-referencia-ciclo-tcgcsv.md, .github/workflows/coleta.yml, .env.example e docs/evidencias/T-58_primeira_sync_rustfs.txt.
```

Resposta de aprovação do autor:

```text
Aprovo o ADR-008, os diffs da spec, do plan e do AGENTS.md e a linha da T-58 no Bloco B, renomeado para "Bloco B: armazenamento".
Decisões: 1) o passo roda sempre que o coletor termina com 0 ou 1, mesmo sem arquivo novo, e só se o passo "publicar" tiver dado certo; 2) os secrets serão criados por mim pelo site do GitHub, não por gh secret set; 3) as variáveis MINIO_* não serão renomeadas; 4) inclua também o ajuste da RES-07 em docs/01_objetivos_negocio.md (e de docs/00_persona.md, se houver menção ao MinIO local como armazenamento oficial) e da docstring de src/tcg/lake/duckdb.py, mostrando os diffs no resumo final.
Pode salvar e seguir para a etapa 2. No resumo final, liste os arquivos de cada commit: o primeiro com ADR-008, spec, plan, AGENTS.md, tasks, docs de persona e objetivos e a evidência da primeira sync; o segundo com workflow, teste, .env.example, README, docstring, evidência da suíte e prompts.
```
