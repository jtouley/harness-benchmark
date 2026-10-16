#!/usr/bin/env bash
# Stub agent for the pipeline runner test: what the agent can reach during its session. It reads the
# dev replay, tries to read the replay's files, and leaves state under HOME (as dlt would).
set -uo pipefail
frames=$(curl -sN -m 3 http://127.0.0.1:8099/v2/stream/recentchange 2>/dev/null | grep -c '^id: ')
replay_readable=false; cat /opt/hb-replay/replay.pyz >/dev/null 2>&1 && replay_readable=true
mkdir -p "$HOME/.dlt/pipelines" && echo dev >"$HOME/.dlt/pipelines/state"
printf '{"dev_frames": %d, "replay_readable": %s, "uv_offline": "%s", "python3": "%s"}\n' \
  "$frames" "$replay_readable" "${UV_OFFLINE:-}" "$(python3 -c 'import sys; print(sys.version.split()[0])')" \
  >"$HB_OUTPUTS/agent-probe.json"
echo "uncommitted" >agent-was-here.txt
# A hostile repository config: git run by root in this repository would run this hook as root.
printf '#!/bin/sh\nid -un >> %s/fsmonitor-ran\nexit 1\n' "$HB_OUTPUTS" >.git/fsmon.sh
chmod 0755 .git/fsmon.sh
git config core.fsmonitor "$PWD/.git/fsmon.sh"
echo '{"type":"result","subtype":"success","is_error":false}'
