"""Reprocessamento das camadas derivadas (T-33; RF-13, RNF-03, RNF-04; ADR-004).

Uso: `make reprocessar CONFIRMAR=24269` (ou `python -m tcg.reprocessar`, com as
variáveis do `.env` e `CONFIRMAR` no ambiente). **Executado só pelo autor**:
o data lake oficial é o bucket da turma (ADR-008), com credencial de
administrador, e este comando apaga objetos.

1. Lista (somente leitura) os objetos dos três prefixos derivados da DRI:
   `silver/*/group_id=24269/` (inclui a quarentena), `gold/group_id=24269/` e
   `gold_turma/carteira/group_id=24269/`. Só entram chaves que a Guarda de
   prefixo aceita; `raw/` e outros group_ids nunca são listados como alvo.
2. Trava de confirmação: sem `CONFIRMAR=24269` (ausente, vazio ou outro valor),
   mostra endpoint, bucket e quantas chaves apagaria em cada prefixo e sai com
   código 4, sem apagar nada e sem abrir o DuckDB.
3. Com a confirmação, apaga pelo `guarda_prefixo.apagar` (única exclusão do
   código, que valida o lote inteiro antes do SDK) e registra cada chave.
4. Reconstrói a partir do bruto: `construir_silver` e depois `construir_gold`,
   os mesmos construtores de `make silver` e `make gold`.

O log registra início, chaves apagadas e fim (specs/plan.md, seção 10).

Códigos de saída: 0 = reprocessado; 2 = configuração ausente ou inválida;
3 = silver da DRI ausente ou fora do contrato (gold não gerada);
4 = sem confirmação, nada apagado.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass, field
import logging
import os
import sys

from tcg.config import Colecao, ConfiguracaoError, ler_colecao, ler_config_minio
from tcg.gold.construtor import ResultadoGold, SilverDriInvalidaError, construir_gold
from tcg.lake.cliente import criar_cliente
from tcg.lake.duckdb import conectar
from tcg.lake.guarda_prefixo import GROUP_ID_DRI, apagar, chave_permitida
from tcg.log import configurar_log
from tcg.silver.construtor import ResultadoSilver, construir_silver

log = logging.getLogger(__name__)

SUCESSO = 0
ERRO_CONFIG = 2
ERRO_SILVER_DRI = 3
SEM_CONFIRMACAO = 4

VARIAVEL_CONFIRMACAO = "CONFIRMAR"
VALOR_CONFIRMACAO = str(GROUP_ID_DRI)

_PARTICAO = f"group_id={GROUP_ID_DRI}"
# rótulo do prefixo -> prefixo de listagem no SDK
PREFIXOS = {
    f"silver/*/{_PARTICAO}/": "silver/",
    f"gold/{_PARTICAO}/": f"gold/{_PARTICAO}/",
    f"gold_turma/carteira/{_PARTICAO}/": f"gold_turma/carteira/{_PARTICAO}/",
}


@dataclass
class ResultadoReprocessamento:
    confirmado: bool
    alvos: dict[str, list[str]] = field(default_factory=dict)
    apagadas: list[str] = field(default_factory=list)
    silver: ResultadoSilver | None = None
    gold: ResultadoGold | None = None


def listar_derivados(cliente, bucket: str) -> dict[str, list[str]]:
    """Chaves dos três prefixos derivados da DRI, agrupadas pelo rótulo do prefixo.

    `silver/` é listado inteiro (há outras coleções), e só ficam as chaves que
    a Guarda de prefixo aceita; nos outros dois prefixos a listagem já é da DRI,
    e o mesmo filtro vale como segunda conferência.
    """
    alvos: dict[str, list[str]] = {}
    for rotulo, prefixo in PREFIXOS.items():
        chaves = (o.object_name for o in cliente.list_objects(bucket_name=bucket, prefix=prefixo, recursive=True))
        alvos[rotulo] = sorted(c for c in chaves if c.startswith(prefixo) and chave_permitida(c))
    return alvos


def confirmacao_valida(confirmacao: str | None) -> bool:
    return confirmacao is not None and confirmacao.strip() == VALOR_CONFIRMACAO


def reprocessar(
    cliente,
    bucket: str,
    colecao: Colecao,
    confirmacao: str | None,
    endpoint: str,
    abrir_duckdb: Callable[[], object],
) -> ResultadoReprocessamento:
    """Apaga as camadas derivadas da DRI e as reconstrói a partir do bruto.

    Sem `confirmacao == "24269"`, só mostra o que seria apagado e não chama
    `guarda_prefixo.apagar`, os construtores nem `abrir_duckdb`.
    """
    alvos = listar_derivados(cliente, bucket)
    total = sum(len(c) for c in alvos.values())
    if not confirmacao_valida(confirmacao):
        log.warning("reprocessamento NÃO executado: falta %s=%s; nada foi apagado",
                    VARIAVEL_CONFIRMACAO, VALOR_CONFIRMACAO)
        log.warning("endpoint=%s bucket=%s", endpoint, bucket)
        for rotulo, chaves in alvos.items():
            log.warning("apagaria %d chave(s) em %s", len(chaves), rotulo)
        log.warning("total que seria apagado: %d chave(s); para executar: make reprocessar %s=%s",
                    total, VARIAVEL_CONFIRMACAO, VALOR_CONFIRMACAO)
        return ResultadoReprocessamento(confirmado=False, alvos=alvos)

    log.info("reprocessamento iniciado: endpoint=%s bucket=%s, %d chave(s) a apagar", endpoint, bucket, total)
    r = ResultadoReprocessamento(confirmado=True, alvos=alvos)
    lote = [c for chaves in alvos.values() for c in chaves]
    r.apagadas = apagar(cliente, bucket, lote)
    log.info("chaves apagadas pelo reprocessamento: %d", len(r.apagadas))

    r.silver = construir_silver(cliente, bucket, colecao)
    con = abrir_duckdb()
    try:
        r.gold = construir_gold(cliente, con, bucket)
    finally:
        con.close()
    log.info("reprocessamento concluído: %d apagada(s), silver e gold reconstruídas", len(r.apagadas))
    return r


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tcg.reprocessar", description=__doc__.splitlines()[0])
    parser.parse_args(argv)
    configurar_log()
    try:
        colecao = ler_colecao()
        config = ler_config_minio(colecao)
    except ConfiguracaoError as erro:
        log.error("%s", erro)
        return ERRO_CONFIG
    try:
        r = reprocessar(
            criar_cliente(config),
            config.bucket,
            colecao,
            os.environ.get(VARIAVEL_CONFIRMACAO),
            config.endpoint,
            lambda: conectar(config),
        )
    except SilverDriInvalidaError as erro:
        log.error("%s; gold não gerada", erro)
        return ERRO_SILVER_DRI
    return SUCESSO if r.confirmado else SEM_CONFIRMACAO


if __name__ == "__main__":
    sys.exit(main())
