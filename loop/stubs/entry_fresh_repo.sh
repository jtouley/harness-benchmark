#!/usr/bin/env bash
# Stub run (loop.driver --kind stub): Cadence's documented first action in a fresh task repository on `main`
# with no ticket, the state a `/cadence <spec>` run starts from. Writes transcript.jsonl and stop.json in OUT.
#   entry_fresh_repo.sh PLUGIN OUT
set -uo pipefail
plugin=$1 out=$2
mkdir -p "$out" repo
cd repo || exit 3
env -u GIT_DIR git init -q -b main
env -u GIT_DIR git -c user.name=stub -c user.email=stub@example.com commit -q --allow-empty -m base
cmd=(python3 "$plugin/scripts/activate_session.py" --from-branch --fresh --supersede)
output=$(CADENCE_HOME="$plugin" "${cmd[@]}" 2>&1)
rc=$?
python3 - "$out" "$rc" "$output" "${cmd[*]}" <<'PY'
import json, sys
out, rc, output, cmd = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
with open(f"{out}/transcript.jsonl", "w") as f:
    f.write(json.dumps({"type": "stub", "step": "activate", "command": cmd, "exit": rc, "output": output}) + "\n")
stop = {"block": "A1", "reason": output.strip().splitlines()[-1] if output.strip() else f"exit {rc}"} if rc else \
    {"block": None, "reason": None}
json.dump(stop, open(f"{out}/stop.json", "w"))
PY
exit "$rc"
