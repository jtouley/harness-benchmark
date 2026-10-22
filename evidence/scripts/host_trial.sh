#!/usr/bin/env bash
# One cadence-core pipeline trial on the host (no Docker daemon here), the 19 October method:
# clean HOME, dev replay (seed 0) during the session, grader (seed 1) after it, no clean room.
# Differences from that round: the session is not bounded by any shell or tool limit (criteria v2
# section 5.3: a harness arm gets only the backstop, runner/pipeline/caps.json default 86,400 s), and
# Claude Code authenticates with the operator's subscription, not an API key.
# Usage: host_trial.sh TASK RUN_NAME [MODEL] [PEER_ALIAS]
set -uo pipefail
TASK=$1 RUN=$2 MODEL=${3:-claude-haiku-5-5} PEER=${4:-haiku}
HB=/home/user/harness-benchmark
GP=$HB/golden/pipeline
SRC=/root/.cache/cadence-bench/src/cadence-core@29315c4e64ff318a80a1a7d2c809beb4b3c15611
BASE=${PIPE_ROOT:-/tmp/claude-0/-home-user/5b20bc6c-3f91-5511-8000-71d5898a937e/scratchpad/pipe}
BACKSTOP=86400
OUT=$BASE/$RUN
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$OUT/driver.log"; }
now() { date +%s.%N; }

[ -e "$OUT" ] && { echo "exists: $OUT" >&2; exit 2; }
mkdir -p "$OUT/home/.config/cadence" "$OUT/outputs"
log "trial $RUN: task $TASK, model $MODEL, peers $PEER, cadence-core $(git -C "$SRC" rev-parse HEAD)"

# 1. The starting repository, on the run's branch, with a local bare origin and the arm's config.
(cd "$GP" && uv run -q --project "$HB" python -m pipetask.assemble "$TASK" --out "$OUT/repo") >/dev/null 2>>"$OUT/driver.log" \
  || { log "assemble failed"; exit 3; }
git init -q --bare "$OUT/origin.git"
cat >"$OUT/repo/.cadence.json" <<'JSON'
{
  "gated_prefixes": ["src/", "lib/", "app/", "packages/", "pipeline/", "engine/", "pipelines/", "transform/", "Makefile"]
}
JSON
printf '{"adapter": "none", "peer_models": {"default": "%s"}}\n' "$PEER" >"$OUT/home/.config/cadence/config.json"
(cd "$OUT/repo" && git checkout -q -b feature/gh-1-pipeline && git add .cadence.json \
  && git -c user.name=cbench -c user.email=cbench@localhost commit -q -m "cadence config for the trial" \
  && git remote add origin "$OUT/origin.git" && git push -q -u origin feature/gh-1-pipeline) 2>>"$OUT/driver.log" \
  || { log "repo setup failed"; exit 3; }
BASE_SHA=$(git -C "$OUT/repo" rev-parse HEAD)

# 2. The prompt: the lockfile's Cadence drive prompt around the task prompt, plus the 19 October environment note.
python3 - "$HB/frameworks.lock.json" "$GP/$TASK/prompt.md" "$OUT" >"$OUT/prompt.txt" <<'PY'
import json, sys
lock, task, out = sys.argv[1:]
drive = json.load(open(lock))["frameworks"]["cadence-core"]["drive_prompt"]
note = ("Environment (same for every run): there is no GitHub and no Linear. Where you would create, update, or "
        f"comment on a PR or ticket, write that text to {out}/outputs/PR.md (append comments) and continue as if it "
        "succeeded. Nobody will answer questions: work autonomously to the end. Save outputs to "
        f"{out}/outputs/: summary.md (what you did, and each pipeline stage and its result) and PR.md (the PR title "
        f"and body). Do all work in {out}/repo (git; branch feature/gh-1-pipeline; origin is a local bare repo). "
        "The task id is gh-1.")
sys.stdout.write(drive.replace("{issue}", open(task).read().rstrip("\n")) + "\n\n" + note + "\n")
PY

# 3. The dev replay on localhost:8099, seed 0.
port_open() { (exec 3<>/dev/tcp/127.0.0.1/8099) 2>/dev/null; }
if port_open; then log "port 8099 is taken before the dev replay starts"; exit 4; fi
(cd "$GP" && exec uv run -q --project "$HB" python -m pipetask.replay --capture data/capture/recentchange.jsonl.gz \
  --seed 0 --port 8099) >"$OUT/replay-dev.log" 2>&1 &
REPLAY=$!
for _ in $(seq 1 60); do port_open && break; sleep 1; done
port_open || { log "the dev replay did not start"; kill $REPLAY; exit 4; }

cat >"$OUT/provenance.json" <<EOF
{
  "arm": "cadence-core",
  "task": "$TASK",
  "model": "$MODEL",
  "cadence_repo": "https://github.com/jtouley/cadence-core",
  "cadence_sha": "$(git -C "$SRC" rev-parse HEAD)",
  "claude_version": "$(claude --version)",
  "auth": "the operator's Claude subscription (no API key)",
  "isolation": "host (no Docker daemon here): clean HOME, no clean room, dev replay seed 0, grading seed 1",
  "time_limit": "none but the harness backstop of $BACKSTOP s (runner/pipeline/caps.json default)",
  "plugin_config": {"adapter": "none", "peer_models": {"default": "$PEER"},
                    "gated_prefixes_extra": ["pipeline/", "engine/", "pipelines/", "transform/", "Makefile"]},
  "base_sha": "$BASE_SHA"
}
EOF

# 4. The agent: its own process group, so every process it leaves can be stopped before grading.
log "agent start"
t0=$(now)
# The operator's own Claude Code session variables are dropped, so the trial is its own session (on
# 21 October the first run inherited them and reported under the operator's session id). Auth still
# works: it goes through the environment's proxy (ANTHROPIC_BASE_URL), on the operator's subscription.
(cd "$OUT/repo" && for v in $(compgen -e | grep -E '^(CLAUDE|CCR_|AI_AGENT$|DOCUMENTS_)'); do unset "$v"; done \
 && export HOME="$OUT/home" CADENCE_HOME="$SRC" DISABLE_AUTOUPDATER=1 \
   CLAUDE_AUTO_BACKGROUND_TASKS=false CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 \
 && exec setsid --wait bash -c 'ps -o sid= -p $$ | tr -d " " >"$0/agent.sid"
      exec timeout "$1" claude -p "$(cat "$0/prompt.txt")" --model "$2" --permission-mode auto \
        --add-dir "$0/outputs" --plugin-dir "$3" --output-format stream-json --verbose' \
      "$OUT" "$BACKSTOP" "$MODEL" "$SRC") >"$OUT/transcript.jsonl" 2>"$OUT/agent.stderr" &
AGENT=$!
wait $AGENT; rc=$?
t1=$(now)
log "agent exit $rc"
[ -s "$OUT/agent.sid" ] && pkill -TERM -s "$(cat "$OUT/agent.sid")" 2>/dev/null
# Any process still started from the trial tree (a stream consumer the agent left running).
for pid in $(pgrep -f "$OUT/repo" || true); do kill -TERM "$pid" 2>/dev/null; done
sleep 2
for pid in $(pgrep -f "$OUT/repo" || true); do kill -KILL "$pid" 2>/dev/null; done
kill $REPLAY 2>/dev/null; wait $REPLAY 2>/dev/null
for _ in $(seq 1 30); do port_open || break; sleep 1; done
grep '"type":"result"' "$OUT/transcript.jsonl" | tail -1 >"$OUT/result.json" || true

# 5. Records the grader's reset would remove: the run's .context, commits.
cp -a "$OUT/repo/.context" "$OUT/context" 2>/dev/null || true
git -C "$OUT/repo" log --format='%h %ad %s' --date=iso-strict "$BASE_SHA..HEAD" >"$OUT/commits.txt" 2>/dev/null || true
cp -a "$OUT/repo" "$OUT/repo-as-left"

# 6. Grade: snapshot the working tree, reset, build twice, stream twice against seed 1, check.
log "grader start"
t2=$(now)
(cd "$GP" && uv run -q --project "$HB" python -m pipetask.trial --repo "$OUT/repo" --key key/answer_key.json \
   --capture data/capture/recentchange.jsonl.gz --deadline 600 --snapshot-worktree --logs "$OUT/grade-logs") \
   >"$OUT/grade.json" 2>"$OUT/grade.stderr"
grc=$?
t3=$(now)
log "grader exit $grc: $(python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print('reward', d.get('reward'))" "$OUT/grade.json" 2>&1)"
python3 - "$OUT/timing.json" "$t0" "$t1" "$t2" "$t3" "$rc" "$grc" "$BACKSTOP" <<'PY'
import json, sys
p, t0, t1, t2, t3, rc, grc, cap = sys.argv[1:]
json.dump({"agent_seconds": round(float(t1) - float(t0), 1), "grader_seconds": round(float(t3) - float(t2), 1),
           "agent_exit": int(rc), "grader_exit": int(grc), "backstop_seconds": int(cap),
           "hit_backstop": int(rc) == 124}, open(p, "w"), indent=1)
PY
log "done"
