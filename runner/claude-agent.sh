#!/usr/bin/env bash
# The default agent: Claude Code, headless. Runs as user `agent` in /trial/repo; stdout is the transcript.
set -uo pipefail
args=(-p "$(cat /trial/prompt.txt)" --model "${HB_MODEL:?HB_MODEL is required}"
  --permission-mode "${HB_PERMISSION_MODE:-auto}" --add-dir "$HB_OUTPUTS"
  --output-format stream-json --verbose)
if [ -n "$(ls -A /trial/plugin 2>/dev/null)" ]; then args+=(--plugin-dir /trial/plugin); fi
exec claude "${args[@]}"
