#!/usr/bin/env bash
# Pilot (harness-benchmark next-steps stage 1): one clean-room run of one arm on T05 budgets.
# Usage: run_arm.sh ARM
#   cadence_haiku         Cadence, every peer stage on Haiku 5.5 (peer_models default haiku)
#   cadence_haiku_opus    Cadence on Haiku 5.5, review peers (P3 P6 P7 R1 R2) on Opus 5.5
#   opus_oneshot          Opus 5.5, no harness
# Needs: CADENCE_SRC (a Cadence checkout with cd-58 peer_models merged), the workspace from
# make_workspace.sh (fixture/, evals.json). Each run gets its own empty HOME: no user-level skill,
# rule, command, memory or settings. Cadence is loaded with --plugin-dir for that session only.
# Runs use permission mode "auto": the host's safety classifier still checks each action.
# A harness run has no time cap (owner decision 2026-10-12).
set -euo pipefail
ARM="${1:?usage: run_arm.sh ARM}"
W="$(cd "$(dirname "$0")/.." && pwd)"
P="$W/pilot"
D="$P/$ARM"
[ -e "$D" ] && { echo "exists: $D" >&2; exit 1; }
mkdir -p "$D/outputs" "$D/home"
HOME_DIR="$D/home"

# Repository: the shared ledgerlite fixture, with a local bare origin.
tmp="$(mktemp -d)"
cp -R "$W/fixture/." "$tmp/"
rm -rf "$tmp/.venv"
printf '.context/\n__pycache__/\n.venv/\n.pytest_cache/\n' > "$tmp/.gitignore"
git -C "$tmp" init -q -b main
git -C "$tmp" -c user.email=eval@local -c user.name=eval add -A
git -C "$tmp" -c user.email=eval@local -c user.name=eval commit -qm "ledgerlite baseline"
git clone -q --bare "$tmp" "$D/origin.git"
git clone -q "$D/origin.git" "$D/repo"
rm -rf "$tmp"
git -C "$D/repo" config user.email eval@local
git -C "$D/repo" config user.name eval

TASK="$(python3 -c "import json,sys;print(next(e['prompt'] for e in json.load(open(sys.argv[1]))['evals'] if e['name']=='budgets'))" "$W/evals.json")"
ENV_NOTE="Environment (same for every run): there is no GitHub and no Linear. Where you would create, update, or comment on a PR or ticket, write that text to $D/outputs/PR.md (append comments) and continue as if it succeeded. Nobody will answer questions: work autonomously to the end. Save outputs to $D/outputs/: summary.md (what you did, and each pipeline stage and its result when you follow a pipeline) and PR.md (the PR title and body). Do all work in $D/repo (git; branch main; origin is a local bare repo)."

PLUGIN=()
EXTRA_ENV=()
case "$ARM" in
  cadence_haiku|cadence_haiku_opus)
    : "${CADENCE_SRC:?set CADENCE_SRC to a Cadence checkout with cd-58 merged}"
    cp -R "$CADENCE_SRC" "$D/cadence"
    rm -rf "$D/cadence/.git" "$D/cadence/.venv" "$D/cadence/.context"
    if [ "$ARM" = cadence_haiku ]; then
      MODELS='{"default": "haiku"}'
    else
      MODELS='{"default": "haiku", "plan-review": "opus", "adversarial-review": "opus", "test-benchmark-plan": "opus", "pr-review-local": "opus", "test-benchmark-pr": "opus"}'
    fi
    python3 - "$D/cadence/cadence.config.json" "$MODELS" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
cfg = json.loads(path.read_text()) if path.is_file() else {}
cfg["peer_models"] = json.loads(sys.argv[2])
path.write_text(json.dumps(cfg, indent=2) + "\n")
PY
    MODEL=claude-haiku-5-5
    PLUGIN=(--plugin-dir "$D/cadence")
    EXTRA_ENV=(CADENCE_HOME="$D/cadence")
    PROMPT="/cadence:cadence $TASK

$ENV_NOTE"
    ;;
  opus_oneshot)
    MODEL=claude-opus-5-5
    PROMPT="$TASK

$ENV_NOTE"
    ;;
  *) echo "unknown arm: $ARM" >&2; exit 2 ;;
esac

printf '%s\n' "$PROMPT" > "$D/prompt.txt"
start=$(python3 -c 'import time;print(time.time())')
cd "$D/repo"
# The haiku alias (used by peer_models) must resolve to Haiku 5.5, not Claude Code's default Haiku.
env -i PATH="$PATH" HOME="$HOME_DIR" TERM=dumb LANG="${LANG:-en_US.UTF-8}" \
  ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-haiku-5-5 \
  ANTHROPIC_DEFAULT_OPUS_MODEL=claude-opus-5-5 \
  ${EXTRA_ENV[@]+"${EXTRA_ENV[@]}"} \
  claude -p "$PROMPT" --model "$MODEL" ${PLUGIN[@]+"${PLUGIN[@]}"} \
    --permission-mode auto --add-dir "$D/outputs" --output-format json \
    > "$D/result.json" 2> "$D/stderr.log" || echo "claude exit $?" >> "$D/stderr.log"
end=$(python3 -c 'import time;print(time.time())')
python3 - "$D" "$start" "$end" <<'PY'
import json, sys
from pathlib import Path
d, start, end = Path(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
(d / "timing.json").write_text(json.dumps({"total_duration_seconds": round(end - start, 1)}, indent=2))
PY
echo "done: $D"
