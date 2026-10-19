#!/usr/bin/env bash
# The default agent: Claude Code, headless. Runs as user `agent` in /trial/repo; stdout is the transcript.
set -uo pipefail
# A harness peer must run in the foreground, and the host must wait for a background task: with
# auto-background on, Claude Code 2.1.3xx starts an Agent call as a background task, a stop guard
# that allows the stop while the peer runs ends the headless session, and the host stops the peer
# after ten minutes (the first cadence-core pipeline trial, 2026-10-19).
export CLAUDE_AUTO_BACKGROUND_TASKS=false CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0
args=(-p "$(cat /trial/prompt.txt)" --model "${HB_MODEL:?HB_MODEL is required}"
  --permission-mode "${HB_PERMISSION_MODE:-auto}" --add-dir "$HB_OUTPUTS"
  --output-format stream-json --verbose)
if [ -n "$(ls -A /trial/plugin 2>/dev/null)" ]; then args+=(--plugin-dir /trial/plugin); fi
exec claude "${args[@]}"
