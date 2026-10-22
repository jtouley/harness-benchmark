"""Time per block of a Cadence run, from the attest logs its hooks write in `.context/attest/`.

Each peer a block sends is one allowed call (`<run>.calls.jsonl`: stage, tool_use_id), joined to the agent
that ran it (`<run>.joins.jsonl`), whose start and stop are in `<run>.agents.jsonl`. A stage's seconds are
the sum of its agents' start-to-stop times; `calls` counts its peer runs, so calls above one are repeat
rounds (plan reviews, fix rounds). An agent that never stopped (the session ended first) is counted in
`unfinished` with no seconds. Time the orchestrator spends between peers is not in any stage.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def _rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def peer_time(context_dir: Path) -> dict[str, dict] | None:
    """{stage: {"seconds", "calls", "unfinished"}} of every run in `context_dir`, or None with no attest log."""
    attest = Path(context_dir) / "attest"
    calls_files = sorted(attest.glob("*.calls.jsonl")) if attest.is_dir() else []
    if not calls_files:
        return None
    out: dict[str, dict] = defaultdict(lambda: {"seconds": 0.0, "calls": 0, "unfinished": 0})
    for calls_file in calls_files:
        prefix = calls_file.name[: -len(".calls.jsonl")]
        joins_file, agents_file = attest / f"{prefix}.joins.jsonl", attest / f"{prefix}.agents.jsonl"
        joins = {j.get("tool_use_id"): j.get("agent_id") for j in (_rows(joins_file) if joins_file.exists() else [])}
        times: dict[str, dict] = defaultdict(dict)
        for event in _rows(agents_file) if agents_file.exists() else []:
            times[event.get("agent_id")][event.get("event")] = event.get("at")
        for call in _rows(calls_file):
            if call.get("decision") != "allow" or not call.get("stage"):
                continue
            stage = out[call["stage"]]
            stage["calls"] += 1
            agent = times.get(joins.get(call.get("tool_use_id")), {})
            if isinstance(agent.get("start"), (int, float)) and isinstance(agent.get("stop"), (int, float)):
                stage["seconds"] = round(stage["seconds"] + agent["stop"] - agent["start"], 3)
            else:
                stage["unfinished"] += 1
    return dict(out)
