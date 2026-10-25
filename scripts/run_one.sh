#!/usr/bin/env bash
# One benchmark Cadence run ($BATCH: batch F iteration 1, then the 2026-10-24-shapes head to head, its round 2, 2026-10-24-shapes-r2, round 3, 2026-10-25-shapes-r3, and its smoke run on the unmerged fix, BATCH=2026-10-25-smoke-r3fix), from a fresh cloud container of this environment (host method, the
# subscription through the session's HTTPS proxy). One run per container: the dev replay owns localhost:8099,
# which the spec itself names (golden/pipeline/P1/prompt.md:17), so two runs never share a host.
#
#   scripts/run_one.sh <run-id> [--dry-run]       e.g. 20261024-P2-cadence-haiku-core-1
#
# The run id names the Cadence run shape (owner, 2026-10-24: core and full, head to head): -cadence-haiku-core-
# or -cadence-haiku-full-. The shape goes on the record (loop.driver --shape) and into the run repo's
# .cadence.json `profile` (host_trial --shape).
#
# It clones harness-benchmark at HB_SHA (the driver), adds a worktree of it at the batch's pinned grader_commit
# (GRADER_SHA: the grader, batches/<batch>.json), and clones cadence at CADENCE_SHA (a clean plugin clone), installs the driver's environment, runs loop.driver --spec for the run (Haiku, peers on Haiku,
# adapter none, a fresh HOME, a cwd holding only the run, both isolation scans, the batch's agent cap), then
# publishes: the blobs to runs-store, and the record with its regenerated postmortem and scoreboard on branch
# rec/<run-id> from origin/main, after loop.check and scripts/ci_local.sh pass. The pull request itself is
# opened by the session (no gh here): the body is written to $WORK/pr.md.
# --dry-run stops just before the agent starts, after every setup check, and prints the driver command.
#
#   scripts/run_one.sh <run-id> --detach [--dry-run | --finish [--again]]
#   scripts/run_one.sh <run-id> --wait
#
# --detach starts the run (with the options after it) under setsid nohup, in its own session, so a caller's
# timeout that kills its process group does not kill the run (2026-10-24: the Bash tool's 2 h limit killed
# P1 core-1 and core-3). It writes $WORK/run.pid and $WORK/run.log and returns at once. --wait blocks while
# that run is alive, at most RUN_ONE_WAIT_SECONDS (default 6600, 110 min); exit 0 when it has finished (its exit
# code and last log line are printed), 75 while it still runs (call --wait again), 1 if it died without an exit
# code, 2 if there is no detached run.
# Exit 2: a setup failure (the message says which); 4: the run was an infrastructure loss (nothing published);
# 3: a check before publishing failed (nothing pushed); 1: anything else.
set -euo pipefail

HB_REPO=https://github.com/jtouley/harness-benchmark
CADENCE_REPO=https://github.com/jtouley/cadence
# The driver: by default the commit of this script's own checkout, so the run uses the code that runs it.
# Override with HB_SHA=<commit>. The grader is not HB_SHA but the batch's pinned grader_commit (GRADER_SHA below).
HB_SHA=${HB_SHA:-$(git -C "$(dirname "$0")" rev-parse HEAD)}
BATCH=${BATCH:-2026-10-25-shapes-r3}
CADENCE_CAP=21600   # batches/2026-10-23-batch-f.json agent_caps.cadence: 3 x the one-shot cap
PORT=8099

die() { echo "run_one: $*" >&2; exit 2; }
log() { printf '%s run_one %s: %s\n' "$(date -u +%FT%TZ)" "$RID" "$*" | tee -a "$WORK/run_one.log" >&2; }

[ $# -ge 1 ] || die "usage: scripts/run_one.sh <run-id> [--detach] [--dry-run | --finish [--again]] | <run-id> --wait"
RID=$1
case "${2:-}" in --detach|--wait)
  [[ "$RID" =~ ^[0-9]{8}-P[12]-cadence-haiku-(core|full)-[a-z0-9-]+$ ]] || die "run id $RID is not <date>-P1|P2-cadence-haiku-core|full-<n>"
  WORK=${RUN_ONE_WORK:-/var/tmp/run-one}/$RID
  if [ "$2" = --detach ]; then
    [ ! -e "$WORK" ] || die "$WORK exists: a run id is never reused"
    mkdir -p "$WORK"
    # RUN_ONE_DETACH_CMD replaces the run in tests (a fake long command); the run is this script itself.
    CMD=${RUN_ONE_DETACH_CMD:-$(printf '%q ' bash "$(realpath "$0")" "$RID" "${@:3}")}
    RUN_ONE_DETACHED=1 W=$WORK setsid nohup bash -c 'echo $$ >"$W/run.pid.tmp" && mv "$W/run.pid.tmp" "$W/run.pid"
      ( '"$CMD"' )
      echo $? >"$W/run.exit"' >"$WORK/run.log" 2>&1 </dev/null &
    for _ in $(seq 100); do [ -s "$WORK/run.pid" ] && break; sleep 0.1; done
    [ -s "$WORK/run.pid" ] || die "the detached run wrote no $WORK/run.pid"
    echo "detached: pid $(cat "$WORK/run.pid"), log $WORK/run.log; wait with: $0 $RID --wait"
    exit 0
  fi
  [ -s "$WORK/run.pid" ] || die "no detached run: $WORK/run.pid is missing"
  PID=$(cat "$WORK/run.pid")
  END=$(( $(date +%s) + ${RUN_ONE_WAIT_SECONDS:-6600} ))
  while [ ! -e "$WORK/run.exit" ] && kill -0 "$PID" 2>/dev/null && [ "$(date +%s)" -lt "$END" ]; do
    sleep "${RUN_ONE_POLL_SECONDS:-30}"
  done
  if [ -e "$WORK/run.exit" ]; then
    echo "$RID finished, exit $(cat "$WORK/run.exit"): $(tail -n 1 "$WORK/run.log")"
    exit 0
  fi
  if kill -0 "$PID" 2>/dev/null; then echo "$RID still running (pid $PID): call --wait again"; exit 75; fi
  echo "$RID ended without an exit code (pid $PID is gone): see $WORK/run.log"
  exit 1;;
esac
MODE=${2:-}
AGAIN=${3:-}
case "$MODE" in ""|--dry-run|--finish) ;; *) die "unknown option $MODE (--dry-run or --finish)";; esac
case "$AGAIN" in "") ;; --again) [ "$MODE" = --finish ] || die "--again goes with --finish";; *) die "unknown option $AGAIN";; esac
[[ "$RID" =~ ^[0-9]{8}-(P[12])-cadence-haiku-(core|full)-[a-z0-9-]+$ ]] \
  || die "run id $RID is not <date>-P1|P2-cadence-haiku-core|full-<n>"
TASK=${BASH_REMATCH[1]}
SHAPE=${BASH_REMATCH[2]}
# The cadence commit is the batch pin's: one sha, or one per run shape (batches/2026-10-24-shapes.json: core and
# full). A CADENCE_SHA from the environment must be that pin.
PIN_FILE="$(cd "$(dirname "$0")/.." && pwd)/batches/$BATCH.json"
[ -f "$PIN_FILE" ] || die "no batches/$BATCH.json in this checkout: the batch has no pin"
PINNED=$(python3 - "$PIN_FILE" "$SHAPE" <<'PY'
import json, sys
pinned = json.load(open(sys.argv[1])).get("cadence_commit")
print((pinned.get(sys.argv[2]) if isinstance(pinned, dict) else pinned) or "")
PY
)
[ -n "$PINNED" ] || die "batches/$BATCH.json pins no cadence commit for shape $SHAPE"
[ -z "${CADENCE_SHA:-}" ] || [ "$CADENCE_SHA" = "$PINNED" ] \
  || die "CADENCE_SHA=$CADENCE_SHA is not the pin of batches/$BATCH.json for shape $SHAPE ($PINNED)"
CADENCE_SHA=$PINNED
# The grader is the batch pin's grader_commit (criteria v2: the grader is pinned before the first run; batch F:
# "every run is graded with this grader"), checked out as its own worktree $WORK/grader, so the grade runs that
# commit's golden/pipeline/pipetask and the score names it. Before this, the run graded with HB_SHA and recorded
# HB_SHA (every 2026-10-24-shapes-r2 score names c344bea, the pin is 10172ce; same grader tree 8a0977e).
read -r PIN_GRADER PIN_TREE < <(python3 - "$PIN_FILE" <<'PY'
import json, sys
pin = json.load(open(sys.argv[1]))
print(pin.get("grader_commit") or "-", pin.get("grader_tree") or "-")
PY
)
[ "$PIN_GRADER" != - ] || die "batches/$BATCH.json pins no grader_commit"
[ -z "${GRADER_SHA:-}" ] || [ "$GRADER_SHA" = "$PIN_GRADER" ] \
  || die "GRADER_SHA=$GRADER_SHA is not the grader_commit of batches/$BATCH.json ($PIN_GRADER)"
GRADER_SHA=$PIN_GRADER
# Never under HOME: the plugin clone would sit where the driver's other-checkout scan looks, and the publish
# step's ci_local runs driver tests that scan HOME (run 20261024-P1-cadence-haiku-core-1r).
WORK=${RUN_ONE_WORK:-/var/tmp/run-one}/$RID
case "$(realpath -m "$WORK")/" in "$(realpath -m "$HOME")"/*) die "$WORK is under HOME ($HOME): set RUN_ONE_WORK outside it";; esac
RUN=$WORK/run/$RID
STORE=$WORK/store
PLUGIN=$WORK/plugin
GRADER=$WORK/grader
FINISH_ARGS=()
# Where the record, its stop and its branch go. --finish --again writes them all to new places and deletes
# nothing: a run whose first finish was wrong (#105) gets a second record on rec/<id>-v2, with no force push.
RUNS_DIR=$WORK/hb/runs
STOP_FILE=$RUN/stop.json
REC_WT=$WORK/rec
REC_BRANCH=rec/$RID
PR_MD=$WORK/pr.md
if [ "$AGAIN" = --again ]; then
  RUNS_DIR=$WORK/again/runs
  STOP_FILE=$WORK/again/stop.json
  REC_WT=$WORK/rec-v2
  REC_BRANCH=rec/$RID-v2
  PR_MD=$WORK/pr-v2.md
  for path in "$WORK/again" "$REC_WT" "$PR_MD"; do [ ! -e "$path" ] || die "--again: $path exists (nothing is deleted)"; done
  if git -C "$WORK/hb" ls-remote --exit-code --heads origin "$REC_BRANCH" >/dev/null 2>&1; then
    die "--again: $REC_BRANCH is already on origin"
  fi
  mkdir -p "$WORK/again"
fi
if [ "$MODE" = --finish ]; then
  # The agent ran in $WORK and was graded, but no record was written (run 20261024-P2-cadence-haiku-core-1: the
  # driver crashed on a transcript event). Finish it from the saved run directory with this checkout's driver
  # (HB_SHA), without running the agent again: loop.driver --finish, then the same publish step.
  [ -f "$RUN/transcript.jsonl" ] || die "--finish: no $RUN/transcript.jsonl; the run never ran in $WORK"
  [ -d "$PLUGIN/.git" ] && [ -d "$STORE/.git" ] && [ -d "$WORK/hb/.git" ] || die "--finish: $WORK lacks hb, plugin or store"
  [ "$(git -C "$GRADER" rev-parse HEAD 2>/dev/null)" = "$GRADER_SHA" ] \
    || die "--finish: no grader worktree $GRADER at the pinned $GRADER_SHA, so no commit names the grader that graded it"
  [ "$(git -C "$PLUGIN" rev-parse HEAD)" = "$CADENCE_SHA" ] || die "--finish: the plugin clone is not at $CADENCE_SHA"
  [ ! -e "$RUNS_DIR/$RID/record.json" ] || die "--finish: $RID already has a record in $RUNS_DIR (finish it again with --finish --again)"
  log "finishing from $RUN with harness-benchmark $HB_SHA"
  git -C "$WORK/hb" fetch -q origin || die "cannot fetch harness-benchmark"
  git -C "$WORK/hb" checkout -q --detach "$HB_SHA" || die "harness-benchmark has no commit $HB_SHA"
  (cd "$WORK/hb" && uv sync -q --frozen) || die "uv sync --frozen failed in $WORK/hb"
  grep -q -- '"--finish"' "$WORK/hb/loop/driver.py" || die "harness-benchmark $HB_SHA has no loop.driver --finish"
  FINISH_ARGS=(--finish)
  # The stop with this checkout's rules (the transcript's last open block, run 20261024-P2-cadence-haiku-core-1).
  (cd "$WORK/hb" && uv run -q --frozen python scripts/host_trial.py "$TASK" --out "$RUN" --model claude-haiku-5-5 \
     --plugin-dir "$PLUGIN" --stop-only --stop-file "$STOP_FILE") >>"$RUN/driver.out" 2>&1 \
     || die "--finish: host_trial --stop-only failed (see $RUN/driver.out)"
  log "stop derived again: $(cat "$STOP_FILE")"
else
# A detached run (--detach) starts in the folder that holds only its run.pid and run.log.
if [ -n "${RUN_ONE_DETACHED:-}" ]; then
  [ -z "$(ls -A "$WORK" | grep -v -x -e run.pid -e run.log)" ] || die "$WORK exists: a run id is never reused (remove it only if nothing was published)"
else
  [ ! -e "$WORK" ] || die "$WORK exists: a run id is never reused (remove it only if nothing was published)"
fi

# --- setup checks
for tool in git uv python3 claude; do command -v "$tool" >/dev/null || die "$tool is not on PATH"; done
claude --version >/dev/null 2>&1 || die "claude --version fails"
[ -n "${HTTPS_PROXY:-}" ] || die "HTTPS_PROXY is not set: the agent authenticates through the session's proxy (--auth proxy)"
[ -z "${ANTHROPIC_API_KEY:-}" ] || die "ANTHROPIC_API_KEY is set: the runs use the subscription, never an API key"
python3 - "$PORT" <<'PY' || die "port $PORT is taken: one run per container (the spec names localhost:$PORT)"
import socket, sys
s = socket.socket()
sys.exit(1 if s.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 0)
PY
mkdir -p "$WORK"

log "cloning harness-benchmark at $HB_SHA"
git clone -q "$HB_REPO" "$WORK/hb" || die "cannot clone $HB_REPO"
git -C "$WORK/hb" checkout -q --detach "$HB_SHA" || die "harness-benchmark has no commit $HB_SHA"
(cd "$WORK/hb" && uv sync -q --frozen) || die "uv sync --frozen failed in $WORK/hb"
[ -f "$WORK/hb/golden/pipeline/$TASK/prompt.md" ] || die "no golden/pipeline/$TASK/prompt.md at $HB_SHA"
grep -q -- '"--shape"' "$WORK/hb/loop/driver.py" && grep -q -- '"--shape"' "$WORK/hb/scripts/host_trial.py" \
  || die "harness-benchmark $HB_SHA has no --shape (driver or host_trial): use a commit with run shapes"
grep -q -- '"--grader-root"' "$WORK/hb/scripts/host_trial.py" && grep -q -- 'check_pinned_grader' "$WORK/hb/loop/driver.py" \
  || die "harness-benchmark $HB_SHA cannot grade with the pinned grader (host_trial --grader-root): use a later commit"

log "grader worktree at the pinned grader_commit $GRADER_SHA"
git -C "$WORK/hb" worktree add -q --detach "$GRADER" "$GRADER_SHA" || die "harness-benchmark has no commit $GRADER_SHA"
[ "$PIN_TREE" = - ] || [ "$(git -C "$GRADER" rev-parse "HEAD:golden/pipeline/pipetask")" = "$PIN_TREE" ] \
  || die "the grader tree at $GRADER_SHA is not batches/$BATCH.json's grader_tree $PIN_TREE"

log "cloning cadence at $CADENCE_SHA"
git clone -q "$CADENCE_REPO" "$PLUGIN" || die "cannot clone $CADENCE_REPO"
# The clone has every branch head, so a pin on an unmerged branch (2026-10-25-smoke-r3fix: cadence #234,
# fix/shapes-r3) is there. A pin whose branch is gone (merged and deleted) is still a pull request head: fetch
# those as remote refs, so the checkout finds it and the remote-branch check below sees it.
if ! git -C "$PLUGIN" cat-file -e "$CADENCE_SHA^{commit}" 2>/dev/null; then
  git -C "$PLUGIN" fetch -q origin '+refs/pull/*/head:refs/remotes/origin/pull/*' || die "cannot fetch cadence pull request heads"
fi
git -C "$PLUGIN" checkout -q --detach "$CADENCE_SHA" || die "cadence has no commit $CADENCE_SHA"
[ -n "$(git -C "$PLUGIN" branch -r --contains HEAD)" ] || die "cadence $CADENCE_SHA is on no remote branch"
[ -z "$(git -C "$PLUGIN" status --porcelain --ignored)" ] || die "the plugin clone is not clean"

log "cloning the runs-store branch (blobs)"
git clone -q --single-branch --branch runs-store --depth 1 "$HB_REPO" "$STORE" || die "cannot clone runs-store"

mkdir -p "$RUN/spec"
cp "$WORK/hb/golden/pipeline/$TASK/prompt.md" "$RUN/spec/spec.md"
fi
DRIVER=(uv run -q --frozen python -m loop.driver --run-id "$RID" --kind benchmark --batch "$BATCH"
  --task "$TASK" --request-id "$TASK-spec" --arm cadence --model claude-haiku-5-5
  --plugin-dir "$PLUGIN" --context "$RUN/context" --spec "$RUN/spec/spec.md" --cwd "$RUN"
  --fresh-home "$RUN/home" --agent-argv "$RUN/agent-argv.json" --transcript "$RUN/transcript.jsonl"
  --tree "$RUN/repo-as-left" --graded-repo "$RUN/repo" --grade "$RUN/grade.json" --grader-repo "$GRADER" --stop-point-file "$STOP_FILE"
  --timing "$RUN/timing.json" --store "$STORE" --isolation-method host --auth proxy --shape "$SHAPE"
  --runs "$RUNS_DIR" "${FINISH_ARGS[@]}" -- uv run -q --frozen --project "$WORK/hb" python "$WORK/hb/scripts/host_trial.py" "$TASK" --out "$RUN"
  --model claude-haiku-5-5 --auth proxy --plugin-dir "$PLUGIN" --peer-model haiku --agent-cap "$CADENCE_CAP"
  --shape "$SHAPE" --grader-root "$GRADER")

if [ "$MODE" = --dry-run ]; then
  # The agent's jail (#112) on this host: the scan from inside finds nothing, and claude logs in there.
  grep -q -- '"--jail-check"' "$WORK/hb/scripts/host_trial.py" || die "harness-benchmark $HB_SHA has no host_trial --jail-check"
  (cd "$WORK/hb" && uv run -q --frozen python scripts/host_trial.py "$TASK" --out "$RUN" --model claude-haiku-5-5 \
     --plugin-dir "$PLUGIN" --jail-check) >>"$RUN/driver.out" 2>&1 || die "the agent's jail check failed: $(cat "$RUN/jail-check.json" 2>/dev/null || tail -3 "$RUN/driver.out")"
  log "jail check: $(python3 -c 'import json, sys; r = json.load(open(sys.argv[1])); print("visible", r["visible"], "agent exit", r["agent_exit"], "reply", repr(r["agent_reply"]))' "$RUN/jail-check.json")"
  log "dry run: every setup check passed; the agent would start now with:"
  printf '%q ' "${DRIVER[@]}"; echo
  exit 0
fi

# --- the run
log "start (shape $SHAPE, batch $BATCH, cadence $CADENCE_SHA, harness $HB_SHA, grader $GRADER_SHA)"
set +e
(cd "$WORK/hb" && "${DRIVER[@]}") >>"$RUN/driver.out" 2>&1
rc=$?
set -e
REC=$RUNS_DIR/$RID
[ -f "$REC/record.json" ] || { log "driver exit $rc and no record (see $RUN/driver.out)"; exit 1; }
# The summary line (loop/run_summary.py, from this script's own checkout): the headline is the scoreboard's score,
# round(reward x total)/total, then passed, reward, stream_ok and idempotent (run 20261024-P1-cadence-haiku-core-4
# printed its passed 2/7 here while its score was 0/7). It goes in the commit message, pr.md and the last log line.
SUMMARY=$(PYTHONPATH="$(cd "$(dirname "$0")/.." && pwd)" python3 -m loop.run_summary "$REC")
log "driver exit $rc: $SUMMARY"
if [ -n "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("api_error") or "")' "$REC/record.json")" ]; then
  log "infrastructure loss (the API cut the run off): nothing is published; rerun with a new id"
  exit 4
fi
# The blocks the run opened (scripts/blocks_report.py from this script's own checkout: HB_SHA predates it).
BLOCKS=$(python3 -I "$(dirname "$0")/blocks_report.py" "$RUN" 2>&1 || true)

# --- publish: blobs, then the record on rec/<run-id>
log "pushing blobs to runs-store"
# Parallel runs push to the same branch: push_blobs.sh retries on the new tip and checks every blob landed.
bash "$(dirname "$0")/push_blobs.sh" "$STORE" "$RID" || { log "the blobs are not all on runs-store; nothing else is pushed"; exit 1; }

log "record branch $REC_BRANCH from origin/main"
git -C "$WORK/hb" fetch -q origin main
git -C "$WORK/hb" worktree add -q -b "$REC_BRANCH" "$REC_WT" origin/main
cp -r "$REC" "$REC_WT/runs/$RID"
(
  set -eo pipefail
  cd "$REC_WT"
  [ -f "batches/$BATCH.json" ] || { echo "run_one: batches/$BATCH.json is not on main"; exit 3; }
  uv sync -q --frozen
  [ -f "postmortems/$BATCH.md" ] || uv run -q --frozen python -m loop.postmortem "$BATCH" --out "postmortems/$BATCH.md"
  uv run -q --frozen python -m loop.postmortem --all >/dev/null
  uv run -q --frozen python -m loop.scoreboard --out scoreboard.md
  uv run -q --frozen python -m loop.check --base origin/main
  uv run -q --frozen python -m loop.graded --store "$STORE" --run "$RID"
  bash scripts/ci_local.sh 2>&1 | tail -3
) || { log "a check before publishing failed: nothing pushed (fix, then push $REC_BRANCH by hand)"; exit 3; }
git -C "$REC_WT" add -A runs postmortems scoreboard.md
git -C "$REC_WT" commit -q -m "$BATCH: $RID

$SUMMARY"
for i in 1 2 3 4; do
  git -C "$REC_WT" push -q -u origin "$REC_BRANCH" && break
  [ "$i" = 4 ] && { log "push of $REC_BRANCH failed 4 times"; exit 1; }
  sleep $((2 ** i))
done
HEAD_SHA=$(git -C "$REC_WT" rev-parse --short HEAD)
cat >"$PR_MD" <<EOF
Record of batch $BATCH: \`$RID\`. Merge with a merge commit (the record cites its grader commit $GRADER_SHA).

**Score:** $SUMMARY

Ran on cadence $CADENCE_SHA, the driver at harness-benchmark $HB_SHA and the grader at the batch's pinned
grader_commit $GRADER_SHA, on its own host
(one run per container; the spec names localhost:8099). The record is the driver's, unchanged; the batch
postmortem and \`scoreboard.md\` are regenerated by the generators. The transcript and tree blobs are on runs-store.

**Blocks opened, from the run's attest logs** (a known deviation from ADR-0007's twelve-block core):
\`\`\`
$BLOCKS
\`\`\`

Checks before the push: \`loop.check --base origin/main\` and \`scripts/ci_local.sh\` at $HEAD_SHA (see the
session's log $WORK/run_one.log).
EOF
log "pushed $REC_BRANCH at $HEAD_SHA; PR title '$BATCH: $RID', body $PR_MD"
echo "$SUMMARY"
