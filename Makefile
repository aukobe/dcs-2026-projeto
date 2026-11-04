PYTHON ?= .venv/bin/python
# python3.13 do PATH; se não houver, o caminho fixo do Codespace
PYTHON313 ?= $(shell command -v python3.13 2>/dev/null || echo /usr/local/python/3.13.8/bin/python3.13)

.PHONY: setup test up sync

setup:
	@test -x "$(PYTHON313)" || { echo "python3.13 não encontrado no PATH nem em /usr/local/python/3.13.8/bin" >&2; exit 1; }
	$(PYTHON313) -m venv .venv
	$(PYTHON) -m pip install -q -e ".[dev]"
	# Extensão httpfs do DuckDB, baixada só aqui (R-08); o código nunca a baixa
	$(PYTHON) -c "import duckdb; duckdb.connect().install_extension('httpfs')"

test:
	$(PYTHON) -m pytest -v

# Sobe o MinIO local e só termina quando o healthcheck estiver healthy (ADR-002)
up:
	docker compose up -d --wait

# Branch dados-raw → bucket tcg do MinIO local, sem sobrescrita (RF-05, ADR-001).
# O .env é carregado só no ambiente da receita; nenhum valor é impresso (RNF-08).
sync:
	@test -f .env || { echo ".env ausente: copie .env.example para .env e preencha" >&2; exit 2; }
	@set -a && . ./.env && set +a && $(PYTHON) -m tcg.sync.sincronizador
