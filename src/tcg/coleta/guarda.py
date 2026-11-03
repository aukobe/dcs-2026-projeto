"""Guarda de horário e duplicidade (specs/plan.md, seção 4; RF-04, RES-03).

- A data da coleta é a data UTC do momento (spec, Definições).
- A coleta é recusada antes de `hora_minima_utc` (20h UTC).
- Para cada arquivo do dia, verifica se ele já existe no checkout da Branch
  dados-raw **antes** de qualquer requisição.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import logging
from pathlib import Path

log = logging.getLogger(__name__)


class ForaDoHorarioError(RuntimeError):
    """Coleta pedida antes da hora mínima UTC (RF-04)."""


@dataclass(frozen=True)
class ArquivoDoDia:
    fonte: str  # pasta da fonte em raw/ (contrato do bruto)
    arquivo: str


# Os quatro arquivos do bruto de cada dia (spec, Contratos: Bruto).
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


def data_coleta(agora: dt.datetime) -> dt.date:
    """Data UTC do momento da coleta."""
    return _em_utc(agora).date()


def verificar_horario(agora: dt.datetime, hora_minima_utc: int) -> None:
    """Levanta `ForaDoHorarioError` antes de `hora_minima_utc` (UTC)."""
    utc = _em_utc(agora)
    if utc.hour < hora_minima_utc:
        motivo = (
            f"coleta recusada: {utc:%Y-%m-%dT%H:%M:%SZ} é antes de "
            f"{hora_minima_utc:02d}h UTC; nenhuma requisição enviada"
        )
        log.error(motivo)
        raise ForaDoHorarioError(motivo)


def caminho_raw(destino: Path, item: ArquivoDoDia, group_id: int, data: dt.date) -> Path:
    """`raw/<fonte>/group_id=<id>/data=AAAA-MM-DD/<arquivo>` dentro do destino."""
    return (
        Path(destino) / "raw" / item.fonte / f"group_id={group_id}"
        / f"data={data:%Y-%m-%d}" / item.arquivo
    )


def arquivos_pendentes(destino: Path, data: dt.date, group_id: int) -> list[ArquivoDoDia]:
    """Arquivos do dia que ainda não existem; os existentes são registrados no log."""
    pendentes = []
    for item in ARQUIVOS_DO_DIA:
        caminho = caminho_raw(destino, item, group_id, data)
        if caminho.exists():
            log.info(
                "arquivo do dia já existe, fonte pulada sem requisição: %s",
                caminho.relative_to(destino),
            )
        else:
            pendentes.append(item)
    return pendentes
