"""Time per block of a Cadence run, from the attest logs its hooks write in `.context/attest/`.

Each peer a block sends is one allowed call (`<run>.calls.jsonl`: stage, tool_use_id), joined to the agent
that ran it (`<run>.joins.jsonl`), whose start and stop events are in `<run>.agents.jsonl`. An agent that
is resumed has several start/stop pairs: in time order, each start is paired with the next stop and the
pairs are summed; a second stop with no start between (a duplicate) is ignored, so the first stop wins. A
start with no stop after it (the session ended first) makes the peer `unfinished` and adds no seconds.

A stage's seconds are the sum of its agents' paired times; `calls` counts its peer runs, so calls above one
are repeat rounds (plan reviews, fix rounds). Peers that run in parallel are each counted in full, so the
stages can add up to more than the wall time they overlap. Time the orchestrator spends between peers is in
no stage.
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


def _paired(events: list[tuple[float, str]]) -> tuple[float, bool]:
    """(seconds of the start/stop pairs, whether a start is left open) of one agent's events."""
    total, opened = 0.0, None
    for at, kind in sorted(events):
        if kind == "start" and opened is None:
            opened = at
        elif kind == "stop" and opened is not None:
            total += at - opened
            opened = None
    return total, opened is not None


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
        events: dict[str, list[tuple[float, str]]] = defaultdict(list)
        for event in _rows(agents_file) if agents_file.exists() else []:
            if event.get("event") in ("start", "stop") and isinstance(event.get("at"), (int, float)):
                events[event.get("agent_id")].append((float(event["at"]), event["event"]))
        for call in _rows(calls_file):
            if call.get("decision") != "allow" or not call.get("stage"):
                continue
            stage = out[call["stage"]]
            stage["calls"] += 1
            agent = events.get(joins.get(call.get("tool_use_id")), [])
            seconds, still_open = _paired(agent)
            stage["seconds"] = round(stage["seconds"] + seconds, 3)
            if still_open or not agent:
                stage["unfinished"] += 1
    return dict(out)
