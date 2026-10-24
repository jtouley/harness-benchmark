"""Blocks that ran in one Cadence run, in order, from its .context attest logs: stage, model, minutes, return
decision, and the verdict line of any review file the peer wrote. Usage: blocks_report.py <run dir>"""
import json
import re
import sys
from pathlib import Path

run = Path(sys.argv[1])
ctx = run / "repo" / ".context"
attest = ctx / "attest"


def rows(suffix):
    out = []
    for f in sorted(attest.glob(f"*{suffix}")):
        out += [json.loads(line) for line in f.read_text().splitlines() if line.strip()]
    return out


calls = rows(".calls.jsonl")
joins = {j["tool_use_id"]: j for j in rows(".joins.jsonl")}
starts = {a["agent_id"]: a["at"] for a in rows(".agents.jsonl") if a["event"] == "start"}
stops = {a["agent_id"]: a["at"] for a in rows(".agents.jsonl") if a["event"] == "stop"}
returns = {r["agent_id"]: r for r in rows(".returns.jsonl")}
writes = {}
for w in [r for r in rows(".jsonl") if "path" in r]:
    writes.setdefault(w["agent_id"], []).append(w["path"])


def verdict(path):
    p = ctx / path
    if not p.exists():
        return None
    text = p.read_text(errors="replace")
    m = re.search(r"^#+\s*Verdict\s*\n+\s*(\S[^\n]*)", text, re.M) or re.search(r"(?im)^\**verdict\**[:\s]+(.+)$", text)
    return m.group(1).strip()[:80] if m else None


counts = {}
print(f"{'#':>2} {'stage':28} {'model':18} {'min':>6}  return / verdict")
for i, c in enumerate(calls, 1):
    stage = c["stage"]
    counts[stage] = counts.get(stage, 0) + 1
    j = joins.get(c["tool_use_id"], {})
    aid = j.get("agent_id")
    mins = (stops[aid] - starts[aid]) / 60 if aid in starts and aid in stops else None
    ret = returns.get(aid, {})
    vs = [f"{p}: {verdict(p)}" for p in writes.get(aid, []) if verdict(p)]
    print(f"{i:>2} {stage + (' (round ' + str(counts[stage]) + ')' if counts[stage] > 1 else ''):28} "
          f"{(j.get('resolved_model') or '?'):18} {mins if mins is None else round(mins, 1)!s:>6}  "
          f"{ret.get('decision')} {ret.get('reason') or ''} | {'; '.join(vs) or '-'}")
print("rounds per stage:", counts)
