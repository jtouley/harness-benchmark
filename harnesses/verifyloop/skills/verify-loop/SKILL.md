---
name: verify-loop
description: Get an executable contract written before coding, implement until every contract check passes, and do not stop before. Use for every code change in this session.
---

# Verify loop

1. Before you change anything, call the Agent tool with `subagent_type: "verifyloop:contract-writer"`.
   In the prompt, give the original request word for word and the repository path. Nothing else.
2. Read `CONTRACT.md`. Do not delete or weaken a check. If a check is wrong (it tests something the request
   does not ask), add a line under it starting `DISPUTE:` with the reason; the check still runs.
3. Implement. Run the contract yourself: `bash "$CLAUDE_PLUGIN_ROOT/hooks/run_contract.sh"`.
4. Fix until every check passes, then finish. The session cannot end while a check fails: a Stop hook runs
   the contract and sends you back with the failures.
