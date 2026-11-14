"""Testes do painel das perguntas P1 a P5 (T-46; RF-15 a RF-19, RF-22).

Gold mínima gravada em Parquet num `tmp_path` com DuckDB local e lida pelo
painel via `PAINEL_GOLD_DIR`; o S3 nunca é usado. Rede bloqueada (conftest),
com só AF_UNIX liberado para o loop asyncio do AppTest, como na T-45.
"""

import datetime as dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import socket

from conftest import RedeBloqueadaError
import duckdb
import pyarrow as pa
import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[2] / "dashboard" / "app.py"
TIMEOUT = 60
GID, OUTRA = 24269, 99999
DIAS = [dt.date(2026, 11, d) for d in (1, 2, 3, 4)]
COT = dict(zip(DIAS, (5.0, 5.1, 5.2, 5.5)))
AVISO = "Faltam dados de outras coleções"
TITULO_P3 = "Valor da coleção e PTAX (base 100)"

# product_id: (nome, tipo, raridade, usd no primeiro dia, usd no último dia)
PRODUTOS_DRI = {
    1: ("Carta 90 centavos", "carta", "Rare", 0.90, 1.50),
    2: ("Code Card", "carta", "Code Card", 10.0, 20.0),
    3: ("Carta mais cara", "carta", "Special Illustration Rare", 355.396, 381.38),
    4: ("Booster Box", "selado", None, 100.0, 110.0),
    **{10 + i: (f"Alta {i:02d}", "carta", "Double Rare", 2.0 + i, (2.0 + i) * 1.05) for i in range(1, 13)},
    **{30 + i: (f"Queda {i}", "carta", "Ultra Rare", 10.0, 7.0) for i in range(1, 4)},
}
# A outra coleção começa em 02/11: o primeiro dia comum da P3 é 02/11
PRODUTOS_OUTRA = {
    1: ("Outra carta A", "carta", "Rare", 20.0, 25.0),
    2: ("Outra carta B", "carta", "Illustration Rare", 8.0, 6.0),
}


_SOCKET_ORIGINAL = socket.socket  # capturado na importação, antes do bloqueio do conftest


class _SoSocketLocal(_SOCKET_ORIGINAL):
    """Só AF_UNIX (socketpair do asyncio); AF_INET e AF_INET6 seguem recusados (RNF-05)."""

    def __init__(self, family=-1, type=-1, proto=-1, fileno=None):
        if family != socket.AF_UNIX:
            raise RedeBloqueadaError(
                f"rede bloqueada nos testes de unidade (RNF-05): família {family!r} recusada"
            )
        super().__init__(family, type, proto, fileno)


@pytest.fixture(autouse=True)
def permitir_so_socket_local(bloquear_rede, monkeypatch):
    monkeypatch.setattr(socket, "socket", _SoSocketLocal)
    yield


def test_rede_continua_bloqueada_neste_modulo():
    with pytest.raises(RedeBloqueadaError):
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with pytest.raises(RedeBloqueadaError):
        socket.getaddrinfo("example.com", 443)


def _carregar_modulo():
    spec = importlib.util.spec_from_file_location("painel_app", APP)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# ---------------------------------------------------------------- gold de teste


def _preco(usd1, usd4, k):
    return usd1 + (usd4 - usd1) * k / 3


def _gravar(con, sql, destino):
    con.execute(f"COPY ({sql}) TO '{destino}' (FORMAT parquet)")


def _gold(pasta: Path, com_outra: bool) -> Path:
    con = duckdb.connect()
    fato, prod = [], []
    colecoes = [(GID, PRODUTOS_DRI, DIAS)]
    if com_outra:
        colecoes.append((OUTRA, PRODUTOS_OUTRA, DIAS[1:]))
    for gid, produtos, dias in colecoes:
        for pid, (nome, tipo, raridade, usd1, usd4) in produtos.items():
            rar = "NULL" if raridade is None else f"'{raridade}'"
            prod.append(
                f"({gid}, {pid}, '{nome}', '{tipo}', {rar}, '{pid:03d}', "
                f"'https://img.exemplo/{gid}/{pid}.jpg', 'https://tcg.exemplo/{gid}/{pid}')"
            )
            for k, dia in enumerate(dias):
                usd = _preco(usd1, usd4, k * 3 / (len(dias) - 1))
                fato.append(f"(DATE '{dia}', {pid}, {gid}, 'Normal', {usd}, {COT[dia]}, {usd * COT[dia]})")
    _gravar(
        con,
        "SELECT CAST(data AS DATE) AS data, product_id::INTEGER AS product_id, group_id::INTEGER AS group_id, "
        "acabamento, market_price::DOUBLE AS market_price, cotacao_aplicada::DOUBLE AS cotacao_aplicada, "
        "market_price_brl::DOUBLE AS market_price_brl FROM (VALUES "
        + ", ".join(fato)
        + ") AS t(data, product_id, group_id, acabamento, market_price, cotacao_aplicada, market_price_brl)",
        pasta / "fato_preco_diario.parquet",
    )
    _gravar(
        con,
        "SELECT group_id::INTEGER AS group_id, product_id::INTEGER AS product_id, nome, tipo_produto, "
        "raridade::VARCHAR AS raridade, numero::VARCHAR AS numero, image_url, url FROM (VALUES "
        + ", ".join(prod)
        + ") AS t(group_id, product_id, nome, tipo_produto, raridade, numero, image_url, url)",
        pasta / "dim_produto.parquet",
    )
    _gravar(
        con,
        "SELECT CAST(data AS DATE) AS data, (venda - 0.01)::DOUBLE AS cotacao_compra, "
        "venda::DOUBLE AS cotacao_venda, CAST(data AS DATE) AS data_ptax, 0.0::DOUBLE AS cdi_taxa_dia, "
        "false AS cdi_pendente FROM (VALUES "
        + ", ".join(f"('{d}', {c})" for d, c in COT.items())
        + ") AS t(data, venda)",
        pasta / "fato_cambio_diario.parquet",
    )
    _gravar(
        con,
        f"SELECT CAST(unnest(generate_series(DATE '{DIAS[0]}', DATE '{DIAS[-1]}', INTERVAL 1 DAY)) AS DATE) AS data",
        pasta / "dim_data.parquet",
    )
    linhas_colecao = [f"({GID}, 'SV10: Destined Rivals', 'DRI')"]
    if com_outra:
        linhas_colecao.append(f"({OUTRA}, 'Outra Colecao', 'OUT')")
    _gravar(
        con,
        "SELECT group_id::INTEGER AS group_id, nome, sigla, DATE '2025-05-30' AS data_lancamento, "
        "'Autor' AS responsavel FROM (VALUES " + ", ".join(linhas_colecao) + ") AS t(group_id, nome, sigla)",
        pasta / "dim_colecao.parquet",
    )
    con.close()
    return pasta


@pytest.fixture
def painel(tmp_path, monkeypatch):
    def _abrir(com_outra=True):
        pasta = tmp_path / ("duas" if com_outra else "so_dri")
        pasta.mkdir()
        _gold(pasta, com_outra)
        monkeypatch.setenv("PAINEL_GOLD_DIR", str(pasta))
        at = AppTest.from_file(str(APP), default_timeout=TIMEOUT).run()
        assert not at.exception, at.exception
        return at, pasta

    return _abrir


def _graficos(at):
    """(spec, dados) de cada gráfico Vega-Lite, com os dados do Arrow em dicionário."""
    saida = []
    for g in at.get("vega_lite_chart"):
        spec = json.loads(g.proto.spec)
        dados = pa.ipc.open_stream(g.proto.datasets[0].data.data).read_all().to_pydict()
        saida.append((spec, dados))
    return saida


def _grafico(at, inicio_titulo):
    achados = [(s, d) for s, d in _graficos(at) if str(s.get("title", "")).startswith(inicio_titulo)]
    assert len(achados) == 1, [s.get("title") for s, _ in _graficos(at)]
    return achados[0]


def _rankings(at):
    return [df.value for df in at.dataframe if "Variação em reais" in df.value.columns]


def _avisos_outras(at):
    return [w.value for w in at.warning if AVISO in w.value]


# ---------------------------------------------------------------- formatação


def test_formatar_moeda_em_ptbr():
    app = _carregar_modulo()
    assert app.formatar_moeda(1776.98, "R$") == "R$ 1.776,98"
    assert app.formatar_moeda(381.38, "US$") == "US$ 381,38"
    assert app.formatar_moeda(0, "R$") == "R$ 0,00"
    assert app.formatar_moeda(1234567.891, "R$") == "R$ 1.234.567,89"
    assert app.formatar_moeda(-2.5, "R$") == "-R$ 2,50"
    assert app.formatar_moeda(None, "R$") == "—"
    assert app.formatar_moeda(math.nan, "US$") == "—"


def test_formatar_percentual_e_data():
    app = _carregar_modulo()
    assert app.formatar_percentual(0.1234) == "12,34%"
    assert app.formatar_percentual(-0.01) == "-1,00%"
    assert app.formatar_percentual(None) == "—"
    assert app.formatar_data(dt.date(2026, 11, 3)) == "03/11"


# ---------------------------------------------------------------- abas


def test_seis_abas_renderizam_em_reais_e_em_dolar(painel):
    at, _ = painel()
    app = _carregar_modulo()
    assert [t.label for t in at.tabs] == list(app.ABAS)
    assert at.sidebar.number_input[0].value == 1.0 and "P1" in at.sidebar.number_input[0].label
    assert at.sidebar.number_input[1].value == 5.0 and "P5" in at.sidebar.number_input[1].label
    at.sidebar.radio[0].set_value("dólar")
    at.run()
    assert not at.exception, at.exception
    assert len(_graficos(at)) >= 5  # série do item, P2, P3, P4 e P5


# ---------------------------------------------------------------- P1 (RF-15)


def test_p1_rankings_com_decomposicao_e_filtros(painel):
    at, _ = painel()
    alta, queda = _rankings(at)
    assert 0 < len(alta) <= 10 and 0 < len(queda) <= 10
    assert len(alta) == 10  # 13 itens em alta, só os 10 primeiros
    nomes = set(alta["Produto"]) | set(queda["Produto"])
    assert "Code Card" not in nomes and "Carta 90 centavos" not in nomes
    assert alta["Produto"].iloc[0] == "Carta mais cara"
    assert set(queda["Produto"]) == {"Queda 1", "Queda 2", "Queda 3"}
    linha = queda[queda["Produto"] == "Queda 1"].iloc[0]
    assert linha["Carta (dólar)"] == "-30,00%"
    assert linha["Câmbio"] == "10,00%"
    assert linha["Cruzado"] == "-3,00%"
    assert linha["Variação em reais"] == "-23,00%"  # 0,70 × 1,10 − 1
    topo = alta.iloc[0]
    assert topo["Preço inicial (R$)"] == "R$ 1.776,98"
    assert topo["Imagem"] == f"https://img.exemplo/{GID}/3.jpg"


def test_p1_em_dolar_formata_us(painel):
    at, _ = painel()
    at.sidebar.radio[0].set_value("dólar")
    at.run()
    alta, _ = _rankings(at)
    topo = alta.iloc[0]
    assert topo["Preço atual (US$)"] == "US$ 381,38"
    assert not any("R$" in c for c in alta.columns)


# ---------------------------------------------------------------- P2 (RF-16)


def test_p2_indice_base_100_da_dri(painel):
    at, _ = painel()
    spec, dados = _grafico(at, "Índice base 100")
    assert spec["mark"]["invalid"] == "break-paths-show-domains"
    series = set(dados["serie"])
    assert series == {"Selados (média)", "Double Rare em diante (soma)"}
    for s in series:
        primeiro = [v for d, v, x in zip(dados["data"], dados["valor"], dados["serie"]) if x == s and d.date() == DIAS[0]]
        assert primeiro == [pytest.approx(100.0)]


# ---------------------------------------------------------------- P3 (RF-17, RF-22)


def test_p3_base_comum_ptax_e_dri_destacada(painel):
    at, _ = painel()
    spec, dados = _grafico(at, TITULO_P3)
    assert set(dados["serie"]) == {"DRI", "OUT", "PTAX"}
    linhas = list(zip(dados["data"], dados["serie"], dados["valor"], dados["espessura"]))
    for serie in ("DRI", "OUT", "PTAX"):
        base = [v for d, s, v, _ in linhas if s == serie and d.date() == DIAS[1]]
        assert base == [pytest.approx(100.0)]  # todas com 100 no primeiro dia comum (02/11)
    assert not [v for d, _, v, _ in linhas if d.date() == DIAS[0] and v is not None]
    espessura = {s: e for _, s, _, e in linhas}
    assert espessura["DRI"] > espessura["OUT"] and espessura["DRI"] > espessura["PTAX"]
    assert spec["encoding"]["strokeWidth"]["field"] == "espessura"
    assert _avisos_outras(at) == []


# ---------------------------------------------------------------- P4 (RF-18)


def test_p4_participacao_soma_100_e_itens_80(painel):
    at, _ = painel()
    _, dados = _grafico(at, "Participação por raridade")
    soma = {}
    for c, p in zip(dados["colecao"], dados["participacao"]):
        soma[c] = soma.get(c, 0.0) + p
    assert set(soma) == {"DRI", "OUT"}
    assert all(v == pytest.approx(1.0) for v in soma.values())
    assert "Code Card" not in set(dados["raridade"])
    tabela = next(df.value for df in at.dataframe if "Itens que somam 80% do valor" in df.value.columns)
    assert set(tabela["Coleção"]) == {"DRI", "OUT"}
    assert set(tabela["Último dia"]) == {"04/11"}
    assert (tabela["Itens que somam 80% do valor"] <= tabela["Itens no total"]).all()


# ---------------------------------------------------------------- P5 (RF-19)


def test_p5_dispersao_volatilidade_x_retorno_com_tooltip(painel):
    at, _ = painel()
    spec, dados = _grafico(at, "Retorno no período")
    enc = spec["encoding"]
    assert enc["x"]["field"] == "volatilidade"
    assert enc["y"]["field"] == "retorno"
    assert enc["color"]["field"] == "colecao"
    assert "nome" in [t["field"] for t in enc["tooltip"]]
    assert set(dados["colecao"]) == {"DRI", "OUT"}
    assert all(u > 5 for u in dados["usd_inicial"])  # filtro padrão da P5, estrito
    assert "Code Card" not in set(dados["nome"])


# ---------------------------------------------------------------- RF-22


def test_sem_outras_colecoes_p3_p4_p5_avisam_e_mostram_so_a_dri(painel):
    at, _ = painel(com_outra=False)
    assert len(_avisos_outras(at)) == 3  # P3, P4 e P5
    _, p3 = _grafico(at, TITULO_P3)
    assert set(p3["serie"]) == {"DRI", "PTAX"}
    assert any(v is not None for v in p3["valor"])  # sem gráfico vazio
    _, p4 = _grafico(at, "Participação por raridade")
    assert set(p4["colecao"]) == {"DRI"} and len(p4["colecao"]) > 0
    _, p5 = _grafico(at, "Retorno no período")
    assert set(p5["colecao"]) == {"DRI"} and len(p5["colecao"]) > 0


# ---------------------------------------------------------------- datas dd/mm


def test_eixos_de_data_em_dd_mm_e_utc(painel):
    at, _ = painel()
    linhas = [s for s, _ in _graficos(at) if s["mark"]["type"] == "line"]
    assert len(linhas) == 3  # série do item, P2 e P3
    for spec in linhas:
        x = spec["encoding"]["x"]
        assert x["axis"]["format"] == "%d/%m"
        assert x["timeUnit"] == "utcyearmonthdate"


# ---------------------------------------------------------------- só leitura


def test_painel_nao_grava_nada(painel):
    def _hashes(pasta):
        return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(pasta.iterdir())}

    at, pasta = painel()
    antes = _hashes(pasta)
    at.sidebar.radio[0].set_value("dólar")
    at.run()
    assert not at.exception
    assert _hashes(pasta) == antes
