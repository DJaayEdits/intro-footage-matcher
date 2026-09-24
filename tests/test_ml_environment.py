import importlib

import pytest


def test_local_ml_dependencies_import_cleanly():
    pytest.importorskip("faster_whisper")
    pytest.importorskip("torch")
    for module in ("numpy", "PIL", "transformers", "sentence_transformers"):
        assert importlib.import_module(module) is not None
