#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3.13}

cd "$PROJECT_DIR"
if [ ! -x .venv/bin/python ]; then
  "$PYTHON_BIN" -m venv .venv
fi
.venv/bin/python -m pip install -e '.[ml,test]'

# exFAT stores macOS extended attributes as binary ._* sidecars. Some Python
# packages recursively scan source/metadata and mistake them for real files.
find .venv/lib -type f -name '._*' -delete

.venv/bin/python -m intro_footage_matcher.model_setup
.venv/bin/python -m pytest -q
