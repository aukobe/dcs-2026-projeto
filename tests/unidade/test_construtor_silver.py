"""Testes do Construtor da silver (T-27; RF-06, RF-07, RNF-11).

Cliente MinIO falso em memória e rede bloqueada (conftest). O bruto segue o
formato real: `results` no TCGCSV, `value` na PTAX e lista no CDI.
"""

import datetime as dt
import io
import json
import logging

import duckdb
import pytest

from tcg.config import ler_colecao
from tcg.lake.guarda_prefixo import PrefixoProibidoError
from tcg.silver import construtor
from tcg.silver.construtor import CONTRATO, chave_silver, construir_silver

BUCKET = "tcg"
DIAS = ["2026-11-01", "2026-11-02", "2026-11-03"]


class _Objeto:
    def __init__(self, nome):
        self.object_name = nome


class _Resposta(io.BytesIO):
    def release_conn(self):
        pass


class ClienteFalso:
    """Imita list_objects, get_object e put_object do SDK; sem exclusão."""

    def __init__(self, objetos):
        self.objetos = dict(objetos)
        self.gravadas = []

    def list_objects(self, bucket_name, prefix="", recursive=False):
        assert bucket_name == BUCKET and recursive
        return [_Objeto(k) for k in sorted(self.objetos) if k.startswith(prefix)]

    def get_object(self, bucket_name, object_name):
        return _Resposta(self.objetos[object_name])

    def put_object(self, bucket_name, object_name, data, length, content_type):
        assert not object_name.startswith("raw/")
        self.objetos[object_name] = data.read()
        assert len(self.objetos[object_name]) == length
        self.gravadas.append(object_name)


def _k(fonte, dia, arquivo):
    return f"raw/{fonte}/group_id=24269/data={dia}/{arquivo}"


def _produto(pid, nome, numero=None, raridade=None):
    ext = []
    if numero:
        ext.append({"name": "Number", "value": numero})
    if raridade:
        ext.append({"name": "Rarity", "value": raridade})
    return {"productId": pid, "groupId": 24269, "name": nome, "imageUrl": f"https://img/{pid}.jpg",
            "url": f"https://tcgplayer/{pid}", "extendedData": ext}


def _preco(pid, sub="Normal", market=1.0):
    return {"productId": pid, "subTypeName": sub, "marketPrice": market, "lowPrice": market / 2,
            "midPrice": market, "highPrice": market * 3}


def _ptax(data, venda=5.4321, boletim="Fechamento"):
    item = {"paridadeCompra": 1.0, "paridadeVenda": 1.0, "cotacaoCompra": 5.4315,
            "cotacaoVenda": venda, "dataHoraCotacao": f"{data} 13:09:27.123", "tipoBoletim": boletim}
    if venda is None:
        del item["cotacaoVenda"]
    return item


def _b(obj):
    return json.dumps(obj).encode()


def _bruto_tres_dias():
    objetos = {}
    janelas_ptax = {"2026-11-01": ["2026-10-29", "2026-10-30"],
                    "2026-11-02": ["2026-10-30"],
                    "2026-11-03": ["2026-10-30", "2026-11-03"]}
    for i, dia in enumerate(DIAS):
        nome_box = "Destined Rivals Booster Box" + (" (v2)" if i == 2 else "")
        produtos = [_produto(600001, "Carta A", "001/182", "Double Rare"), _produto(600002, nome_box)]
        objetos[_k("tcgplayer", dia, "products.json")] = _b({"totalItems": 2, "success": True, "results": produtos})
        precos = [_preco(600001, "Normal", 2.0 + i), _preco(600001, "Reverse Holofoil", 4.0), _preco(600002, "Normal", 150.0)]
        objetos[_k("tcgplayer", dia, "prices.json")] = _b({"totalItems": 3, "success": True, "results": precos})
        ptax = [_ptax(d) for d in janelas_ptax[dia]] + [_ptax(janelas_ptax[dia][0], boletim="Intermediário")]
        objetos[_k("bcb_ptax", dia, "cotacao.json")] = _b({"@odata.context": "x", "value": ptax})
        objetos[_k("bcb_cdi", dia, "cdi.json")] = _b(
            [{"data": "29/10/2026", "valor": "0.050788"}, {"data": "30/10/2026", "valor": "0.050788"}])
    # objeto de outra coleção não é lido
    objetos["raw/tcgplayer/group_id=99999/data=2026-11-03/prices.json"] = _b({"results": [_preco(1)]})
    return objetos


def _parquet(cliente, chave, tmp_path):
    caminho = tmp_path / chave.replace("/", "__")
    caminho.write_bytes(cliente.objetos[chave])
    con = duckdb.connect()
    origem = f"read_parquet('{caminho}', hive_partitioning = false)"
    tipos = [(c[0], c[1]) for c in con.execute(f"DESCRIBE SELECT * FROM {origem}").fetchall()]
    linhas = con.execute(f"SELECT * FROM {origem}").fetchall()
    nomes = [c[0] for c in tipos]
    return tipos, [dict(zip(nomes, linha)) for linha in linhas]


@pytest.fixture
def tres_dias(tmp_path, caplog):
    cliente = ClienteFalso(_bruto_tres_dias())
    bruto_antes = {k: v for k, v in cliente.objetos.items() if k.startswith("raw/")}
    with caplog.at_level(logging.INFO):
        resultado = construir_silver(cliente, BUCKET, ler_colecao())
    resultado.texto_log = caplog.text  # o log é emitido no setup do fixture
    return cliente, bruto_antes, resultado


def test_cinco_tabelas_e_quarentena_nos_caminhos_do_contrato(tres_dias):
    cliente, _, _ = tres_dias
    esperadas = {
        "silver/colecao/group_id=24269/colecao.parquet",
        "silver/produto/group_id=24269/produto.parquet",
        "silver/cambio_diario/group_id=24269/cambio.parquet",
        "silver/cdi_diario/group_id=24269/cdi.parquet",
        "silver/quarentena/group_id=24269/quarentena.parquet",
    } | {f"silver/preco_diario/group_id=24269/data={d}/preco.parquet" for d in DIAS}
    assert set(cliente.gravadas) == esperadas
    assert all(k.split("/")[2] == "group_id=24269" for k in cliente.gravadas)


def test_nomes_e_tipos_do_contrato(tres_dias, tmp_path):
    cliente, _, _ = tres_dias
    tabelas = ["colecao", "produto", "cambio_diario", "cdi_diario", "quarentena"]
    for tabela in tabelas:
        tipos, _ = _parquet(cliente, chave_silver(tabela), tmp_path)
        assert tipos == CONTRATO[tabela], tabela
    for dia in DIAS:
        tipos, _ = _parquet(cliente, chave_silver("preco_diario", dt.date.fromisoformat(dia)), tmp_path)
        assert tipos == CONTRATO["preco_diario"]
    assert [n for n, _ in CONTRATO["preco_diario"]] == [
        "data", "product_id", "group_id", "acabamento", "market_price", "low_price",
        "mid_price", "high_price", "moeda", "fonte", "chave_raw"]


def test_chave_raw_em_preco_cambio_e_cdi_aponta_para_o_bruto(tres_dias, tmp_path):
    cliente, bruto, _ = tres_dias
    for dia in DIAS:
        _, linhas = _parquet(cliente, chave_silver("preco_diario", dt.date.fromisoformat(dia)), tmp_path)
        assert len(linhas) == 3
        assert {l["chave_raw"] for l in linhas} == {_k("tcgplayer", dia, "prices.json")}
        assert all(l["data"] == dt.date.fromisoformat(dia) and l["group_id"] == 24269 for l in linhas)
    for tabela in ("cambio_diario", "cdi_diario"):
        _, linhas = _parquet(cliente, chave_silver(tabela), tmp_path)
        assert linhas and all(l["chave_raw"] in bruto for l in linhas)


def test_ptax_e_cdi_repetidos_entre_brutos_viram_uma_linha_por_data(tres_dias, tmp_path):
    cliente, _, _ = tres_dias
    _, cambio = _parquet(cliente, chave_silver("cambio_diario"), tmp_path)
    assert [l["data"] for l in cambio] == [dt.date(2026, 10, 29), dt.date(2026, 10, 30), dt.date(2026, 11, 3)]
    assert all(l["boletim"] == "Fechamento" for l in cambio)
    assert cambio[1]["chave_raw"] == _k("bcb_ptax", "2026-11-01", "cotacao.json")
    _, cdi = _parquet(cliente, chave_silver("cdi_diario"), tmp_path)
    assert [(l["data"], l["taxa_dia"]) for l in cdi] == [
        (dt.date(2026, 10, 29), 0.050788), (dt.date(2026, 10, 30), 0.050788)]


def test_produto_uma_linha_por_product_id_do_bruto_mais_recente(tres_dias, tmp_path):
    cliente, _, _ = tres_dias
    _, produtos = _parquet(cliente, chave_silver("produto"), tmp_path)
    assert [(p["product_id"], p["tipo_produto"]) for p in produtos] == [(600001, "carta"), (600002, "selado")]
    assert produtos[1]["nome"] == "Destined Rivals Booster Box (v2)"


def test_colecao_vem_da_config(tres_dias, tmp_path):
    cliente, _, _ = tres_dias
    _, colecao = _parquet(cliente, chave_silver("colecao"), tmp_path)
    assert colecao == [{"group_id": 24269, "nome": "SV10: Destined Rivals", "sigla": "DRI",
                        "data_lancamento": dt.date(2025, 5, 30), "responsavel": "Augusto"}]


def test_bruto_intacto_e_outra_colecao_ignorada(tres_dias):
    cliente, bruto, resultado = tres_dias
    assert {k: v for k, v in cliente.objetos.items() if k.startswith("raw/")} == bruto
    assert all(p.group_id == 24269 for p in resultado.preco_diario)


def test_sem_quarentena_no_cenario_limpo_e_log_com_contagens(tres_dias):
    _, _, resultado = tres_dias
    assert resultado.quarentena == []
    texto = resultado.texto_log
    assert "quarentena por tabela: preco_diario: 0, cambio_diario: 0, demais: 0" in texto
    assert ("linhas gravadas por tabela: colecao: 1, produto: 2, cambio_diario: 3, "
            "cdi_diario: 2, preco_diario: 9, quarentena: 0") in texto


def _bruto_rf07():
    dia = "2026-11-03"
    precos = [_preco(600001), {k: v for k, v in _preco(600002).items() if k != "productId"}]
    return {
        _k("tcgplayer", dia, "products.json"): _b({"results": [_produto(600001, "Carta A", "001/182")]}),
        _k("tcgplayer", dia, "prices.json"): _b({"results": precos}),
        _k("bcb_ptax", dia, "cotacao.json"): _b({"value": [
            _ptax("2026-10-30"), _ptax("2026-11-03", venda=None), _ptax("2026-11-03", boletim="Intermediário")]}),
        _k("bcb_cdi", dia, "cdi.json"): _b([{"data": "30/10/2026", "valor": "0.050788"}]),
    }


def test_cenario_rf07_quarentena_com_motivo_e_contagem_no_log(tmp_path, caplog):
    cliente = ClienteFalso(_bruto_rf07())
    with caplog.at_level(logging.INFO):
        construir_silver(cliente, BUCKET, ler_colecao())
    assert "quarentena por tabela: preco_diario: 1, cambio_diario: 1, demais: 0" in caplog.text

    _, quarentena = _parquet(cliente, chave_silver("quarentena"), tmp_path)
    assert sorted(q["tabela"] for q in quarentena) == ["cambio_diario", "preco_diario"]
    por_tabela = {q["tabela"]: q for q in quarentena}
    assert por_tabela["preco_diario"]["motivo"].startswith("product_id:")
    assert por_tabela["preco_diario"]["chave_raw"] == _k("tcgplayer", "2026-11-03", "prices.json")
    assert "cotacao_venda" in por_tabela["cambio_diario"]["motivo"]
    assert por_tabela["cambio_diario"]["chave_raw"] == _k("bcb_ptax", "2026-11-03", "cotacao.json")
    assert all(json.loads(q["conteudo"]).get("tipoBoletim") != "Intermediário" for q in quarentena)

    _, precos = _parquet(cliente, chave_silver("preco_diario", dt.date(2026, 11, 3)), tmp_path)
    assert [p["product_id"] for p in precos] == [600001]
    _, cambio = _parquet(cliente, chave_silver("cambio_diario"), tmp_path)
    assert [c["data"] for c in cambio] == [dt.date(2026, 10, 30)]


def test_ptax_divergente_entre_brutos_vai_para_a_quarentena(tmp_path):
    objetos = _bruto_rf07()
    objetos[_k("bcb_ptax", "2026-11-04", "cotacao.json")] = _b({"value": [_ptax("2026-10-30", venda=5.5)]})
    cliente = ClienteFalso(objetos)
    construir_silver(cliente, BUCKET, ler_colecao())
    _, quarentena = _parquet(cliente, chave_silver("quarentena"), tmp_path)
    divergentes = [q for q in quarentena if q["motivo"] == "valor divergente entre brutos"]
    assert len(divergentes) == 2
    _, cambio = _parquet(cliente, chave_silver("cambio_diario"), tmp_path)
    assert cambio == []


def test_bruto_ilegivel_vai_para_a_quarentena(tmp_path):
    objetos = _bruto_rf07()
    objetos[_k("bcb_cdi", "2026-11-03", "cdi.json")] = b"<html>erro</html>"
    cliente = ClienteFalso(objetos)
    resultado = construir_silver(cliente, BUCKET, ler_colecao())
    assert [q.tabela for q in resultado.quarentena if q.motivo.startswith("bruto ilegível")] == ["cdi_diario"]


def test_escrita_passa_pela_guarda_de_prefixo(monkeypatch):
    monkeypatch.setattr(construtor, "chave_silver", lambda tabela, data=None: f"raw/x/group_id=24269/{tabela}")
    cliente = ClienteFalso(_bruto_rf07())
    with pytest.raises(PrefixoProibidoError):
        construir_silver(cliente, BUCKET, ler_colecao())
    assert cliente.gravadas == []
