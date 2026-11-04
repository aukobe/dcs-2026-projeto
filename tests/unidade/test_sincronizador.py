"""Testes do Cliente MinIO e do Sincronizador (T-18; RF-05, RNF-03, RNF-08).

Usam um cliente falso em memória no lugar do SDK e um leitor falso no lugar
do git: nenhum teste acessa a rede nem o MinIO local.
"""

import hashlib
import logging

import pytest
from minio.error import S3Error

from tcg.lake import cliente as lake_cliente
from tcg.lake.cliente import criar_cliente, existe, garantir_bucket
from tcg.sync import sincronizador
from tcg.sync.leitor_branch import ArquivoBranch
from tcg.sync.sincronizador import chave_permitida, sha1_blob, sincronizar

BUCKET = "tcg"
GROUP_ID = 24269
PRODUCTS = "raw/tcgplayer/group_id=24269/data=2026-11-03/products.json"
PRICES = "raw/tcgplayer/group_id=24269/data=2026-11-03/prices.json"
CDI = "raw/bcb_cdi/group_id=24269/data=2026-11-03/cdi.json"


def _erro_s3(codigo: str) -> S3Error:
    return S3Error(None, codigo, "falso", "/recurso", "req", "host")


class _Resposta:
    def __init__(self, corpo: bytes):
        self._corpo = corpo

    def read(self) -> bytes:
        return self._corpo

    def close(self) -> None:
        pass

    def release_conn(self) -> None:
        pass


class ClienteFalso:
    """Imita o subconjunto do SDK `minio` usado pelo sincronizador; registra as chamadas."""

    def __init__(self, objetos=None, buckets=(BUCKET,), corromper=False):
        self.objetos: dict[str, bytes] = dict(objetos or {})
        self.buckets = set(buckets)
        self.chamadas: list[tuple[str, str]] = []
        self.corromper = corromper

    def bucket_exists(self, bucket_name):
        self.chamadas.append(("bucket_exists", bucket_name))
        return bucket_name in self.buckets

    def make_bucket(self, bucket_name):
        self.chamadas.append(("make_bucket", bucket_name))
        if bucket_name in self.buckets:
            raise _erro_s3("BucketAlreadyOwnedByYou")
        self.buckets.add(bucket_name)

    def stat_object(self, bucket_name, object_name):
        self.chamadas.append(("stat_object", object_name))
        if object_name not in self.objetos:
            raise _erro_s3("NoSuchKey")
        return object()

    def put_object(self, bucket_name, object_name, data, length, content_type="application/octet-stream"):
        self.chamadas.append(("put_object", object_name))
        corpo = data.read()
        assert len(corpo) == length
        self.objetos[object_name] = corpo + (b"x" if self.corromper else b"")

    def get_object(self, bucket_name, object_name):
        self.chamadas.append(("get_object", object_name))
        return _Resposta(self.objetos[object_name])

    def chaves_chamadas(self, metodo: str) -> list[str]:
        return [chave for nome, chave in self.chamadas if nome == metodo]


def _arquivos(conteudos: dict[str, bytes]):
    blobs = {sha1_blob(corpo): corpo for corpo in conteudos.values()}
    arquivos = [ArquivoBranch(chave=c, blob=sha1_blob(corpo)) for c, corpo in conteudos.items()]
    return arquivos, blobs.__getitem__


def _sha256(corpo: bytes) -> str:
    return hashlib.sha256(corpo).hexdigest()


def test_chave_existente_nao_e_regravada_e_recusa_no_log(caplog):
    original = b'{"results": ["versao do MinIO"]}'
    da_branch = b'{"results": ["versao da branch"]}\r\n'
    cliente = ClienteFalso(objetos={PRICES: original})
    arquivos, ler = _arquivos({PRICES: da_branch})

    with caplog.at_level(logging.INFO):
        resumo = sincronizar(cliente, BUCKET, GROUP_ID, arquivos, ler)

    assert cliente.chaves_chamadas("put_object") == []
    assert _sha256(cliente.objetos[PRICES]) == _sha256(original)
    assert resumo.recusados == [PRICES] and resumo.enviados == []
    assert resumo.codigo_saida == sincronizador.SUCESSO
    assert f"recusa de sobrescrita: chave já existe no MinIO, não regravada: {PRICES}" in caplog.text


def test_arquivo_novo_enviado_com_hash_da_origem(caplog):
    conteudos = {
        PRODUCTS: b'{"results": [\r\n  {"productId": 1}\r\n]}\r\n',
        CDI: b'[{"data": "03/11/2026", "valor": "0.055131"}]\xff\xfe',
    }
    cliente = ClienteFalso()
    arquivos, ler = _arquivos(conteudos)

    with caplog.at_level(logging.INFO):
        resumo = sincronizar(cliente, BUCKET, GROUP_ID, arquivos, ler)

    assert resumo.enviados == [PRODUCTS, CDI]
    for chave, corpo in conteudos.items():
        assert _sha256(cliente.objetos[chave]) == _sha256(corpo)
        assert f"sha256={_sha256(corpo)}" in caplog.text
    # stat_object vem antes do put_object em cada chave
    nomes = [nome for nome, chave in cliente.chamadas if chave == PRODUCTS]
    assert nomes.index("stat_object") < nomes.index("put_object")


def test_mistura_de_existente_e_novo():
    cliente = ClienteFalso(objetos={PRODUCTS: b"ja estava"})
    arquivos, ler = _arquivos({PRODUCTS: b"novo products", PRICES: b"novo prices"})

    resumo = sincronizar(cliente, BUCKET, GROUP_ID, arquivos, ler)

    assert resumo.recusados == [PRODUCTS]
    assert resumo.enviados == [PRICES]
    assert cliente.objetos[PRODUCTS] == b"ja estava"


@pytest.mark.parametrize(
    "chave",
    [
        "raw/tcgplayer/group_id=99999/data=2026-11-03/prices.json",
        "silver/preco_diario/group_id=24269/data=2026-11-03/x.parquet",
        "gold/group_id=24269/fato.parquet",
        "raw/tcgplayer/group_id=24269/../group_id=99999/prices.json",
        "raw/../silver/group_id=24269/x.json",
        "/raw/tcgplayer/group_id=24269/data=2026-11-03/prices.json",
        "raw/tcgplayer//group_id=24269/prices.json",
        "raw/tcgplayer/group_id=242690/data=2026-11-03/prices.json",
        "raw/tcgplayer/group_id=24269",
    ],
)
def test_chave_fora_do_escopo_nunca_chega_ao_sdk(chave, caplog):
    cliente = ClienteFalso()
    arquivos, ler = _arquivos({chave: b"qualquer"})

    resumo = sincronizar(cliente, BUCKET, GROUP_ID, arquivos, ler)

    assert cliente.chamadas == []
    assert cliente.objetos == {}
    assert resumo.fora_do_escopo == [chave]
    assert resumo.codigo_saida == sincronizador.FALHA
    assert f"chave fora do escopo recusada, nada gravado: {chave}" in caplog.text


def test_nenhuma_chave_gravada_fora_de_raw_do_group_id():
    validas = {PRODUCTS: b"a", PRICES: b"b", CDI: b"c"}
    invalidas = {
        "raw/tcgplayer/group_id=1/data=2026-11-03/prices.json": b"d",
        "silver/x/group_id=24269/y.parquet": b"e",
    }
    cliente = ClienteFalso()
    arquivos, ler = _arquivos({**validas, **invalidas})

    sincronizar(cliente, BUCKET, GROUP_ID, arquivos, ler)

    gravadas = cliente.chaves_chamadas("put_object")
    assert sorted(gravadas) == sorted(validas)
    assert all(c.startswith("raw/") and "/group_id=24269/" in c for c in gravadas)


def test_chave_permitida_aceita_as_tres_fontes():
    for chave in (PRODUCTS, PRICES, CDI, "raw/bcb_ptax/group_id=24269/data=2026-11-03/cotacao.json"):
        assert chave_permitida(chave, GROUP_ID)


def test_blob_corrompido_nao_e_enviado(caplog):
    cliente = ClienteFalso()
    arquivos = [ArquivoBranch(chave=PRICES, blob=sha1_blob(b"original"))]

    resumo = sincronizar(cliente, BUCKET, GROUP_ID, arquivos, lambda blob: b"alterado")

    assert cliente.chaves_chamadas("put_object") == []
    assert resumo.falhas == [PRICES]
    assert resumo.codigo_saida == sincronizador.FALHA
    assert "blob corrompido" in caplog.text


def test_hash_divergente_apos_envio_e_falha(caplog):
    cliente = ClienteFalso(corromper=True)
    arquivos, ler = _arquivos({PRICES: b"corpo"})

    resumo = sincronizar(cliente, BUCKET, GROUP_ID, arquivos, ler)

    assert resumo.falhas == [PRICES] and resumo.enviados == []
    assert "hash divergente após envio" in caplog.text


def test_sha1_blob_igual_ao_git():
    # `printf 'hello\n' | git hash-object --stdin`
    assert sha1_blob(b"hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"


def test_existe_propaga_erro_que_nao_e_ausencia():
    class ClienteNegado(ClienteFalso):
        def stat_object(self, bucket_name, object_name):
            raise _erro_s3("AccessDenied")

    with pytest.raises(S3Error):
        existe(ClienteNegado(), BUCKET, PRICES)


def test_bucket_ausente_e_criado(caplog):
    cliente = ClienteFalso(buckets=())

    with caplog.at_level(logging.INFO):
        criado = garantir_bucket(cliente, BUCKET)

    assert criado is True
    assert BUCKET in cliente.buckets
    assert cliente.chaves_chamadas("make_bucket") == [BUCKET]
    assert f"bucket criado: {BUCKET}" in caplog.text


def test_bucket_existente_nao_e_recriado(caplog):
    cliente = ClienteFalso(buckets=(BUCKET,))

    with caplog.at_level(logging.INFO):
        criado = garantir_bucket(cliente, BUCKET)

    assert criado is False
    assert cliente.chaves_chamadas("make_bucket") == []
    assert f"bucket já existe, não recriado: {BUCKET}" in caplog.text


def test_bucket_criado_em_paralelo_e_idempotente():
    class ClienteCorrida(ClienteFalso):
        def bucket_exists(self, bucket_name):
            return False

    assert garantir_bucket(ClienteCorrida(buckets=(BUCKET,)), BUCKET) is False


@pytest.fixture
def ambiente_minio(monkeypatch):
    valores = {
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": "chave-ficticia-AKIA123",
        "MINIO_SECRET_KEY": "segredo-ficticio-xyz789",
        "MINIO_BUCKET": BUCKET,
        "MINIO_SECURE": "false",
        "GROUP_ID": str(GROUP_ID),
    }
    for nome, valor in valores.items():
        monkeypatch.setenv(nome, valor)
    return valores


def test_criar_cliente_le_credenciais_do_ambiente_sem_registrar(ambiente_minio, monkeypatch, caplog):
    recebidos = {}

    class MinioFalso:
        def __init__(self, endpoint, access_key, secret_key, secure):
            recebidos.update(endpoint=endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    monkeypatch.setattr(lake_cliente, "Minio", MinioFalso)
    with caplog.at_level(logging.DEBUG):
        criar_cliente()

    assert recebidos == {
        "endpoint": "localhost:9000",
        "access_key": ambiente_minio["MINIO_ACCESS_KEY"],
        "secret_key": ambiente_minio["MINIO_SECRET_KEY"],
        "secure": False,
    }
    assert ambiente_minio["MINIO_ACCESS_KEY"] not in caplog.text
    assert ambiente_minio["MINIO_SECRET_KEY"] not in caplog.text


def test_executar_cria_bucket_e_sincroniza_sem_vazar_credencial(ambiente_minio, monkeypatch, capsys):
    from tcg.log import configurar_log

    conteudos = {PRODUCTS: b"products", PRICES: b"prices"}
    arquivos, ler = _arquivos(conteudos)
    monkeypatch.setattr(sincronizador.leitor_branch, "buscar", lambda repo: None)
    monkeypatch.setattr(sincronizador.leitor_branch, "listar", lambda repo: arquivos)
    monkeypatch.setattr(sincronizador.leitor_branch, "ler", lambda repo, blob: ler(blob))
    cliente = ClienteFalso(buckets=())

    configurar_log()
    codigo = sincronizador.executar(cliente=cliente)
    segunda = sincronizador.executar(cliente=cliente)
    saida = capsys.readouterr().out

    assert codigo == segunda == sincronizador.SUCESSO
    assert cliente.chaves_chamadas("make_bucket") == [BUCKET]
    assert sorted(cliente.chaves_chamadas("put_object")) == sorted(conteudos)
    assert "recusados=2" in saida
    assert ambiente_minio["MINIO_ACCESS_KEY"] not in saida
    assert ambiente_minio["MINIO_SECRET_KEY"] not in saida


def test_executar_sem_configuracao_recusa(monkeypatch):
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.setenv("GROUP_ID", str(GROUP_ID))
    cliente = ClienteFalso()

    assert sincronizador.executar(cliente=cliente) == sincronizador.ERRO_CONFIG
    assert cliente.chamadas == []
