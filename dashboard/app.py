"""Painel (Streamlit): base comum das seções (T-45; RF-14, RF-20, RF-21).

O painel **só lê** a gold da DRI em `gold/group_id=24269/<tabela>.parquet`
(`fato_preco_diario`, `dim_produto`, `dim_data`, `dim_colecao`): nunca grava
nem apaga nada (RNF-03). A leitura vai ao servidor S3 de `MINIO_ENDPOINT` pela
conexão DuckDB de `tcg.lake.duckdb` (data lake da turma ou MinIO local, ADR-008).

Gancho de teste e de desenvolvimento: se a variável opcional `PAINEL_GOLD_DIR`
apontar para uma pasta com os mesmos `<tabela>.parquet`, a gold é lida dessa
pasta e o S3 não é usado.

Peças reutilizáveis pelas seções das perguntas (T-46):
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

GROUP_ID_DRI = 24269
PREFIXO_GOLD = f"gold/group_id={GROUP_ID_DRI}"
TABELAS_GOLD = ("fato_preco_diario", "dim_produto", "dim_data", "dim_colecao")
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


def grafico_serie(serie: pd.DataFrame, titulo: str, rotulo_y: str, cor: str | None = None) -> None:
    """Gráfico de linha que interrompe a linha nos valores nulos (RF-21)."""
    codificacao = {
        "x": alt.X("data:T", title="Data"),
        "y": alt.Y("valor:Q", title=rotulo_y),
        "tooltip": [alt.Tooltip("data:T", title="Data"), alt.Tooltip("valor:Q", title=rotulo_y, format=",.2f")],
    }
    if cor:
        codificacao["color"] = alt.Color(f"{cor}:N", title=None)
    grafico = (
        alt.Chart(serie, title=titulo)
        .mark_line(point=True, invalid="break-paths-show-domains")
        .encode(**codificacao)
    )
    st.altair_chart(grafico, use_container_width=True)


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


# ---------------------------------------------------------------- página


def main() -> None:
    st.set_page_config(page_title="Painel DRI", layout="wide")
    moeda = escolher_moeda()
    simbolo = SIMBOLO_MOEDA[moeda]
    minimo = filtro_preco_minimo("P1")

    try:
        gold = carregar_gold(fonte_gold())
    except Exception as erro:  # mensagem sem credenciais (RNF-08)
        st.error(f"Não foi possível ler a gold: {type(erro).__name__}. Rode `make gold` e confira o `.env`.")
        st.stop()

    fato, dim_produto = gold["fato_preco_diario"], gold["dim_produto"]
    colecao = gold["dim_colecao"]
    colecao = colecao[colecao["group_id"] == GROUP_ID_DRI]
    nome = colecao["nome"].iloc[0] if len(colecao) else f"group_id {GROUP_ID_DRI}"
    primeiro, ultimo = periodo(fato)

    st.title(f"Painel: {nome}")
    st.caption(f"Data de corte: {ultimo:%d/%m/%Y}. Valores em {moeda} ({simbolo}).")
    aviso_periodo_curto(primeiro, ultimo)

    itens = aplicar_filtro_preco(tabela_itens(fato, dim_produto, moeda), minimo)
    st.subheader("Cartas da coleção")
    st.caption(f"{len(itens)} itens com preço acima de US$ {minimo:,.2f} em {primeiro:%d/%m/%Y}.")
    st.dataframe(
        itens[["nome", "acabamento", "raridade", "preco_inicial", "preco_final"]].rename(
            columns={
                "nome": "Produto",
                "acabamento": "Acabamento",
                "raridade": "Raridade",
                "preco_inicial": f"Preço inicial ({simbolo})",
                "preco_final": f"Preço atual ({simbolo})",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

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


if __name__ == "__main__":
    main()
