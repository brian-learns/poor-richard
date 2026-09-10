#!/usr/bin/env sh
# Run the test suite on every supported Python version (see requires-python).
#
# 3.14 uses the project's normal .venv; other versions get their own
# .venv-<ver> via UV_PROJECT_ENVIRONMENT so the dev env is never clobbered
# (a plain `uv run --python 3.11` would recreate .venv with 3.11).
#
# Notes:
# - uv downloads missing interpreters automatically.
# - --all-extras installs the 'full' extra (financedatabase, pypostal-multiarch);
#   drop it for a base-only run (those tests then skip).
# - test_financedatabase skips in envs without the fetched data; enable it
#   per env with: UV_PROJECT_ENVIRONMENT=.venv-3.11 uv run python \
#       scripts/fetch_financedatabase.py

set -eu

for v in 3.11 3.12 3.13; do
    echo "=== Python $v (.venv-$v) ==="
    UV_PROJECT_ENVIRONMENT=".venv-$v" uv sync --python "$v" --all-extras
    UV_PROJECT_ENVIRONMENT=".venv-$v" uv run --no-sync pytest -q
done

echo "=== Python 3.14 (.venv, dev env) ==="
uv sync --all-extras
uv run --no-sync pytest -q

echo "=== all versions passed ==="
