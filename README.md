# Branch dados-raw

Bruto da coleção Pokémon TCG "SV10: Destined Rivals" (DRI, groupId 24269),
gravado pelo coletor diário do GitHub Actions (ADR-001).

- Caminho de cada arquivo: `raw/<fonte>/group_id=24269/data=AAAA-MM-DD/<arquivo>`.
- Cada arquivo é a resposta original da fonte, byte a byte, sem transformação.
- Nenhum arquivo é sobrescrito nem apagado.
- `.gitattributes` com `* -text` impede conversão de fim de linha.
- Commits do coletor: `dados(coleta): AAAA-MM-DD [RF-01]`.

O código fica na branch `main`; esta branch é órfã e guarda só dados.
