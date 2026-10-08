"""Integration tests: golden tasks and report determinism.

"""

from __future__ import annotations

import importlib
import json
import shutil
from pathlib import Path

import pytest

BENCH = Path(__file__).resolve().parents[1]


@pytest.fixture
def scratch_results(tmp_path, monkeypatch):
    monkeypatch.setenv("CBENCH_RESULTS", str(tmp_path / "results"))
    import cbench.util

    importlib.reload(cbench.util)
    for mod in ("cbench.grade", "cbench.report"):
        importlib.reload(importlib.import_module(mod))
    yield tmp_path / "results"
    monkeypatch.delenv("CBENCH_RESULTS")
    importlib.reload(cbench.util)
    for mod in ("cbench.grade", "cbench.report"):
        importlib.reload(importlib.import_module(mod))


def test_golden_tasks_are_valid():
    from cbench.grade import golden_check

    data = golden_check()
    assert data["tasks"], "no golden tasks found"
    for name, row in data["tasks"].items():
        assert row["valid"], name


def test_report_is_a_pure_function_of_results(tmp_path):
    from cbench.report import render

    src = BENCH / "results"
    if not (src / "footprint.json").is_file():
        pytest.skip("results not generated")
    for name in ("footprint.json", "probes.json", "golden.json", "install.json"):
        if (src / name).is_file():
            shutil.copy(src / name, tmp_path / name)
    assert render(tmp_path) == render(tmp_path)
    assert render(tmp_path) == (src / "REPORT.md").read_text()
