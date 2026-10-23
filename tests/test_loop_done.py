"""The owner's Done line (docs/rules.md, Owner's goals; Oct 22, 19:30): P1 and P2 means meet the bar on two
consecutive batches, at no more than 1.25x the one-shot time. loop.scoreboard.done measures it against the
pinned time basis (baselines.json: P1 Haiku 1882.6 s, P2 Haiku 1596.9 s) and the owner's floor: a mean of
4/7 or more is GOOD, 5/7 or more IDEAL (Oct 23)."""

from __future__ import annotations

from pathlib import Path

from loop import record, scoreboard

HAIKU = "claude-haiku-5-5"
BASIS = {"P1": 1882.6, "P2": 1596.9}
GOOD = {"P1": 6, "P2": 4}  # IDEAL on P1, GOOD on P2: both pass


def _run(runs: Path, run_id: str, batch: str, task: str, passed: int, ratio: float, started: str,
         model: str = HAIKU) -> None:
    record.write_record(runs, {
        "schema": 1, "run_id": run_id, "kind": "benchmark", "batch": batch,
        "provenance": {"source": "driver", "evidence": []}, "task": task, "request_id": "gh-1", "arm": "cadence",
        "cadence": {"repo": "https://github.com/jtouley/cadence", "sha": "abcdef1", "tree_clean": True},
        "model_requested": model, "models_served": [model], "command": None, "started_at": started,
        "ended_at": None, "exit_code": 0, "cost": {"list_usd": None, "reported_usd": None},
        "stop_point": {"block": "R7", "reason": None}, "transcript": {"sha256": None, "missing": "t"},
        "tree": {"sha256": None, "missing": "t"}, "counts": {"counts": True, "why": "t"},
        "timing": {"agent_wall_seconds": round(BASIS[task] * ratio, 3), "run_wall_seconds": None,
                   "agent_active_seconds": None, "blocks": None},
        "isolation": None})
    record.append_score(runs, {"run_id": run_id, "grader": {"repo": "jtouley/harness-benchmark", "commit": "abc1234",
                                                          "tree": "b" * 40}, "reward": passed / 7, "passed": passed,
                               "total": 7, "idempotent": True, "stream_ok": True, "error": None, "source": "driver",
                               "graded_at": None})


def _batch(runs: Path, day: str, name: str, passed=GOOD, ratio: float = 1.0, n: int = 3) -> str:
    batch = f"2026-10-{day}-{name}"
    for task in ("P1", "P2"):
        for i in range(1, n + 1):
            _run(runs, f"202610{day}-{task}-cadence-haiku-{name}-{i}", batch, task, passed[task], ratio,
                 f"2026-10-{day}T10:00:00Z")
    return batch


def test_two_consecutive_passing_batches_are_done(tmp_path):
    a, b = _batch(tmp_path, "24", "it1"), _batch(tmp_path, "25", "it2", ratio=1.2)
    ok, lines = scoreboard.done(tmp_path)
    assert ok and lines[-1] == f"DONE: {a} and {b} pass in a row"
    assert f"{a}: P1 mean 6.00/7 IDEAL, time 1.00x; P2 mean 4.00/7 GOOD, time 1.00x: PASS" in lines
    assert f"{b}: P1 mean 6.00/7 IDEAL, time 1.20x; P2 mean 4.00/7 GOOD, time 1.20x: PASS" in lines


def test_one_passing_batch_is_not_done(tmp_path):
    _batch(tmp_path, "24", "it1")
    ok, lines = scoreboard.done(tmp_path)
    assert not ok and lines[-1] == "NOT DONE: no two consecutive batches pass"


def test_a_ratio_over_1_25_fails_the_batch(tmp_path):
    a, b = _batch(tmp_path, "24", "it1"), _batch(tmp_path, "25", "it2", ratio=1.3)
    ok, lines = scoreboard.done(tmp_path)
    assert not ok
    assert f"{b}: P1 mean 6.00/7 IDEAL, time 1.30x; P2 mean 4.00/7 GOOD, time 1.30x: FAIL (time above 1.25x on P1, P2)" in lines


def test_two_passes_with_a_failing_batch_between_are_not_done(tmp_path):
    a = _batch(tmp_path, "24", "it1")
    b = _batch(tmp_path, "25", "it2", passed={"P1": 3, "P2": 4})
    c = _batch(tmp_path, "26", "it3")
    ok, lines = scoreboard.done(tmp_path)
    assert not ok and lines[-1] == "NOT DONE: no two consecutive batches pass"
    assert f"{b}: P1 mean 3.00/7 MISS, time 1.00x; P2 mean 4.00/7 GOOD, time 1.00x: FAIL (below 4/7 on P1)" in lines


def test_a_batch_short_of_n_runs_fails_and_other_models_and_one_shots_are_not_batches(tmp_path):
    _batch(tmp_path, "24", "it1", n=2)
    _run(tmp_path, "20261024-P1-cadence-opus-1", "2026-10-24-opus", "P1", 7, 1.0, "2026-10-24T10:00:00Z",
         model="claude-opus-5-5")
    ok, lines = scoreboard.done(tmp_path)
    assert not ok and lines[0] == "2026-10-24-it1: P1 2 run(s), needs 3; P2 2 run(s), needs 3: FAIL"
    assert not any("opus" in line for line in lines)


def test_the_committed_runs_are_not_done_and_the_scoreboard_shows_it():
    ok, lines = scoreboard.done(scoreboard.ROOT / "runs")
    assert not ok
    text = (scoreboard.ROOT / "scoreboard.md").read_text(encoding="utf-8")
    assert "## Done" in text and lines[-1] in text
