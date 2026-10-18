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
def suite(pytester):
    pytester.makepyfile(SUITE)
    return pytester


def _run(pytester, *args):
    return pytester.runpytest_inprocess("-p", "time_budget", "-p", "no:xdist", "-p", "no:cacheprovider", *args)


def test_over_budget_fails_the_run_when_enforced(suite, monkeypatch):
    monkeypatch.setenv("HB_TEST_BUDGET", "1")
    monkeypatch.setenv("HB_TEST_TOTAL_BUDGET", "0.1")
    result = _run(suite)
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.stdout.fnmatch_lines(["*TIME BUDGET EXCEEDED: total *s is over its budget of 0s*"])


def test_within_budget_passes(suite, monkeypatch):
    monkeypatch.setenv("HB_TEST_BUDGET", "1")
    result = _run(suite)
    assert result.ret == pytest.ExitCode.OK
    result.stdout.fnmatch_lines(["time budget: wall *s, total *s, slowest *s (*test_slow); enforced: wall 55s, total 190s"])


def test_not_enforced_without_the_flag(suite, monkeypatch):
    monkeypatch.delenv("HB_TEST_BUDGET", raising=False)
    monkeypatch.setenv("HB_TEST_TOTAL_BUDGET", "0.1")
    result = _run(suite)
    assert result.ret == pytest.ExitCode.OK
    result.stdout.fnmatch_lines(["*; not enforced (HB_TEST_BUDGET is not 1)"])


@pytest.mark.parametrize("selection", [["test_a_subset_is_measured_not_failed.py"], ["-k", "slow"], ["-m", "not x"]])
def test_a_subset_is_measured_not_failed(suite, monkeypatch, selection):
    monkeypatch.setenv("HB_TEST_BUDGET", "1")
    monkeypatch.setenv("HB_TEST_TOTAL_BUDGET", "0.1")
    result = _run(suite, *selection)
    assert result.ret in (pytest.ExitCode.OK, pytest.ExitCode.NO_TESTS_COLLECTED)
    result.stdout.fnmatch_lines(["*; not enforced (a subset of tests was selected)"])


def test_the_slowest_test_is_reported_not_budgeted():
    assert set(time_budget.BUDGETS) == {"wall", "total"}


def test_the_suite_runs_in_parallel_with_work_stealing():
    """Losing either one roughly doubled the wall time (2026-10-18)."""
    import tomllib
    from pathlib import Path

    addopts = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text())[
        "tool"]["pytest"]["ini_options"]["addopts"].split()
    assert "-n" in addopts and "--dist" in addopts
    assert addopts[addopts.index("--dist") + 1] == "worksteal"
