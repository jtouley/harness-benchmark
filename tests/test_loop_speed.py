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


def _oneshots(runs: Path) -> Path:
    """Two pinned P1 Haiku one-shots (900 s and 1100 s: the basis is 1000 s) and one more one-shot record that is
    not pinned, so moves nothing. Returns the pinned file."""
    _run(runs, "20261023-P1-haiku-oneshot-1", arm="baseline", seconds=900.0)
    _run(runs, "20261023-P1-haiku-oneshot-2", arm="one-shot", seconds=1100.0)
    _run(runs, "20261023-P1-haiku-oneshot-not-pinned", arm="one-shot", seconds=5000.0)
    pinned = runs / "pinned.json"
    pinned.write_text(json.dumps({"batch": "2026-10-23-speed", "rule": "t", "cells": {"P1": {"claude-haiku-5-5": [
        {"run_id": f"20261023-P1-haiku-oneshot-{i}", "passed": 3, "total": 7, "agent_wall_seconds": s}
        for i, s in ((1, 900.0), (2, 1100.0))]}}}))
    return pinned


# --- the rows (written first)

def test_a_run_at_1_1_is_not_flagged_and_one_at_1_3_is(tmp_path):
    pinned = _oneshots(tmp_path)
    _run(tmp_path, "20261023-P1-cadence-haiku-1", arm="cadence", seconds=1100.0, blocks=BLOCKS)
    _run(tmp_path, "20261023-P1-cadence-haiku-2", arm="cadence", seconds=1300.0, blocks=BLOCKS)
    rows = {r["run_id"]: r for r in speed.rows(tmp_path, pinned=pinned)}
    assert set(rows) == {"20261023-P1-cadence-haiku-1", "20261023-P1-cadence-haiku-2"}  # one-shots are not rows
    fast, slow = rows["20261023-P1-cadence-haiku-1"], rows["20261023-P1-cadence-haiku-2"]
    assert fast["oneshot_seconds"] == 1000.0  # the pinned two; the 5000 s record that is not pinned moves nothing
    assert fast["basis"] == "pinned 20261023-P1-haiku-oneshot-1, 20261023-P1-haiku-oneshot-2"
    assert fast["ratio"] == 1.1 and fast["flagged"] is False
    assert slow["ratio"] == 1.3 and slow["flagged"] is True
    assert slow["slowest"] == [("plan-review", 1500.0), ("implement", 900.0), ("plan-create", 600.0)]


def test_a_task_with_no_pinned_one_shot_has_no_ratio(tmp_path):
    pinned = _oneshots(tmp_path)
    _run(tmp_path, "20261023-P2-haiku-oneshot-1", arm="one-shot", seconds=900.0, task="P2")  # a record, not pinned
    _run(tmp_path, "20261023-P2-cadence-haiku-1", arm="cadence", seconds=1300.0, task="P2", blocks=BLOCKS)
    p2 = speed.rows(tmp_path, pinned=pinned)[0]
    assert p2["ratio"] is None and p2["basis"] == "no pinned one-shot of this task and model"


def test_a_run_that_hit_its_cap_shows_it_and_an_early_stop_keeps_its_ratio(tmp_path):
    pinned = _oneshots(tmp_path)
    _run(tmp_path, "20261023-P1-cadence-haiku-1", arm="cadence", seconds=7200.0, blocks=BLOCKS, hit_cap=True,
         block="E1", passed=0)
    r = speed.rows(tmp_path, pinned=pinned)[0]
    assert r["hit_cap"] is True and speed.cap_text(r) == "hit"
    assert r["ratio"] == 7.2 and r["flagged"] and not r["reached_end"]
    assert speed.ratio_text(r) == "7.20 (above 1.25) (stopped early)"
    line = speed.line(r)
    assert "| hit |" in line and "| E1 |" in line and "plan-review 25.0 min, implement 15.0 min, plan-create 10.0 min" in line


def test_the_table_groups_by_task_and_model_and_names_the_flagged_runs(tmp_path):
    pinned = _oneshots(tmp_path)
    _run(tmp_path, "20261023-P1-cadence-haiku-1", arm="cadence", seconds=1100.0, blocks=BLOCKS)
    _run(tmp_path, "20261023-P1-cadence-haiku-2", arm="cadence", seconds=1300.0, blocks=BLOCKS, batch="2026-10-24-x")
    text = speed.table(tmp_path, pinned=pinned)
    assert "## P1, claude-haiku-5-5" in text and "Above the stretch goal: `20261023-P1-cadence-haiku-2`." in text
    assert "Above the stretch goal: none." in speed.table(tmp_path, batch="2026-10-23-speed", pinned=pinned)
    assert "No Cadence run in batch 2026-10-25-none." in speed.table(tmp_path, batch="2026-10-25-none", pinned=pinned)
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
    """The postmortem reads the committed baselines.json: P1 Haiku is 20261015-P1-haiku-1, 1882.6 s."""
    _run(tmp_path, "20261023-P1-cadence-haiku-2", arm="cadence", seconds=2447.38, blocks=BLOCKS, hit_cap=False)
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
    argv = ["--run-id", "20261023-P1-cadence-haiku-9", "--kind", "stub", "--batch", "2026-10-23-stub", "--task", "P1",
            "--arm", "cadence", "--runs", str(tmp_path / "runs"), "--store", str(tmp_path / "store"),
            "--transcript", str(tmp_path / "t.jsonl"), "--timing", str(tmp_path / "timing.json"),
            "--cwd", str(tmp_path / "work"), "--", "true"]
    assert driver.main(argv) == 0
    timing = record.load(tmp_path / "runs" / "20261023-P1-cadence-haiku-9")["timing"]
    assert timing["agent_wall_seconds"] == 123.4 and timing["hit_cap"] is True and timing["cap_seconds"] == 120


# --- one basis: the gate, the findings and the postmortem read the same one-shot mean

def test_the_scoreboards_time_ratio_takes_the_same_basis_as_speed_and_keeps_the_early_stop_rule(tmp_path):
    """scoreboard.time_ratio (the gate's `_ratios`, the scoreboard table and findings' `max_time_ratio` call it)
    reads the pinned file through loop.baselines, as speed does, so the two agree, and the gate's own rule
    stays: no ratio for a Cadence run that stopped early."""
    from loop import scoreboard
    pinned = _oneshots(tmp_path)
    _run(tmp_path, "20261023-P1-cadence-haiku-1", arm="cadence", seconds=1300.0, blocks=BLOCKS)
    _run(tmp_path, "20261023-P1-cadence-haiku-2", arm="cadence", seconds=1300.0, tree="c" * 40, blocks=BLOCKS)
    _run(tmp_path, "20261023-P1-cadence-haiku-3", arm="cadence", seconds=1300.0, blocks=BLOCKS, block="E1", passed=0)
    one, other_tree, early = (record.load(tmp_path / f"20261023-P1-cadence-haiku-{i}") for i in (1, 2, 3))
    by_id = {r["run_id"]: r for r in speed.rows(tmp_path, pinned=pinned)}
    for rec in (one, other_tree):  # the grader tree no longer picks a basis
        assert scoreboard.time_ratio(tmp_path, rec, pinned) == 1.3 == by_id[rec["run_id"]]["ratio"]
    assert scoreboard.time_ratio(tmp_path, early, pinned) is None and by_id[early["run_id"]]["ratio"] == 1.3
    assert scoreboard.oneshot_seconds("P1", "claude-haiku-5-5", pinned) == 1000.0
    assert speed.oneshot_mean("P1", "claude-haiku-5-5", pinned) == (1000.0, "pinned 20261023-P1-haiku-oneshot-1, "
                                                                            "20261023-P1-haiku-oneshot-2")


# --- no one-shot record moves a ratio: a later batch leaves a postmortem byte-identical

def test_a_later_one_shot_record_moves_no_ratio_and_leaves_a_postmortem_byte_identical(tmp_path):
    """Owner, 2026-10-23: the baselines are fixed. One-shots landing in a later batch, slower or faster, change neither
    the earlier postmortem, its scoreboard ratio nor the later Cadence run's basis."""
    from loop import scoreboard
    _run(tmp_path, "20261023-P1-cadence-haiku-1", arm="cadence", seconds=2447.38, blocks=BLOCKS)
    gen = lambda: postmortem.generate("2026-10-23-speed", tmp_path, {}, tmp_path / "no-findings.jsonl",
                                      citations={"citations": {}})
    before = gen()
    rec = record.load(tmp_path / "20261023-P1-cadence-haiku-1")
    assert scoreboard.time_ratio(tmp_path, rec) == 1.3  # 2447.38 / 1882.6, the pinned 20261015-P1-haiku-1
    _run(tmp_path, "20261024-P1-haiku-oneshot-2", arm="one-shot", seconds=100.0, batch="2026-10-24-x")
    _run(tmp_path, "20261024-P1-haiku-oneshot-1", arm="one-shot", seconds=5000.0, batch="2026-10-24-x")
    _run(tmp_path, "20261024-P1-cadence-haiku-1", arm="cadence", seconds=1882.6, blocks=BLOCKS, batch="2026-10-24-x")
    assert gen() == before and scoreboard.time_ratio(tmp_path, rec) == 1.3
    later = speed.rows(tmp_path, batch="2026-10-24-x")[0]
    assert later["ratio"] == 1.0 and later["basis"] == "pinned 20261015-P1-haiku-1"
