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
| 2026-11-09 | T-33 | "prompt de implementação padrão" | Criados pelo agente `src/tcg/reprocessar.py` (apaga pela Guarda de prefixo só `silver/*/group_id=24269/`, `gold/group_id=24269/` e `gold_turma/carteira/group_id=24269/` e reconstrói silver e gold a partir do bruto), `tests/unidade/test_reprocessar.py` e `tests/integracao/test_reprocessar_integracao.py`; alvo `make reprocessar` no `Makefile`. Teste de integração executado pelo autor contra o MinIO descartável (o agente não executa exclusões, conforme o AGENTS.md): 5 passed em 6,27 s; sem confirmação nada muda; a primeira execução apaga só os órfãos derivados da DRI; raw e prefixos de terceiros mantêm o hash; duas execuções seguidas com as mesmas chaves, contagens e conteúdo, 446 preços e 281 produtos na silver e 446 linhas em `fato_preco_diario` por execução (iguais ao bruto real da T-13 e da T-28, conferidas pelas asserções do teste, já que a saída do pytest não imprime as contagens); nenhuma chave de grão duplicada; evidência em `docs/evidencias/T-33_reprocessar.txt` |
| 2026-11-12 | T-34 | "prompt de implementação padrão" | plano aprovado sem ajustes; o autor autorizou o agente a rodar o teste, porque encerrar o contêiner descartável não conta como exclusão. Criado `tests/integracao/test_pipeline.py` (MinIO descartável da T-19, bucket `tcg-pipeline`): objetos de terceiros (`group_id=99999`) em raw, silver, gold e gold_turma; coleta com o cassete da T-20; branch `dados-raw` num remoto bare temporário e `sincronizador.executar`; `construir_silver`; `construir_gold`. Verifica: chaves novas ou alteradas só em `raw|silver/*/group_id=24269/` e `gold/group_id=24269/`; objetos de terceiros com o mesmo hash; bruto com o SHA-256 do manifesto; gold incluindo o 99999 sem gravar no prefixo dele; linha sorteada de `fato_preco_diario` (semente 34: product_id 632934, Reverse Holofoil, US$ 0,33) com `chave_raw` existente e contendo o produto e o preço; log sem credenciais. Nenhum código em `src/` alterado. 1ª execução falhou (httpfs não encontrado, porque o `HOME` temporário do git valia também para o DuckDB); corrigido restringindo o `HOME` à criação da branch e à sincronização; 2ª execução: 8 passed. `pytest -q` interrompe na coleta por erro anterior à T-34 (`tests/unidade/test_reprocessar.py` e `tests/integracao/test_reprocessar.py` com o mesmo nome de módulo); suíte sem o teste de exclusão da T-33, que só o autor roda: 289 passed; nenhum contêiner de teste restante; evidência em `docs/evidencias/T-34_pipeline.txt`; pendência resolvida no mesmo dia, como parte da T-33: o teste de integração foi renomeado para `tests/integracao/test_reprocessar_integracao.py` |
| 2026-11-12 | T-35 | "prompt de implementação padrão" | plano aprovado com dois acréscimos do autor: teste do caso US$ 100 → 110 com PTAX 5,00 → 5,25 (carta 10%, câmbio 5%, cruzado 0,5%, total 15,5%) e `perguntas.py` na árvore da seção 9 do `specs/plan.md`. Criados `src/tcg/gold/perguntas.py` (`decompor`, função pura, e `decomposicao_por_item`, SQL DuckDB sobre `fato_preco_diario` usando `market_price` e `cotacao_aplicada` do primeiro e do último dia, sem preencher lacunas) e `tests/unidade/test_decomposicao.py` (dois casos conhecidos, 1.000 casos gerados com semente 35, entradas não positivas e SQL sobre fato em memória); as duas identidades do RNF-02 ficam dentro de 1e-9; filtros e rankings da P1 ficam para a T-36; 8 passed; evidência em `docs/evidencias/T-35_decomposicao.txt` |
| 2026-11-12 | T-36 | "prompt de implementação padrão" | plano aprovado com três ajustes do autor: 1) filtro de preço mínimo estritamente maior (`>`), seguindo o "acima de US$ 1" do RF-15 e valendo também para a P5; texto do critério do RF-14 alinhado em `specs/spec.md` ("menor ou igual ao mínimo" some); 2) alta só com r_brl > 0 e queda só com r_brl < 0, até dez itens cada; 3) P2 com cestas fixas: só entram selados e cartas Double Rare em diante com preço em todos os dias do período, um item sem preço em algum dia sai da cesta inteira, nada é preenchido, e a função devolve a quantidade de itens de cada cesta; regra registrada no RF-16 de `specs/spec.md`. Alterado `src/tcg/gold/perguntas.py` (`p1_rankings`, que reaproveita a decomposição da T-35 entre o primeiro e o último dia da coleção e junta `dim_produto` para nome, imagem e link; `p2_indice`, em reais por padrão ou em dólar; constante `RARIDADES_DOUBLE_RARE_EM_DIANTE`); criado `tests/unidade/test_p1_p2.py` (DuckDB em memória: rankings de 10 sem Code Card, sem o item de US$ 0,90 e sem selado; ranking com menos de dez; mínimo estrito com US$ 1 e US$ 5; filtro por coleção; P2 com 100 no primeiro dia e a Rare fora; P2 em dólar; Double Rare cara sem preço no dia 2 fora da cesta sem derrubar o índice; coluna inválida). 8 passed na 1ª execução; suíte de unidade: 271 passed; evidência em `docs/evidencias/T-36_p1_p2.txt` |
| 2026-11-12 | T-37 | "prompt de implementação padrão" | plano aprovado com o diff do RF-17 em `specs/spec.md` (cesta fixa por coleção, como na P2: só itens de carta, sem Code Card, com preço em todos os dias da data base ao último dia da coleção; a quantidade de itens de cada cesta acompanha o resultado) e duas decisões do autor: P4 no último dia de cada coleção e P3 com cada série até o último dia da sua coleção. Alterado `src/tcg/gold/perguntas.py` (`p3_indice`, em formato longo, com uma série por coleção mais a PTAX de venda do `fato_cambio_diario`, todas em base 100 no primeiro dia comum, com `itens_cesta` e `destaque` só para a DRI, em reais por padrão ou em dólar; `p4_concentracao`, que devolve a participação por raridade, com raridade nula como "Sem raridade", e `itens_80` por coleção); criado `tests/unidade/test_p3_p4.py` (DuckDB em memória: cenário do RF-17 com 100 em 03/11 nas três séries; cesta fixa com carta cara sem preço em 04/11 fora e item sem preço antes da data base dentro; só a DRI; coluna inválida; 50, 20, 15, 10 e 5 dão 3 itens e participações somando 100%; duas coleções com último dia próprio). 1ª execução: 5 passed e 1 failed por erro na expectativa do teste (90% sozinho já chega a 80%, então o certo era 1 item); cenário trocado para 70 e 30; 2ª execução: 6 passed; suíte de unidade: 277 passed; evidência em `docs/evidencias/T-37_p3_p4.txt` |
| 2026-11-14 | T-38 | "prompt de implementação padrão" | plano aprovado com decisões do autor: 1) volatilidade = desvio-padrão amostral (`stddev_samp`), nula com menos de dois retornos; 2) janela da coleção, não do item: o item entra só com preço no primeiro e no último dia da sua coleção, o filtro estritamente acima de `preco_minimo_p5_usd` usa o `market_price` em US$ do primeiro dia da coleção e o retorno vai do primeiro ao último dia da coleção; 3) retornos diários só entre dias de calendário seguidos com preço, os que atravessam lacuna são descartados (um item com lacuna no meio continua entrando); regra da janela acrescentada ao RF-19 de `specs/spec.md`. Alterado `src/tcg/gold/perguntas.py` (`p5_retorno_volatilidade`, todas as coleções com `group_id`, em reais por padrão ou em dólar, com `n_retornos`, imagem e link); criado `tests/unidade/test_p5.py` (DuckDB em memória: 10, 11 e 9,9 dão −1% e desvio-padrão de (+10%, −10%) em dólar e em reais; 01, 02 e 04/11 dão só o retorno 01→02; item com lacuna e extremos com preço perde só o retorno da lacuna; item sem preço no último ou no primeiro dia da coleção fica fora; mínimo estrito de US$ 5 e sem Code Card nem selado; duas coleções com janela própria; coluna inválida). 8 passed na 1ª execução; suíte de unidade: 295 passed; evidência em `docs/evidencias/T-38_p5.txt` |
| 2026-11-14 | T-45 | "prompt de implementação padrão" | plano aprovado sem ajustes, com as três decisões: gancho opcional `PAINEL_GOLD_DIR` (pasta local com a gold, fora do `.env.example`), funções reutilizáveis em `dashboard/app.py` (sem módulo novo em `src/`) e base com tabela de cartas e detalhe do item, sem as perguntas (T-46). Criados `dashboard/app.py` (só lê a gold; reais por padrão e dólar; filtro estritamente acima do mínimo com padrões US$ 1 na P1 e US$ 5 na P5; aviso de período curto; série reindexada pela `dim_data` com linha interrompida na lacuna; "imagem indisponível" e "link indisponível"), `tests/unidade/test_painel_base.py` (AppTest com gold em `tmp_path`) e o alvo `make painel`; removido `dashboard/.gitkeep`. Uma correção: o loop asyncio do AppTest abre `socket.socketpair()` (AF_UNIX), recusado pelo bloqueio do conftest; o módulo de teste permite só AF_UNIX e prova que AF_INET e DNS continuam bloqueados. `pytest tests/unidade/test_painel_base.py -v`: 10 passed; suíte de unidade: 287 passed (`docs/evidencias/T-45_painel_base.txt`). Primeira execução real do painel fica com o autor. |
| 2026-11-14 | T-46 | "prompt de implementação padrão" | plano aprovado com decisões do autor: 1) aviso de coleções faltando na P3, P4 e P5, conforme o RF-22 (o prompt citava só P3 e P5); 2) sem chamada à parte de `decomposicao_por_item`, as parcelas vêm de `p1_rankings`; 3) tabelas com texto formatado em pt-BR, aceitando a ordenação alfabética no cabeçalho; 4) imagem no tooltip da P5 pelo campo `image` do vega-tooltip, tentada uma vez, com seletor de item (imagem e link) abaixo do gráfico. Alterado `dashboard/app.py`: abas Itens, P1 a P5 sobre `p1_rankings`, `p2_indice`, `p3_indice`, `p4_concentracao` e `p5_retorno_volatilidade` com a gold registrada como views DuckDB em memória (`conectar_gold`); leitura também de `fato_cambio_diario`; filtro da P5 na barra lateral; P3 com a DRI destacada (espessura e opacidade) e a PTAX tracejada; P4 em barras empilhadas a 100% com tabela de `itens_80`; P5 em dispersão volatilidade × retorno com cor por coleção; aviso do RF-22 na P3, P4 e P5 quando o fato só tem a DRI; `formatar_moeda`, `formatar_percentual` e `formatar_data` (R$ 1.776,98, US$ 381,38, 03/11); eixos de data em `%d/%m` com `utcyearmonthdate`; `width="stretch"` no lugar de `use_container_width`; item padrão continua o de maior preço. Criado `tests/unidade/test_painel_perguntas.py` (AppTest, gold em `tmp_path`); ajustado `tests/unidade/test_painel_base.py` (fixture com `fato_cambio_diario`, preços em texto pt-BR, gráfico da série localizado pelo título, imagens de base, P1 e P5). `pytest tests/unidade/test_painel_perguntas.py -v`: 13 passed na 1ª execução; suíte de unidade: 308 passed (`docs/evidencias/T-46_painel_perguntas.txt`). Renderização da imagem no tooltip e conferência visual com dados reais ficam com o autor (`make painel`). |
| 2026-11-14 | T-46 | "ajuste visual após conferência com dados reais" | três ajustes em `dashboard/app.py` pedidos pelo autor após o `make painel`: 1) P3 com o eixo y sem começar em 0 (`scale zero=False`), para as variações em torno de 100 ficarem visíveis; 2) gráficos de linha com um rótulo por dia no eixo x, sem datas repetidas (`eixo_data`: ticks nos próprios dias dos dados, `utc`, `labelOverlap`; antes, com dois dias, o Vega punha ticks a cada 12 h e repetia 12/11); 3) seletor de item da P5 só com os itens do gráfico (volatilidade não nula), padrão no de maior preço entre eles. Testes novos em `tests/unidade/test_painel_perguntas.py` (eixo y da P3, `eixo_data` com 12/11 e 13/11 repetido, um tick por dia em cada gráfico de linha, seletor da P5 sem a carta cara com lacunas, acrescentada à fixture). `pytest tests/unidade/test_painel_perguntas.py tests/unidade/test_painel_base.py -v`: 27 passed na 1ª execução; saída acrescentada a `docs/evidencias/T-46_painel_perguntas.txt`. |
| 2026-11-14 | T-46 | "ajuste visual após conferência com dados reais" | três ajustes em `dashboard/app.py`: 1) P2 com o eixo y sem começar em 0 (`scale zero=False`), como na P3; 2) conferido no RF-16 e no SQL (`avg(preco)` da cesta fixa): o índice dos selados é a média dos preços da cesta fixa, que dá o mesmo índice da soma (n constante), não a média dos índices dos itens; as duas séries passam a "Selados (cesta fixa)" e "Double Rare em diante (cesta fixa)", a legenda explica a equivalência e fica abaixo do gráfico com `labelLimit=0`, sem corte; 3) P4 com os rótulos das coleções na horizontal (`labelAngle=0`). Testes novos em `tests/unidade/test_painel_perguntas.py` (eixo y e legenda da P2, ângulo do eixo x da P4; rótulos da P2 atualizados). `pytest tests/unidade/test_painel_perguntas.py tests/unidade/test_painel_base.py -v`: 29 passed na 1ª execução; saída acrescentada a `docs/evidencias/T-46_painel_perguntas.txt`. |
| 2026-11-16 | T-39 | texto completo em [Prompt da T-39 – ADR-005, regra da carteira propria (2026-11-16)](#prompt-da-t-39--adr-005-regra-da-carteira-propria-2026-11-16) | rascunho aprovado; dois pontos fechados pelo autor antes do commit (dia de montagem pela definição de primeiro dia da spec; empate do selado por `product_id` e depois `acabamento`); ADR salvo, T-39 marcada como [x]; pendência sobre o primeiro dia em `perguntas.py` anotada para a T-55 e a T-56 |
| 2026-11-16 | T-40 | texto completo em [Prompt da T-40 – ADR-006, fallback do selado (2026-11-16)](#prompt-da-t-40--adr-006-fallback-do-selado-2026-11-16) | rascunho aprovado sem alterações, mantendo os dois acréscimos do agente (alternativa "buscar o preço do booster box em outro dia" e risco "regra do nome pegar outro produto", tratado como pendência); ADR salvo em `docs/adr/ADR-006-fallback-selado.md`, T-40 marcada como [x] |
| 2026-11-16 | T-41 | "prompt de implementação padrão" (detalhes em [Prompt da T-41 – Composição das carteiras (2026-11-16)](#prompt-da-t-41--composição-das-carteiras-2026-11-16)) | plano aprovado com duas decisões do autor (pendência só com mais de um `product_id` na regra do booster box; "regra pendente" pelo parâmetro `regra_propria`); criados `src/tcg/gold/carteiras.py` e `tests/unidade/test_composicao.py`; quatro tentativas até passar (uma no código, três nos valores esperados do teste); 24 passed; suíte de unidade: 338 passed (`docs/evidencias/T-41_composicao.txt`) |
| 2026-11-16 | T-42 | "prompt de implementação padrão" (detalhes em [Prompt da T-42 – Liquidação diária das carteiras (2026-11-16)](#prompt-da-t-42--liquidação-diária-das-carteiras-2026-11-16)) | plano aprovado com um ajuste do autor no CDI (a taxa do dia útil d remunera de d ao próximo dia útil: valor(D) = inicial × Π (1 + cdi_taxa_dia(d)/100), primeiro dia ≤ d < D; `cdi_pendente` marca a linha quando falta a taxa de algum d < D usado); criados `src/tcg/gold/liquidacao.py` e `tests/unidade/test_liquidacao.py`; uma correção no teste (relação DuckDB sem `fetchone()`); 10 passed; suíte de unidade: 348 passed (`docs/evidencias/T-42_liquidacao.txt`) |
| 2026-11-16 | T-43 | "prompt de implementação padrão" (detalhes em [Prompt da T-43 – Métricas das carteiras (2026-11-16)](#prompt-da-t-43--métricas-das-carteiras-2026-11-16)) | plano aprovado sem alterações (contas conferidas pelo autor); criados `src/tcg/gold/metricas_carteira.py` e `tests/unidade/test_metricas_carteira.py`; 9 passed na 1ª execução; suíte de unidade: 357 passed (`docs/evidencias/T-43_metricas_carteira.txt`) |
| 2026-11-16 | T-44 | "prompt de implementação padrão" (detalhes em [Prompt da T-44 – gold_turma e carteiras no make gold (2026-11-16)](#prompt-da-t-44--gold_turma-e-carteiras-no-make-gold-2026-11-16)) | contradição apontada no plano (o prompt pedia uma linha por dia × carteira × taxa; RF-26 pede dia × carteira); o autor decidiu seguir a spec: gold_turma só com a taxa do parâmetro (0 em dolar e cdi) e taxa 0 na gold da DRI; `construir_carteiras` e `regra_propria_aceita` em `src/tcg/gold/construtor.py`, chamados pelo `make gold` e pelo `reprocessar.py`; criados `tests/unidade/test_carteiras_gold.py` e `tests/integracao/test_gold_turma.py`; uma correção no teste de integração da T-33 (gold_turma da DRI agora é recriada); 5 passed na verificação; suíte completa: 407 passed (`docs/evidencias/T-44_gold_turma.txt`) |
| 2026-11-16 | T-47 | "prompt de implementação padrão" (detalhes em [Prompt da T-47 – Painel das carteiras e placar da turma (2026-11-16)](#prompt-da-t-47--painel-das-carteiras-e-placar-da-turma-2026-11-16)) | divergência apontada no plano (o prompt ligava o placar ao RF-26; na spec é o RF-28) e confirmada pelo autor; decisões: seletor de carteira na menor perda máxima com cesta_raras como padrão, gancho `PAINEL_GOLD_TURMA_DIR` só para teste e desenvolvimento, comparação estrita (empate não conta); abas "Carteiras" e "Placar da turma" em `dashboard/app.py`, só lendo a gold e a gold_turma; criado `tests/unidade/test_painel_carteiras.py`; 14 passed na 1ª execução; suíte de unidade: 377 passed (`docs/evidencias/T-47_painel_carteiras.txt`) |
| 2026-11-16 | T-47 | "ajuste visual após conferência com dados reais" (detalhes em [Ajuste da T-47 após o make painel (2026-11-16)](#ajuste-da-t-47-após-o-make-painel-2026-11-16)) | três ajustes em `dashboard/app.py`: 1) eixo y do gráfico das carteiras com o mesmo campo, escala (domínio dos dados e de R$ 1.000,00, `zero=False`) e eixo em todas as camadas, rótulos em R$ pt-BR; 2) cifrão escapado em todo texto Markdown do painel (`escapar_cifrao` e `texto.*`); 3) coluna "Observação" para carta com 0 unidades e aviso quando nenhuma carta cabe em R$ 100,00; uma correção de asserção no teste antigo do gráfico; testes do painel: 50 passed; suíte de unidade: 384 passed (saída acrescentada a `docs/evidencias/T-47_painel_carteiras.txt`); observação para o ATAM (T-53) registrada no detalhe |
| 2026-11-16 | T-47 | "ajuste visual após conferência com dados reais" (detalhes em [Ajuste 2 da T-47: altura dos gráficos (2026-11-16)](#ajuste-2-da-t-47-altura-dos-gráficos-2026-11-16)) | altura fixa `ALTURA_GRAFICO = 420` em todos os gráficos do painel (série do item, P2, P3, P4, P5 e carteiras; nenhum tinha altura) e legenda das carteiras à direita (`orient="right"`, como na P3); dois testes novos (altura e legenda no spec das carteiras; os seis gráficos com a mesma altura); 52 passed nos testes do painel na 1ª execução; suíte de unidade: 386 passed (saída acrescentada a `docs/evidencias/T-47_painel_carteiras.txt`) |
| 2026-11-16 | T-48 | "prompt de implementação padrão" (detalhes em [Prompt da T-48 – Verificador de cobertura (2026-11-16)](#prompt-da-t-48--verificador-de-cobertura-2026-11-16)) | plano aprovado sem ajustes; `src/tcg/cobertura/verificador.py` (período = menor e maior `data` com bruto do TCGCSV; origem por data `bruto`, `registro` ou `faltante`; lê a Branch dados-raw pelos blobs, sem checkout, e a tabela "Dias sem coleta" do README; saída 0, 1 ou 2) e alvo `make cobertura` sem `.env`; `pytest tests/unidade/test_cobertura.py`: 16 passed; suíte de unidade: 402 passed; evidência em `docs/evidencias/T-48_cobertura.txt` |
| 2026-11-16 | T-49 | "prompt de implementação padrão" (detalhes em [Prompt da T-49 – README completo (2026-11-16)](#prompt-da-t-49--readme-completo-2026-11-16)) | divergência apontada no plano: a linha da T-49 pedia "disparo manual antes das 23h59 UTC (R-01)", regra substituída pelo ADR-007; decisão do autor: README e linha da T-49 corrigidos para "disparo manual dentro do ciclo, antes das 20h UTC de D+1 (R-01, ADR-007)"; README com visão geral e camadas, P1 a P5 e carteiras, serviços e custo zero, coleta agendada, R-01 e R-02, data lake, "Como rodar" do clone limpo e "Dias sem coleta" sem linhas, com a observação de 04/11 fora da tabela; `pytest tests/unidade/test_readme.py`: 17 passed; suíte de unidade: 419 passed; evidência em `docs/evidencias/T-49_readme.txt` |
| 2026-11-16 | T-49 | "ajustes do README após revisão do autor" (detalhes em [Ajustes do README da T-49 (2026-11-16)](#ajustes-do-readme-da-t-49-2026-11-16)) | P2 descrita como índice base 100 da cesta fixa de selados contra o da cesta fixa de cartas Double Rare em diante; cesta_raras "sem Code Card"; R-02 com os 60 dias contados desde a última atividade no repositório e conferência e reativação na aba Actions, sem a afirmação, não confirmada, de que os commits da coleta mantêm o agendamento ativo; `pytest tests/unidade/test_readme.py`: 17 passed; saída acrescentada a `docs/evidencias/T-49_readme.txt` |
| 2026-11-16 | T-50 | "registro da T-50 executada pelo autor" (detalhes em [Registro da T-50 – Clone limpo (2026-11-16)](#registro-da-t-50--clone-limpo-2026-11-16)) | reprodução executada pelo autor num clone novo em `/tmp/clone-limpo`, seguindo só o README, com o `.env` copiado do `.env` do autor; agente só registrou, sem executar comando do pipeline; saída conferida sem credencial antes da cópia; `make setup` e `make up` (contêiner Healthy) sem erro; `make sync`: enviados=0 recusados=52 falhas=0; `make silver`: produto 281, preco_diario 5798, quarentena 0; `make gold`: coleções 24269 e 24541, fato_preco_diario 7114, gold_turma_carteira 65; `make test`: 463 passed; `make cobertura`: 13 datas, 0 faltantes; `make painel` com as oito abas, conferido pelo autor; evidência em `docs/evidencias/T-50_clone_limpo.md`; T-50 marcada como [x] |
| 2026-11-16 | T-51 | "registro da T-51 executada pelo autor" (detalhes em [Registro da T-51 – Busca de credenciais (2026-11-16)](#registro-da-t-51--busca-de-credenciais-2026-11-16)) | buscas executadas pelo autor no Codespace, com os valores lidos do `.env` ou digitados com `read -rs`, sem eco e só com contagens; agente só registrou, sem executar busca e sem ler o `.env`; `git log -p --all` (após `git fetch --all`) com a chave e o segredo atuais: 0; arquivos do repositório sem `.env`, `.venv` e `.git`: 0 arquivos; segredos antigos (Railway e primeiro endpoint do RustFS, trocado em 15/11): 0; usuário antigo não buscado (falso positivo); log do run agendado 43905874560 (564 linhas): 0, com secrets mascarados como `***`; evidência em `docs/evidencias/T-51_busca_credenciais.md`; T-51 marcada como [x] |
| 2026-11-16 | T-52 | "registro da T-52 a partir dos dados coletados pelo autor" (detalhes em [Registro da T-52 – Agendador e requisições (2026-11-16)](#registro-da-t-52--agendador-e-requisições-2026-11-16)) | dados coletados pelo autor por volta das 23h30 UTC (`gh run list`, `gh run view --log` das 29 execuções, `make cobertura`); agente só analisou os arquivos, sem executar `gh`, `git fetch` nem `make` e sem ler o `.env`; logs sem credencial (secrets como `***`); 29 execuções (25 schedule, 4 workflow_dispatch; 25 success, 4 failure); atraso das agendadas: média 6h14min47s, máximo 10h15min30s; 26 requisições ao TCGCSV, no máximo 4 num dia civil UTC e 2 por data de referência, contra o limite de 10000; 03/11 a 15/11 com bruto, coerente com `make cobertura` e a tabela "Dias sem coleta" vazia; 04/11 recuperado na T-57; 16/11 ainda no ciclo; agendamento ativo (última agendada 43905874560, 2026-11-16T16:17Z); evidência em `docs/evidencias/T-52_agendador.md`; T-52 marcada como [x]; ajuste após revisão: `make sync` do autor em 15/11, antes das 14h04 UTC, sem saída guardada, e `[[x]` da T-51 corrigido em `specs/tasks.md` |
| 2026-11-16 | T-53 | texto completo em [Prompt da T-53 – Avaliação ATAM (2026-11-16)](#prompt-da-t-53--avaliação-atam-2026-11-16) | rascunho mostrado antes de gravar; aprovado com três ajustes do autor: 1) evidência nova `docs/evidencias/T-53_observacoes_painel.md` com as observações do autor no `make painel` de 16/11 (carteiras, composição, placar e linhas da gold por coleção), usada em S-01, C-13 e RS-03, que saíram das pendências; 2) RS-05 reescrito: o placar usa comparação estrita, e a selado da DRI aparece como "não" acima da cdi por empate; 3) evidência da verificação em `docs/evidencias/T-53_atam.txt`; `docs/atam.md` com 13 cenários em seis partes, cada RNF em ao menos um cenário; verificação: 42 linhas com "RNF-", nenhuma evidência citada faltando; T-53 marcada como [x] |
| 2026-11-16 | T-54 | texto completo em [Prompt da T-54 – Matriz de rastreabilidade (2026-11-16)](#prompt-da-t-54--matriz-de-rastreabilidade-2026-11-16) | matriz com 41 linhas (40 atendidos, 1 parcial: RNF-13); revisão do autor: amostra de três linhas "atendido" com semente 54 (RF-09, RNF-01, RNF-08; 8 testes, 8 passed); colunas Decisão e Razão mantidas, com desvio registrado em relação ao formato literal do prompt 11.2; nome do teste corrigido em `docs/atam.md`; nota sobre `scripts/hipoteses_bruto.py`, `tests/unidade/test_hipoteses_bruto.py` e os `__init__.py`; T-54 marcada como [x]; evidência em `docs/evidencias/T-54_rastreabilidade.txt` |
| 2026-11-17 | T-55 | texto completo em [Prompt da T-55 – Registro de pendências (2026-11-17)](#prompt-da-t-55--registro-de-pendências-2026-11-17) | rascunho mostrado antes de gravar; aprovado com ajustes do autor: evidência `docs/evidencias/T-55_pendencias.txt`; categoria `entrega` criada para P-02 e P-04, só a P-01 como `limitador`; P-03 passou a `funcional` (as ações já rodam forçadas no Node.js 24); "a ASC (24541)" na pergunta 3; regra de tarefa nova antes de qualquer código em "Como ler"; `docs/pendencias_aula08.md` com 15 pendências (1 limitador, 2 entrega, 7 funcional, 3 documentação, 2 cosmético) e 4 perguntas para a mentoria; verificação `test -s` com código 0 e conferência das colunas de cada linha sem falta |
| 2026-11-17 | T-56 | texto completo em [Prompt da T-56 – Autoauditoria final (2026-11-17)](#prompt-da-t-56--autoauditoria-final-2026-11-17) | relatório aprovado pelo autor sem alterações; 13 itens cumpridos e 1 parcial (item 9, dois commits fora da convenção), nenhum limitador encontrado; duas lacunas novas viraram P-16 (L-08) e P-17 (L-11) em `docs/pendencias_aula08.md`, as duas `aceita`; verificação com código de saída 0 e nenhum outro arquivo no `git diff`; evidência em `docs/evidencias/T-56_auditoria.txt` |

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

## Prompt da T-58 – Troca do endpoint do data lake da turma (2026-11-15)

```text
O professor trocou o endpoint e as credenciais do data lake da turma. Eu já atualizei o .env e os secrets do GitHub. O novo endpoint é lake-aulas-mackenzie.afonsolelis.tech.
Procure no repositório (sem ler o .env) todas as menções ao endpoint antigo s3.afonsolelis.tech e troque pelo novo. No docs/adr/ADR-008-data-lake-rustfs.md, não apague o histórico: acrescente uma nota de revisão datada de 15/11/2026 dizendo que o endpoint e as credenciais foram trocados pelo professor, sem mudança de arquitetura.
Registre como evidência em docs/evidencias/T-58_troca_endpoint.txt: a linha final do make sync local e a do workflow #26 (enviados=0 recusados=48 fora_do_escopo=0 falhas=0), sem credenciais.
Mostre a lista de arquivos alterados, acrescente a linha em docs/prompts.md e proponha a mensagem de commit docs(T-58): ... Não faça commit e não escreva credenciais em nenhum arquivo.
```

Resultado: endpoint trocado em `.env.example`, `AGENTS.md`, `README.md`, `specs/spec.md`, `specs/plan.md` e na decisão do ADR-008, que ganhou a seção "Revisões" com a nota de 2026-11-15. Ficaram com o endereço antigo, de propósito, os registros datados de 2026-11-07: o contexto do ADR-008, as evidências `T-58_primeira_sync_rustfs.txt` e `T-58_silver_gold_rustfs.txt` e o prompt anterior da T-58. Evidência em `docs/evidencias/T-58_troca_endpoint.txt`, com a linha final do `make sync` local executado pelo autor (2026-11-15T14:04:33Z) e a do workflow coleta #26. Nenhum comando contra o data lake foi executado pelo agente, e nenhuma credencial foi escrita.

## Prompt da T-39 – ADR-005, regra da carteira propria (2026-11-16)

```text
Execute a tarefa T-39 de specs/tasks.md: escreva docs/adr/ADR-005-carteira-propria.md registrando a regra da carteira propria que eu decidi. Mostre o rascunho, espere minha confirmação, grave o arquivo, marque T-39, registre em docs/prompts.md e proponha a mensagem de commit.
Regra (R$ 1.000,00): dia de montagem = primeiro dia de coleta da DRI, só preços desse dia; compra por market_price × PTAX de venda do dia, sem taxa. Parte selada (R$ 500,00): selado de maior preço com preço de compra ≤ R$ 500,00, máximo de unidades inteiras, empate pelo menor product_id, sem selado elegível o valor fica em caixa. Parte de cartas (R$ 500,00): cinco itens Illustration Rare (sem Code Card) de maior market_price, R$ 100,00 cada em unidades inteiras, empate por product_id e depois acabamento; faltando elegíveis, o valor fica em caixa. Sobra em caixa rendendo CDI de dia útil; avaliação e preço ausente como nas carteiras fixas (RF-24).
Justificativas: sem informação do futuro; diferencia-se da cesta_raras testando a raridade abaixo da Special Illustration Rare; exposição real a selado. Alternativas descartadas: momento e menor volatilidade (informação do futuro), cartas mais caras (repete a cesta_raras). Evidência: commit do ADR antes do primeiro cálculo; teste da T-41 provando que dias posteriores não mudam a composição.
Não calcule a composição, não consulte preços, não acesse o RustFS nem o MinIO, não faça commit.
```

Resultado: rascunho apresentado e aprovado pelo autor. Gravado `docs/adr/ADR-005-carteira-propria.md` e marcada a T-39 em `specs/tasks.md`. RF citado: RF-23 (o RF-24 é referência da avaliação). Os dois pontos levantados pelo agente foram fechados pelo autor antes do commit: 1) o dia de montagem passou a ser "o primeiro dia, conforme as Definições da spec (menor `data` com bruto do TCGCSV da coleção)", o mesmo das carteiras selado e cesta_raras, em vez da menor `data` do fato de preços; 2) o empate da parte selada passou a ser pelo menor `product_id` e depois por `acabamento` em ordem alfabética, com o cenário correspondente na tabela de requisitos do ADR.

Pendência para a autoauditoria (T-56) e para o registro de pendências (T-55): `src/tcg/gold/perguntas.py` (linhas 270 a 274) usa como primeiro dia da coleção a menor `data` com `market_price` não nulo, diferente da definição da spec (menor `data` com bruto do TCGCSV). Os dois só divergem se o primeiro dia tiver todos os preços nulos. Nada foi corrigido nesta tarefa. Nenhuma composição foi calculada, nenhum preço foi consultado e nenhum acesso ao data lake ou ao MinIO foi feito.

## Prompt da T-40 – ADR-006, fallback do selado (2026-11-16)

```text
[C] Personagem
Você é um arquiteto de dados que registra decisões de forma verificável. Você escreve o ADR a partir da decisão do autor, sem inventar regras e sem calcular resultados.

[R] Pedido
Execute a tarefa T-40 de specs/tasks.md: escreva docs/adr/ADR-006-fallback-selado.md registrando a decisão do autor sobre o selado da carteira selado (abaixo). Siga esta ordem:
1. mostre o rascunho completo do ADR;
2. espere minha confirmação;
3. grave o arquivo, marque T-40 como [x] em specs/tasks.md, acrescente a linha em docs/prompts.md (entrada detalhada e linha na tabela de índice) e proponha a mensagem de commit no formato docs(T-40): descrição [RF-yy].

Decisão do autor:
- Selado principal: o booster box da coleção, identificado pela regra validada no T-13 e registrada no RF-23 (nome contém "Booster Box", não contém "Case" nem "Half"). Na DRI é o productId 624679.
- Fallback: só se o booster box não tiver market_price no primeiro dia (Definições da spec). Nesse caso, usa-se o produto tipo_produto = 'selado' de maior market_price com preço no primeiro dia; empate por menor product_id, depois acabamento em ordem alfabética.
- Orçamento e unidades: a regra é seguida literalmente. Compra-se o máximo de unidades inteiras que caibam em R$ 1.000,00 ao preço de compra do primeiro dia; se o selado custar mais que o orçamento, a carteira fica com zero unidades e todo o valor fica em caixa rendendo CDI de dia útil. O fallback não é acionado por preço acima do orçamento, só por ausência de preço.

[E] Exemplos
Use a estrutura dos ADRs já existentes em docs/adr/ (por exemplo ADR-005): Status, Contexto e forças, Requisitos e cenários, Alternativas, Decisão e táticas, Consequências positivas, Consequências negativas, Riscos, Evidência necessária, Condição de revisão.

[A] Ajustes
- Escreva como decisão do autor, com justificativa própria; não cite material de aula.
- Justificativas a registrar: seguir a regra literal mantém a carteira selado comparável entre as coleções da turma no placar; acionar o fallback por preço alto mudaria o significado da carteira (deixaria de ser booster box) e seria uma escolha diferente para cada coleção.
- Alternativa descartada a registrar: usar o fallback quando o booster box não cabe no orçamento, pelo motivo acima.
- Consequência negativa a registrar: na DRI, com o booster box acima de R$ 1.000,00 no primeiro dia, a carteira selado tende a ficar com zero unidades e se comportar como a carteira cdi; a exposição a selado do autor fica na carteira propria (ADR-005). Escreva "tende a" e não afirme o preço exato, porque não se calcula nada nesta tarefa.
- Não calcule a composição, não consulte preços e não acesse o RustFS nem o MinIO nesta tarefa.
- Se a decisão contradisser specs/spec.md ou AGENTS.md, pare e pergunte.
- Não faça git commit nem git push. Responda em português do Brasil.

[T] Tipo de saída
O ADR, specs/tasks.md e docs/prompts.md atualizados, e um resumo de até cinco linhas com a mensagem de commit proposta.

[E] Extras
Leia antes: AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md, docs/adr/ADR-005-carteira-propria.md e os demais ADRs em docs/adr/.
Pare ao final da tarefa.
```

Resposta de aprovação do autor:

```text
Aprovado, mantendo os dois acréscimos. Pode gravar o ADR, marcar a T-40 em specs/tasks.md, registrar em docs/prompts.md (entrada e linha na tabela de índice) e propor a mensagem de commit. Não faça commit.
```

Resultado: o agente conferiu que a decisão não contradiz a spec nem o AGENTS.md (o RF-23 já prevê "o selado de maior preço com preço (escolha em ADR)", unidades inteiras e sobra em caixa; como o preço de compra é market_price × PTAX do mesmo dia, ordenar por um ou pelo outro dá a mesma ordem). Rascunho apresentado e aprovado sem alterações. Gravado `docs/adr/ADR-006-fallback-selado.md` e marcada a T-40 em `specs/tasks.md`. RF citado: RF-23 (RF-24 e RF-26 como referência da avaliação e do placar). O ADR cita a evidência do T-13: regra do booster box com exclusão de "Half", booster box com market_price no bruto de 2026-11-03 e 25 de 25 selados com preço próprio. Acréscimos do agente, mantidos pelo autor: a alternativa "buscar o preço do booster box em outro dia" (descartada por informação do futuro e por não preencher lacunas) e o risco "regra do nome pegar outro produto numa coleta futura" (tratado como pendência). Nenhum preço em reais foi escrito, nenhuma composição foi calculada, nenhum preço foi consultado e nenhum acesso ao data lake ou ao MinIO foi feito.

## Prompt da T-41 – Composição das carteiras (2026-11-16)

Prompt: "prompt de implementação padrão" (C-R-E-A-T-E) para a T-41, com as leituras obrigatórias (AGENTS.md, spec, plan, tasks, ADR-005, ADR-006, `perguntas.py`), as confirmações por carteira no plano e os testes obrigatórios em `tests/unidade/test_composicao.py`.

Decisões do autor na aprovação do plano:
- (a) Erro de pendência (`PendenciaBoosterBox`) só quando mais de um `product_id` distinto casa com a regra do nome do booster box; o mesmo `product_id` com mais de um acabamento com preço escolhe o acabamento em ordem alfabética, com teste próprio.
- (b) "Regra pendente" da propria representada pelo parâmetro `regra_propria` de `compor_carteiras`, sem verificar o arquivo do ADR.
- Comentário em `carteiras.py` registrando que o primeiro dia usado (menor `data` do fato da coleção) equivale à definição da spec (menor `data` com bruto do TCGCSV). O agente apontou que o registro da T-39 não verificou essa equivalência; por decisão do autor, o comentário não cita a T-39 e traz a justificativa verificada nesta tarefa: a silver grava uma linha por item válido de cada `prices.json`, inclusive com `market_price` nulo, e o fato não filtra preço nulo; só divergiria se o `prices.json` do primeiro dia não tivesse nenhuma linha válida.

Implementação: `src/tcg/gold/carteiras.py` com `ler_primeiro_dia` (único ponto que lê o DuckDB; só data, PTAX de venda aplicada e itens do primeiro dia; erro sem PTAX aplicada), funções puras `compor_selado`, `compor_cesta_raras`, `compor_propria`, `compor_dolar`, `compor_cdi` e `compor_carteiras`, e `registrar_composicao` (tabela DuckDB `composicao_carteira`, uma linha por posição e uma de caixa por carteira). Preço de compra = market_price × PTAX de venda, sem taxa; unidades = floor com tolerância de 1e-9; sobra por item e caixa por carteira; item com preço = market_price não nulo e maior que zero; desempate por maior preço, menor `product_id` e `acabamento` alfabético. Liquidação, métricas e gold_turma não foram adiantadas (T-42 a T-44).

Tentativas até a verificação passar:
1. Código: nesta versão do DuckDB, relação não tem `fetchone()` (24 falhas com `AttributeError`); `ler_primeiro_dia` passou a usar `con.execute(...).fetchone()`. Resultado: 23 passed, 1 failed.
2. Fixture do teste: a Illustration Rare 26 (US$ 18) custava mais que a SIR 7 (US$ 17) e entrava, corretamente, na cesta_raras; os preços das Illustration Rare foram baixados para US$ 1,50 a 9 e o esperado da propria recalculado. Resultado: 23 passed, 1 failed.
3. Valor esperado do teste (autorizado pelo autor): a carta 3 custa R$ 65 (US$ 13 × 5,00), compra 1 unidade e sobra R$ 35, não R$ 70 e R$ 30. Resultado: 23 passed, 1 failed.
4. Valor esperado do teste (autorizado pelo autor): a carta 11 (R$ 105) também passa de R$ 100 e fica com zero unidades; o custo esperado da cesta_raras é R$ 660 e o caixa R$ 340, com o comentário ajustado. O agente havia afirmado na tentativa 3 que o caixa total "já confere" sem ter conferido. Resultado: 24 passed.

Em nenhuma das tentativas o código de composição estava errado nas regras; as três últimas falhas eram contas do agente nos valores esperados.

Resultado: `.venv/bin/python -m pytest tests/unidade/test_composicao.py -v`: 24 passed; suíte de unidade (`.venv/bin/python -m pytest tests/unidade -q`): 338 passed; evidência em `docs/evidencias/T-41_composicao.txt`. T-41 marcada como [x] em `specs/tasks.md`. Nenhum acesso ao RustFS nem ao MinIO; nenhuma composição foi calculada com dados reais.

## Prompt da T-42 – Liquidação diária das carteiras (2026-11-16)

Prompt: "prompt de implementação padrão" (C-R-E-A-T-E) para a T-42, com as leituras obrigatórias (AGENTS.md, spec, plan, tasks, ADR-005, ADR-006, `carteiras.py`), as confirmações no plano (liquidação, taxa_venda do parâmetro e taxa 0, preço carregado, CDI em dia útil com coluna, unidade e início, dolar pela PTAX de compra, uma linha por carteira e dia) e os testes obrigatórios em `tests/unidade/test_liquidacao.py`.

Decisões do autor na aprovação do plano:
- CDI: a taxa do dia útil d remunera de d até o próximo dia útil, então valor(D) = valor inicial × Π (1 + cdi_taxa_dia(d)/100) para primeiro dia ≤ d < D. No primeiro dia o valor é exatamente o inicial; no segundo dia já rende a taxa do primeiro. `cdi_taxa_dia` em percentual ao dia, como publicado; fim de semana e feriado têm 0 no fato (RF-12).
- `cdi_pendente` da linha só quando falta a taxa de algum dia útil d < D usado no produto; nesse caso taxa 0, sem estimativa.
- O agente conferiu o RF-24 ("rendem (1 + taxa_dia/100) em cada dia útil e não rendem em fim de semana nem feriado"): a spec não fixa o dia do crédito e a regra é compatível; efeito visível: o sábado recebe a taxa da sexta, e sábado, domingo e segunda ficam iguais. O período do teste foi estendido até a quarta para que a marcação de `cdi_pendente` apareça; os valores esperados do CDI foram recalculados conta por conta antes de escrever o teste.

Implementação: `src/tcg/gold/liquidacao.py` com `ler_dados_diarios` (único ponto que lê o DuckDB, só SELECT; período do dia de montagem ao último dia com preço da coleção, todos os dias de calendário; erro sem PTAX de compra aplicada), funções puras `liquidar` e `liquidar_carteiras` e `registrar_liquidacao` (tabelas DuckDB `liquidacao_carteira` e `liquidacao_item`, com a taxa do parâmetro e com taxa 0, separadas pela coluna `taxa_venda`). Cartas e selados: Σ unidades × market_price × (1 − taxa_venda) × PTAX de compra + caixa; dolar: usd × PTAX de compra; caixa e cdi pelo fator de CDI acima; preço ausente (sem linha, nulo ou ≤ 0) usa o último market_price > 0 observado, com `preco_carregado` no item e no dia e `data_preco` de origem, sem gravar no fato; propria com "regra pendente" tem uma linha por dia com valor nulo. A composição da T-41 não é recalculada nem alterada; nada foi ligado ao `make gold` (gravação na T-44). Métricas, gold_turma e painel não foram adiantados (T-43, T-44, T-47).

Tentativas até a verificação passar:
1. Teste: nesta versão do DuckDB, relação não tem `fetchone()` (1 falha, em `test_uma_linha_por_carteira_dia_e_taxa`); a contagem passou a usar `con.execute(...).fetchone()`. Resultado: 10 passed. Nenhum valor esperado precisou de ajuste.

Resultado: `.venv/bin/python -m pytest tests/unidade/test_liquidacao.py -v`: 10 passed; suíte de unidade (`.venv/bin/python -m pytest tests/unidade -q`): 348 passed; evidência em `docs/evidencias/T-42_liquidacao.txt`. T-42 marcada como [x] em `specs/tasks.md`. Nenhum acesso ao RustFS, ao MinIO ou à rede; nenhuma liquidação foi calculada com dados reais.

## Prompt da T-43 – Métricas das carteiras (2026-11-16)

Prompt: "prompt de implementação padrão" (C-R-E-A-T-E) para a T-43, com as leituras obrigatórias (AGENTS.md, spec com Definições e RF-23 a RF-26, plan, tasks, `carteiras.py`, `liquidacao.py`), as confirmações no plano (retorno acumulado, excesso sobre o CDI, perda máxima, dias com preço carregado e propria com "regra pendente", por carteira e por taxa, com a taxa do parâmetro e com taxa 0) e os testes obrigatórios em `tests/unidade/test_metricas_carteira.py`.

Decisões no plano, aprovado sem alterações pelo autor ("As contas conferem"):
- Módulo separado `src/tcg/gold/metricas_carteira.py`, no mesmo padrão de `liquidacao.py` da T-42 (a árvore do plan.md lista só `carteiras.py` em `gold/`).
- Excesso sobre o CDI comparado com a carteira cdi da mesma taxa de venda; sem a carteira cdi naquela taxa, erro.
- Perda máxima = máximo de (pico corrente − valor) ÷ pico corrente; 0 se a série nunca cai.
- Dias com preço carregado = dias com `preco_carregado` na linha da carteira (T-42).
- Valores esperados conferidos conta por conta no plano e nos comentários do teste: 1000, 1200, 900, 1100 → retorno 10% e perda 25%; 1000, 1100, 990, 1200, 1000, 840, 900 → perda 30% (primeiro pico daria 23,6%; maior queda diária, 16,7%); taxa 0 contra 15% com `liquidar_carteiras` da T-42 → diferença 0,12 = 800 × 0,15 / 1000 no selado e 0 em dolar e cdi.

Implementação: `src/tcg/gold/metricas_carteira.py` com `retorno_acumulado`, `perda_maxima`, `calcular_metricas` (função pura sobre as `LinhaCarteira` da T-42, agrupadas por taxa de venda × carteira e ordenadas por data, sem recalcular valores; propria com "regra pendente" sai com métricas nulas, sem erro) e `registrar_metricas` (tabela DuckDB `metricas_carteira`, uma linha por carteira × taxa). Nada foi ligado ao `make gold`; gold_turma e painel não foram adiantados (T-44, T-47).

Tentativas até a verificação passar: nenhuma correção; 9 passed na 1ª execução.

Resultado: `.venv/bin/python -m pytest tests/unidade/test_metricas_carteira.py -v`: 9 passed; suíte de unidade (`.venv/bin/python -m pytest tests/unidade -q`): 357 passed; evidência em `docs/evidencias/T-43_metricas_carteira.txt`. T-43 marcada como [x] em `specs/tasks.md`. Nenhum acesso ao RustFS, ao MinIO ou à rede; nenhuma métrica foi calculada com dados reais.

## Prompt da T-44 – gold_turma e carteiras no make gold (2026-11-16)

Prompt: "prompt de implementação padrão" (C-R-E-A-T-E) para a T-44, com as leituras obrigatórias (AGENTS.md, spec com RF-23 a RF-26 e o contrato de gold_turma, plan, tasks, `docs/adr/`, `construtor.py`, `carteiras.py`, `liquidacao.py`, `metricas_carteira.py`, `guarda_prefixo.py`), as confirmações no plano (contrato, entrada no `make gold`, arquivos da gold da DRI, decisão de `regra_propria`, idempotência) e testes de unidade e de integração.

Contradição apontada no plano: o prompt pedia "uma linha por dia × carteira × taxa" na gold_turma; o RF-26 e a evidência esperada da T-44 pedem uma linha por dia de calendário × carteira, com taxa_venda = 0 em dolar e cdi. Decisão do autor: seguir a spec ("meu prompt estava errado"); gold_turma só com a taxa do parâmetro (0 em dolar e cdi); a versão com taxa 0 de todas as carteiras fica na gold da DRI. O autor também autorizou alterar `reprocessar.py` e o fixture de `tests/unidade/test_reprocessar.py`.

Implementação:
- `src/tcg/gold/construtor.py`: `regra_propria_aceita` (True só se `docs/adr/ADR-005-carteira-propria.md` existe e a seção "## Status" começa com "Aceito"); `calcular_carteiras` (composição T-41, liquidação T-42 com a taxa do parâmetro e com taxa 0, métricas T-43 a partir das linhas da liquidação registrada, e a tabela da gold_turma: data DATE, group_id INTEGER, carteira VARCHAR, valor_brl DOUBLE, retorno_acumulado = valor_brl / 1000 − 1 DOUBLE, taxa_venda DOUBLE com 0 em dolar e cdi); `construir_carteiras` (views sobre a gold da DRI já gravada, sem ler nem gravar a silver; grava `gold/group_id=24269/{composicao_carteira, liquidacao_carteira, liquidacao_item, metricas_carteira}.parquet` e `gold_turma/carteira/group_id=24269/carteira.parquet` por `gravar_parquet`, que passa pela Guarda de prefixo). `construir_gold` não mudou; `main` chama `construir_carteiras` depois dela, com `ler_parametros().taxa_venda`; código de saída 4 quando as carteiras não podem ser calculadas.
- `src/tcg/reprocessar.py`: a mesma chamada depois de `construir_gold` (sem ela, `make reprocessar` apagaria a gold_turma sem recriá-la); código de saída 5 para carteiras não calculadas.
- Chaves fixas: regravar substitui só os arquivos da DRI; nada é apagado pelo `make gold`.
- Painel e placar não foram adiantados (T-47).

Tentativas até a verificação passar:
1. `tests/integracao/test_gold_turma.py` e os testes de unidade passaram na 1ª execução; a suíte completa acusou 1 falha em `tests/integracao/test_reprocessar_integracao.py` (T-33): o teste tratava `gold_turma/carteira/group_id=24269/carteira.parquet` como órfão que devia sumir, e agora o reprocessar o recria. A asserção passou a exigir que a chave seja recriada com conteúdo diferente do órfão; as demais chaves órfãs continuam tendo de sumir. Resultado: 407 passed.

Resultado: `.venv/bin/python -m pytest tests/integracao/test_gold_turma.py -v`: 5 passed (MinIO descartável da T-19, executado pelo agente; contêiner removido no final); `tests/unidade/test_carteiras_gold.py`, `tests/unidade/test_reprocessar.py` e `tests/integracao/test_reprocessar_integracao.py`: 24 passed; suíte completa (`.venv/bin/python -m pytest -q`): 407 passed; evidência em `docs/evidencias/T-44_gold_turma.txt`. T-44 marcada como [x] em `specs/tasks.md`. Nenhum acesso ao RustFS; a execução real de `make gold` fica com o autor.

## Prompt da T-47 – Painel das carteiras e placar da turma (2026-11-16)

Prompt: "prompt de implementação padrão" (C-R-E-A-T-E) para a T-47, com as leituras obrigatórias (AGENTS.md, spec com RF-23 a RF-26, plan, tasks, ADR-005, ADR-006, `dashboard/app.py`, `carteiras.py`, `liquidacao.py`, `metricas_carteira.py`, `construtor.py`), as confirmações no plano das abas "Carteiras" e "Placar da turma" e testes com AppTest e gold local em `tmp_path`.

Divergência apontada no plano: o prompt ligava o placar ao RF-26; na spec, o placar é o RF-28 (o RF-26 é a gravação no contrato gold_turma). O autor confirmou ("meu prompt estava errado"); a T-47 atende RF-24, RF-25 e RF-28.

Decisões do autor no plano:
1. Menor perda máxima com seletor de carteira, cesta_raras como padrão (o RF-28 não diz de qual carteira).
2. `PAINEL_GOLD_TURMA_DIR` só para teste e desenvolvimento, fora do `.env.example`.
3. Comparação estrita: empate não conta como "superou" (a selado da DRI com 0 unidades empata com a cdi).

Implementação em `dashboard/app.py` (nenhum arquivo em `src/` alterado):
- Leitura: as quatro tabelas das carteiras da gold da DRI (`composicao_carteira`, `liquidacao_carteira`, `liquidacao_item`, `metricas_carteira`), opcionais (sem elas, aviso "rode `make gold`"); a gold_turma de todas as coleções por curinga (`gold_turma/carteira/*/carteira.parquet`, `union_by_name`, só as colunas do contrato), somente leitura; sem arquivo, aviso em vez de erro. Com `PAINEL_GOLD_DIR` e sem `PAINEL_GOLD_TURMA_DIR`, o placar não vai ao S3.
- Aba "Carteiras": seletor "com taxa de venda (15%)" e "sem taxa (0%)" (a taxa vem da própria gold); gráfico do valor de liquidação por dia e carteira com a linha de referência em R$ 1.000,00 e losangos nos dias com preço carregado ou CDI pendente; tabela de métricas da taxa escolhida com o retorno com e sem taxa e a diferença em p.p. (zero em dolar e cdi); composição por carteira com a regra numa frase, item, acabamento, unidades, preço de compra, custo, sobra e caixa, aviso explícito da selado com 0 unidades e todo o valor em caixa (ADR-006) e legenda do fallback; propria com "regra pendente" como aviso, fora do gráfico, com métricas "—".
- Aba "Placar da turma": `placar_turma` (função pura) com retorno acumulado no último dia de cada coleção, "X de N" para selado × cdi e cesta_raras × dolar (N = coleções com as duas carteiras com valor) e menor perda máxima pela `perda_maxima` da T-43, com empates listados; avisos de só DRI, de coleção na gold sem gold_turma e de período diferente do da DRI; tabela por coleção.
- Formatação pt-BR (`formatar_pp` novo, sem "-0,00"), datas dd/mm e `width="stretch"`.

Teste: `tests/unidade/test_painel_carteiras.py`; carteiras e gold_turma da DRI geradas pelo código real (`calcular_carteiras`, T-44) sobre uma gold de fixture; gold_turma de OUTA e OUTB escrita à mão no contrato; contas conferidas no docstring do teste (booster box 250 × 5,00 = R$ 1.250,00 → 0 unidades; dolar 200 × 4,99 = R$ 998,00; cdi 1000 → 1000,50; perdas 10% e 0% na cesta; "2 de 3", "1 de 3", OUTB).

Tentativas até a verificação passar: nenhuma correção; 14 passed na 1ª execução; os testes da T-45 e da T-46 continuaram passando sem alteração.

Resultado: `.venv/bin/python -m pytest tests/unidade/test_painel_carteiras.py -v`: 14 passed; suíte de unidade (`.venv/bin/python -m pytest tests/unidade -q`): 377 passed; evidência em `docs/evidencias/T-47_painel_carteiras.txt`. T-47 marcada como [x] em `specs/tasks.md`. Nenhum acesso ao RustFS, ao MinIO ou à rede; a conferência visual com dados reais fica com o autor (`make painel`).

## Ajuste da T-47 após o make painel (2026-11-16)

Prompt: "ajuste visual após conferência com dados reais", com três pedidos do autor depois do `make painel`, com teste, sem commit.

1. Gráfico da aba "Carteiras": eixo y sem rótulos e linhas sobrepostas (com dados reais, propria ≈ R$ 875 e dolar ≈ R$ 1.028 no último dia). Diagnóstico pelo spec gerado (não houve como renderizar o Vega no Codespace): a camada da linha de referência usava outro campo (`referencia`), sem escala nem eixo, e a escala y compartilhada das camadas misturava as definições (a da referência inclui o zero) e o eixo formatado. Correção: o mesmo `alt.Y` (campo `valor`, escala com domínio explícito de `dominio_y`, `zero=False`, `nice=False`, eixo com rótulos "R$ 1.000,00") em todas as camadas, `resolve_scale(y="shared")`; `dominio_y` cobre os dados e R$ 1.000,00 com folga de 5% (mínimo R$ 1,00). Conta no teste: 875 e 1.028 → folga (1028 − 875) × 5% = 7,65 → domínio 867,35 a 1.035,65.
2. "R$" em `st.markdown`, `st.caption`, `st.info` e similares virava fórmula LaTeX (par de "$"). Todas as chamadas de texto Markdown do painel (todas as abas: caption, markdown, info, warning, error, title, subheader) passam por `texto.*`, que escapa o "$" sem escape (`escapar_cifrao`, sem escape duplo); rótulos de `st.metric` e do filtro de preço mínimo também. Teste: em reais e em dólar, nenhum corpo de texto, rótulo de métrica ou de widget tem "$" sem escape, e "R\$ 1.250,00", "R\$ 100,00" e "US\$" continuam presentes. Tabelas (`st.dataframe`) e gráficos não interpretam Markdown e não mudaram.
3. Composição: coluna "Observação" com "0 unidades: preço de compra acima de R$ 100,00" (ou do valor alocado) em qualquer item com 0 unidades; quando todas as cartas de uma carteira ficam com 0 unidades, aviso "Nenhuma das dez cartas cabe em R$ 100,00; todo o valor ficou em caixa." (na propria, com o selado comprado: "Nenhuma das cinco cartas cabe em R$ 100,00; o valor das cartas ficou em caixa.").

Fixture do teste: Carta 12 a US$ 30 (30 × 5,00 = R$ 150,00 > R$ 100,00 → 0 unidades na cesta_raras, sem mudar as demais contas) e a variante `cartas_caras` (+ US$ 20 em todas as cartas, a mais barata a R$ 130,00 → nenhuma carta compra unidade).

Tentativas até a verificação passar:
1. 1 falha em `test_grafico_com_referencia_em_1000_e_dias_marcados` (teste anterior): o valor da referência passou da coluna `referencia` para `valor`, o mesmo campo das outras camadas; a asserção foi atualizada (`valor` = 1000 e `referencia` = "R$ 1.000,00"). Resultado: 50 passed.

Resultado: `.venv/bin/python -m pytest tests/unidade/test_painel_carteiras.py tests/unidade/test_painel_base.py tests/unidade/test_painel_perguntas.py -v`: 50 passed; suíte de unidade: 384 passed; saída acrescentada a `docs/evidencias/T-47_painel_carteiras.txt`. Nenhum acesso ao RustFS, ao MinIO ou à rede; a nova conferência visual fica com o autor (`make painel`).

Observação para o ATAM (T-53), registrada a pedido do autor a partir da conferência com dados reais: na DRI, a selado e a cesta_raras ficaram 100% em caixa pela regra de unidades inteiras (o booster box custa mais que R$ 1.000,00 e as dez cartas mais caras custam mais que R$ 100,00 cada), de modo que só a propria teve exposição real a mercado. É um ponto de sensibilidade da regra de unidades inteiras e do orçamento por item (RF-23, ADR-005, ADR-006) e um risco para a leitura do placar (RF-28): selado e cesta_raras da DRI medem o caixa rendendo CDI, não o desempenho de selado ou de cartas.

## Ajuste 2 da T-47: altura dos gráficos (2026-11-16)

Prompt: "ajuste visual após conferência com dados reais". No `make painel`, o gráfico das carteiras aparecia certo em tela cheia, mas na tela normal a área de plotagem ficava espremida a uma linha, sem eixo y visível. Pedido do autor: altura fixa (height=420 no Altair), legenda à direita como na P3, a mesma altura nos outros gráficos que não a tivessem e um teste da altura no spec.

Conferência: nenhum gráfico do painel definia altura (série do item, P2, P3, P4, P5 e carteiras). As carteiras usavam a legenda abaixo e na vertical (`LEGENDA_INTEIRA`), que com cinco itens disputa a altura com a área de plotagem.

Implementação em `dashboard/app.py`: constante `ALTURA_GRAFICO = 420` aplicada em `grafico_linhas` (série do item, P2 e P3), na P4, na P5 e no gráfico em camadas das carteiras; legenda das carteiras `LEGENDA_DIREITA` (`orient="right"`, `labelLimit=0`). A P2 continua com a legenda abaixo (não foi pedido mudar).

Teste: `test_grafico_das_carteiras_com_altura_fixa_e_legenda_a_direita` (height 420 e legenda à direita no spec) e `test_todos_os_graficos_do_painel_tem_a_mesma_altura` (os seis gráficos com `ALTURA_GRAFICO`).

Tentativas até a verificação passar: nenhuma correção; 52 passed na 1ª execução.

Resultado: testes do painel (`test_painel_carteiras.py`, `test_painel_base.py`, `test_painel_perguntas.py`): 52 passed; suíte de unidade: 386 passed; saída acrescentada a `docs/evidencias/T-47_painel_carteiras.txt`. Conferência visual na tela normal fica com o autor (`make painel`).

## Prompt da T-48 – Verificador de cobertura (2026-11-16)

Prompt: "prompt de implementação padrão" para a T-48, com os extras: confirmar no plano o que o verificador mede, de onde lê e o formato da saída de `make cobertura` (insumo da tabela "Dias sem coleta" da T-49 e da conferência do agendador da T-52); testes de unidade sem rede; sem acesso ao RustFS nem ao MinIO.

Plano aprovado sem ajustes:
- Mede, para cada data de calendário entre o primeiro e o último dia (menor e maior `data` com arquivo do TCGCSV, spec "Definições"), a origem: `bruto` (os quatro arquivos de `ARQUIVOS_DO_DIA`, reusados de `tcg.coleta.guarda`), `registro` (linha na tabela com motivo não vazio, com os arquivos que faltam) ou `faltante` (linha sem motivo não conta e aparece como "registro sem motivo"). Avisos sem reprovar: registro fora do período, data inválida na tabela, data completa também registrada, chave de outro group_id.
- Lê a Branch dados-raw pelo Leitor da branch (`git fetch` só da ref remota, `git ls-tree`, sem checkout), como o `make sync`, e não o data lake (plan.md, decisão "Verificador de cobertura lê a Branch dados-raw"; ADR-001); `--sem-buscar` lê a ref local. Tabela: seção `## Dias sem coleta` do README até o próximo título, `| data | motivo |` com data `AAAA-MM-DD`.
- Saída: relatório na saída padrão (`periodo: …`, uma linha por data, `resumo: …`, `datas faltantes: …`), logs na saída de erro; códigos 0 (coberto), 1 (datas faltantes), 2 (falha do git, branch sem bruto do TCGCSV ou README sem a seção). `make cobertura` não carrega o `.env`.
- Observação registrada no plano, sem mudança: pelo spec, o período termina no último dia com bruto; dias depois de uma parada definitiva da coleta não aparecem como faltantes, o que a T-52 cobre pelo `gh run list`.

Teste: `tests/unidade/test_cobertura.py` (16 testes): parser do README, período completo, dia ausente, registro com e sem motivo, dia parcial, período só pelo TCGCSV (`cotacao.json` em 01 não estende 03 a 05 → 3 datas), avisos, formato exato do relatório e ponta a ponta com remoto bare local (bruto em 03, 04 e 06 e 05 registrado → 6 − 3 + 1 = 4 datas, código 0; data faltante → 1; sem TCGCSV ou sem repositório → 2).

Tentativas até a verificação passar: nenhuma correção; 16 passed na 1ª execução.

Resultado: `.venv/bin/python -m pytest tests/unidade/test_cobertura.py -v`: 16 passed; suíte de unidade: 402 passed; evidência em `docs/evidencias/T-48_cobertura.txt`. T-48 marcada como [x] em `specs/tasks.md`. Nenhum acesso ao RustFS, ao MinIO ou à rede; `make cobertura` sobre a branch real (com `git fetch` do GitHub) fica com o autor.

## Prompt da T-49 – README completo (2026-11-16)

Prompt: "prompt de implementação padrão" para a T-49, com os extras: README que permita a reprodução da T-50 a partir de clone limpo (pré-requisitos, `make setup`, `.env` a partir do `.env.example` sem expor valores, MinIO local × data lake da turma, ordem `make sync` → `make silver` → `make gold` → `make painel` → `make test` → `make cobertura`); visão geral e camadas, serviços e custo zero, coleta agendada com os dois crons e a regra do ADR-007, evidências e ADRs, P1 a P5 e as cinco carteiras em uma frase cada, R-01 e R-02, e a seção "Dias sem coleta" no formato do `make cobertura`, sem linhas (o `make cobertura` do autor em 16/11 deu 13 datas de 03 a 15/11, todas com bruto, 0 faltantes), com a recuperação manual de 04/11 como observação fora da tabela.

Divergência encontrada no plano e correção: a linha da T-49 em `specs/tasks.md` pedia "disparo manual antes das 23h59 UTC (R-01)". Essa era a mitigação do ADR-001, substituída pelo ADR-007 (data de referência pelo ciclo do TCGCSV): o R-01 de `specs/plan.md` e a seção 15 do plano já diziam "disparo manual dentro do ciclo". Decisão do autor: seguir o ADR-007 no README ("dentro do ciclo, antes das 20h UTC de D+1", de preferência a partir das 20h30 UTC de D) e corrigir o texto da linha da T-49 para "disparo manual dentro do ciclo, antes das 20h UTC de D+1 (R-01, ADR-007)".

README: seções Coleção escolhida, Visão geral (diagrama mermaid e tabela das camadas), Perguntas e carteiras, Serviços usados e custo zero (tabela com custo de cada serviço), Coleta agendada (`30 20 * * *` e `30 6 * * *`, regra do ciclo com exemplos, nenhuma requisição para arquivo existente, sincronização no mesmo job), Riscos do agendador (R-01 e R-02), Data lake (texto anterior mantido, mais a tabela dos três ambientes), Como rodar (pré-requisitos, `make setup`, `cp .env.example .env` com a tabela das variáveis sem valores de credencial, `make up` opcional, a ordem dos seis comandos e os códigos de saída do `make cobertura`), Documentação e evidências (specs, os oito ADRs, `docs/evidencias/`, `docs/prompts.md`) e Dias sem coleta, por último, com a tabela vazia e a observação de 04/11 (recuperada às 2026-11-05T01:31Z, `docs/evidencias/T-57_recuperacao.txt`).

Teste: `tests/unidade/test_readme.py` (17 testes): seções na ordem, serviços listados e todos gratuitos, comandos de "Como rodar" na ordem, MinIO local × data lake, crons iguais aos de `.github/workflows/coleta.yml` e exemplos do ciclo, R-01 pela regra do ADR-007 (sem "23h59") e R-02 com 60 dias e 12/12/2026, tabela lida por `ler_dias_sem_coleta` (T-48) com 0 registros e 0 avisos, observação de 04/11 fora da tabela, links relativos existentes e nenhuma credencial preenchida.

Tentativas até a verificação passar: nenhuma correção; 17 passed na 1ª execução.

Resultado: `.venv/bin/python -m pytest tests/unidade/test_readme.py -v`: 17 passed; suíte de unidade: 419 passed; evidência em `docs/evidencias/T-49_readme.txt`. T-49 marcada como [x] em `specs/tasks.md`, com o texto corrigido. Nenhum acesso ao RustFS, ao MinIO ou à rede; a reprodução a partir de clone limpo é a T-50, do autor.

## Ajustes do README da T-49 (2026-11-16)

Prompt: "ajustes do README após revisão do autor", em duas rodadas, mantendo os testes passando, sem commit.

Rodada 1 (três ajustes pedidos pelo autor):
1. P2: "índice base 100 da cesta fixa de selados contra o da cesta fixa de cartas Double Rare em diante", como no painel (RF-16), no lugar de "média dos selados contra a soma das cartas".
2. cesta_raras: acrescentado "sem Code Card" (RF-23).
3. R-02: explicado que os 60 dias contam desde a última atividade no repositório e, a pedido do autor, que os commits diários da coleta na `dados-raw` manteriam o agendamento ativo. Ao entregar, o agente avisou que essa afirmação não tinha sido conferida na documentação do GitHub.

Rodada 2 (correção do R-02): o autor mandou retirar a afirmação sobre os commits da coleta, por não estar confirmada. O R-02 ficou só com os 60 dias contados desde a última atividade no repositório, e não desde o início do projeto, o workflow na `main`, o prazo do projeto (12/12/2026) e a recomendação de conferir na aba Actions (e com `gh run list --workflow coleta.yml`) se o agendamento do workflow `coleta` continua ativo, reativando-o ali (Actions → coleta → Enable workflow) se for desativado.

Tentativas até a verificação passar: nenhuma correção; 17 passed nas duas rodadas, sem alterar o teste.

Resultado: `.venv/bin/python -m pytest tests/unidade/test_readme.py -v`: 17 passed após cada rodada; saídas acrescentadas a `docs/evidencias/T-49_readme.txt`. Nenhum acesso ao RustFS, ao MinIO ou à rede.

## Registro da T-50 – Clone limpo (2026-11-16)

Prompt: registrar a T-50, executada pelo autor, sem executar nenhum comando do pipeline. O autor entregou em `/tmp/t50.txt` a saída real de `make setup`, `make up`, `make sync`, `make silver`, `make gold`, `make test` e `make cobertura` num clone limpo em `/tmp/clone-limpo`, seguindo só o README; o agente conferiu que o arquivo não tinha usuário, senha nem chave antes de copiar trechos, criou a evidência com data e hora, roteiro, observação sobre o `.env` e as linhas relevantes de cada comando, marcou a T-50 e propôs a mensagem de commit.

Observação: o `.env` do clone foi copiado do `.env` do autor, com o mesmo conteúdo que o README manda preencher a partir do `.env.example`; `make up` é opcional no README e foi executado para conferir o MinIO local; `make painel` foi conferido pelo autor no navegador (oito abas).

Resultado: todos os comandos terminaram com sucesso (2026-11-16, 23h05 a 23h10 UTC): sincronização com 52 chaves já existentes recusadas e 0 falhas; silver com 281 produtos, 5798 preços em 13 datas e quarentena vazia; gold com a DRI e a coleção 24541 (só leitura), 7114 linhas no fato de preços e 65 na gold_turma; `make test`: 463 passed; `make cobertura`: 13 datas, 13 com bruto, 0 faltantes. Evidência em `docs/evidencias/T-50_clone_limpo.md`. Nenhum acesso do agente ao data lake, ao MinIO ou à rede.

## Registro da T-51 – Busca de credenciais (2026-11-16)

Prompt: registrar a T-51, executada pelo autor em 16/11/2026, por volta das 23h20 UTC, no Codespace, em `/workspaces/dcs-2026-projeto`, sem executar nenhuma busca e sem ler o `.env`. O autor informou só as contagens de ocorrências; nenhum valor foi exibido, porque os valores foram lidos do `.env` (MINIO_ACCESS_KEY e MINIO_SECRET_KEY) ou digitados com `read -rs`, sem eco. O agente criou a evidência com os comandos (com as variáveis, sem valores), os resultados e a conclusão, marcou a T-51 e propôs a mensagem de commit.

Resultado: `git fetch --all` e `git log -p --all | grep -c -F` com a chave e o segredo atuais: 0; `grep -rlF` com a chave e o segredo atuais nos arquivos do repositório, excluindo `.env`, `.venv` e `.git`: 0 arquivos; `git log -p --all | grep -c -F` com o segredo do MinIO antigo da turma (Railway): 0, e com o segredo do primeiro endpoint do RustFS (s3.afonsolelis.tech), trocado pelo professor em 15/11: 0; o usuário antigo não foi buscado, por ser palavra comum nos textos do projeto (falso positivo); `gh run view 43905874560 --log` (último run da coleta por `gh run list --workflow coleta.yml --limit 1`, evento schedule, concluído com sucesso cerca de 7 horas antes da busca; 564 linhas por `wc -l`, confirmando o download do log): 0 ocorrências da chave e do segredo atuais, com os secrets mascarados como `***`. Conclusão: nenhuma credencial encontrada no histórico, nos arquivos nem nos logs (RNF-08). Evidência em `docs/evidencias/T-51_busca_credenciais.md`. Nenhum acesso do agente ao `.env`, ao data lake, ao MinIO ou à rede.

Ajuste após revisão do autor: evidência renomeada de `T-51_busca_segredos.md` para `T-51_busca_credenciais.md`, nome previsto em `specs/tasks.md`; comandos da evidência trocados pelos comandos exatos do autor (carga do `.env` com `set -a`, `git fetch --all -q`, contagem de arquivos com `wc -l`, segredos antigos com `read -rs ANTIGA` e `unset ANTIGA`, `gh run list` para achar o run, `wc -l` do log e `unset` final das variáveis MINIO_*); data e hora (por volta das 23h20 UTC) e dados do run acrescentados.

## Registro da T-52 – Agendador e requisições (2026-11-16)

Prompt: registrar a T-52 a partir dos dados que o autor coletou do GitHub em 16/11/2026, por volta das 23h30 UTC, e salvou em `/tmp/t52/`: `runs.txt` e `runs.json` (`gh run list --workflow coleta.yml --limit 100`, 29 execuções), `log_<id>.txt` (`gh run view <id> --log` de cada execução) e `cobertura.txt` (`make cobertura`). O agente só analisou os arquivos, sem executar `gh`, `git fetch` nem `make` e sem ler o `.env`. Antes de citar trechos, conferiu que os logs não têm credencial. Depois montou a tabela por execução (id, evento, início, horário agendado de referência e atraso, conclusão, data de referência, arquivos novos e pulados, requisições ao TCGCSV e resultado do sync, com "não consta" quando o dado não está no log), os totais, a conferência por data e o R-02, marcou a T-52 e propôs a mensagem de commit.

Resultado: os 29 logs têm só valores mascarados (`token: ***`, `AUTHORIZATION: basic ***`, `MINIO_*: ***`, `endpoint=***`), sem nenhuma credencial. 29 execuções: 25 schedule (13 principais, 12 reservas) e 4 workflow_dispatch; 25 success e 4 failure (duas recusas da guarda antiga antes da T-57, a falha do CDI em 08/11, recuperada pela reserva, e a falha `InvalidAccessKeyId` do sync em 15/11, na troca de endpoint da T-58, com o bruto de 14/11 já publicado). O horário agendado de referência é o cron imediatamente anterior ao início, porque o log não informa qual cron disparou. Atraso das agendadas: média 6h14min47s, máximo 10h15min30s (reserva 42657979297); nenhum dos 26 horários agendados do período ficou sem execução. 15 execuções sem nenhuma requisição (13 com todos os arquivos já presentes e 2 recusadas); 26 requisições ao TCGCSV (2 por coleta, todas `status=200` na primeira tentativa), no máximo 4 num dia civil UTC (07/11) e 2 por data de referência, contra o limite de 10000 de `config/parametros.toml` (RNF-12). Cada data de 03/11 a 15/11 tem bruto e execução bem-sucedida dentro do ciclo, o que bate com `make cobertura` (13 datas, 0 faltantes, 52 arquivos) e com a tabela "Dias sem coleta" vazia. 04/11 foi recuperado pela execução manual 41949048376 (T-57). Ressalva: 03/11 e 04/11 foram gravados por execuções manuais. 16/11 ainda não estava coletado, porque a principal das 20h30 UTC de 16/11 ainda não tinha rodado. R-02: agendamento ativo, com a última agendada 43905874560 em 2026-11-16T16:17:36Z, com success. Evidência em `docs/evidencias/T-52_agendador.md`. Nenhum acesso do agente ao `.env`, ao data lake, ao MinIO ou à rede.

Ajuste após revisão do autor: a ressalva do RNF-13 e o critério do horário de referência foram mantidos como estavam. Na falha da execução 43656334396, acrescentado que o autor rodou `make sync` em 15/11, antes das 14h04 UTC, mas a saída dessa execução não foi guardada, e o resultado dela continua como "não consta". Corrigido também o erro de digitação `[[x]` para `[x]` na linha da T-51 em `specs/tasks.md`, sem nenhuma outra alteração na linha.

## Prompt da T-53 – Avaliação ATAM (2026-11-16)

Prompt (C-R-E-A-T-E): conduzir, como arquiteto de dados, a avaliação ATAM do próprio projeto só com o que está no repositório e nas evidências, sem mudar código. Escrever `docs/atam.md` com objetivo e escopo; atributos de qualidade e drivers (OBJ, DRV, RNF); árvore de utilidade com prioridade (importância e dificuldade, A/M/B); cenários em seis partes (fonte, estímulo, artefato, ambiente, resposta e medida), um por atributo relevante e todos citando RNF; abordagens e ADRs por cenário; pontos de sensibilidade; tradeoffs; riscos com mitigação; não riscos; e ligação para `docs/rastreabilidade.md`. Cada afirmação aponta para evidência, e o que não tem evidência vira hipótese ou pendência. Itens obrigatórios: atrasos do agendador (T-52) e ADR-007; ressalva do RNF-13 (03/11 e 04/11 manuais); dependência das silvers dos colegas (24541 depois da troca de endpoint); troca de endpoint sem mudança de código e busca de credenciais com zero ocorrências (ADR-008, T-51); taxa de venda de 15% e unidades inteiras como pontos de sensibilidade; branch `dados-raw` contra data lake como tradeoff (ADR-001, ADR-008); divergência do "primeiro dia" em `perguntas.py` como risco baixo. Mostrar o rascunho, esperar a confirmação e só depois gravar, verificar, registrar e propor o commit.

Resultado do rascunho: 13 cenários (C-01 a C-13), seis pontos de sensibilidade, seis tradeoffs, nove riscos e oito não riscos, com evidência citada em cada item. O agente apontou dois itens sem evidência no repositório, marcados como pendência: os retornos da propria (−12,49% e −3,49%) e as datas da coleção 24541 no data lake novo. Apontou também que a linha da T-53 em `specs/tasks.md` não indica nome de evidência.

Ajustes do autor antes de gravar:
1. Criada `docs/evidencias/T-53_observacoes_painel.md` com as observações do autor no `make painel` de 16/11/2026, depois do `make silver` e do `make gold` das 22h12 UTC (13 datas da DRI):
   - métricas das cinco carteiras com taxa de 15%, incluindo a propria com −12,49% com taxa, −3,49% sem taxa e diferença de −9,01 p.p.;
   - composição: selado e cesta_raras com 0 unidades, booster box a R$ 2.095,11, carta mais barata a R$ 132,12, e itens da propria;
   - placar: ASC de 14/11 a 15/11, 0 de 2 e 1 de 2;
   - gold: 7114 linhas, das quais 5798 da DRI e 1316 de 2 dias da 24541.
   A evidência entrou em S-01, S-02, C-13 e RS-03, e os dois itens saíram das pendências.
2. RS-05 reescrito: o placar usa comparação estrita (conferido em `dashboard/app.py`, `placar_turma`), e a selado da DRI aparece como "não" acima da cdi por empate. O leitor pode interpretar isso como desempenho ruim, quando ela ficou 100% em caixa.
3. Evidência da verificação em `docs/evidencias/T-53_atam.txt`.

Resultado: `test -s docs/atam.md && grep -c "RNF-" docs/atam.md`: 42, código 0. Cada RNF-01 a RNF-13 aparece no título de ao menos um cenário, e os 13 cenários têm as linhas "Resposta" e "Medida". Nenhum arquivo de `docs/evidencias/` citado falta. Saída em `docs/evidencias/T-53_atam.txt`. Nenhum código alterado; nenhum acesso do agente ao `.env`, ao data lake, ao MinIO ou à rede.

## Prompt da T-54 – Matriz de rastreabilidade (2026-11-16)

Prompt (C-R-E-A-T-E, prompt 11.2 do enunciado da Aula 08): como engenheiro de qualidade que monta matrizes de rastreabilidade a partir de artefatos existentes, sem completar lacunas por conta própria, gerar `docs/rastreabilidade.md` com uma linha para cada RF e RNF de `specs/spec.md`, na ordem do arquivo, com as colunas Requisito, Objetivo, Decisão, Componente, Evidência, Estado e Razão. Regras: IDs e texto dos requisitos exatamente como na spec; não criar requisito, decisão, componente ou teste; coluna vazia vira "sem registro", e "sem registro" em Evidência nunca é "atendido"; testes confirmados com `pytest --collect-only -q`; não alterar `specs/`, `src/`, `dashboard/` nem `tests/`. Abaixo da tabela, três listas: requisitos sem evidência, componentes que nenhum requisito cita e testes que não citam requisito. Ordem de leitura: persona, objetivos, spec, plan, ADRs, tasks, coleta do pytest e evidências. Perguntar antes se a spec tivesse IDs repetidos. Complemento do projeto: coleta com `.venv/bin/python -m pytest --collect-only -q`; `docs/atam.md` e `docs/prompts.md` também como fontes; commit que implementou o requisito na coluna Evidência (`git log --oneline`); sem `.env`, sem RustFS, sem MinIO e sem commit; rodar a verificação da T-54 e mostrar a saída real; T-54 e este registro só depois da revisão do autor.

Resultado do rascunho: a spec não tem IDs repetidos. A matriz tem 41 linhas: 40 "atendido" e 1 "parcial" (RNF-13, porque 03/11 e 04/11 foram gravados por execuções manuais, como na ressalva do C-01 e no RS-02 do `docs/atam.md`). Os 104 testes citados estão na coleta (463 testes), todos os commits citados existem, e a coluna Objetivo confere com a linha "Origem" de cada requisito. Requisitos sem evidência: nenhum. Componentes sem requisito: os seis `__init__.py` dos subpacotes e `scripts/hipoteses_bruto.py`. Testes sem requisito: os 6 de `tests/unidade/test_hipoteses_bruto.py`. A verificação da T-54 não imprimiu nenhuma linha "falta".

Revisão do autor:
1. Amostra de três linhas "atendido", sorteadas com `random.seed(54)`: RF-09, RNF-01 e RNF-08. Para cada uma, o agente mostrou o critério Dado/Quando/Então da spec, o trecho dos testes citados com as asserções e a saída real de `.venv/bin/python -m pytest -v` (8 testes, 8 passed). Avaliação:
   - RF-09: `test_tipo_produto_rf09_selado_carta_e_code_card` verifica o critério. Monta os três produtos do critério (sem número, carta com número, Code Card sem número) e compara os tipos com `selado`, `carta` e `carta`. `test_contagens_iguais_as_do_t13` complementa com o bruto real (25 selados, 256 cartas, 12 Code Cards).
   - RNF-01: `test_nunca_usa_ptax_posterior` verifica o critério. Com PTAX de 09/10 e de 13/10, confere que 10/10, 11/10 e 12/10 usam a de 09/10, que 13/10 usa a de 13/10 e que nenhuma linha do fato tem `data_ptax` posterior à `data`. `test_feriado_nunca_usa_ptax_posterior` repete a conferência no `fato_cambio_diario`.
   - RNF-08: os testes verificam só parte do critério. Os dois testes do workflow verificam por inteiro a parte "secrets só no `env` do passo de sincronização, sem `echo`". `test_credenciais_nao_aparecem_no_log` verifica que o log mascara credenciais. `test_config_minio_lida_do_ambiente` mostra que a configuração é lida do ambiente, mas não prova que ela venha "só" do ambiente. A parte "a busca por credenciais no histórico e nos logs não encontra nada" não tem teste automatizado: vem da busca manual do autor em `docs/evidencias/T-51_busca_credenciais.md`. O estado "atendido" depende da soma dos testes com essa evidência.
2. Colunas Decisão e Razão mantidas como o agente preencheu. Desvio em relação ao formato literal do prompt 11.2:
   - em Decisão, quando nenhum ADR cita o requisito, a célula diz "sem registro em ADR" e aponta a escolha técnica da seção 6 (ou 4) de `specs/plan.md` que o cobre, em vez de só "sem registro";
   - em Razão, as linhas "atendido" também têm o motivo do estado, em vez de "sem registro".
3. Corrigido em `docs/atam.md` (C-05 e C-06) o nome do teste: `tests/integracao/test_reprocessar.py` passou a `tests/integracao/test_reprocessar_integracao.py`, o nome coletado depois do commit `775d3bf` (T-33). Duas ocorrências, sem nenhuma outra alteração. A observação da matriz foi atualizada.
4. `scripts/hipoteses_bruto.py` e `tests/unidade/test_hipoteses_bruto.py` servem de apoio à validação das hipóteses da spec na T-13 (`docs/evidencias/T-13_hipoteses.md`), sem papel no pipeline, e por isso não ganham requisito próprio. Os `__init__.py` só marcam pacote. Nota acrescentada abaixo das listas da matriz.
5. T-54 marcada como [x] em `specs/tasks.md`; saída da verificação e da revisão por amostra em `docs/evidencias/T-54_rastreabilidade.txt`.
6. Segunda rodada de ajustes do autor:
   - RNF-08 mantido como "atendido". A coluna Razão agora diz que os testes cobrem as credenciais lidas do ambiente, o mascaramento no log e os secrets só no `env` do passo de sincronização, sem `echo`. A parte "busca no histórico e nos logs" é comprovada pela busca manual do autor (`docs/evidencias/T-51_busca_credenciais.md`), e não por teste automatizado.
   - Seção 11 do `docs/atam.md`: "que será criada na T-54" passou a "criada na T-54", sem outra alteração.

Resultado: a verificação da T-54 não imprimiu nenhuma linha "falta" (código de saída 0); 41 linhas na matriz (40 atendidos e 1 parcial); 463 testes coletados. Nenhum código, teste, `specs/spec.md` ou `specs/plan.md` alterado; nenhum acesso do agente ao `.env`, ao data lake, ao MinIO ou à rede; nenhum commit.

## Prompt da T-55 – Registro de pendências (2026-11-17)

```text
[C] Personagem
Você é um engenheiro de dados que organiza as pendências do projeto de forma verificável, sem resolver nenhuma delas.

[R] Pedido
Execute a tarefa T-55 de specs/tasks.md: crie docs/pendencias_aula08.md. Mostre o rascunho, espere minha confirmação e depois grave, rode a verificação da tarefa, salve a evidência em docs/evidencias/ com o nome indicado em specs/tasks.md, marque a T-55 como [x], registre em docs/prompts.md e proponha a mensagem de commit docs(T-55): descrição [RF-yy ou RNF-yy].

[E] Exemplos
Tabela com as colunas #, Pendência, Origem, Requisito, Impacto, Responsável, Prazo e Estado (exemplo: P-01, trocar "MinIO" por "data lake" nas mensagens de log, revisão da T-58, cosmético, agente, 05/12/2026, aberta).

[A] Ajustes
- Reúna as pendências já registradas em docs/atam.md (seção de pendências e riscos), docs/rastreabilidade.md (linhas parcial) e docs/prompts.md, sem inventar outras.
- Inclua também as que o autor registrou na conversa: divergência de "primeiro dia" em src/tcg/gold/perguntas.py; "MinIO" por "data lake" nos logs e nome do logger; passo do workflow com a palavra "turma"; actions/checkout v5 e actions/setup-python v6; credenciais de teste em tracebacks do pytest; coleção dos itens fora do gráfico na P5 e aviso de um só dia comum na P3; make sync, silver, gold e cobertura antes da mentoria (05/12) e da entrega (12/12), com prints e conclusões atualizados; backup do prefixo raw da DRI fora do repositório; commit de fechamento com tag entrega-final e envio do formulário até 12/12/2026, 23h59.
- Classifique o impacto (limitador, funcional, documentação, cosmético) e ordene: primeiro o que pode acionar limitador.
- Prazo: 05/12/2026 ou 12/12/2026. Responsável: autor ou agente. O que não couber até 12/12 deve dizer que vira "parcial" ou "não atendido" na matriz, com a razão.
- Escreva como registro do autor, sem citar material de aula. Não altere nenhum outro arquivo além dos listados. Não leia o .env, não acesse o RustFS e não faça commit.

[T] Tipo de saída
docs/pendencias_aula08.md com a tabela e uma seção "Perguntas para a mentoria", a evidência, specs/tasks.md e docs/prompts.md atualizados, e um resumo de até cinco linhas.
```

Resultado do rascunho: 15 pendências, com a coluna Encaminhamento acrescentada ao exemplo, porque o critério da T-55 pede descrição, origem e encaminhamento. O agente apontou que a linha da T-55 em `specs/tasks.md` não indica nome de evidência e propôs `T-55_pendencias.txt`. Para as pendências que não mudam o estado de nenhum requisito, o encaminhamento diz isso com a razão, em vez de forçar "parcial" ou "não atendido".

Ajustes do autor antes de gravar:
1. Evidência em `docs/evidencias/T-55_pendencias.txt`.
2. `limitador` reservado ao que pode acionar um limitador da avaliação ou impedir a entrega. Só a P-01 ficou assim. Categoria nova `entrega` para P-02 e P-04, e ordem: limitador, entrega, funcional, documentação, cosmético. Seção "Como ler" atualizada.
3. P-03 passou a `funcional`: o aviso do workflow diz que as ações já rodam forçadas no Node.js 24, então a coleta não para por isso. Encaminhamento ajustado.
4. Pergunta 3 da mentoria: "a 24541 e a ASC" corrigido para "a ASC (24541)", que é a mesma coleção.
5. Em "Como ler": toda pendência que muda código (P-03, P-06, P-07, P-08, P-09, P-14, P-15) precisa antes virar tarefa nova em `specs/tasks.md`.
6. Tratamento dos itens sem mudança de estado na matriz aprovado.

Os IDs P-xx do rascunho foram mantidos, porque o autor se refere a eles nos ajustes. Por isso a P-04 aparece antes da P-03 na tabela.

Resultado: `test -s docs/pendencias_aula08.md` com código de saída 0. 15 linhas P-xx com descrição, encaminhamento e origem preenchidos e impacto, responsável, prazo e estado válidos, em ordem por impacto. 4 perguntas para a mentoria. Saída em `docs/evidencias/T-55_pendencias.txt`. T-55 marcada como [x]. Nenhuma pendência foi resolvida, nenhum código foi alterado e não houve acesso do agente ao `.env`, ao data lake, ao MinIO ou à rede, nem commit.

## Prompt da T-56 – Autoauditoria final (2026-11-17)

Prompt 11.1 do enunciado da Aula 08, seguido do complemento do autor para este projeto.

```text
[C] Personagem
Você é um auditor técnico de projetos de engenharia de dados. Você
compara o repositório com o enunciado e relata o que encontrou. Você não
corrige nada.

[R] Pedido
Audite o repositório contra o enunciado do projeto final (pipeline de
cartas Pokémon do TCGplayer) e escreva o relatório em
docs/auditoria_final.md. Para cada item abaixo, diga cumprido, parcial
ou ausente, com o arquivo e a linha que sustentam o julgamento.
1. Artefatos SDD: AGENTS.md, docs/00_persona.md,
   docs/01_objetivos_negocio.md, specs/spec.md (RF/RNF com
   Dado/Quando/Então), specs/plan.md (C4 em Mermaid), specs/tasks.md,
   docs/atam.md, docs/adr/, docs/rastreabilidade.md, docs/prompts.md.
2. Coleta: job diário com User-Agent próprio, pausa entre chamadas e
   repetição com espera crescente.
3. Bruto: chave tcg/raw/tcgplayer/group_id=<id>/data=<AAAA-MM-DD>/;
   o código confere a existência da chave e recusa a sobrescrita; há
   teste que demonstra isso.
4. Silver: colecao, produto e preco_diario com as colunas e os tipos do
   contrato comum; modelo Pydantic por tabela; quarentena com motivo;
   preço ausente gravado como nulo.
5. Gold: fato_preco_diario e dimensões de produto, coleção, data e
   acabamento, lidas sobre a silver de todas as coleções; ADR.
6. Reprocessamento: um comando reconstrói silver e gold sem duplicar.
7. Dashboard: as cinco perguntas, com imagem das cartas e link do
   produto.
8. Testes: unidade sem rede; VCR para o TCGCSV; Testcontainers para o
   MinIO.
9. Rastreabilidade: toda linha "atendido" tem evidência; commits citam
   T-xx e RF/RNF (git log --oneline).
10. Ordem SDD: spec.md e tasks.md têm commits anteriores aos commits de
    código que implementam seus itens (git log --follow).
11. Segredos: procure no histórico (git log -p) senhas, chaves do MinIO,
    URLs com usuário e senha e arquivos .env versionados.
12. Lacunas da série: dias sem coleta declarados no README.
13. Câmbio: PTAX e CDI no bruto; conversão pela PTAX de fechamento do
    dia ou do último dia útil anterior, nunca posterior; teste com fim
    de semana e feriado.
14. Desafio: cinco carteiras com unidades inteiras, PTAX de compra e de
    venda, taxa de venda parametrizada, composição escolhida só com
    dados do primeiro dia; resultado no contrato de gold_turma.

[E] Exemplos
| # | Item | Estado | Evidência | Lacuna |
|---|------|--------|-----------|--------|
| 3 | Bruto | parcial | src/coleta/gravador_raw.py:41 usa put_object sem stat_object | falta verificação de existência e teste de recusa |
| 4 | Silver | parcial | src/silver/preco.py:22 grava market_price como VARCHAR | quebra o contrato comum |

[A] Ajustes
- Não edite nenhum arquivo além de docs/auditoria_final.md.
- Não rode git commit, git push nem comandos que gravem no MinIO.
- Não marque "cumprido" sem citar arquivo e linha ou saída de comando.
- Se encontrar um segredo, não o copie: informe só o arquivo, o commit
  e o tipo de credencial.
- Separe fato, lacuna e suposição.

[T] Tipo de saída
docs/auditoria_final.md com a tabela dos 14 itens no formato do
exemplo; as lacunas ordenadas pelo impacto, primeiro as que acionam
limitador (pipeline que não roda, segredo versionado, silver fora do
contrato, dado inventado, código sem especificação prévia); e uma seção
"Suposições".

[E] Extras
Fontes de verdade: os arquivos do repositório, o histórico do git e a
leitura (somente leitura) da própria partição no MinIO. Pode rodar
pytest e DESCRIBE no DuckDB sobre a silver. Se não conseguir rodar algum
comando, diga qual e por quê. Pare ao final.

Complemento do projeto (T-56 de specs/tasks.md):
- O AGENTS.md proíbe o agente de acessar o data lake da turma (RustFS) e de ler o .env; ele prevalece sobre a leitura da partição citada acima. Use as evidências em docs/evidencias/ (por exemplo T-50_clone_limpo.md e T-53_observacoes_painel.md) e os testes com MinIO descartável no lugar do DESCRIBE sobre a silver real, e diga na seção "Suposições" que esse comando não foi rodado e por quê.
- Rode os testes com .venv/bin/python -m pytest, nunca com o pytest do PATH.
- Use também docs/pendencias_aula08.md: lacuna já registrada lá deve citar o número P-xx.
- Ao final, rode a verificação da T-56: test -s docs/auditoria_final.md && git diff --stat -- . ':!docs/auditoria_final.md' (a segunda parte não pode listar nenhum arquivo) e mostre a saída real.
- Não marque a T-56 em specs/tasks.md nem altere docs/prompts.md: isso será feito num segundo passo, depois da minha revisão.
```

Resultado da auditoria: `docs/auditoria_final.md` com a tabela dos 14 itens, as lacunas por impacto, os fatos de verificação, as suposições e os comandos não executados. 13 itens cumpridos e 1 parcial: o item 9, por causa de dois commits fora da convenção (`10b6b13`, com espaço em `chore (T-00)`, e `bed3e94`, `Initial commit`). Nenhum limitador encontrado. Suíte com `.venv/bin/python -m pytest -q`: 463 passed. Scripts sobre o histórico conferiram que as referências da matriz existem, que nenhum commit de código vem antes da sua tarefa ou dos seus requisitos e que o único valor no padrão de credencial do histórico é o texto fictício "ficticio" em `docs/evidencias/T-15_compose.txt` (commit `7f693b5`). Duas lacunas eram novas: L-08 (verificação e gravação em duas chamadas no sincronizador) e L-11 (commits fora da convenção). As demais citam P-xx. Não foram rodados, por regra do `AGENTS.md`: o DESCRIBE sobre a silver real e qualquer leitura do data lake (substituídos pelos testes com MinIO descartável e pelas evidências T-50 e T-58), `git fetch`, `make cobertura`, `gh run list` e `make reprocessar`. Verificação: `test -s docs/auditoria_final.md && git diff --stat -- . ':!docs/auditoria_final.md'` com código de saída 0 e nenhum arquivo listado.

Revisão do autor: relatório aprovado sem alterações. Segundo passo pedido pelo autor:
1. P-16 (L-08) em `docs/pendencias_aula08.md`: impacto documentação, estado `aceita`. O grupo de concorrência do workflow cobre as execuções do Actions; um `make sync` manual simultâneo gravaria os mesmos bytes da branch; recomendação de não rodar `make sync` perto das 20h30 e das 06h30 UTC.
2. P-17 (L-11): impacto cosmético, estado `aceita`. Corrigir exigiria reescrever o histórico com `push --force`, proibido pelo `AGENTS.md`.
3. Contagem do registro atualizada: 17 pendências, 14 abertas e 3 aceitas.
4. Saída da verificação em `docs/evidencias/T-56_auditoria.txt`, executada de novo antes das alterações do segundo passo, com o mesmo resultado.
5. T-56 marcada como [x] em `specs/tasks.md` e este registro.

`docs/auditoria_final.md` não foi alterado no segundo passo. Não houve acesso do agente ao `.env`, ao data lake, ao MinIO local ou à rede, nem commit.
