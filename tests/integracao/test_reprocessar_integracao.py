"""Reprocessamento contra MinIO descartável (T-33; RF-13, RNF-03, RNF-04; ADR-004) [contêiner].

**Executado pelo autor**: o teste apaga objetos (só no MinIO descartável da
T-19, com porta aleatória e credenciais geradas na hora; o `.env` não é lido,
e nem o MinIO local de trabalho nem o RustFS da turma são tocados).

Cenário no bucket `tcg-reprocessar`:
- bruto real de 2026-11-03, gerado pelo coletor com o cassete da T-20 (sem rede)
  e gravado em `raw/` com `put_object` direto, só neste teste;
- objetos de outra coleção (99999) em `silver/`, `gold/` e `gold_turma/`;
- objetos órfãos da DRI nos três prefixos derivados, que o reprocessamento
  tem de remover.

Depois de uma chamada sem confirmação (nada muda), o reprocessamento roda duas
vezes seguidas com `CONFIRMAR=24269`. As duas execuções produzem as mesmas
chaves, as mesmas contagens e o mesmo conteúdo, sem chave de grão duplicada;
`raw/` e a outra coleção mantêm o SHA-256.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
from pathlib import Path

import pytest
import vcr

from tcg.coleta import __main__ as coleta
from tcg.config import ConfigMinio, ler_colecao
from tcg.lake.cliente import garantir_bucket
from tcg.lake.duckdb import caminho_s3, conectar
from tcg.reprocessar import reprocessar

from test_minio import minio_descartavel  # noqa: F401  (fixture da T-19)

DRI = 24269
OUTRA = 99999
BUCKET = "tcg-reprocessar"
CASSETE = Path(__file__).parent / "cassetes" / "coleta_2026-11-03.yaml"
AGORA = dt.datetime(2026, 11, 3, 20, 30, tzinfo=dt.UTC)

ORFAOS = {
    f"silver/preco_diario/group_id={DRI}/data=2020-01-01/preco.parquet": b"orfao silver",
    f"silver/tabela_renomeada/group_id={DRI}/antiga.parquet": b"orfao silver 2",
    f"gold/group_id={DRI}/tabela_antiga.parquet": b"orfao gold",
    f"gold_turma/carteira/group_id={DRI}/carteira.parquet": b"orfao gold_turma",
}
TERCEIROS = {
    f"silver/outra_tabela/group_id={OUTRA}/x.parquet": b"silver de terceiro",
    f"gold/group_id={OUTRA}/fato_preco_diario.parquet": b"gold de terceiro",
    f"gold_turma/carteira/group_id={OUTRA}/carteira.parquet": b"gold_turma de terceiro",
}
GRAO = {
    "silver/preco_diario/": "data, product_id, acabamento",
    "gold/group_id=24269/fato_preco_diario.parquet": "data, group_id, product_id, acabamento",
}


def _bruto_do_cassete(pasta: Path) -> dict[str, bytes]:
    """Bruto real de 2026-11-03 gerado pelo coletor com o cassete (vcrpy, sem rede)."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("TCG_USER_AGENT", "colecao-dri/teste")
        with vcr.VCR(record_mode="none").use_cassette(str(CASSETE), allow_playback_repeats=False):
            assert coleta.executar(pasta, agora=AGORA) == coleta.SUCESSO
    return {p.relative_to(pasta).as_posix(): p.read_bytes() for p in pasta.rglob("*") if p.is_file()}


def _hashes(cliente) -> dict[str, str]:
    resultado = {}
    for objeto in cliente.list_objects(BUCKET, recursive=True):
        resposta = cliente.get_object(BUCKET, objeto.object_name)
        try:
            resultado[objeto.object_name] = hashlib.sha256(resposta.read()).hexdigest()
        finally:
            resposta.close()
            resposta.release_conn()
    return resultado


def _config(minio) -> ConfigMinio:
    return ConfigMinio(minio["endpoint"], BUCKET, False, DRI, minio["usuario"], minio["senha"])


def _derivadas(chaves) -> list[str]:
    return sorted(c for c in chaves if c.startswith(("silver/", "gold/", "gold_turma/")) and f"group_id={DRI}/" in c)


def _conteudo(minio, chaves: list[str]) -> dict[str, list[tuple]]:
    """Linhas ordenadas de cada Parquet derivado da DRI (comparação de conteúdo, RNF-04)."""
    con = conectar(_config(minio))
    try:
        return {
            c: con.execute(
                f"SELECT * FROM read_parquet('{caminho_s3(BUCKET, c)}', hive_partitioning = false) ORDER BY ALL"
            ).fetchall()
            for c in chaves
        }
    finally:
        con.close()


def _duplicadas(minio, chaves: list[str]) -> dict[str, int]:
    """Número de chaves de grão repetidas em cada Parquet de preço."""
    con = conectar(_config(minio))
    try:
        resultado = {}
        for c in chaves:
            grao = next((g for p, g in GRAO.items() if c.startswith(p)), None)
            if grao is None:
                continue
            origem = f"read_parquet('{caminho_s3(BUCKET, c)}', hive_partitioning = false)"
            resultado[c] = con.execute(
                f"SELECT count(*) FROM (SELECT {grao} FROM {origem} GROUP BY ALL HAVING count(*) > 1)"
            ).fetchone()[0]
        return resultado
    finally:
        con.close()


def _executar(minio, confirmacao):
    return reprocessar(
        minio["cliente"], BUCKET, ler_colecao(), confirmacao, minio["endpoint"], lambda: conectar(_config(minio))
    )


@pytest.fixture(scope="module")
def duas_execucoes(minio_descartavel, tmp_path_factory):  # noqa: F811
    cliente = minio_descartavel["cliente"]
    garantir_bucket(cliente, BUCKET)
    bruto = _bruto_do_cassete(tmp_path_factory.mktemp("dados_raw"))
    for chave, dados in {**bruto, **ORFAOS, **TERCEIROS}.items():
        cliente.put_object(BUCKET, chave, io.BytesIO(dados), len(dados))
    inicial = _hashes(cliente)

    sem_confirmacao = _executar(minio_descartavel, None)
    apos_recusa = _hashes(cliente)

    r1 = _executar(minio_descartavel, "24269")
    h1 = _hashes(cliente)
    c1 = _conteudo(minio_descartavel, _derivadas(h1))
    d1 = _duplicadas(minio_descartavel, _derivadas(h1))

    r2 = _executar(minio_descartavel, "24269")
    h2 = _hashes(cliente)
    c2 = _conteudo(minio_descartavel, _derivadas(h2))
    d2 = _duplicadas(minio_descartavel, _derivadas(h2))
    return {
        "bruto": bruto, "inicial": inicial, "sem_confirmacao": sem_confirmacao, "apos_recusa": apos_recusa,
        "r": (r1, r2), "h": (h1, h2), "c": (c1, c2), "d": (d1, d2),
    }


def test_sem_confirmacao_nada_muda(duas_execucoes):
    e = duas_execucoes
    assert e["sem_confirmacao"].confirmado is False and e["sem_confirmacao"].apagadas == []
    assert e["apos_recusa"] == e["inicial"]


def test_primeira_execucao_apaga_orfaos_e_so_derivadas_da_dri(duas_execucoes):
    e = duas_execucoes
    r1, _ = e["r"]
    assert sorted(r1.apagadas) == sorted(ORFAOS)
    h1, _ = e["h"]
    assert not set(ORFAOS) & set(h1), "órfãos removidos"


def test_raw_e_terceiros_mantem_o_hash(duas_execucoes):
    e = duas_execucoes
    preservadas = {c: h for c, h in e["inicial"].items() if c not in ORFAOS}
    assert sorted(c for c in preservadas if c.startswith("raw/")) == sorted(e["bruto"])
    assert len(e["bruto"]) == 4
    for h in e["h"]:
        assert {c: h[c] for c in preservadas} == preservadas
        assert set(h) - set(preservadas) == set(_derivadas(h)), "nenhuma chave nova fora dos prefixos da DRI"


def test_duas_execucoes_mesmas_chaves_contagens_e_conteudo(duas_execucoes):
    e = duas_execucoes
    r1, r2 = e["r"]
    h1, h2 = e["h"]
    c1, c2 = e["c"]
    assert _derivadas(h1) == _derivadas(h2)
    assert r1.silver.gravadas == r2.silver.gravadas
    assert r1.gold.linhas == r2.gold.linhas
    assert sorted(r2.apagadas) == _derivadas(h1), "a segunda execução apaga exatamente o que a primeira gravou"
    assert c1 == c2
    # contagem de uma única execução, igual às do bruto real (T-13, T-28)
    assert r2.silver.gravadas["preco_diario"] == 446 and r2.silver.gravadas["produto"] == 281
    assert r2.gold.linhas["fato_preco_diario"] == 446


def test_nenhuma_chave_de_grao_duplicada(duas_execucoes):
    for d in duas_execucoes["d"]:
        assert d, "nenhum Parquet de preço encontrado"
        assert any(c.startswith("gold/") for c in d) and any(c.startswith("silver/") for c in d)
        assert all(n == 0 for n in d.values()), d
