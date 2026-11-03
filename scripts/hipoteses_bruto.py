"""Validação das hipóteses da spec sobre o bruto de um dia (T-13).

Lê os quatro arquivos brutos da branch `dados-raw` por `git show`, sem checkout
e sem nenhuma requisição às fontes, e imprime as contagens usadas em
`docs/evidencias/T-13_hipoteses.md`.

Uso: python scripts/hipoteses_bruto.py [AAAA-MM-DD]
(sem data, usa a primeira data de raw/tcgplayer/group_id=24269/ na branch).
"""

from __future__ import annotations

from collections import Counter
import json
import subprocess
import sys

REF = "origin/dados-raw"
GRUPO = "group_id=24269"
LISTA_DOUBLE_RARE = [
    "Double Rare",
    "Ultra Rare",
    "Illustration Rare",
    "Special Illustration Rare",
    "Hyper Rare",
]


def campo_estendido(produto: dict, nome: str) -> str | None:
    """Valor de um campo de `extendedData`, ou None se ausente ou vazio."""
    for campo in produto.get("extendedData") or []:
        if campo.get("name") == nome:
            valor = campo.get("value")
            return valor if valor not in (None, "") else None
    return None


def tipo_produto(produto: dict) -> str:
    """Regra hipotética da spec: sem número é selado, salvo Code Card."""
    if campo_estendido(produto, "Rarity") == "Code Card":
        return "carta"
    return "selado" if campo_estendido(produto, "Number") is None else "carta"


def eh_booster_box(nome: str) -> bool:
    return "Booster Box" in nome and "Case" not in nome


def analisar_produtos(produtos: dict) -> dict:
    resultados = produtos["results"]
    raridades = Counter(campo_estendido(p, "Rarity") for p in resultados)
    sem_numero = [p for p in resultados if campo_estendido(p, "Number") is None]
    return {
        "total_items": produtos.get("totalItems"),
        "total_results": len(resultados),
        "raridades": dict(sorted(raridades.items(), key=lambda kv: (kv[0] is None, kv[0] or ""))),
        "fora_da_lista": sorted(
            r for r in raridades if r is not None and r not in LISTA_DOUBLE_RARE
        ),
        "sem_numero": len(sem_numero),
        "sem_numero_code_card": sorted(
            p["name"] for p in sem_numero if campo_estendido(p, "Rarity") == "Code Card"
        ),
        "sem_numero_nomes": sorted(p["name"] for p in sem_numero),
        "tipos": dict(Counter(tipo_produto(p) for p in resultados)),
        "com_image_url": sum(1 for p in resultados if p.get("imageUrl")),
        "com_url": sum(1 for p in resultados if p.get("url")),
        "booster_box": sorted(
            (p["productId"], p["name"]) for p in resultados if eh_booster_box(p["name"])
        ),
    }


def analisar_precos(produtos: dict, precos: dict) -> dict:
    linhas = precos["results"]
    por_id = {p["productId"]: p for p in produtos["results"]}
    selados = {pid for pid, p in por_id.items() if tipo_produto(p) == "selado"}
    caixas = {pid for pid, p in por_id.items() if eh_booster_box(p["name"])}
    com_preco = {l["productId"] for l in linhas if l.get("marketPrice") is not None}
    ids_com_linha = {l["productId"] for l in linhas}
    return {
        "linhas": len(linhas),
        "subtipos": dict(Counter(l.get("subTypeName") for l in linhas)),
        "market_price_nulo": sum(1 for l in linhas if l.get("marketPrice") is None),
        "produtos_sem_linha": len(set(por_id) - ids_com_linha),
        "selados": len(selados),
        "selados_com_preco": len(selados & com_preco),
        "selados_sem_preco": sorted(por_id[i]["name"] for i in selados - com_preco),
        "booster_box_precos": sorted(
            (l["productId"], l.get("subTypeName"), l.get("marketPrice"))
            for l in linhas
            if l["productId"] in caixas
        ),
    }


def analisar_ptax(cotacao: dict) -> dict:
    valores = cotacao["value"]
    fechamentos = sorted(
        v["dataHoraCotacao"][:10] for v in valores if v.get("tipoBoletim") == "Fechamento"
    )
    return {
        "boletins": len(valores),
        "tipos": dict(Counter(v.get("tipoBoletim") for v in valores)),
        "datas": sorted({v["dataHoraCotacao"][:10] for v in valores}),
        "fechamentos": fechamentos,
    }


def analisar_cdi(cdi: list) -> dict:
    return {"dias": len(cdi), "datas": [d["data"] for d in cdi]}


def _git_show(caminho: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{REF}:{caminho}"], check=True, capture_output=True
    ).stdout


def _primeira_data() -> str:
    saida = subprocess.run(
        ["git", "ls-tree", "--name-only", f"{REF}:raw/tcgplayer/{GRUPO}/"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return saida.splitlines()[0].split("=", 1)[1]


def main(argv: list[str]) -> int:
    data = argv[1] if len(argv) > 1 else _primeira_data()
    base = f"data={data}"
    produtos = json.loads(_git_show(f"raw/tcgplayer/{GRUPO}/{base}/products.json"))
    precos = json.loads(_git_show(f"raw/tcgplayer/{GRUPO}/{base}/prices.json"))
    cotacao = json.loads(_git_show(f"raw/bcb_ptax/{GRUPO}/{base}/cotacao.json"))
    cdi = json.loads(_git_show(f"raw/bcb_cdi/{GRUPO}/{base}/cdi.json"))
    relatorio = {
        "data": data,
        "produtos": analisar_produtos(produtos),
        "precos": analisar_precos(produtos, precos),
        "ptax": analisar_ptax(cotacao),
        "cdi": analisar_cdi(cdi),
    }
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
