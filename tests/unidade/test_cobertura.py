"""Testes do Verificador de cobertura (T-48, RF-27).

Contas dos períodos (datas de calendário, extremos incluídos):
- 2026-11-03 a 2026-11-05: 5 − 3 + 1 = 3 datas;
- 2026-11-03 a 2026-11-06: 6 − 3 + 1 = 4 datas.

O teste ponta a ponta monta um remoto bare local com a branch `dados-raw` e um
clone só com a `main`, como em `test_leitor_branch.py`; nenhum acesso à rede
nem a data lake.
"""

from __future__ import annotations

import datetime as dt
import io
import os
from pathlib import Path
import subprocess

import pytest

from tcg.cobertura import verificador
from tcg.cobertura.verificador import (
    BRUTO,
    FALTANTE,
    REGISTRO,
    CoberturaError,
    LinhaRegistro,
    formatar,
    ler_dias_sem_coleta,
    verificar,
)

GID = 24269
QUATRO = ("products.json", "prices.json", "cotacao.json", "cdi.json")
FONTE = {
    "products.json": "tcgplayer",
    "prices.json": "tcgplayer",
    "cotacao.json": "bcb_ptax",
    "cdi.json": "bcb_cdi",
}


def chaves(data: str, arquivos=QUATRO, gid: int = GID) -> list[str]:
    return [f"raw/{FONTE[a]}/group_id={gid}/data={data}/{a}" for a in arquivos]


def d(texto: str) -> dt.date:
    return dt.date.fromisoformat(texto)


README = """# Projeto

## Como rodar

| data | motivo |
|------|--------|
| 2026-11-04 | tabela de outra seção, não conta |

## Dias sem coleta

| data | motivo |
|------|--------|
| 2026-11-04 | atraso do agendador depois das 20h UTC de D+1 |
| 2026-11-05 |  |
| 04/11/2026 | data em outro formato |
| 2026-02-30 | data inexistente |

## Outra seção

| 2026-11-09 | depois da seção, não conta |
"""


# ---------------------------------------------------------------- README


def test_le_so_a_tabela_da_secao_dias_sem_coleta():
    registros, avisos = ler_dias_sem_coleta(README)

    assert registros == [
        LinhaRegistro(d("2026-11-04"), "atraso do agendador depois das 20h UTC de D+1"),
        LinhaRegistro(d("2026-11-05"), ""),
    ]
    assert len(avisos) == 2
    assert any("04/11/2026" in a for a in avisos)
    assert any("2026-02-30" in a for a in avisos)


def test_tabela_vazia_do_readme_atual_nao_tem_registros():
    texto = "## Dias sem coleta\n\n| data | motivo |\n|------|--------|\n"
    assert ler_dias_sem_coleta(texto) == ([], [])


def test_readme_sem_a_secao_e_erro():
    with pytest.raises(CoberturaError, match="Dias sem coleta"):
        ler_dias_sem_coleta("# Projeto\n\n## Como rodar\n")


# ---------------------------------------------------------------- verificação


def test_periodo_completo_termina_com_sucesso():
    todas = chaves("2026-11-03") + chaves("2026-11-04") + chaves("2026-11-05")

    resultado = verificar(todas, [], GID)

    assert (resultado.inicio, resultado.fim) == (d("2026-11-03"), d("2026-11-05"))
    assert len(resultado.dias) == 3  # 5 − 3 + 1
    assert all(dia.origem == BRUTO for dia in resultado.dias)
    assert resultado.faltantes == []
    assert resultado.codigo_saida == 0


def test_dia_sem_arquivo_e_sem_linha_falha_e_e_listado():
    todas = chaves("2026-11-03") + chaves("2026-11-05")

    resultado = verificar(todas, [], GID)

    assert resultado.faltantes == [d("2026-11-04")]
    assert resultado.dias[1].faltam == QUATRO
    assert resultado.codigo_saida == 1
    assert "datas faltantes: 2026-11-04" in formatar(resultado)


def test_dia_registrado_com_motivo_conta_como_coberto():
    todas = chaves("2026-11-03") + chaves("2026-11-05")
    registros = [LinhaRegistro(d("2026-11-04"), "atraso do agendador")]

    resultado = verificar(todas, registros, GID)

    dia = resultado.dias[1]
    assert (dia.origem, dia.motivo) == (REGISTRO, "atraso do agendador")
    assert resultado.codigo_saida == 0


def test_linha_sem_motivo_nao_conta():
    todas = chaves("2026-11-03") + chaves("2026-11-05")
    registros = [LinhaRegistro(d("2026-11-04"), "")]

    resultado = verificar(todas, registros, GID)

    dia = resultado.dias[1]
    assert dia.origem == FALTANTE and dia.registro_sem_motivo
    assert resultado.codigo_saida == 1
    assert "2026-11-04 faltante: registro sem motivo; faltam" in formatar(resultado)


def test_dia_parcial_sem_linha_lista_o_arquivo_que_falta():
    todas = chaves("2026-11-03") + chaves("2026-11-04", QUATRO[:3]) + chaves("2026-11-05")

    resultado = verificar(todas, [], GID)

    assert resultado.dias[1].origem == FALTANTE
    assert resultado.dias[1].faltam == ("cdi.json",)
    assert resultado.faltantes == [d("2026-11-04")]


def test_periodo_definido_so_pelo_tcgcsv():
    # cotacao.json em 2026-11-01 não estende o período; TCGCSV de 03 a 05 → 3 datas
    todas = chaves("2026-11-01", ("cotacao.json",)) + [
        c for data in ("2026-11-03", "2026-11-04", "2026-11-05") for c in chaves(data)
    ]

    resultado = verificar(todas, [], GID)

    assert (resultado.inicio, resultado.fim) == (d("2026-11-03"), d("2026-11-05"))
    assert len(resultado.dias) == 3


def test_registro_fora_do_periodo_e_outro_group_id_viram_aviso():
    todas = chaves("2026-11-03") + chaves("2026-11-04", gid=99999)
    registros = [LinhaRegistro(d("2026-10-01"), "antes da primeira coleta")]

    resultado = verificar(todas, registros, GID)

    assert len(resultado.dias) == 1 and resultado.codigo_saida == 0
    assert any("fora do período" in a for a in resultado.avisos)
    assert any("group_id=99999" in a for a in resultado.avisos)


def test_bruto_sem_tcgcsv_e_erro():
    with pytest.raises(CoberturaError, match="TCGCSV"):
        verificar(chaves("2026-11-03", ("cotacao.json", "cdi.json")), [], GID)


def test_formato_do_relatorio():
    todas = (
        chaves("2026-11-03")
        + chaves("2026-11-05", ("products.json", "cotacao.json"))
        + chaves("2026-11-07")
    )
    registros = [
        LinhaRegistro(d("2026-11-04"), "atraso do agendador"),
        LinhaRegistro(d("2026-11-06"), ""),
    ]

    texto = formatar(verificar(todas, registros, GID))

    assert texto == (
        "periodo: 2026-11-03 a 2026-11-07 (5 datas)\n"
        "2026-11-03 bruto\n"
        "2026-11-04 registro: atraso do agendador "
        "(faltam: products.json, prices.json, cotacao.json, cdi.json)\n"
        "2026-11-05 faltante: faltam prices.json, cdi.json\n"
        "2026-11-06 faltante: registro sem motivo; "
        "faltam products.json, prices.json, cotacao.json, cdi.json\n"
        "2026-11-07 bruto\n"
        "resumo: 5 datas, 2 com bruto, 1 registradas, 2 faltantes\n"
        "datas faltantes: 2026-11-05, 2026-11-06\n"
    )


# ---------------------------------------------------------------- ponta a ponta (git local)


@pytest.fixture
def ambiente(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    for nome, valor in {
        "HOME": str(home),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "Teste",
        "GIT_AUTHOR_EMAIL": "teste@example.invalid",
        "GIT_COMMITTER_NAME": "Teste",
        "GIT_COMMITTER_EMAIL": "teste@example.invalid",
    }.items():
        monkeypatch.setenv(nome, valor)
    return {**os.environ}


def _git(repo: Path, *args: str, env) -> None:
    subprocess.run(["git", "-C", str(repo), *args], env=env, check=True, capture_output=True)


def _repos(tmp_path: Path, env, chaves_branch: list[str]) -> Path:
    """Remoto bare com `main` e `dados-raw`; devolve o clone só com a `main`."""
    remoto = tmp_path / "remoto.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remoto)], env=env, check=True)
    autor = tmp_path / "autor"
    subprocess.run(["git", "init", "-q", "-b", "main", str(autor)], env=env, check=True)
    (autor / "codigo.py").write_text("print('main')\n")
    _git(autor, "add", "codigo.py", env=env)
    _git(autor, "commit", "-q", "-m", "inicial", env=env)
    _git(autor, "remote", "add", "origin", str(remoto), env=env)
    _git(autor, "push", "-q", "origin", "main", env=env)

    _git(autor, "checkout", "-q", "--orphan", "dados-raw", env=env)
    _git(autor, "rm", "-rq", "--cached", ".", env=env)
    (autor / "codigo.py").unlink()
    (autor / "README.md").write_text("# dados-raw\n")
    for chave in chaves_branch:
        caminho = autor / chave
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(b"{}")
    _git(autor, "add", "-A", env=env)
    _git(autor, "commit", "-q", "-m", "dados(coleta) [RF-01]", env=env)
    _git(autor, "push", "-q", "origin", "dados-raw", env=env)

    leitor = tmp_path / "leitor"
    subprocess.run(
        ["git", "clone", "-q", "--single-branch", "-b", "main", str(remoto), str(leitor)],
        env=env, check=True,
    )
    return leitor


def test_ponta_a_ponta_pela_branch_dados_raw(tmp_path, ambiente):
    # bruto em 03, 04 e 06; 05 registrado no README → 6 − 3 + 1 = 4 datas, sucesso
    leitor = _repos(
        tmp_path, ambiente, chaves("2026-11-03") + chaves("2026-11-04") + chaves("2026-11-06")
    )
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Dias sem coleta\n\n| data | motivo |\n|------|--------|\n"
        "| 2026-11-05 | principal e reserva atrasaram até depois das 20h UTC de D+1 |\n",
        encoding="utf-8",
    )
    saida = io.StringIO()

    codigo = verificador.executar(leitor, readme, buscar=True, group_id=GID, saida=saida)

    assert codigo == 0
    assert saida.getvalue().splitlines() == [
        "periodo: 2026-11-03 a 2026-11-06 (4 datas)",
        "2026-11-03 bruto",
        "2026-11-04 bruto",
        "2026-11-05 registro: principal e reserva atrasaram até depois das 20h UTC de D+1 "
        "(faltam: products.json, prices.json, cotacao.json, cdi.json)",
        "2026-11-06 bruto",
        "resumo: 4 datas, 3 com bruto, 1 registradas, 0 faltantes",
    ]


def test_ponta_a_ponta_com_data_faltante_sai_com_1(tmp_path, ambiente):
    leitor = _repos(tmp_path, ambiente, chaves("2026-11-03") + chaves("2026-11-05"))
    readme = tmp_path / "README.md"
    readme.write_text("## Dias sem coleta\n\n| data | motivo |\n|------|--------|\n", encoding="utf-8")
    saida = io.StringIO()

    codigo = verificador.executar(leitor, readme, buscar=True, group_id=GID, saida=saida)

    assert codigo == 1
    assert "datas faltantes: 2026-11-04" in saida.getvalue()


def test_branch_sem_bruto_do_tcgcsv_sai_com_2(tmp_path, ambiente):
    leitor = _repos(tmp_path, ambiente, chaves("2026-11-03", ("cotacao.json",)))
    readme = tmp_path / "README.md"
    readme.write_text("## Dias sem coleta\n", encoding="utf-8")

    assert verificador.executar(leitor, readme, group_id=GID, saida=io.StringIO()) == 2


def test_falha_do_git_sai_com_2(tmp_path, ambiente):
    sem_repo = tmp_path / "nao_e_repo"
    sem_repo.mkdir()
    readme = tmp_path / "README.md"
    readme.write_text("## Dias sem coleta\n", encoding="utf-8")

    assert verificador.executar(sem_repo, readme, group_id=GID, saida=io.StringIO()) == 2
