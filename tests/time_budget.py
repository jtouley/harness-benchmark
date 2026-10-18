"""Test-suite time budget: a run that gets much slower fails, so a slowdown cannot merge unseen.

Three measures, printed after every full run:
- wall: seconds from session start to finish. Catches lost parallelism or poor scheduling.
- total: the sum of every test's setup, call and teardown. Catches tests getting slower across the
  board (a sleep in a shared helper), whatever the number of workers.
- slowest: the slowest single test.

With HB_TEST_BUDGET=1 (CI sets it), a measure over its budget fails the run. The budgets are below
twice what CI measures, so a doubling fails. A run of fewer than MIN_FULL_RUN tests is a subset
(one file, -k) and is only measured, never failed. HB_TEST_WALL_BUDGET, HB_TEST_TOTAL_BUDGET and
HB_TEST_SLOWEST_BUDGET override a budget in seconds, for a slower machine.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict

import pytest

BUDGETS = {"wall": 90.0, "total": 270.0, "slowest": 20.0}
MIN_FULL_RUN = 600


class TimeBudget:
    def __init__(self) -> None:
        self.start = time.monotonic()
        self.per_test: dict[str, float] = defaultdict(float)
        self.measures: dict[str, float] = {}
        self.over: list[str] = []

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        self.per_test[report.nodeid] += report.duration

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        slowest = max(self.per_test.items(), key=lambda kv: kv[1], default=("", 0.0))
        self.measures = {"wall": time.monotonic() - self.start, "total": sum(self.per_test.values()),
                         "slowest": slowest[1]}
        self.slowest_id = slowest[0]
        if os.environ.get("HB_TEST_BUDGET") != "1" or len(self.per_test) < MIN_FULL_RUN:
            return
        for name, value in self.measures.items():
            budget = float(os.environ.get(f"HB_TEST_{name.upper()}_BUDGET", BUDGETS[name]))
            if value > budget:
                self.over.append(f"{name} {value:.1f}s is over its budget of {budget:.0f}s")
        if self.over and session.exitstatus == pytest.ExitCode.OK:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED

    def pytest_terminal_summary(self, terminalreporter) -> None:
        if not self.measures:
            return
        m = self.measures
        terminalreporter.write_line(f"time budget: wall {m['wall']:.1f}s, total {m['total']:.1f}s, "
                                    f"slowest {m['slowest']:.1f}s ({self.slowest_id})")
        for line in self.over:
            terminalreporter.write_line(f"TIME BUDGET EXCEEDED: {line}", red=True, bold=True)


def pytest_configure(config: pytest.Config) -> None:
    if not hasattr(config, "workerinput"):  # the xdist controller sees every worker's reports
        config.pluginmanager.register(TimeBudget(), "time-budget")
