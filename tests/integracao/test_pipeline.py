"""Pipeline completo contra MinIO descartável (T-34; RNF-03, RNF-11) [contêiner].

Fluxo, num bucket próprio (`tcg-pipeline`) do MinIO descartável da T-19
(mesma imagem do compose, porta aleatória, credenciais geradas na hora; o
`.env` não é lido e nem o MinIO local de trabalho nem o RustFS são tocados):

1. objetos de outra coleção (`group_id=99999`) em `raw/`, `silver/`, `gold/`
   e `gold_turma/carteira/`, gravados com `put_object` direto só neste teste,
   simulando terceiros; retrato do bucket (chave → SHA-256);
2. coleta (T-06) com o cassete da T-20 (vcrpy, `record_mode="none"`);
3. branch `dados-raw` num remoto bare temporário com os quatro brutos e
   Sincronizador (T-18) pelo mesmo `executar` do `make sync`;
4. Construtor da silver (T-27) e Construtor da gold (T-32);
5. segundo retrato do bucket.

Nada é apagado: o Sincronizador recusa sobrescrita e silver e gold só
sobrescrevem as próprias chaves (ADR-004).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import random
import re
import subprocess

import pytest
import vcr

from tcg.coleta import __main__ as coleta
from tcg.config import ConfigMinio, ler_colecao
from tcg.gold.construtor import chave_gold, construir_gold
from tcg.lake.cliente import garantir_bucket
from tcg.lake.duckdb import caminho_s3, conectar
from tcg.log import configurar_log
from tcg.silver.construtor import construir_silver
from tcg.sync import sincronizador

from test_construtor_gold import _gravar_terceiro, _hashes
from test_minio import minio_descartavel  # noqa: F401  (fixture da T-19)

PASTA_CASSETES = Path(__file__).parent / "cassetes"
CASSETE = PASTA_CASSETES / "coleta_2026-11-03.yaml"
MANIFESTO = PASTA_CASSETES / "coleta_2026-11-03.hashes.json"
AGORA = dt.datetime(2026, 11, 3, 20, 30, tzinfo=dt.UTC)
BUCKET = "tcg-pipeline"
DRI = 24269
OUTRA = 99999
SEMENTE = 34

PERMITIDOS = (
    re.compile(rf"raw/[a-z0-9_]+/group_id={DRI}/.+"),
    re.compile(rf"silver/[a-z0-9_]+/group_id={DRI}/.+"),
    re.compile(rf"gold/group_id={DRI}/.+"),
    re.compile(rf"gold_turma/carteira/group_id={DRI}/.+"),
)

TERCEIROS_AVULSOS = {
    f"raw/tcgplayer/group_id={OUTRA}/data=2026-10-10/prices.json": b'{"results": [{"productId": 1}]}',
    f"gold/group_id={OUTRA}/fato_preco_diario.parquet": b"gold de terceiro",
    f"gold_turma/carteira/group_id={OUTRA}/carteira.parquet": b"carteira de terceiro",
}


def _permitida(chave: str) -> bool:
    return any(p.fullmatch(chave) for p in PERMITIDOS) and ".." not in chave.split("/")


def _git(repo, *args, env):
    subprocess.run(["git", "-C", str(repo), *args], env=env, check=True, capture_output=True)


def _clone_com_dados_raw(tmp: Path, bruto: dict[str, bytes], monkeypatch) -> Path:
    """Remoto bare com a branch `dados-raw` (os brutos da coleta); devolve um clone da `main`."""
    home = tmp / "home"
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

    remoto = tmp / "remoto.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remoto)], env=env, check=True)
    autor = tmp / "autor"
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
    for chave, corpo in bruto.items():
        caminho = autor / chave
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(corpo)
    _git(autor, "add", "-A", env=env)
    _git(autor, "commit", "-q", "-m", "dados(coleta): 2026-11-03 [RF-01]", env=env)
    _git(autor, "push", "-q", "origin", "dados-raw", env=env)

    clone = tmp / "clone"
    subprocess.run(
        ["git", "clone", "-q", "--single-branch", "-b", "main", str(remoto), str(clone)],
        env=env, check=True,
    )
    return clone


def _ler(cliente, chave: str) -> bytes:
    resposta = cliente.get_object(BUCKET, chave)
    try:
        return resposta.read()
    finally:
        resposta.close()
        resposta.release_conn()


@pytest.fixture(scope="module")
def pipeline(minio_descartavel, tmp_path_factory):  # noqa: F811
    cliente = minio_descartavel["cliente"]
    garantir_bucket(cliente, BUCKET)

    # 1. terceiros e primeiro retrato
    _gravar_terceiro(cliente, BUCKET, tmp_path_factory.mktemp("terceiro"), OUTRA)
    for chave, corpo in TERCEIROS_AVULSOS.items():
        cliente.put_object(BUCKET, chave, io.BytesIO(corpo), len(corpo))
    antes = _hashes(cliente, BUCKET)

    with pytest.MonkeyPatch.context() as mp:
        # 2. coleta com o cassete
        mp.setenv("TCG_USER_AGENT", "colecao-dri/teste")
        pasta = tmp_path_factory.mktemp("dados_raw")
        with vcr.VCR(record_mode="none").use_cassette(str(CASSETE), allow_playback_repeats=False) as cassete:
            codigo_coleta = coleta.executar(pasta, agora=AGORA)
        bruto = {p.relative_to(pasta).as_posix(): p.read_bytes() for p in pasta.rglob("*") if p.is_file()}

        for nome, valor in {
            "MINIO_ENDPOINT": minio_descartavel["endpoint"],
            "MINIO_ACCESS_KEY": minio_descartavel["usuario"],
            "MINIO_SECRET_KEY": minio_descartavel["senha"],
            "MINIO_BUCKET": BUCKET,
            "MINIO_SECURE": "false",
            "GROUP_ID": str(DRI),
        }.items():
            mp.setenv(nome, valor)
        saida = io.StringIO()
        handler = configurar_log(fluxo=saida)
        try:
            # 3. sincronização a partir da branch dados-raw; o HOME temporário (git isolado da
            # configuração do usuário) vale só aqui, porque o DuckDB procura o httpfs em ~/.duckdb
            with pytest.MonkeyPatch.context() as mp_git:
                clone = _clone_com_dados_raw(tmp_path_factory.mktemp("git"), bruto, mp_git)
                codigo_sync = sincronizador.executar(clone, cliente=cliente)

            # 4. silver e gold
            silver = construir_silver(cliente, BUCKET, ler_colecao())
            config = ConfigMinio(minio_descartavel["endpoint"], BUCKET, False, DRI,
                                 minio_descartavel["usuario"], minio_descartavel["senha"])
            con = conectar(config)
            try:
                gold = construir_gold(cliente, con, BUCKET)
                origem = f"read_parquet('{caminho_s3(BUCKET, chave_gold('fato_preco_diario'))}', hive_partitioning = false)"
                cursor = con.execute(
                    f"SELECT data, product_id, group_id, acabamento, market_price, chave_raw FROM {origem} "
                    "ORDER BY data, group_id, product_id, acabamento"
                )
                nomes = [d[0] for d in cursor.description]
                fato = [dict(zip(nomes, linha)) for linha in cursor.fetchall()]
            finally:
                con.close()
        finally:
            logging.getLogger().removeHandler(handler)

    # 5. segundo retrato
    depois = _hashes(cliente, BUCKET)
    return {
        "antes": antes, "depois": depois, "bruto": bruto, "cassete": cassete,
        "codigo_coleta": codigo_coleta, "codigo_sync": codigo_sync, "log": saida.getvalue(),
        "silver": silver, "gold": gold, "fato": fato, "cliente": cliente,
        "manifesto": json.loads(MANIFESTO.read_text(encoding="utf-8")),
        "minio": minio_descartavel,
    }


def test_etapas_concluidas(pipeline):
    assert pipeline["codigo_coleta"] == coleta.SUCESSO
    assert pipeline["cassete"].all_played and pipeline["cassete"].play_count == 4
    assert pipeline["codigo_sync"] == sincronizador.SUCESSO
    assert "enviados=4 recusados=0 fora_do_escopo=0 falhas=0" in pipeline["log"]
    assert pipeline["gold"].linhas["fato_preco_diario"] == 446 + 1  # DRI real (T-13) + 1 linha do terceiro


def test_chaves_novas_ou_alteradas_so_nos_prefixos_permitidos(pipeline):
    antes, depois = pipeline["antes"], pipeline["depois"]
    mudadas = sorted(c for c in depois if antes.get(c) != depois[c])
    assert mudadas, "o pipeline não gravou nada"
    fora = [c for c in mudadas if not _permitida(c)]
    assert fora == []
    assert set(antes) <= set(depois), "algum objeto sumiu"
    prefixos = {c.split("/")[0] for c in mudadas}
    assert prefixos == {"raw", "silver", "gold"}


def test_objetos_de_terceiros_intactos(pipeline):
    antes, depois = pipeline["antes"], pipeline["depois"]
    assert len(antes) == 3 + len(TERCEIROS_AVULSOS)
    assert all(f"group_id={OUTRA}" in c for c in antes)
    assert {c: depois[c] for c in antes} == antes
    assert not any(f"group_id={OUTRA}" in c for c in depois if c not in antes)


def test_bruto_com_hash_do_manifesto(pipeline):
    bruto_dri = {c: h for c, h in pipeline["depois"].items() if c.startswith("raw/") and f"group_id={DRI}" in c}
    assert sorted(bruto_dri) == sorted(pipeline["manifesto"]) == sorted(pipeline["bruto"])
    for chave, esperado in pipeline["manifesto"].items():
        assert bruto_dri[chave] == esperado["sha256"], chave
        assert hashlib.sha256(pipeline["bruto"][chave]).hexdigest() == esperado["sha256"], chave


def test_gold_le_terceiro_sem_escrever(pipeline):
    assert pipeline["gold"].incluidas == [DRI, OUTRA]
    assert {l["group_id"] for l in pipeline["fato"]} == {DRI, OUTRA}


def test_chave_raw_de_linha_sorteada_rastreavel(pipeline):
    dri = [l for l in pipeline["fato"] if l["group_id"] == DRI]
    assert len(dri) == 446
    linha = random.Random(SEMENTE).choice(dri)

    chave = linha["chave_raw"]
    assert chave in pipeline["depois"], chave
    documento = json.loads(_ler(pipeline["cliente"], chave))
    itens = [i for i in documento["results"]
             if i["productId"] == linha["product_id"] and i["subTypeName"] == linha["acabamento"]]
    assert len(itens) == 1, linha
    if linha["market_price"] is None:
        assert itens[0]["marketPrice"] is None
    else:
        assert itens[0]["marketPrice"] == pytest.approx(linha["market_price"])
    print(f"\nlinha sorteada (semente {SEMENTE}): product_id={linha['product_id']} "
          f"acabamento={linha['acabamento']} market_price={linha['market_price']} chave_raw={chave}")


def test_toda_chave_raw_da_dri_existe_no_bruto(pipeline):
    chaves = {l["chave_raw"] for l in pipeline["fato"] if l["group_id"] == DRI}
    assert chaves == {"raw/tcgplayer/group_id=24269/data=2026-11-03/prices.json"}
    assert chaves <= set(pipeline["depois"])


def test_log_sem_credenciais(pipeline):
    assert pipeline["minio"]["usuario"] not in pipeline["log"]
    assert pipeline["minio"]["senha"] not in pipeline["log"]
