"""SQL do esquema estrela da gold (T-30; RF-10, RF-11, RNF-01; ADR-003).

Cada arquivo `.sql` desta pasta define uma tabela. `montar_estrela` executa os
arquivos numa conexão DuckDB e cria as tabelas em memória; não grava nada (a
gravação pela Guarda de prefixo é do Construtor da gold, T-32).

`{base}` é o prefixo do lake: um diretório local (testes) ou `s3://tcg`
(MinIO). Toda leitura da silver usa `hive_partitioning = false`: `group_id`
já é coluna do contrato, e a coluna derivada do caminho a duplicaria (nota da
T-24, ADR-003). As silvers de todas as coleções são lidas por curinga, com
`union_by_name = true`; câmbio vem só da silver da DRI.
"""

from __future__ import annotations

from importlib import resources

import duckdb

# Ordem de criação: as dimensões de data e acabamento derivam do fato.
TABELAS = ("dim_colecao", "dim_produto", "fato_preco_diario", "dim_data", "dim_acabamento")


def _literal(valor: str) -> str:
    """Literal SQL entre aspas simples, com aspas internas duplicadas."""
    return "'" + str(valor).replace("'", "''") + "'"


def ler_sql(tabela: str, base: str) -> str:
    """Texto SQL da tabela com `{base}` trocado pelo literal do prefixo do lake."""
    texto = resources.files(__name__).joinpath(f"{tabela}.sql").read_text(encoding="utf-8")
    return texto.replace("{base}", _literal(base.rstrip("/")))


def montar_estrela(con: duckdb.DuckDBPyConnection, base: str) -> tuple[str, ...]:
    """Cria na conexão as dimensões e o `fato_preco_diario` a partir da silver em `base`."""
    for tabela in TABELAS:
        con.execute(f"CREATE OR REPLACE TABLE {tabela} AS {ler_sql(tabela, base)}")
    return TABELAS
