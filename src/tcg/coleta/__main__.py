"""Coletor diário (specs/plan.md, seção 5; RF-01, RF-02, RF-04; ADR-007).

Uso: `python -m tcg.coleta --destino <checkout da Branch dados-raw>`.

1. Calcula a data de referência pelo ciclo do TCGCSV (20h UTC de D até 20h
   UTC de D+1 grava `data=D`); não há recusa por horário.
2. Verifica cada arquivo da data de referência antes de qualquer requisição;
   os existentes são pulados.
3. Para cada arquivo pendente, busca pelo cliente da fonte e grava o corpo
   byte a byte; cada arquivo é independente dos demais.

Códigos de saída: 0 = tudo gravado ou já existente; 1 = alguma fonte falhou
(os demais arquivos foram gravados); 2 = destino inexistente (nada foi
requisitado nem gravado).
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
import datetime as dt
import logging
from pathlib import Path
import sys

from tcg.coleta.bcb import ClienteBcb
from tcg.coleta.gravador import gravar
from tcg.coleta.guarda import (
    ArquivoDoDia,
    arquivos_pendentes,
    caminho_raw,
    data_referencia,
)
from tcg.coleta.http import ClienteHttp
from tcg.coleta.tcgcsv import ClienteTcgcsv
from tcg.config import Colecao, Parametros, ler_colecao, ler_parametros
from tcg.log import configurar_log

log = logging.getLogger("tcg.coleta")

SUCESSO = 0
FALHA_FONTE = 1
RECUSA = 2


def _buscadores(
    tcgcsv: ClienteTcgcsv, bcb: ClienteBcb, data: dt.date
) -> dict[str, Callable[[], bytes]]:
    return {
        "products.json": tcgcsv.buscar_products,
        "prices.json": tcgcsv.buscar_prices,
        "cotacao.json": lambda: bcb.buscar_ptax(data),
        "cdi.json": lambda: bcb.buscar_cdi(data),
    }


def executar(
    destino: Path,
    agora: dt.datetime | None = None,
    http: ClienteHttp | None = None,
    parametros: Parametros | None = None,
    colecao: Colecao | None = None,
) -> int:
    destino = Path(destino)
    parametros = parametros or ler_parametros()
    colecao = colecao or ler_colecao()
    agora = agora or dt.datetime.now(dt.UTC)

    if not destino.is_dir():
        log.error("coleta recusada: destino inexistente: %s", destino)
        return RECUSA

    data = data_referencia(agora, parametros.hora_virada_ciclo_utc)
    log.info(
        "coleta iniciada: data=%s (data de referência do ciclo) agora=%s group_id=%d",
        data, f"{agora.astimezone(dt.UTC):%Y-%m-%dT%H:%M:%SZ}", colecao.group_id,
    )
    pendentes = arquivos_pendentes(destino, data, colecao.group_id)
    if not pendentes:
        log.info("coleta encerrada: todos os arquivos da data de referência já existem; requisicoes=0")
        return SUCESSO

    http = http or ClienteHttp(parametros=parametros)
    buscar = _buscadores(ClienteTcgcsv(http, colecao), ClienteBcb(http, parametros), data)
    falhas: list[ArquivoDoDia] = []
    for item in pendentes:
        caminho = caminho_raw(destino, item, colecao.group_id, data)
        try:
            gravar(caminho, buscar[item.arquivo]())
        except Exception as erro:  # fontes independentes: uma falha não para as demais
            log.error(
                "fonte falhou, nada gravado: %s/%s erro=%s: %s",
                item.fonte, item.arquivo, type(erro).__name__, erro,
            )
            falhas.append(item)

    requisicoes = getattr(http, "requisicoes", None)
    if falhas:
        log.error(
            "coleta encerrada com falha: %d de %d arquivos pendentes falharam (%s); requisicoes=%s",
            len(falhas), len(pendentes),
            ", ".join(f"{f.fonte}/{f.arquivo}" for f in falhas), requisicoes,
        )
        return FALHA_FONTE
    log.info("coleta encerrada: %d arquivos gravados; requisicoes=%s", len(pendentes), requisicoes)
    return SUCESSO


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tcg.coleta", description=__doc__.splitlines()[0])
    parser.add_argument("--destino", required=True, type=Path, help="checkout da Branch dados-raw")
    args = parser.parse_args(argv)
    configurar_log()
    return executar(args.destino)


if __name__ == "__main__":
    sys.exit(main())
