#!/usr/bin/env bash
# Regrade a run's delivered working tree with the committed grader and with the #49 patch.
# Usage (from the repository root): bash evidence/scripts/regrade.sh RUN OUT_DIR
#   RUN is a folder under evidence/runs/ (its worktree-from-skeleton.patch is applied to a fresh
#   starting repository of the run's task). The patched grader runs from a git worktree of this commit
#   with evidence/issue49/mart_digests-single-file.patch applied; the repository's files are not changed.
set -euo pipefail
RUN=${1:?usage: regrade.sh RUN OUT_DIR}; OUT=$(realpath -m "${2:?usage: regrade.sh RUN OUT_DIR}")
HB=$(git rev-parse --show-toplevel)
TASK=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['task'])" \
  "$HB/docs/evidence/2026-10-21-pipeline-cadence-core-subscription/$RUN/provenance.json")
mkdir -p "$OUT"
echo "harness-benchmark $(git -C "$HB" rev-parse HEAD), run $RUN, task $TASK" | tee "$OUT/provenance.txt"
FIXED=$OUT/hb-patched
if [ ! -d "$FIXED" ]; then
  git -C "$HB" worktree add --detach "$FIXED" HEAD >/dev/null 2>&1
  git -C "$FIXED" apply "$HB/evidence/issue49/mart_digests-single-file.patch"
fi
rm -rf "$OUT/repo"
(cd "$HB/golden/pipeline" && uv run -q --frozen --project "$HB" python -m pipetask.assemble "$TASK" --out "$OUT/repo") >/dev/null
git -C "$OUT/repo" apply --whitespace=nowarn "$HB/evidence/runs/$RUN/worktree-from-skeleton.patch"
git -C "$OUT/repo" add -A && git -C "$OUT/repo" -c user.name=regrade -c user.email=regrade@localhost commit -qm "$RUN as delivered"
for grader in committed patched; do
  tree=$HB; [ $grader = patched ] && tree=$FIXED
  rm -rf "$OUT/work-$grader"; cp -a "$OUT/repo" "$OUT/work-$grader"
  (cd "$tree/golden/pipeline" && uv run -q --frozen --project "$tree" python -m pipetask.trial --repo "$OUT/work-$grader" \
     --key key/answer_key.json --capture data/capture/recentchange.jsonl.gz --deadline 600 --snapshot-worktree \
     --logs "$OUT/logs-$grader") >"$OUT/grade-$grader.json" 2>"$OUT/grade-$grader.stderr"
  python3 - "$OUT/grade-$grader.json" "$RUN" "$grader" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(f"{sys.argv[2]} grader={sys.argv[3]:9} reward={d['reward']} passed={d['passed']}/{d['total']} "
      f"idempotent={d['idempotent']} stream_ok={d['stream_ok']} builds={[b['exit'] for b in d['build']]} "
      f"changed_by_second_build={d.get('changed_by_second_build')}")
for k, v in sorted(d["checks"].items()):
    print(f"  check {k}: pass={v.get('pass')} {str(v.get('error') or v.get('trap') or '')[:110]}")
PY
done
