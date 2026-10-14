#!/usr/bin/env bash
# Run one trial in one disposable container with its own Docker daemon, then copy the outputs to the
# host and delete the container and its volume. Nothing else is left on the host.
#
# Usage:
#   runner/run_trial.sh --repo DIR --prompt FILE --grader FILE --out DIR
#                       [--model ID] [--plugin-dir DIR] [--suffix TEXT] [--permission-mode MODE]
#                       [--agent-timeout SEC] [--grader-timeout SEC] [--image IMAGE] [--name NAME]
#                       [--agent-cmd FILE]
#
#   --repo         task repository; copied into the container (the host copy is not changed)
#   --prompt       task prompt; the arm's --suffix is appended after one space
#   --grader       executable, copied in after the agent has finished and run as
#                  `grader /trial/repo`; its stdout is grade.json
#   --out          output directory on the host; must not exist or be empty
#   --plugin-dir   the arm's Claude Code plugin (passed as `claude --plugin-dir`)
#   --agent-cmd    replaces Claude Code with this script (tests only; it runs as the agent would)
#
# ANTHROPIC_API_KEY is read from this process's environment and written to the container's standard
# input (a shell builtin, so it is in no process's arguments). It is not in the container's
# configuration, the image, a file or a log.
set -euo pipefail

usage() { sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; }
die() { printf 'run_trial: %s\n' "$*" >&2; exit 2; }

IMAGE="${HB_RUNNER_IMAGE:-harness-benchmark/runner:local}"
MODEL=claude-opus-5-5 PLUGIN="" SUFFIX="" REPO="" PROMPT="" GRADER="" OUT="" AGENT_CMD=""
PERMISSION_MODE=auto AGENT_TIMEOUT=3600 GRADER_TIMEOUT=900
NAME="hb-trial-$(date +%Y%m%d-%H%M%S)-$$"

while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="${2:?}"; shift 2 ;;
    --prompt) PROMPT="${2:?}"; shift 2 ;;
    --grader) GRADER="${2:?}"; shift 2 ;;
    --out) OUT="${2:?}"; shift 2 ;;
    --model) MODEL="${2:?}"; shift 2 ;;
    --plugin-dir) PLUGIN="${2:?}"; shift 2 ;;
    --suffix) SUFFIX="${2-}"; shift 2 ;;
    --permission-mode) PERMISSION_MODE="${2:?}"; shift 2 ;;
    --agent-timeout) AGENT_TIMEOUT="${2:?}"; shift 2 ;;
    --grader-timeout) GRADER_TIMEOUT="${2:?}"; shift 2 ;;
    --image) IMAGE="${2:?}"; shift 2 ;;
    --name) NAME="${2:?}"; shift 2 ;;
    --agent-cmd) AGENT_CMD="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; die "unknown argument: $1" ;;
  esac
done

[ -d "$REPO" ] || die "--repo must be a directory"
[ -f "$PROMPT" ] || die "--prompt must be a file"
[ -f "$GRADER" ] && [ -x "$GRADER" ] || die "--grader must be an executable file"
[ -n "$OUT" ] || die "--out is required"
[ -z "$PLUGIN" ] || [ -d "$PLUGIN" ] || die "--plugin-dir must be a directory"
[ -z "$AGENT_CMD" ] || [ -f "$AGENT_CMD" ] || die "--agent-cmd must be a file"
if [ -e "$OUT" ] && [ -n "$(ls -A "$OUT")" ]; then die "--out exists and is not empty: $OUT"; fi
mkdir -p "$OUT"

STAGE="$(mktemp -d)"
cleanup() {
  docker rm -f -v "$NAME" >/dev/null 2>&1 || true
  rm -rf "$STAGE"
}
trap cleanup EXIT
trap 'exit 130' INT TERM

{ cat "$PROMPT"; [ -z "$SUFFIX" ] || printf ' %s' "$SUFFIX"; } >"$STAGE/prompt.txt"

# The container has no bind mount and no published port: inputs go in and outputs come out by copy.
docker create --name "$NAME" --label hb.runner=trial --privileged --interactive \
  -e HB_MODEL="$MODEL" -e HB_PERMISSION_MODE="$PERMISSION_MODE" \
  -e HB_AGENT_TIMEOUT="$AGENT_TIMEOUT" -e HB_GRADER_TIMEOUT="$GRADER_TIMEOUT" \
  "$IMAGE" >/dev/null
docker cp -q "$REPO/." "$NAME:/trial/repo"
docker cp -q "$STAGE/prompt.txt" "$NAME:/trial/prompt.txt"
[ -z "$PLUGIN" ] || docker cp -q "$PLUGIN/." "$NAME:/trial/plugin"
[ -z "$AGENT_CMD" ] || docker cp -q "$AGENT_CMD" "$NAME:/trial/agent.sh"

t0=$(python3 -c 'import time; print(time.time())')
# In the background, so that INT or TERM runs the cleanup at once.
printf '%s\n' "${ANTHROPIC_API_KEY:-}" | docker start --attach --interactive "$NAME" >"$OUT/runner.log" 2>&1 &
attach=$!
# The grader goes in only after every agent process is dead, so the agent cannot read it.
while kill -0 "$attach" 2>/dev/null; do
  if grep -q 'waiting for the grader' "$OUT/runner.log"; then
    docker cp -q "$GRADER" "$NAME:/trial/grader"
    docker exec "$NAME" touch /trial/grader-ready
    break
  fi
  sleep 1
done
wait "$attach" || true
t1=$(python3 -c 'import time; print(time.time())')
rc=$(docker inspect --format '{{.State.ExitCode}}' "$NAME")

docker cp -q "$NAME:/trial/out/." "$OUT/"
python3 - "$t0" "$t1" "$rc" "$NAME" >"$OUT/host.json" <<'PY'
import json, sys
t0, t1 = float(sys.argv[1]), float(sys.argv[2])
print(json.dumps({"container": sys.argv[4], "container_exit": int(sys.argv[3]),
                  "container_seconds": round(t1 - t0, 1)}))
PY
echo "run_trial: $NAME exit $rc; outputs in $OUT" >&2
exit "$rc"
