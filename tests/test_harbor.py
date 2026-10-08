"""The generated Harbor tasks follow the lockfile, hide the tests, and stay in sync."""

from __future__ import annotations

import re
from pathlib import Path

from cbench import harbor
from cbench.lock import load_lock


def test_every_arm_and_task_is_generated(tmp_path):
    lock = load_lock()
    paths = harbor.generate(out=tmp_path)
    assert len(paths) == len(lock.frameworks) * 3
    assert {p.name for p in paths} >= {"t01-slugify-bugfix--baseline", "t03-token-bucket--cadence"}


def test_hidden_tests_never_enter_the_image(tmp_path):
    for task in harbor.generate(out=tmp_path):
        env = task / "environment"
        assert not list(env.rglob("*hidden*")), task
        assert (task / "tests" / "hidden").is_dir()
        assert "hidden" not in (task / "instruction.md").read_text().lower()


def test_dockerfile_pins_the_lockfile_sha_and_runs_its_install_ops(tmp_path):
    lock = load_lock()
    for task in harbor.generate(arms=[a for a in lock.frameworks if a != "baseline"], tasks=["T01-slugify-bugfix"], out=tmp_path):
        arm = task.name.split("--")[1]
        fw = lock.frameworks[arm]
        text = (task / "environment" / "Dockerfile").read_text()
        assert fw.sha in text and fw.repo in text, arm
        for op in fw.install:
            if op["op"] == "run":
                assert harbor.sub(op["argv"][0]) in text, (arm, op)


def test_baseline_installs_no_framework(tmp_path):
    (task,) = harbor.generate(arms=["baseline"], tasks=["T01-slugify-bugfix"], out=tmp_path)
    text = (task / "environment" / "Dockerfile").read_text()
    assert "/opt/fw" not in text and "FETCH_HEAD" not in text


def test_committed_tasks_are_in_sync():
    assert harbor.check() == 0


def test_collect_reads_harbor_results(tmp_path):
    trial = tmp_path / "job1" / "t01-slugify-bugfix--cadence__abc"
    trial.mkdir(parents=True)
    (trial / "result.json").write_text(
        '{"task_name": "harness-benchmark/t01-slugify-bugfix--cadence", "trial_name": "x",'
        ' "config": {"agent": {"model_name": "anthropic/claude-haiku-5-5"}},'
        ' "agent_result": {"n_input_tokens": 100, "n_cache_tokens": 40, "n_output_tokens": 7, "cost_usd": 0.01},'
        ' "verifier_result": {"rewards": {"reward": 1.0, "tests_passed": 13, "tests_total": 13}}}')
    (t,) = harbor.collect(tmp_path)["trials"]
    assert (t["task"], t["arm"], t["reward"], t["cost_usd"]) == ("t01-slugify-bugfix", "cadence", 1.0, 0.01)


def test_agent_hook_matches_harbor():
    """The subclass keys on a command Harbor builds; if a Harbor upgrade changes it, fail here."""
    import inspect
    import sys

    import pytest

    pytest.importorskip("harbor", reason="harbor is only needed for the live tier")
    from harbor.agents.installed.claude_code import ClaudeCode

    sys.path.insert(0, str(harbor.HARBOR_DIR / "agents"))
    try:
        import cbench_claude
    finally:
        sys.path.pop(0)
    assert cbench_claude.SETUP_MARKER in inspect.getsource(ClaudeCode.run)
    assert 'CLAUDE_CONFIG_DIR"] = (self.environment_logs_dir / "sessions")' in inspect.getsource(ClaudeCode.run)
