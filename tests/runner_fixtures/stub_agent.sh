#!/usr/bin/env bash
# Stub agent for the runner tests: spends no API money. Like an agent, it starts a service in the
# trial's Docker daemon, leaves a background process running, commits a change and prints a transcript.
# It also does what a careless agent does: it prints its (fake) API key into the transcript and into a
# session log, and writes one line that is not JSON.
set -euo pipefail
t_start=$(date +%s.%N)
tag="$(cat TAG)"
# The service runs as uid 1000, the uid of user `agent`: the kill step must not touch it.
docker run -d --name svc --user 1000 busybox:1.37 sh -c \
  "mkdir -p /tmp/hbmarker-$tag && echo served-$tag > /tmp/hbmarker-$tag/index.html && exec httpd -f -p 8080 -h /tmp/hbmarker-$tag" >/dev/null
nohup bash -c "exec -a hb-stray-$tag sleep 3000" >/dev/null 2>&1 &
echo answer >answer.txt
git -c user.email=stub@local -c user.name=stub add answer.txt
git -c user.email=stub@local -c user.name=stub commit -qm "stub change"
echo "stub summary" >"$HB_OUTPUTS/summary.md"
mkdir -p "$HOME/.claude/projects/stub"
printf 'session %s\n' "${ANTHROPIC_API_KEY:-}" >"$HOME/.claude/projects/stub/session.jsonl"
# Hold until the test releases the trial (it inspects the running container meanwhile).
if [ -f HOLD ]; then for _ in $(seq 1 180); do [ -f /tmp/release ] && break; sleep 1; done; fi
grader_visible=false; [ -e /trial/grader ] && grader_visible=true
key_sha=$(printf '%s' "${ANTHROPIC_API_KEY:-}" | sha256sum | cut -d' ' -f1)
env_names=$(compgen -e | sort | jq -Rsc 'split("\n") | map(select(. != ""))')
echo '{"type":"system","subtype":"init"}'
printf '{"type":"assistant","printed_env":"ANTHROPIC_API_KEY=%s"}\n' "${ANTHROPIC_API_KEY:-}"
echo 'not json: a tool printed this'
t_end=$(date +%s.%N)
printf '{"type":"result","subtype":"success","is_error":false,"model":"%s","key_sha256":"%s","prompt_sha256":"%s","grader_visible":%s,"env_names":%s,"stub_seconds":%s}\n' \
  "$HB_MODEL" "$key_sha" "$(sha256sum </trial/prompt.txt | cut -d' ' -f1)" "$grader_visible" \
  "$env_names" "$(python3 -c "print(round($t_end - $t_start, 3))")"
