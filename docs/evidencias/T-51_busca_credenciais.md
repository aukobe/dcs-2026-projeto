# T-51 – Busca de credenciais no histórico completo do repositório e nos logs de execução [RNF-08]

- **Executor:** autor
- **Data e hora:** 2026-11-16, por volta das 23h20 UTC
- **Local:** Codespace, em /workspaces/dcs-2026-projeto
- **Registro:** feito pelo agente a partir dos comandos e resultados informados pelo autor; o agente não executou nenhuma busca e não leu o .env.

## Como os valores foram fornecidos

Nenhum valor de credencial aparece nesta evidência, nos comandos nem na saída. Os valores atuais foram carregados do .env para variáveis do shell (MINIO_ACCESS_KEY e MINIO_SECRET_KEY), e os segredos antigos foram digitados com `read -rs`, sem eco. As buscas usam só `grep -c` (contagem de linhas) ou `grep -l` seguido de `wc -l` (contagem de arquivos), que não imprimem o texto encontrado. No fim, as variáveis foram apagadas do shell com `unset`.

## Comandos usados

Comandos exatos, na ordem em que foram executados:

```bash
set -a; . ./.env; set +a
git fetch --all -q

# 1. Histórico completo de todas as branches, com a chave e o segredo atuais
git log -p --all | grep -c -F -e "$MINIO_ACCESS_KEY" -e "$MINIO_SECRET_KEY"

# 2. Arquivos do repositório, excluindo .env, .venv e .git
grep -rlF -e "$MINIO_ACCESS_KEY" -e "$MINIO_SECRET_KEY" . --exclude=.env --exclude-dir=.venv --exclude-dir=.git | wc -l

# 3. Histórico completo com um segredo antigo, digitado sem eco
#    (executado duas vezes: segredo do MinIO antigo da turma e segredo do primeiro RustFS)
read -rs ANTIGA; git log -p --all | grep -c -F -e "$ANTIGA"; unset ANTIGA

# 4. Log do último run agendado da coleta no GitHub Actions
gh run list --workflow coleta.yml --limit 1
gh run view 43905874560 --log | grep -c -F -e "$MINIO_ACCESS_KEY" -e "$MINIO_SECRET_KEY"
gh run view 43905874560 --log | wc -l

unset MINIO_ACCESS_KEY MINIO_SECRET_KEY MINIO_ENDPOINT MINIO_BUCKET MINIO_SECURE
```

## Resultados

| # | Alvo da busca | Valores procurados | Resultado |
|---|---|---|---|
| 1 | `git log -p --all`, depois de `git fetch --all -q` | chave e segredo atuais (MINIO_ACCESS_KEY e MINIO_SECRET_KEY do .env) | 0 ocorrências |
| 2 | arquivos do repositório, excluindo .env, .venv e .git | chave e segredo atuais | 0 arquivos |
| 3a | `git log -p --all` | segredo do MinIO antigo da turma (Railway) | 0 ocorrências |
| 3b | `git log -p --all` | segredo do primeiro endpoint do RustFS (s3.afonsolelis.tech), trocado pelo professor em 15/11/2026 | 0 ocorrências |
| 4 | log do run 43905874560 | chave e segredo atuais | 0 ocorrências, em 564 linhas de log |

## Run conferido

- O run 43905874560 é o último run do workflow `coleta`, segundo `gh run list --workflow coleta.yml --limit 1`: um run agendado (evento `schedule`), concluído com sucesso em 16/11/2026, cerca de 7 horas antes da busca.
- `gh run view 43905874560 --log | wc -l` retornou 564 linhas, o que confirma que o log foi baixado e que a contagem 0 não vem de um log vazio.

## Observações

- O usuário antigo (Railway e primeiro endpoint do RustFS) não foi buscado: é uma palavra comum nos textos do projeto e daria falso positivo. Os segredos antigos, que identificam a credencial, foram buscados e não aparecem.
- Nos logs do GitHub Actions, os secrets aparecem mascarados como `***`; a busca do item 4 confirma que nenhum valor atual aparece em texto claro no log do run agendado.
- O item 1 cobre todas as branches obtidas pelo `git fetch --all`, inclusive `main` e `dados-raw`.

## Conclusão

Nenhuma credencial do data lake, atual ou antiga, foi encontrada no histórico completo do repositório, nos arquivos versionados nem no log do último run agendado da coleta. O critério de aceite do RNF-08 ("dado o histórico completo do repositório e os logs de execução, quando uma busca por credenciais for executada, então nada é encontrado") está atendido.
