"""Time per block from a Cadence run's attest logs (loop/blocks.py)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from loop import blocks

ROOT = Path(__file__).resolve().parents[1]
RUN = "c11abad2-208f-4d85-bb55-2a95c021b556"
OCT21 = "d8b96111ecca4367ce42c1c0feb7c85b4e1f27a7"


def _write(ctx: Path, name: str, rows: list[dict]) -> None:
    path = ctx / "attest" / f"{RUN}.{name}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _call(tool: str, stage: str, at: float, decision: str = "allow") -> dict:
    return {"tool_use_id": tool, "stage": stage, "decision": decision, "run_id": RUN, "at": at}


@pytest.fixture
def ctx(tmp_path) -> Path:
    ctx = tmp_path / ".context"
    _write(ctx, "calls", [_call("t0", "plan-create", 0, "deny"), _call("t1", "plan-create", 1),
                          _call("t2", "plan-review", 100), _call("t3", "plan-update", 200),
                          _call("t4", "plan-review", 300), _call("t5", "spec-driven", 400)])
    _write(ctx, "joins", [{"tool_use_id": f"t{i}", "agent_id": f"a{i}", "at": 0} for i in range(1, 6)])
    _write(ctx, "agents", [e for i, (start, stop) in enumerate([(2, 92), (101, 161), (201, 231), (301, 331)], 1)
                           for e in ({"agent_id": f"a{i}", "event": "start", "at": start},
                                     {"agent_id": f"a{i}", "event": "stop", "at": stop})]
                          + [{"agent_id": "a5", "event": "start", "at": 401}])  # killed before it stopped
    return ctx


def test_peer_seconds_and_calls_per_stage(ctx):
    assert blocks.peer_time(ctx) == {
        "plan-create": {"seconds": 90.0, "calls": 1, "unfinished": 0},
        "plan-review": {"seconds": 90.0, "calls": 2, "unfinished": 0},
        "plan-update": {"seconds": 30.0, "calls": 1, "unfinished": 0},
        "spec-driven": {"seconds": 0.0, "calls": 1, "unfinished": 1},
    }


def test_a_denied_call_is_not_a_peer_run(ctx):
    assert blocks.peer_time(ctx)["plan-create"]["calls"] == 1


def test_no_attest_logs_give_none(tmp_path):
    assert blocks.peer_time(tmp_path / ".context") is None


@pytest.mark.skipif(subprocess.run(["git", "cat-file", "-e", f"{OCT21}^{{commit}}"], cwd=ROOT).returncode != 0,
                    reason="the 21 October evidence commit is not fetched")
def test_the_21_october_p2_run_spent_most_of_its_peer_time_in_one_e1_call(tmp_path):
    folder = "docs/evidence/2026-10-21-pipeline-cadence-core-subscription/P2-cadence-core-haiku-2/context/attest"
    for name in ("calls", "joins", "agents"):
        text = subprocess.run(["git", "show", f"{OCT21}:{folder}/{RUN}.{name}.jsonl"], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout
        (tmp_path / "attest").mkdir(exist_ok=True)
        (tmp_path / "attest" / f"{RUN}.{name}.jsonl").write_text(text)
    found = blocks.peer_time(tmp_path)
    assert found["spec-driven"]["calls"] == 1 and round(found["spec-driven"]["seconds"] / 60, 1) == 50.1
    assert found["plan-review"]["calls"] == 4
