"""Quarentena da silver (T-26; RF-07).

Funções puras, sem I/O: gravar a quarentena no MinIO e escrever a contagem no
log é papel do construtor da silver (T-27).

- `validar` aplica um conversor de `modelos.py`; erro de validação vira uma
  `LinhaQuarentena` com motivo e `chave_raw`; `None` do conversor (boletim da
  PTAX diferente de `Fechamento`) é descarte por regra e não vai à quarentena.
- `deduplicar_por_data` junta PTAX e CDI vindos de brutos de dias diferentes:
  valores iguais geram uma linha; valores divergentes mandam a data inteira
  para a quarentena, uma linha por bruto, com o motivo `MOTIVO_DIVERGENTE`.
- `contar_por_tabela` e `formatar_contagem` produzem a contagem do log.

Esquema da quarentena (specs/spec.md, RF-07): tabela VARCHAR, motivo VARCHAR,
chave_raw VARCHAR, conteudo VARCHAR (a linha original em JSON).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, ValidationError

TABELAS = ("colecao", "produto", "preco_diario", "cambio_diario", "cdi_diario")
MOTIVO_DIVERGENTE = "valor divergente entre brutos"

M = TypeVar("M", bound=BaseModel)


class LinhaQuarentena(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tabela: str
    motivo: str
    chave_raw: str
    conteudo: str


def _json(valor: Any) -> str:
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, default=str)


def _motivo_do_erro(erro: Exception) -> str:
    if isinstance(erro, ValidationError):
        partes = []
        for detalhe in erro.errors():
            campo = ".".join(str(p) for p in detalhe.get("loc", ())) or "linha"
            partes.append(f"{campo}: {detalhe.get('msg')}")
        return "; ".join(partes)
    return f"{type(erro).__name__}: {erro}"


def validar(
    tabela: str,
    conversor: Callable[..., M | None],
    item: dict[str, Any],
    chave_raw: str,
    *args: Any,
    **kwargs: Any,
) -> M | LinhaQuarentena | None:
    """Converte uma linha do bruto.

    Devolve o modelo válido, uma `LinhaQuarentena` com o motivo, ou `None`
    quando o conversor descarta a linha por regra.
    """
    if tabela not in TABELAS:
        raise ValueError(f"tabela desconhecida: {tabela}")
    try:
        return conversor(item, *args, **kwargs)
    except (ValidationError, ValueError, TypeError) as erro:
        return LinhaQuarentena(
            tabela=tabela,
            motivo=_motivo_do_erro(erro),
            chave_raw=chave_raw,
            conteudo=_json(item),
        )


def _valores(registro: BaseModel) -> dict[str, Any]:
    return registro.model_dump(exclude={"chave_raw"})


def deduplicar_por_data(
    tabela: str, registros: Iterable[M]
) -> tuple[list[M], list[LinhaQuarentena]]:
    """Uma linha por `data` para PTAX e CDI repetidos em brutos diferentes.

    Valores iguais (todos os campos menos `chave_raw`): fica a linha da menor
    `chave_raw`, isto é, do bruto mais antigo. Valores divergentes: nenhuma
    linha da data fica na silver e cada bruto gera uma linha de quarentena.
    """
    if tabela not in TABELAS:
        raise ValueError(f"tabela desconhecida: {tabela}")
    por_data: dict[Any, list[M]] = {}
    for registro in registros:
        por_data.setdefault(registro.data, []).append(registro)

    validos: list[M] = []
    quarentena: list[LinhaQuarentena] = []
    for data in sorted(por_data):
        grupo = sorted(por_data[data], key=lambda r: r.chave_raw)
        primeiro = _valores(grupo[0])
        if all(_valores(r) == primeiro for r in grupo[1:]):
            validos.append(grupo[0])
            continue
        quarentena.extend(
            LinhaQuarentena(
                tabela=tabela,
                motivo=MOTIVO_DIVERGENTE,
                chave_raw=r.chave_raw,
                conteudo=_json(r.model_dump(mode="json")),
            )
            for r in grupo
        )
    return validos, quarentena


def contar_por_tabela(linhas: Iterable[LinhaQuarentena]) -> dict[str, int]:
    """Contagem de linhas em quarentena para cada uma das cinco tabelas."""
    contagem = dict.fromkeys(TABELAS, 0)
    for linha in linhas:
        contagem[linha.tabela] += 1
    return contagem


def formatar_contagem(
    contagem: dict[str, int], destaque: Sequence[str] = ("preco_diario", "cambio_diario")
) -> str:
    """Texto do log: `preco_diario: 1, cambio_diario: 1, demais: 0`."""
    partes = [f"{t}: {contagem.get(t, 0)}" for t in destaque]
    demais = sum(n for t, n in contagem.items() if t not in destaque)
    partes.append(f"demais: {demais}")
    return ", ".join(partes)
