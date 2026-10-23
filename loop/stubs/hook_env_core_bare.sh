#!/usr/bin/env bash
# Stub run (loop.driver --kind stub): a cadence contract test run under the GIT_DIR and GIT_INDEX_FILE that a
# git hook gets in a worktree (absolute paths), as the pre-commit `contract tests` hook runs it. Records
# core.bare of the repository that owns the worktree before and after. Writes transcript.jsonl and stop.json.
#   hook_env_core_bare.sh PLUGIN OUT VENV
set -uo pipefail
plugin=$1 out=$2 venv=$3
mkdir -p "$out"
clean() { env -u GIT_DIR -u GIT_INDEX_FILE -u GIT_WORK_TREE "$@"; }
clean git init -q -b main main-repo
clean git -C main-repo -c user.name=stub -c user.email=stub@example.com commit -q --allow-empty -m base
clean git -C main-repo worktree add -q ../wt -b wt
gitdir=$(clean git -C wt rev-parse --absolute-git-dir)
before=$(clean git -C main-repo config --get core.bare)
test=tests/contract/test_ste_writing_contract.py
(cd wt && GIT_DIR="$gitdir" GIT_INDEX_FILE="$gitdir/index" UV_PROJECT_ENVIRONMENT="$venv" \
  uv run -q --frozen --project "$plugin" --extra dev python -m pytest -q -p no:cacheprovider "$plugin/$test") \
  >"$out/pytest.txt" 2>&1
pytest_rc=$?
after=$(clean git -C main-repo config --get core.bare)
python3 - "$out" "$before" "$after" "$pytest_rc" "$test" <<'PY'
import json, sys
out, before, after, rc, test = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
tail = open(f"{out}/pytest.txt").read().strip().splitlines()[-1:] or [""]
row = {"type": "stub", "step": "contract test under a worktree hook's GIT_DIR", "test": test,
       "core_bare_before": before, "core_bare_after": after, "pytest_exit": rc, "pytest_tail": tail[0]}
open(f"{out}/transcript.jsonl", "w").write(json.dumps(row) + "\n")
flipped = before != after
json.dump({"block": None, "reason": f"core.bare {before} -> {after}" if flipped else None},
          open(f"{out}/stop.json", "w"))
sys.exit(1 if flipped else 0)
PY
