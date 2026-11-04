"""Integração com MinIO descartável (T-19; RNF-07, RF-02, RF-05).

Sobe, por testcontainers, um MinIO com a mesma imagem e tag do
`docker-compose.yml` (lida do próprio arquivo, ADR-002), numa porta aleatória
do host e com credenciais geradas na hora; o `.env` não é lido. Testa
gravação, sincronização e recusa de sobrescrita e, no encerramento, confere
que o contêiner de teste foi removido e que o MinIO local de trabalho não
mudou (mesmo Id, StartedAt e RestartCount).

O Ryuk (contêiner de limpeza do testcontainers) fica desligado só neste
módulo, para não baixar outra imagem; a remoção é feita por `stop()` e
conferida pela label `tcg.teste=T-19`.
"""

from __future__ import annotations

import hashlib
import io
import logging
import os
from pathlib import Path
import secrets
import subprocess

import pytest
import yaml

from tcg.lake.cliente import garantir_bucket
from tcg.log import configurar_log
from tcg.sync import sincronizador
from tcg.sync.leitor_branch import ArquivoBranch
from tcg.sync.sincronizador import sha1_blob, sincronizar

docker = pytest.importorskip("docker")
from testcontainers.community.minio import MinioContainer  # noqa: E402
from testcontainers.core.config import testcontainers_config  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
COMPOSE = RAIZ / "docker-compose.yml"
LABEL = ("tcg.teste", "T-19")
GROUP_ID = 24269
DATA = "2026-11-03"

PRODUCTS = f"raw/tcgplayer/group_id=24269/data={DATA}/products.json"
PRICES = f"raw/tcgplayer/group_id=24269/data={DATA}/prices.json"
PTAX = f"raw/bcb_ptax/group_id=24269/data={DATA}/cotacao.json"
CDI = f"raw/bcb_cdi/group_id=24269/data={DATA}/cdi.json"

CONTEUDOS = {
    PRODUCTS: b'{"results": [\r\n  {"productId": 1}\r\n]}\r\n',
    PRICES: b'{"results": []}\n\r\n\rfim sem quebra',
    PTAX: b'{"value": [{"cotacaoVenda": 5.3}]}\r\n\xff\xfe\x00bytes nao utf-8',
    CDI: b'[{"data": "03/11/2026", "valor": "0.055131"}]',
}


def _sha256(corpo: bytes) -> str:
    return hashlib.sha256(corpo).hexdigest()


def _imagem_do_compose() -> str:
    compose = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    imagem = compose["services"]["minio"]["image"]
    _, _, tag = imagem.rpartition(":")
    assert tag and tag != "latest", f"imagem do compose sem tag fixada: {imagem}"
    return imagem


def _docker():
    try:
        cliente = docker.from_env()
        cliente.ping()
    except Exception as erro:  # sem Docker não há como subir o MinIO descartável
        pytest.skip(f"Docker indisponível: {type(erro).__name__}")
    return cliente


def _conteineres_de_teste(cliente_docker) -> list:
    return cliente_docker.containers.list(all=True, filters={"label": f"{LABEL[0]}={LABEL[1]}"})


def _minio_de_trabalho(cliente_docker) -> dict | None:
    """Estado do MinIO local de trabalho (serviço `minio` do compose), se estiver no ar."""
    for conteiner in cliente_docker.containers.list(
        all=True, filters={"label": "com.docker.compose.service=minio"}
    ):
        if conteiner.labels.get(LABEL[0]) == LABEL[1]:
            continue
        estado = conteiner.attrs["State"]
        return {
            "id": conteiner.id,
            "started_at": estado["StartedAt"],
            "restart_count": conteiner.attrs["RestartCount"],
            "status": estado["Status"],
        }
    return None


@pytest.fixture(scope="module")
def minio_descartavel():
    cliente_docker = _docker()
    assert _conteineres_de_teste(cliente_docker) == [], "sobrou contêiner de uma execução anterior"
    trabalho_antes = _minio_de_trabalho(cliente_docker)

    ryuk_original = testcontainers_config.ryuk_disabled
    testcontainers_config.ryuk_disabled = True
    usuario = "teste-" + secrets.token_hex(6)
    senha = secrets.token_urlsafe(24)
    conteiner = (
        MinioContainer(image=_imagem_do_compose(), access_key=usuario, secret_key=senha)
        .with_env("MINIO_ROOT_USER", usuario)
        .with_env("MINIO_ROOT_PASSWORD", senha)
        .with_kwargs(labels={LABEL[0]: LABEL[1]})
    )
    try:
        conteiner.start()
        config = conteiner.get_config()
        assert not config["endpoint"].endswith(":9000"), "o MinIO descartável não pode usar a porta 9000"
        yield {
            "cliente": conteiner.get_client(),
            "endpoint": config["endpoint"],
            "usuario": usuario,
            "senha": senha,
        }
    finally:
        conteiner.stop()
        testcontainers_config.ryuk_disabled = ryuk_original

    assert _conteineres_de_teste(cliente_docker) == [], "o contêiner de teste não foi removido"
    trabalho_depois = _minio_de_trabalho(cliente_docker)
    if trabalho_antes is None:
        logging.getLogger(__name__).warning("MinIO local de trabalho fora do ar; conferência pulada")
    else:
        assert trabalho_depois == trabalho_antes, "o MinIO local de trabalho mudou durante o teste"


def test_imagem_igual_a_do_compose(minio_descartavel):
    cliente_docker = _docker()
    (conteiner,) = _conteineres_de_teste(cliente_docker)
    assert conteiner.attrs["Config"]["Image"] == _imagem_do_compose()


def test_bucket_criado_uma_vez(minio_descartavel, caplog):
    cliente = minio_descartavel["cliente"]
    bucket = "tcg-bucket"
    assert not cliente.bucket_exists(bucket)

    with caplog.at_level(logging.INFO):
        assert garantir_bucket(cliente, bucket) is True
        assert garantir_bucket(cliente, bucket) is False

    assert cliente.bucket_exists(bucket)
    assert f"bucket criado: {bucket}" in caplog.text
    assert f"bucket já existe, não recriado: {bucket}" in caplog.text


def test_gravacao_arquivo_novo(minio_descartavel):
    cliente = minio_descartavel["cliente"]
    bucket = "tcg-gravacao"
    garantir_bucket(cliente, bucket)
    corpo = CONTEUDOS[PTAX]

    resumo = sincronizar(
        cliente, bucket, GROUP_ID, [ArquivoBranch(PTAX, sha1_blob(corpo))], lambda blob: corpo
    )

    assert resumo.enviados == [PTAX] and resumo.codigo_saida == sincronizador.SUCESSO
    gravado = cliente.get_object(bucket, PTAX)
    try:
        assert _sha256(gravado.read()) == _sha256(corpo)
    finally:
        gravado.close()
        gravado.release_conn()


def test_recusa_de_sobrescrita(minio_descartavel, caplog):
    cliente = minio_descartavel["cliente"]
    bucket = "tcg-recusa"
    garantir_bucket(cliente, bucket)
    original = b'{"results": ["original"]}'
    cliente.put_object(bucket, PRICES, io.BytesIO(original), len(original))
    antes = cliente.stat_object(bucket, PRICES)
    outro = b'{"results": ["outro conteudo"]}\r\n'

    with caplog.at_level(logging.INFO):
        resumo = sincronizar(
            cliente, bucket, GROUP_ID, [ArquivoBranch(PRICES, sha1_blob(outro))], lambda blob: outro
        )

    depois = cliente.stat_object(bucket, PRICES)
    assert resumo.recusados == [PRICES] and resumo.enviados == []
    assert (depois.etag, depois.last_modified, depois.size) == (antes.etag, antes.last_modified, antes.size)
    assert _sha256(cliente.get_object(bucket, PRICES).read()) == _sha256(original)
    assert f"recusa de sobrescrita: chave já existe no MinIO, não regravada: {PRICES}" in caplog.text


# --- sincronização a partir de uma branch dados-raw num repositório temporário ---


def _git(repo, *args, env):
    return subprocess.run(["git", "-C", str(repo), *args], env=env, check=True, capture_output=True).stdout


@pytest.fixture
def repo_com_branch(tmp_path, monkeypatch):
    """Remoto bare com `main` e `dados-raw`; devolve um clone só com a `main`."""
    home = tmp_path / "home"
    home.mkdir()
    env = {
        **os.environ,
        "HOME": str(home),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "Teste",
        "GIT_AUTHOR_EMAIL": "teste@example.invalid",
        "GIT_COMMITTER_NAME": "Teste",
        "GIT_COMMITTER_EMAIL": "teste@example.invalid",
    }
    for nome in ("HOME", "GIT_CONFIG_NOSYSTEM"):
        monkeypatch.setenv(nome, env[nome])

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
    (autor / ".gitattributes").write_bytes(b"* -text\n")
    for chave, corpo in CONTEUDOS.items():
        caminho = autor / chave
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(corpo)
    _git(autor, "add", "-A", env=env)
    _git(autor, "commit", "-q", "-m", f"dados(coleta): {DATA} [RF-01]", env=env)
    _git(autor, "push", "-q", "origin", "dados-raw", env=env)

    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "-q", "--single-branch", "-b", "main", str(remoto), str(clone)],
        env=env, check=True,
    )
    return clone


def test_sincronizacao_da_branch_duas_vezes(minio_descartavel, repo_com_branch, monkeypatch):
    cliente = minio_descartavel["cliente"]
    bucket = "tcg"
    variaveis = {
        "MINIO_ENDPOINT": minio_descartavel["endpoint"],
        "MINIO_ACCESS_KEY": minio_descartavel["usuario"],
        "MINIO_SECRET_KEY": minio_descartavel["senha"],
        "MINIO_BUCKET": bucket,
        "MINIO_SECURE": "false",
        "GROUP_ID": str(GROUP_ID),
    }
    for nome, valor in variaveis.items():
        monkeypatch.setenv(nome, valor)
    saida = io.StringIO()
    handler = configurar_log(fluxo=saida)
    try:
        primeira = sincronizador.executar(repo_com_branch, cliente=cliente)
        texto_primeira = saida.getvalue()
        segunda = sincronizador.executar(repo_com_branch, cliente=cliente)
    finally:
        logging.getLogger().removeHandler(handler)
    texto = saida.getvalue()
    texto_segunda = texto[len(texto_primeira):]

    assert primeira == segunda == sincronizador.SUCESSO
    assert "enviados=4 recusados=0 fora_do_escopo=0 falhas=0" in texto_primeira
    assert "enviados=0 recusados=4 fora_do_escopo=0 falhas=0" in texto_segunda
    assert texto_segunda.count("recusa de sobrescrita") == 4

    chaves = sorted(o.object_name for o in cliente.list_objects(bucket, recursive=True))
    assert chaves == sorted(CONTEUDOS)
    assert all(c.startswith("raw/") and "/group_id=24269/" in c for c in chaves)
    for chave, corpo in CONTEUDOS.items():
        assert _sha256(cliente.get_object(bucket, chave).read()) == _sha256(corpo)

    assert minio_descartavel["usuario"] not in texto
    assert minio_descartavel["senha"] not in texto
