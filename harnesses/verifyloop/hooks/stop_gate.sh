#!/usr/bin/env bash
# Stop hook: block the end of the session while CONTRACT.md is missing or has a failing check.
# Only blocks on failing checks count toward the cap (10); after it, the session may end and the grader
# still judges the result. Every decision is logged to .contract_gate.log.
cd "${CLAUDE_PROJECT_DIR:-$PWD}" || exit 0
cat >/dev/null
block() { python3 -c 'import json,sys; print(json.dumps({"decision":"block","reason":sys.argv[1][-1500:]}))' "$1"; exit 0; }
if [ ! -f CONTRACT.md ]; then
  echo "$(date +%T) no CONTRACT.md" >> .contract_gate.log
  block "CONTRACT.md does not exist yet. Get it written by the verifyloop:contract-writer agent first (verify-loop skill, step 1)."
fi
n=$(cat .contract_attempts 2>/dev/null || echo 0)
out=$(bash "$CLAUDE_PLUGIN_ROOT/hooks/run_contract.sh" 2>&1); rc=$?
printf '%s rc=%s attempts=%s\n%s\n---\n' "$(date +%T)" "$rc" "$n" "$out" >> .contract_gate.log
[ $rc -eq 0 ] && exit 0
[ "$n" -ge 10 ] && exit 0
echo $((n + 1)) > .contract_attempts
block "CONTRACT.md checks fail; fix them before finishing:
$out"
