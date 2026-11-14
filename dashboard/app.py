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

Executado com `make painel` (`streamlit run dashboard/app.py`); o `main()` só
roda quando o arquivo é o script principal, para que as funções possam ser
importadas.
"""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

from tcg.config import ler_parametros
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
ABAS = ("Itens", "P1: alta e queda", "P2: selados × raras", "P3: coleções", "P4: concentração", "P5: risco")


# ---------------------------------------------------------------- leitura da gold


def _literal(valor: str) -> str:
    return "'" + str(valor).replace("'", "''") + "'"


def _ler_local(pasta: Path) -> dict[str, pd.DataFrame]:
    con = duckdb.connect()
    try:
        return {
            tabela: con.sql(
                f"SELECT * FROM read_parquet({_literal(pasta / f'{tabela}.parquet')}, "
                "hive_partitioning = false)"
            ).df()
            for tabela in TABELAS_GOLD
        }
    finally:
        con.close()


def _ler_s3() -> dict[str, pd.DataFrame]:
    from tcg.config import ler_config_minio
    from tcg.lake.duckdb import caminho_s3, conectar

    config = ler_config_minio()
    con = conectar(config)
    try:
        return {
            tabela: con.sql(
                "SELECT * FROM read_parquet("
                f"{_literal(caminho_s3(config.bucket, f'{PREFIXO_GOLD}/{tabela}.parquet'))}, "
                "hive_partitioning = false)"
            ).df()
            for tabela in TABELAS_GOLD
        }
    finally:
        con.close()


@st.cache_data(ttl=3600, show_spinner="Lendo a gold...")
def carregar_gold(fonte: str) -> dict[str, pd.DataFrame]:
    """Tabelas da gold, só leitura. `fonte` é uma pasta local ou `"s3"`."""
    return _ler_s3() if fonte == "s3" else _ler_local(Path(fonte))


def fonte_gold() -> str:
    pasta = os.environ.get(VARIAVEL_GOLD_LOCAL, "").strip()
    return pasta or "s3"


# ---------------------------------------------------------------- formatação pt-BR


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
            f"Preço mínimo no primeiro dia (US$), {pergunta}",
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
    st.warning(
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
        alt.Chart(dados, title=titulo)
        .mark_line(point=True, invalid="break-paths-show-domains")
        .encode(**codificacao)
    )


def grafico_serie(serie: pd.DataFrame, titulo: str, rotulo_y: str, cor: str | None = None) -> None:
    """Gráfico de linha que interrompe a linha nos valores nulos (RF-21)."""
    st.altair_chart(grafico_linhas(serie, titulo, rotulo_y, cor), width="stretch")


def mostrar_produto(nome: str, image_url: str | None, url: str | None) -> None:
    """Imagem e link do produto, ou os avisos de indisponível (RF-20)."""
    if image_url is None or pd.isna(image_url) or not str(image_url).strip():
        st.caption(AVISO_IMAGEM)
    else:
        st.image(str(image_url), caption=nome, width=200)
    if url is None or pd.isna(url) or not str(url).strip():
        st.caption(AVISO_LINK)
    else:
        st.markdown(f"[Ver {nome} no TCGplayer]({url})")


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
    st.subheader("Cartas da coleção")
    st.caption(f"{len(itens)} itens com preço acima de {formatar_moeda(minimo, 'US$')} em {primeiro:%d/%m/%Y}.")
    exibicao = itens[["nome", "acabamento", "raridade"]].rename(
        columns={"nome": "Produto", "acabamento": "Acabamento", "raridade": "Raridade"}
    )
    exibicao[f"Preço inicial ({simbolo})"] = itens["preco_inicial"].map(lambda v: formatar_moeda(v, simbolo))
    exibicao[f"Preço atual ({simbolo})"] = itens["preco_final"].map(lambda v: formatar_moeda(v, simbolo))
    st.dataframe(exibicao, hide_index=True, width="stretch")

    if itens.empty:
        st.info("Nenhum item acima do preço mínimo.")
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
    st.subheader("P1: cartas que mais valorizaram e desvalorizaram")
    st.caption(
        f"Variação em reais do primeiro ao último dia, decomposta em carta (dólar), câmbio e "
        f"termo cruzado; só cartas sem Code Card acima de {formatar_moeda(minimo, 'US$')} no primeiro dia."
    )
    alta, queda = (r.df() for r in p1_rankings(con, "fato_preco_diario", "dim_produto", preco_minimo_usd=minimo))
    configuracao = {
        "Imagem": st.column_config.ImageColumn("Imagem"),
        "Link": st.column_config.LinkColumn("Link", display_text="TCGplayer"),
    }
    for titulo, ranking in (("Maiores altas", alta), ("Maiores quedas", queda)):
        st.markdown(f"**{titulo}**")
        if ranking.empty:
            st.info(f"Nenhum item em {titulo.lower()}.")
            continue
        st.dataframe(tabela_ranking(ranking, moeda), hide_index=True, width="stretch", column_config=configuracao)
    detalhe = pd.concat([alta, queda], ignore_index=True)
    if not detalhe.empty:
        fim = "brl_final" if moeda == "reais" else "usd_final"
        seletor_item(detalhe.assign(preco_final=detalhe[fim]), "item_p1")


def secao_p2(con, gold, moeda: str) -> None:
    simbolo = SIMBOLO_MOEDA[moeda]
    st.subheader("P2: selados contra cartas Double Rare em diante")
    p2 = p2_indice(con, "fato_preco_diario", "dim_produto", coluna=COLUNA_MOEDA[moeda]).df()
    if p2.empty:
        st.info("Sem preços da DRI para a P2.")
        return
    n_sel, n_rar = int(p2["itens_selados"].iloc[0]), int(p2["itens_double_rare_mais"].iloc[0])
    st.caption(
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
    st.subheader("P3: valor da coleção em índice base 100")
    if so_dri:
        st.warning(AVISO_OUTRAS_COLECOES)
    p3 = p3_indice(
        con, "fato_preco_diario", "dim_produto", "fato_cambio_diario", coluna=COLUNA_MOEDA[moeda]
    ).df()
    if p3.empty:
        st.info("Sem preços para a P3.")
        return
    base = p3["data"].min()
    cestas = p3[p3["serie"] != "PTAX"].groupby("group_id")["itens_cesta"].first()
    st.caption(
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
    st.subheader("P4: concentração do valor no último dia")
    if so_dri:
        st.warning(AVISO_OUTRAS_COLECOES)
    participacao, concentracao = (r.df() for r in p4_concentracao(con, "fato_preco_diario", "dim_produto"))
    if participacao.empty:
        st.info("Sem preços para a P4.")
        return
    participacao = participacao.assign(
        colecao=participacao["group_id"].map(rotulos),
        participacao_fmt=participacao["participacao"].map(formatar_percentual),
        valor_fmt=participacao["valor"].map(lambda v: formatar_moeda(v, "R$")),
    )
    grafico = (
        alt.Chart(participacao, title="Participação por raridade (cartas sem Code Card)")
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
    st.caption("A participação usa o market_price em reais do último dia; no mesmo dia, ela não muda com a moeda.")


def secao_p5(con, moeda: str, minimo: float, rotulos: dict[int, str], so_dri: bool) -> None:
    simbolo = SIMBOLO_MOEDA[moeda]
    st.subheader("P5: retorno contra volatilidade")
    if so_dri:
        st.warning(AVISO_OUTRAS_COLECOES)
    p5 = p5_retorno_volatilidade(
        con, "fato_preco_diario", "dim_produto", coluna=COLUNA_MOEDA[moeda], preco_minimo_usd=minimo
    ).df()
    if p5.empty:
        st.info("Nenhum item acima do preço mínimo para a P5.")
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
    st.caption(
        f"Cartas sem Code Card acima de {formatar_moeda(minimo, 'US$')} no primeiro dia da coleção; "
        f"volatilidade = desvio-padrão amostral dos retornos diários em {moeda}, sem retornos que "
        f"atravessam lacuna. {len(pontos)} itens no gráfico"
        + (f"; {sem_vol} sem dois retornos diários válidos ficam fora." if sem_vol else ".")
    )
    if not pontos.empty:
        grafico = (
            alt.Chart(pontos, title="Retorno no período × volatilidade diária")
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
        st.error(f"Não foi possível ler a gold: {type(erro).__name__}. Rode `make gold` e confira o `.env`.")
        st.stop()

    fato, dim_produto = gold["fato_preco_diario"], gold["dim_produto"]
    dim_colecao = gold["dim_colecao"]
    dri = dim_colecao[dim_colecao["group_id"] == GROUP_ID_DRI]
    nome = dri["nome"].iloc[0] if len(dri) else f"group_id {GROUP_ID_DRI}"
    primeiro, ultimo = periodo(fato)
    group_ids = sorted(int(g) for g in fato["group_id"].dropna().unique())
    rotulos = rotulos_colecoes(dim_colecao, group_ids)
    so_dri = group_ids == [GROUP_ID_DRI]

    st.title(f"Painel: {nome}")
    st.caption(f"Data de corte: {ultimo:%d/%m/%Y}. Valores em {moeda} ({simbolo}).")
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
    finally:
        con.close()


if __name__ == "__main__":
    main()
