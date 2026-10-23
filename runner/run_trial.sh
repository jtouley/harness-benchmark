#!/usr/bin/env bash
# Run one trial in one disposable container with its own Docker daemon, then copy the outputs to the
# host and delete the container and its volume. Nothing else is left on the host.
#
# Usage:
#   runner/run_trial.sh --repo DIR --prompt FILE --grader FILE --out DIR
#                       [--model ID] [--plugin-dir DIR] [--suffix TEXT] [--permission-mode MODE]
#                       [--agent-timeout SEC | --agent-backstop SEC [--max-budget-usd USD]]
#                       [--grader-timeout SEC] [--image IMAGE] [--name NAME]
#                       [--agent-cmd FILE] [--replay FILE [--replay-seed N]] [--grader-arg ARG]...
#                       [--auth key | --auth proxy --ca FILE [--relay-port PORT]]
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
#                  positive value is refused; without it, 0 is refused
#   --agent-backstop  harness arms only, and required for them: seconds after which the session is stopped
#                  as a runaway (criteria v2 section 5.3, the backstop)
#   --max-budget-usd  harness arms only: Claude Code's own spend limit for the session (its --max-budget-usd)
#   --agent-cmd    replaces Claude Code with this script (tests only; it runs as the agent would)
#   --auth         how the agent reaches the API. `key` (default): ANTHROPIC_API_KEY, below. `proxy`: a host
#                  whose outbound traffic goes through a local HTTPS proxy that adds the credentials
#                  (HTTPS_PROXY=http://HOST:PORT, no user or password in it). No key is sent. The runner
#                  starts runner/proxy_relay.py on the Docker bridge's gateway at --relay-port (default
#                  3129); the agent gets HTTPS_PROXY=http://<gateway>:<port>, ANTHROPIC_BASE_URL (if set
#                  here) and --ca as NODE_EXTRA_CA_CERTS. Before the trial container is created, a probe
#                  container must reach the relay and nothing else (no other port of the host, no address
#                  outside; runner/net_guard.sh sets the host's firewall so), or the runner exits 2.
#   --ca           the proxy's CA certificate (PEM), copied into the container (--auth proxy only)
#
# ANTHROPIC_API_KEY is read from this process's environment and written to the container's standard
# input (a shell builtin, so it is in no process's arguments). It is not in the container's
# configuration, the image, a file or a log. The agent holds it in its environment and can print it, so
# after the outputs are copied every file in --out is scanned and each copy of the key is replaced by
# [REDACTED:ANTHROPIC_API_KEY]. The scan reads the key from the environment and never prints it.
set -euo pipefail

usage() { sed -n '2,35p' "$0" | sed 's/^# \{0,1\}//'; }
die() { printf 'run_trial: %s\n' "$*" >&2; exit 2; }

IMAGE="${HB_RUNNER_IMAGE:-harness-benchmark/runner:local}"
MODEL=claude-opus-5-5 PLUGIN="" SUFFIX="" REPO="" PROMPT="" GRADER="" OUT="" AGENT_CMD=""
PERMISSION_MODE=auto AGENT_TIMEOUT="" AGENT_BACKSTOP="" MAX_BUDGET_USD="" GRADER_TIMEOUT=900 REPLAY="" REPLAY_SEED=0
AUTH=key CA="" RELAY_PORT=3129
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
    --agent-backstop) AGENT_BACKSTOP="${2:?}"; shift 2 ;;
    --max-budget-usd) MAX_BUDGET_USD="${2:?}"; shift 2 ;;
    --grader-timeout) GRADER_TIMEOUT="${2:?}"; shift 2 ;;
    --image) IMAGE="${2:?}"; shift 2 ;;
    --name) NAME="${2:?}"; shift 2 ;;
    --agent-cmd) AGENT_CMD="${2:?}"; shift 2 ;;
    --replay) REPLAY="${2:?}"; shift 2 ;;
    --replay-seed) REPLAY_SEED="${2:?}"; shift 2 ;;
    --grader-arg) GRADER_ARGS+=("${2?}"); shift 2 ;;
    --auth) AUTH="${2:?}"; shift 2 ;;
    --ca) CA="${2:?}"; shift 2 ;;
    --relay-port) RELAY_PORT="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; die "unknown argument: $1" ;;
  esac
done

[ -d "$REPO" ] || die "--repo must be a directory"
[ -f "$PROMPT" ] || die "--prompt must be a file"
[ -f "$GRADER" ] && [ -x "$GRADER" ] || die "--grader must be an executable file"
[ -n "$OUT" ] || die "--out is required"
[ -z "$PLUGIN" ] || [ -d "$PLUGIN" ] || die "--plugin-dir must be a directory"
# An empty plugin is not loaded (claude-agent.sh), so it would be a one-shot that the rules below leave uncapped.
[ -z "$PLUGIN" ] || [ -n "$(ls -A "$PLUGIN")" ] || die "--plugin-dir is empty"
[ -z "$AGENT_CMD" ] || [ -f "$AGENT_CMD" ] || die "--agent-cmd must be a file"
[ -z "$REPLAY" ] || [ -f "$REPLAY" ] || die "--replay must be a file"
case "$REPLAY_SEED" in ''|*[!0-9]*) die "--replay-seed must be a number" ;; esac
[ -n "$AGENT_TIMEOUT" ] || AGENT_TIMEOUT=$([ -n "$PLUGIN" ] && echo 0 || echo 3600)
case "$AGENT_TIMEOUT" in *[!0-9]*) die "--agent-timeout must be a whole number of seconds" ;; esac
[ -z "$PLUGIN" ] || [ "$AGENT_TIMEOUT" -eq 0 ] ||
  die "--agent-timeout is a one-shot guard cap; a harness arm (--plugin-dir) has no guard cap, only --agent-backstop (criteria v2 section 5.3)"
[ -n "$PLUGIN" ] || [ "$AGENT_TIMEOUT" -gt 0 ] ||
  die "--agent-timeout 0 is for a harness arm; a one-shot keeps a guard cap (criteria v2 section 5.3)"
# A harness arm always has a backstop, chosen by the caller (criteria v2 section 5.3; the pipeline trials
# take it from runner/pipeline/caps.json). A one-shot has none.
[ -n "$AGENT_BACKSTOP" ] || [ -n "$PLUGIN" ] || AGENT_BACKSTOP=0
[ -n "$AGENT_BACKSTOP" ] || die "--agent-backstop is required for a harness arm (--plugin-dir)"
case "$AGENT_BACKSTOP" in *[!0-9]*) die "--agent-backstop must be a whole number of seconds" ;; esac
[ -z "$MAX_BUDGET_USD" ] || [[ "$MAX_BUDGET_USD" =~ ^[0-9]+(\.[0-9]+)?$ ]] || die "--max-budget-usd must be a number"
AGENT_TIMEOUT=$((10#$AGENT_TIMEOUT)) AGENT_BACKSTOP=$((10#$AGENT_BACKSTOP))  # 00 is 0 (entrypoint compares numbers)
[ -z "$PLUGIN" ] || [ "$AGENT_BACKSTOP" -gt 0 ] || die "--agent-backstop 0: a harness arm always has a backstop"
[ -n "$PLUGIN" ] || { [ "$AGENT_BACKSTOP" -eq 0 ] && [ -z "$MAX_BUDGET_USD" ]; } ||
  die "--agent-backstop and --max-budget-usd are for a harness arm (--plugin-dir); a one-shot has its guard cap"
case "$AUTH" in key|proxy) ;; *) die "--auth must be key or proxy" ;; esac
case "$RELAY_PORT" in ''|*[!0-9]*) die "--relay-port must be a number" ;; esac
UPSTREAM=""
if [ "$AUTH" = proxy ]; then
  [ -f "$CA" ] || die "--auth proxy needs --ca, the proxy's CA certificate"
  proxy_url="${HTTPS_PROXY:-${https_proxy:-}}"
  [ -n "$proxy_url" ] || die "--auth proxy needs HTTPS_PROXY (http://HOST:PORT)"
  # Never printed: a URL with a user or password in it would put a credential in the error output.
  [[ "$proxy_url" =~ ^http://([A-Za-z0-9.-]+):([0-9]+)/?$ ]] ||
    die "--auth proxy takes HTTPS_PROXY as http://HOST:PORT only (no user, password or path); not started"
  UPSTREAM="${BASH_REMATCH[1]}:${BASH_REMATCH[2]}"
  unset proxy_url
  # No key goes in with --auth proxy: it would be one more credential in the container.
  unset ANTHROPIC_API_KEY
else
  [ -z "$CA" ] || die "--ca is for --auth proxy"
fi
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
RELAY_PID=""
cleanup() {
  docker rm -f -v "$NAME" >/dev/null 2>&1 || true
  [ -z "$RELAY_PID" ] || kill "$RELAY_PID" 2>/dev/null || true
  rm -rf "$STAGE"
  # An interrupted trial still leaves runner.log in $OUT.
  [ -n "$REDACTED_FILES" ] || redact_key >/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM

{ cat "$PROMPT"; [ -z "$SUFFIX" ] || printf ' %s' "$SUFFIX"; } >"$STAGE/prompt.txt"
: >"$STAGE/grader-args"
[ ${#GRADER_ARGS[@]} -eq 0 ] || printf '%s\n' "${GRADER_ARGS[@]}" >"$STAGE/grader-args"

# --auth proxy: the relay, then a probe from the trial network. It must reach the relay and nothing else.
PROXY_ENV=()
if [ "$AUTH" = proxy ]; then
  GATEWAY=$(docker network inspect bridge --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}')
  [ -n "$GATEWAY" ] || die "--auth proxy: the Docker bridge has no gateway address"
  python3 "$(dirname "$0")/proxy_relay.py" --listen "$GATEWAY:$RELAY_PORT" --upstream "$UPSTREAM" \
    >"$STAGE/relay.log" 2>&1 &
  RELAY_PID=$!
  for _ in $(seq 1 50); do grep -q listening "$STAGE/relay.log" && break; sleep 0.1; done
  grep -q listening "$STAGE/relay.log" || die "--auth proxy: the relay did not start: $(cat "$STAGE/relay.log")"
  host_ports=$(python3 "$(dirname "$0")/proxy_relay.py" --host-ports "$GATEWAY" --except "$RELAY_PORT")
  # shellcheck disable=SC2086  # one argument per port
  probe=$(docker run --rm --label hb.runner=probe --entrypoint bash "$IMAGE" -c '
    gw=$1 relay=$2; shift 2
    reach() { timeout 3 bash -c "exec 3<>/dev/tcp/$1/$2" 2>/dev/null; }
    reach "$gw" "$relay" || echo "the relay is unreachable"
    for p in "$@"; do reach "$gw" "$p" && echo "host port $p is open"; done
    reach 1.1.1.1 443 && echo "1.1.1.1:443 outside is open"
    exit 0' probe "$GATEWAY" "$RELAY_PORT" $host_ports 2>&1) ||
    die "--auth proxy: the network probe did not run: $probe"
  [ -z "$probe" ] ||
    die "--auth proxy: the trial network is not closed: $(echo $probe). Run runner/net_guard.sh $RELAY_PORT as root"
  PROXY_ENV=(-e HB_PROXY="http://$GATEWAY:$RELAY_PORT")
  [ -z "${ANTHROPIC_BASE_URL:-}" ] || PROXY_ENV+=(-e ANTHROPIC_BASE_URL="$ANTHROPIC_BASE_URL")
fi

# The container has no bind mount and no published port: inputs go in and outputs come out by copy.
docker create --name "$NAME" --label hb.runner=trial --privileged --interactive "${PROXY_ENV[@]}" \
  -e HB_MODEL="$MODEL" -e HB_PERMISSION_MODE="$PERMISSION_MODE" \
  -e HB_AGENT_TIMEOUT="$AGENT_TIMEOUT" -e HB_AGENT_BACKSTOP="$AGENT_BACKSTOP" -e HB_MAX_BUDGET_USD="$MAX_BUDGET_USD" \
  -e HB_GRADER_TIMEOUT="$GRADER_TIMEOUT" -e HB_REPLAY_SEED="$REPLAY_SEED" \
  "$IMAGE" >/dev/null
docker cp -q "$REPO/." "$NAME:/trial/repo"
docker cp -q "$STAGE/prompt.txt" "$NAME:/trial/prompt.txt"
docker cp -q "$STAGE/grader-args" "$NAME:/trial/grader-args"
# Into a root-only directory (mode 0700 in the image): the agent can reach the service, not its files.
[ -z "$REPLAY" ] || docker cp -q "$REPLAY" "$NAME:/opt/hb-replay/replay.pyz"
[ -z "$PLUGIN" ] || docker cp -q "$PLUGIN/." "$NAME:/trial/plugin"
[ -z "$AGENT_CMD" ] || docker cp -q "$AGENT_CMD" "$NAME:/trial/agent.sh"
[ -z "$CA" ] || docker cp -q "$CA" "$NAME:/trial/ca.crt"

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
image_id=$(docker inspect --format '{{.Image}}' "$NAME" 2>/dev/null || true)
python3 - "$t0" "$t1" "$rc" "$NAME" "$REDACTED_FILES" "$image_id" "$AUTH" >"$OUT/host.json" <<'PY'
import json, sys
t0, t1 = float(sys.argv[1]), float(sys.argv[2])
print(json.dumps({"container": sys.argv[4], "container_exit": int(sys.argv[3]),
                  "container_seconds": round(t1 - t0, 1),
                  "api_key_redacted_files": int(sys.argv[5]), "image": sys.argv[6], "auth": sys.argv[7]}))
PY
echo "run_trial: $NAME exit $rc; outputs in $OUT" >&2
exit "$rc"
