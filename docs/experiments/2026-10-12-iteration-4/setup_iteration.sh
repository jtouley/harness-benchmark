#!/usr/bin/env bash
# Usage: setup_iteration.sh N  -> iteration-N/eval-<name>/{with_skill,old_skill}/{origin.git,repo,outputs}
set -euo pipefail
W="$(cd "$(dirname "$0")" && pwd)"
N="$1"
for name in multicurrency budgets audit-undo; do
  for cfg in with_skill old_skill; do
    d="$W/iteration-$N/eval-$name/$cfg"
    [ -e "$d/repo" ] && { echo "exists: $d" >&2; exit 1; }
    mkdir -p "$d/outputs"
    tmp="$(mktemp -d)"
    cp -R "$W/fixture/." "$tmp/"
    rm -rf "$tmp/.venv"
    printf '.context/\n__pycache__/\n.venv/\n.pytest_cache/\n' > "$tmp/.gitignore"
    git -C "$tmp" init -q -b main
    git -C "$tmp" -c user.email=eval@local -c user.name=eval add -A
    git -C "$tmp" -c user.email=eval@local -c user.name=eval commit -qm "ledgerlite baseline"
    git clone -q --bare "$tmp" "$d/origin.git"
    git clone -q "$d/origin.git" "$d/repo"
    rm -rf "$tmp"
  done
  python3 - "$W" "$N" "$name" <<'PY'
import json, sys
from pathlib import Path
w, n, name = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
ev = next(e for e in json.loads((w / "evals.json").read_text())["evals"] if e["name"] == name)
(w / f"iteration-{n}" / f"eval-{name}" / "eval_metadata.json").write_text(
    json.dumps({"eval_id": ev["id"], "eval_name": name, "prompt": ev["prompt"], "assertions": []}, indent=2))
PY
done
echo "iteration-$N ready"
