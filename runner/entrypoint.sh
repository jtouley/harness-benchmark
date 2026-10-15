#!/usr/bin/env bash
# Runs one trial inside the trial container (PID 1 is tini; this script is its only child).
#
# Inputs, copied in by run_trial.sh before the container starts:
#   /trial/repo/        the task repository (the agent's working directory)
#   /trial/prompt.txt   the full prompt (task prompt plus the arm's suffix)
#   /trial/plugin/      the arm's Claude Code plugin (empty: no plugin)
#   /trial/agent.sh     optional; replaces the Claude Code agent (tests use a stub here)
#   /trial/grader-args  the grader's extra arguments, one per line (may be empty)
#   /opt/hb-replay/replay.pyz  optional dev service (root-only directory): started as root before the
#                       agent on localhost:8099 with --seed HB_REPLAY_SEED, stopped after the agent
# From the image: /opt/hb/toolchain.env (optional), NAME=VALUE lines: the task toolchain's variables
# (PATH, caches, offline switches), given to the agent and to the grader.
# The grader arrives later: run_trial.sh copies it to /opt/hb-grader/grader (a root-only directory) once
# this script logs "waiting for the grader" (after every agent process is dead), then creates
# /trial/grader-ready. It runs as root as `grader /trial/repo [ARG...]` and prints the grade JSON on
# stdout. While it runs, processes of user `agent` (the candidate's make, when the grader drops to that
# user) have no network beyond loopback.
# Environment: HB_MODEL, HB_PERMISSION_MODE, HB_AGENT_TIMEOUT, HB_GRADER_TIMEOUT (seconds), HB_REPLAY_SEED.
# Standard input: one line, the Anthropic API key (may be empty). It is held in a shell variable and
# given to the agent process only: never to the daemon or the grader, never to a file.
#
# Outputs, under /trial/out (run_trial.sh copies them to the host):
#   transcript.jsonl  the agent's stdout (Claude Code stream-json)
#   result.json       the last `"type":"result"` line of the transcript
#   repo/ (the working tree the agent left, without .git, environments and build outputs),
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

# The task toolchain's variables, if the image has any (validated NAME=VALUE lines).
toolchain=()
if [ -f /opt/hb/toolchain.env ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in ''|'#'*) continue ;; esac
    [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] || { log "bad line in /opt/hb/toolchain.env"; exit 93; }
    toolchain+=("$line")
  done </opt/hb/toolchain.env
  log "toolchain environment: ${#toolchain[@]} variables"
fi
toolchain_path=/usr/local/bin:/usr/bin:/bin
for v in "${toolchain[@]}"; do [ "${v%%=*}" = PATH ] && toolchain_path="${v#PATH=}"; done

# 1b. The dev service, as root from a root-only directory, so the agent can use it but not read it.
replay_pid=""
port_open() { (exec 3<>/dev/tcp/127.0.0.1/8099) 2>/dev/null; }
if [ -f /opt/hb-replay/replay.pyz ]; then
  if port_open; then log "port 8099 is taken before the dev replay starts"; exit 92; fi
  /usr/bin/python3 /opt/hb-replay/replay.pyz --seed "${HB_REPLAY_SEED:-0}" --port 8099 \
    >"$OUT/replay-dev.log" 2>&1 &
  replay_pid=$!
  for _ in $(seq 1 60); do port_open && break; sleep 1; done
  if ! port_open; then log "the dev replay did not start"; exit 92; fi
  log "dev replay ready on localhost:8099 (seed ${HB_REPLAY_SEED:-0})"
fi

# 2. The agent, as user `agent`, in the repository.
mkdir -p "$OUT/agent" /home/agent/.claude
chown -R agent:agent /trial/repo "$OUT/agent" /home/agent
AGENT=/opt/hb/claude-agent.sh
[ -f /trial/agent.sh ] && { chmod 0755 /trial/agent.sh; AGENT=/trial/agent.sh; log "agent command replaced by /trial/agent.sh"; }

agent_timeout="${HB_AGENT_TIMEOUT:-3600}"
agent_vars=(PATH=/home/agent/.local/bin:/usr/local/bin:/usr/bin:/bin "${toolchain[@]}" HOME=/home/agent
  USER=agent TERM=dumb LANG=C.UTF-8 DISABLE_AUTOUPDATER=1 HB_OUTPUTS="$OUT/agent"
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

# The dev service stops before the grader, which serves the grading seed on the same port.
if [ -n "$replay_pid" ]; then
  kill "$replay_pid" 2>/dev/null; wait "$replay_pid" 2>/dev/null
  for _ in $(seq 1 30); do port_open || break; sleep 1; done
  if port_open; then log "the dev replay did not stop"; else log "dev replay stopped"; fi
fi

# The working tree the agent left, for audit and regrading: plain files (no .git, whose objects are
# compressed and would hide a key from the redaction scan), without environments and build outputs.
mkdir -p "$OUT/repo"
tar -C /trial/repo --exclude=./.git --exclude=./.venv --exclude=./out --exclude=./lake --exclude=./target \
  --exclude=./project/target --exclude=./project/project --exclude=./node_modules -cf - . 2>/dev/null \
  | tar -C "$OUT/repo" -xf - 2>/dev/null

# A non-JSON line (a tool that wrote to stdout) must not hide the result line.
jq -cR 'fromjson? | select(.type? == "result")' "$OUT/transcript.jsonl" 2>/dev/null | tail -n 1 >"$OUT/result.json"
[ -s "$OUT/result.json" ] || echo '{}' >"$OUT/result.json"
[ -d /home/agent/.claude/projects ] && cp -r /home/agent/.claude/projects "$OUT/claude-projects"

log "agent phase done; waiting for the grader"
for _ in $(seq 1 300); do [ -f /trial/grader-ready ] && break; sleep 1; done
if [ ! -f /trial/grader-ready ]; then log "the grader was not delivered"; exit 91; fi

# 4. The grader, as root, with the inner daemon (and anything the agent left in it) still up. Processes
# of user `agent` (the candidate's make, when the grader runs it as that user) get no network beyond
# loopback: the build uses the image's toolchain, not package indexes.
agent_network=open
if iptables -I OUTPUT 1 -m owner --uid-owner agent ! -o lo -j REJECT 2>>"$OUT/runner-iptables.log" \
   && ip6tables -I OUTPUT 1 -m owner --uid-owner agent ! -o lo -j REJECT 2>>"$OUT/runner-iptables.log"; then
  agent_network=blocked
fi
log "network of user agent during grading: $agent_network"
grader_args=()
[ -f /trial/grader-args ] && mapfile -t grader_args </trial/grader-args
grader_timeout="${HB_GRADER_TIMEOUT:-900}"
t_grade_start=$(now)
log "grader start (timeout ${grader_timeout}s)"
(cd /trial/repo && env -i PATH="/opt/grader/bin:$toolchain_path" HOME=/root LANG=C.UTF-8 TZ=UTC \
   timeout --kill-after=30 "$grader_timeout" /opt/hb-grader/grader /trial/repo "${grader_args[@]}") \
  >"$OUT/grade.json" 2>"$OUT/grade.stderr"
grade_rc=$?
t2=$(now)
log "grader exit $grade_rc"
# A grader killed at its cap leaves no JSON: record why, with reward 0, instead of an empty file.
if ! { [ -s "$OUT/grade.json" ] && jq -e . "$OUT/grade.json" >/dev/null 2>&1; }; then
  reason="the grader exited $grade_rc without a JSON result"
  [ "$grade_rc" = 124 ] || [ "$grade_rc" = 137 ] && reason="the grader was killed at its cap of ${grader_timeout}s"
  [ -s "$OUT/grade.json" ] && mv "$OUT/grade.json" "$OUT/grade.raw"
  jq -n --arg e "$reason" '{error: $e, reward: 0.0}' >"$OUT/grade.json"
fi

# agent_seconds ends when the agent exits; the kill step, result extraction and the wait for the
# grader are postprocess_seconds.
python3 - "$t0" "$t_agent_end" "$t_grade_start" "$t2" "$agent_rc" "$grade_rc" "$stray" "$left" \
  "$agent_timeout" "$grader_timeout" "$agent_network" "${replay_pid:+1}" >"$OUT/timing.json" <<'PY'
import json, sys
t0, t_agent_end, t_grade_start, t2 = map(float, sys.argv[1:5])
print(json.dumps({"agent_seconds": round(t_agent_end - t0, 1),
                  "postprocess_seconds": round(t_grade_start - t_agent_end, 1),
                  "grader_seconds": round(t2 - t_grade_start, 1),
                  "agent_exit": int(sys.argv[5]), "grader_exit": int(sys.argv[6]),
                  "leftover_agent_processes_killed": int(sys.argv[7]),
                  "agent_processes_left_after_kill": int(sys.argv[8]),
                  "agent_timeout": int(sys.argv[9]), "grader_timeout": int(sys.argv[10]),
                  "agent_network_during_grading": sys.argv[11], "dev_replay": sys.argv[12] == "1"}))
PY
exit 0
