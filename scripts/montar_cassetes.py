"""Monta os cassetes vcrpy da coleta a partir do bruto real (T-20; RNF-06, RF-01).

Lê, com o Leitor da branch (T-17), os quatro arquivos de `data=<DATA>` na ref
local `origin/dados-raw` — sem `git fetch` e sem nenhuma requisição ao TCGCSV
nem ao Banco Central — e grava em `tests/integracao/cassetes/`:

- `coleta_<DATA>.yaml`: quatro interações GET, com a URL exatamente como o
  coletor a envia (montada pelos próprios ClienteTcgcsv e ClienteBcb e
  preparada pelo `requests`), status 200 e corpo igual aos bytes do blob;
- `coleta_<DATA>.hashes.json`: id do blob e sha256 de cada arquivo.

Os cabeçalhos de resposta originais não estão no bruto; o cassete traz só
`Content-Type: application/json`, sem `Content-Encoding`, para que o corpo
chegue ao coletor sem nenhuma decodificação.

Uso: python scripts/montar_cassetes.py [AAAA-MM-DD] [--sobrescrever]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys

import requests
from vcr.request import Request
from vcr.serialize import serialize
from vcr.serializers import yamlserializer

from tcg.coleta.bcb import ClienteBcb
from tcg.coleta.guarda import ARQUIVOS_DO_DIA, caminho_raw
from tcg.coleta.tcgcsv import ClienteTcgcsv
from tcg.config import ler_colecao, ler_parametros
from tcg.sync import leitor_branch

RAIZ = Path(__file__).resolve().parents[1]
PASTA_CASSETES = RAIZ / "tests" / "integracao" / "cassetes"
REF = "origin/dados-raw"
DATA_PADRAO = "2026-11-03"


def urls_do_coletor(data: dt.date) -> dict[str, str]:
    """URL, como o `requests` a envia, de cada arquivo do dia."""
    tcgcsv = ClienteTcgcsv(http=None, colecao=ler_colecao())
    bcb = ClienteBcb(http=None, parametros=ler_parametros())
    brutas = {
        "products.json": tcgcsv.url_products(),
        "prices.json": tcgcsv.url_prices(),
        "cotacao.json": bcb.url_ptax(data),
        "cdi.json": bcb.url_cdi(data),
    }
    return {arquivo: requests.Request("GET", url).prepare().url for arquivo, url in brutas.items()}


def montar(data: dt.date, repo: Path = RAIZ, ref: str = REF) -> tuple[str, dict]:
    group_id = ler_colecao().group_id
    blobs = {a.chave: a.blob for a in leitor_branch.listar(repo, ref)}
    urls = urls_do_coletor(data)
    pedidos, respostas, hashes = [], [], {}
    for item in ARQUIVOS_DO_DIA:
        chave = caminho_raw(Path(), item, group_id, data).as_posix()
        if chave not in blobs:
            raise SystemExit(f"arquivo ausente em {ref}: {chave}")
        corpo = leitor_branch.ler(repo, blobs[chave])
        pedidos.append(Request("GET", urls[item.arquivo], None, {}))
        respostas.append({
            "status": {"code": 200, "message": "OK"},
            "headers": {"Content-Type": ["application/json"]},
            "body": {"string": corpo},
        })
        hashes[chave] = {"blob": blobs[chave], "sha256": hashlib.sha256(corpo).hexdigest(), "bytes": len(corpo)}
    metadados = {"origem": f"{ref}, data={data:%Y-%m-%d}", "montado_por": "scripts/montar_cassetes.py (T-20)"}
    texto = serialize({"requests": pedidos, "responses": respostas, "metadata": metadados}, yamlserializer)
    return texto, hashes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("data", nargs="?", default=DATA_PADRAO, type=dt.date.fromisoformat)
    parser.add_argument("--sobrescrever", action="store_true", help="regrava cassetes existentes")
    args = parser.parse_args(argv)

    cassete = PASTA_CASSETES / f"coleta_{args.data:%Y-%m-%d}.yaml"
    manifesto = PASTA_CASSETES / f"coleta_{args.data:%Y-%m-%d}.hashes.json"
    if not args.sobrescrever and (cassete.exists() or manifesto.exists()):
        print(f"cassete já existe, nada gravado: {cassete.relative_to(RAIZ)}", file=sys.stderr)
        return 1
    texto, hashes = montar(args.data)
    PASTA_CASSETES.mkdir(parents=True, exist_ok=True)
    cassete.write_text(texto, encoding="utf-8")
    manifesto.write_text(json.dumps(hashes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for chave, h in hashes.items():
        print(f"{chave} blob={h['blob']} sha256={h['sha256']} bytes={h['bytes']}")
    print(f"gravados: {cassete.relative_to(RAIZ)}, {manifesto.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
