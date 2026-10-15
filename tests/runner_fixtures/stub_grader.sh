#!/usr/bin/env bash
# Stub grader for the runner tests: reports what it can see inside the trial container.
set -uo pipefail
repo="$1"
running=$(docker inspect --format '{{.State.Running}}' svc 2>/dev/null || echo false)
served=$(docker exec svc wget -qO- http://127.0.0.1:8080/index.html 2>/dev/null || true)
# Agent processes in the trial's own PID namespace (not the uid-1000 service in the inner daemon).
left=$(pgrep --ns $$ --nslist pid -u agent | wc -l)
key=false; [ -n "${ANTHROPIC_API_KEY:-}" ] && key=true
# No safe.directory override: the image must let root run git in the agent-owned repository.
commits=$(git -C "$repo" rev-list --count HEAD)
printf '{"inner_service_running": %s, "inner_service_body": "%s", "agent_processes_left": %d, "grader_sees_api_key": %s, "commits": %d}\n' \
  "$running" "$served" "$left" "$key" "$commits"
