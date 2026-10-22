"""The postmortem generator and the scoreboard (loop/postmortem.py, loop/scoreboard.py)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from loop import postmortem, record, scoreboard

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
BATCH = "2026-10-21-cadence-core-subscription"
A_RUN = "20261021-P1-cadence-core-haiku-1"


# --- postmortem

@pytest.mark.parametrize("item", [
    {"text": "a cause"},                                      # no run id
    {"text": "a cause", "run_ids": []},
    {"text": "a cause", "run_ids": ["live run 7"]},           # not a run id
    {"text": "a cause", "run_ids": ["20261020-P1-nowhere"]},  # no record
])
def test_a_hand_written_line_without_a_resolvable_run_id_is_refused(item):
    with pytest.raises(postmortem.PostmortemError, match="root_causes"):
        postmortem.generate(BATCH, RUNS, {"root_causes": [item]})


def test_a_ledger_line_needs_one_of_the_three_statuses():
    with pytest.raises(postmortem.PostmortemError, match="status"):
        postmortem.generate(BATCH, RUNS, {"ledger": [{"status": "PROBABLY", "claim": "x", "run_ids": [A_RUN]}]})


def test_the_sections_are_fixed_and_in_order():
    text = postmortem.generate(BATCH, RUNS, {})
    found = [line[3:] for line in text.splitlines() if line.startswith("## ")]
    assert found == list(postmortem.SECTIONS)


def test_each_counted_scored_run_is_a_verified_line():
    text = postmortem.generate(BATCH, RUNS, {})
    verified = [line for line in text.splitlines() if line.startswith("| VERIFIED |")]
    assert len(verified) == 6 and all("0/7" in line for line in verified)


def test_the_committed_postmortem_is_what_the_generator_writes():
    notes = json.loads((ROOT / "postmortems" / f"{BATCH}.notes.json").read_text(encoding="utf-8"))
    assert postmortem.generate(BATCH, RUNS, notes) == (ROOT / "postmortems" / f"{BATCH}.md").read_text(encoding="utf-8")


# --- scoreboard

def test_the_baselines_are_the_15_october_one_shots():
    assert scoreboard.baseline(RUNS, "P1", scoreboard.SONNET) == 3
    assert scoreboard.baseline(RUNS, "P1", scoreboard.OPUS) == 6
    assert scoreboard.baseline(RUNS, "P2", scoreboard.SONNET) == 3
    assert scoreboard.baseline(RUNS, "P2", scoreboard.OPUS) == 5


def test_the_gate_fails_cadence_core_29315c4_on_haiku():
    ok, lines = scoreboard.gate(RUNS, "claude-haiku-5-5", "29315c4")
    assert not ok and all("FAIL" in line for line in lines)


def test_the_gate_needs_n_runs_per_task():
    ok, lines = scoreboard.gate(RUNS, "claude-haiku-5-5", "b1bbdcd")
    assert not ok and any("the gate needs 3" in line for line in lines)


def _copy_baselines(dest: Path) -> None:
    for run in RUNS.iterdir():
        if run.name.startswith("20261015-"):
            shutil.copytree(run, dest / run.name)


def _scored(runs: Path, run_id: str, task: str, passed: int) -> None:
    record.write_record(runs, {
        "schema": 1, "run_id": run_id, "kind": "benchmark", "batch": "2026-10-23-gate",
        "provenance": {"source": "driver", "evidence": []}, "task": task, "request_id": "gh-1", "arm": "cadence",
        "cadence": {"repo": "https://github.com/jtouley/cadence", "sha": "abcdef1", "tree_clean": True},
        "model_requested": "claude-haiku-5-5", "models_served": ["claude-haiku-5-5"], "command": None,
        "started_at": None, "ended_at": None, "exit_code": 0, "cost": {"list_usd": None, "reported_usd": None},
        "stop_point": {"block": "R7", "reason": None}, "transcript": {"sha256": None, "missing": "t"},
        "tree": {"sha256": None, "missing": "t"}, "counts": {"counts": True, "why": "t"}})
    record.append_score(runs, {"run_id": run_id, "grader": {"repo": "jtouley/harness-benchmark", "commit": "abc1234",
                                                          "tree": "b" * 40}, "reward": passed / 7, "passed": passed,
                               "total": 7, "idempotent": True, "stream_ok": True, "error": None, "source": "driver",
                               "graded_at": None})


@pytest.mark.parametrize(("p1", "p2", "ok"), [
    ((6, 6, 6), (5, 5, 5), True),   # matches Opus on both
    ((6, 6, 5), (5, 5, 5), False),  # P1 mean 5.67 is below Opus 6
    ((7, 7, 7), (4, 4, 4), False),  # P2 beats Sonnet but not Opus
])
def test_the_gate_compares_the_mean_with_sonnet_and_opus(tmp_path, p1, p2, ok):
    _copy_baselines(tmp_path)
    for task, passed in (("P1", p1), ("P2", p2)):
        for i, p in enumerate(passed, 1):
            _scored(tmp_path, f"20261023-{task}-cadence-haiku-{i}", task, p)
    assert scoreboard.gate(tmp_path, "claude-haiku-5-5", "abcdef1")[0] is ok


def test_the_committed_scoreboard_is_what_the_generator_writes():
    assert scoreboard.table(RUNS) == (ROOT / "scoreboard.md").read_text(encoding="utf-8")
