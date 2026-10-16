"""scripts/pipeline_trial.py: how one pipeline trial's outputs become a row of the results table.

Cost comes from token counts at pricing.json list prices (Claude Code misprices some models), per model
in the session. A stalled API request is not a model failure: it is reported apart, as in the
calibration's hard3 summary.
"""

from __future__ import annotations

import json
import subprocess
from decimal import Decimal
from pathlib import Path

import pytest

from scripts import pipeline_trial as pt

PRICING = json.loads((Path(__file__).resolve().parents[1] / "pricing.json").read_text())


def write_run(tmp_path: Path, *, result: dict | None = None, grade: dict | None = None,
              timing: dict | None = None, session: list[str] | None = None, meta: dict | None = None) -> Path:
    run = tmp_path / "run"
    run.mkdir(parents=True)
    (run / "result.json").write_text(json.dumps(result if result is not None else {}))
    (run / "grade.json").write_text(json.dumps(grade or {"reward": 0.0}))
    (run / "timing.json").write_text(json.dumps({"agent_seconds": 100.0, "grader_seconds": 50.0,
                                                 "agent_exit": 0, "grader_exit": 0, "agent_timeout": 7200,
                                                 **(timing or {})}))
    (run / "trial.json").write_text(json.dumps({"task": "P1", "model": "claude-haiku-5-5", "arm": "one-shot",
                                                **(meta or {})}))
    if session is not None:
        (run / "claude-projects" / "p").mkdir(parents=True)
        (run / "claude-projects" / "p" / "s.jsonl").write_text(
            "\n".join(json.dumps({"timestamp": t}) for t in session) + "\n")
    return run


def test_cost_is_priced_per_model_from_token_counts_not_from_claude_codes_figure():
    usage = {"claude-sonnet-5-5": {"inputTokens": 1_000_000, "outputTokens": 100_000,
                                   "cacheCreationInputTokens": 200_000, "cacheReadInputTokens": 2_000_000,
                                   "costUSD": 999.0},
             "claude-haiku-5-5[1m]": {"inputTokens": 1_000_000, "outputTokens": 0,
                                      "cacheCreationInputTokens": 0, "cacheReadInputTokens": 0}}
    cost, tokens = pt.cost_and_tokens({"modelUsage": usage}, PRICING)
    # sonnet: 2.00 + 1.00 + 0.50 + 0.40 ; haiku: 0.10
    assert cost == Decimal("4.00")
    assert tokens == {"input": 2_000_000, "output": 100_000, "cache_write": 200_000, "cache_read": 2_000_000}


def test_a_model_without_a_price_is_an_error_not_a_zero():
    with pytest.raises(KeyError):
        pt.cost_and_tokens({"modelUsage": {"claude-unknown-9": {"inputTokens": 1}}}, PRICING)


def test_a_graded_run_reports_reward_checks_and_wall_time_with_and_without_the_first_build(tmp_path):
    grade = {"reward": 0.5714, "passed": 4, "total": 7, "idempotent": True, "stream_ok": True,
             "build": [{"seconds": 40.0, "exit": 0}, {"seconds": 5.0, "exit": 0}]}
    result = {"is_error": False, "subtype": "success", "num_turns": 12,
              "modelUsage": {"claude-haiku-5-5": {"inputTokens": 10, "outputTokens": 20,
                                                  "cacheCreationInputTokens": 0, "cacheReadInputTokens": 0}}}
    row = pt.summarize(write_run(tmp_path, result=result, grade=grade), PRICING)
    assert row["outcome"] == "graded"
    assert (row["reward"], row["checks"]) == (0.5714, "4/7")
    assert row["wall_seconds"] == 150.0 and row["wall_seconds_without_first_build"] == 110.0
    assert row["first_build_seconds"] == 40.0
    assert row["cost_usd"] == "0.000011"


@pytest.mark.parametrize("text", ["API Error: Request timed out.", "API Error: 529 overloaded_error",
                                  "API Error: Connection error."])
def test_an_api_error_that_ends_the_session_is_a_stall_not_a_model_failure(tmp_path, text):
    row = pt.summarize(write_run(tmp_path, result={"is_error": True, "subtype": "success", "result": text}),
                       PRICING)
    assert row["outcome"] == "api_stall" and row["counts_as_model_failure"] is False


def test_a_session_idle_long_before_the_guard_cap_is_a_stall(tmp_path):
    run = write_run(tmp_path, timing={"agent_exit": 124, "agent_seconds": 7200.0},
                    session=["2026-10-15T10:00:00.000Z", "2026-10-15T10:20:00.000Z"])
    row = pt.summarize(run, PRICING)
    assert row["outcome"] == "api_stall" and row["counts_as_model_failure"] is False


def test_a_session_busy_until_the_guard_cap_is_a_guard_cap_run(tmp_path):
    run = write_run(tmp_path, timing={"agent_exit": 124, "agent_seconds": 7200.0},
                    session=["2026-10-15T10:00:00.000Z", "2026-10-15T11:58:00.000Z"])
    row = pt.summarize(run, PRICING)
    assert row["outcome"] == "guard_cap" and row["counts_as_model_failure"] is True


def test_the_grading_deadline_is_the_measured_worst_case_plus_half():
    grades = [{"grader_seconds": 100.0}, {"grader_seconds": 120.0}]
    caps = pt.caps_from_measurements(grades)
    assert caps["grader_deadline"] == 180  # 1.5 x 120: the whole grading run
    assert caps["grader_timeout"] == 180 + pt.RUNNER_MARGIN  # the runner's backstop, above the deadline
    assert caps["measured"] == {"grader_seconds": [100.0, 120.0], "worst": 120.0}


def test_a_regrade_keeps_the_original_sessions_cost_and_agent_time_and_its_own_grade(tmp_path):
    usage = {"claude-opus-5-5": {"inputTokens": 1_000_000, "outputTokens": 0,
                                 "cacheCreationInputTokens": 0, "cacheReadInputTokens": 0}}
    original = write_run(tmp_path / "a", result={"modelUsage": usage}, grade={"reward": 0.0, "passed": 0},
                         timing={"agent_seconds": 1000.0, "grader_seconds": 150.0},
                         meta={"model": "claude-opus-5-5"})
    regrade = write_run(tmp_path / "b", grade={"reward": 1.0, "passed": 7, "build": [{"seconds": 20.0}]},
                        timing={"agent_seconds": 0.1, "grader_seconds": 160.0},
                        meta={"mode": "regrade", "model": None, "regrade_of": str(original)})
    row = pt.summarize(regrade, PRICING)
    assert (row["reward"], row["checks"], row["mode"]) == (1.0, "7/7", "regrade")
    assert row["model"] == "claude-opus-5-5" and row["cost_usd"] == "4.000000"
    assert row["agent_seconds"] == 1000.0 and row["grader_seconds"] == 160.0 and row["wall_seconds"] == 1160.0


def test_a_regrade_repository_is_the_saved_working_tree_with_its_own_ignores(tmp_path):
    saved = tmp_path / "run" / "repo"
    (saved / "pipeline").mkdir(parents=True)
    (saved / "pipeline" / "batch.py").write_text("print('x')\n")
    (saved / ".gitignore").write_text("state/\n")
    (saved / "state").mkdir()
    (saved / "state" / "pos.json").write_text("{}")
    repo = pt.repo_from_saved(saved, tmp_path / "repo")
    tracked = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True, text=True).stdout.split()
    assert tracked == [".gitignore", "pipeline/batch.py"]
