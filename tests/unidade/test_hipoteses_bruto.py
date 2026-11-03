"""Testes das funções puras de `scripts/hipoteses_bruto.py` (T-13).

Usam JSONs sintéticos pequenos, sem rede e sem git.
"""

from pathlib import Path
import importlib.util

CAMINHO = Path(__file__).resolve().parents[2] / "scripts" / "hipoteses_bruto.py"
_spec = importlib.util.spec_from_file_location("hipoteses_bruto", CAMINHO)
hb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hb)


def _produto(pid, nome, numero=None, raridade=None, imagem="i", url="u"):
    estendido = []
    if numero is not None:
        estendido.append({"name": "Number", "value": numero})
    if raridade is not None:
        estendido.append({"name": "Rarity", "value": raridade})
    return {"productId": pid, "name": nome, "imageUrl": imagem, "url": url, "extendedData": estendido}


PRODUTOS = {
    "totalItems": 5,
    "results": [
        _produto(1, "Destined Rivals Booster Box"),
        _produto(2, "Destined Rivals Booster Box Case", imagem=""),
        _produto(3, "Carta X", numero="001/182", raridade="Double Rare"),
        _produto(4, "Code Card - X", raridade="Code Card", url=None),
        _produto(5, "Carta Y", numero="002/182", raridade="Rare"),
    ],
}

PRECOS = {
    "results": [
        {"productId": 1, "marketPrice": 200.0, "subTypeName": "Normal"},
        {"productId": 2, "marketPrice": None, "subTypeName": "Normal"},
        {"productId": 3, "marketPrice": 10.0, "subTypeName": "Holofoil"},
        {"productId": 5, "marketPrice": 0.5, "subTypeName": "Normal"},
        {"productId": 5, "marketPrice": 0.8, "subTypeName": "Reverse Holofoil"},
    ]
}


def test_tipo_produto_sem_numero_selado_e_code_card_carta():
    tipos = [hb.tipo_produto(p) for p in PRODUTOS["results"]]
    assert tipos == ["selado", "selado", "carta", "carta", "carta"]


def test_booster_box_exclui_case():
    assert hb.eh_booster_box("Destined Rivals Booster Box")
    assert not hb.eh_booster_box("Destined Rivals Booster Box Case")


def test_analisar_produtos_conta_raridades_numero_imagem_e_link():
    r = hb.analisar_produtos(PRODUTOS)
    assert r["total_results"] == 5
    assert r["sem_numero"] == 3
    assert r["sem_numero_code_card"] == ["Code Card - X"]
    assert r["fora_da_lista"] == ["Code Card", "Rare"]
    assert r["raridades"][None] == 2
    assert r["com_image_url"] == 4
    assert r["com_url"] == 4
    assert r["booster_box"] == [(1, "Destined Rivals Booster Box")]


def test_analisar_precos_preco_nulo_conta_como_sem_preco():
    r = hb.analisar_precos(PRODUTOS, PRECOS)
    assert r["linhas"] == 5
    assert r["market_price_nulo"] == 1
    assert r["produtos_sem_linha"] == 1
    assert r["selados"] == 2
    assert r["selados_com_preco"] == 1
    assert r["selados_sem_preco"] == ["Destined Rivals Booster Box Case"]
    assert r["booster_box_precos"] == [(1, "Normal", 200.0)]
    assert r["subtipos"] == {"Normal": 3, "Holofoil": 1, "Reverse Holofoil": 1}


def test_analisar_ptax_agrupa_boletins_por_tipo():
    cotacao = {
        "value": [
            {"dataHoraCotacao": "2026-10-26 10:11:39.2", "tipoBoletim": "Abertura"},
            {"dataHoraCotacao": "2026-10-26 13:09:51.0", "tipoBoletim": "Fechamento"},
            {"dataHoraCotacao": "2026-10-27 13:05:00.0", "tipoBoletim": "Fechamento"},
        ]
    }
    r = hb.analisar_ptax(cotacao)
    assert r["tipos"] == {"Abertura": 1, "Fechamento": 2}
    assert r["fechamentos"] == ["2026-10-26", "2026-10-27"]
    assert r["datas"] == ["2026-10-26", "2026-10-27"]


def test_analisar_cdi_conta_dias():
    r = hb.analisar_cdi([{"data": "26/10/2026", "valor": "0.05"}, {"data": "27/10/2026", "valor": "0.05"}])
    assert r == {"dias": 2, "datas": ["26/10/2026", "27/10/2026"]}
