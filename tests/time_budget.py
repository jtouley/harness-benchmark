"""Test-suite time budget: a run that gets much slower fails, so a slowdown cannot merge unseen.

Three measures, printed after every run:
- wall: seconds from session start to finish. Catches lost parallelism or poor scheduling.
- total: the sum of every test's setup, call and teardown. Catches tests getting slower across the
  board (a sleep in a shared helper), whatever the number of workers.
- slowest: the slowest single test. Reported only: the slowest tests fetch pinned tools, so their time
  varies with the network and would make a budget flaky.

With HB_TEST_BUDGET=1 (CI sets it), wall or total over its budget fails the run. The budgets sit
about 1.4 times above a typical CI run: tight enough that a doubling, or one slow shared helper,
fails, and loose enough for CI's run-to-run spread (about 2%). A run that selects tests (paths on the
command line, -k, -m, --deselect, --lf, --ignore) is only measured, never failed; the summary line
says which. Set
HB_TEST_WALL_BUDGET or HB_TEST_TOTAL_BUDGET to override a budget in seconds, for a slower machine.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict

import pytest

# CI on ubuntu-latest, 18 October 2026: four runs at wall 38.7-40.0 s, total 143-147 s (one earlier
# run was faster: 28.5 s, 97.1 s). Restoring the 5 s replay keepalive in the pipeline tests adds about
# 90 s of total time, so a looser total budget (2x, 290 s) would miss that regression.
BUDGETS = {"wall": 55.0, "total": 190.0}


def selects_tests(config: pytest.Config) -> bool:
    """True when the run is a chosen subset, not the whole suite."""
    o = config.option
    return (config.args_source == pytest.Config.ArgsSource.ARGS or bool(o.keyword) or bool(o.markexpr)
            or bool(getattr(o, "deselect", None)) or bool(getattr(o, "lf", False))
            or bool(getattr(o, "ignore", None)) or bool(getattr(o, "ignore_glob", None)))


class TimeBudget:
    def __init__(self, config: pytest.Config) -> None:
        self.config = config
        self.start = time.monotonic()
        self.per_test: dict[str, float] = defaultdict(float)
        self.measures: dict[str, float] = {}
        self.status = ""
        self.over: list[str] = []

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        self.per_test[report.nodeid] += report.duration

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        slowest = max(self.per_test.items(), key=lambda kv: kv[1], default=("", 0.0))
        self.measures = {"wall": time.monotonic() - self.start, "total": sum(self.per_test.values()),
                         "slowest": slowest[1]}
        self.slowest_id = slowest[0]
        if os.environ.get("HB_TEST_BUDGET") != "1":
            self.status = "not enforced (HB_TEST_BUDGET is not 1)"
            return
        if selects_tests(self.config):
            self.status = "not enforced (a subset of tests was selected)"
            return
        budgets = {name: float(os.environ.get(f"HB_TEST_{name.upper()}_BUDGET", value))
                   for name, value in BUDGETS.items()}
        self.status = "enforced: " + ", ".join(f"{n} {b:.0f}s" for n, b in budgets.items())
        self.over = [f"{n} {self.measures[n]:.1f}s is over its budget of {b:.0f}s"
                     for n, b in budgets.items() if self.measures[n] > b]
        if self.over and session.exitstatus == pytest.ExitCode.OK:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED

    def pytest_terminal_summary(self, terminalreporter) -> None:
        if not self.measures:
            return
        m = self.measures
        terminalreporter.write_line(f"time budget: wall {m['wall']:.1f}s, total {m['total']:.1f}s, "
                                    f"slowest {m['slowest']:.1f}s ({self.slowest_id}); {self.status}")
        for line in self.over:
            terminalreporter.write_line(f"TIME BUDGET EXCEEDED: {line}", red=True, bold=True)


def pytest_configure(config: pytest.Config) -> None:
    if not hasattr(config, "workerinput"):  # the xdist controller sees every worker's reports
        config.pluginmanager.register(TimeBudget(config), "time-budget")
