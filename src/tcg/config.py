"""Leitor de configuração (specs/plan.md, seção 8).

- `config/colecao.toml` e `config/parametros.toml`, lidos com `tomllib`.
- Variáveis de ambiente (nomes do `.env.example`); credenciais só do ambiente
  (RNF-08). Mensagens de erro citam o nome da variável, nunca o valor.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
import datetime as dt
import os
from pathlib import Path
import tomllib

PASTA_CONFIG = Path(__file__).resolve().parents[2] / "config"


class ConfiguracaoError(RuntimeError):
    """Configuração ausente ou inválida."""


@dataclass(frozen=True)
class Colecao:
    nome: str
    sigla: str
    data_lancamento: dt.date
    responsavel: str
    group_id: int


@dataclass(frozen=True)
class Parametros:
    janela_dias: int
    tentativas: int
    esperas_s: tuple[float, ...]
    pausa_minima_ms: int
    hora_virada_ciclo_utc: int
    limite_requisicoes_dia: int
    taxa_venda: float
    preco_minimo_p1_usd: float
    preco_minimo_p5_usd: float


@dataclass(frozen=True)
class ConfigMinio:
    endpoint: str
    bucket: str
    secure: bool
    group_id: int
    access_key: str = field(repr=False)
    secret_key: str = field(repr=False)


def _ler_toml(caminho: Path, classe: type) -> dict:
    try:
        with caminho.open("rb") as arquivo:
            dados = tomllib.load(arquivo)
    except FileNotFoundError:
        raise ConfiguracaoError(f"arquivo de configuração ausente: {caminho}") from None
    except tomllib.TOMLDecodeError as erro:
        raise ConfiguracaoError(f"TOML inválido em {caminho}: {erro}") from None
    esperadas = {f.name for f in fields(classe)}
    faltando = sorted(esperadas - dados.keys())
    sobrando = sorted(dados.keys() - esperadas)
    if faltando:
        raise ConfiguracaoError(f"chave ausente em {caminho.name}: {', '.join(faltando)}")
    if sobrando:
        raise ConfiguracaoError(f"chave desconhecida em {caminho.name}: {', '.join(sobrando)}")
    return dados


def ler_colecao(caminho: Path | None = None) -> Colecao:
    caminho = caminho or PASTA_CONFIG / "colecao.toml"
    dados = _ler_toml(caminho, Colecao)
    if not isinstance(dados["data_lancamento"], dt.date):
        raise ConfiguracaoError("data_lancamento deve ser uma data TOML (AAAA-MM-DD)")
    if not isinstance(dados["group_id"], int):
        raise ConfiguracaoError("group_id deve ser inteiro")
    return Colecao(**dados)


def ler_parametros(caminho: Path | None = None) -> Parametros:
    caminho = caminho or PASTA_CONFIG / "parametros.toml"
    dados = _ler_toml(caminho, Parametros)
    dados["esperas_s"] = tuple(dados["esperas_s"])
    if len(dados["esperas_s"]) != dados["tentativas"]:
        raise ConfiguracaoError("esperas_s deve ter um valor de espera por repetição")
    return Parametros(**dados)


def _variavel(nome: str) -> str:
    valor = os.environ.get(nome, "").strip()
    if not valor:
        raise ConfiguracaoError(
            f"variável de ambiente {nome} ausente ou vazia; defina-a no .env (modelo em .env.example)"
        )
    return valor


def ler_user_agent() -> str:
    """User-Agent próprio para o TCGCSV (RF-03)."""
    return _variavel("TCG_USER_AGENT")


def ler_config_minio(colecao: Colecao | None = None) -> ConfigMinio:
    """Configuração do MinIO local; credenciais só do ambiente (RNF-08)."""
    colecao = colecao or ler_colecao()
    texto_group_id = _variavel("GROUP_ID")
    try:
        group_id = int(texto_group_id)
    except ValueError:
        raise ConfiguracaoError("variável de ambiente GROUP_ID deve ser inteira") from None
    if group_id != colecao.group_id:
        raise ConfiguracaoError(
            f"GROUP_ID={group_id} diverge do group_id {colecao.group_id} de config/colecao.toml"
        )
    secure = _variavel("MINIO_SECURE").lower()
    if secure not in {"true", "false"}:
        raise ConfiguracaoError("variável de ambiente MINIO_SECURE deve ser true ou false")
    return ConfigMinio(
        endpoint=_variavel("MINIO_ENDPOINT"),
        bucket=_variavel("MINIO_BUCKET"),
        secure=secure == "true",
        group_id=group_id,
        access_key=_variavel("MINIO_ACCESS_KEY"),
        secret_key=_variavel("MINIO_SECRET_KEY"),
    )
