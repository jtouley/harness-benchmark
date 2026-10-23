"""Speed on every run (loop/speed.py): each Cadence run against the one-shot of the same task and model,
flagged above the stretch goal, with its cap and its slowest blocks; the postmortem reads the same rows;
loop.check refuses a counted Cadence run the loop cannot time."""

from __future__ import annotations

import json
from pathlib import Path

from loop import check, postmortem, record, speed

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
TREE_A, TREE_B = "a" * 40, "b" * 40
BLOCKS = {"plan-create": {"seconds": 600.0, "calls": 1, "unfinished": 0},
          "plan-review": {"seconds": 1500.0, "calls": 3, "unfinished": 0},
          "implement": {"seconds": 900.0, "calls": 1, "unfinished": 0},
          "pr-review": {"seconds": 300.0, "calls": 1, "unfinished": 0}}


def _run(runs: Path, run_id: str, *, arm: str, seconds: float | None, tree: str | None = TREE_A, task="P1",
         model="claude-haiku-5-5", block="R7", passed=3, blocks=None, hit_cap=None, counts=True,
         batch="2026-10-23-speed", score=True) -> None:
    timing = {"agent_wall_seconds": seconds, "run_wall_seconds": None, "agent_active_seconds": None, "blocks": blocks}
    if hit_cap is not None:
        timing["hit_cap"] = hit_cap
    record.write_record(runs, {
        "schema": 1, "run_id": run_id, "kind": "benchmark", "batch": batch,
        "provenance": {"source": "driver", "evidence": []}, "task": task, "request_id": "gh-1", "arm": arm,
        "cadence": None if arm in speed.ONESHOT_ARMS else {"repo": "x", "sha": "abcdef1", "tree_clean": True},
        "model_requested": model, "models_served": [model], "command": None, "started_at": None, "ended_at": None,
        "exit_code": 0, "cost": {"list_usd": None, "reported_usd": None}, "stop_point": {"block": block, "reason": None},
        "transcript": {"sha256": None, "missing": "t"}, "tree": {"sha256": None, "missing": "t"},
        "counts": {"counts": counts, "why": "t"}, "timing": timing, "isolation": None})
    if score:
        record.append_score(runs, {"run_id": run_id, "grader": {"repo": "jtouley/harness-benchmark", "commit": "abc1234",
                                                              "tree": tree}, "reward": passed / 7, "passed": passed,
                                   "total": 7, "idempotent": True, "stream_ok": True, "error": None, "source": "driver",
                                   "graded_at": None})


def _oneshots(runs: Path) -> None:
    _run(runs, "20261023-P1-haiku-oneshot-1", arm="baseline", seconds=900.0)
    _run(runs, "20261023-P1-haiku-oneshot-2", arm="one-shot", seconds=1100.0)  # both arm names count
    _run(runs, "20261023-P1-haiku-oneshot-other-tree", arm="baseline", seconds=5000.0, tree=TREE_B)
    _run(runs, "20261023-P1-haiku-oneshot-not-counted", arm="baseline", seconds=5000.0, counts=False)


# --- the rows (written first)

def test_a_run_at_1_1_is_not_flagged_and_one_at_1_3_is(tmp_path):
    _oneshots(tmp_path)
    _run(tmp_path, "20261023-P1-cadence-haiku-1", arm="cadence", seconds=1100.0, blocks=BLOCKS)
    _run(tmp_path, "20261023-P1-cadence-haiku-2", arm="cadence", seconds=1300.0, blocks=BLOCKS)
    rows = {r["run_id"]: r for r in speed.rows(tmp_path)}
    assert set(rows) == {"20261023-P1-cadence-haiku-1", "20261023-P1-cadence-haiku-2"}  # one-shots are not rows
    fast, slow = rows["20261023-P1-cadence-haiku-1"], rows["20261023-P1-cadence-haiku-2"]
    assert fast["oneshot_seconds"] == 1000.0 and fast["basis"] == f"same grader tree {TREE_A[:7]}"
    assert fast["ratio"] == 1.1 and fast["flagged"] is False
    assert slow["ratio"] == 1.3 and slow["flagged"] is True
    assert slow["slowest"] == [("plan-review", 1500.0), ("implement", 900.0), ("plan-create", 600.0)]


def test_a_one_shot_missing_on_the_runs_tree_falls_back_to_every_one_shot_with_a_label(tmp_path):
    _oneshots(tmp_path)
    _run(tmp_path, "20261023-P1-cadence-haiku-1", arm="cadence", seconds=1300.0, tree="c" * 40, blocks=BLOCKS)
    r = speed.rows(tmp_path)[0]
    assert r["oneshot_seconds"] == round((900 + 1100 + 5000) / 3, 3)  # the other tree's one-shot joins the mean
    assert r["basis"] == "any grader tree (no counted one-shot on ccccccc)"
    _run(tmp_path, "20261023-P2-cadence-haiku-1", arm="cadence", seconds=1300.0, task="P2", blocks=BLOCKS)
    p2 = next(r for r in speed.rows(tmp_path) if r["task"] == "P2")
    assert p2["ratio"] is None and p2["basis"] == "no counted one-shot of this task and model"


def test_a_run_that_hit_its_cap_shows_it_and_an_early_stop_keeps_its_ratio(tmp_path):
    _oneshots(tmp_path)
    _run(tmp_path, "20261023-P1-cadence-haiku-1", arm="cadence", seconds=7200.0, blocks=BLOCKS, hit_cap=True,
         block="E1", passed=0)
    r = speed.rows(tmp_path)[0]
    assert r["hit_cap"] is True and speed.cap_text(r) == "hit"
    assert r["ratio"] == 7.2 and r["flagged"] and not r["reached_end"]
    assert speed.ratio_text(r) == "7.20 (above 1.25) (stopped early)"
    line = speed.line(r)
    assert "| hit |" in line and "| E1 |" in line and "plan-review 25.0 min, implement 15.0 min, plan-create 10.0 min" in line


def test_the_table_groups_by_task_and_model_and_names_the_flagged_runs(tmp_path):
    _oneshots(tmp_path)
    _run(tmp_path, "20261023-P1-cadence-haiku-1", arm="cadence", seconds=1100.0, blocks=BLOCKS)
    _run(tmp_path, "20261023-P1-cadence-haiku-2", arm="cadence", seconds=1300.0, blocks=BLOCKS, batch="2026-10-24-x")
    text = speed.table(tmp_path)
    assert "## P1, claude-haiku-5-5" in text and "Above the stretch goal: `20261023-P1-cadence-haiku-2`." in text
    assert "Above the stretch goal: none." in speed.table(tmp_path, batch="2026-10-23-speed")
    assert "No Cadence run in batch 2026-10-25-none." in speed.table(tmp_path, batch="2026-10-25-none")
    assert speed.main(["--runs", str(tmp_path), "--batch", "2026-10-24-x"]) == 0


# --- the check rule

def test_a_counted_cadence_run_without_timing_or_blocks_is_a_problem(tmp_path):
    _oneshots(tmp_path)
    _run(tmp_path, "20261023-P1-cadence-haiku-1", arm="cadence", seconds=None, blocks=None)
    _run(tmp_path, "20261023-P1-cadence-haiku-2", arm="cadence", seconds=1000.0, blocks=None, counts=False)
    _run(tmp_path, "20261023-P1-cadence-haiku-3", arm="cadence", seconds=1000.0, blocks=BLOCKS)
    problems = speed.problems(tmp_path)
    assert problems == ["20261023-P1-cadence-haiku-1: counted Cadence run with no agent session time (timing.json's agent_seconds)",
                        "20261023-P1-cadence-haiku-1: counted Cadence run with no time per block (loop.blocks from its .context)"]
    (tmp_path / "20261023-P1-cadence-haiku-1" / "blocks.json").write_text(json.dumps({"source": "t", "blocks": BLOCKS}))
    assert len(speed.problems(tmp_path)) == 1  # a backfilled blocks.json counts as time per block


def test_the_committed_runs_can_all_be_timed():
    assert speed.problems(RUNS) == []
    assert check.main([]) == 0


# --- the postmortem reads the same rows

def test_the_postmortem_speed_section_is_the_speed_rows(tmp_path):
    _oneshots(tmp_path)
    _run(tmp_path, "20261023-P1-cadence-haiku-2", arm="cadence", seconds=1300.0, blocks=BLOCKS, hit_cap=False)
    text = postmortem.generate("2026-10-23-speed", tmp_path, {}, tmp_path / "no-findings.jsonl",
                               citations={"citations": {}})
    section = text.split("## Speed", 1)[1].split("\n## ", 1)[0]
    r = speed.rows(tmp_path)[0]
    assert speed.line(r) in section
    assert "Above the stretch goal: `20261023-P1-cadence-haiku-2` (1.30; slowest blocks plan-review 25.0 min" in section
    assert "| no |" in speed.line(r)


def test_the_driver_keeps_hit_cap_and_the_cap_from_timing_json(tmp_path):
    (tmp_path / "store").mkdir()
    (tmp_path / "work").mkdir()
    (tmp_path / "timing.json").write_text(json.dumps({"agent_seconds": 123.4, "grader_seconds": 5, "agent_exit": 124,
                                                      "agent_cap_seconds": 120, "hit_cap": True}))
    from loop import driver
    argv = ["--run-id", "20261023-P1-baseline-haiku-9", "--kind", "stub", "--batch", "2026-10-23-stub", "--task", "P1",
            "--arm", "baseline", "--runs", str(tmp_path / "runs"), "--store", str(tmp_path / "store"),
            "--transcript", str(tmp_path / "t.jsonl"), "--timing", str(tmp_path / "timing.json"),
            "--cwd", str(tmp_path / "work"), "--", "true"]
    assert driver.main(argv) == 0
    timing = record.load(tmp_path / "runs" / "20261023-P1-baseline-haiku-9")["timing"]
    assert timing["agent_wall_seconds"] == 123.4 and timing["hit_cap"] is True and timing["cap_seconds"] == 120
