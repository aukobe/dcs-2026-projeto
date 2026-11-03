"""Testes do Leitor de configuração (T-03; RF-01, RF-03, RF-06, RF-24, RNF-08)."""

import datetime as dt

import pytest

from tcg.config import (
    ConfiguracaoError,
    ler_colecao,
    ler_config_minio,
    ler_parametros,
    ler_user_agent,
)

CHAVE_FICTICIA = "chave-ficticia-AKIA123"
SEGREDO_FICTICIO = "segredo-ficticio-xyz789"


@pytest.fixture
def ambiente_minio(monkeypatch):
    valores = {
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": CHAVE_FICTICIA,
        "MINIO_SECRET_KEY": SEGREDO_FICTICIO,
        "MINIO_BUCKET": "tcg",
        "MINIO_SECURE": "false",
        "GROUP_ID": "24269",
    }
    for nome, valor in valores.items():
        monkeypatch.setenv(nome, valor)
    return valores


def test_colecao_com_valores_da_spec():
    colecao = ler_colecao()
    assert colecao.nome == "SV10: Destined Rivals"
    assert colecao.sigla == "DRI"
    assert colecao.data_lancamento == dt.date(2025, 5, 30)
    assert colecao.responsavel == "Augusto"
    assert colecao.group_id == 24269


def test_parametros_com_valores_do_plano():
    p = ler_parametros()
    assert p.janela_dias == 10
    assert p.tentativas == 3
    assert p.esperas_s == (2, 4, 8)
    assert p.pausa_minima_ms == 100
    assert p.hora_minima_utc == 20
    assert p.limite_requisicoes_dia == 10000
    assert p.taxa_venda == 0.15
    assert p.preco_minimo_p1_usd == 1
    assert p.preco_minimo_p5_usd == 5


def test_toml_com_chave_ausente_gera_erro_claro(tmp_path):
    arquivo = tmp_path / "colecao.toml"
    arquivo.write_text('nome = "X"\nsigla = "X"\ndata_lancamento = 2025-05-30\nresponsavel = "X"\n')
    with pytest.raises(ConfiguracaoError, match="chave ausente.*group_id"):
        ler_colecao(arquivo)


def test_toml_ausente_gera_erro_claro(tmp_path):
    with pytest.raises(ConfiguracaoError, match="arquivo de configuração ausente"):
        ler_parametros(tmp_path / "nao_existe.toml")


def test_user_agent_lido_do_ambiente(monkeypatch):
    monkeypatch.setenv("TCG_USER_AGENT", "colecao-dri/1.0")
    assert ler_user_agent() == "colecao-dri/1.0"


@pytest.mark.parametrize("valor", [None, "", "   "])
def test_user_agent_ausente_ou_vazio_gera_erro_claro(monkeypatch, valor):
    if valor is None:
        monkeypatch.delenv("TCG_USER_AGENT", raising=False)
    else:
        monkeypatch.setenv("TCG_USER_AGENT", valor)
    with pytest.raises(ConfiguracaoError, match="TCG_USER_AGENT ausente ou vazia"):
        ler_user_agent()


def test_config_minio_lida_do_ambiente(ambiente_minio):
    cfg = ler_config_minio()
    assert cfg.endpoint == "localhost:9000"
    assert cfg.bucket == "tcg"
    assert cfg.secure is False
    assert cfg.group_id == 24269
    assert cfg.access_key == CHAVE_FICTICIA
    assert cfg.secret_key == SEGREDO_FICTICIO


@pytest.mark.parametrize("nome", ["MINIO_ACCESS_KEY", "MINIO_SECRET_KEY", "MINIO_ENDPOINT"])
def test_variavel_minio_ausente_gera_erro_com_o_nome(ambiente_minio, monkeypatch, nome):
    monkeypatch.delenv(nome)
    with pytest.raises(ConfiguracaoError, match=f"{nome} ausente ou vazia"):
        ler_config_minio()


def test_erro_nao_expoe_valor_de_credencial(ambiente_minio, monkeypatch):
    monkeypatch.setenv("GROUP_ID", "99999")
    with pytest.raises(ConfiguracaoError) as erro:
        ler_config_minio()
    assert "diverge" in str(erro.value)
    assert CHAVE_FICTICIA not in str(erro.value)
    assert SEGREDO_FICTICIO not in str(erro.value)


def test_repr_nao_mostra_credenciais(ambiente_minio):
    texto = repr(ler_config_minio())
    assert CHAVE_FICTICIA not in texto
    assert SEGREDO_FICTICIO not in texto
    assert "localhost:9000" in texto
