# AGENTS.md

Regras para qualquer agente de IA (ou pessoa) que trabalhe neste repositório. Idioma de todos os arquivos: português do Brasil.

## Escopo

- Projeto final individual da disciplina Data Collection and Storage.
- Coleção única: Pokémon TCG "SV10: Destined Rivals" (sigla DRI, groupId 24269).
- Fontes de dados:
  - TCGCSV: `https://tcgcsv.com/tcgplayer/3/24269/products` e `https://tcgcsv.com/tcgplayer/3/24269/prices`.
  - Banco Central do Brasil: PTAX (câmbio USD/BRL) e CDI.
- Entregas: camada raw (resposta original), silver, gold e um dashboard em Python.
- Fora do escopo: outras coleções ou groupIds, escrita em prefixos de outros alunos, qualquer dado que não venha das fontes acima.

## Ambiente

- Desenvolvimento e execução local no GitHub Codespaces, com Docker e Python.
- MinIO local por docker compose (a criar numa tarefa futura), acessível em `localhost:9000`, bucket `tcg`.
- Configuração lida de variáveis de ambiente definidas no `.env` (modelo em `.env.example`).

## Arquitetura prevista

Tudo nesta seção está **a confirmar no plan.md**.

1. Coleta diária no GitHub Actions, depois das 20h UTC, gravando as respostas originais numa branch `dados-raw` deste repositório.
2. Um comando local sincroniza esses arquivos da branch `dados-raw` para o MinIO local, recusando sobrescrita.
3. Silver, gold e dashboard rodam a partir do MinIO local.

## Regras de escrita no data lake

- Escreva somente em prefixos com `group_id=24269`: `tcg/raw/*/group_id=24269/`, `tcg/silver/*/group_id=24269/`, `tcg/gold/group_id=24269/`, `tcg/gold_turma/carteira/group_id=24269/`.
- Nenhum objeto em `tcg/raw/` é sobrescrito ou apagado; antes de gravar, confira se a chave já existe e, se existir, aborte com erro.
- A camada raw guarda a resposta original da fonte, byte a byte, sem transformação.
- Silver e gold são derivadas exclusivamente da raw; podem ser reconstruídas, mas só dentro dos prefixos acima.
- TCGCSV: toda requisição envia o User-Agent próprio definido em `TCG_USER_AGENT`; pausa mínima de 100 ms entre chamadas; no máximo uma coleta por dia, sempre depois das 20h UTC.
- Dia sem coleta é registrado na tabela "Dias sem coleta" do README.md, com data e motivo; não se inventam nem se copiam dados para preencher lacunas.

## Comandos permitidos e proibidos

Permitidos:
- Ler e editar arquivos do repositório (exceto `.env`).
- `git status`, `git diff`, `git log`, `git add`.
- Rodar testes locais com pytest, quando existirem.

Proibidos:
- Ler, abrir ou imprimir o `.env` (`cat .env`, `source .env` seguido de `echo`, `printenv` de credenciais etc.).
- Qualquer comando de exclusão no MinIO: `mc rm`, `mc rb`, `remove_object`, `remove_bucket` ou equivalentes.
- `git push --force` (e variantes como `--force-with-lease`).
- `git commit` e `git push` pelo agente: o agente apenas propõe a mensagem de commit; quem commita é o autor.
- Acessar a rede ou o MinIO fora de uma tarefa de `specs/tasks.md` que peça isso explicitamente.

## Política de segredos

- A credencial do MinIO local fica só no `.env`, que está no `.gitignore`.
- Nunca escreva credencial em arquivo versionado, log, evidência (`docs/evidencias/`), prompt (`docs/prompts.md`) ou mensagem de commit.
- O `.env.example` contém apenas nomes de variáveis com valores vazios ou fictícios.
- O código lê credenciais de variáveis de ambiente; nunca as recebe por argumento de linha de comando nem as imprime.
- Se uma credencial vazar em qualquer lugar, pare e avise o autor antes de qualquer outro passo.

## Ordem SDD e gates por etapa

Ordem obrigatória:

1. `AGENTS.md`
2. `docs/00_persona.md`
3. `docs/01_objetivos_negocio.md`
4. `specs/spec.md`
5. `specs/plan.md`
6. `specs/tasks.md`
7. Implementação: uma tarefa por vez, cada uma com teste.
8. Validação ATAM.

Regras:
- Nenhum código em `src/` antes de `specs/tasks.md` existir.
- Gate de cada etapa: o artefato foi revisado pelo autor e commitado antes da etapa seguinte.
- Não crie artefatos de uma etapa futura antecipadamente.
- Registre cada prompt relevante e o resultado da revisão em `docs/prompts.md`.

## Convenção de commits

- Formato: `tipo(T-xx): descrição [RF-yy]`.
  - `tipo`: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`.
  - `T-xx`: identificador da tarefa em `specs/tasks.md`.
  - `[RF-yy]`: requisito funcional de `specs/spec.md` atendido (omitir quando não houver).
- Descrição curta, no imperativo ou nominal, em português do Brasil.
- Mensagem desta etapa: `chore(T-00): esqueleto SDD do projeto final`.
