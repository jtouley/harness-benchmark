#!/usr/bin/env bash
# Stop hook: block the end of the session while CONTRACT.md is missing, has no checks, or has a failing check.
# Every block counts toward one cap (10), whatever the reason; after it, the session may end and the grader
# still judges the result. Every decision is logged to .contract_gate.log; at the cap the contract is still
# run once and its result logged ("cap reached") before the stop is allowed.
# Bound: hooks.json gives this hook 900 s. Setup (up to 600 s) plus slow checks (up to 300 s each) can exceed it;
# a killed hook does not block, so keep contracts well inside that budget.
cd "${CLAUDE_PROJECT_DIR:-$PWD}" || exit 0
cat >/dev/null
CAP=10
block() { python3 -c 'import json,sys; print(json.dumps({"decision":"block","reason":sys.argv[1][-1500:]}))' "$1"; exit 0; }
n=$(cat .contract_attempts 2>/dev/null || echo 0)
if [ "$n" -ge "$CAP" ]; then
  # Run the contract once more so the log holds the state at which the session ended, then allow the stop.
  if [ -f CONTRACT.md ]; then
    out=$(bash "$CLAUDE_PLUGIN_ROOT/hooks/run_contract.sh" 2>&1); rc=$?
  else
    out="no CONTRACT.md"; rc=1
  fi
  printf '%s cap reached rc=%s attempts=%s: allowing stop\n%s\n---\n' "$(date +%T)" "$rc" "$n" "$out" >> .contract_gate.log
  exit 0
fi
if [ ! -f CONTRACT.md ]; then
  echo $((n + 1)) > .contract_attempts
  echo "$(date +%T) no CONTRACT.md attempts=$n" >> .contract_gate.log
  block "CONTRACT.md does not exist yet. Get it written by the verifyloop:contract-writer agent first (verify-loop skill, step 1)."
fi
out=$(bash "$CLAUDE_PLUGIN_ROOT/hooks/run_contract.sh" 2>&1); rc=$?
printf '%s rc=%s attempts=%s\n%s\n---\n' "$(date +%T)" "$rc" "$n" "$out" >> .contract_gate.log
[ $rc -eq 0 ] && exit 0
echo $((n + 1)) > .contract_attempts
block "CONTRACT.md checks fail; fix them before finishing:
$out"
