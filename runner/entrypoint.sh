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

agent_timeout="${HB_AGENT_TIMEOUT:-3600}"
agent_vars=(PATH=/home/agent/.local/bin:/usr/local/bin:/usr/bin:/bin HOME=/home/agent USER=agent
  TERM=dumb LANG=C.UTF-8 DISABLE_AUTOUPDATER=1 HB_OUTPUTS="$OUT/agent"
  HB_MODEL="${HB_MODEL:-}" HB_PERMISSION_MODE="${HB_PERMISSION_MODE:-auto}")

log "agent start (model ${HB_MODEL:-unset}, timeout ${agent_timeout}s)"
t0=$(now)
# The subshell drops every inherited variable and exports only the agent's. `export` is a builtin, so
# the key is in the environment of the agent process and in no process's arguments.
(cd /trial/repo || exit 1
 while read -r name; do unset "$name" 2>/dev/null; done < <(compgen -e)
 export "${agent_vars[@]}"
 [ -z "$HB_API_KEY" ] || export ANTHROPIC_API_KEY="$HB_API_KEY"
 exec timeout --kill-after=30 "$agent_timeout" setpriv --reuid=agent --regid=agent --init-groups "$AGENT") \
  >"$OUT/transcript.jsonl" 2>"$OUT/agent.stderr"
agent_rc=$?
t_agent_end=$(now)
HB_API_KEY=""
log "agent exit $agent_rc"

# 3. Nothing the agent started may serve the grader: kill every process of user `agent` in this PID
# namespace. Processes in the inner daemon's containers are visible here too, and one that runs as
# uid 1000 is uid `agent`; the namespace filter keeps those (the task's services) up for the grader.
in_trial_ns=(--ns $$ --nslist pid -u agent)
stray=$(pgrep "${in_trial_ns[@]}" | wc -l)
# Repeat: a process can fork while pkill scans /proc.
for _ in $(seq 1 20); do
  pgrep "${in_trial_ns[@]}" >/dev/null || break
  pkill -KILL "${in_trial_ns[@]}" 2>/dev/null
  sleep 0.2
done
left=$(pgrep "${in_trial_ns[@]}" | wc -l)
log "killed $stray leftover agent processes; $left left"

# A non-JSON line (a tool that wrote to stdout) must not hide the result line.
jq -cR 'fromjson? | select(.type? == "result")' "$OUT/transcript.jsonl" 2>/dev/null | tail -n 1 >"$OUT/result.json"
[ -s "$OUT/result.json" ] || echo '{}' >"$OUT/result.json"
[ -d /home/agent/.claude/projects ] && cp -r /home/agent/.claude/projects "$OUT/claude-projects"

log "agent phase done; waiting for the grader"
for _ in $(seq 1 300); do [ -f /trial/grader-ready ] && break; sleep 1; done
if [ ! -f /trial/grader-ready ]; then log "the grader was not delivered"; exit 91; fi

# 4. The grader, as root, with the inner daemon (and anything the agent left in it) still up.
t_grade_start=$(now)
log "grader start (timeout ${HB_GRADER_TIMEOUT:-900}s)"
(cd /trial/repo && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/root LANG=C.UTF-8 \
   timeout --kill-after=30 "${HB_GRADER_TIMEOUT:-900}" /trial/grader /trial/repo) \
  >"$OUT/grade.json" 2>"$OUT/grade.stderr"
grade_rc=$?
t2=$(now)
log "grader exit $grade_rc"

# agent_seconds ends when the agent exits; the kill step, result extraction and the wait for the
# grader are postprocess_seconds.
python3 - "$t0" "$t_agent_end" "$t_grade_start" "$t2" "$agent_rc" "$grade_rc" "$stray" "$left" \
  >"$OUT/timing.json" <<'PY'
import json, sys
t0, t_agent_end, t_grade_start, t2 = map(float, sys.argv[1:5])
print(json.dumps({"agent_seconds": round(t_agent_end - t0, 1),
                  "postprocess_seconds": round(t_grade_start - t_agent_end, 1),
                  "grader_seconds": round(t2 - t_grade_start, 1),
                  "agent_exit": int(sys.argv[5]), "grader_exit": int(sys.argv[6]),
                  "leftover_agent_processes_killed": int(sys.argv[7]),
                  "agent_processes_left_after_kill": int(sys.argv[8])}))
PY
exit 0
