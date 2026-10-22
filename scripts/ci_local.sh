#!/usr/bin/env bash
# What .github/workflows/verify.yml runs, on this machine. GitHub-hosted CI is off (billing blocks every
# hosted runner), so run this before each push and paste its last lines into the pull request.
# The framework fetch, install-check and verify steps need network access and every pinned framework;
# run them by hand with `python -m cbench fetch && python -m cbench verify` when you have access.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== unit and pipeline tests (HB_TEST_BUDGET=1)"
HB_TEST_BUDGET=1 uv run --frozen --with tokenizers python -m pytest -q

echo "== regenerate the report"
uv run --frozen --with tokenizers python -m cbench report
git diff --exit-code results/
echo "ci_local: OK at $(git rev-parse --short HEAD)"
