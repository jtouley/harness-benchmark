#!/usr/bin/env python3
"""Summarize Harbor jobs under jobs/ into results.json: per job and task, reward, cost, tokens, errors.

Harbor's cost_usd is Claude Code's own figure; for models Claude Code does not price (Haiku 5.5) the
dollars are recomputed from token counts at ../../pricing.json list prices.
"""
import json, sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRICES = json.loads((HERE.parents[1] / "pricing.json").read_text())["models"]
MODEL = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5", "haiku": "claude-haiku-5-5"}

def usd(model, a):
    p = PRICES.get(model)
    if not p:
        return None
    inp, cache, out = a.get("n_input_tokens") or 0, a.get("n_cache_tokens") or 0, a.get("n_output_tokens") or 0
    # Harbor's n_input_tokens includes cache reads; cache writes are not split out, so they are priced as input.
    return float((Decimal(inp - cache) * Decimal(p["input"]) + Decimal(cache) * Decimal(p["cache_read"])
                  + Decimal(out) * Decimal(p["output"])) / Decimal(10**6))

rows = []
for job in sorted((HERE / "jobs").glob("*")):
    model = next((m for k, m in MODEL.items() if job.name.startswith(k)), None)
    for f in sorted(job.glob("instance_*/result.json")):
        d = json.loads(f.read_text())
        if not d.get("finished_at"):
            continue
        a = d.get("agent_result") or {}
        e = d.get("exception_info") or {}
        reward = ((d.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        rows.append({"job": job.name, "task": d.get("task_name", "").split("/")[-1], "reward": reward,
                     "exception": e.get("exception_type"), "harbor_cost_usd": a.get("cost_usd"),
                     "usd_from_tokens": usd(model, a) if model else None,
                     "tokens": {k: a.get(k) for k in ("n_input_tokens", "n_cache_tokens", "n_output_tokens")}})
(HERE / "results.json").write_text(json.dumps(rows, indent=1) + "\n")
by = {}
for r in rows:
    b = by.setdefault(r["job"], {"trials": 0, "pass": 0, "fail": 0, "infra_error": 0})
    b["trials"] += 1
    if r["reward"] == 1.0: b["pass"] += 1
    elif r["reward"] is None: b["infra_error"] += 1
    else: b["fail"] += 1
print(json.dumps(by, indent=1))
