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


@pytest.mark.parametrize("rc", [124, 137, 143])
def test_a_harness_session_ended_before_its_backstop_is_its_own(tmp_path, rc):
    """Criteria v2 section 5.3: short of the backstop, a crash or self-kill is graded on what the arm left."""
    run = write_run(tmp_path, timing={"agent_exit": rc, "agent_seconds": 7203.0, "agent_timeout": 0,
                                      "agent_backstop": 86400},
                    session=["2026-10-19T04:46:00.000Z", "2026-10-19T06:46:00.000Z"], meta={"arm": "cadence-core"})
    row = pt.summarize(run, PRICING)
    assert row["outcome"] == "graded" and row["counted"] is True and row["counts_as_model_failure"] is True


@pytest.mark.parametrize("timing, result", [
    ({"agent_exit": 124, "agent_seconds": 9001.0, "agent_backstop": 9000}, {}),
    ({"agent_exit": 1, "agent_seconds": 600.0, "agent_backstop": 9000}, {"subtype": "error_max_budget_usd"}),
])
def test_a_harness_run_at_its_backstop_is_attempted_and_not_delivered(tmp_path, timing, result):
    """Owner, 2026-10-20: time or Claude Code's spend limit, whichever first; counted, a model failure."""
    run = write_run(tmp_path, timing={"agent_timeout": 0, **timing}, result=result, grade={"reward": 1.0},
                    meta={"arm": "cadence-core"})
    row = pt.summarize(run, PRICING)
    assert row["outcome"] == "backstop" and row["counted"] is True and row["counts_as_model_failure"] is True


def _harness_rows(seconds, costs, harness=True, outcome="graded", task="P1", source="default", rc=0, name="r"):
    return [{"counted": True, "outcome": outcome, "harness": harness, "agent_seconds": s, "host_cost_usd": c,
             "run_path": f"runs/{name}{i}", "task": task, "backstop_source": source, "agent_exit": rc}
            for i, (s, c) in enumerate(zip(seconds, costs))]


def test_a_backstop_uses_only_its_classes_tasks_and_runs_made_under_the_default():
    rows = _harness_rows([100, 200, 300, 400, 500], [1.0, 2.0, 3.0, 4.0, 5.0])
    rows += _harness_rows([99999] * 3, [99.0] * 3, task="P2", name="p2-")  # another class
    rows += _harness_rows([99999] * 3, [99.0] * 3, source="class lift", name="c")  # under the class backstop
    rows += _harness_rows([99999] * 3, [99.0] * 3, source=None, name="old")  # before backstops: a guard cap
    rows += _harness_rows([3000] * 3, [9.0] * 3, rc=137, name="k")  # killed from outside, not marked infra
    rows += _harness_rows([100, 200], [1.0, 2.0])  # the same runs listed again
    assert pt.backstop_from_rows(rows, min_runs=5, tasks=["P1"])["seconds"] == 617


def test_a_cost_of_nothing_sets_no_dollar_backstop():
    assert pt.backstop_from_rows(_harness_rows([1, 2], [0.0, 0.0]), min_runs=2)["usd"] is None


def test_the_backstop_is_the_mean_plus_two_standard_deviations_of_time_and_cost():
    rows = _harness_rows([100, 200, 300, 400, 500], [1.0, 2.0, 3.0, 4.0, 5.0])
    rows += _harness_rows([99999] * 3, [99.0] * 3, harness=False)  # a one-shot, a reference or a skeleton run
    rows += _harness_rows([99999], [99.0], outcome="backstop")  # did not end on its own
    backstop = pt.backstop_from_rows(rows, min_runs=5)
    # mean 300, sample SD 158.11 -> 616.2 -> 617 s; mean 3.0, SD 1.5811 -> 6.162 -> $6.17 (both round up)
    assert (backstop["seconds"], backstop["usd"], backstop["measured"]["n"]) == (617, 6.17, 5)
    assert backstop["from_runs"] == [f"runs/r{i}" for i in range(5)]  # only the runs used


def test_reference_and_skeleton_trials_are_not_harness_runs():
    assert not pt.is_harness({"mode": "reference", "arm": "reference"})
    assert not pt.is_harness({"mode": "skeleton", "arm": "skeleton"})
    assert not pt.is_harness({"mode": "agent", "arm": "one-shot"})
    assert pt.is_harness({"mode": "agent", "arm": "cadence-core"})  # an older trial.json
    assert pt.is_harness({"harness": True, "mode": "regrade", "arm": "regrade"})


def test_a_backstop_needs_enough_runs_and_drops_a_cost_it_cannot_measure():
    with pytest.raises(ValueError, match="needs 5"):
        pt.backstop_from_rows(_harness_rows([1, 2, 3, 4], [1, 1, 1, 1]), min_runs=5)
    with pytest.raises(ValueError, match="needs 2"):  # a standard deviation needs two, whatever min_runs says
        pt.backstop_from_rows(_harness_rows([1], [1]), min_runs=1)
    assert pt.backstop_from_rows(_harness_rows([1, 2, 3, 4, 5], [1, 1, None, 1, 1]), min_runs=5)["usd"] is None


def test_the_backstop_command_writes_the_class(tmp_path, monkeypatch):
    caps = tmp_path / "caps.json"
    caps.write_text(json.dumps({"agent_timeout": 7200, "tasks": {"P1": {"class": "lift"}},
                                "harness_backstop": {"min_runs": 2, "default": {"seconds": 86400, "usd": None},
                                                     "classes": {}}}))
    monkeypatch.setattr(pt, "CAPS", caps)
    runs = [write_run(tmp_path / str(i), timing={"agent_seconds": s, "agent_timeout": 0},
                      result={"total_cost_usd": c}, meta={"arm": "cadence-core", "backstop_source": "default"})
            for i, (s, c) in enumerate([(100.0, 1.0), (300.0, 3.0)])]
    assert pt.main(["backstop", "lift", *map(str, runs)]) == 0
    lift = json.loads(caps.read_text())["harness_backstop"]["classes"]["lift"]
    assert lift["seconds"] == 483 and lift["usd"] == 4.83 and lift["tasks"] == ["P1"]
    assert lift["from_runs"] == [str(r) for r in runs]
    with pytest.raises(SystemExit, match="set once and then fixed"):
        pt.main(["backstop", "lift", *map(str, runs)])
    assert pt.main(["backstop", "lift", "--replace", *map(str, runs)]) == 0


def test_the_backstop_command_refuses_a_class_no_task_has(tmp_path, monkeypatch):
    caps = tmp_path / "caps.json"
    caps.write_text(json.dumps({"agent_timeout": 7200, "tasks": {"P1": {}},
                                "harness_backstop": {"min_runs": 2, "default": {}, "classes": {}}}))
    monkeypatch.setattr(pt, "CAPS", caps)
    with pytest.raises(SystemExit, match="no task in caps.json has class 'lift'"):
        pt.main(["backstop", "lift", str(tmp_path)])


def test_a_harness_run_stopped_at_the_runners_guard_cap_is_an_infrastructure_error(tmp_path):
    """Section 5.3 gives a harness no guard cap; a cap the runner recorded and applied is not the arm's."""
    run = write_run(tmp_path, timing={"agent_exit": 124, "agent_seconds": 7203.0, "agent_timeout": 7200},
                    session=["2026-10-19T04:46:00.000Z", "2026-10-19T06:46:00.000Z"], meta={"arm": "cadence-core"})
    row = pt.summarize(run, PRICING)
    assert row["outcome"] == "infra_error" and row["counted"] is False


def test_a_spend_limit_stop_is_a_backstop_even_after_an_idle_spell(tmp_path):
    run = write_run(tmp_path, timing={"agent_exit": 1, "agent_seconds": 3000.0, "agent_timeout": 0,
                                      "agent_backstop": 9000},
                    result={"subtype": "error_max_budget_usd", "is_error": True},
                    session=["2026-10-20T10:00:00.000Z", "2026-10-20T10:10:00.000Z"], meta={"arm": "cadence-core"})
    assert pt.summarize(run, PRICING)["outcome"] == "backstop"


def test_a_harness_session_idle_long_before_its_backstop_is_a_stall(tmp_path):
    run = write_run(tmp_path, timing={"agent_exit": 124, "agent_seconds": 9001.0, "agent_timeout": 0,
                                      "agent_backstop": 9000},
                    session=["2026-10-20T10:00:00.000Z", "2026-10-20T10:20:00.000Z"], meta={"arm": "cadence-core"})
    assert pt.summarize(run, PRICING)["outcome"] == "api_stall"


def test_a_regrade_keeps_its_sources_backstop_record_and_stall(tmp_path):
    src = write_run(tmp_path / "a", timing={"agent_exit": 124, "agent_seconds": 9001.0, "agent_timeout": 0,
                                            "agent_backstop": 9000},
                    session=["2026-10-20T10:00:00.000Z", "2026-10-20T10:20:00.000Z"],
                    meta={"arm": "cadence-core", "harness": True, "backstop_source": "class lift"})
    regrade = write_run(tmp_path / "b", meta={"mode": "regrade", "regrade_of": str(src), "arm": "regrade"})
    row = pt.summarize(regrade, PRICING)
    assert row["outcome"] == "api_stall" and row["backstop_source"] == "class lift"


def test_a_regrade_of_an_infrastructure_error_is_not_counted(tmp_path):
    src = write_run(tmp_path / "a", meta={"arm": "cadence-core", "infra_error": "host guard"})
    regrade = write_run(tmp_path / "b", meta={"mode": "regrade", "regrade_of": str(src), "arm": "regrade"})
    row = pt.summarize(regrade, PRICING)
    assert row["outcome"] == "infra_error" and row["counted"] is False


def test_a_one_shot_killed_before_its_cap_is_graded_not_a_guard_cap_run(tmp_path):
    run = write_run(tmp_path, timing={"agent_exit": 137, "agent_seconds": 300.0},
                    session=["2026-10-15T10:00:00.000Z", "2026-10-15T10:05:00.000Z"])
    assert pt.summarize(run, PRICING)["outcome"] == "graded"


def test_an_infrastructure_error_is_marked_by_the_operator_and_not_counted(tmp_path):
    run = write_run(tmp_path, timing={"agent_exit": 137, "agent_seconds": 7203.0, "agent_timeout": 0},
                    meta={"arm": "cadence-core"})
    pt.main(["infra", str(run), "--reason", "host guard killed the session"])
    row = pt.summarize(run, PRICING)
    assert row["outcome"] == "infra_error" and row["infra_error"] == "host guard killed the session"
    assert row["counted"] is False and row["counts_as_model_failure"] is False


def test_a_run_with_no_timing_record_is_an_infrastructure_error(tmp_path):
    run = write_run(tmp_path)
    (run / "timing.json").unlink()
    row = pt.summarize(run, PRICING)
    assert row["outcome"] == "infra_error" and row["counted"] is False


def test_a_regrade_keeps_its_source_trials_arm(tmp_path):
    """A regrade's own arm is "regrade"; the guard-cap rule must read the source trial's."""
    src = write_run(tmp_path / "a", timing={"agent_exit": 124, "agent_seconds": 7200.0},
                    session=["2026-10-15T10:00:00.000Z", "2026-10-15T11:58:00.000Z"])
    regrade = write_run(tmp_path / "b", meta={"mode": "regrade", "regrade_of": str(src), "arm": "regrade"})
    assert pt.summarize(regrade, PRICING)["outcome"] == "guard_cap"


def _run_trial_cmd(tmp_path, monkeypatch, plugin_dir, caps, mode="agent", regrade_of=None):
    import sys
    import types

    def assemble(task, dest, with_reference=False):
        dest.mkdir(parents=True)
        return dest

    pipetask = types.ModuleType("pipetask")
    pipetask.assemble = types.SimpleNamespace(assemble=assemble)
    pipetask.bundle = types.SimpleNamespace(bundle=lambda dist: None)
    monkeypatch.setitem(sys.modules, "pipetask", pipetask)
    calls = []
    monkeypatch.setattr(pt.subprocess, "call", lambda cmd, env=None: calls.append(cmd) or 0)
    monkeypatch.setattr(pt, "repo_from_saved", lambda saved, out: out.mkdir(parents=True) or out)
    out = tmp_path / "out"
    pt.run_trial("P1", out, mode=mode, model="claude-haiku-5-5" if mode == "agent" else None, plugin_dir=plugin_dir,
                 replay_seed=0, caps=caps, regrade_of=regrade_of)
    return calls[0], json.loads((out / "trial.json").read_text())


def _flag(cmd, name):
    return cmd[cmd.index(name) + 1] if name in cmd else None


CAPS = {"agent_timeout": 7200, "tasks": {"P1": {"image": "img", "grader_timeout": 900}},
        "harness_backstop": {"min_runs": 5, "default": {"seconds": 86400, "usd": None},
                             "classes": {"lift": {"seconds": 9000, "usd": 4.5, "tasks": ["P1"]}}}}


def test_a_class_backstop_applies_only_to_the_tasks_it_was_measured_on():
    caps = json.loads(json.dumps(CAPS))
    caps["tasks"]["P2"] = {"image": "img", "grader_timeout": 900, "class": "lift"}  # joined the class later
    assert pt.harness_backstop(caps, "P2") == ({"seconds": 86400, "usd": None}, "default")


def test_a_kill_a_moment_short_of_the_cap_on_the_wall_clock_is_still_the_cap(tmp_path):
    run = write_run(tmp_path, timing={"agent_exit": 124, "agent_seconds": 7199.9},
                    session=["2026-10-15T10:00:00.000Z", "2026-10-15T11:59:00.000Z"])
    assert pt.summarize(run, PRICING)["outcome"] == "guard_cap"


def test_a_regrade_of_a_harness_trial_is_recorded_as_one_but_keeps_the_runners_cap(tmp_path, monkeypatch):
    src = write_run(tmp_path / "src", meta={"arm": "cadence-core", "harness": True})
    (src / "repo").mkdir()
    cmd, meta = _run_trial_cmd(tmp_path, monkeypatch, None, CAPS, mode="regrade", regrade_of=src)
    assert meta["harness"] is True
    assert _flag(cmd, "--agent-timeout") == "7200"  # the stub agent is not a harness session


def test_a_one_shot_gets_the_guard_cap_and_no_backstop(tmp_path, monkeypatch):
    cmd, meta = _run_trial_cmd(tmp_path, monkeypatch, None, CAPS)
    assert _flag(cmd, "--agent-timeout") == "7200" and "--agent-backstop" not in cmd and "--max-budget-usd" not in cmd
    assert meta["agent_timeout"] == 7200 and meta["backstop_seconds"] is None


@pytest.mark.parametrize("task_class, seconds, usd, source", [(None, "86400", None, "default"),
                                                              ("lift", "9000", "4.5", "class lift")])
def test_a_harness_arm_gets_its_class_backstop_or_the_default(tmp_path, monkeypatch, task_class, seconds, usd, source):
    caps = json.loads(json.dumps(CAPS))
    if task_class:
        caps["tasks"]["P1"]["class"] = task_class
    cmd, meta = _run_trial_cmd(tmp_path, monkeypatch, tmp_path / "cadence-core", caps)
    assert _flag(cmd, "--agent-timeout") == "0"
    assert (_flag(cmd, "--agent-backstop"), _flag(cmd, "--max-budget-usd")) == (seconds, usd)
    assert meta["agent_timeout"] is None and meta["backstop_source"] == source


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


def test_void_and_superseded_rows_are_kept_but_not_counted(tmp_path):
    """A void run (lost to a harness defect) and a run regraded later stay in the table, uncounted."""
    void = write_run(tmp_path / "v", grade={"reward": 0.0}, meta={"void": "grader deleted uncommitted work"})
    first = write_run(tmp_path / "f", grade={"reward": 0.0})
    regrade = write_run(tmp_path / "r", grade={"reward": 1.0, "passed": 7},
                        meta={"mode": "regrade", "regrade_of": str(first)})
    rows = {r["run_path"]: r for r in pt.summarize_all([void, first, regrade], PRICING)}
    v, f, r = rows[str(void)], rows[str(first)], rows[str(regrade)]
    assert v["outcome"] == "void" and v["void"] == "grader deleted uncommitted work"
    assert f["superseded_by"] == str(regrade)
    assert not v["counted"] and not f["counted"] and r["counted"]
    assert v["counts_as_model_failure"] is False and f["counts_as_model_failure"] is False
    assert r["counts_as_model_failure"] is False  # reward 1.0
    assert pt.counted_rows([v, f, r]) == [r]


def test_void_marks_a_run_with_its_reason(tmp_path):
    run = write_run(tmp_path, grade={"reward": 0.0})
    pt.main(["void", str(run), "--reason", "stopped by the operator"])
    assert json.loads((run / "trial.json").read_text())["void"] == "stopped by the operator"


def test_a_diagnostic_regrade_is_shown_but_never_counted(tmp_path):
    run = write_run(tmp_path, grade={"reward": 0.4286, "passed": 3},
                    meta={"diagnostic": "the map was edited by the operator"})
    row = pt.summarize_all([run], PRICING)[0]
    assert row["outcome"] == "diagnostic" and not row["counted"] and row["counts_as_model_failure"] is False


def test_a_regrade_repository_ignores_the_hosts_global_gitignore(tmp_path, monkeypatch):
    excludes = tmp_path / "global-ignore"
    excludes.write_text("*.py\n")
    config = tmp_path / "gitconfig"
    config.write_text(f"[core]\n\texcludesFile = {excludes}\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    saved = tmp_path / "run" / "repo"
    saved.mkdir(parents=True)
    (saved / "batch.py").write_text("print('x')\n")
    repo = pt.repo_from_saved(saved, tmp_path / "repo")
    assert subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True, text=True).stdout.split() == ["batch.py"]


@pytest.mark.parametrize("mark", [{"diagnostic": "the map was edited by the operator"},
                                  {"void": "stopped by the operator"}])
def test_a_regrade_that_is_not_counted_does_not_supersede_the_trial(tmp_path, mark):
    trial_run = write_run(tmp_path / "t", grade={"reward": 0.0})
    regrade = write_run(tmp_path / "r", grade={"reward": 1.0, "passed": 7},
                        meta={"mode": "regrade", "regrade_of": str(trial_run), **mark})
    rows = {r["run_path"]: r for r in pt.summarize_all([trial_run, regrade], PRICING)}
    assert rows[str(trial_run)]["counted"] and rows[str(trial_run)]["superseded_by"] is None
    assert not rows[str(regrade)]["counted"]
    assert pt.counted_rows(list(rows.values())) == [rows[str(trial_run)]]
