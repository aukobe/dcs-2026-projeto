"""gold_turma e carteiras contra MinIO descartável (T-44; RF-26; ADR-004, ADR-008) [contêiner].

Reaproveita o fixture `minio_descartavel` da T-19 e os auxiliares da T-32
(mesma imagem do compose, porta aleatória, credenciais geradas na hora; o
`.env` não é lido e o MinIO local de trabalho não é tocado).

Bucket `tcg-gold-turma`: silver da DRI gravada pela Guarda de prefixo e uma
gold_turma de terceiro (`group_id=99999`), gravada com `put_object` direto, só
neste teste. Roda `construir_gold` e `construir_carteiras` duas vezes.

Dados (contas conferidas no plano da T-44 e em tests/unidade/test_carteiras_gold.py):
PTAX de sex 09/10/2026 (compra 4,90, venda 5,00) aplicada em sáb 10/10 e dom
11/10; CDI 0 no fim de semana. Booster box 624679 a US$ 150 e US$ 160; IR 10 a
US$ 8 nos dois dias; SIR 11 a US$ 19 só em 10/10. Dia 11/10 com taxa 0,15:
selado 916,4; cesta_raras 970,775; propria 986,64; dolar 980 (taxa 0);
cdi 1000 (taxa 0).
"""

from __future__ import annotations

import datetime as dt
import io
from pathlib import Path

import duckdb
import pytest

from tcg.gold.construtor import (
    CHAVE_GOLD_TURMA,
    TABELAS_CARTEIRA,
    chave_gold,
    construir_carteiras,
    construir_gold,
    regra_propria_aceita,
)
from tcg.gold.sql import TABELAS
from tcg.lake.cliente import garantir_bucket
from tcg.lake.duckdb import caminho_s3, conectar
from tcg.lake.guarda_prefixo import chave_permitida, gravar

from test_construtor_gold import DDL, _config, _hashes, _parquet, _preco
from test_minio import minio_descartavel  # noqa: F401  (fixture da T-19)

DRI = 24269
TERCEIRO = 99999
D = dt.date
D1, D2 = D(2026, 10, 10), D(2026, 10, 11)
BOX, IR, SIR = 624679, 10, 11
BUCKET = "tcg-gold-turma"
CHAVE_TERCEIRO = f"gold_turma/carteira/group_id={TERCEIRO}/carteira.parquet"
CONTRATO = [
    ("data", "DATE"),
    ("group_id", "INTEGER"),
    ("carteira", "VARCHAR"),
    ("valor_brl", "DOUBLE"),
    ("retorno_acumulado", "DOUBLE"),
    ("taxa_venda", "DOUBLE"),
]
DDL_GOLD_TURMA = ", ".join(f"{n} {t}" for n, t in CONTRATO)


def _gravar_silver_dri(cliente, tmp: Path) -> None:
    base = f"silver/{{}}/group_id={DRI}"
    objetos = {
        f"{base.format('colecao')}/colecao.parquet": _parquet(
            tmp, DDL["colecao"], [(DRI, "Destined Rivals", "DRI", D(2025, 5, 30), "autor")]),
        f"{base.format('produto')}/produto.parquet": _parquet(tmp, DDL["produto"], [
            (BOX, DRI, "Destined Rivals Booster Box", "selado", None, None, None, None),
            (IR, DRI, "Carta IR", "carta", "Illustration Rare", "200/182", None, None),
            (SIR, DRI, "Carta SIR", "carta", "Special Illustration Rare", "230/182", None, None),
        ]),
        f"{base.format('cambio_diario')}/cambio.parquet": _parquet(tmp, DDL["cambio_diario"], [
            (D(2026, 10, 9), 4.90, 5.00, dt.datetime(2026, 10, 9, 13, 5), "Fechamento", "raw/bcb_ptax/a")]),
        f"{base.format('cdi_diario')}/cdi.parquet": _parquet(
            tmp, DDL["cdi_diario"], [(D(2026, 10, 9), 0.055131, "raw/bcb_cdi/a")]),
    }
    precos = {
        D1: [_preco(D1, BOX, DRI, "Normal", 150.0), _preco(D1, IR, DRI, "Holofoil", 8.0),
             _preco(D1, SIR, DRI, "Holofoil", 19.0)],
        D2: [_preco(D2, BOX, DRI, "Normal", 160.0), _preco(D2, IR, DRI, "Holofoil", 8.0)],
    }
    for data, linhas in precos.items():
        objetos[f"{base.format('preco_diario')}/data={data}/preco.parquet"] = _parquet(
            tmp, DDL["preco_diario"], linhas)
    for chave, dados in objetos.items():
        gravar(cliente, BUCKET, chave, dados, content_type="application/vnd.apache.parquet")


def _gravar_gold_turma_terceiro(cliente, tmp: Path) -> None:
    """gold_turma de outra coleção, como um terceiro a publicaria (só neste teste)."""
    dados = _parquet(tmp, DDL_GOLD_TURMA, [(D1, TERCEIRO, "selado", 1100.0, 0.1, 0.15)])
    cliente.put_object(BUCKET, CHAVE_TERCEIRO, io.BytesIO(dados), len(dados))


def _executar(minio):
    con = conectar(_config(minio, BUCKET))
    try:
        construir_gold(minio["cliente"], con, BUCKET)
        return construir_carteiras(con, BUCKET, 0.15, regra_propria_aceita())
    finally:
        con.close()


def _ler(minio, chave: str, consulta: str):
    con = conectar(_config(minio, BUCKET))
    try:
        origem = f"read_parquet('{caminho_s3(BUCKET, chave)}', hive_partitioning = false)"
        return con.execute(consulta.format(t=origem)).fetchall()
    finally:
        con.close()


CONSULTA_TUDO = "SELECT * FROM {t} ORDER BY data, carteira"


@pytest.fixture(scope="module")
def duas_execucoes(minio_descartavel, tmp_path_factory):  # noqa: F811
    cliente = minio_descartavel["cliente"]
    garantir_bucket(cliente, BUCKET)
    tmp = tmp_path_factory.mktemp("gold_turma")
    _gravar_silver_dri(cliente, tmp)
    _gravar_gold_turma_terceiro(cliente, tmp)
    antes = _hashes(cliente, BUCKET)
    r1 = _executar(minio_descartavel)
    depois1 = _hashes(cliente, BUCKET)
    conteudo1 = _ler(minio_descartavel, CHAVE_GOLD_TURMA, CONSULTA_TUDO)
    r2 = _executar(minio_descartavel)
    depois2 = _hashes(cliente, BUCKET)
    conteudo2 = _ler(minio_descartavel, CHAVE_GOLD_TURMA, CONSULTA_TUDO)
    return {
        "antes": antes, "depois1": depois1, "depois2": depois2,
        "r1": r1, "r2": r2, "conteudo1": conteudo1, "conteudo2": conteudo2,
    }


def test_so_chaves_permitidas_da_dri_e_terceiro_intocado(duas_execucoes):
    antes, depois = duas_execucoes["antes"], duas_execucoes["depois1"]
    novas = sorted(set(depois) - set(antes))
    esperadas = sorted(
        [chave_gold(t) for t in TABELAS] + [chave_gold(t) for t in TABELAS_CARTEIRA] + [CHAVE_GOLD_TURMA]
    )
    assert novas == esperadas
    assert all(chave_permitida(c) for c in novas)
    assert all(c.startswith(("gold/group_id=24269/", "gold_turma/carteira/group_id=24269/")) for c in novas)
    # nada que já existia mudou: silver da DRI e gold_turma do terceiro com o mesmo hash
    assert {c: depois[c] for c in antes} == antes
    assert depois[CHAVE_TERCEIRO] == antes[CHAVE_TERCEIRO]
    assert duas_execucoes["r1"].chaves == [chave_gold(t) for t in TABELAS_CARTEIRA] + [CHAVE_GOLD_TURMA]


def test_contrato_de_colunas_e_tipos(duas_execucoes, minio_descartavel):  # noqa: F811
    esquema = _ler(minio_descartavel, CHAVE_GOLD_TURMA, "DESCRIBE SELECT * FROM {t}")
    assert [(n, t) for n, t, *_ in esquema] == CONTRATO


def test_uma_linha_por_dia_e_carteira_com_valores(duas_execucoes):
    linhas = duas_execucoes["conteudo1"]
    # 2 dias × 5 carteiras = 10 linhas, cada (data, carteira) uma vez
    assert len(linhas) == 10
    assert len({(l[0], l[2]) for l in linhas}) == 10
    assert {l[1] for l in linhas} == {DRI}
    d2 = {l[2]: l for l in linhas if l[0] == D2}
    esperado = {  # valor_brl, retorno = valor / 1000 − 1, taxa_venda
        "selado": (916.4, -0.0836, 0.15),
        "cesta_raras": (970.775, -0.029225, 0.15),
        "propria": (986.64, -0.01336, 0.15),
        "dolar": (980.0, -0.02, 0.0),
        "cdi": (1000.0, 0.0, 0.0),
    }
    for carteira, (valor, retorno, taxa) in esperado.items():
        _, _, _, v, r, t = d2[carteira]
        assert v == pytest.approx(valor), carteira
        assert r == pytest.approx(retorno, abs=1e-12), carteira
        assert t == taxa, carteira
    assert all(l[4] == pytest.approx(l[3] / 1000 - 1, abs=1e-12) for l in linhas)


def test_gold_da_dri_tem_as_duas_taxas_para_o_painel(duas_execucoes, minio_descartavel):  # noqa: F811
    taxas = _ler(minio_descartavel, chave_gold("liquidacao_carteira"),
                 "SELECT taxa_venda, count(*) FROM {t} GROUP BY 1 ORDER BY 1")
    assert taxas == [(0.0, 10), (0.15, 10)]
    metricas = _ler(minio_descartavel, chave_gold("metricas_carteira"),
                    "SELECT count(*), count(DISTINCT (carteira, taxa_venda)) FROM {t}")
    assert metricas == [(10, 10)]


def test_regravar_e_idempotente(duas_execucoes):
    d1, d2 = duas_execucoes["depois1"], duas_execucoes["depois2"]
    assert set(d2) == set(d1), "a segunda execução não cria nem remove chaves"
    assert duas_execucoes["conteudo2"] == duas_execucoes["conteudo1"]
    assert d2[CHAVE_TERCEIRO] == duas_execucoes["antes"][CHAVE_TERCEIRO]
    assert duas_execucoes["r2"].linhas == duas_execucoes["r1"].linhas
