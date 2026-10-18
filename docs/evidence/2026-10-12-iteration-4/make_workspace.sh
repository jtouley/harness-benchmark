#!/usr/bin/env bash
# Build a runnable eval workspace from committed files.
# Usage: make_workspace.sh <dir>   (then: cd <dir> && bash setup_iteration.sh 4)
#   <dir>/fixture/  = golden/tasks/T04-ledgerlite-multicurrency/repo (T04-T06 share this repo)
#   <dir>/hidden/   = the hidden tests of T04-T06 and their shared _cli.py
#   <dir>/grade.py, setup_iteration.sh, evals.json, build_blind.py (from this folder)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
OUT="${1:?usage: make_workspace.sh <dir>}"
mkdir -p "$OUT/hidden"
cp -R "$ROOT/golden/tasks/T04-ledgerlite-multicurrency/repo" "$OUT/fixture"
for t in T04-ledgerlite-multicurrency T05-ledgerlite-budgets T06-ledgerlite-audit-undo; do
  cp "$ROOT/golden/tasks/$t/hidden/"test_hidden_*.py "$OUT/hidden/"
done
cp "$ROOT/golden/tasks/T04-ledgerlite-multicurrency/hidden/_cli.py" "$OUT/hidden/_cli.py"
cp "$HERE/grade.py" "$HERE/setup_iteration.sh" "$HERE/evals.json" "$HERE/build_blind.py" "$OUT/"
echo "workspace ready: $OUT"
