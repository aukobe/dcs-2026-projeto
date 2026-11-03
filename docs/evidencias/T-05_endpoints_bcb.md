# T-05 – Endpoints do BCB confirmados (2026-11-03)

Consulta real feita em 2026-11-03 pelos próprios clientes (`ClienteBcb` sobre `ClienteHttp`), com a janela D−9 até D da data de coleta 2026-11-03 (25/10/2026 a 03/11/2026). User-Agent genérico de verificação (`dcs-2026-projeto/T-05 verificacao-endpoints`). Foram feitas 2 requisições, ambas com status 200 na primeira tentativa. O TCGCSV não foi chamado.

## PTAX: Olinda, `CotacaoMoedaPeriodo`

URL enviada (a requisição preparada pelo `requests` é idêntica a esta):

```text
https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?@moeda='USD'&@dataInicial='10-25-2026'&@dataFinalCotacao='11-03-2026'&$format=json
```

- Status 200, 5.338 bytes, sha256 `e48f248bd84adc3d09fd153811a3fa1b3a22c28a35a75b3841b7fde723511fbd`.
- Formato: objeto com `@odata.context` e a lista `value`. Cada item tem `paridadeCompra`, `paridadeVenda`, `cotacaoCompra`, `cotacaoVenda` (números), `dataHoraCotacao` (texto `AAAA-MM-DD HH:MM:SS.ffffff`, sem fuso) e `tipoBoletim`.
- A resposta tem 30 itens: 6 de `Abertura`, 18 de `Intermediário` e 6 de `Fechamento`. O valor de `tipoBoletim` vem acentuado, em UTF-8. A data do boletim só existe dentro de `dataHoraCotacao`.
- Há 6 dias úteis com `Fechamento`: 26/10 a 30/10 e 03/11. O dia 02/11 (Finados) e o fim de semana não aparecem. O boletim de 03/11 já estava publicado no horário da consulta.

Exemplo (primeiro item da resposta e um boletim `Fechamento`):

```json
{"@odata.context":"https://was-p.bcnet.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata$metadata#_CotacaoMoedaPeriodo","value":[{"paridadeCompra":1.00000,"paridadeVenda":1.00000,"cotacaoCompra":5.60360,"cotacaoVenda":5.60520,"dataHoraCotacao":"2026-10-26 10:11:39.211173","tipoBoletim":"Abertura"}, ...]}
{"paridadeCompra":1.00000,"paridadeVenda":1.00000,"cotacaoCompra":5.49980,"cotacaoVenda":5.50070,"dataHoraCotacao":"2026-10-26 13:09:51.106105","tipoBoletim":"Fechamento"}
```

## CDI: SGS, série 12

URL enviada (idêntica à requisição preparada):

```text
https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial=25/10/2026&dataFinal=03/11/2026
```

- Status 200, 206 bytes, sha256 `5667042041c7163de0c0d33a37652759accdabc9c59771f9570bb3f4a8032b42`.
- Formato: lista de objetos `{"data": "DD/MM/AAAA", "valor": "<texto decimal>"}`. O valor vem como **texto**, em % ao dia, com ponto decimal.
- Só há dias úteis, de 26/10 a 30/10. O CDI de 03/11 ainda não estava publicado, o que confirma a razão da janela (RF-01). O dia 02/11 é feriado.

Resposta completa:

```json
[{"data":"26/10/2026","valor":"0.050788"},{"data":"27/10/2026","valor":"0.050788"},{"data":"28/10/2026","valor":"0.050788"},{"data":"29/10/2026","valor":"0.050788"},{"data":"30/10/2026","valor":"0.050788"}]
```

## Consequências para tarefas futuras (só registro, nada foi implementado)

- T-25: a data da PTAX sai de `dataHoraCotacao`, e o filtro compara `tipoBoletim == "Fechamento"`. O `valor` do CDI precisa ser convertido de texto para DOUBLE.
- Pergunta aberta 2 de `specs/plan.md` (endpoints e formato do BCB): respondida por esta evidência.
