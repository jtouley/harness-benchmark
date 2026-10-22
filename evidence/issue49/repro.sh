#!/usr/bin/env bash
# Reproduce #49: the grader's run-twice check (pipetask/trial.py mart_digests) reads only mart folders,
# so a correct pipeline that publishes its marts as single files scores 0.
#
# Usage (from the repository root): bash evidence/issue49/repro.sh OUT_DIR
# Needs uv and git; no Docker, no model. About 12 minutes (four grading runs).
#
#   A  the P1 reference as committed (marts are folders)        graded by the committed grader
#   B  the same reference plus one build step that rewrites     graded by the committed grader
#      each batch mart folder as out/marts/<name>.parquet
#      (same rows; tools/single_file_marts.py below)
#   B' B again                                                   graded with mart_digests-single-file.patch
#   A' A again                                                   graded with the patch (it must not change A)
# The patched grader runs from a git worktree of this commit, so the repository's own files are not changed.
set -euo pipefail
OUT=$(realpath -m "${1:?usage: repro.sh OUT_DIR}")
HB=$(git rev-parse --show-toplevel)
PATCH=$HB/evidence/issue49/mart_digests-single-file.patch
mkdir -p "$OUT"
echo "harness-benchmark $(git -C "$HB" rev-parse HEAD)" | tee "$OUT/provenance.txt"
sha256sum "$HB/golden/pipeline/data/MANIFEST.json" "$HB/golden/pipeline/key/answer_key.json" | tee -a "$OUT/provenance.txt"

# The patched grader: a worktree of this commit with the patch applied.
FIXED=$OUT/hb-patched
[ -d "$FIXED" ] || git -C "$HB" worktree add --detach "$FIXED" HEAD >/dev/null
git -C "$FIXED" apply "$PATCH"
git -C "$FIXED" diff --stat | tee -a "$OUT/provenance.txt"

assemble() {  # $1 = output repo
  (cd "$HB/golden/pipeline" && uv run -q --frozen --project "$HB" python -m pipetask.assemble P1 --out "$1" --with-reference) >/dev/null
}
grade() {  # $1 = grader tree, $2 = repo, $3 = result name
  local work=$OUT/work-$3
  rm -rf "$work"; cp -a "$2" "$work"
  (cd "$1/golden/pipeline" && uv run -q --frozen --project "$1" python -m pipetask.trial --repo "$work" \
     --key key/answer_key.json --capture data/capture/recentchange.jsonl.gz --deadline 600 --snapshot-worktree \
     --logs "$OUT/logs-$3") >"$OUT/grade-$3.json" 2>"$OUT/grade-$3.stderr"
  python3 - "$OUT/grade-$3.json" "$3" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(f"{sys.argv[2]:28} reward={d['reward']} passed={d['passed']}/{d['total']} idempotent={d['idempotent']} "
      f"stream_ok={d['stream_ok']} builds={[b['exit'] for b in d['build']]}")
PY
}

rm -rf "$OUT/A" "$OUT/B"
assemble "$OUT/A"
assemble "$OUT/B"
mkdir -p "$OUT/B/tools"
cat >"$OUT/B/tools/single_file_marts.py" <<'PY'
"""Rewrite each mart folder under out/marts/ as one Parquet file with the same rows."""
import shutil
from pathlib import Path

import duckdb

marts = Path("out/marts")
for folder in sorted(p for p in marts.iterdir() if p.is_dir() and any(p.rglob("*.parquet"))):
    target = marts / f"{folder.name}.parquet"
    duckdb.sql(f"copy (select * from read_parquet('{folder.as_posix()}/**/*.parquet', union_by_name = true)) "
               f"to '{target.as_posix()}' (format parquet)")
    shutil.rmtree(folder)
PY
python3 - "$OUT/B/Makefile" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
old = "\t$(DBT) build $(DBT_ARGS) --exclude tag:stream\n"
assert s.count(old) == 1
open(p, "w").write(s.replace(old, old + "\t$(UV) run --frozen python tools/single_file_marts.py\n", 1))
PY
git -C "$OUT/B" add -A && git -C "$OUT/B" -c user.name=repro -c user.email=repro@localhost commit -qm "publish batch marts as single files"
git -C "$OUT/B" show --stat HEAD | tail -3

echo "--- results" | tee "$OUT/results.txt"
grade "$HB"    "$OUT/A" "A-reference-committed" | tee -a "$OUT/results.txt"
grade "$HB"    "$OUT/B" "B-single-file-committed" | tee -a "$OUT/results.txt"
grade "$FIXED" "$OUT/B" "B-single-file-patched" | tee -a "$OUT/results.txt"
grade "$FIXED" "$OUT/A" "A-reference-patched" | tee -a "$OUT/results.txt"
ls "$OUT"/work-B-single-file-committed/out/marts | tee -a "$OUT/results.txt" || true
