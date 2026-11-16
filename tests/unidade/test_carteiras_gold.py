"""Testes de unidade das carteiras no construtor da gold (T-44; RF-23 a RF-26).

DuckDB em memória; rede bloqueada (conftest). Tabelas da gold montadas à mão,
com os mesmos dados do teste de integração `tests/integracao/test_gold_turma.py`:

    PTAX (boletim de sex 09/10/2026): compra 4,90, venda 5,00 → aplicada em
    sáb 10/10 e dom 11/10; CDI 0 no fim de semana (cdi constante em 1000).
    booster box 624679: US$ 150 (10/10), US$ 160 (11/10)
    IR 10: US$ 8 nos dois dias;  SIR 11: US$ 19 em 10/10, sem preço em 11/10

    Composição (PTAX de venda 5,00):
    selado       1 box (750)              caixa 250
    cesta_raras  1 SIR (95) + 2 IR (80)   caixa 825
    propria      nenhum selado ≤ R$ 500 (box = 750); 2 IR (80)   caixa 920
    dolar        1000 / 5 = 200 USD;  cdi  1000

    Dia 11/10, compra 4,90, taxa 0,15:
    selado       160 × 0,85 × 4,9 = 666,4 + 250 = 916,4       → retorno −0,0836
    cesta_raras  19 × 0,85 × 4,9 = 79,135 (carregado)
                 + 2 × 8 × 0,85 × 4,9 = 66,64 + 825 = 970,775 → retorno −0,029225
    propria      66,64 + 920 = 986,64                         → retorno −0,01336
    dolar        200 × 4,9 = 980 (taxa 0)                     → retorno −0,02
    cdi          1000 (taxa 0)                                → retorno 0
"""

import datetime as dt

import duckdb
import pytest

from tcg.gold import construtor
from tcg.gold.construtor import (
    CHAVE_GOLD_TURMA,
    TABELA_GOLD_TURMA,
    calcular_carteiras,
    regra_propria_aceita,
)
from tcg.lake.duckdb import gravar_parquet
from tcg.lake.guarda_prefixo import PrefixoProibidoError

GID = 24269
D1, D2 = dt.date(2026, 10, 10), dt.date(2026, 10, 11)
BOX, IR, SIR = 624679, 10, 11
CONTRATO = [
    ("data", "DATE"),
    ("group_id", "INTEGER"),
    ("carteira", "VARCHAR"),
    ("valor_brl", "DOUBLE"),
    ("retorno_acumulado", "DOUBLE"),
    ("taxa_venda", "DOUBLE"),
]


@pytest.fixture
def con():
    c = duckdb.connect()
    c.execute(
        "CREATE TABLE fato_preco_diario (group_id INTEGER, product_id INTEGER, acabamento VARCHAR, "
        "data DATE, market_price DOUBLE)"
    )
    c.executemany("INSERT INTO fato_preco_diario VALUES (?, ?, ?, ?, ?)", [
        (GID, BOX, "Normal", D1, 150.0), (GID, BOX, "Normal", D2, 160.0),
        (GID, IR, "Holofoil", D1, 8.0), (GID, IR, "Holofoil", D2, 8.0),
        (GID, SIR, "Holofoil", D1, 19.0),
        (99999, BOX, "Normal", D1, 999.0),  # outra coleção na gold: ignorada
    ])
    c.execute(
        "CREATE TABLE dim_produto (group_id INTEGER, product_id INTEGER, nome VARCHAR, "
        "tipo_produto VARCHAR, raridade VARCHAR)"
    )
    c.executemany("INSERT INTO dim_produto VALUES (?, ?, ?, ?, ?)", [
        (GID, BOX, "Destined Rivals Booster Box", "selado", None),
        (GID, IR, "Carta IR", "carta", "Illustration Rare"),
        (GID, SIR, "Carta SIR", "carta", "Special Illustration Rare"),
        (99999, BOX, "Outra Booster Box", "selado", None),
    ])
    c.execute(
        "CREATE TABLE fato_cambio_diario (data DATE, cotacao_compra DOUBLE, cotacao_venda DOUBLE, "
        "cdi_taxa_dia DOUBLE, cdi_pendente BOOLEAN)"
    )
    c.executemany("INSERT INTO fato_cambio_diario VALUES (?, ?, ?, ?, ?)", [
        (D1, 4.90, 5.00, 0.0, False), (D2, 4.90, 5.00, 0.0, False),
    ])
    yield c
    c.close()


def _calcular(con, regra_propria=True):
    return calcular_carteiras(
        con, "fato_preco_diario", "dim_produto", "fato_cambio_diario", 0.15, regra_propria
    )


def test_regra_propria_aceita_pelo_status_do_adr(tmp_path):
    adr = tmp_path / "ADR-005.md"
    adr.write_text("# ADR-005\n\n## Status\n\nAceito em 2026-11-16.\n", encoding="utf-8")
    assert regra_propria_aceita(adr) is True
    adr.write_text("# ADR-005\n\n## Status\n\nProposto.\n", encoding="utf-8")
    assert regra_propria_aceita(adr) is False
    adr.write_text("# ADR-005\n\nAceito, mas sem seção de status.\n", encoding="utf-8")
    assert regra_propria_aceita(adr) is False
    assert regra_propria_aceita(tmp_path / "ausente.md") is False
    # o ADR-005 commitado no repositório está aceito: a propria é calculada
    assert regra_propria_aceita() is True


def test_gold_turma_no_contrato_uma_linha_por_dia_e_carteira(con):
    linhas = _calcular(con)
    esquema = [(n, t) for n, t, *_ in con.execute(f"DESCRIBE {TABELA_GOLD_TURMA}").fetchall()]
    assert esquema == CONTRATO
    # 2 dias × 5 carteiras = 10 linhas, sem repetição de (data, carteira)
    assert linhas[TABELA_GOLD_TURMA] == 10
    assert con.execute(
        f"SELECT count(DISTINCT (data, carteira)) FROM {TABELA_GOLD_TURMA}"
    ).fetchone()[0] == 10
    assert con.execute(f"SELECT DISTINCT group_id FROM {TABELA_GOLD_TURMA}").fetchall() == [(GID,)]
    # liquidação da gold da DRI tem as duas taxas: 2 dias × 5 carteiras × 2 taxas = 20
    assert linhas["liquidacao_carteira"] == 20
    assert linhas["metricas_carteira"] == 10


def test_gold_turma_valores_retorno_e_taxa(con):
    _calcular(con)
    d2 = dict(
        (c, (v, r, t))
        for c, v, r, t in con.execute(
            f"SELECT carteira, valor_brl, retorno_acumulado, taxa_venda FROM {TABELA_GOLD_TURMA} "
            "WHERE data = ?", [D2]
        ).fetchall()
    )
    esperado = {  # contas no docstring do módulo
        "selado": (916.4, -0.0836, 0.15),
        "cesta_raras": (970.775, -0.029225, 0.15),
        "propria": (986.64, -0.01336, 0.15),
        "dolar": (980.0, -0.02, 0.0),
        "cdi": (1000.0, 0.0, 0.0),
    }
    assert set(d2) == set(esperado)
    for carteira, (valor, retorno, taxa) in esperado.items():
        assert d2[carteira][0] == pytest.approx(valor), carteira
        assert d2[carteira][1] == pytest.approx(retorno, abs=1e-12), carteira
        assert d2[carteira][2] == taxa, carteira
    # retorno_acumulado = valor_brl / 1000 − 1 em todas as linhas
    assert con.execute(
        f"SELECT max(abs(retorno_acumulado - (valor_brl / 1000 - 1))) FROM {TABELA_GOLD_TURMA}"
    ).fetchone()[0] == pytest.approx(0.0, abs=1e-12)


def test_metricas_e_liquidacao_com_taxa_zero_na_gold_da_dri(con):
    _calcular(con)
    # selado com taxa 0 no dia 11/10: 160 × 4,9 = 784 + 250 = 1034 → retorno 0,034
    assert con.execute(
        "SELECT retorno_acumulado FROM metricas_carteira WHERE carteira = 'selado' AND taxa_venda = 0"
    ).fetchone()[0] == pytest.approx(0.034)
    # cesta_raras: SIR sem preço em 11/10 → 1 dia com preço carregado
    assert con.execute(
        "SELECT dias_preco_carregado FROM metricas_carteira "
        "WHERE carteira = 'cesta_raras' AND taxa_venda = 0.15"
    ).fetchone()[0] == 1


def test_propria_pendente_sai_com_valores_nulos(con):
    linhas = _calcular(con, regra_propria=False)
    assert linhas[TABELA_GOLD_TURMA] == 10
    propria = con.execute(
        f"SELECT valor_brl, retorno_acumulado FROM {TABELA_GOLD_TURMA} WHERE carteira = 'propria'"
    ).fetchall()
    assert propria == [(None, None), (None, None)]
    assert con.execute(
        f"SELECT count(*) FROM {TABELA_GOLD_TURMA} WHERE carteira <> 'propria' AND valor_brl IS NULL"
    ).fetchone()[0] == 0


class _ConexaoFalsa:
    def __init__(self):
        self.consultas = []

    def execute(self, sql, *args):
        self.consultas.append(sql)


def test_guarda_de_prefixo_recusa_destino_fora_do_permitido():
    falsa = _ConexaoFalsa()
    for chave in (
        "gold_turma/carteira/group_id=99999/carteira.parquet",
        "gold_turma/outra/group_id=24269/carteira.parquet",
        "raw/tcgplayer/group_id=24269/carteira.parquet",
    ):
        with pytest.raises(PrefixoProibidoError):
            gravar_parquet(falsa, "tcg", f"SELECT * FROM {TABELA_GOLD_TURMA}", chave)
    assert falsa.consultas == [], "nenhum COPY antes da recusa"
    assert CHAVE_GOLD_TURMA == "gold_turma/carteira/group_id=24269/carteira.parquet"
    assert all(
        c.startswith("gold/group_id=24269/")
        for c in (construtor.chave_gold(t) for t in construtor.TABELAS_CARTEIRA)
    )
