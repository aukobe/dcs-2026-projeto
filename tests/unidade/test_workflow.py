"""Testes do workflow do Coletor diário (T-10, T-57; RF-01, RNF-08, RNF-13).

Lê `.github/workflows/coleta.yml` com `yaml.safe_load`. No YAML 1.1 a chave
`on:` vira o booleano True; os gatilhos são buscados pelos dois casos.
"""

from pathlib import Path
import re

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "coleta.yml"


@pytest.fixture(scope="module")
def texto():
    return WORKFLOW.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def wf(texto):
    return yaml.safe_load(texto)


@pytest.fixture(scope="module")
def gatilhos(wf):
    valor = wf.get("on", wf.get(True))
    assert valor is not None, "workflow sem gatilhos (chave 'on')"
    return valor


@pytest.fixture(scope="module")
def job(wf):
    assert list(wf["jobs"]) == ["coletar"]
    return wf["jobs"]["coletar"]


@pytest.fixture(scope="module")
def passos(job):
    return job["steps"]


def _passo(passos, nome):
    encontrados = [p for p in passos if p.get("name") == nome]
    assert len(encontrados) == 1, f"passo '{nome}' ausente ou duplicado"
    return encontrados[0]


def _checkouts(passos):
    return [p for p in passos if str(p.get("uses", "")).startswith("actions/checkout@")]


def test_cron_principal_20h30_e_reserva_06h30_utc(gatilhos):
    # ADR-007: principal às 20h30 UTC e reserva às 06h30 UTC, no mesmo ciclo do TCGCSV.
    assert gatilhos["schedule"] == [{"cron": "30 20 * * *"}, {"cron": "30 6 * * *"}]


def test_disparo_manual(gatilhos):
    assert "workflow_dispatch" in gatilhos


def test_grupo_de_concorrencia_sem_cancelar(wf):
    assert wf["concurrency"]["group"]
    assert wf["concurrency"]["cancel-in-progress"] is False


def test_permissoes_minimas(wf, job):
    assert wf["permissions"] == {"contents": "write"}
    assert "permissions" not in job


def test_nenhum_secret(texto):
    assert "secrets." not in texto


def test_user_agent_vem_de_vars(job):
    assert job["env"]["TCG_USER_AGENT"] == "${{ vars.TCG_USER_AGENT }}"


def test_python_313(passos):
    setup = [p for p in passos if str(p.get("uses", "")).startswith("actions/setup-python@")]
    assert len(setup) == 1
    assert setup[0]["with"]["python-version"] == "3.13"


def test_checkouts_main_e_dados_raw_separados(passos):
    por_ref = {p["with"]["ref"]: p["with"] for p in _checkouts(passos)}
    assert set(por_ref) == {"main", "dados-raw"}
    assert por_ref["main"]["path"] != por_ref["dados-raw"]["path"]
    assert por_ref["main"]["persist-credentials"] is False
    coleta = _passo(passos, "coletar")
    assert f"--destino ../{por_ref['dados-raw']['path']}" in coleta["run"]
    assert coleta["working-directory"] == por_ref["main"]["path"]


def test_push_so_na_dados_raw(passos):
    caminho_dados = next(p["with"]["path"] for p in _checkouts(passos) if p["with"]["ref"] == "dados-raw")
    pushes = [
        (p, linha.strip())
        for p in passos
        for linha in str(p.get("run", "")).splitlines()
        if re.search(r"\bgit\s+push\b", linha)
    ]
    assert len(pushes) == 1
    passo, linha = pushes[0]
    assert passo["working-directory"] == caminho_dados
    assert linha == "git push origin HEAD:refs/heads/dados-raw"
    assert "--force" not in linha and " -f" not in linha


def test_commit_no_formato_do_coletor(passos):
    publicar = _passo(passos, "publicar na dados-raw")
    assert 'git commit -m "dados(coleta): $datas [RF-01]"' in publicar["run"]


def test_publica_com_codigo_1_e_falha_depois(passos):
    nomes = [p.get("name") for p in passos]
    publicar = _passo(passos, "publicar na dados-raw")
    resultado = _passo(passos, "resultado da coleta")
    assert nomes.index("coletar") < nomes.index("publicar na dados-raw") < nomes.index("resultado da coleta")
    condicao = publicar["if"]
    assert "steps.coleta.outputs.codigo == '0'" in condicao
    assert "steps.coleta.outputs.codigo == '1'" in condicao
    assert "'2'" not in condicao
    assert "set +e" in _passo(passos, "coletar")["run"]
    assert resultado["if"] == "always()"
    assert resultado["env"]["CODIGO"] == "${{ steps.coleta.outputs.codigo }}"
    assert 'exit "${CODIGO:-1}"' in resultado["run"]
