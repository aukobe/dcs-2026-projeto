"""Testes do painel das carteiras e do placar da turma (T-47; RF-24, RF-25, RF-28).

Gold mínima da DRI gravada em Parquet num `tmp_path` com DuckDB local; as
tabelas das carteiras e a gold_turma da DRI saem do código real do `make gold`
(`calcular_carteiras`, T-44), e a gold_turma de duas outras coleções é escrita à
mão no contrato. O painel lê tudo por `PAINEL_GOLD_DIR` e `PAINEL_GOLD_TURMA_DIR`;
o S3 nunca é usado. Rede bloqueada (conftest), com só AF_UNIX liberado para o
loop asyncio do AppTest, como na T-45 e na T-46.

Contas da fixture (PTAX de venda 5,00 e de compra 4,99 em todos os dias):
- selado: Booster Box a US$ 250 → preço de compra 250 × 5,00 = R$ 1.250,00 >
  R$ 1.000,00 → 0 unidades, custo R$ 0,00, caixa R$ 1.000,00 (ADR-006). O valor
  diário da selado é só o caixa, igual ao da cdi: não supera a cdi (empate).
- dolar: 1000 / 5,00 = US$ 200,00 → 200 × 4,99 = R$ 998,00 em todos os dias.
- cdi: 01/11 é domingo (taxa 0), 02/11 rende 0,05%, 03/11 tem CDI pendente
  (taxa 0), 04/11 rende 0,05%. A taxa de d rende de d a d+1: 1000; 1000;
  1000 × 1,0005 = 1000,50; 1000,50. Retorno 0,05%; 04/11 marcado como pendente.
- cesta_raras: a carta 21 (a mais cara) cai de US$ 17 para US$ 14 em 04/11, e
  a carta 20 não tem preço em 03/11 (preço carregado). Com taxa 15%, a cesta
  vale ≈ 85% do custo: muito abaixo da dolar (R$ 998,00) no último dia.

gold_turma das outras coleções (retorno no último dia):
- OUTA (11111, 01 a 04/11): selado 1200 > cdi 1001,5 (sim); cesta 980 < dolar
  1030 (não); perda máxima da cesta = (1000 − 900) / 1000 = 10%; da selado =
  (1100 − 1050) / 1100 ≈ 4,55%.
- OUTB (22222, 02 a 05/11, período diferente): selado 1020 > 1001,5 (sim);
  cesta 1200 > 1030 (sim); cesta sempre sobe: perda 0%; selado (1000 − 990) /
  1000 = 1%.
- DRI: selado = cdi (não); cesta < dolar (não); perda da cesta > 0; perda da
  selado = 0 (série 1000; 1000; 1000,50; 1000,50 nunca cai).
Placar: selado "2 de 3", cesta "1 de 3", menor perda da cesta_raras: OUTB;
da selado: DRI.
"""

import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import socket

from conftest import RedeBloqueadaError
import duckdb
import pandas as pd
import pyarrow as pa
import pytest
from streamlit.testing.v1 import AppTest

from tcg.gold.construtor import TABELA_GOLD_TURMA, TABELAS_CARTEIRA, calcular_carteiras

APP = Path(__file__).resolve().parents[2] / "dashboard" / "app.py"
TIMEOUT = 60
GID, OUTA, OUTB, OUTC = 24269, 11111, 22222, 33333
DIAS = [dt.date(2026, 11, d) for d in (1, 2, 3, 4)]
TAXA = 0.15
AVISO_SO_DRI = "Faltam dados de outras coleções na gold_turma"
TITULO = "Valor de liquidação por dia"

# product_id: (nome, tipo, raridade, usd por dia; None = sem linha no fato)
PRODUTOS = {
    1: ("Destined Rivals Booster Box", "selado", None, [250.0] * 4),
    2: ("Destined Rivals Elite Trainer Box", "selado", None, [50.0] * 4),
    3: ("Code Card", "carta", "Code Card", [50.0] * 4),
    **{
        10 + i: (
            f"Carta {i:02d}",
            "carta",
            "Illustration Rare" if i <= 6 else "Special Illustration Rare",
            [5.0 + i] * 4,
        )
        for i in range(1, 12)
    },
}
PRODUTOS[20] = ("Carta 10", "carta", "Special Illustration Rare", [15.0, 15.0, None, 15.0])
PRODUTOS[21] = ("Carta 11", "carta", "Special Illustration Rare", [17.0, 17.0, 17.0, 14.0])
CDI = {DIAS[0]: (0.0, False), DIAS[1]: (0.05, False), DIAS[2]: (0.0, True), DIAS[3]: (0.05, False)}

CDI_OUT = [1000.0, 1000.5, 1001.0, 1001.5]
DOLAR_OUT = [1000.0, 1010.0, 1020.0, 1030.0]
OUTRAS = {
    OUTA: (DIAS, {
        "selado": [1000.0, 1100.0, 1050.0, 1200.0],
        "cesta_raras": [1000.0, 900.0, 950.0, 980.0],
        "propria": [1000.0] * 4,
        "dolar": DOLAR_OUT,
        "cdi": CDI_OUT,
    }),
    OUTB: ([d + dt.timedelta(days=1) for d in DIAS], {
        "selado": [1000.0, 990.0, 1010.0, 1020.0],
        "cesta_raras": [1000.0, 1100.0, 1150.0, 1200.0],
        "propria": [1000.0] * 4,
        "dolar": DOLAR_OUT,
        "cdi": CDI_OUT,
    }),
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


def _copiar(con, sql, destino: Path):
    destino.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY ({sql}) TO '{destino}' (FORMAT parquet)")


def _gold(pasta: Path, turma: Path, regra_propria: bool, com_outras: bool) -> None:
    """Gold da DRI (com OUTC só no fato), carteiras pelo código real e gold_turma."""
    con = duckdb.connect()
    fato, prod = [], []
    for pid, (nome, tipo, raridade, precos) in PRODUTOS.items():
        rar = "NULL" if raridade is None else f"'{raridade}'"
        prod.append(f"({GID}, {pid}, '{nome}', '{tipo}', {rar}, '{pid:03d}', NULL, NULL)")
        for dia, usd in zip(DIAS, precos):
            if usd is not None:
                fato.append(f"(DATE '{dia}', {pid}, {GID}, 'Normal', {usd}, 5.0, {usd * 5.0})")
    # OUTC tem silver (está no fato da gold), mas não grava gold_turma
    prod.append(f"({OUTC}, 1, 'Outra carta', 'carta', 'Rare', '001', NULL, NULL)")
    for dia in DIAS:
        fato.append(f"(DATE '{dia}', 1, {OUTC}, 'Normal', 20.0, 5.0, 100.0)")
    _copiar(
        con,
        "SELECT CAST(data AS DATE) AS data, product_id::INTEGER AS product_id, group_id::INTEGER AS group_id, "
        "acabamento, market_price::DOUBLE AS market_price, cotacao_aplicada::DOUBLE AS cotacao_aplicada, "
        "market_price_brl::DOUBLE AS market_price_brl FROM (VALUES " + ", ".join(fato)
        + ") AS t(data, product_id, group_id, acabamento, market_price, cotacao_aplicada, market_price_brl)",
        pasta / "fato_preco_diario.parquet",
    )
    _copiar(
        con,
        "SELECT group_id::INTEGER AS group_id, product_id::INTEGER AS product_id, nome, tipo_produto, "
        "raridade::VARCHAR AS raridade, numero::VARCHAR AS numero, image_url::VARCHAR AS image_url, "
        "url::VARCHAR AS url FROM (VALUES " + ", ".join(prod)
        + ") AS t(group_id, product_id, nome, tipo_produto, raridade, numero, image_url, url)",
        pasta / "dim_produto.parquet",
    )
    _copiar(
        con,
        "SELECT CAST(data AS DATE) AS data, 4.99::DOUBLE AS cotacao_compra, 5.0::DOUBLE AS cotacao_venda, "
        "CAST(data AS DATE) AS data_ptax, taxa::DOUBLE AS cdi_taxa_dia, pendente AS cdi_pendente FROM (VALUES "
        + ", ".join(f"('{d}', {t}, {str(p).lower()})" for d, (t, p) in CDI.items())
        + ") AS t(data, taxa, pendente)",
        pasta / "fato_cambio_diario.parquet",
    )
    _copiar(
        con,
        f"SELECT CAST(unnest(generate_series(DATE '{DIAS[0]}', DATE '{DIAS[-1]}', INTERVAL 1 DAY)) AS DATE) AS data",
        pasta / "dim_data.parquet",
    )
    _copiar(
        con,
        "SELECT group_id::INTEGER AS group_id, nome, sigla, DATE '2025-05-30' AS data_lancamento, "
        f"'Autor' AS responsavel FROM (VALUES ({GID}, 'SV10: Destined Rivals', 'DRI'), "
        f"({OUTA}, 'Outra A', 'OUTA'), ({OUTB}, 'Outra B', 'OUTB'), ({OUTC}, 'Outra C', 'OUTC')) "
        "AS t(group_id, nome, sigla)",
        pasta / "dim_colecao.parquet",
    )

    # carteiras e gold_turma da DRI pelo código do `make gold` (T-44)
    for tabela in ("fato_preco_diario", "dim_produto", "fato_cambio_diario"):
        con.execute(f"CREATE VIEW g_{tabela} AS SELECT * FROM read_parquet('{pasta / f'{tabela}.parquet'}')")
    calcular_carteiras(con, "g_fato_preco_diario", "g_dim_produto", "g_fato_cambio_diario", TAXA, regra_propria)
    for tabela in TABELAS_CARTEIRA:
        _copiar(con, f"SELECT * FROM {tabela}", pasta / f"{tabela}.parquet")
    _copiar(con, f"SELECT * FROM {TABELA_GOLD_TURMA}", turma / f"group_id={GID}" / "carteira.parquet")

    if com_outras:
        for gid, (dias, series) in OUTRAS.items():
            linhas = [
                f"(DATE '{d}', {gid}, '{c}', {v}, {v / 1000 - 1}, {0.0 if c in ('dolar', 'cdi') else TAXA})"
                for c, valores in series.items()
                for d, v in zip(dias, valores)
            ]
            _copiar(
                con,
                "SELECT CAST(data AS DATE) AS data, group_id::INTEGER AS group_id, carteira, "
                "valor_brl::DOUBLE AS valor_brl, retorno_acumulado::DOUBLE AS retorno_acumulado, "
                "taxa_venda::DOUBLE AS taxa_venda FROM (VALUES " + ", ".join(linhas)
                + ") AS t(data, group_id, carteira, valor_brl, retorno_acumulado, taxa_venda)",
                turma / f"group_id={gid}" / "carteira.parquet",
            )
    con.close()


@pytest.fixture
def painel(tmp_path, monkeypatch):
    def _abrir(regra_propria=True, com_outras=True):
        nome = f"{'propria' if regra_propria else 'pendente'}_{'turma' if com_outras else 'so_dri'}"
        pasta, turma = tmp_path / nome / "gold", tmp_path / nome / "gold_turma"
        pasta.mkdir(parents=True)
        turma.mkdir()
        _gold(pasta, turma, regra_propria, com_outras)
        monkeypatch.setenv("PAINEL_GOLD_DIR", str(pasta))
        monkeypatch.setenv("PAINEL_GOLD_TURMA_DIR", str(turma))
        at = AppTest.from_file(str(APP), default_timeout=TIMEOUT).run()
        assert not at.exception, at.exception
        return at, pasta, turma

    return _abrir


def _grafico_carteiras(at):
    """Spec e camadas (dados do Arrow por nome do dataset) do gráfico das carteiras."""
    achados = [g for g in at.get("vega_lite_chart") if str(json.loads(g.proto.spec).get("title", "")).startswith(TITULO)]
    assert len(achados) == 1
    proto = achados[0].proto
    datasets = {
        d.name: pa.ipc.open_stream(d.data.data).read_all().to_pydict() for d in proto.datasets
    }
    return json.loads(proto.spec), list(datasets.values())


def _tabela(at, coluna):
    tabelas = [df.value for df in at.dataframe if coluna in df.value.columns]
    assert tabelas, coluna
    return tabelas


def _metricas(at) -> pd.DataFrame:
    (tabela,) = _tabela(at, "Diferença com − sem taxa")
    return tabela.set_index("Carteira")


def _placar(at) -> dict[str, str]:
    return {m.label: m.value for m in at.metric}


# ---------------------------------------------------------------- abas e gráfico (RF-24)


def test_abas_carteiras_e_placar_renderizam(painel):
    at, _, _ = painel()
    app = _carregar_modulo()
    assert [t.label for t in at.tabs] == list(app.ABAS)
    assert app.ABAS[-2:] == ("Carteiras", "Placar da turma")
    assert [o for o in at.radio(key="taxa_carteiras").options] == ["com taxa de venda (15%)", "sem taxa (0%)"]


def test_grafico_com_referencia_em_1000_e_dias_marcados(painel):
    at, _, _ = painel()
    spec, camadas = _grafico_carteiras(at)
    assert spec["title"] == f"{TITULO}, com taxa de venda (15%)"
    marcas = [c["mark"]["type"] for c in spec["layer"]]
    assert marcas == ["line", "rule", "point"]
    assert spec["layer"][0]["encoding"]["x"]["axis"]["format"] == "%d/%m"

    linhas = next(d for d in camadas if "carteira" in d and "marca" in d and len(d["data"]) > 10)
    assert set(linhas["carteira"]) == {"selado", "cesta_raras", "propria", "dolar", "cdi"}
    referencia = next(d for d in camadas if "referencia" in d)
    assert referencia["referencia"] == [1000.0]

    marcados = next(d for d in camadas if "marca" in d and len(d["data"]) <= 10)
    pontos = {(d.date(), c): m for d, c, m in zip(marcados["data"], marcados["carteira"], marcados["marca"])}
    # 03/11: carta 20 sem preço só na cesta_raras; 04/11: CDI de 03/11 pendente em todas
    assert pontos[(DIAS[2], "cesta_raras")] == "preço carregado"
    assert all(pontos[(DIAS[3], c)] == "CDI pendente" for c in ("selado", "cesta_raras", "propria", "dolar", "cdi"))
    assert len(pontos) == 6

    # valores conferidos no docstring: dolar 998,00 e cdi 1000 → 1000,50
    por = {(d.date(), c): v for d, c, v in zip(linhas["data"], linhas["carteira"], linhas["valor"])}
    assert por[(DIAS[0], "dolar")] == pytest.approx(998.0)
    assert por[(DIAS[3], "cdi")] == pytest.approx(1000.5)
    assert por[(DIAS[3], "selado")] == por[(DIAS[3], "cdi")]


def test_seletor_sem_taxa_troca_o_grafico_e_a_tabela(painel):
    at, _, _ = painel()
    com = _metricas(at)
    at.radio(key="taxa_carteiras").set_value("sem taxa (0%)")
    at.run()
    assert not at.exception, at.exception
    spec, _ = _grafico_carteiras(at)
    assert spec["title"] == f"{TITULO}, sem taxa (0%)"
    sem = _metricas(at)
    assert sem.loc["cesta_raras", "Retorno acumulado"] == com.loc["cesta_raras", "Retorno sem taxa (0%)"]
    assert com.loc["cesta_raras", "Retorno acumulado"] == com.loc["cesta_raras", "Retorno com taxa (15%)"]
    assert sem.loc["cesta_raras", "Retorno acumulado"] != com.loc["cesta_raras", "Retorno acumulado"]


# ---------------------------------------------------------------- métricas (RF-25)


def test_metricas_com_e_sem_taxa_lado_a_lado(painel):
    at, _, _ = painel()
    m = _metricas(at)
    assert list(m.index) == ["selado", "cesta_raras", "propria", "dolar", "cdi"]
    # diferença com − sem taxa: zero em dolar e cdi (e na selado, só caixa); negativa na cesta e na propria
    for c in ("dolar", "cdi", "selado"):
        assert m.loc[c, "Diferença com − sem taxa"] == "0,00 p.p."
    for c in ("cesta_raras", "propria"):
        assert m.loc[c, "Diferença com − sem taxa"].startswith("-")
    # cdi: retorno 1000,50 / 1000 − 1 = 0,05%; excesso sobre ela mesma 0; dolar: 998 / 1000 − 1 = −0,20%
    assert m.loc["cdi", "Retorno acumulado"] == "0,05%"
    assert m.loc["cdi", "Excesso sobre o CDI"] == "0,00%"
    assert m.loc["cdi", "Valor no último dia"] == "R$ 1.000,50"
    assert m.loc["dolar", "Retorno acumulado"] == "-0,20%"
    assert m.loc["dolar", "Perda máxima"] == "0,00%"
    assert m.loc["cesta_raras", "Dias com preço carregado"] == "1"
    assert m.loc["selado", "Dias com preço carregado"] == "0"


def test_formatar_pp_sem_menos_zero():
    app = _carregar_modulo()
    assert app.formatar_pp(-0.12) == "-12,00 p.p."
    assert app.formatar_pp(-0.0) == "0,00 p.p."
    assert app.formatar_pp(-1e-15) == "0,00 p.p."
    assert app.formatar_pp(None) == "—"


# ---------------------------------------------------------------- composição (ADR-005, ADR-006)


def test_composicao_selado_com_zero_unidades_e_tudo_em_caixa(painel):
    at, _, _ = painel()
    tabelas = _tabela(at, "Unidades")
    selado = next(t for t in tabelas if "Destined Rivals Booster Box" in set(t["Item"]))
    box = selado[selado["Item"] == "Destined Rivals Booster Box"].iloc[0]
    assert box["Unidades"] == "0"
    assert box["Preço de compra"] == "R$ 1.250,00"  # 250 × 5,00
    assert box["Custo"] == "R$ 0,00"
    assert box["Sobra"] == "R$ 1.000,00"
    assert selado[selado["Item"] == "Caixa"].iloc[0]["Caixa"] == "R$ 1.000,00"
    avisos = [i.value for i in at.info]
    assert any("0 unidades" in a and "R$ 1.250,00" in a and "ADR-006" in a for a in avisos)
    markdown = [m.value for m in at.markdown]
    assert any(m.startswith("**selado**: Compra o booster box") for m in markdown)
    assert any(m.startswith("**propria**:") and "ADR-005" in m for m in markdown)


def test_composicao_cesta_raras_e_propria(painel):
    at, _, _ = painel()
    tabelas = _tabela(at, "Unidades")
    cesta = next(t for t in tabelas if "Carta 11" in set(t["Item"]) and "Carta 01" not in set(t["Item"]))
    assert len(cesta) == 11  # dez cartas e o caixa; Code Card fora
    assert "Code Card" not in set(cesta["Item"])
    # Carta 11: US$ 17 × 5,00 = R$ 85,00 → 1 unidade, sobra R$ 15,00
    c11 = cesta[cesta["Item"] == "Carta 11"].iloc[0]
    assert (c11["Unidades"], c11["Preço de compra"], c11["Sobra"]) == ("1", "R$ 85,00", "R$ 15,00")
    propria = next(t for t in tabelas if "Destined Rivals Elite Trainer Box" in set(t["Item"]))
    # Elite Trainer Box: US$ 50 × 5,00 = R$ 250,00 → 2 unidades em R$ 500,00
    etb = propria[propria["Item"] == "Destined Rivals Elite Trainer Box"].iloc[0]
    assert (etb["Unidades"], etb["Custo"]) == ("2", "R$ 500,00")
    # cinco Illustration Rare de maior preço: Cartas 02 a 06
    assert {"Carta 02", "Carta 03", "Carta 04", "Carta 05", "Carta 06"} <= set(propria["Item"])
    assert "Carta 01" not in set(propria["Item"])


def test_propria_com_regra_pendente_vira_aviso_sem_quebrar(painel):
    at, _, _ = painel(regra_propria=False)
    avisos = [w.value for w in at.warning]
    assert any("propria" in a and "regra pendente" in a for a in avisos)
    m = _metricas(at)
    assert m.loc["propria", "Status"] == "regra pendente"
    assert m.loc["propria", "Retorno acumulado"] == "—"
    assert m.loc["propria", "Diferença com − sem taxa"] == "—"
    _, camadas = _grafico_carteiras(at)
    linhas = next(d for d in camadas if "carteira" in d and len(d["data"]) > 10)
    assert "propria" not in set(linhas["carteira"])


# ---------------------------------------------------------------- placar (RF-28)


def test_placar_com_tres_colecoes(painel):
    at, _, _ = painel()
    placar = _placar(at)
    assert placar["Selado acima da cdi"] == "2 de 3"
    assert placar["Cesta_raras acima da dolar"] == "1 de 3"
    assert placar["Menor perda máxima (cesta_raras)"] == "OUTB"
    assert at.selectbox(key="carteira_perda").value == "cesta_raras"
    avisos = [w.value for w in at.warning]
    assert not any(AVISO_SO_DRI in a for a in avisos)
    assert any("período diferente" in a and "OUTB (02/11 a 05/11)" in a and "OUTA" not in a for a in avisos)
    assert any("sem gold_turma" in a and "OUTC" in a for a in avisos)
    (tabela,) = _tabela(at, "Selado acima da cdi")
    linhas = tabela.set_index("Coleção")
    assert linhas.loc["DRI", "Selado acima da cdi"] == "não"  # empate com a cdi não conta
    assert linhas.loc["OUTA", "Perda máxima cesta_raras"] == "10,00%"
    assert linhas.loc["OUTB", "Perda máxima cesta_raras"] == "0,00%"


def test_placar_seletor_da_perda_maxima(painel):
    at, _, _ = painel()
    at.selectbox(key="carteira_perda").set_value("selado")
    at.run()
    assert not at.exception, at.exception
    # selado: DRI 0% (só caixa), OUTB 1%, OUTA (1100 − 1050) / 1100 ≈ 4,55%
    assert _placar(at)["Menor perda máxima (selado)"] == "DRI"


def test_placar_so_com_a_dri_avisa(painel):
    at, _, _ = painel(com_outras=False)
    avisos = [w.value for w in at.warning]
    assert any(AVISO_SO_DRI in a for a in avisos)
    placar = _placar(at)
    assert placar["Selado acima da cdi"] == "0 de 1"
    assert placar["Cesta_raras acima da dolar"] == "0 de 1"
    assert placar["Menor perda máxima (cesta_raras)"] == "DRI"
    (tabela,) = _tabela(at, "Selado acima da cdi")
    assert list(tabela["Coleção"]) == ["DRI"]


def test_placar_funcao_pura_empate_e_denominador():
    app = _carregar_modulo()
    linhas = []
    for gid, sel, cdi in ((1, 1010.0, 1010.0), (2, 1020.0, 1010.0)):
        for c, v in (("selado", sel), ("cdi", cdi), ("cesta_raras", 1000.0), ("dolar", None)):
            linhas.append({"data": DIAS[0], "group_id": gid, "carteira": c, "valor_brl": 1000.0,
                           "retorno_acumulado": 0.0, "taxa_venda": 0.0})
            linhas.append({"data": DIAS[1], "group_id": gid, "carteira": c, "valor_brl": v,
                           "retorno_acumulado": None if v is None else v / 1000 - 1, "taxa_venda": 0.0})
    placar = app.placar_turma(pd.DataFrame(linhas))
    assert placar["selado_cdi"] == (1, 2)  # empate no group_id 1 não conta
    assert placar["cesta_dolar"] == (0, 0)  # dolar sem valor: nenhuma coleção comparável
    assert placar["menor_perda"] == [1, 2]  # cesta 1000 → 1000 nas duas: empate, entram as duas


# ---------------------------------------------------------------- só leitura


def test_painel_nao_grava_nada(painel):
    def _hashes(*pastas):
        return {
            str(p.relative_to(pasta)): hashlib.sha256(p.read_bytes()).hexdigest()
            for pasta in pastas for p in sorted(pasta.rglob("*")) if p.is_file()
        }

    at, pasta, turma = painel()
    antes = _hashes(pasta, turma)
    at.radio(key="taxa_carteiras").set_value("sem taxa (0%)")
    at.selectbox(key="carteira_perda").set_value("selado")
    at.run()
    assert not at.exception
    assert _hashes(pasta, turma) == antes
