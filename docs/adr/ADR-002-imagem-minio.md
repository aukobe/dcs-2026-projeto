# ADR-002: Imagem do MinIO com tag fixada

## Status

Aceito em 2026-11-03.

## Contexto e forças

Silver, gold e painel rodam a partir de um MinIO local no Codespace (RES-07), e o sincronizador grava nele o bruto da branch `dados-raw` (ADR-001, RF-05). Esse MinIO precisa subir igual em qualquer clone limpo (RNF-10), sem custo (RNF-09) e com as credenciais só no `.env` (RNF-08).

Fatos que pesam na escolha da imagem:
- A edição comunitária do MinIO entrou em modo de manutenção em dezembro de 2025, o repositório foi arquivado em abril de 2026 e deixaram de ser publicadas imagens Docker oficiais.
- A imagem `ghcr.io/coollabsio/minio`, da coolLabs, é construída a partir das releases oficiais e é a usada pelo template de MinIO do Railway.
- Essa imagem já traz o cliente `mc` e não traz `curl` nem `wget`; um healthcheck por requisição HTTP não tem como rodar dentro dela.

Forças em jogo:
- **Reprodutibilidade** (RNF-10): o mesmo clone tem de rodar o mesmo binário do servidor hoje e no dia da avaliação.
- **Custo zero** (RNF-09): imagem pública, sem registro pago.
- **Segredos fora do Git** (RNF-08, RES-06): usuário e senha raiz vêm do `.env`, nunca do `docker-compose.yml`.
- **Volume efêmero**: o MinIO local só existe enquanto o Codespace existe.

## Requisitos e cenários relacionados

| Requisito | Cenário que esta decisão precisa atender |
|---|---|
| RF-05 | O sincronizador encontra o MinIO pronto em `localhost:9000` e grava no bucket `tcg`. |
| RNF-07 | Os testes de integração sobem um MinIO descartável com a mesma imagem e a mesma tag do MinIO local de trabalho, separado dele, e o descartam no final. |
| RNF-08 | `docker-compose.yml` versionado não contém credencial; usuário e senha raiz vêm de `MINIO_ACCESS_KEY` e `MINIO_SECRET_KEY` do `.env`. |
| RNF-09 | A imagem é pública e gratuita. |
| RNF-10 | A partir de um clone limpo com `.env` preenchido, `make up` sobe o mesmo binário e o serviço fica `healthy`. |

## Alternativas consideradas

| Alternativa | Por que foi descartada |
|---|---|
| Tag `latest` da coolLabs | Cada execução poderia baixar e rodar um binário diferente, o que quebra a reprodução (RNF-10). |
| Imagem `minio/minio` antiga do Docker Hub | Sem atualizações oficiais desde o fim da publicação das imagens; ficaria presa numa versão sem correções. |
| Compilar o MinIO a partir do código-fonte | Tempo de build e manutenção de um Dockerfile próprio sem ganho para o projeto. |
| Outro object storage compatível com S3, como o RustFS | O projeto já está desenhado sobre o MinIO (SDK `minio`, testcontainers, DuckDB com httpfs) e a troca não atende nenhum requisito a mais. |
| Bind mount numa pasta do repositório | Os dados do MinIO correriam o risco de ir para o Git. |
| Binário do MinIO instalado à mão no Codespace | Não reproduzível a partir de clone limpo. |

## Decisão e táticas

O MinIO local roda por docker compose com a imagem `ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z`, porta 9000 (API) e 9001 (console), dados num volume nomeado e healthcheck `mc ready local`. Usuário e senha raiz vêm de `MINIO_ACCESS_KEY` e `MINIO_SECRET_KEY` do `.env`; o código acha o servidor por `MINIO_ENDPOINT`. `make up` é o único ponto de entrada.

Os testes de integração (RNF-07) usam a mesma imagem e a mesma tag (`ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z`), para que o teste rode o mesmo binário do ambiente de trabalho.

| Tática | Atributo de qualidade | Como aparece |
|---|---|---|
| Vínculo em tempo de configuração | Modificabilidade | Endpoint, bucket e credenciais no `.env`; trocar de servidor não muda código. |
| Versão fixada | Reprodutibilidade | Tag `RELEASE.2025-10-15T17-29-55Z` explícita no compose e nos testes de integração; nenhuma referência a `latest`. |
| Monitoramento por healthcheck | Disponibilidade | `mc ready local` dentro do contêiner; o serviço só aparece `healthy` quando o servidor responde. |
| Separar estado da computação | Durabilidade | Dados no volume nomeado; recriar ou atualizar o contêiner não apaga o bucket. |

## Consequências positivas

- Todo clone roda o mesmo binário do servidor (RNF-10), e os testes de integração rodam o mesmo binário do ambiente de trabalho.
- Imagem pública, sem custo (RNF-09).
- Nenhuma credencial no arquivo versionado (RNF-08).
- O healthcheck usa uma ferramenta que já está na imagem, sem instalar nada a mais.
- Trocar a tag é uma alteração pequena, revisável no diff.

## Consequências negativas

- Correções de segurança exigem trocar a tag manualmente; nada atualiza sozinho. A troca precisa ser feita nos dois lugares (compose e testes de integração).
- Dependência de um mantenedor terceiro (coolLabs) para continuar publicando imagens.
- O console na porta 9001 dá acesso total ao MinIO e não pode ter a porta encaminhada como pública no Codespace.
- O volume some se o Codespace for apagado; mitigado pela branch `dados-raw` (ADR-001), de onde `make sync` reconstrói o bruto.
- Tamanho da imagem e tempo do primeiro `make up`: hipótese: validação pendente.

## Riscos

| Risco | Mitigação |
|---|---|
| `mc ready local` não funcionar nessa imagem (R-07) | Confirmar na T-15 antes de depender do estado `healthy`. |
| A coolLabs remover a tag fixada do registro | Condição de revisão abaixo; o bruto continua na `dados-raw`. |
| Tag do compose e dos testes divergirem numa atualização | Teste do compose confere a tag; os testes de integração usam a mesma tag. |
| Porta 9001 encaminhada como pública por engano | Manter a visibilidade privada no Codespace; registrar o cuidado no README. |
| Perda do volume (R-11) | `make sync` a partir da `dados-raw` e `make reprocessar` para silver e gold. |

## Evidência necessária

- Teste do compose confirmando tag fixada (sem `latest`), healthcheck `mc ready local`, volume nomeado e credenciais vindas de variáveis; `docker compose config --quiet` sem erro (T-15).
- Confirmação de que `mc ready local` funciona na imagem fixada (T-15).
- `docker compose ps` com o serviço `healthy` e `git status` sem o `.env` (T-16).
- MinIO descartável dos testes de integração subindo com a mesma imagem e tag e sendo removido no final (T-19).

## Condição de revisão

- Se a coolLabs deixar de publicar a imagem, ou se surgir falha de segurança na tag fixada.
