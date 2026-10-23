"""Speed on every run (loop/speed.py): each Cadence run against the one-shot of the same task and model,
flagged above the stretch goal, with its cap and its slowest blocks; the postmortem reads the same rows;
loop.check refuses a counted Cadence run the loop cannot time."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

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
         batch="2026-10-23-speed", score=True, started=None) -> None:
    timing = {"agent_wall_seconds": seconds, "run_wall_seconds": None, "agent_active_seconds": None, "blocks": blocks}
    if hit_cap is not None:
        timing["hit_cap"] = hit_cap
    record.write_record(runs, {
        "schema": 1, "run_id": run_id, "kind": "benchmark", "batch": batch,
        "provenance": {"source": "driver", "evidence": []}, "task": task, "request_id": "gh-1", "arm": arm,
        "cadence": None if arm in speed.ONESHOT_ARMS else {"repo": "x", "sha": "abcdef1", "tree_clean": True},
        "model_requested": model, "models_served": [model], "command": None, "started_at": started, "ended_at": None,
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
    assert fast["oneshot_seconds"] == 1000.0 and fast["basis"] == f"batch 2026-10-23-speed, same grader tree {TREE_A[:7]}"
    assert fast["ratio"] == 1.1 and fast["flagged"] is False
    assert slow["ratio"] == 1.3 and slow["flagged"] is True
    assert slow["slowest"] == [("plan-review", 1500.0), ("implement", 900.0), ("plan-create", 600.0)]


def test_a_one_shot_missing_on_the_runs_tree_falls_back_to_every_one_shot_with_a_label(tmp_path):
    _oneshots(tmp_path)
    _run(tmp_path, "20261023-P1-cadence-haiku-1", arm="cadence", seconds=1300.0, tree="c" * 40, blocks=BLOCKS)
    r = speed.rows(tmp_path)[0]
    assert r["oneshot_seconds"] == round((900 + 1100 + 5000) / 3, 3)  # the other tree's one-shot joins the mean
    assert r["basis"] == "batch 2026-10-23-speed, any grader tree (no counted one-shot on ccccccc)"
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


# --- one basis: the gate, the findings and the postmortem read the same one-shot mean

def test_the_scoreboards_time_ratio_takes_the_same_basis_as_speed_and_keeps_the_early_stop_rule(tmp_path):
    """Two bases would disagree as soon as a one-shot lands on the runs' grader tree: the one-shots on
    TREE_A mean 1000 s, every counted one-shot means 2333 s. scoreboard.time_ratio (the gate's `_ratios`,
    the scoreboard table and findings' `max_time_ratio` call it) reads speed.oneshot_mean, so the two agree
    on both runs, and the gate's own rule stays: no ratio for a Cadence run that stopped early."""
    from loop import scoreboard
    _oneshots(tmp_path)
    _run(tmp_path, "20261023-P1-cadence-haiku-1", arm="cadence", seconds=1300.0, blocks=BLOCKS)                  # on TREE_A
    _run(tmp_path, "20261023-P1-cadence-haiku-2", arm="cadence", seconds=1300.0, tree="c" * 40, blocks=BLOCKS)   # no one-shot on its tree
    _run(tmp_path, "20261023-P1-cadence-haiku-3", arm="cadence", seconds=1300.0, blocks=BLOCKS, block="E1", passed=0)
    same, other, early = (record.load(tmp_path / f"20261023-P1-cadence-haiku-{i}") for i in (1, 2, 3))
    any_tree = round((900 + 1100 + 5000) / 3, 3)
    assert scoreboard.time_ratio(tmp_path, same) == 1.3                              # 1300 / 1000: its tree's one-shots
    assert scoreboard.time_ratio(tmp_path, other) == round(1300 / any_tree, 4)       # the fallback, same as speed's
    by_id = {r["run_id"]: r for r in speed.rows(tmp_path)}
    assert by_id[same["run_id"]]["ratio"] == scoreboard.time_ratio(tmp_path, same)
    assert by_id[other["run_id"]]["ratio"] == scoreboard.time_ratio(tmp_path, other)
    assert scoreboard.time_ratio(tmp_path, early) is None and by_id[early["run_id"]]["ratio"] == 1.3  # the gate's rule; speed shows the slow stop
    assert scoreboard.oneshot_seconds(tmp_path, "P1", "claude-haiku-5-5", None, "2026-10-23-speed") == any_tree  # no tree: every counted one-shot
    assert scoreboard.oneshot_seconds(tmp_path, "P1", "claude-haiku-5-5", TREE_A, "2026-10-23-speed") == 1000.0
    assert scoreboard.latest_tree(tmp_path / same["run_id"]) == TREE_A


# --- the basis is per batch: a later batch never moves an earlier postmortem

def test_the_basis_is_the_newest_batch_no_later_than_the_run_so_a_later_batch_leaves_a_postmortem_byte_identical(tmp_path):
    """The bars' rule, pinned by batch: a run's one-shots are those of the newest batch no later than its own
    (ids carry the date) on its grader tree, else on any tree. So when batch 2026-10-24-x lands with slower
    one-shots, the 2026-10-23-speed postmortem, its scoreboard ratio and its finding ratio do not change,
    while the new batch's run is measured against its own one-shots."""
    from loop import scoreboard
    _oneshots(tmp_path)  # batch 2026-10-23-speed: 900 and 1100 on TREE_A
    _run(tmp_path, "20261023-P1-cadence-haiku-1", arm="cadence", seconds=1300.0, blocks=BLOCKS)
    before = postmortem.generate("2026-10-23-speed", tmp_path, {}, tmp_path / "no-findings.jsonl",
                                 citations={"citations": {}})
    rec = record.load(tmp_path / "20261023-P1-cadence-haiku-1")
    assert scoreboard.time_ratio(tmp_path, rec) == 1.3
    _run(tmp_path, "20261024-P1-haiku-oneshot-1", arm="one-shot", seconds=5000.0, batch="2026-10-24-x")
    _run(tmp_path, "20261024-P1-haiku-oneshot-2", arm="baseline", seconds=3000.0, tree="d" * 40, batch="2026-10-24-x")
    _run(tmp_path, "20261024-P1-cadence-haiku-1", arm="cadence", seconds=6000.0, blocks=BLOCKS, batch="2026-10-24-x")
    after = postmortem.generate("2026-10-23-speed", tmp_path, {}, tmp_path / "no-findings.jsonl",
                                citations={"citations": {}})
    assert after == before
    assert scoreboard.time_ratio(tmp_path, rec) == 1.3
    later = next(r for r in speed.rows(tmp_path, batch="2026-10-24-x"))
    assert later["oneshot_seconds"] == 5000.0 and later["ratio"] == 1.2       # its own batch, on its tree
    assert later["basis"] == f"batch 2026-10-24-x, same grader tree {TREE_A[:7]}"
    assert scoreboard.oneshot_seconds(tmp_path, "P1", "claude-haiku-5-5", None, "2026-10-24-x") == 4000.0  # no tree: the newest, any tree
    assert scoreboard.oneshot_seconds(tmp_path, "P1", "claude-haiku-5-5", "d" * 40, "2026-10-24-x") == 3000.0
    assert scoreboard.oneshot_seconds(tmp_path, "P1", "claude-haiku-5-5", None, "2026-10-23-zz") == round((900 + 1100 + 5000) / 3, 3)
    assert scoreboard.oneshot_seconds(tmp_path, "P1", "claude-haiku-5-5", TREE_A, "2026-10-23-zz") == 1000.0


def test_a_basis_is_always_read_for_a_batch(tmp_path):
    """A read with no batch would follow the newest batch wherever it lands, and a history test built on it
    would move with batch F in silence; neither function takes one."""
    from loop import scoreboard
    _oneshots(tmp_path)
    with pytest.raises(TypeError):
        speed.oneshot_mean(tmp_path, "P1", "claude-haiku-5-5", TREE_A)
    with pytest.raises(TypeError):
        scoreboard.oneshot_seconds(tmp_path, "P1", "claude-haiku-5-5", TREE_A)
    with pytest.raises(TypeError):
        scoreboard.oneshot_seconds(tmp_path, "P1", "claude-haiku-5-5")


def test_two_batches_of_one_day_order_by_when_they_began_not_by_their_names(tmp_path):
    """Batch 2026-10-23-b began at 18:00 and 2026-10-23-a at 20:00. As strings "-a" sorts before "-b", so a run
    of a third batch of that day with no one-shot of its own would take "-b" as the newest; by batch_order it
    takes "-a", the batch that began last. The 15 October records have no started_at and sort first."""
    from loop import scoreboard
    _run(tmp_path, "20261023-P1-haiku-oneshot-b", arm="one-shot", seconds=2000.0, batch="2026-10-23-b",
         started="2026-10-23T18:00:00Z")
    _run(tmp_path, "20261023-P1-haiku-oneshot-a", arm="one-shot", seconds=4000.0, batch="2026-10-23-a",
         started="2026-10-23T20:00:00Z")
    _run(tmp_path, "20261015-P1-haiku-oneshot", arm="baseline", seconds=1000.0, batch="2026-10-15-pipeline-trials")
    _run(tmp_path, "20261023-P1-cadence-haiku-c", arm="cadence", seconds=4400.0, blocks=BLOCKS, batch="2026-10-23-c",
         started="2026-10-23T21:00:00Z")
    _run(tmp_path, "20261023-P1-cadence-haiku-b", arm="cadence", seconds=2200.0, blocks=BLOCKS, batch="2026-10-23-b",
         started="2026-10-23T18:30:00Z")
    order = speed.batch_order(speed._records(tmp_path))
    assert sorted(order, key=order.__getitem__) == ["2026-10-15-pipeline-trials", "2026-10-23-b", "2026-10-23-a",
                                                    "2026-10-23-c"]
    rows = {r["run_id"]: r for r in speed.rows(tmp_path)}
    c, b = rows["20261023-P1-cadence-haiku-c"], rows["20261023-P1-cadence-haiku-b"]
    assert c["oneshot_seconds"] == 4000.0 and c["basis"] == f"batch 2026-10-23-a, same grader tree {TREE_A[:7]}"
    assert b["oneshot_seconds"] == 2000.0 and b["ratio"] == 1.1   # "-a" began later than "-b": not its basis
    assert scoreboard.time_ratio(tmp_path, record.load(tmp_path / "20261023-P1-cadence-haiku-c")) == 1.1


def test_a_batchs_start_does_not_depend_on_the_order_its_records_are_read(tmp_path):
    """A record with no started_at (the backfilled ones) read after one that has it must not reset the batch's
    start to "": the key is the earliest start among the records that have one, in either read order."""
    _run(tmp_path, "20261023-P1-haiku-oneshot-1", arm="one-shot", seconds=1.0, batch="2026-10-23-a",
         started="2026-10-23T20:00:00Z")
    _run(tmp_path, "20261023-P1-haiku-oneshot-2", arm="one-shot", seconds=1.0, batch="2026-10-23-a")  # no started_at
    _run(tmp_path, "20261023-P1-haiku-oneshot-3", arm="one-shot", seconds=1.0, batch="2026-10-23-a",
         started="2026-10-23T21:00:00Z")
    records = speed._records(tmp_path)
    key = ("2026-10-23", "2026-10-23T20:00:00Z", "2026-10-23-a")
    assert speed.batch_order(records)["2026-10-23-a"] == key
    assert speed.batch_order(records[::-1])["2026-10-23-a"] == key
    assert speed.batch_order([records[2], records[1], records[0]])["2026-10-23-a"] == key
    assert speed.batch_order([records[1]])["2026-10-23-a"] == ("2026-10-23", "", "2026-10-23-a")  # none has one
