"""Testes da base do painel (T-45; RF-14, RF-20, RF-21).

Gold mínima gravada em Parquet num `tmp_path` com DuckDB local e lida pelo
painel via `PAINEL_GOLD_DIR`; o S3 nunca é usado. Rede bloqueada (conftest).
"""

import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import socket

from conftest import RedeBloqueadaError
import duckdb
import pyarrow as pa
import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[2] / "dashboard" / "app.py"
TIMEOUT = 60
GID = 24269
D1, D3 = dt.date(2026, 11, 1), dt.date(2026, 11, 3)  # 02/11 sem coleta
COT = {D1: 5.0, D3: 5.5}

# product_id: (nome, tipo, raridade, usd no primeiro dia, usd no último dia)
PRODUTOS = {
    1: ("Carta 90 centavos", "carta", "Rare", 0.90, 1.20),
    2: ("Carta 3 dolares", "carta", "Rare", 3.00, 4.00),
    3: ("Carta 5 dolares", "carta", "Double Rare", 5.00, 6.00),
    4: ("Carta 5,01 dolares", "carta", "Ultra Rare", 5.01, 7.00),
    5: ("Carta mais cara", "carta", "Special Illustration Rare", 20.00, 30.00),
    6: ("Booster Box", "selado", None, 100.00, 110.00),
}


_SOCKET_ORIGINAL = socket.socket  # capturado na importação, antes do bloqueio do conftest


class _SoSocketLocal(_SOCKET_ORIGINAL):
    """Só AF_UNIX: o loop asyncio do AppTest usa `socket.socketpair()` local.

    Qualquer outra família (AF_INET, AF_INET6) continua recusada, e o DNS
    segue bloqueado pelo conftest (RNF-05).
    """

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


def _gravar(con, sql, destino):
    con.execute(f"COPY ({sql}) TO '{destino}' (FORMAT parquet)")


def _gold(pasta: Path, com_imagem_e_link: bool = False) -> Path:
    con = duckdb.connect()
    linhas_fato, linhas_prod = [], []
    for pid, (nome, tipo, raridade, usd1, usd3) in PRODUTOS.items():
        sem = pid == 5 and not com_imagem_e_link
        img = "NULL" if sem else f"'https://img.exemplo/{pid}.jpg'"
        url = "NULL" if sem else f"'https://tcg.exemplo/{pid}'"
        rar = "NULL" if raridade is None else f"'{raridade}'"
        numero = "NULL" if tipo == "selado" else f"'{pid:03d}/182'"
        linhas_prod.append(f"({GID}, {pid}, '{nome}', '{tipo}', {rar}, {numero}, {img}, {url})")
        for dia, usd in ((D1, usd1), (D3, usd3)):
            linhas_fato.append(
                f"(DATE '{dia}', {pid}, {GID}, 'Normal', {usd}, {COT[dia]}, {usd * COT[dia]})"
            )
    # Outra coleção no fato e na dim_produto: não aparece na base da DRI
    extra = "'https://img.exemplo/outra.jpg', 'https://tcg.exemplo/outra'" if com_imagem_e_link else "NULL, NULL"
    linhas_prod.append(f"(99999, 1, 'Carta de outra colecao', 'carta', 'Rare', '001/100', {extra})")
    linhas_fato.append(f"(DATE '{D1}', 1, 99999, 'Normal', 500.0, 5.0, 2500.0)")
    linhas_fato.append(f"(DATE '{D3}', 1, 99999, 'Normal', 900.0, 5.5, 4950.0)")

    _gravar(
        con,
        "SELECT CAST(data AS DATE) AS data, product_id::INTEGER AS product_id, group_id::INTEGER AS group_id, "
        "acabamento, market_price::DOUBLE AS market_price, cotacao_aplicada::DOUBLE AS cotacao_aplicada, "
        "market_price_brl::DOUBLE AS market_price_brl FROM (VALUES "
        + ", ".join(linhas_fato)
        + ") AS t(data, product_id, group_id, acabamento, market_price, cotacao_aplicada, market_price_brl)",
        pasta / "fato_preco_diario.parquet",
    )
    _gravar(
        con,
        "SELECT group_id::INTEGER AS group_id, product_id::INTEGER AS product_id, nome, tipo_produto, "
        "raridade::VARCHAR AS raridade, numero::VARCHAR AS numero, image_url::VARCHAR AS image_url, "
        "url::VARCHAR AS url FROM (VALUES "
        + ", ".join(linhas_prod)
        + ") AS t(group_id, product_id, nome, tipo_produto, raridade, numero, image_url, url)",
        pasta / "dim_produto.parquet",
    )
    _gravar(
        con,
        f"SELECT CAST(unnest(generate_series(DATE '{D1}', DATE '{D3}', INTERVAL 1 DAY)) AS DATE) AS data",
        pasta / "dim_data.parquet",
    )
    # fato_cambio_diario (lido pela P3 desde a T-46): 02/11 com a PTAX de 01/11
    _gravar(
        con,
        "SELECT CAST(data AS DATE) AS data, compra::DOUBLE AS cotacao_compra, venda::DOUBLE AS cotacao_venda, "
        "CAST(data_ptax AS DATE) AS data_ptax, 0.0::DOUBLE AS cdi_taxa_dia, false AS cdi_pendente FROM (VALUES "
        f"('{D1}', 4.99, 5.0, '{D1}'), ('2026-11-02', 4.99, 5.0, '{D1}'), ('{D3}', 5.49, 5.5, '{D3}')"
        ") AS t(data, compra, venda, data_ptax)",
        pasta / "fato_cambio_diario.parquet",
    )
    _gravar(
        con,
        f"SELECT {GID}::INTEGER AS group_id, 'SV10: Destined Rivals' AS nome, 'DRI' AS sigla, "
        "DATE '2025-05-30' AS data_lancamento, 'Augusto' AS responsavel",
        pasta / "dim_colecao.parquet",
    )
    con.close()
    return pasta


@pytest.fixture
def painel(tmp_path, monkeypatch):
    def _abrir(com_imagem_e_link=False):
        pasta = tmp_path / ("com" if com_imagem_e_link else "sem")
        pasta.mkdir()
        _gold(pasta, com_imagem_e_link)
        monkeypatch.setenv("PAINEL_GOLD_DIR", str(pasta))
        at = AppTest.from_file(str(APP), default_timeout=TIMEOUT).run()
        assert not at.exception, at.exception
        return at, pasta

    return _abrir


def _tabela(at):
    return at.dataframe[0].value


def _ids_na_tabela(at):
    return set(_tabela(at)["Produto"])


# ---------------------------------------------------------------- RF-14


def test_padrao_em_reais_e_filtro_da_p1(painel):
    at, _ = painel()
    assert at.sidebar.radio[0].value == "reais"
    assert at.sidebar.number_input[0].value == 1.0
    tabela = _tabela(at)
    assert "Preço inicial (R$)" in tabela.columns and "Preço atual (R$)" in tabela.columns
    assert "Carta 90 centavos" not in _ids_na_tabela(at)
    assert "Booster Box" not in _ids_na_tabela(at)
    assert "Carta de outra colecao" not in _ids_na_tabela(at)
    linha = tabela[tabela["Produto"] == "Carta mais cara"].iloc[0]
    assert linha["Preço inicial (R$)"] == "R$ 100,00"  # US$ 20 × 5,00 (formato pt-BR, T-46)
    assert linha["Preço atual (R$)"] == "R$ 165,00"  # US$ 30 × 5,50


def test_dolar_e_minimo_5_trocam_moeda_e_removem_itens(painel):
    at, _ = painel()
    at.sidebar.radio[0].set_value("dólar")
    at.sidebar.number_input[0].set_value(5.0)
    at.run()
    assert not at.exception
    tabela = _tabela(at)
    assert "Preço inicial (US$)" in tabela.columns and "Preço atual (US$)" in tabela.columns
    assert not any("R$" in c for c in tabela.columns)
    assert _ids_na_tabela(at) == {"Carta 5,01 dolares", "Carta mais cara"}  # US$ 5,00 sai (estrito)
    linha = tabela[tabela["Produto"] == "Carta mais cara"].iloc[0]
    assert linha["Preço inicial (US$)"] == "US$ 20,00"
    assert linha["Preço atual (US$)"] == "US$ 30,00"


def _script_p5(caminho):
    import importlib.util

    spec = importlib.util.spec_from_file_location("painel_app", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    modulo.filtro_preco_minimo("P5")


def test_padrao_do_filtro_na_p5_vale_5():
    at = AppTest.from_function(_script_p5, args=(str(APP),), default_timeout=TIMEOUT).run()
    assert not at.exception, at.exception
    assert at.sidebar.number_input[0].value == 5.0
    assert "P5" in at.sidebar.number_input[0].label


# ---------------------------------------------------------------- RF-21


def test_completar_calendario_deixa_dia_sem_coleta_nulo():
    import pandas as pd

    app = _carregar_modulo()
    serie = pd.DataFrame({"data": [D1, D3], "valor": [10.0, 12.0]})
    dim_data = pd.DataFrame({"data": [D1, dt.date(2026, 11, 2), D3]})
    completa = app.completar_calendario(serie, dim_data)
    assert [d.date() for d in completa["data"]] == [D1, dt.date(2026, 11, 2), D3]
    assert completa["valor"].iloc[0] == 10.0 and completa["valor"].iloc[2] == 12.0
    assert pd.isna(completa["valor"].iloc[1])


def test_dia_sem_coleta_fica_sem_ponto_no_grafico(painel):
    at, _ = painel()
    # com as abas da T-46 há vários gráficos: o da série do item é localizado pelo título
    graficos = [
        g for g in at.get("vega_lite_chart")
        if json.loads(g.proto.spec).get("title", "").startswith("Preço de ")
    ]
    assert len(graficos) == 1
    proto = graficos[0].proto
    spec = json.loads(proto.spec)
    assert spec["mark"]["type"] == "line"
    assert spec["mark"]["invalid"] == "break-paths-show-domains"
    dados = pa.ipc.open_stream(proto.datasets[0].data.data).read_all().to_pydict()
    por_dia = {d.date(): v for d, v in zip(dados["data"], dados["valor"])}
    assert set(por_dia) == {D1, dt.date(2026, 11, 2), D3}
    assert por_dia[dt.date(2026, 11, 2)] is None  # sem ponto, sem interpolação
    assert por_dia[D1] == pytest.approx(100.0) and por_dia[D3] == pytest.approx(165.0)


def test_aviso_de_periodo_curto(painel):
    at, _ = painel()
    avisos = [w.value for w in at.warning]
    assert any("período é curto e não sustenta previsão" in a for a in avisos)
    assert any("3 dias" in a for a in avisos)


# ---------------------------------------------------------------- RF-20


def test_imagem_e_link_indisponiveis_quando_nulos(painel):
    at, _ = painel()  # item padrão = o mais caro, sem image_url nem url
    legendas = [c.value for c in at.caption]
    assert "imagem indisponível" in legendas
    assert "link indisponível" in legendas
    assert len(at.get("image")) == 0


def test_imagem_e_link_quando_preenchidos(painel):
    at, _ = painel(com_imagem_e_link=True)
    legendas = [c.value for c in at.caption]
    assert "imagem indisponível" not in legendas and "link indisponível" not in legendas
    imagens = at.get("image")
    # base e P1 (T-46) mostram o mais caro da DRI; a P5 mostra o mais caro de todas as coleções
    assert len(imagens) >= 1
    assert imagens[0].proto.imgs[0].url == "https://img.exemplo/5.jpg"
    assert {i.proto.imgs[0].url for i in imagens} <= {"https://img.exemplo/5.jpg", "https://img.exemplo/outra.jpg"}
    assert any("https://tcg.exemplo/5" in m.value for m in at.markdown)


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
