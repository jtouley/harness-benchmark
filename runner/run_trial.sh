#!/usr/bin/env bash
# Run one trial in one disposable container with its own Docker daemon, then copy the outputs to the
# host and delete the container and its volume. Nothing else is left on the host.
#
# Usage:
#   runner/run_trial.sh --repo DIR --prompt FILE --grader FILE --out DIR
#                       [--model ID] [--plugin-dir DIR] [--suffix TEXT] [--permission-mode MODE]
#                       [--agent-timeout SEC] [--grader-timeout SEC] [--image IMAGE] [--name NAME]
#                       [--agent-cmd FILE] [--replay FILE [--replay-seed N]] [--grader-arg ARG]...
#
#   --repo         task repository; copied into the container (the host copy is not changed)
#   --prompt       task prompt; the arm's --suffix is appended after one space
#   --grader       executable, copied in after the agent has finished and run as root as
#                  `grader /trial/repo [ARG...]` from a root-only directory; its stdout is grade.json
#   --grader-arg   one more argument for the grader (repeatable)
#   --replay       a dev service (replay.pyz) started as root before the agent from a root-only
#                  directory, on localhost:8099 with --seed N (--replay-seed, default 0); stopped
#                  before the grader runs
#   --out          output directory on the host; must not exist or be empty
#   --plugin-dir   the arm's Claude Code plugin (passed as `claude --plugin-dir`); an arm with a plugin is a
#                  harness arm
#   --agent-timeout  the one-shot guard cap in seconds (default 3600). A harness arm has no time cap
#                  (criteria v2 section 5.3): with --plugin-dir the default is 0, which means none, and a
#                  positive value is refused
#   --agent-cmd    replaces Claude Code with this script (tests only; it runs as the agent would)
#
# ANTHROPIC_API_KEY is read from this process's environment and written to the container's standard
# input (a shell builtin, so it is in no process's arguments). It is not in the container's
# configuration, the image, a file or a log. The agent holds it in its environment and can print it, so
# after the outputs are copied every file in --out is scanned and each copy of the key is replaced by
# [REDACTED:ANTHROPIC_API_KEY]. The scan reads the key from the environment and never prints it.
set -euo pipefail

usage() { sed -n '2,31p' "$0" | sed 's/^# \{0,1\}//'; }
die() { printf 'run_trial: %s\n' "$*" >&2; exit 2; }

IMAGE="${HB_RUNNER_IMAGE:-harness-benchmark/runner:local}"
MODEL=claude-opus-5-5 PLUGIN="" SUFFIX="" REPO="" PROMPT="" GRADER="" OUT="" AGENT_CMD=""
PERMISSION_MODE=auto AGENT_TIMEOUT="" GRADER_TIMEOUT=900 REPLAY="" REPLAY_SEED=0
GRADER_ARGS=()
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
    --replay) REPLAY="${2:?}"; shift 2 ;;
    --replay-seed) REPLAY_SEED="${2:?}"; shift 2 ;;
    --grader-arg) GRADER_ARGS+=("${2?}"); shift 2 ;;
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
[ -z "$REPLAY" ] || [ -f "$REPLAY" ] || die "--replay must be a file"
case "$REPLAY_SEED" in ''|*[!0-9]*) die "--replay-seed must be a number" ;; esac
[ -n "$AGENT_TIMEOUT" ] || AGENT_TIMEOUT=$([ -n "$PLUGIN" ] && echo 0 || echo 3600)
case "$AGENT_TIMEOUT" in *[!0-9]*) die "--agent-timeout must be a whole number of seconds" ;; esac
[ -z "$PLUGIN" ] || [ "$AGENT_TIMEOUT" -eq 0 ] ||
  die "--agent-timeout is a one-shot guard cap; a harness arm (--plugin-dir) has no time cap (criteria v2 section 5.3)"
if [ -e "$OUT" ] && [ -n "$(ls -A "$OUT")" ]; then die "--out exists and is not empty: $OUT"; fi
mkdir -p "$OUT"

# Replace the API key in every regular file under $OUT and print how many files held it. Symbolic links
# are not followed (the agent made them; they can point at host files outside $OUT). Exit 1 if a file
# cannot be scanned.
redact_key() {
  [ -n "${ANTHROPIC_API_KEY:-}" ] || { echo 0; return 0; }
  python3 - "$OUT" <<'PY'
import os, stat, sys
key = os.environ["ANTHROPIC_API_KEY"].encode()
mark = b"[REDACTED:ANTHROPIC_API_KEY]"
redacted, failed = 0, False
for root, _dirs, files in os.walk(sys.argv[1]):
    for name in files:
        path = os.path.join(root, name)
        try:
            mode = os.lstat(path).st_mode
            if not stat.S_ISREG(mode):
                continue
            with open(path, "rb") as f:
                data = f.read()
            if key in data:
                os.chmod(path, stat.S_IMODE(mode) | stat.S_IWUSR)
                with open(path, "wb") as f:
                    f.write(data.replace(key, mark))
                redacted += 1
        except OSError as e:
            print(f"run_trial: cannot scan {path} for the API key: {e.strerror}", file=sys.stderr)
            failed = True
print(redacted)
sys.exit(1 if failed else 0)
PY
}

STAGE="$(mktemp -d)"
REDACTED_FILES=""
cleanup() {
  docker rm -f -v "$NAME" >/dev/null 2>&1 || true
  rm -rf "$STAGE"
  # An interrupted trial still leaves runner.log in $OUT.
  [ -n "$REDACTED_FILES" ] || redact_key >/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM

{ cat "$PROMPT"; [ -z "$SUFFIX" ] || printf ' %s' "$SUFFIX"; } >"$STAGE/prompt.txt"
: >"$STAGE/grader-args"
[ ${#GRADER_ARGS[@]} -eq 0 ] || printf '%s\n' "${GRADER_ARGS[@]}" >"$STAGE/grader-args"

# The container has no bind mount and no published port: inputs go in and outputs come out by copy.
docker create --name "$NAME" --label hb.runner=trial --privileged --interactive \
  -e HB_MODEL="$MODEL" -e HB_PERMISSION_MODE="$PERMISSION_MODE" \
  -e HB_AGENT_TIMEOUT="$AGENT_TIMEOUT" -e HB_GRADER_TIMEOUT="$GRADER_TIMEOUT" -e HB_REPLAY_SEED="$REPLAY_SEED" \
  "$IMAGE" >/dev/null
docker cp -q "$REPO/." "$NAME:/trial/repo"
docker cp -q "$STAGE/prompt.txt" "$NAME:/trial/prompt.txt"
docker cp -q "$STAGE/grader-args" "$NAME:/trial/grader-args"
# Into a root-only directory (mode 0700 in the image): the agent can reach the service, not its files.
[ -z "$REPLAY" ] || docker cp -q "$REPLAY" "$NAME:/opt/hb-replay/replay.pyz"
[ -z "$PLUGIN" ] || docker cp -q "$PLUGIN/." "$NAME:/trial/plugin"
[ -z "$AGENT_CMD" ] || docker cp -q "$AGENT_CMD" "$NAME:/trial/agent.sh"

t0=$(python3 -c 'import time; print(time.time())')
# In the background, so that INT or TERM runs the cleanup at once.
printf '%s\n' "${ANTHROPIC_API_KEY:-}" | docker start --attach --interactive "$NAME" >"$OUT/runner.log" 2>&1 &
attach=$!
# The grader goes in only after every agent process is dead, so the agent cannot read it.
while kill -0 "$attach" 2>/dev/null; do
  if grep -q 'waiting for the grader' "$OUT/runner.log"; then
    # Root-only directory: the candidate's make, run by the grader as the agent user, cannot read it.
    docker cp -q "$GRADER" "$NAME:/opt/hb-grader/grader"
    docker exec "$NAME" touch /trial/grader-ready
    break
  fi
  sleep 1
done
wait "$attach" || true
t1=$(python3 -c 'import time; print(time.time())')
rc=$(docker inspect --format '{{.State.ExitCode}}' "$NAME")

docker cp -q "$NAME:/trial/out/." "$OUT/"
if ! REDACTED_FILES=$(redact_key); then
  REDACTED_FILES=failed
  echo "run_trial: the outputs could not all be scanned for the API key; do not publish $OUT" >&2
  exit 3
fi
[ "$REDACTED_FILES" = 0 ] || echo "run_trial: the API key was in $REDACTED_FILES output file(s); redacted" >&2
python3 - "$t0" "$t1" "$rc" "$NAME" "$REDACTED_FILES" >"$OUT/host.json" <<'PY'
import json, sys
t0, t1 = float(sys.argv[1]), float(sys.argv[2])
print(json.dumps({"container": sys.argv[4], "container_exit": int(sys.argv[3]),
                  "container_seconds": round(t1 - t0, 1),
                  "api_key_redacted_files": int(sys.argv[5])}))
PY
echo "run_trial: $NAME exit $rc; outputs in $OUT" >&2
exit "$rc"
