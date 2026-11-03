PYTHON ?= .venv/bin/python
# python3.13 do PATH; se não houver, o caminho fixo do Codespace
PYTHON313 ?= $(shell command -v python3.13 2>/dev/null || echo /usr/local/python/3.13.8/bin/python3.13)

.PHONY: setup test

setup:
	@test -x "$(PYTHON313)" || { echo "python3.13 não encontrado no PATH nem em /usr/local/python/3.13.8/bin" >&2; exit 1; }
	$(PYTHON313) -m venv .venv
	$(PYTHON) -m pip install -q -e ".[dev]"

test:
	$(PYTHON) -m pytest -v
