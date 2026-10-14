#!/usr/bin/env bash
# Stub agent for the runner tests: spends no API money. Like an agent, it starts a service in the
# trial's Docker daemon, leaves a background process running, commits a change and prints a transcript.
set -euo pipefail
tag="$(cat TAG)"
docker run -d --name svc busybox:1.37 sh -c \
  "mkdir -p /srv/hbmarker-$tag && echo served-$tag > /srv/hbmarker-$tag/index.html && exec httpd -f -p 8080 -h /srv/hbmarker-$tag" >/dev/null
nohup bash -c "exec -a hb-stray-$tag sleep 3000" >/dev/null 2>&1 &
echo answer >answer.txt
git -c user.email=stub@local -c user.name=stub add answer.txt
git -c user.email=stub@local -c user.name=stub commit -qm "stub change"
echo "stub summary" >"$HB_OUTPUTS/summary.md"
# Hold until the test releases the trial (it inspects the running container meanwhile).
if [ -f HOLD ]; then for _ in $(seq 1 180); do [ -f /tmp/release ] && break; sleep 1; done; fi
grader_visible=false; [ -e /trial/grader ] && grader_visible=true
key_sha=$(printf '%s' "${ANTHROPIC_API_KEY:-}" | sha256sum | cut -d' ' -f1)
echo '{"type":"system","subtype":"init"}'
printf '{"type":"result","subtype":"success","is_error":false,"model":"%s","key_sha256":"%s","prompt_sha256":"%s","grader_visible":%s}\n' \
  "$HB_MODEL" "$key_sha" "$(sha256sum </trial/prompt.txt | cut -d' ' -f1)" "$grader_visible"
