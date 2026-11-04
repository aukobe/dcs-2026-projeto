"""Guarda de prefixo (T-23; RNF-03, RF-13, ADR-004), com cliente falso."""

from __future__ import annotations

from pathlib import Path

import pytest

from tcg.lake import guarda_prefixo
from tcg.lake.guarda_prefixo import PrefixoProibidoError, apagar, chave_permitida, gravar

BUCKET = "tcg"
RAIZ_SRC = Path(__file__).resolve().parents[2] / "src"


class ClienteFalso:
    """Registra toda chamada ao SDK; nenhuma rede."""

    def __init__(self):
        self.chamadas: list[tuple[str, str, bytes | None]] = []

    def put_object(self, bucket_name, object_name, data, length, content_type="application/octet-stream"):
        corpo = data.read()
        assert len(corpo) == length
        self.chamadas.append(("put_object", object_name, corpo))

    def remove_object(self, bucket_name, object_name):
        self.chamadas.append(("remove_object", object_name, None))


ACEITAS = [
    "silver/preco_diario/group_id=24269/data=2026-11-03/preco.parquet",
    "silver/quarentena/group_id=24269/quarentena.parquet",
    "silver/produto/group_id=24269/produto.parquet",
    "gold/group_id=24269/fato_preco_diario/parte.parquet",
    "gold/group_id=24269/dim_data.parquet",
    "gold_turma/carteira/group_id=24269/carteira.parquet",
]

RECUSADAS = [
    "raw/tcgplayer/group_id=24269/data=2026-11-03/prices.json",
    "raw/bcb_ptax/group_id=24269/data=2026-11-03/cotacao.json",
    "silver/preco_diario/group_id=99999/preco.parquet",
    "silver/preco_diario/group_id=242690/preco.parquet",
    "gold/group_id=24269x/fato.parquet",
    "gold/group_id=99999/fato.parquet",
    "gold_turma/carteira/group_id=99999/carteira.parquet",
    "gold_turma/outra/group_id=24269/carteira.parquet",
    "silver/preco_diario/group_id=24269/../../../raw/tcgplayer/group_id=24269/x.json",
    "gold/group_id=24269/../group_id=99999/fato.parquet",
    "silver/./group_id=24269/x.parquet",
    "silver/preco_diario/group_id=24269//x.parquet",
    "/silver/preco_diario/group_id=24269/x.parquet",
    "tcg/silver/preco_diario/group_id=24269/x.parquet",
    "silver\\preco_diario\\group_id=24269\\x.parquet",
    "silver/Preco/group_id=24269/x.parquet",
    "silver/preco_diario/group_id=24269/",
    "silver/preco_diario/group_id=24269",
    "gold/group_id=24269",
    "gold_turma/carteira/group_id=24269",
    "",
]


@pytest.mark.parametrize("chave", ACEITAS)
def test_escrita_aceita_nos_tres_prefixos(chave):
    cliente = ClienteFalso()
    gravar(cliente, BUCKET, chave, b"conteudo")
    assert cliente.chamadas == [("put_object", chave, b"conteudo")]


@pytest.mark.parametrize("chave", ACEITAS)
def test_exclusao_aceita_nos_tres_prefixos(chave, caplog):
    cliente = ClienteFalso()
    with caplog.at_level("INFO"):
        assert apagar(cliente, BUCKET, [chave]) == [chave]
    assert cliente.chamadas == [("remove_object", chave, None)]
    assert f"objeto apagado: {BUCKET}/{chave}" in caplog.text


@pytest.mark.parametrize("chave", RECUSADAS)
def test_escrita_recusada_antes_do_sdk(chave):
    cliente = ClienteFalso()
    with pytest.raises(PrefixoProibidoError):
        gravar(cliente, BUCKET, chave, b"x")
    assert cliente.chamadas == []


@pytest.mark.parametrize("chave", RECUSADAS)
def test_exclusao_recusada_antes_do_sdk(chave, caplog):
    cliente = ClienteFalso()
    with pytest.raises(PrefixoProibidoError):
        apagar(cliente, BUCKET, [chave])
    assert cliente.chamadas == []
    assert "chave recusada pela Guarda de prefixo" in caplog.text


def test_lote_com_uma_chave_proibida_nao_apaga_nada():
    cliente = ClienteFalso()
    lote = [ACEITAS[0], ACEITAS[3], "raw/tcgplayer/group_id=24269/data=2026-11-03/prices.json"]
    with pytest.raises(PrefixoProibidoError):
        apagar(cliente, BUCKET, lote)
    assert cliente.chamadas == []


def test_chave_permitida_coerente_com_as_listas():
    assert all(chave_permitida(c) for c in ACEITAS)
    assert not any(chave_permitida(c) for c in RECUSADAS)


def test_group_id_fixo_da_dri():
    assert guarda_prefixo.GROUP_ID_DRI == 24269


def test_exclusao_so_existe_na_guarda_de_prefixo():
    """Ponto único de exclusão: nenhum outro módulo de src/ chama o SDK para apagar."""
    termos = ("remove_object", "remove_bucket", "delete_object")
    ofensores = [
        str(caminho.relative_to(RAIZ_SRC))
        for caminho in RAIZ_SRC.rglob("*.py")
        if caminho.name != "guarda_prefixo.py"
        and any(t in caminho.read_text(encoding="utf-8") for t in termos)
    ]
    assert ofensores == []
