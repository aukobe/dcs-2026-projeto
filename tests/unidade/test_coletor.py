"""Testes do coletor (T-06, T-57; RF-01, RF-02, RF-04; ADR-007).

Clientes reais do T-05 sobre um Cliente HTTP falso que registra as URLs;
gravação num diretório temporário que faz o papel do checkout da dados-raw.
"""

import datetime as dt
import hashlib
import logging

import pytest

from tcg.coleta.__main__ import FALHA_FONTE, RECUSA, SUCESSO, executar
from tcg.coleta.gravador import ArquivoExistenteError, gravar
from tcg.coleta.guarda import data_referencia
from tcg.coleta.http import FalhaRequisicaoError

DATA = "2026-11-03"
AGORA = dt.datetime(2026, 11, 3, 20, 30, tzinfo=dt.UTC)
CAMINHOS = {
    "products": f"raw/tcgplayer/group_id=24269/data={DATA}/products.json",
    "prices": f"raw/tcgplayer/group_id=24269/data={DATA}/prices.json",
    "ptax": f"raw/bcb_ptax/group_id=24269/data={DATA}/cotacao.json",
    "cdi": f"raw/bcb_cdi/group_id=24269/data={DATA}/cdi.json",
}
# \r\n, BOM, byte não UTF-8: o arquivo tem de ser idêntico ao corpo.
CORPOS = {
    "products": b"\xef\xbb\xbf{\"results\": [1]}\r\n",
    "prices": b"{\"results\": [\"\xff\"]}\r\n",
    "ptax": b"{\"value\": []}\n",
    "cdi": b"[{\"data\":\"30/10/2026\",\"valor\":\"0.050788\"}]",
}


def _fonte_da_url(url):
    if url.endswith("/24269/products"):
        return "products"
    if url.endswith("/24269/prices"):
        return "prices"
    if "CotacaoMoedaPeriodo" in url:
        return "ptax"
    if "bcdata.sgs.12" in url:
        return "cdi"
    raise AssertionError(f"URL inesperada: {url}")


class HttpFalso:
    def __init__(self, falhar=()):
        self.falhar = set(falhar)
        self.urls = []

    @property
    def requisicoes(self):
        return len(self.urls)

    def get(self, url, params=None, fonte=""):
        self.urls.append(url)
        nome = _fonte_da_url(url)
        if nome in self.falhar:
            raise FalhaRequisicaoError(f"{fonte} {url}: status 503 após 4 tentativas")
        return CORPOS[nome]


def _sha(dados):
    return hashlib.sha256(dados).hexdigest()


def _arquivos(destino):
    return sorted(str(p.relative_to(destino)) for p in destino.rglob("*") if p.is_file())


def _caminhos(data):
    return {n: c.replace(f"data={DATA}", f"data={data}") for n, c in CAMINHOS.items()}


# Data de referência pelo ciclo do TCGCSV (RF-01, RF-04, ADR-007)

@pytest.mark.parametrize(
    ("agora", "esperada"),
    [
        (dt.datetime(2026, 11, 5, 0, 59, tzinfo=dt.UTC), "2026-11-04"),  # atraso real da execução #3
        (dt.datetime(2026, 11, 4, 20, 30, tzinfo=dt.UTC), "2026-11-04"),  # cron principal
        (dt.datetime(2026, 11, 5, 6, 30, tzinfo=dt.UTC), "2026-11-04"),  # cron de reserva
        (dt.datetime(2026, 11, 5, 19, 59, 59, tzinfo=dt.UTC), "2026-11-04"),  # último segundo do ciclo
        (dt.datetime(2026, 11, 5, 20, 0, tzinfo=dt.UTC), "2026-11-05"),  # virada do ciclo
    ],
)
def test_grava_na_data_de_referencia_sem_recusa_por_horario(tmp_path, agora, esperada):
    http = HttpFalso()
    assert executar(tmp_path, agora=agora, http=http) == SUCESSO
    assert http.requisicoes == 4
    assert _arquivos(tmp_path) == sorted(_caminhos(esperada).values())


def test_data_referencia_fronteiras():
    assert data_referencia(dt.datetime(2026, 11, 4, 19, 59, 59, tzinfo=dt.UTC), 20) == dt.date(2026, 11, 3)
    assert data_referencia(dt.datetime(2026, 11, 4, 20, 0, tzinfo=dt.UTC), 20) == dt.date(2026, 11, 4)
    assert data_referencia(dt.datetime(2026, 11, 5, 0, 0, tzinfo=dt.UTC), 20) == dt.date(2026, 11, 4)
    # virada do ano: 1º/1 antes das 20h ainda é o ciclo de 31/12
    assert data_referencia(dt.datetime(2027, 1, 1, 10, 0, tzinfo=dt.UTC), 20) == dt.date(2026, 12, 31)


def test_data_referencia_converte_outro_fuso_para_utc():
    brasilia = dt.timezone(dt.timedelta(hours=-3))
    # 17h30 em Brasília = 20h30 UTC: ciclo do próprio dia
    assert data_referencia(dt.datetime(2026, 11, 4, 17, 30, tzinfo=brasilia), 20) == dt.date(2026, 11, 4)
    # 16h59 em Brasília = 19h59 UTC: ainda o ciclo do dia anterior
    assert data_referencia(dt.datetime(2026, 11, 4, 16, 59, tzinfo=brasilia), 20) == dt.date(2026, 11, 3)
    # 22h em Brasília de 4/11 = 01h UTC de 5/11: ciclo de 4/11
    assert data_referencia(dt.datetime(2026, 11, 4, 22, 0, tzinfo=brasilia), 20) == dt.date(2026, 11, 4)


def test_data_referencia_hora_de_virada_invalida():
    with pytest.raises(ValueError):
        data_referencia(AGORA, 24)


def test_janela_ptax_e_cdi_termina_na_data_de_referencia(tmp_path):
    http = HttpFalso()
    agora = dt.datetime(2026, 11, 5, 0, 59, tzinfo=dt.UTC)
    assert executar(tmp_path, agora=agora, http=http) == SUCESSO
    urls = {_fonte_da_url(u): u for u in http.urls}
    assert "@dataInicial='10-26-2026'&@dataFinalCotacao='11-04-2026'" in urls["ptax"]
    assert "dataInicial=26/10/2026&dataFinal=04/11/2026" in urls["cdi"]


def test_arquivos_da_data_de_referencia_existentes_zero_requisicoes_no_dia_seguinte(tmp_path, caplog):
    """A reserva das 06h30 depois de um principal bem-sucedido não requisita nada."""
    caminhos = _caminhos("2026-11-04")
    for nome, caminho in caminhos.items():
        (tmp_path / caminho).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / caminho).write_bytes(b"original " + nome.encode())
    antes = {n: _sha((tmp_path / c).read_bytes()) for n, c in caminhos.items()}
    http = HttpFalso()
    with caplog.at_level(logging.INFO):
        codigo = executar(tmp_path, agora=dt.datetime(2026, 11, 5, 6, 30, tzinfo=dt.UTC), http=http)
    assert codigo == SUCESSO
    assert http.urls == []
    assert {n: _sha((tmp_path / c).read_bytes()) for n, c in caminhos.items()} == antes
    assert "requisicoes=0" in caplog.text


def test_dia_seguinte_apos_a_virada_coleta_a_nova_data(tmp_path):
    """Com 2026-11-04 completo, a execução às 20h30 de 5/11 grava só 2026-11-05."""
    assert executar(tmp_path, agora=dt.datetime(2026, 11, 4, 20, 30, tzinfo=dt.UTC), http=HttpFalso()) == SUCESSO
    http = HttpFalso()
    assert executar(tmp_path, agora=dt.datetime(2026, 11, 5, 20, 30, tzinfo=dt.UTC), http=http) == SUCESSO
    assert http.requisicoes == 4
    assert _arquivos(tmp_path) == sorted(
        list(_caminhos("2026-11-04").values()) + list(_caminhos("2026-11-05").values())
    )


def test_horario_sem_fuso_e_recusado(tmp_path):
    with pytest.raises(ValueError):
        executar(tmp_path, agora=dt.datetime(2026, 11, 3, 20, 30), http=HttpFalso())


def test_destino_inexistente_e_recusado(tmp_path):
    http = HttpFalso()
    assert executar(tmp_path / "nao_existe", agora=AGORA, http=http) == RECUSA
    assert http.urls == []


# Verificação antes da requisição (RF-04)

def _pre_gravar(destino, nomes):
    for nome in nomes:
        caminho = destino / CAMINHOS[nome]
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(b"original " + nome.encode())


def test_arquivos_da_data_de_referencia_existentes_zero_requisicoes(tmp_path, caplog):
    _pre_gravar(tmp_path, CAMINHOS)
    antes = {n: _sha((tmp_path / c).read_bytes()) for n, c in CAMINHOS.items()}
    http = HttpFalso()
    with caplog.at_level(logging.INFO):
        codigo = executar(tmp_path, agora=AGORA, http=http)
    assert codigo == SUCESSO
    assert http.urls == []
    assert {n: _sha((tmp_path / c).read_bytes()) for n, c in CAMINHOS.items()} == antes
    assert caplog.text.count("fonte pulada sem requisição") == 4


def test_so_prices_existente_requisita_os_outros_tres(tmp_path):
    _pre_gravar(tmp_path, ["prices"])
    http = HttpFalso()
    assert executar(tmp_path, agora=AGORA, http=http) == SUCESSO
    assert sorted(_fonte_da_url(u) for u in http.urls) == ["cdi", "products", "ptax"]
    assert (tmp_path / CAMINHOS["prices"]).read_bytes() == b"original prices"


# Gravação (RF-02)

def test_recusa_sobrescrita_com_hash_original_intacto(tmp_path, caplog):
    caminho = tmp_path / CAMINHOS["prices"]
    gravar(caminho, b"corpo original")
    hash_original = _sha(caminho.read_bytes())
    with caplog.at_level(logging.INFO), pytest.raises(ArquivoExistenteError):
        gravar(caminho, b"corpo novo")
    assert _sha(caminho.read_bytes()) == hash_original
    assert "gravação recusada" in caplog.text


def test_hash_do_arquivo_igual_ao_do_corpo_nos_quatro_caminhos(tmp_path):
    assert executar(tmp_path, agora=AGORA, http=HttpFalso()) == SUCESSO
    assert _arquivos(tmp_path) == sorted(CAMINHOS.values())
    for nome, caminho in CAMINHOS.items():
        assert _sha((tmp_path / caminho).read_bytes()) == _sha(CORPOS[nome])


def test_gravar_devolve_sha256_do_corpo(tmp_path):
    assert gravar(tmp_path / "a" / "b.json", CORPOS["products"]) == _sha(CORPOS["products"])


# Fontes independentes (RF-01)

def test_falha_de_uma_fonte_nao_afeta_as_outras(tmp_path, caplog):
    http = HttpFalso(falhar={"ptax"})
    with caplog.at_level(logging.INFO):
        codigo = executar(tmp_path, agora=AGORA, http=http)
    assert codigo == FALHA_FONTE
    assert http.requisicoes == 4
    assert not (tmp_path / CAMINHOS["ptax"]).exists()
    assert not (tmp_path / CAMINHOS["ptax"]).parent.exists() or not any(
        (tmp_path / CAMINHOS["ptax"]).parent.iterdir()
    )
    for nome in ("products", "prices", "cdi"):
        assert (tmp_path / CAMINHOS[nome]).read_bytes() == CORPOS[nome]
    assert "fonte falhou, nada gravado: bcb_ptax/cotacao.json" in caplog.text
    assert "requisicoes=4" in caplog.text


def test_reexecucao_apos_falha_parcial_busca_so_o_que_faltou(tmp_path):
    assert executar(tmp_path, agora=AGORA, http=HttpFalso(falhar={"products"})) == FALHA_FONTE
    http = HttpFalso()
    assert executar(tmp_path, agora=AGORA, http=http) == SUCESSO
    assert [_fonte_da_url(u) for u in http.urls] == ["products"]
