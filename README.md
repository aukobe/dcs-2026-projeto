# dcs-2026-projeto

Projeto final individual da disciplina **Data Collection and Storage**.

## Coleção escolhida

Pokémon TCG **SV10: Destined Rivals** — sigla **DRI**, groupId **24269**.

## Resumo

Pipeline diário que coleta produtos e preços da coleção DRI pelo TCGCSV, a PTAX e o CDI do Banco Central, versiona as respostas originais na branch `dados-raw`, sincroniza esse bruto com o data lake da turma (bucket `tcg`), constrói as camadas silver e gold e alimenta um dashboard em Python.

## Data lake

O armazenamento oficial de bruto, silver, gold e gold_turma é o bucket `tcg` do data lake da turma, um RustFS compatível com S3 (ADR-008):

- endereço: `https://s3.afonsolelis.tech` (região `us-east-1`, endereçamento por caminho, TLS);
- escrita só nos prefixos com `group_id=24269`; as coleções dos colegas são só lidas;
- a branch `dados-raw` continua como fonte de verdade do bruto. O workflow da coleta sincroniza a branch com o data lake todo dia, depois do push; `make sync` faz o mesmo sob demanda e nunca sobrescreve uma chave existente.

**Credenciais.** A chave de acesso é compartilhada pela turma e chega pelo canal da turma. Ela fica só em dois lugares:

- no `.env` do Codespace (copiado do `.env.example`, fora do Git): `MINIO_ACCESS_KEY` e `MINIO_SECRET_KEY`;
- nos secrets do repositório no GitHub (Settings → Secrets and variables → Actions): `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY` e `MINIO_SECRET_KEY`, usados só pelo passo de sincronização do workflow.

Nunca coloque a chave em arquivo versionado, log, evidência ou mensagem de commit. Se ela vazar, avise o responsável pelo data lake para trocá-la e atualize o `.env` e os secrets.

**Desenvolvimento no MinIO local.** Para testar sem tocar no data lake da turma, suba o MinIO local com `make up` e aponte o `.env` para ele:

```dotenv
MINIO_ENDPOINT=localhost:9000
MINIO_SECURE=false
MINIO_ACCESS_KEY=<usuário raiz escolhido para o MinIO local>
MINIO_SECRET_KEY=<senha raiz escolhida para o MinIO local>
```

Volte o `.env` para `s3.afonsolelis.tech` e `MINIO_SECURE=true` antes de rodar `make sync`, `make silver` ou `make gold` para valer. Os testes de integração (`make test`) usam um MinIO descartável próprio e não tocam em nenhum dos dois.

## Como rodar

A definir nas próximas etapas.

## Dias sem coleta

| data | motivo |
|------|--------|
