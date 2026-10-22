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


# --- a resumed agent: several start/stop pairs (review of #66)

def _agent_events(ctx: Path, events: list[tuple[str, float]]) -> None:
    _write(ctx, "calls", [_call("t1", "plan-review", 0)])
    _write(ctx, "joins", [{"tool_use_id": "t1", "agent_id": "a1", "at": 0}])
    _write(ctx, "agents", [{"agent_id": "a1", "event": e, "at": at} for e, at in events])


def test_each_start_is_paired_with_the_next_stop_and_the_pairs_are_summed(tmp_path):
    ctx = tmp_path / ".context"
    _agent_events(ctx, [("start", 10), ("stop", 20), ("start", 30), ("stop", 45), ("start", 50), ("stop", 51)])
    assert blocks.peer_time(ctx)["plan-review"] == {"seconds": 26.0, "calls": 1, "unfinished": 0}


def test_a_start_left_open_after_a_resume_is_unfinished_never_negative(tmp_path):
    ctx = tmp_path / ".context"
    _agent_events(ctx, [("start", 10), ("stop", 20), ("start", 30)])
    assert blocks.peer_time(ctx)["plan-review"] == {"seconds": 10.0, "calls": 1, "unfinished": 1}


def test_a_duplicate_stop_counts_once_the_first_wins(tmp_path):
    ctx = tmp_path / ".context"
    _agent_events(ctx, [("start", 10), ("stop", 20), ("stop", 90)])
    assert blocks.peer_time(ctx)["plan-review"] == {"seconds": 10.0, "calls": 1, "unfinished": 0}


def test_events_are_paired_in_time_order_not_file_order(tmp_path):
    ctx = tmp_path / ".context"
    _agent_events(ctx, [("stop", 20), ("start", 10)])
    assert blocks.peer_time(ctx)["plan-review"]["seconds"] == 10.0


@pytest.mark.skipif(subprocess.run(["git", "cat-file", "-e", f"{OCT21}^{{commit}}"], cwd=ROOT).returncode != 0,
                    reason="the 21 October evidence commit is not fetched")
def test_the_resumed_plan_review_of_the_21_october_p1_run_counts_all_its_pairs(tmp_path):
    folder = "docs/evidence/2026-10-21-pipeline-cadence-core-subscription/P1-cadence-core-haiku-1/context/attest"
    names = subprocess.run(["git", "ls-tree", "--name-only", f"{OCT21}:{folder}"], cwd=ROOT,
                           capture_output=True, text=True, check=True).stdout.split()
    (tmp_path / "attest").mkdir()
    for name in names:
        (tmp_path / "attest" / name).write_text(subprocess.run(
            ["git", "show", f"{OCT21}:{folder}/{name}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
    assert round(blocks.peer_time(tmp_path)["plan-review"]["seconds"], 1) == 98.8
