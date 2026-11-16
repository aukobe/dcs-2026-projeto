"""Painel (Streamlit): base comum das seções (T-45; RF-14, RF-20, RF-21).

O painel **só lê** a gold da DRI em `gold/group_id=24269/<tabela>.parquet`
(`fato_preco_diario`, `dim_produto`, `dim_data`, `dim_colecao`): nunca grava
nem apaga nada (RNF-03). A leitura vai ao servidor S3 de `MINIO_ENDPOINT` pela
conexão DuckDB de `tcg.lake.duckdb` (data lake da turma ou MinIO local, ADR-008).

Gancho de teste e de desenvolvimento: se a variável opcional `PAINEL_GOLD_DIR`
apontar para uma pasta com os mesmos `<tabela>.parquet`, a gold é lida dessa
pasta e o S3 não é usado.

Seções das perguntas (T-46; RF-15 a RF-19, RF-22), uma aba por pergunta, com
as métricas vindas de `tcg.gold.perguntas` (o app não recalcula nada): os
DataFrames da gold são registrados como views numa conexão DuckDB em memória
(`conectar_gold`). P3, P4 e P5 avisam quando faltam outras coleções (RF-22).
Valores em formato brasileiro (`formatar_moeda`, `formatar_percentual`) e datas
em dd/mm.

Peças reutilizáveis pelas seções das perguntas (T-45):
- moeda: reais por padrão, opção em dólar (`escolher_moeda`, RF-14);
- filtro de preço mínimo no primeiro dia, estritamente acima do mínimo, com o
  padrão de cada pergunta (`filtro_preco_minimo`, `aplicar_filtro_preco`, RF-14);
- aviso de período curto (`aviso_periodo_curto`, RF-21);
- séries interrompidas nas lacunas, sem ponto interpolado
  (`completar_calendario`, `grafico_serie`, RF-21);
- imagem e link do produto, com "imagem indisponível" e "link indisponível"
  (`mostrar_produto`, RF-20).

Carteiras e placar da turma (T-47; RF-24, RF-25, RF-28): a aba "Carteiras"
lê `composicao_carteira`, `liquidacao_carteira`, `liquidacao_item` e
`metricas_carteira` da gold da DRI (gravadas pelo `make gold`, T-44), sem
recalcular carteira nenhuma; a aba "Placar da turma" lê
`gold_turma/carteira/*/carteira.parquet` de todas as coleções, somente leitura,
e só agrega retorno no último dia e perda máxima. Gancho de teste e de
desenvolvimento: `PAINEL_GOLD_TURMA_DIR` aponta para uma pasta com
`group_id=<id>/carteira.parquet`; com `PAINEL_GOLD_DIR` e sem ele, o placar não
vai ao S3 e avisa que a gold_turma não está configurada.

Executado com `make painel` (`streamlit run dashboard/app.py`); o `main()` só
roda quando o arquivo é o script principal, para que as funções possam ser
importadas.
"""

from __future__ import annotations

import datetime as dt
import os
import re
from pathlib import Path

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

from tcg.config import ler_parametros
from tcg.gold.carteiras import CARTEIRAS, ORCAMENTO, STATUS_REGRA_PENDENTE, VALOR_POR_CARTA
from tcg.gold.metricas_carteira import perda_maxima
from tcg.gold.perguntas import (
    p1_rankings,
    p2_indice,
    p3_indice,
    p4_concentracao,
    p5_retorno_volatilidade,
)

GROUP_ID_DRI = 24269
PREFIXO_GOLD = f"gold/group_id={GROUP_ID_DRI}"
TABELAS_GOLD = (
    "fato_preco_diario",
    "fato_cambio_diario",
    "dim_produto",
    "dim_data",
    "dim_colecao",
)
VARIAVEL_GOLD_LOCAL = "PAINEL_GOLD_DIR"
# Tabelas das carteiras (T-44): opcionais; sem elas, a aba "Carteiras" só avisa
TABELAS_CARTEIRA = ("composicao_carteira", "liquidacao_carteira", "liquidacao_item", "metricas_carteira")
VARIAVEL_GOLD_TURMA_LOCAL = "PAINEL_GOLD_TURMA_DIR"
PREFIXO_GOLD_TURMA = "gold_turma/carteira"
COLUNAS_GOLD_TURMA = ("data", "group_id", "carteira", "valor_brl", "retorno_acumulado", "taxa_venda")

MOEDAS = ("reais", "dólar")
COLUNA_MOEDA = {"reais": "market_price_brl", "dólar": "market_price"}
SIMBOLO_MOEDA = {"reais": "R$", "dólar": "US$"}

_PARAMETROS = ler_parametros()
PRECO_MINIMO_PADRAO = {
    "P1": float(_PARAMETROS.preco_minimo_p1_usd),
    "P5": float(_PARAMETROS.preco_minimo_p5_usd),
}

AVISO_IMAGEM = "imagem indisponível"
AVISO_LINK = "link indisponível"
AVISO_OUTRAS_COLECOES = (
    "Faltam dados de outras coleções: exibindo só a DRI (RF-22). "
    "A comparação entre coleções fica parcial até outras silvers estarem no bucket."
)
SERIE_P2_SELADOS = "Selados (cesta fixa)"
SERIE_P2_RARAS = "Double Rare em diante (cesta fixa)"
# Legenda abaixo do gráfico e sem limite de largura do rótulo: nada aparece cortado
LEGENDA_INTEIRA = alt.Legend(orient="bottom", direction="vertical", labelLimit=0)
LEGENDA_DIREITA = alt.Legend(orient="right", labelLimit=0)
# Altura fixa de todos os gráficos: com `width="stretch"` e sem altura, na tela normal a
# área de plotagem das carteiras ficava espremida a uma linha, sem eixo y visível.
ALTURA_GRAFICO = 420
ABAS = (
    "Itens", "P1: alta e queda", "P2: selados × raras", "P3: coleções", "P4: concentração", "P5: risco",
    "Carteiras", "Placar da turma",
)
AVISO_PLACAR_SO_DRI = (
    "Faltam dados de outras coleções na gold_turma: o placar mostra só a DRI (RF-28). "
    "Ele fica completo quando as outras coleções gravarem `gold_turma/carteira/`."
)
REGRAS_CARTEIRAS = {
    "selado": "Compra o booster box da coleção com R$ 1.000,00, em unidades inteiras, ao preço do "
    "primeiro dia; só se ele não tiver preço, o selado de maior preço (ADR-006); a sobra fica em caixa.",
    "cesta_raras": "R$ 100,00 em cada um dos dez itens de carta (sem Code Card) de maior market_price "
    "no primeiro dia, em unidades inteiras; a sobra fica em caixa.",
    "propria": "R$ 500,00 no selado de maior preço de compra até R$ 500,00 e R$ 100,00 em cada uma das "
    "cinco Illustration Rare de maior market_price no primeiro dia (ADR-005); a sobra fica em caixa.",
    "dolar": "R$ 1.000,00 convertidos em dólar pela PTAX de venda do primeiro dia e avaliados pela "
    "PTAX de compra de cada dia.",
    "cdi": "R$ 1.000,00 rendendo o CDI em cada dia útil.",
}


# ---------------------------------------------------------------- leitura da gold


def _literal(valor: str) -> str:
    return "'" + str(valor).replace("'", "''") + "'"


def _ler_local(pasta: Path) -> dict[str, pd.DataFrame]:
    """Tabelas obrigatórias da gold e, se existirem, as das carteiras."""
    con = duckdb.connect()
    try:
        tabelas = [*TABELAS_GOLD, *(t for t in TABELAS_CARTEIRA if (pasta / f"{t}.parquet").exists())]
        return {
            tabela: con.sql(
                f"SELECT * FROM read_parquet({_literal(pasta / f'{tabela}.parquet')}, "
                "hive_partitioning = false)"
            ).df()
            for tabela in tabelas
        }
    finally:
        con.close()


def _ler_s3() -> dict[str, pd.DataFrame]:
    from tcg.config import ler_config_minio
    from tcg.lake.duckdb import caminho_s3, conectar

    config = ler_config_minio()
    con = conectar(config)

    def ler(tabela: str) -> pd.DataFrame:
        caminho = caminho_s3(config.bucket, f"{PREFIXO_GOLD}/{tabela}.parquet")
        return con.sql(f"SELECT * FROM read_parquet({_literal(caminho)}, hive_partitioning = false)").df()

    try:
        gold = {tabela: ler(tabela) for tabela in TABELAS_GOLD}
        for tabela in TABELAS_CARTEIRA:  # opcionais: ausentes antes do primeiro `make gold` com carteiras
            try:
                gold[tabela] = ler(tabela)
            except duckdb.Error:
                pass
        return gold
    finally:
        con.close()


@st.cache_data(ttl=3600, show_spinner="Lendo a gold...")
def carregar_gold(fonte: str) -> dict[str, pd.DataFrame]:
    """Tabelas da gold, só leitura. `fonte` é uma pasta local ou `"s3"`."""
    return _ler_s3() if fonte == "s3" else _ler_local(Path(fonte))


def fonte_gold() -> str:
    pasta = os.environ.get(VARIAVEL_GOLD_LOCAL, "").strip()
    return pasta or "s3"


def _sql_gold_turma(origem: str) -> str:
    colunas = ", ".join(c if c != "data" else "CAST(data AS DATE) AS data" for c in COLUNAS_GOLD_TURMA)
    return (
        f"SELECT {colunas} FROM read_parquet({_literal(origem)}, "
        "hive_partitioning = false, union_by_name = true) ORDER BY group_id, carteira, data"
    )


def _gold_turma_vazia() -> pd.DataFrame:
    return pd.DataFrame(columns=list(COLUNAS_GOLD_TURMA))


@st.cache_data(ttl=3600, show_spinner="Lendo a gold_turma...")
def carregar_gold_turma(fonte: str) -> pd.DataFrame:
    """`gold_turma/carteira/` de todas as coleções, só leitura (RF-28).

    `fonte` é uma pasta local com `group_id=<id>/carteira.parquet` ou `"s3"`.
    Sem nenhum arquivo, devolve uma tabela vazia; só as colunas do contrato.
    """
    if fonte != "s3":
        pasta = Path(fonte)
        if not any(pasta.glob("*/carteira.parquet")):
            return _gold_turma_vazia()
        con = duckdb.connect()
        try:
            return con.sql(_sql_gold_turma(str(pasta / "*" / "carteira.parquet"))).df()
        finally:
            con.close()

    from tcg.config import ler_config_minio
    from tcg.lake.duckdb import caminho_s3, conectar

    config = ler_config_minio()
    con = conectar(config)
    try:
        return con.sql(_sql_gold_turma(caminho_s3(config.bucket, f"{PREFIXO_GOLD_TURMA}/*/carteira.parquet"))).df()
    except duckdb.IOException as erro:
        if "No files found" in str(erro):
            return _gold_turma_vazia()
        raise
    finally:
        con.close()


def fonte_gold_turma() -> str | None:
    """Pasta do gancho, `"s3"` ou None (gold local sem gold_turma configurada)."""
    pasta = os.environ.get(VARIAVEL_GOLD_TURMA_LOCAL, "").strip()
    if pasta:
        return pasta
    if os.environ.get(VARIAVEL_GOLD_LOCAL, "").strip():
        return None
    return "s3"


# ---------------------------------------------------------------- formatação pt-BR


_CIFRAO_SEM_ESCAPE = re.compile(r"(?<!\\)\$")


def escapar_cifrao(corpo) -> str:
    """Escapa o "$" ainda sem escape: no Markdown do Streamlit, "R$ ... R$" vira fórmula LaTeX."""
    return _CIFRAO_SEM_ESCAPE.sub(r"\\$", str(corpo))


class _TextoSeguro:
    """Delega `caption`, `markdown`, `info` etc. ao `st`, escapando o cifrão do corpo (T-47)."""

    def __getattr__(self, nome):
        funcao = getattr(st, nome)

        def chamar(corpo, *args, **kwargs):
            return funcao(escapar_cifrao(corpo), *args, **kwargs)

        return chamar


texto = _TextoSeguro()


def _nulo(valor) -> bool:
    return valor is None or bool(pd.isna(valor))


def formatar_numero(valor, casas: int = 2) -> str:
    """1776.98 → "1.776,98"; nulo → "—"."""
    if _nulo(valor):
        return "—"
    texto = f"{float(valor):,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def formatar_moeda(valor, simbolo: str = "R$") -> str:
    """1776.98 → "R$ 1.776,98"; −2.5 → "-R$ 2,50"; nulo → "—"."""
    if _nulo(valor):
        return "—"
    sinal = "-" if float(valor) < 0 else ""
    return f"{sinal}{simbolo} {formatar_numero(abs(float(valor)))}"


def formatar_percentual(fracao, casas: int = 2) -> str:
    """0.1234 → "12,34%"; −0.01 → "-1,00%"; nulo → "—"."""
    if _nulo(fracao):
        return "—"
    return f"{formatar_numero(float(fracao) * 100, casas)}%"


def formatar_pp(diferenca, casas: int = 2) -> str:
    """Diferença de frações em pontos percentuais: −0.12 → "-12,00 p.p."; 0 → "0,00 p.p."."""
    if _nulo(diferenca):
        return "—"
    valor = float(diferenca) * 100
    if abs(valor) < 0.5 * 10 ** -casas:
        valor = 0.0  # sem "-0,00"
    return f"{formatar_numero(valor, casas)} p.p."


def formatar_data(valor) -> str:
    """Data → "03/11"; nulo → "—"."""
    if _nulo(valor):
        return "—"
    return pd.Timestamp(valor).strftime("%d/%m")


def _expr_pt(formato: str) -> str:
    """Expressão Vega que formata `datum.value` com `formato` e troca ponto e vírgula."""
    return (
        f"replace(replace(replace(format(datum.value, '{formato}'), regexp(',', 'g'), '_'), "
        "regexp('[.]', 'g'), ','), regexp('_', 'g'), '.')"
    )


def eixo_numero(titulo: str, formato: str = ",.2f") -> alt.Axis:
    return alt.Axis(title=titulo, labelExpr=_expr_pt(formato))


# Datas em UTC: o Arrow manda meia-noite UTC; em horário local o dia mudaria.
def eixo_data(datas) -> dict:
    """Eixo x de datas em dd/mm com um rótulo por dia, sem repetição.

    Os ticks são os próprios dias dos dados (`values`), em vez dos ticks
    automáticos do Vega, que com poucos dias caem a cada 12 h e repetem a data.
    Com muitos dias, `labelOverlap` esconde os rótulos que se sobrepõem.
    """
    dias = sorted({pd.Timestamp(d).date() for d in datas if not _nulo(d)})
    valores = [{"year": d.year, "month": d.month, "date": d.day, "utc": True} for d in dias]
    return {
        "timeUnit": "utcyearmonthdate",
        "title": "Data",
        "axis": alt.Axis(format="%d/%m", labelAngle=0, values=valores, labelOverlap=True),
    }


TOOLTIP_DATA = alt.Tooltip("data:T", timeUnit="utcyearmonthdate", title="Data", format="%d/%m/%Y")


# ---------------------------------------------------------------- funções puras


def periodo(fato: pd.DataFrame, group_id: int = GROUP_ID_DRI) -> tuple[dt.date, dt.date]:
    """Primeiro e último dia com preço da coleção."""
    datas = pd.to_datetime(fato.loc[fato["group_id"] == group_id, "data"])
    return datas.min().date(), datas.max().date()


def tabela_itens(
    fato: pd.DataFrame,
    dim_produto: pd.DataFrame,
    moeda: str,
    group_id: int = GROUP_ID_DRI,
) -> pd.DataFrame:
    """Cartas da coleção (produto × acabamento) com preço no primeiro e no último dia.

    `usd_inicial` (dólar, primeiro dia) alimenta o filtro de preço mínimo;
    `preco_inicial` e `preco_final` estão na moeda escolhida. Item sem preço num
    dos dois dias fica com nulo; nada é preenchido.
    """
    coluna = COLUNA_MOEDA[moeda]
    primeiro, ultimo = periodo(fato, group_id)
    f = fato[fato["group_id"] == group_id].copy()
    f["data"] = pd.to_datetime(f["data"]).dt.date
    chave = ["product_id", "acabamento"]
    dia1 = f[f["data"] == primeiro]
    ini = dia1[chave].assign(usd_inicial=dia1["market_price"], preco_inicial=dia1[coluna])
    fim = f[f["data"] == ultimo][chave + [coluna]].rename(columns={coluna: "preco_final"})
    cartas = dim_produto[
        (dim_produto["group_id"] == group_id) & (dim_produto["tipo_produto"] == "carta")
    ][["product_id", "nome", "raridade", "image_url", "url"]]
    itens = f[chave].drop_duplicates().merge(cartas, on="product_id", how="inner")
    itens = itens.merge(ini, on=chave, how="left").merge(fim, on=chave, how="left")
    return itens.sort_values(
        ["preco_final", "product_id", "acabamento"], ascending=[False, True, True],
        na_position="last",
    ).reset_index(drop=True)


def aplicar_filtro_preco(itens: pd.DataFrame, minimo_usd: float) -> pd.DataFrame:
    """Mantém só itens com preço em dólar no primeiro dia estritamente acima do mínimo (RF-14)."""
    return itens[itens["usd_inicial"] > float(minimo_usd)].reset_index(drop=True)


def completar_calendario(serie: pd.DataFrame, dim_data: pd.DataFrame) -> pd.DataFrame:
    """Reindexa `serie` (`data`, `valor`) pelo calendário da `dim_data` (RF-21).

    Dia sem preço (sem coleta ou sem preço do item) fica com `valor` nulo: nada
    é interpolado, copiado ou estimado.
    """
    calendario = pd.DataFrame({"data": pd.to_datetime(dim_data["data"])}).drop_duplicates()
    s = serie.assign(data=pd.to_datetime(serie["data"]))[["data", "valor"]]
    return calendario.merge(s, on="data", how="left").sort_values("data").reset_index(drop=True)


def completar_series(longo: pd.DataFrame, dim_data: pd.DataFrame, coluna: str = "serie") -> pd.DataFrame:
    """Como `completar_calendario`, por série, do primeiro ao último dia de cada uma (RF-21)."""
    calendario = pd.Series(pd.to_datetime(dim_data["data"]).drop_duplicates().sort_values().values)
    partes = []
    for nome, grupo in longo.groupby(coluna, sort=False):
        grupo = grupo.assign(data=pd.to_datetime(grupo["data"]))
        dias = calendario[(calendario >= grupo["data"].min()) & (calendario <= grupo["data"].max())]
        parte = pd.DataFrame({"data": dias.values}).merge(
            grupo.drop(columns=[coluna]), on="data", how="left"
        )
        parte[coluna] = nome
        partes.append(parte)
    if not partes:
        return longo.assign(data=pd.to_datetime(longo["data"]))
    return pd.concat(partes, ignore_index=True)


def conectar_gold(gold: dict[str, pd.DataFrame]) -> duckdb.DuckDBPyConnection:
    """Conexão DuckDB em memória com cada tabela da gold como view (só leitura).

    A coluna `data` volta a ser DATE: o pandas a traz como timestamp, e as
    funções de `tcg.gold.perguntas` contam dias de calendário.
    """
    con = duckdb.connect()
    for tabela, df in gold.items():
        con.register(f"_df_{tabela}", df)
        selecao = "* REPLACE (CAST(data AS DATE) AS data)" if "data" in df.columns else "*"
        con.execute(f"CREATE VIEW {tabela} AS SELECT {selecao} FROM _df_{tabela}")
    return con


def rotulos_colecoes(dim_colecao: pd.DataFrame, group_ids) -> dict[int, str]:
    """Sigla (ou nome) de cada coleção; sem linha na `dim_colecao`, "group_id N"."""
    rotulos = {}
    for gid in group_ids:
        linha = dim_colecao[dim_colecao["group_id"] == gid]
        rotulo = None
        if len(linha):
            for campo in ("sigla", "nome"):
                if campo in linha.columns and not _nulo(linha[campo].iloc[0]):
                    rotulo = str(linha[campo].iloc[0])
                    break
        rotulos[int(gid)] = rotulo or f"group_id {int(gid)}"
    return rotulos


def tabela_ranking(ranking: pd.DataFrame, moeda: str) -> pd.DataFrame:
    """Linhas da P1 prontas para exibição, com preços e parcelas formatados (RF-15)."""
    simbolo = SIMBOLO_MOEDA[moeda]
    ini, fim = ("brl_inicial", "brl_final") if moeda == "reais" else ("usd_inicial", "usd_final")
    return pd.DataFrame(
        {
            "Imagem": ranking["image_url"],
            "Produto": ranking["nome"],
            "Acabamento": ranking["acabamento"],
            "Raridade": ranking["raridade"],
            f"Preço inicial ({simbolo})": ranking[ini].map(lambda v: formatar_moeda(v, simbolo)),
            f"Preço atual ({simbolo})": ranking[fim].map(lambda v: formatar_moeda(v, simbolo)),
            "Variação em reais": ranking["r_brl"].map(formatar_percentual),
            "Carta (dólar)": ranking["r_usd"].map(formatar_percentual),
            "Câmbio": ranking["r_cambio"].map(formatar_percentual),
            "Cruzado": ranking["r_cruzado"].map(formatar_percentual),
            "Link": ranking["url"],
        }
    )


# ---------------------------------------------------------------- componentes


def escolher_moeda() -> str:
    """Radio da moeda na barra lateral; padrão reais (RF-14)."""
    return st.sidebar.radio("Moeda", MOEDAS, index=0, key="moeda", horizontal=True)


def filtro_preco_minimo(pergunta: str) -> float:
    """Preço mínimo em US$ no primeiro dia, com o padrão da pergunta (RF-14)."""
    return float(
        st.sidebar.number_input(
            escapar_cifrao(f"Preço mínimo no primeiro dia (US$), {pergunta}"),
            min_value=0.0,
            value=PRECO_MINIMO_PADRAO[pergunta],
            step=0.5,
            key=f"preco_minimo_{pergunta}",
            help="Mantém só itens com preço estritamente acima do mínimo no primeiro dia.",
        )
    )


def aviso_periodo_curto(primeiro: dt.date, ultimo: dt.date) -> None:
    """Aviso de que o período é curto e não sustenta previsão (RF-21)."""
    dias = (ultimo - primeiro).days + 1
    texto.warning(
        f"Período de {dias} dias ({primeiro:%d/%m/%Y} a {ultimo:%d/%m/%Y}): "
        "o período é curto e não sustenta previsão. Dias sem coleta aparecem "
        "como interrupção na linha, sem ponto interpolado."
    )


def grafico_linhas(
    dados: pd.DataFrame,
    titulo: str,
    rotulo_y: str,
    cor: str | None = None,
    formato_y: str = ",.2f",
    destaque: bool = False,
    zero: bool = True,
    legenda: alt.Legend | None = None,
) -> alt.Chart:
    """Linhas por data que se interrompem nos valores nulos (RF-21).

    `dados` tem `data` e `valor` (e a coluna `cor`, se houver). Com `destaque`,
    usa as colunas `espessura`, `opacidade` e `tipo` (coleção ou PTAX). Com
    `zero=False`, o eixo y não começa em 0 (índices em torno de 100). `legenda`
    substitui a legenda padrão da cor.
    """
    dados = dados.assign(valor_fmt=dados["valor"].map(lambda v: formatar_numero(v)))
    tooltip = [TOOLTIP_DATA, alt.Tooltip("valor_fmt:N", title=rotulo_y)]
    codificacao = {
        "x": alt.X("data:T", **eixo_data(dados["data"])),
        "y": alt.Y("valor:Q", axis=eixo_numero(rotulo_y, formato_y), scale=alt.Scale(zero=zero)),
    }
    if cor:
        codificacao["color"] = alt.Color(f"{cor}:N", title=None, **({"legend": legenda} if legenda else {}))
        tooltip.insert(0, alt.Tooltip(f"{cor}:N", title="Série"))
    if destaque:
        codificacao["strokeWidth"] = alt.StrokeWidth("espessura:Q", scale=None, legend=None)
        codificacao["opacity"] = alt.Opacity("opacidade:Q", scale=None, legend=None)
        codificacao["strokeDash"] = alt.StrokeDash(
            "tipo:N", scale=alt.Scale(domain=["coleção", "PTAX"], range=[[1, 0], [6, 4]]), legend=None
        )
    codificacao["tooltip"] = tooltip
    return (
        alt.Chart(dados, title=titulo, height=ALTURA_GRAFICO)
        .mark_line(point=True, invalid="break-paths-show-domains")
        .encode(**codificacao)
    )


def grafico_serie(serie: pd.DataFrame, titulo: str, rotulo_y: str, cor: str | None = None) -> None:
    """Gráfico de linha que interrompe a linha nos valores nulos (RF-21)."""
    st.altair_chart(grafico_linhas(serie, titulo, rotulo_y, cor), width="stretch")


def mostrar_produto(nome: str, image_url: str | None, url: str | None) -> None:
    """Imagem e link do produto, ou os avisos de indisponível (RF-20)."""
    if image_url is None or pd.isna(image_url) or not str(image_url).strip():
        texto.caption(AVISO_IMAGEM)
    else:
        st.image(str(image_url), caption=nome, width=200)
    if url is None or pd.isna(url) or not str(url).strip():
        texto.caption(AVISO_LINK)
    else:
        texto.markdown(f"[Ver {nome} no TCGplayer]({url})")


# ---------------------------------------------------------------- seções


def seletor_item(itens: pd.DataFrame, chave: str, rotulo=None) -> None:
    """Seletor com imagem e link do item (RF-20); padrão: o de maior preço atual."""
    if itens.empty:
        return
    itens = itens.sort_values("preco_final", ascending=False, na_position="last").reset_index(drop=True)
    rotulo = rotulo or (lambda r: f"{r['nome']} ({r['acabamento']})")
    rotulos = [rotulo(r) for _, r in itens.iterrows()]
    escolhido = st.selectbox("Item", range(len(itens)), format_func=lambda i: rotulos[i], key=chave)
    item = itens.iloc[escolhido]
    mostrar_produto(item["nome"], item["image_url"], item["url"])


def secao_itens(gold, fato, dim_produto, moeda, minimo, primeiro) -> None:
    simbolo = SIMBOLO_MOEDA[moeda]
    itens = aplicar_filtro_preco(tabela_itens(fato, dim_produto, moeda), minimo)
    texto.subheader("Cartas da coleção")
    texto.caption(f"{len(itens)} itens com preço acima de {formatar_moeda(minimo, 'US$')} em {primeiro:%d/%m/%Y}.")
    exibicao = itens[["nome", "acabamento", "raridade"]].rename(
        columns={"nome": "Produto", "acabamento": "Acabamento", "raridade": "Raridade"}
    )
    exibicao[f"Preço inicial ({simbolo})"] = itens["preco_inicial"].map(lambda v: formatar_moeda(v, simbolo))
    exibicao[f"Preço atual ({simbolo})"] = itens["preco_final"].map(lambda v: formatar_moeda(v, simbolo))
    st.dataframe(exibicao, hide_index=True, width="stretch")

    if itens.empty:
        texto.info("Nenhum item acima do preço mínimo.")
        return

    rotulos = [f"{r.nome} ({r.acabamento})" for r in itens.itertuples()]
    escolhido = st.selectbox("Item", range(len(itens)), format_func=lambda i: rotulos[i], key="item")
    item = itens.iloc[escolhido]
    coluna_imagem, coluna_serie = st.columns([1, 3])
    with coluna_imagem:
        mostrar_produto(item["nome"], item["image_url"], item["url"])
    with coluna_serie:
        f = fato[
            (fato["group_id"] == GROUP_ID_DRI)
            & (fato["product_id"] == item["product_id"])
            & (fato["acabamento"] == item["acabamento"])
        ]
        serie = completar_calendario(
            f.rename(columns={COLUNA_MOEDA[moeda]: "valor"})[["data", "valor"]], gold["dim_data"]
        )
        grafico_serie(serie, f"Preço de {item['nome']} ({item['acabamento']})", f"Preço ({simbolo})")


def secao_p1(con, moeda: str, minimo: float) -> None:
    texto.subheader("P1: cartas que mais valorizaram e desvalorizaram")
    texto.caption(
        f"Variação em reais do primeiro ao último dia, decomposta em carta (dólar), câmbio e "
        f"termo cruzado; só cartas sem Code Card acima de {formatar_moeda(minimo, 'US$')} no primeiro dia."
    )
    alta, queda = (r.df() for r in p1_rankings(con, "fato_preco_diario", "dim_produto", preco_minimo_usd=minimo))
    configuracao = {
        "Imagem": st.column_config.ImageColumn("Imagem"),
        "Link": st.column_config.LinkColumn("Link", display_text="TCGplayer"),
    }
    for titulo, ranking in (("Maiores altas", alta), ("Maiores quedas", queda)):
        texto.markdown(f"**{titulo}**")
        if ranking.empty:
            texto.info(f"Nenhum item em {titulo.lower()}.")
            continue
        st.dataframe(tabela_ranking(ranking, moeda), hide_index=True, width="stretch", column_config=configuracao)
    detalhe = pd.concat([alta, queda], ignore_index=True)
    if not detalhe.empty:
        fim = "brl_final" if moeda == "reais" else "usd_final"
        seletor_item(detalhe.assign(preco_final=detalhe[fim]), "item_p1")


def secao_p2(con, gold, moeda: str) -> None:
    simbolo = SIMBOLO_MOEDA[moeda]
    texto.subheader("P2: selados contra cartas Double Rare em diante")
    p2 = p2_indice(con, "fato_preco_diario", "dim_produto", coluna=COLUNA_MOEDA[moeda]).df()
    if p2.empty:
        texto.info("Sem preços da DRI para a P2.")
        return
    n_sel, n_rar = int(p2["itens_selados"].iloc[0]), int(p2["itens_double_rare_mais"].iloc[0])
    texto.caption(
        f"Índice base 100 no primeiro dia, em {moeda} ({simbolo}), cestas fixas da DRI: "
        f"{n_sel} selados e {n_rar} cartas Double Rare em diante. O RF-16 usa a média dos "
        "selados e a soma das cartas; com a cesta fixa, a média é a soma dividida por um número "
        "constante de itens, e o índice é o mesmo."
    )
    longo = pd.concat(
        [
            p2[["data"]].assign(serie=SERIE_P2_SELADOS, valor=p2["indice_selados"]),
            p2[["data"]].assign(serie=SERIE_P2_RARAS, valor=p2["indice_double_rare_mais"]),
        ],
        ignore_index=True,
    )
    serie = completar_series(longo, gold["dim_data"])
    st.altair_chart(
        grafico_linhas(serie, "Índice base 100", "Índice", cor="serie", zero=False, legenda=LEGENDA_INTEIRA),
        width="stretch",
    )


def secao_p3(con, gold, moeda: str, rotulos: dict[int, str], so_dri: bool) -> None:
    texto.subheader("P3: valor da coleção em índice base 100")
    if so_dri:
        texto.warning(AVISO_OUTRAS_COLECOES)
    p3 = p3_indice(
        con, "fato_preco_diario", "dim_produto", "fato_cambio_diario", coluna=COLUNA_MOEDA[moeda]
    ).df()
    if p3.empty:
        texto.info("Sem preços para a P3.")
        return
    base = p3["data"].min()
    cestas = p3[p3["serie"] != "PTAX"].groupby("group_id")["itens_cesta"].first()
    texto.caption(
        f"Base 100 em {formatar_data(base)}, o primeiro dia comum às coleções; PTAX de venda tracejada; "
        "DRI destacada. Itens por cesta fixa: "
        + ", ".join(f"{rotulos.get(int(g), g)} {int(n)}" for g, n in cestas.items())
        + "."
    )
    nomes = {str(g): r for g, r in rotulos.items()}
    p3 = p3.assign(serie=p3["serie"].map(lambda s: nomes.get(s, "PTAX" if s == "PTAX" else f"group_id {s}")))
    destaque = p3.groupby("serie")["destaque"].any()
    serie = completar_series(p3[["data", "serie", "indice"]].rename(columns={"indice": "valor"}), gold["dim_data"])
    serie["destaque"] = serie["serie"].map(destaque).fillna(False).astype(bool)
    serie["espessura"] = serie["destaque"].map({True: 4.0, False: 1.5})
    serie["opacidade"] = serie["destaque"].map({True: 1.0, False: 0.6})
    serie["tipo"] = serie["serie"].map(lambda s: "PTAX" if s == "PTAX" else "coleção")
    st.altair_chart(
        grafico_linhas(
            serie, "Valor da coleção e PTAX (base 100)", "Índice", cor="serie", destaque=True, zero=False
        ),
        width="stretch",
    )


def secao_p4(con, rotulos: dict[int, str], so_dri: bool) -> None:
    texto.subheader("P4: concentração do valor no último dia")
    if so_dri:
        texto.warning(AVISO_OUTRAS_COLECOES)
    participacao, concentracao = (r.df() for r in p4_concentracao(con, "fato_preco_diario", "dim_produto"))
    if participacao.empty:
        texto.info("Sem preços para a P4.")
        return
    participacao = participacao.assign(
        colecao=participacao["group_id"].map(rotulos),
        participacao_fmt=participacao["participacao"].map(formatar_percentual),
        valor_fmt=participacao["valor"].map(lambda v: formatar_moeda(v, "R$")),
    )
    grafico = (
        alt.Chart(participacao, title="Participação por raridade (cartas sem Code Card)", height=ALTURA_GRAFICO)
        .mark_bar()
        .encode(
            x=alt.X("colecao:N", title="Coleção", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("participacao:Q", stack="normalize", axis=alt.Axis(title="Participação", format=".0%")),
            color=alt.Color("raridade:N", title="Raridade"),
            tooltip=[
                alt.Tooltip("colecao:N", title="Coleção"),
                alt.Tooltip("raridade:N", title="Raridade"),
                alt.Tooltip("participacao_fmt:N", title="Participação"),
                alt.Tooltip("valor_fmt:N", title="Valor"),
                alt.Tooltip("itens:Q", title="Itens"),
            ],
        )
    )
    st.altair_chart(grafico, width="stretch")
    st.dataframe(
        pd.DataFrame(
            {
                "Coleção": concentracao["group_id"].map(rotulos),
                "Último dia": concentracao["data"].map(formatar_data),
                "Itens que somam 80% do valor": concentracao["itens_80"].astype(int),
                "Itens no total": concentracao["itens_total"].astype(int),
                "Valor total (R$)": concentracao["valor_total"].map(lambda v: formatar_moeda(v, "R$")),
            }
        ),
        hide_index=True,
        width="stretch",
    )
    texto.caption("A participação usa o market_price em reais do último dia; no mesmo dia, ela não muda com a moeda.")


def secao_p5(con, moeda: str, minimo: float, rotulos: dict[int, str], so_dri: bool) -> None:
    simbolo = SIMBOLO_MOEDA[moeda]
    texto.subheader("P5: retorno contra volatilidade")
    if so_dri:
        texto.warning(AVISO_OUTRAS_COLECOES)
    p5 = p5_retorno_volatilidade(
        con, "fato_preco_diario", "dim_produto", coluna=COLUNA_MOEDA[moeda], preco_minimo_usd=minimo
    ).df()
    if p5.empty:
        texto.info("Nenhum item acima do preço mínimo para a P5.")
        return
    p5 = p5.assign(
        colecao=p5["group_id"].map(rotulos),
        retorno_fmt=p5["retorno"].map(formatar_percentual),
        volatilidade_fmt=p5["volatilidade"].map(formatar_percentual),
        preco_inicial_fmt=p5["preco_inicial"].map(lambda v: formatar_moeda(v, simbolo)),
        preco_final_fmt=p5["preco_final"].map(lambda v: formatar_moeda(v, simbolo)),
    )
    pontos = p5[p5["volatilidade"].notna()]
    sem_vol = len(p5) - len(pontos)
    texto.caption(
        f"Cartas sem Code Card acima de {formatar_moeda(minimo, 'US$')} no primeiro dia da coleção; "
        f"volatilidade = desvio-padrão amostral dos retornos diários em {moeda}, sem retornos que "
        f"atravessam lacuna. {len(pontos)} itens no gráfico"
        + (f"; {sem_vol} sem dois retornos diários válidos ficam fora." if sem_vol else ".")
    )
    if not pontos.empty:
        grafico = (
            alt.Chart(pontos, title="Retorno no período × volatilidade diária", height=ALTURA_GRAFICO)
            .mark_circle(size=80, opacity=0.8)
            .encode(
                x=alt.X("volatilidade:Q", axis=eixo_numero("Volatilidade (desvio-padrão diário)", ".1%")),
                y=alt.Y("retorno:Q", axis=eixo_numero("Retorno no período", ".0%")),
                color=alt.Color("colecao:N", title="Coleção"),
                tooltip=[
                    alt.Tooltip("nome:N", title="Item"),
                    alt.Tooltip("acabamento:N", title="Acabamento"),
                    alt.Tooltip("colecao:N", title="Coleção"),
                    alt.Tooltip("retorno_fmt:N", title="Retorno"),
                    alt.Tooltip("volatilidade_fmt:N", title="Volatilidade"),
                    alt.Tooltip("preco_inicial_fmt:N", title="Preço inicial"),
                    alt.Tooltip("preco_final_fmt:N", title="Preço atual"),
                    alt.Tooltip("image_url:N", title="image"),  # vega-tooltip mostra como imagem
                ],
            )
        )
        st.altair_chart(grafico, width="stretch")
    # só os itens do gráfico (volatilidade não nula); padrão: o de maior preço entre eles
    seletor_item(pontos, "item_p5", lambda r: f"{r['nome']} ({r['acabamento']}), {r['colecao']}")


# ---------------------------------------------------------------- carteiras (T-47)


def _ordem_carteiras(carteiras) -> list[str]:
    presentes = list(dict.fromkeys(carteiras))
    return [c for c in CARTEIRAS if c in presentes] + [c for c in presentes if c not in CARTEIRAS]


def taxas_da_gold(liquidacao: pd.DataFrame) -> tuple[float, float]:
    """(taxa do parâmetro, 0): a maior taxa_venda gravada pelo `make gold` e a taxa 0."""
    taxas = sorted(float(t) for t in liquidacao["taxa_venda"].dropna().unique())
    return (taxas[-1] if taxas else 0.0), 0.0


def marca_dia(preco_carregado, cdi_pendente) -> str | None:
    """Marcação do dia no gráfico das carteiras (RF-24)."""
    partes = [t for t, v in (("preço carregado", preco_carregado), ("CDI pendente", cdi_pendente)) if bool(v)]
    return " e ".join(partes) or None


def tabela_metricas(metricas: pd.DataFrame, taxa: float, taxa_parametro: float) -> pd.DataFrame:
    """Métricas da taxa escolhida e o retorno com e sem taxa lado a lado (RF-25).

    A diferença (com taxa − sem taxa, em p.p.) é o ponto de sensibilidade à
    taxa de venda: zero em dolar e cdi. Nada é recalculado; tudo vem da
    `metricas_carteira` da gold.
    """
    m = metricas.assign(taxa_venda=metricas["taxa_venda"].astype(float))
    linhas = []
    for carteira in _ordem_carteiras(m["carteira"]):
        da = m[m["carteira"] == carteira]
        escolhida = da[da["taxa_venda"] == taxa]
        com = da.loc[da["taxa_venda"] == taxa_parametro, "retorno_acumulado"]
        sem = da.loc[da["taxa_venda"] == 0.0, "retorno_acumulado"]
        r_com = com.iloc[0] if len(com) else None
        r_sem = sem.iloc[0] if len(sem) else None
        e = escolhida.iloc[0] if len(escolhida) else None
        dias = None if e is None or _nulo(e["dias_preco_carregado"]) else int(e["dias_preco_carregado"])
        linhas.append({
            "Carteira": carteira,
            "Status": "—" if e is None else e["status"],
            "Valor no último dia": formatar_moeda(None if e is None else e["valor_final_brl"]),
            "Retorno acumulado": formatar_percentual(None if e is None else e["retorno_acumulado"]),
            "Excesso sobre o CDI": formatar_percentual(None if e is None else e["excesso_cdi"]),
            "Perda máxima": formatar_percentual(None if e is None else e["perda_maxima"]),
            "Dias com preço carregado": "—" if dias is None else str(dias),
            f"Retorno com taxa ({formatar_percentual(taxa_parametro, 0)})": formatar_percentual(r_com),
            "Retorno sem taxa (0%)": formatar_percentual(r_sem),
            "Diferença com − sem taxa": formatar_pp(
                None if _nulo(r_com) or _nulo(r_sem) else float(r_com) - float(r_sem)
            ),
        })
    return pd.DataFrame(linhas)


def tabela_composicao(composicao: pd.DataFrame, dim_produto: pd.DataFrame, carteira: str) -> pd.DataFrame:
    """Posições de uma carteira (item, unidades, preço de compra, custo, sobra) e a linha de caixa."""
    linhas_c = composicao[composicao["carteira"] == carteira]
    nomes = dim_produto[dim_produto["group_id"] == GROUP_ID_DRI].set_index("product_id")["nome"]
    posicoes = linhas_c[linhas_c["product_id"].notna()]
    caixa = linhas_c[linhas_c["product_id"].isna()]
    saida = [
        {
            "Item": str(nomes.get(int(p.product_id), f"product_id {int(p.product_id)}")),
            "Acabamento": p.acabamento,
            "Unidades": str(int(p.unidades)),
            "Preço de compra": formatar_moeda(p.preco_compra_brl),
            "Custo": formatar_moeda(p.custo_brl),
            "Sobra": formatar_moeda(p.sobra_brl),
            "Caixa": "—",
            "Observação": (
                f"0 unidades: preço de compra acima de {formatar_moeda(p.valor_alocado_brl)}"
                if int(p.unidades) == 0 else ""
            ),
        }
        for p in posicoes.itertuples()
    ]
    if len(caixa):
        saida.append({
            "Item": "Caixa", "Acabamento": "—", "Unidades": "—", "Preço de compra": "—",
            "Custo": "—", "Sobra": "—", "Caixa": formatar_moeda(caixa["caixa_brl"].iloc[0]), "Observação": "",
        })
    return pd.DataFrame(
        saida,
        columns=["Item", "Acabamento", "Unidades", "Preço de compra", "Custo", "Sobra", "Caixa", "Observação"],
    )


_NUMERAIS = {2: "duas", 3: "três", 4: "quatro", 5: "cinco", 6: "seis", 7: "sete", 8: "oito", 9: "nove", 10: "dez"}


def aviso_cartas_sem_unidade(composicao: pd.DataFrame, carteira: str) -> str | None:
    """Aviso quando nenhuma carta da carteira cabe nos R$ 100,00 alocados (todas com 0 unidades)."""
    linhas_c = composicao[(composicao["carteira"] == carteira) & composicao["product_id"].notna()]
    cartas = linhas_c[(linhas_c["valor_alocado_brl"] - VALOR_POR_CARTA).abs() < 1e-9]
    if cartas.empty or (cartas["unidades"] > 0).any():
        return None
    n = len(cartas)
    sujeito = "A única carta não cabe" if n == 1 else f"Nenhuma das {_NUMERAIS.get(n, n)} cartas cabe"
    destino = "todo o valor ficou em caixa" if len(cartas) == len(linhas_c) else "o valor das cartas ficou em caixa"
    return f"{sujeito} em {formatar_moeda(VALOR_POR_CARTA)}; {destino}."


def dominio_y(valores, referencia: float = ORCAMENTO) -> tuple[float, float]:
    """Domínio do eixo y a partir dos dados e da referência, com folga de 5% (mínimo R$ 1,00)."""
    serie = pd.Series(valores, dtype="float64").dropna()
    minimo = min([referencia, *serie.tolist()])
    maximo = max([referencia, *serie.tolist()])
    folga = max((maximo - minimo) * 0.05, 1.0)
    return minimo - folga, maximo + folga


def grafico_carteiras(liquidacao: pd.DataFrame, taxa: float, titulo: str) -> alt.LayerChart:
    """Valor de liquidação por dia e carteira, referência em R$ 1.000,00 e dias marcados (RF-24)."""
    liq = liquidacao[(liquidacao["taxa_venda"].astype(float) == taxa) & liquidacao["valor_brl"].notna()].copy()
    liq["data"] = pd.to_datetime(liq["data"])
    liq["valor"] = liq["valor_brl"].astype(float)
    liq["valor_fmt"] = liq["valor"].map(formatar_moeda)
    liq["marca"] = [marca_dia(p, c) for p, c in zip(liq["preco_carregado"], liq["cdi_pendente"])]
    dados = liq[["data", "carteira", "valor", "valor_fmt", "marca"]]
    ordem = _ordem_carteiras(dados["carteira"])
    x = alt.X("data:T", **eixo_data(dados["data"]))
    # O mesmo `y` (campo, escala e eixo) em todas as camadas: antes, a referência usava
    # outro campo, sem escala nem eixo, e a escala compartilhada voltava a incluir o zero.
    y = alt.Y(
        "valor:Q",
        axis=alt.Axis(title="Valor de liquidação", labelExpr="'R$ ' + " + _expr_pt(",.2f")),
        scale=alt.Scale(domain=list(dominio_y(dados["valor"])), zero=False, nice=False),
    )
    cor = alt.Color("carteira:N", title="Carteira", sort=ordem, legend=LEGENDA_DIREITA)
    tooltip = [
        alt.Tooltip("carteira:N", title="Carteira"), TOOLTIP_DATA,
        alt.Tooltip("valor_fmt:N", title="Valor"), alt.Tooltip("marca:N", title="Marcação"),
    ]
    linhas = alt.Chart(dados).mark_line(point=True).encode(x=x, y=y, color=cor, tooltip=tooltip)
    referencia = (
        alt.Chart(pd.DataFrame({"valor": [ORCAMENTO], "referencia": [formatar_moeda(ORCAMENTO)]}))
        .mark_rule(strokeDash=[6, 4], color="gray")
        .encode(y=y, tooltip=[alt.Tooltip("referencia:N", title="Valor inicial")])
    )
    marcados = dados[dados["marca"].notna()]
    camadas = [linhas, referencia]
    if not marcados.empty:
        camadas.append(
            alt.Chart(marcados)
            .mark_point(shape="diamond", size=160, filled=False, strokeWidth=2, color="black")
            .encode(x=x, y=y, tooltip=tooltip)
        )
    return alt.layer(*camadas, title=titulo, height=ALTURA_GRAFICO).resolve_scale(y="shared")


def secao_carteiras(carteiras: dict[str, pd.DataFrame], dim_produto: pd.DataFrame) -> None:
    texto.subheader("Carteiras de R$ 1.000,00 montadas no primeiro dia")
    faltando = [t for t in TABELAS_CARTEIRA if t not in carteiras]
    if faltando:
        texto.info(f"Carteiras não encontradas na gold ({', '.join(faltando)}): rode `make gold`.")
        return
    composicao, liquidacao = carteiras["composicao_carteira"], carteiras["liquidacao_carteira"]
    metricas = carteiras["metricas_carteira"]
    taxa_parametro, _ = taxas_da_gold(liquidacao)
    opcoes = {f"com taxa de venda ({formatar_percentual(taxa_parametro, 0)})": taxa_parametro, "sem taxa (0%)": 0.0}
    escolha = st.radio("Taxa de venda na liquidação", list(opcoes), index=0, horizontal=True, key="taxa_carteiras")
    taxa = opcoes[escolha]

    pendentes = sorted(set(composicao.loc[composicao["status"] == STATUS_REGRA_PENDENTE, "carteira"]))
    for carteira in pendentes:
        texto.warning(
            f"Carteira {carteira}: regra pendente (ADR-005 sem status Aceito). "
            "Ela não é calculada e fica fora do gráfico, com métricas em branco."
        )

    st.altair_chart(grafico_carteiras(liquidacao, taxa, f"Valor de liquidação por dia, {escolha}"), width="stretch")
    texto.caption(
        "Linha tracejada: R$ 1.000,00 investidos no primeiro dia. Losangos: dias com preço carregado "
        "(item sem preço no dia avaliado pelo último preço observado, só nesta avaliação) ou com CDI "
        "pendente (dia útil sem CDI publicado, que rende 0)."
    )

    texto.markdown("**Métricas no último dia**")
    st.dataframe(tabela_metricas(metricas, taxa, taxa_parametro), hide_index=True, width="stretch")
    texto.caption(
        "Retorno acumulado = valor no último dia ÷ R$ 1.000,00 − 1; excesso sobre o CDI = retorno − retorno "
        "da cdi com a mesma taxa; perda máxima = maior queda entre um pico e o ponto mais baixo seguinte. "
        "A diferença com − sem taxa mostra a sensibilidade à taxa de venda: zero em dolar e cdi."
    )

    texto.markdown("**Composição**")
    montagem = composicao["data_montagem"].dropna()
    ptax = composicao["ptax_venda"].dropna()
    if len(montagem) and len(ptax):
        texto.caption(
            f"Montagem em {pd.Timestamp(montagem.iloc[0]):%d/%m/%Y} com PTAX de venda "
            f"{formatar_numero(ptax.iloc[0], 4)}; preço de compra = market_price × PTAX de venda, sem taxa na compra."
        )
    for carteira in _ordem_carteiras(composicao["carteira"]):
        linhas_c = composicao[composicao["carteira"] == carteira]
        texto.markdown(f"**{carteira}**: {REGRAS_CARTEIRAS.get(carteira, '')}")
        if (linhas_c["status"] == STATUS_REGRA_PENDENTE).any():
            texto.warning(f"Carteira {carteira}: regra pendente, sem composição.")
            continue
        posicoes = linhas_c[linhas_c["product_id"].notna()]
        if carteira == "selado":
            if bool(linhas_c["fallback"].fillna(False).any()):
                texto.caption("Booster box sem preço no primeiro dia: fallback para o selado de maior preço (ADR-006).")
            if posicoes.empty:
                texto.info("Nenhum selado com preço no primeiro dia: todo o valor ficou em caixa (ADR-006).")
            elif (posicoes["unidades"] == 0).all():
                texto.info(
                    f"A selado ficou com 0 unidades: o preço de compra "
                    f"({formatar_moeda(posicoes['preco_compra_brl'].iloc[0])}) passa do orçamento de "
                    f"{formatar_moeda(ORCAMENTO)}, e todo o valor ficou em caixa (ADR-006)."
                )
        aviso_cartas = aviso_cartas_sem_unidade(composicao, carteira)
        if aviso_cartas:
            texto.info(aviso_cartas)
        if carteira == "dolar":
            usd = linhas_c["usd"].dropna()
            if len(usd):
                texto.caption(f"Comprados {formatar_moeda(usd.iloc[0], 'US$')} no primeiro dia.")
        st.dataframe(tabela_composicao(composicao, dim_produto, carteira), hide_index=True, width="stretch")


# ---------------------------------------------------------------- placar da turma (T-47)


def placar_turma(gold_turma: pd.DataFrame, carteira_perda: str = "cesta_raras") -> dict:
    """Placar a partir da gold_turma de todas as coleções (RF-28), sem recalcular carteiras.

    Por coleção: retorno acumulado no último dia de cada carteira e perda máxima
    da série de valor_brl (`perda_maxima` da T-43). "Superou" é comparação
    estrita (empate não conta); o denominador conta só as coleções com as duas
    carteiras com valor no último dia. A menor perda máxima é da
    `carteira_perda`; empates entram todos.
    """
    gt = gold_turma.assign(data=pd.to_datetime(gold_turma["data"]))
    resumo = []
    for gid, g in gt.groupby("group_id", sort=True):
        ultimo = g["data"].max()
        ret = g[g["data"] == ultimo].set_index("carteira")["retorno_acumulado"]
        perdas = {}
        for carteira, s in g.sort_values("data").groupby("carteira"):
            valores = s["valor_brl"]
            perdas[carteira] = None if valores.isna().any() or valores.empty else perda_maxima(valores.astype(float).tolist())

        def superou(a: str, b: str):
            if a not in ret.index or b not in ret.index or _nulo(ret[a]) or _nulo(ret[b]):
                return None
            return bool(float(ret[a]) > float(ret[b]))

        linha = {"group_id": int(gid), "primeiro": g["data"].min().date(), "ultimo": ultimo.date()}
        for carteira in CARTEIRAS:
            valor = ret.get(carteira)
            linha[f"retorno_{carteira}"] = None if _nulo(valor) else float(valor)
            linha[f"perda_{carteira}"] = perdas.get(carteira)
        linha["selado_superou_cdi"] = superou("selado", "cdi")
        linha["cesta_superou_dolar"] = superou("cesta_raras", "dolar")
        resumo.append(linha)
    resumo = pd.DataFrame(resumo)

    def contagem(coluna: str) -> tuple[int, int]:
        if resumo.empty:
            return 0, 0
        validas = resumo[coluna].dropna()
        return int(sum(bool(v) for v in validas)), int(len(validas))

    menor, valor_menor = [], None
    if not resumo.empty:
        perdas = resumo[["group_id", f"perda_{carteira_perda}"]].dropna()
        if len(perdas):
            valor_menor = float(perdas.iloc[:, 1].min())
            menor = [int(g) for g, v in perdas.itertuples(index=False) if abs(float(v) - valor_menor) < 1e-12]
    return {
        "resumo": resumo,
        "selado_cdi": contagem("selado_superou_cdi"),
        "cesta_dolar": contagem("cesta_superou_dolar"),
        "menor_perda": menor,
        "valor_menor_perda": valor_menor,
    }


def secao_placar(gold_turma: pd.DataFrame | None, erro: str | None, fato: pd.DataFrame, dim_colecao: pd.DataFrame) -> None:
    texto.subheader("Placar da turma")
    texto.caption(
        "Lê `gold_turma/carteira/` de todas as coleções disponíveis, somente leitura (RF-28), "
        "com o retorno acumulado no último dia de cada coleção, na taxa de venda gravada por ela."
    )
    if erro:
        texto.error(f"Não foi possível ler a gold_turma: {erro}.")
        return
    if gold_turma is None:
        texto.info(f"gold_turma não configurada: com `{VARIAVEL_GOLD_LOCAL}`, defina também `{VARIAVEL_GOLD_TURMA_LOCAL}`.")
        return
    if gold_turma.empty:
        texto.warning("Nenhuma gold_turma encontrada em `gold_turma/carteira/`: rode `make gold`.")
        return
    ids = sorted(int(g) for g in gold_turma["group_id"].dropna().unique())
    ids_gold = sorted(int(g) for g in fato["group_id"].dropna().unique())
    rotulos = rotulos_colecoes(dim_colecao, sorted(set(ids) | set(ids_gold)))
    if GROUP_ID_DRI not in ids:
        texto.warning("A gold_turma da DRI não foi encontrada: rode `make gold`.")
    if ids == [GROUP_ID_DRI]:
        texto.warning(AVISO_PLACAR_SO_DRI)
    sem_turma = [g for g in ids_gold if g not in ids]
    if sem_turma:
        texto.warning(
            "Coleções com silver na gold, mas sem gold_turma (fora do placar): "
            + ", ".join(rotulos[g] for g in sem_turma) + "."
        )

    carteira = st.selectbox(
        "Carteira da menor perda máxima", list(CARTEIRAS), index=CARTEIRAS.index("cesta_raras"), key="carteira_perda"
    )
    placar = placar_turma(gold_turma, carteira)
    resumo = placar["resumo"]

    dri = resumo[resumo["group_id"] == GROUP_ID_DRI]
    if len(dri):
        p, u = dri["primeiro"].iloc[0], dri["ultimo"].iloc[0]
        diferentes = resumo[(resumo["primeiro"] != p) | (resumo["ultimo"] != u)]
        if len(diferentes):
            texto.warning(
                f"Coleções com período diferente da DRI ({p:%d/%m} a {u:%d/%m}); o retorno é o do último dia de "
                "cada uma: " + ", ".join(
                    f"{rotulos[int(r.group_id)]} ({r.primeiro:%d/%m} a {r.ultimo:%d/%m})" for r in diferentes.itertuples()
                ) + "."
            )

    (a, n_a), (b, n_b) = placar["selado_cdi"], placar["cesta_dolar"]
    menor = ", ".join(rotulos[g] for g in placar["menor_perda"]) or "—"
    c1, c2, c3 = st.columns(3)
    c1.metric(escapar_cifrao("Selado acima da cdi"), f"{a} de {n_a}")
    c2.metric(escapar_cifrao("Cesta_raras acima da dolar"), f"{b} de {n_b}")
    c3.metric(escapar_cifrao(f"Menor perda máxima ({carteira})"), menor)
    texto.caption(
        f"Menor perda máxima da carteira {carteira}: {formatar_percentual(placar['valor_menor_perda'])}. "
        "Empate não conta como superou."
    )

    sim_nao = {True: "sim", False: "não"}
    tabela = pd.DataFrame({
        "Coleção": resumo["group_id"].map(rotulos),
        "Período": [f"{r.primeiro:%d/%m} a {r.ultimo:%d/%m}" for r in resumo.itertuples()],
        **{f"Retorno {c}": resumo[f"retorno_{c}"].map(formatar_percentual) for c in CARTEIRAS},
        "Selado acima da cdi": resumo["selado_superou_cdi"].map(lambda v: "—" if v is None else sim_nao[v]),
        "Cesta_raras acima da dolar": resumo["cesta_superou_dolar"].map(lambda v: "—" if v is None else sim_nao[v]),
        **{f"Perda máxima {c}": resumo[f"perda_{c}"].map(formatar_percentual) for c in CARTEIRAS},
    })
    st.dataframe(tabela, hide_index=True, width="stretch")


# ---------------------------------------------------------------- página


def main() -> None:
    st.set_page_config(page_title="Painel DRI", layout="wide")
    moeda = escolher_moeda()
    simbolo = SIMBOLO_MOEDA[moeda]
    minimo_p1 = filtro_preco_minimo("P1")
    minimo_p5 = filtro_preco_minimo("P5")

    try:
        gold = carregar_gold(fonte_gold())
    except Exception as erro:  # mensagem sem credenciais (RNF-08)
        texto.error(f"Não foi possível ler a gold: {type(erro).__name__}. Rode `make gold` e confira o `.env`.")
        st.stop()

    gold = dict(gold)
    carteiras = {t: gold.pop(t) for t in TABELAS_CARTEIRA if t in gold}
    turma, erro_turma = None, None
    fonte_turma = fonte_gold_turma()
    if fonte_turma is not None:
        try:
            turma = carregar_gold_turma(fonte_turma)
        except Exception as erro:  # mensagem sem credenciais (RNF-08)
            erro_turma = type(erro).__name__

    fato, dim_produto = gold["fato_preco_diario"], gold["dim_produto"]
    dim_colecao = gold["dim_colecao"]
    dri = dim_colecao[dim_colecao["group_id"] == GROUP_ID_DRI]
    nome = dri["nome"].iloc[0] if len(dri) else f"group_id {GROUP_ID_DRI}"
    primeiro, ultimo = periodo(fato)
    group_ids = sorted(int(g) for g in fato["group_id"].dropna().unique())
    rotulos = rotulos_colecoes(dim_colecao, group_ids)
    so_dri = group_ids == [GROUP_ID_DRI]

    texto.title(f"Painel: {nome}")
    texto.caption(f"Data de corte: {ultimo:%d/%m/%Y}. Valores em {moeda} ({simbolo}).")
    aviso_periodo_curto(primeiro, ultimo)

    con = conectar_gold(gold)
    try:
        abas = st.tabs(list(ABAS))
        with abas[0]:
            secao_itens(gold, fato, dim_produto, moeda, minimo_p1, primeiro)
        with abas[1]:
            secao_p1(con, moeda, minimo_p1)
        with abas[2]:
            secao_p2(con, gold, moeda)
        with abas[3]:
            secao_p3(con, gold, moeda, rotulos, so_dri)
        with abas[4]:
            secao_p4(con, rotulos, so_dri)
        with abas[5]:
            secao_p5(con, moeda, minimo_p5, rotulos, so_dri)
        with abas[6]:
            secao_carteiras(carteiras, dim_produto)
        with abas[7]:
            secao_placar(turma, erro_turma, fato, dim_colecao)
    finally:
        con.close()


if __name__ == "__main__":
    main()
