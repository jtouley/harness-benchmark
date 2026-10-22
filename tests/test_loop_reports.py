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
    assert not ok and all("FAIL" in line for line in lines if "/7" in line)


def test_the_gate_needs_n_runs_per_task():
    ok, lines = scoreboard.gate(RUNS, "claude-haiku-5-5", "b1bbdcd")
    assert not ok and any("the gate needs 3" in line for line in lines)


def _copy_baselines(dest: Path) -> None:
    for run in RUNS.iterdir():
        if run.name.startswith("20261015-"):
            shutil.copytree(run, dest / run.name)


def _scored(runs: Path, run_id: str, task: str, passed: int, seconds: float | None = None, block: str = "R7") -> None:
    record.write_record(runs, {
        "schema": 1, "run_id": run_id, "kind": "benchmark", "batch": "2026-10-23-gate",
        "provenance": {"source": "driver", "evidence": []}, "task": task, "request_id": "gh-1", "arm": "cadence",
        "cadence": {"repo": "https://github.com/jtouley/cadence", "sha": "abcdef1", "tree_clean": True},
        "model_requested": "claude-haiku-5-5", "models_served": ["claude-haiku-5-5"], "command": None,
        "started_at": None, "ended_at": None, "exit_code": 0, "cost": {"list_usd": None, "reported_usd": None},
        "stop_point": {"block": block, "reason": None}, "transcript": {"sha256": None, "missing": "t"},
        "tree": {"sha256": None, "missing": "t"}, "counts": {"counts": True, "why": "t"},
        "timing": {"agent_wall_seconds": seconds, "run_wall_seconds": None, "agent_active_seconds": None, "blocks": None},
        "isolation": None})
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


# --- speed: agent time against the one-shot of the same task and model

def test_the_one_shot_time_is_the_mean_agent_session_of_the_counted_baseline_runs():
    assert scoreboard.oneshot_seconds(RUNS, "P1", "claude-haiku-5-5") == 1882.6
    assert scoreboard.oneshot_seconds(RUNS, "P2", "claude-opus-5-5") == 2465.2
    assert scoreboard.oneshot_seconds(RUNS, "P1", "claude-fable-5-1") is None


def test_the_time_ratio_of_a_cadence_run_that_passed_a_check():
    rec = record.load(RUNS / "20261019-P1-cadence-core-haiku-1")  # stopped at E4 with 5/7
    assert scoreboard.time_ratio(RUNS, rec) == pytest.approx(3062 / 1882.6, abs=1e-3)
    assert scoreboard.time_ratio(RUNS, record.load(RUNS / "20261021-P1-cadence-core-haiku-0-killed")) is None


def test_a_run_that_stopped_early_with_no_check_passed_has_no_ratio():
    rec = record.load(RUNS / "20261021-P1-cadence-core-haiku-1")  # stopped at P4 after 10 min, 0/7
    assert not scoreboard.reached_end(RUNS, rec)
    assert scoreboard.time_ratio(RUNS, rec) is None
    assert scoreboard.reached_end(RUNS, record.load(RUNS / "20261019-P1-cadence-core-haiku-3"))  # R7, 0/7


def test_the_scoreboard_shows_the_time_ratio_beside_the_score_and_the_runs_it_left_out():
    text = scoreboard.table(RUNS)
    assert "Agent min" in text and "Time ÷ one-shot" in text
    p1 = next(line for line in text.splitlines() if "cadence-core@29315c4" in line and "| 3 |" in line)
    assert "— (3 stopped early)" in p1  # all three stopped before the end with no check passed
    b1 = next(line for line in text.splitlines() if "cadence@b1bbdcd" in line)
    assert "1.63x (1 stopped early)" in b1  # 5/7 counts; the run that stopped at P9 does not


def test_an_early_stop_does_not_lower_the_ratio(tmp_path):
    for run in RUNS.iterdir():
        if run.name.startswith("20261015-"):
            shutil.copytree(run, tmp_path / run.name)
    _scored(tmp_path, "20261023-P1-cadence-haiku-1", "P1", 6, seconds=3000.0)
    _scored(tmp_path, "20261023-P1-cadence-haiku-2", "P1", 0, seconds=60.0, block="P4")  # fast and broken
    _scored(tmp_path, "20261023-P1-cadence-haiku-3", "P1", 0, seconds=4000.0, block="R7")
    row = next(line for line in scoreboard.table(tmp_path).splitlines() if "cadence@abcdef1" in line)
    assert f"{(3000 / 1882.6 + 4000 / 1882.6) / 2:.2f}x (1 stopped early)" in row


def test_the_gate_reports_the_time_ratio_against_the_stretch_goal():
    _, lines = scoreboard.gate(RUNS, "claude-haiku-5-5", "29315c4")
    assert any("time" in line and "1.25" in line for line in lines)


def test_the_postmortem_has_a_speed_section_with_each_run_and_the_slowest():
    text = postmortem.generate(BATCH, RUNS, {})
    speed = text.split("## Speed", 1)[1].split("\n## ", 1)[0]
    row = next(line for line in speed.splitlines() if line.startswith("| `20261022-P2-cadence-core-haiku-3`"))
    assert "81.3" in row and "— (stopped early)" in row  # 3.06x the one-shot, but it never finished
    assert "Slowest runs: `20261022-P2-cadence-core-haiku-3`" in speed
    assert "Peer time per block" in speed and "| plan-review | 51.4 | 28 | 6 | 22 |" in speed
