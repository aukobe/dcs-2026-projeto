"""Guarda de data de referência e duplicidade (specs/plan.md, seção 4; RF-01, RF-04, ADR-007).

- A data de referência segue o ciclo do TCGCSV (spec, Definições): a coleta
  feita entre `hora_virada_ciclo_utc` (20h UTC) do dia D e a mesma hora de
  D+1 grava como `data=D`. Não há recusa por horário.
- Para cada arquivo da data de referência, verifica se ele já existe no
  checkout da Branch dados-raw **antes** de qualquer requisição.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import logging
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ArquivoDoDia:
    fonte: str  # pasta da fonte em raw/ (contrato do bruto)
    arquivo: str


# Os quatro arquivos do bruto de cada data de referência (spec, Contratos: Bruto).
ARQUIVOS_DO_DIA = (
    ArquivoDoDia("tcgplayer", "products.json"),
    ArquivoDoDia("tcgplayer", "prices.json"),
    ArquivoDoDia("bcb_ptax", "cotacao.json"),
    ArquivoDoDia("bcb_cdi", "cdi.json"),
)


def _em_utc(agora: dt.datetime) -> dt.datetime:
    if agora.tzinfo is None or agora.utcoffset() is None:
        raise ValueError("o horário da coleta precisa de fuso horário (datetime sem tzinfo recusado)")
    return agora.astimezone(dt.UTC)


def data_referencia(agora: dt.datetime, hora_virada_ciclo_utc: int) -> dt.date:
    """Data de referência do ciclo do TCGCSV a que `agora` pertence.

    Antes de `hora_virada_ciclo_utc` (UTC), o momento ainda pertence ao ciclo
    do dia anterior; a partir dela, ao ciclo do próprio dia.
    """
    if not 0 <= hora_virada_ciclo_utc <= 23:
        raise ValueError("hora_virada_ciclo_utc deve estar entre 0 e 23")
    utc = _em_utc(agora)
    if utc.hour < hora_virada_ciclo_utc:
        return utc.date() - dt.timedelta(days=1)
    return utc.date()


def caminho_raw(destino: Path, item: ArquivoDoDia, group_id: int, data: dt.date) -> Path:
    """`raw/<fonte>/group_id=<id>/data=AAAA-MM-DD/<arquivo>` dentro do destino."""
    return (
        Path(destino) / "raw" / item.fonte / f"group_id={group_id}"
        / f"data={data:%Y-%m-%d}" / item.arquivo
    )


def arquivos_pendentes(destino: Path, data: dt.date, group_id: int) -> list[ArquivoDoDia]:
    """Arquivos da data de referência que ainda não existem; os existentes vão para o log."""
    pendentes = []
    for item in ARQUIVOS_DO_DIA:
        caminho = caminho_raw(destino, item, group_id, data)
        if caminho.exists():
            log.info(
                "arquivo da data de referência já existe, fonte pulada sem requisição: %s",
                caminho.relative_to(destino),
            )
        else:
            pendentes.append(item)
    return pendentes
