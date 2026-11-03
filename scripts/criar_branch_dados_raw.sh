#!/usr/bin/env bash
# Cria localmente a branch órfã dados-raw (T-08, RF-02, ADR-001).
#
# Uso: scripts/criar_branch_dados_raw.sh [diretório do repositório]
#
# A branch contém só `.gitattributes` (`* -text`) e um README curto, sem
# nenhum histórico da main. O script usa só comandos internos do Git
# (hash-object, mktree, commit-tree, branch): não faz checkout, não altera a
# árvore de trabalho, não acessa a rede e NÃO faz push. A publicação é feita
# pelo autor no T-09.
set -euo pipefail

BRANCH="dados-raw"
MENSAGEM="chore(T-08): branch órfã dados-raw [RF-02]"
REPO="${1:-.}"

erro() {
    echo "erro: $*" >&2
    exit 1
}

git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1 \
    || erro "'$REPO' não é um repositório Git"

if git -C "$REPO" rev-parse --verify --quiet "refs/heads/$BRANCH" >/dev/null; then
    erro "a branch local '$BRANCH' já existe; nada foi alterado"
fi
if git -C "$REPO" rev-parse --verify --quiet "refs/remotes/origin/$BRANCH" >/dev/null; then
    erro "a branch remota 'origin/$BRANCH' já existe; nada foi alterado"
fi

GITATTRIBUTES='* -text
'

README='# Branch dados-raw

Bruto da coleção Pokémon TCG "SV10: Destined Rivals" (DRI, groupId 24269),
gravado pelo coletor diário do GitHub Actions (ADR-001).

- Caminho de cada arquivo: `raw/<fonte>/group_id=24269/data=AAAA-MM-DD/<arquivo>`.
- Cada arquivo é a resposta original da fonte, byte a byte, sem transformação.
- Nenhum arquivo é sobrescrito nem apagado.
- `.gitattributes` com `* -text` impede conversão de fim de linha.
- Commits do coletor: `dados(coleta): AAAA-MM-DD [RF-01]`.

O código fica na branch `main`; esta branch é órfã e guarda só dados.
'

blob_attr=$(printf '%s' "$GITATTRIBUTES" | git -C "$REPO" hash-object -w --stdin)
blob_readme=$(printf '%s' "$README" | git -C "$REPO" hash-object -w --stdin)

arvore=$(printf '100644 blob %s\t.gitattributes\n100644 blob %s\tREADME.md\n' \
    "$blob_attr" "$blob_readme" | git -C "$REPO" mktree)

commit=$(git -C "$REPO" commit-tree "$arvore" -m "$MENSAGEM")

git -C "$REPO" branch "$BRANCH" "$commit"

echo "branch órfã '$BRANCH' criada localmente no commit $commit (sem push)"
echo "para publicar (T-09): git push -u origin $BRANCH"
