#!/usr/bin/env bash
# Run the live tier on Harbor. Spends real money, so it refuses to start unless you
# state a budget at least as large as the worst case (trials x per-trial cap).
#
#   CBENCH_BUDGET_USD=90 ANTHROPIC_API_KEY=... scripts/live.sh            # full matrix
#   CBENCH_BUDGET_USD=1  ANTHROPIC_API_KEY=... scripts/live.sh smoke      # 1 trial, ~$1 cap
#
# Environment knobs: TRIALS (default 3), HAIKU_CAP_USD (1.00), BASELINE_CAP_USD (3.00),
# BASELINE_MODEL (claude-sonnet-5-5), JOBS_DIR (jobs).
set -euo pipefail
cd "$(dirname "$0")/.."

mode="${1:-full}"
trials="${TRIALS:-3}"
haiku_cap="${HAIKU_CAP_USD:-1.00}"
base_cap="${BASELINE_CAP_USD:-3.00}"
base_model="${BASELINE_MODEL:-claude-sonnet-5-5}"
jobs="${JOBS_DIR:-jobs}"
claude_version="$(python3 -c 'import re;print(re.search(r"CLAUDE_CODE_VERSION = \"([^\"]+)\"", open("cbench/harbor.py").read()).group(1))')"

# Arms run on Haiku 5.5: every framework plus a bare-Haiku control.
haiku_arms=(baseline cadence superpowers spec-kit openspec gsd-core bmad)
tasks=(t01-slugify-bugfix t02-invstat-json t03-token-bucket)
if [ "$mode" = smoke ]; then haiku_arms=(baseline); tasks=(t01-slugify-bugfix); trials=1; fi

haiku_trials=$(( ${#haiku_arms[@]} * ${#tasks[@]} * trials ))
base_trials=$(( ${#tasks[@]} * trials ))
[ "$mode" = smoke ] && base_trials=0
ceiling="$(python3 -c "print(f'{$haiku_trials * $haiku_cap + $base_trials * $base_cap:.2f}')")"
echo "haiku trials: $haiku_trials x \$$haiku_cap cap; ${base_model} baseline trials: $base_trials x \$$base_cap cap"
echo "worst-case spend: \$$ceiling (typical runs cost a fraction of the cap)"
: "${ANTHROPIC_API_KEY:?set ANTHROPIC_API_KEY}"
: "${CBENCH_BUDGET_USD:?set CBENCH_BUDGET_USD to at least the worst-case spend to confirm it}"
python3 -c "import sys; sys.exit(0 if float('$CBENCH_BUDGET_USD') >= float('$ceiling') else 1)" \
  || { echo "CBENCH_BUDGET_USD=$CBENCH_BUDGET_USD is below the worst case \$$ceiling; refusing to start" >&2; exit 1; }

export PYTHONPATH="$PWD/harbor/agents${PYTHONPATH:+:$PYTHONPATH}"
run() { # model cap arm...
  local model="$1" cap="$2"; shift 2
  local args=()
  for arm in "$@"; do for t in "${tasks[@]}"; do args+=(-i "${t}--${arm}"); done; done
  harbor run -p harbor/tasks "${args[@]}" -k "$trials" -n 2 -o "$jobs" -y \
    --agent-import-path cbench_claude:CbenchClaudeCode -m "anthropic/${model}" \
    --ak "version=${claude_version}" --ak "max_budget_usd=${cap}"
}
run claude-haiku-5-5 "$haiku_cap" "${haiku_arms[@]}"
[ "$base_trials" -gt 0 ] && run "$base_model" "$base_cap" baseline
echo "done. python -m cbench harbor-collect $jobs && python -m cbench report"
