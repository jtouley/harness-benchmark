#!/usr/bin/env bash
# Runs one trial inside the trial container (PID 1 is tini; this script is its only child).
#
# Inputs, copied in by run_trial.sh before the container starts:
#   /trial/repo/        the task repository (the agent's working directory)
#   /trial/prompt.txt   the full prompt (task prompt plus the arm's suffix)
#   /trial/plugin/      the arm's Claude Code plugin (empty: no plugin)
#   /trial/agent.sh     optional; replaces the Claude Code agent (tests use a stub here)
# The grader arrives later: run_trial.sh copies it to /trial/grader once this script logs "waiting for
# the grader" (after every agent process is dead), then creates /trial/grader-ready. It runs as
# `grader /trial/repo` and prints the grade JSON on stdout.
# Environment: HB_MODEL, HB_PERMISSION_MODE, HB_AGENT_TIMEOUT, HB_GRADER_TIMEOUT (seconds).
# Standard input: one line, the Anthropic API key (may be empty). It is held in a shell variable and
# given to the agent process only: never to the daemon or the grader, never to a file.
#
# Outputs, under /trial/out (run_trial.sh copies them to the host):
#   transcript.jsonl  the agent's stdout (Claude Code stream-json)
#   result.json       the last `"type":"result"` line of the transcript
#   agent.stderr, grade.json, grade.stderr, timing.json, dockerd.log, agent/ (files the agent wrote),
#   claude-projects/ (Claude Code's own session logs)
set -uo pipefail
OUT=/trial/out
log() { printf '[trial %s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }
now() { date +%s.%N; }

HB_API_KEY=""
IFS= read -r -t 10 HB_API_KEY || true
exec </dev/null

# 1. The trial's own Docker daemon. Its storage is the container's anonymous volume.
log "starting the inner Docker daemon"
dind dockerd --host=unix:///var/run/docker.sock >"$OUT/dockerd.log" 2>&1 &
for _ in $(seq 1 60); do docker info >/dev/null 2>&1 && break; sleep 1; done
if ! docker info >/dev/null 2>&1; then log "the inner Docker daemon did not start"; exit 90; fi
log "inner daemon ready: $(docker version --format '{{.Server.Version}} {{.Server.Arch}}')"

# 2. The agent, as user `agent`, in the repository.
mkdir -p "$OUT/agent" /home/agent/.claude
chown -R agent:agent /trial/repo "$OUT/agent" /home/agent
AGENT=/opt/hb/claude-agent.sh
[ -f /trial/agent.sh ] && { chmod 0755 /trial/agent.sh; AGENT=/trial/agent.sh; log "agent command replaced by /trial/agent.sh"; }

agent_env=(PATH=/home/agent/.local/bin:/usr/local/bin:/usr/bin:/bin HOME=/home/agent USER=agent
  TERM=dumb LANG=C.UTF-8 DISABLE_AUTOUPDATER=1 HB_OUTPUTS="$OUT/agent"
  HB_MODEL="${HB_MODEL:-}" HB_PERMISSION_MODE="${HB_PERMISSION_MODE:-auto}")
[ -n "$HB_API_KEY" ] && agent_env+=(ANTHROPIC_API_KEY="$HB_API_KEY")

log "agent start (model ${HB_MODEL:-unset}, timeout ${HB_AGENT_TIMEOUT:-3600}s)"
t0=$(now)
(cd /trial/repo && env -i "${agent_env[@]}" timeout --kill-after=30 "${HB_AGENT_TIMEOUT:-3600}" \
   setpriv --reuid=agent --regid=agent --init-groups "$AGENT") \
  >"$OUT/transcript.jsonl" 2>"$OUT/agent.stderr"
agent_rc=$?
t1=$(now)
HB_API_KEY=""; unset agent_env
log "agent exit $agent_rc"

# 3. Nothing the agent started may serve the grader: kill every process of user `agent`.
stray=$(pgrep -u agent | wc -l)
pkill -KILL -u agent 2>/dev/null; sleep 1
log "killed $stray leftover agent processes"

jq -c 'select(.type? == "result")' "$OUT/transcript.jsonl" 2>/dev/null | tail -n 1 >"$OUT/result.json"
[ -s "$OUT/result.json" ] || echo '{}' >"$OUT/result.json"
[ -d /home/agent/.claude/projects ] && cp -r /home/agent/.claude/projects "$OUT/claude-projects"

log "agent phase done; waiting for the grader"
for _ in $(seq 1 300); do [ -f /trial/grader-ready ] && break; sleep 1; done
if [ ! -f /trial/grader-ready ]; then log "the grader was not delivered"; exit 91; fi

# 4. The grader, as root, with the inner daemon (and anything the agent left in it) still up.
t1=$(now)
log "grader start (timeout ${HB_GRADER_TIMEOUT:-900}s)"
(cd /trial/repo && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/root LANG=C.UTF-8 \
   timeout --kill-after=30 "${HB_GRADER_TIMEOUT:-900}" /trial/grader /trial/repo) \
  >"$OUT/grade.json" 2>"$OUT/grade.stderr"
grade_rc=$?
t2=$(now)
log "grader exit $grade_rc"

python3 - "$t0" "$t1" "$t2" "$agent_rc" "$grade_rc" "$stray" >"$OUT/timing.json" <<'PY'
import json, sys
t0, t1, t2 = map(float, sys.argv[1:4])
print(json.dumps({"agent_seconds": round(t1 - t0, 1), "grader_seconds": round(t2 - t1, 1),
                  "agent_exit": int(sys.argv[4]), "grader_exit": int(sys.argv[5]),
                  "leftover_agent_processes_killed": int(sys.argv[6])}))
PY
exit 0
