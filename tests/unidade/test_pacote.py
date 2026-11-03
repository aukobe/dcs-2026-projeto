"""T-01: o pacote tcg instala e importa no Python do projeto (RNF-10)."""

import importlib.metadata
import sys


def test_importa_pacote():
    import tcg

    assert tcg.__name__ == "tcg"


def test_versao_igual_metadados():
    import tcg

    assert tcg.__version__ == importlib.metadata.version("tcg")


def test_python_313():
    assert sys.version_info[:2] == (3, 13)
