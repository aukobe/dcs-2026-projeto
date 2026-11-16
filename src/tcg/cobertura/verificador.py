"""Verificador de cobertura (specs/plan.md, seções 4 e 10; RF-27, ADR-001, ADR-007).

Uso: `make cobertura` (ou `python -m tcg.cobertura.verificador [--sem-buscar]`).

Compara cada data entre o primeiro e o último dia (spec, Definições: menor e
maior `data` com bruto do TCGCSV) com:
1. os quatro arquivos do bruto na Branch dados-raw, lidos pelos blobs, sem
   checkout (Leitor da branch, como no `make sync`);
2. a tabela "Dias sem coleta" do README.md (`| data | motivo |`).

Origem de cada data: `bruto` (os quatro arquivos), `registro` (linha na tabela
com motivo não vazio) ou `faltante`. Linha sem motivo não conta.

O relatório vai para a saída padrão; os logs, para a saída de erro.
Não lê o `.env` e não acessa nenhum data lake.

Códigos de saída: 0 = nenhuma data faltante; 1 = há datas faltantes (listadas);
2 = falha do git, branch sem bruto do TCGCSV ou README sem a tabela.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from dataclasses import dataclass, field
import datetime as dt
import logging
from pathlib import Path
import re
import sys

from tcg.coleta.guarda import ARQUIVOS_DO_DIA
from tcg.config import ler_colecao
from tcg.log import configurar_log
from tcg.sync import leitor_branch
from tcg.sync.leitor_branch import LeitorBranchError

log = logging.getLogger(__name__)

SUCESSO = 0
FALHA = 1
ERRO = 2

RAIZ_REPO = Path(__file__).resolve().parents[3]
TITULO_SECAO = "## Dias sem coleta"
FONTE_TCGCSV = "tcgplayer"

BRUTO = "bruto"
REGISTRO = "registro"
FALTANTE = "faltante"


class CoberturaError(RuntimeError):
    """Entrada que impede a verificação (README sem tabela, branch sem bruto do TCGCSV)."""


@dataclass(frozen=True)
class LinhaRegistro:
    data: dt.date
    motivo: str  # já sem espaços nas pontas; vazio = linha sem motivo


@dataclass(frozen=True)
class Dia:
    data: dt.date
    origem: str
    faltam: tuple[str, ...] = ()
    motivo: str = ""
    registro_sem_motivo: bool = False


@dataclass
class Resultado:
    inicio: dt.date
    fim: dt.date
    dias: list[Dia]
    avisos: list[str] = field(default_factory=list)

    def _com(self, origem: str) -> list[Dia]:
        return [d for d in self.dias if d.origem == origem]

    @property
    def faltantes(self) -> list[dt.date]:
        return [d.data for d in self._com(FALTANTE)]

    @property
    def codigo_saida(self) -> int:
        return FALHA if self.faltantes else SUCESSO


# ---------------------------------------------------------------- README


def ler_dias_sem_coleta(texto: str) -> tuple[list[LinhaRegistro], list[str]]:
    """Linhas da tabela "Dias sem coleta" e avisos de linhas ilegíveis.

    A seção começa no título `## Dias sem coleta` e vai até o próximo título
    `#`. Cabeçalho (`data`) e separador (`---`) são ignorados.
    """
    linhas = texto.splitlines()
    try:
        inicio = next(i for i, l in enumerate(linhas) if l.strip() == TITULO_SECAO)
    except StopIteration:
        raise CoberturaError(f"README sem a seção '{TITULO_SECAO}'") from None

    registros: list[LinhaRegistro] = []
    avisos: list[str] = []
    for linha in linhas[inicio + 1:]:
        if linha.startswith("#"):
            break
        linha = linha.strip()
        if not linha.startswith("|"):
            continue
        celulas = [c.strip() for c in linha.strip("|").split("|")]
        primeira = celulas[0]
        if primeira.lower() == "data" or re.fullmatch(r":?-+:?", primeira):
            continue
        motivo = " ".join(c for c in celulas[1:] if c)
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", primeira):
                raise ValueError
            data = dt.date.fromisoformat(primeira)
        except ValueError:
            avisos.append(f"linha da tabela com data inválida ignorada: {linha}")
            continue
        registros.append(LinhaRegistro(data=data, motivo=motivo))
    return registros, avisos


# ---------------------------------------------------------------- bruto


_PADRAO_CHAVE = re.compile(
    r"raw/(?P<fonte>[a-z0-9_]+)/group_id=(?P<gid>\d+)/data=(?P<data>\d{4}-\d{2}-\d{2})/(?P<arquivo>[^/]+)"
)


def arquivos_por_data(
    chaves: Iterable[str], group_id: int
) -> tuple[dict[dt.date, set[tuple[str, str]]], list[str]]:
    """Agrupa as chaves do bruto por data: {data: {(fonte, arquivo)}}; avisa as ignoradas."""
    por_data: dict[dt.date, set[tuple[str, str]]] = {}
    avisos: list[str] = []
    for chave in chaves:
        m = _PADRAO_CHAVE.fullmatch(chave)
        if m is None or int(m["gid"]) != group_id:
            avisos.append(f"chave fora do contrato do bruto ou de outro group_id ignorada: {chave}")
            continue
        try:
            data = dt.date.fromisoformat(m["data"])
        except ValueError:
            avisos.append(f"chave com data inválida ignorada: {chave}")
            continue
        por_data.setdefault(data, set()).add((m["fonte"], m["arquivo"]))
    return por_data, avisos


# ---------------------------------------------------------------- verificação


def verificar(
    chaves: Iterable[str], registros: Iterable[LinhaRegistro], group_id: int
) -> Resultado:
    """Classifica cada data de calendário do primeiro ao último dia (RF-27)."""
    por_data, avisos = arquivos_por_data(chaves, group_id)
    datas_tcgcsv = [d for d, arqs in por_data.items() if any(f == FONTE_TCGCSV for f, _ in arqs)]
    if not datas_tcgcsv:
        raise CoberturaError("nenhum arquivo do TCGCSV no bruto: primeiro e último dia indefinidos")
    inicio, fim = min(datas_tcgcsv), max(datas_tcgcsv)

    com_motivo: dict[dt.date, str] = {}
    sem_motivo: set[dt.date] = set()
    for r in registros:
        if not inicio <= r.data <= fim:
            avisos.append(f"registro fora do período {inicio} a {fim} ignorado: {r.data}")
        elif r.motivo:
            com_motivo.setdefault(r.data, r.motivo)
        else:
            sem_motivo.add(r.data)

    esperados = [(a.fonte, a.arquivo) for a in ARQUIVOS_DO_DIA]
    dias: list[Dia] = []
    data = inicio
    while data <= fim:
        presentes = por_data.get(data, set())
        faltam = tuple(arquivo for fonte, arquivo in esperados if (fonte, arquivo) not in presentes)
        if not faltam:
            if data in com_motivo or data in sem_motivo:
                avisos.append(f"data com os quatro arquivos também registrada na tabela: {data}")
            dias.append(Dia(data, BRUTO))
        elif data in com_motivo:
            dias.append(Dia(data, REGISTRO, faltam, motivo=com_motivo[data]))
        else:
            dias.append(Dia(data, FALTANTE, faltam, registro_sem_motivo=data in sem_motivo))
        data += dt.timedelta(days=1)
    return Resultado(inicio=inicio, fim=fim, dias=dias, avisos=avisos)


def formatar(resultado: Resultado) -> str:
    """Relatório em texto, uma data por linha (formato lido pela T-49 e pela T-52)."""
    r = resultado
    saida = [f"periodo: {r.inicio} a {r.fim} ({len(r.dias)} datas)"]
    for dia in r.dias:
        faltam = ", ".join(dia.faltam)
        if dia.origem == BRUTO:
            saida.append(f"{dia.data} {BRUTO}")
        elif dia.origem == REGISTRO:
            saida.append(f"{dia.data} {REGISTRO}: {dia.motivo} (faltam: {faltam})")
        else:
            prefixo = "registro sem motivo; " if dia.registro_sem_motivo else ""
            saida.append(f"{dia.data} {FALTANTE}: {prefixo}faltam {faltam}")
    saida.append(
        f"resumo: {len(r.dias)} datas, {len(r._com(BRUTO))} com bruto, "
        f"{len(r._com(REGISTRO))} registradas, {len(r.faltantes)} faltantes"
    )
    if r.faltantes:
        saida.append("datas faltantes: " + ", ".join(str(d) for d in r.faltantes))
    return "\n".join(saida) + "\n"


# ---------------------------------------------------------------- CLI


def executar(
    repo: Path = RAIZ_REPO,
    readme: Path | None = None,
    buscar: bool = True,
    group_id: int | None = None,
    saida=None,
) -> int:
    saida = saida or sys.stdout
    readme = readme or repo / "README.md"
    group_id = group_id if group_id is not None else ler_colecao().group_id
    try:
        if buscar:
            leitor_branch.buscar(repo)
        chaves = [a.chave for a in leitor_branch.listar(repo)]
    except LeitorBranchError:
        return ERRO
    try:
        registros, avisos_readme = ler_dias_sem_coleta(readme.read_text(encoding="utf-8"))
        resultado = verificar(chaves, registros, group_id)
    except (CoberturaError, OSError) as erro:
        log.error("verificação de cobertura recusada: %s", erro)
        return ERRO
    for aviso in avisos_readme + resultado.avisos:
        log.warning(aviso)
    saida.write(formatar(resultado))
    log.info(
        "cobertura: %d datas, %d faltantes", len(resultado.dias), len(resultado.faltantes)
    )
    return resultado.codigo_saida


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tcg.cobertura.verificador", description=__doc__.splitlines()[0]
    )
    parser.add_argument("--repo", type=Path, default=RAIZ_REPO, help="clone com o remoto origin")
    parser.add_argument("--readme", type=Path, default=None, help="README com a tabela (padrão: <repo>/README.md)")
    parser.add_argument(
        "--sem-buscar", action="store_true",
        help="não faz git fetch; lê a ref local origin/dados-raw",
    )
    args = parser.parse_args(argv)
    configurar_log(fluxo=sys.stderr)
    return executar(args.repo, args.readme, buscar=not args.sem_buscar)


if __name__ == "__main__":
    sys.exit(main())
