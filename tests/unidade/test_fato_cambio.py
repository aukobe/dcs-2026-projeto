"""Testes do `fato_cambio_diario` (T-31; RF-12, RNF-01; ADR-003).

DuckDB local em memória, Parquets em `tmp_path` no layout do contrato e rede
bloqueada (conftest). Preços da DRI de 08/10 a 13/10/2026, o que define o
calendário de `dim_data`. PTAX: 09/10 (sexta; compra 4,9990, venda 5,0000) e
13/10 (terça; compra 5,4990, venda 5,5000); 10/10 e 11/10 são fim de semana e
12/10 é feriado, sem boletim. CDI em 09/10 e, no cenário padrão, em 13/10.
"""

import datetime as dt
from pathlib import Path

import duckdb
import pytest

from tcg.gold.sql import montar_estrela

DRI = 24269
D = dt.date
CDI_0910 = 0.055131
CDI_1310 = 0.055200

DDL_COLECAO = "group_id INTEGER, nome VARCHAR, sigla VARCHAR, data_lancamento DATE, responsavel VARCHAR"
DDL_PRODUTO = (
    "product_id INTEGER, group_id INTEGER, nome VARCHAR, tipo_produto VARCHAR, raridade VARCHAR, "
    "numero VARCHAR, image_url VARCHAR, url VARCHAR"
)
DDL_PRECO = (
    "data DATE, product_id INTEGER, group_id INTEGER, acabamento VARCHAR, market_price DOUBLE, "
    "low_price DOUBLE, mid_price DOUBLE, high_price DOUBLE, moeda VARCHAR, fonte VARCHAR, chave_raw VARCHAR"
)
DDL_CAMBIO = (
    "data DATE, cotacao_compra DOUBLE, cotacao_venda DOUBLE, data_hora_cotacao TIMESTAMP, "
    "boletim VARCHAR, chave_raw VARCHAR"
)
DDL_CDI = "data DATE, taxa_dia DOUBLE, chave_raw VARCHAR"


def _gravar(con, pasta: Path, nome: str, ddl: str, linhas: list[tuple]) -> None:
    """Cria uma tabela temporária com os tipos do contrato e exporta para Parquet."""
    pasta.mkdir(parents=True, exist_ok=True)
    con.execute(f"CREATE OR REPLACE TEMP TABLE t ({ddl})")
    if linhas:
        marcadores = ", ".join("?" * len(linhas[0]))
        con.executemany(f"INSERT INTO t VALUES ({marcadores})", linhas)
    con.execute(f"COPY t TO '{pasta / nome}' (FORMAT parquet)")


def _montar(base: Path, cdi_1310: bool) -> duckdb.DuckDBPyConnection:
    """Grava a silver da DRI sob `base` e devolve a conexão com a estrela montada."""
    con = duckdb.connect()
    s = base / "silver"
    _gravar(con, s / "colecao" / f"group_id={DRI}", "colecao.parquet", DDL_COLECAO,
            [(DRI, "Destined Rivals", "DRI", D(2025, 5, 30), "teste")])
    _gravar(con, s / "produto" / f"group_id={DRI}", "produto.parquet", DDL_PRODUTO,
            [(1, DRI, "Carta A", "carta", "Double Rare", "001/182", None, None)])
    for dia in range(8, 14):
        data = D(2026, 10, dia)
        chave = f"raw/tcgplayer/group_id={DRI}/data={data}/prices.json"
        _gravar(con, s / "preco_diario" / f"group_id={DRI}" / f"data={data}", "preco.parquet", DDL_PRECO,
                [(data, 1, DRI, "Normal", 10.0, 9.0, 10.0, 12.0, "USD", "tcgcsv", chave)])
    _gravar(con, s / "cambio_diario" / f"group_id={DRI}", "cambio.parquet", DDL_CAMBIO, [
        (D(2026, 10, 9), 4.9990, 5.0000, dt.datetime(2026, 10, 9, 13, 5), "Fechamento", "raw/bcb_ptax/a"),
        (D(2026, 10, 13), 5.4990, 5.5000, dt.datetime(2026, 10, 13, 13, 5), "Fechamento", "raw/bcb_ptax/b"),
    ])
    cdi = [(D(2026, 10, 9), CDI_0910, "raw/bcb_cdi/a")]
    if cdi_1310:
        cdi.append((D(2026, 10, 13), CDI_1310, "raw/bcb_cdi/b"))
    _gravar(con, s / "cdi_diario" / f"group_id={DRI}", "cdi.parquet", DDL_CDI, cdi)
    con.close()
    estrela = duckdb.connect()
    montar_estrela(estrela, str(base))
    return estrela


@pytest.fixture
def lake(tmp_path):
    estrela = _montar(tmp_path, cdi_1310=True)
    yield estrela
    estrela.close()


@pytest.fixture
def lake_sem_cdi_1310(tmp_path):
    estrela = _montar(tmp_path, cdi_1310=False)
    yield estrela
    estrela.close()


def _dia(con, data):
    return con.execute(
        "SELECT cotacao_compra, cotacao_venda, data_ptax, cdi_taxa_dia, cdi_pendente "
        "FROM fato_cambio_diario WHERE data = ?",
        [data],
    ).fetchone()


def test_fim_de_semana_usa_ptax_de_sexta_e_cdi_zero(lake):
    for dia in (10, 11):
        linha = _dia(lake, D(2026, 10, dia))
        assert linha is not None, f"{dia}/10 deve existir no fato"
        compra, venda, data_ptax, cdi, pendente = linha
        assert compra == pytest.approx(4.9990), dia
        assert venda == pytest.approx(5.0000), dia
        assert data_ptax == D(2026, 10, 9), dia
        assert cdi == 0.0, dia
        assert pendente is False, dia


def test_dia_util_tem_ptax_e_cdi_do_proprio_dia(lake):
    assert _dia(lake, D(2026, 10, 9)) == (
        pytest.approx(4.9990), pytest.approx(5.0000), D(2026, 10, 9), pytest.approx(CDI_0910), False,
    )
    assert _dia(lake, D(2026, 10, 13)) == (
        pytest.approx(5.4990), pytest.approx(5.5000), D(2026, 10, 13), pytest.approx(CDI_1310), False,
    )


def test_feriado_nunca_usa_ptax_posterior(lake):
    compra, venda, data_ptax, cdi, pendente = _dia(lake, D(2026, 10, 12))
    assert (data_ptax, venda, compra) == (D(2026, 10, 9), pytest.approx(5.0), pytest.approx(4.999))
    assert cdi == 0.0 and pendente is False
    posteriores = lake.execute("SELECT count(*) FROM fato_cambio_diario WHERE data_ptax > data").fetchone()[0]
    assert posteriores == 0


def test_um_dia_de_calendario_por_linha(lake):
    datas = [r[0] for r in lake.execute("SELECT data FROM fato_cambio_diario ORDER BY data").fetchall()]
    assert datas == [r[0] for r in lake.execute("SELECT data FROM dim_data ORDER BY data").fetchall()]
    assert datas == [D(2026, 10, 8) + dt.timedelta(days=i) for i in range(6)]
    assert len(set(datas)) == len(datas)
    tipos = {c[0]: c[1] for c in lake.execute("DESCRIBE fato_cambio_diario").fetchall()}
    assert tipos == {
        "data": "DATE", "cotacao_compra": "DOUBLE", "cotacao_venda": "DOUBLE",
        "data_ptax": "DATE", "cdi_taxa_dia": "DOUBLE", "cdi_pendente": "BOOLEAN",
    }


def test_dia_antes_do_primeiro_boletim(lake):
    assert _dia(lake, D(2026, 10, 8)) == (None, None, None, 0.0, False)


def test_dia_util_sem_cdi_fica_pendente(lake_sem_cdi_1310):
    compra, venda, data_ptax, cdi, pendente = _dia(lake_sem_cdi_1310, D(2026, 10, 13))
    assert data_ptax == D(2026, 10, 13) and venda == pytest.approx(5.5)
    assert cdi == 0.0
    assert pendente is True
    assert _dia(lake_sem_cdi_1310, D(2026, 10, 12))[4] is False  # feriado
    pendentes = lake_sem_cdi_1310.execute(
        "SELECT data FROM fato_cambio_diario WHERE cdi_pendente ORDER BY data"
    ).fetchall()
    assert pendentes == [(D(2026, 10, 13),)]
