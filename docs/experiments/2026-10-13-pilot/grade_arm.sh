#!/usr/bin/env bash
# Grade one pilot arm: hidden tests and procedure (grade.py), clean room, quality model, cost.
# Usage: grade_arm.sh ARM   (HB = harness-benchmark checkout with clean_room_check.py and quality_metrics.py)
set -euo pipefail
ARM="${1:?usage: grade_arm.sh ARM}"
W="$(cd "$(dirname "$0")/.." && pwd)"
D="$W/pilot/$ARM"
HB="${HB:-/Users/jasontouleyrou/Projects/harness-benchmark-wt/cleanroom}"

# The delivered head: the newest commit on any branch of the run's repo.
HEAD_SHA="$(git -C "$D/repo" for-each-ref --sort=-committerdate --format='%(objectname)' refs/heads | head -1)"
BASE="$(git -C "$D/repo" rev-list --max-parents=0 "$HEAD_SHA")"

python3 "$W/grade.py" "$D" budgets > /dev/null 2> "$D/grade.err" || true

rm -rf "$D/baseline" "$D/solution"
git clone -q "$D/origin.git" "$D/baseline" && git -C "$D/baseline" checkout -q "$BASE"
git clone -q "$D/repo" "$D/solution" && git -C "$D/solution" checkout -q "$HEAD_SHA"
git -C "$D/repo" diff "$BASE" "$HEAD_SHA" > "$D/solution/CHANGE.diff"
rm -rf "$D/solution/.git" "$D/baseline/.git"
python3 "$HB/scripts/quality_metrics.py" "$D/solution" "$D/baseline" > "$D/quality_metrics.json" 2> "$D/quality.err" || true

ALLOW=()
case "$ARM" in cadence_*) ALLOW=(--allow-path "$D/cadence") ;; esac
for t in "$D"/home/.claude/projects/*/*.jsonl; do
  # Cadence arms may call their own plugin's skills; list them from the plugin's skills folder.
  extra=()
  if [ -d "$D/cadence" ]; then
    extra+=(--allow cadence:cadence)
    for s in "$D"/cadence/skills/*/; do extra+=(--allow "cadence:$(basename "$s")"); done
    for c in "$D"/cadence/commands/*.md; do extra+=(--allow "cadence:$(basename "$c" .md)"); done
  fi
  python3 "$HB/scripts/clean_room_check.py" "$t" --cwd "$D/repo" --allow-path "$D/repo" \
    ${ALLOW[@]+"${ALLOW[@]}"} ${extra[@]+"${extra[@]}"} --json > "$D/clean_room.json" || true
done

# Cost from token counts at pricing.json list prices (Claude Code does not price Haiku 5.5).
python3 - "$D" "$HB/pricing.json" <<'PY'
import json, sys
from decimal import Decimal
from pathlib import Path
d, prices = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text())
table = prices.get("models") or prices
result = json.loads((d / "result.json").read_text())
rows, total = {}, Decimal(0)
for model, u in (result.get("modelUsage") or {}).items():
    p = table.get(model)
    if not p:
        rows[model] = {"usage": u, "usd": None, "note": "no price in pricing.json"}
        continue
    usd = (Decimal(u.get("inputTokens", 0)) * Decimal(p["input"]) + Decimal(u.get("outputTokens", 0)) * Decimal(p["output"])
           + Decimal(u.get("cacheCreationInputTokens", 0)) * Decimal(p["cache_write_5m"])
           + Decimal(u.get("cacheReadInputTokens", 0)) * Decimal(p["cache_read"])) / Decimal(1_000_000)
    rows[model] = {"input": u.get("inputTokens"), "output": u.get("outputTokens"),
                   "cache_write": u.get("cacheCreationInputTokens"), "cache_read": u.get("cacheReadInputTokens"),
                   "usd": str(usd.quantize(Decimal("0.0001")))}
    total += usd
out = {"by_model": rows, "usd_total": str(total.quantize(Decimal("0.0001"))),
       "host_reported_usd": result.get("total_cost_usd"), "num_turns": result.get("num_turns"),
       "is_error": result.get("is_error")}
(d / "cost.json").write_text(json.dumps(out, indent=2) + "\n")
PY

python3 - "$D" <<'PY'
import json, sys
from pathlib import Path
d = Path(sys.argv[1])
g = json.loads((d / "grading.json").read_text())
q = json.loads((d / "quality_metrics.json").read_text()) if (d / "quality_metrics.json").stat().st_size else {}
c = json.loads((d / "clean_room.json").read_text())
cost = json.loads((d / "cost.json").read_text())
t = json.loads((d / "timing.json").read_text())
exp = g.get("expectations", [])
print(f"{d.name}: {sum(e['passed'] for e in exp)}/{len(exp)} checks; "
      + "; ".join(f"{e['text'].split()[0]} {'ok' if e['passed'] else 'FAIL'}" for e in exp))
print(f"  clean room: {c['verdict']}  quality gate: {q.get('gate_passed')}  new-code cov {q.get('new_code_coverage')}  "
      f"cog max {q.get('cognitive_max')}  cost ${cost['usd_total']}  {t['total_duration_seconds']}s")
PY
