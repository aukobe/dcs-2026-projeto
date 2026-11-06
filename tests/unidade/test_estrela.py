"""Testes do SQL do esquema estrela (T-30; RF-10, RF-11, RNF-01; ADR-003).

DuckDB local em memória, Parquets em `tmp_path` no layout do contrato e rede
bloqueada (conftest). Duas coleções: a DRI (24269) e uma segunda (99999).
PTAX de venda: 09/10 (sexta) = 5,0000 e 13/10 (terça) = 5,5000; 10/10, 11/10 e
12/10 (feriado) não têm boletim.
"""

import datetime as dt
from pathlib import Path

import duckdb
import pytest

from tcg.gold.sql import TABELAS, montar_estrela

DRI = 24269
OUTRA = 99999
D = dt.date


def _gravar(con, pasta: Path, nome: str, ddl: str, linhas: list[tuple]) -> None:
    """Cria uma tabela temporária com os tipos do contrato e exporta para Parquet."""
    pasta.mkdir(parents=True, exist_ok=True)
    con.execute(f"CREATE OR REPLACE TEMP TABLE t ({ddl})")
    if linhas:
        marcadores = ", ".join("?" * len(linhas[0]))
        con.executemany(f"INSERT INTO t VALUES ({marcadores})", linhas)
    con.execute(f"COPY t TO '{pasta / nome}' (FORMAT parquet)")


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


def _preco(data, product_id, group_id, acabamento, market):
    chave = f"raw/tcgplayer/group_id={group_id}/data={data.isoformat()}/prices.json"
    return (data, product_id, group_id, acabamento, market, market * 0.9, market, market * 1.2, "USD", "tcgcsv", chave)


@pytest.fixture
def lake(tmp_path):
    """Silver de duas coleções no layout do contrato, sob `tmp_path`."""
    con = duckdb.connect()
    s = tmp_path / "silver"
    for gid, nome, sigla in [(DRI, "Destined Rivals", "DRI"), (OUTRA, "Outra Coleção", "OUT")]:
        _gravar(con, s / "colecao" / f"group_id={gid}", "colecao.parquet", DDL_COLECAO,
                [(gid, nome, sigla, D(2025, 5, 30), "teste")])
    _gravar(con, s / "produto" / f"group_id={DRI}", "produto.parquet", DDL_PRODUTO, [
        (1, DRI, "Carta A", "carta", "Double Rare", "001/182", None, None),
        (2, DRI, "Booster Box", "selado", None, None, None, None),
    ])
    _gravar(con, s / "produto" / f"group_id={OUTRA}", "produto.parquet", DDL_PRODUTO, [
        (1, OUTRA, "Carta X", "carta", "Ultra Rare", "010/100", None, None),
    ])
    precos_dri = {
        D(2026, 10, 8): [_preco(D(2026, 10, 8), 1, DRI, "Normal", 8.0)],   # antes do 1º boletim
        D(2026, 10, 10): [_preco(D(2026, 10, 10), 1, DRI, "Normal", 10.0),
                          _preco(D(2026, 10, 10), 1, DRI, "Reverse Holofoil", 4.0),
                          _preco(D(2026, 10, 10), 2, DRI, "Normal", 200.0)],
        D(2026, 10, 11): [_preco(D(2026, 10, 11), 1, DRI, "Normal", 11.0)],
        D(2026, 10, 12): [_preco(D(2026, 10, 12), 1, DRI, "Normal", 12.0)],
        D(2026, 10, 13): [_preco(D(2026, 10, 13), 1, DRI, "Normal", 13.0)],
    }
    for data, linhas in precos_dri.items():
        _gravar(con, s / "preco_diario" / f"group_id={DRI}" / f"data={data}", "preco.parquet", DDL_PRECO, linhas)
    _gravar(con, s / "preco_diario" / f"group_id={OUTRA}" / "data=2026-10-10", "preco.parquet", DDL_PRECO,
            [_preco(D(2026, 10, 10), 1, OUTRA, "Holofoil", 20.0)])
    _gravar(con, s / "cambio_diario" / f"group_id={DRI}", "cambio.parquet", DDL_CAMBIO, [
        (D(2026, 10, 9), 4.9990, 5.0000, dt.datetime(2026, 10, 9, 13, 5), "Fechamento", "raw/bcb_ptax/a"),
        (D(2026, 10, 13), 5.4990, 5.5000, dt.datetime(2026, 10, 13, 13, 5), "Fechamento", "raw/bcb_ptax/b"),
    ])
    con.close()
    estrela = duckdb.connect()
    montar_estrela(estrela, str(tmp_path))
    yield estrela
    estrela.close()


def _linha(con, data, product_id=1, group_id=DRI, acabamento="Normal"):
    return con.execute(
        "SELECT market_price, market_price_brl, cotacao_aplicada, data_ptax FROM fato_preco_diario "
        "WHERE data = ? AND product_id = ? AND group_id = ? AND acabamento = ?",
        [data, product_id, group_id, acabamento],
    ).fetchone()


def test_conversao_sabado_usa_ptax_de_sexta(lake):
    market, brl, cotacao, data_ptax = _linha(lake, D(2026, 10, 10))
    assert market == 10.0
    assert brl == pytest.approx(50.00)
    assert cotacao == pytest.approx(5.0000)
    assert data_ptax == D(2026, 10, 9)


def test_nunca_usa_ptax_posterior(lake):
    for dia in (10, 11, 12):
        _, brl, cotacao, data_ptax = _linha(lake, D(2026, 10, dia))
        assert data_ptax == D(2026, 10, 9), dia
        assert cotacao == pytest.approx(5.0000), dia
        assert brl == pytest.approx(dia * 5.0), dia
    # o ASOF avança quando sai o boletim novo
    _, brl, cotacao, data_ptax = _linha(lake, D(2026, 10, 13))
    assert (data_ptax, cotacao, brl) == (D(2026, 10, 13), pytest.approx(5.5), pytest.approx(13 * 5.5))
    posteriores = lake.execute("SELECT count(*) FROM fato_preco_diario WHERE data_ptax > data").fetchone()[0]
    assert posteriores == 0


def test_preco_anterior_ao_primeiro_boletim_fica_com_conversao_nula(lake):
    linha = _linha(lake, D(2026, 10, 8))
    assert linha is not None, "o preço de 08/10 deve continuar no fato"
    market, brl, cotacao, data_ptax = linha
    assert market == 8.0
    assert brl is None and cotacao is None and data_ptax is None


def test_dim_colecao_tem_as_duas_colecoes(lake):
    linhas = lake.execute("SELECT group_id, sigla FROM dim_colecao ORDER BY group_id").fetchall()
    assert linhas == [(DRI, "DRI"), (OUTRA, "OUT")]
    produtos = lake.execute("SELECT group_id, product_id FROM dim_produto ORDER BY 1, 2").fetchall()
    assert produtos == [(DRI, 1), (DRI, 2), (OUTRA, 1)]


def test_group_id_vem_da_coluna_sem_hive(lake):
    for tabela in ("fato_preco_diario", "dim_produto", "dim_colecao"):
        colunas = [c[0] for c in lake.execute(f"DESCRIBE {tabela}").fetchall()]
        assert colunas.count("group_id") == 1, tabela
        assert "data_1" not in colunas and "group_id_1" not in colunas, tabela
    tipo = dict((c[0], c[1]) for c in lake.execute("DESCRIBE fato_preco_diario").fetchall())
    assert tipo["group_id"] == "INTEGER" and tipo["data"] == "DATE"
    # a segunda coleção usa a PTAX da DRI (ADR-003)
    _, brl, cotacao, data_ptax = _linha(lake, D(2026, 10, 10), product_id=1, group_id=OUTRA, acabamento="Holofoil")
    assert (brl, cotacao, data_ptax) == (pytest.approx(100.0), pytest.approx(5.0), D(2026, 10, 9))


def test_dimensoes_e_grao(lake):
    assert set(TABELAS) == {"dim_produto", "dim_colecao", "dim_data", "dim_acabamento", "fato_preco_diario"}
    datas = [r[0] for r in lake.execute("SELECT data FROM dim_data ORDER BY data").fetchall()]
    assert datas == [D(2026, 10, 8) + dt.timedelta(days=i) for i in range(6)]  # 08/10 a 13/10, com o 09/10 sem preço
    fds = lake.execute("SELECT data FROM dim_data WHERE fim_de_semana ORDER BY data").fetchall()
    assert fds == [(D(2026, 10, 10),), (D(2026, 10, 11),)]
    acabamentos = [r[0] for r in lake.execute("SELECT acabamento FROM dim_acabamento").fetchall()]
    assert acabamentos == ["Holofoil", "Normal", "Reverse Holofoil"]
    total, distintos = lake.execute(
        "SELECT count(*), count(DISTINCT (data, group_id, product_id, acabamento)) FROM fato_preco_diario"
    ).fetchone()
    assert total == distintos == 8  # 1 + 3 + 1 + 1 + 1 da DRI e 1 da segunda coleção
    sem_preco = lake.execute("SELECT count(*) FROM fato_preco_diario WHERE data = DATE '2026-10-09'").fetchone()[0]
    assert sem_preco == 0
