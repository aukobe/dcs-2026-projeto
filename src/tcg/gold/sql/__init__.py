"""SQL do esquema estrela da gold (T-30; RF-10, RF-11, RNF-01; ADR-003).

Cada arquivo `.sql` desta pasta define uma tabela. `montar_estrela` executa os
arquivos numa conexão DuckDB e cria as tabelas em memória; não grava nada (a
gravação pela Guarda de prefixo é do Construtor da gold, T-32).

`{base}` é o prefixo do lake: um diretório local (testes) ou `s3://tcg`
(MinIO). Toda leitura da silver usa `hive_partitioning = false`: `group_id`
já é coluna do contrato, e a coluna derivada do caminho a duplicaria (nota da
T-24, ADR-003). `colecao`, `produto` e `preco_diario` são lidas de todas as
coleções com `union_by_name = true`; câmbio e CDI vêm só da silver da DRI.

Os marcadores `{arquivos_<tabela>}` viram, sem `arquivos`, o curinga
`<base>/silver/<tabela>/...` (testes locais) ou, com `arquivos`, a lista de
caminhos que o Construtor da gold aprovou na conferência do contrato (T-32).

`fato_cambio_diario` (T-31, RF-12) tem um dia de calendário por linha, os
mesmos de `dim_data`, com a PTAX aplicada, a `data_ptax` do boletim, o CDI do
dia (0 sem CDI na data) e `cdi_pendente` (dia útil sem CDI).
"""

from __future__ import annotations

from importlib import resources

import duckdb

# Ordem de criação: as dimensões de data e acabamento derivam do fato de preço,
# e o fato de câmbio deriva de dim_data.
TABELAS = (
    "dim_colecao",
    "dim_produto",
    "fato_preco_diario",
    "dim_data",
    "dim_acabamento",
    "fato_cambio_diario",
)


def _literal(valor: str) -> str:
    """Literal SQL entre aspas simples, com aspas internas duplicadas."""
    return "'" + str(valor).replace("'", "''") + "'"


# Tabelas da silver lidas de todas as coleções e o curinga de cada uma.
CURINGAS = {
    "colecao": "silver/colecao/*/*.parquet",
    "produto": "silver/produto/*/*.parquet",
    "preco_diario": "silver/preco_diario/*/*/*.parquet",
}


def _origem(base: str, tabela: str, arquivos: dict[str, list[str]] | None) -> str:
    """Curinga sob `base` ou lista literal dos caminhos aprovados."""
    if arquivos is None:
        return _literal(f"{base}/{CURINGAS[tabela]}")
    caminhos = arquivos.get(tabela) or []
    if not caminhos:
        raise ValueError(f"nenhum arquivo de {tabela} para montar a estrela")
    return "[" + ", ".join(_literal(c) for c in caminhos) + "]"


def ler_sql(tabela: str, base: str, arquivos: dict[str, list[str]] | None = None) -> str:
    """Texto SQL da tabela com `{base}` e `{arquivos_<tabela>}` trocados pelos literais."""
    texto = resources.files(__name__).joinpath(f"{tabela}.sql").read_text(encoding="utf-8")
    base = base.rstrip("/")
    for origem in CURINGAS:
        marcador = "{arquivos_" + origem + "}"
        if marcador in texto:
            texto = texto.replace(marcador, _origem(base, origem, arquivos))
    return texto.replace("{base}", _literal(base))


def montar_estrela(
    con: duckdb.DuckDBPyConnection,
    base: str,
    arquivos: dict[str, list[str]] | None = None,
) -> tuple[str, ...]:
    """Cria na conexão as dimensões e os fatos de preço e câmbio a partir da silver em `base`.

    `arquivos` (opcional): caminhos de `colecao`, `produto` e `preco_diario`
    a ler; sem ele, todas as coleções sob `base` são lidas por curinga.
    """
    for tabela in TABELAS:
        con.execute(f"CREATE OR REPLACE TABLE {tabela} AS {ler_sql(tabela, base, arquivos)}")
    return TABELAS
