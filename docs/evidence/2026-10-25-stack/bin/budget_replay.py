"""Replay the stored shapes-r2 transcripts through the stack's context budget (hooks/guard_context_budget.py rules).

usage: python3 -I budget_replay.py <cadence checkout> <tx dir> <out.jsonl>
For each orchestrator (main-thread, non-sidechain) Write/Edit/MultiEdit/NotebookEdit/Bash call: the prompt tokens
of the newest main-thread assistant row before it, context_budget.block_work and judge_work with the shipped
cadence.config.json. Agent/Task calls: judge() against max_tokens (guard_subagent_handoff). Prints the first
work deny per run, how many calls would be denied, and the block the run was in (the last /command dispatched).
"""
import glob
import json
import os
import re
import sys
from pathlib import Path

cad, tx, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path[:0] = [str(cad / "scripts"), str(cad / "shared" / "scripts")]
import context_budget as cb  # noqa: E402

cfg = cb.load_config(cad)
USAGE = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
rows = []
for f in sorted(glob.glob(str(tx / "*.jsonl"))):
    name = os.path.basename(f)[:-6].replace("20261024-", "").replace("-cadence-haiku", "")
    tokens, first, denies, agent_denies, calls, last_cmd, plugin = None, None, 0, 0, 0, None, None
    for n, line in enumerate(open(f, encoding="utf-8"), 1):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("isSidechain") or row.get("parent_tool_use_id"):
            continue
        msg = row.get("message") or {}
        if row.get("type") != "assistant" or not isinstance(msg, dict):
            continue
        usage = msg.get("usage") or {}
        if usage:
            tokens = sum(int(usage.get(k) or 0) for k in USAGE)
        for block in msg.get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            tool, inp = block.get("name"), block.get("input") or {}
            if plugin is None:
                m = re.search(r"(/var/tmp/run-one/[^/\s\"']+/plugin)", json.dumps(inp))
                plugin = m.group(1) if m else None
            if tool in ("Agent", "Task"):
                cmd = re.match(r"\s*(/[\w:-]+)", str(inp.get("prompt") or ""))
                last_cmd = cmd.group(1) if cmd else last_cmd
                if cb.judge(cfg, tokens) == "deny":
                    agent_denies += 1
                continue
            if tool not in cb.WORK_TOOLS:
                continue
            calls += 1
            if plugin and tool == "Bash":
                inp = {**inp, "command": str(inp.get("command") or "").replace(plugin, str(cad))}
            work = cb.block_work(tool, inp, cad)
            if cb.judge_work(cfg, tokens, work is not None) == "deny":
                denies += 1
                if first is None:
                    first = {"line": n, "tokens": tokens, "tool": tool, "work": work[:120], "after": last_cmd}
    r = {"run": name, "orchestrator_work_calls": calls, "work_denies": denies, "agent_denies": agent_denies,
         "first_deny": first}
    rows.append(r)
    print(json.dumps(r))
out.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
