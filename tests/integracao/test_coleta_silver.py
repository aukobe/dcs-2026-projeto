"""Integração coleta → silver com os cassetes da T-20, sem rede (T-28; RNF-06).

Fluxo: o coletor (T-06) roda com o cassete `cassetes/coleta_2026-11-03.yaml`
(vcrpy em `record_mode="none"`) e grava os quatro brutos reais de 2026-11-03;
os bytes gravados vão a um bucket em memória e o Construtor da silver (T-27)
monta e grava as tabelas. O teste de contrato confere caminhos, nomes e tipos
de coluna, `chave_raw` e as contagens do bruto real registradas no T-13
(`docs/evidencias/T-13_hipoteses.md`).

Sem contêiner (a tarefa não tem a marca [contêiner]): o bucket é um cliente
falso em memória. `socket.socket` e `socket.getaddrinfo` ficam bloqueados no
módulo inteiro e cada tentativa é contada; ao final, o contador tem de ser 0.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import socket

import duckdb
import pytest
import vcr

from tcg.coleta import __main__ as coleta
from tcg.config import ler_colecao
from tcg.silver.construtor import CONTRATO, chave_silver, construir_silver

PASTA_CASSETES = Path(__file__).parent / "cassetes"
CASSETE = PASTA_CASSETES / "coleta_2026-11-03.yaml"
MANIFESTO = PASTA_CASSETES / "coleta_2026-11-03.hashes.json"
AGORA = dt.datetime(2026, 11, 3, 20, 30, tzinfo=dt.UTC)
DIA = dt.date(2026, 11, 3)
BUCKET = "tcg"

PRICES = "raw/tcgplayer/group_id=24269/data=2026-11-03/prices.json"
PTAX = "raw/bcb_ptax/group_id=24269/data=2026-11-03/cotacao.json"
CDI = "raw/bcb_cdi/group_id=24269/data=2026-11-03/cdi.json"

TENTATIVAS_DE_REDE: list[str] = []


class RedeBloqueadaError(RuntimeError):
    """Tentativa de acesso à rede no teste coleta → silver."""


class _SocketBloqueado:
    def __init__(self, *args, **kwargs):
        TENTATIVAS_DE_REDE.append(f"socket {args!r}")
        raise RedeBloqueadaError(f"rede bloqueada no teste coleta → silver: socket {args!r}")


def _getaddrinfo_bloqueado(host, *args, **kwargs):
    TENTATIVAS_DE_REDE.append(f"DNS {host!r}")
    raise RedeBloqueadaError(f"rede bloqueada no teste coleta → silver: DNS {host!r}")


@pytest.fixture(scope="module", autouse=True)
def sem_rede():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(socket, "socket", _SocketBloqueado)
        mp.setattr(socket, "getaddrinfo", _getaddrinfo_bloqueado)
        yield


# ---------------------------------------------------------------- bucket em memória


class _Objeto:
    def __init__(self, nome):
        self.object_name = nome


class _Resposta(io.BytesIO):
    def release_conn(self):
        pass


class BucketEmMemoria:
    """Imita list_objects, get_object e put_object do SDK; sem exclusão."""

    def __init__(self, objetos: dict[str, bytes]):
        self.objetos = dict(objetos)
        self.gravadas: list[str] = []

    def list_objects(self, bucket_name, prefix="", recursive=False):
        assert bucket_name == BUCKET and recursive
        return [_Objeto(k) for k in sorted(self.objetos) if k.startswith(prefix)]

    def get_object(self, bucket_name, object_name):
        assert bucket_name == BUCKET
        return _Resposta(self.objetos[object_name])

    def put_object(self, bucket_name, object_name, data, length, content_type):
        assert bucket_name == BUCKET
        self.objetos[object_name] = data.read()
        assert len(self.objetos[object_name]) == length
        self.gravadas.append(object_name)


def _sha256(corpo: bytes) -> str:
    return hashlib.sha256(corpo).hexdigest()


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory):
    """Coleta com o cassete e silver construída a partir do bruto gravado."""
    manifesto = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    pasta = tmp_path_factory.mktemp("dados_raw")
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("TCG_USER_AGENT", "colecao-dri/teste")
        with vcr.VCR(record_mode="none").use_cassette(str(CASSETE), allow_playback_repeats=False) as cassete:
            codigo = coleta.executar(pasta, agora=AGORA)

    bruto = {p.relative_to(pasta).as_posix(): p.read_bytes() for p in pasta.rglob("*") if p.is_file()}
    bucket = BucketEmMemoria(bruto)
    resultado = construir_silver(bucket, BUCKET, ler_colecao())
    return {
        "codigo": codigo, "cassete": cassete, "manifesto": manifesto, "bruto": bruto,
        "bucket": bucket, "resultado": resultado, "tmp": tmp_path_factory.mktemp("parquet"),
    }


def _parquet(p, chave):
    caminho = p["tmp"] / chave.replace("/", "__")
    caminho.write_bytes(p["bucket"].objetos[chave])
    with duckdb.connect() as con:
        origem = f"read_parquet('{caminho}', hive_partitioning = false)"
        tipos = [(c[0], c[1]) for c in con.execute(f"DESCRIBE SELECT * FROM {origem}").fetchall()]
        linhas = con.execute(f"SELECT * FROM {origem}").fetchall()
    nomes = [n for n, _ in tipos]
    return tipos, [dict(zip(nomes, linha)) for linha in linhas]


# ---------------------------------------------------------------- testes


def test_coleta_com_cassete_grava_o_bruto_real(pipeline):
    assert pipeline["codigo"] == coleta.SUCESSO
    assert pipeline["cassete"].all_played and pipeline["cassete"].play_count == 4
    assert sorted(pipeline["bruto"]) == sorted(pipeline["manifesto"])
    for chave, esperado in pipeline["manifesto"].items():
        assert _sha256(pipeline["bruto"][chave]) == esperado["sha256"], chave


def test_silver_nos_caminhos_e_no_prefixo_do_contrato(pipeline):
    esperadas = {chave_silver(t) for t in ("colecao", "produto", "cambio_diario", "cdi_diario", "quarentena")}
    esperadas.add(chave_silver("preco_diario", DIA))
    assert set(pipeline["bucket"].gravadas) == esperadas
    assert all(k.startswith("silver/") and k.split("/")[2] == "group_id=24269" for k in pipeline["bucket"].gravadas)


def test_contrato_de_nomes_e_tipos(pipeline):
    for tabela in ("colecao", "produto", "cambio_diario", "cdi_diario", "quarentena"):
        tipos, _ = _parquet(pipeline, chave_silver(tabela))
        assert tipos == CONTRATO[tabela], tabela
    tipos, _ = _parquet(pipeline, chave_silver("preco_diario", DIA))
    assert tipos == CONTRATO["preco_diario"]


def test_chave_raw_aponta_para_o_bruto_coletado(pipeline):
    esperado = {"preco_diario": PRICES, "cambio_diario": PTAX, "cdi_diario": CDI}
    for tabela, chave_bruto in esperado.items():
        chave = chave_silver("preco_diario", DIA) if tabela == "preco_diario" else chave_silver(tabela)
        _, linhas = _parquet(pipeline, chave)
        assert linhas, tabela
        assert {l["chave_raw"] for l in linhas} == {chave_bruto}, tabela
        assert chave_bruto in pipeline["bucket"].objetos


def test_contagens_iguais_as_do_t13(pipeline):
    _, produtos = _parquet(pipeline, chave_silver("produto"))
    assert len(produtos) == 281
    tipos = [p["tipo_produto"] for p in produtos]
    assert (tipos.count("selado"), tipos.count("carta")) == (25, 256)
    assert sum(p["raridade"] == "Code Card" for p in produtos) == 12
    assert all(p["image_url"] and p["url"] for p in produtos)

    _, precos = _parquet(pipeline, chave_silver("preco_diario", DIA))
    assert len(precos) == 446
    assert all(p["data"] == DIA and p["group_id"] == 24269 for p in precos)
    nulos = [(p["product_id"], p["acabamento"]) for p in precos if p["market_price"] is None]
    assert nulos == [(637654, "Normal")]  # RF-08: linha existe, preço nulo

    _, cambio = _parquet(pipeline, chave_silver("cambio_diario"))
    assert [c["data"].isoformat() for c in cambio] == [
        "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30", "2026-11-03"]
    assert all(c["boletim"] == "Fechamento" for c in cambio)
    assert (cambio[-1]["cotacao_compra"], cambio[-1]["cotacao_venda"]) == (5.4929, 5.4935)

    _, cdi = _parquet(pipeline, chave_silver("cdi_diario"))
    assert [(c["data"].isoformat(), c["taxa_dia"]) for c in cdi] == [
        (d, 0.050788) for d in ("2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30")]

    _, quarentena = _parquet(pipeline, chave_silver("quarentena"))
    assert quarentena == []


def test_bruto_intacto_depois_da_silver(pipeline):
    bruto_no_bucket = {k: v for k, v in pipeline["bucket"].objetos.items() if k.startswith("raw/")}
    assert bruto_no_bucket == pipeline["bruto"]
    for chave, esperado in pipeline["manifesto"].items():
        assert _sha256(bruto_no_bucket[chave]) == esperado["sha256"], chave


def test_nenhuma_requisicao_saiu_para_a_rede(pipeline):
    assert TENTATIVAS_DE_REDE == []
    with pytest.raises(RedeBloqueadaError):
        socket.create_connection(("tcgcsv.com", 443), timeout=1)
    assert TENTATIVAS_DE_REDE == ["DNS 'tcgcsv.com'"]
