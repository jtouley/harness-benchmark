"""tests/time_budget.py: a full run over its time budget fails; a subset or a local run only reports."""

from __future__ import annotations

import pytest

import time_budget

pytest_plugins = ["pytester"]

SUITE = """
import time

def test_fast():
    pass

def test_slow():
    time.sleep(0.3)
"""


@pytest.fixture
def suite(pytester, monkeypatch):
    monkeypatch.setattr(time_budget, "MIN_FULL_RUN", 2)
    pytester.makepyfile(SUITE)
    return pytester


def _run(pytester):
    return pytester.runpytest_inprocess("-p", "time_budget", "-p", "no:xdist", "-p", "no:cacheprovider")


def test_over_budget_fails_the_run_when_enforced(suite, monkeypatch):
    monkeypatch.setenv("HB_TEST_BUDGET", "1")
    monkeypatch.setenv("HB_TEST_SLOWEST_BUDGET", "0.1")
    result = _run(suite)
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.stdout.fnmatch_lines(["*TIME BUDGET EXCEEDED: slowest *s is over its budget of 0s*"])


def test_within_budget_passes(suite, monkeypatch):
    monkeypatch.setenv("HB_TEST_BUDGET", "1")
    result = _run(suite)
    assert result.ret == pytest.ExitCode.OK
    result.stdout.fnmatch_lines(["time budget: wall *s, total *s, slowest *s (*test_slow)"])


def test_not_enforced_without_the_flag(suite, monkeypatch):
    monkeypatch.delenv("HB_TEST_BUDGET", raising=False)
    monkeypatch.setenv("HB_TEST_SLOWEST_BUDGET", "0.1")
    assert _run(suite).ret == pytest.ExitCode.OK


def test_a_subset_is_measured_not_failed(suite, monkeypatch):
    monkeypatch.setattr(time_budget, "MIN_FULL_RUN", 3)
    monkeypatch.setenv("HB_TEST_BUDGET", "1")
    monkeypatch.setenv("HB_TEST_TOTAL_BUDGET", "0.1")
    assert _run(suite).ret == pytest.ExitCode.OK


def test_the_suite_runs_in_parallel_with_work_stealing():
    """Losing either one roughly doubled the wall time (2026-10-18)."""
    import tomllib
    from pathlib import Path

    addopts = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text())[
        "tool"]["pytest"]["ini_options"]["addopts"].split()
    assert "-n" in addopts and "--dist" in addopts
    assert addopts[addopts.index("--dist") + 1] == "worksteal"
