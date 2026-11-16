"""Testes do README (T-49; RNF-09, RNF-10, RNF-13).

Confere as seções obrigatórias, a lista de serviços com custo zero, o roteiro de
"Como rodar", os horários da coleta (iguais aos do workflow), os riscos R-01 e
R-02 com a regra do ADR-007, os links relativos e a tabela "Dias sem coleta"
no formato que o Verificador de cobertura (T-48) lê. Não lê o `.env`.
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest
import yaml

from tcg.cobertura.verificador import ler_dias_sem_coleta

RAIZ = Path(__file__).resolve().parents[2]
TEXTO = (RAIZ / "README.md").read_text(encoding="utf-8")

SECOES = [
    "Coleção escolhida",
    "Visão geral",
    "Perguntas e carteiras",
    "Serviços usados e custo zero",
    "Coleta agendada",
    "Riscos do agendador",
    "Data lake",
    "Como rodar",
    "Documentação e evidências",
    "Dias sem coleta",
]


def secao(titulo: str) -> str:
    """Corpo da seção `## titulo` até o próximo título de nível 2."""
    m = re.search(rf"^## {re.escape(titulo)}\n(.*?)(?=^## |\Z)", TEXTO, re.M | re.S)
    assert m, f"seção ausente: {titulo}"
    return m.group(1)


def test_secoes_obrigatorias_na_ordem():
    titulos = re.findall(r"^## (.+)$", TEXTO, re.M)
    assert titulos == SECOES


@pytest.mark.parametrize(
    "servico",
    ["GitHub Actions", "Codespaces", "TCGCSV", "Banco Central", "RustFS", "MinIO", "Python 3.13"],
)
def test_servico_listado(servico):
    assert servico in secao("Serviços usados e custo zero")


def test_todo_servico_da_tabela_e_gratuito():
    linhas = [
        l for l in secao("Serviços usados e custo zero").splitlines()
        if l.startswith("|") and not l.startswith(("| Serviço", "|---"))
    ]
    assert len(linhas) >= 6
    for linha in linhas:
        custo = linha.strip("|").split("|")[-1]
        assert "gratuito" in custo, linha


def test_como_rodar_do_clone_limpo_na_ordem():
    texto = secao("Como rodar")
    for trecho in ("Python 3.13", "Docker", "Codespaces", "make setup", "cp .env.example .env", "make up"):
        assert trecho in texto, trecho
    comandos = re.findall(r"^make (\w+)", texto, re.M)
    assert comandos == ["setup", "sync", "silver", "gold", "painel", "test", "cobertura"]


def test_diferenca_entre_minio_local_e_data_lake_da_turma():
    texto = secao("Data lake")
    assert "lake-aulas-mackenzie.afonsolelis.tech" in texto
    assert "localhost:9000" in texto
    assert "bucket `tcg`" in texto


def test_horarios_da_coleta_iguais_aos_do_workflow():
    workflow = yaml.safe_load((RAIZ / ".github/workflows/coleta.yml").read_text(encoding="utf-8"))
    gatilhos = workflow.get("on", workflow.get(True))
    crons = [item["cron"] for item in gatilhos["schedule"]]
    texto = secao("Coleta agendada")
    assert crons == ["30 20 * * *", "30 6 * * *"]
    for cron in crons:
        assert f"`{cron}`" in texto
    assert "ADR-007" in texto
    assert "20h00 UTC" in texto
    # exemplos da regra do ciclo (spec, Definições)
    assert "2026-11-05T19:59Z" in texto and "2026-11-05T20:00Z" in texto


def test_riscos_r01_pela_regra_do_adr_007_e_r02():
    texto = secao("Riscos do agendador")
    assert "R-01" in texto and "R-02" in texto
    assert "antes das 20h UTC de D+1" in texto
    assert "ADR-007" in texto
    assert "23h59" not in TEXTO  # regra antiga, substituída pelo ADR-007
    assert "60 dias" in texto and "12/12/2026" in texto


def test_tabela_dias_sem_coleta_no_formato_do_verificador():
    texto = secao("Dias sem coleta")
    assert "| data | motivo |" in texto
    registros, avisos = ler_dias_sem_coleta(TEXTO)
    assert registros == []  # make cobertura de 16/11: 13 datas, 0 faltantes
    assert avisos == []


def test_observacao_de_04_11_fica_fora_da_tabela():
    texto = secao("Dias sem coleta")
    linhas_tabela = [l for l in texto.splitlines() if l.startswith("|")]
    assert not any("2026-11-04" in l for l in linhas_tabela)
    assert "2026-11-04" in texto and "manual" in texto


def test_links_relativos_apontam_para_arquivos_existentes():
    links = re.findall(r"\]\(([^)#]+)\)", TEXTO)
    relativos = [l for l in links if not l.startswith(("http://", "https://"))]
    assert len(relativos) >= 10
    for link in relativos:
        assert (RAIZ / link).exists(), link
    for n in range(1, 9):
        assert f"ADR-00{n}" in secao("Documentação e evidências")


def test_nenhuma_credencial_no_readme():
    for linha in TEXTO.splitlines():
        m = re.match(r"\s*(MINIO_ACCESS_KEY|MINIO_SECRET_KEY)\s*=\s*(.*)$", linha)
        if m:
            assert m.group(2) == "" or re.fullmatch(r"<[^>]+>", m.group(2)), linha
