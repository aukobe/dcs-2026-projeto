"""Testes do workflow do Coletor diário (T-10, T-57, T-58; RF-01, RF-05, RNF-08, RNF-13).

Lê `.github/workflows/coleta.yml` com `yaml.safe_load`. No YAML 1.1 a chave
`on:` vira o booleano True; os gatilhos são buscados pelos dois casos.
"""

from pathlib import Path
import re
import tomllib

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[2]
WORKFLOW = RAIZ / ".github" / "workflows" / "coleta.yml"
SINCRONIZAR = "sincronizar com o data lake da turma"
SECRETS_ESPERADOS = {
    "MINIO_ENDPOINT": "${{ secrets.MINIO_ENDPOINT }}",
    "MINIO_ACCESS_KEY": "${{ secrets.MINIO_ACCESS_KEY }}",
    "MINIO_SECRET_KEY": "${{ secrets.MINIO_SECRET_KEY }}",
}


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


# --- T-58: sincronização com o data lake da turma (ADR-008; RF-05, RNF-08) ---


def test_sem_gatilho_de_pull_request(gatilhos):
    # Secrets não podem ficar ao alcance de código vindo de pull request.
    assert "pull_request" not in gatilhos
    assert "pull_request_target" not in gatilhos


def test_sincronizacao_depois_do_push_e_antes_do_resultado(passos):
    nomes = [p.get("name") for p in passos]
    assert nomes.index("publicar na dados-raw") < nomes.index(SINCRONIZAR) < nomes.index("resultado da coleta")


def test_sincronizacao_so_com_codigo_0_ou_1_e_publicacao_concluida(passos):
    publicar = _passo(passos, "publicar na dados-raw")
    assert publicar["id"] == "publicar"
    condicao = _passo(passos, SINCRONIZAR)["if"]
    assert "steps.coleta.outputs.codigo == '0'" in condicao
    assert "steps.coleta.outputs.codigo == '1'" in condicao
    assert "steps.publicar.outcome == 'success'" in condicao
    assert "'2'" not in condicao
    # Sem always(), failure() nem cancelled(): o passo não roda se a publicação falhou.
    assert not re.search(r"always\(|failure\(|cancelled\(", condicao)


def test_sincronizacao_roda_o_sincronizador_sobre_a_dados_raw(passos):
    caminho_main = next(p["with"]["path"] for p in _checkouts(passos) if p["with"]["ref"] == "main")
    caminho_dados = next(p["with"]["path"] for p in _checkouts(passos) if p["with"]["ref"] == "dados-raw")
    passo = _passo(passos, SINCRONIZAR)
    assert passo["working-directory"] == caminho_main
    assert passo["run"].strip() == f"python -m tcg.sync.sincronizador --repo ../{caminho_dados}"


def test_sincronizacao_com_tls_bucket_e_group_id_literais(passos):
    env = _passo(passos, SINCRONIZAR)["env"]
    assert env["MINIO_SECURE"] == "true"
    assert env["MINIO_BUCKET"] == "tcg"
    colecao = tomllib.loads((RAIZ / "config" / "colecao.toml").read_text(encoding="utf-8"))
    assert env["GROUP_ID"] == str(colecao["group_id"]) == "24269"


def test_secrets_so_no_env_do_passo_de_sincronizacao(texto, wf, job, passos):
    env = _passo(passos, SINCRONIZAR)["env"]
    assert {k: v for k, v in env.items() if "secrets." in str(v)} == SECRETS_ESPERADOS
    # Exatamente três referências a secrets no arquivo inteiro: as do env acima.
    assert len(re.findall(r"secrets\.", texto)) == len(SECRETS_ESPERADOS)
    assert "secrets." not in str(wf.get("env", ""))
    assert "secrets." not in str({k: v for k, v in job.items() if k != "steps"})
    for passo in passos:
        if passo.get("name") != SINCRONIZAR:
            assert "secrets." not in str(passo), f"secret fora do passo de sincronização: {passo.get('name')}"


def test_secrets_nunca_em_run_echo_ou_set_x(texto, passos):
    sincronizar = _passo(passos, SINCRONIZAR)
    assert "${{" not in sincronizar["run"]
    assert "secrets." not in sincronizar["run"]
    assert not re.search(r"set\s+-[a-z]*x", texto)
    for passo in passos:
        for linha in str(passo.get("run", "")).splitlines():
            if re.search(r"\b(echo|printf|printenv|env)\b", linha):
                assert "MINIO_" not in linha, f"variável MINIO_* impressa em: {linha.strip()}"
            assert "printenv" not in linha


def test_falha_da_sincronizacao_marca_o_job_e_nao_desfaz_o_push(job, passos):
    # Sem continue-on-error: a falha do passo deixa o job vermelho.
    assert "continue-on-error" not in job
    assert all("continue-on-error" not in p for p in passos)
    # Nenhum comando que desfaça o push depois dele.
    depois = passos[[p.get("name") for p in passos].index(SINCRONIZAR):]
    for passo in depois:
        assert not re.search(r"\bgit\s+(push|reset|revert)\b", str(passo.get("run", "")))
