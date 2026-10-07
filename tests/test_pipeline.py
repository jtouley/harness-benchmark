"""Integration tests: golden tasks, the live pipeline with a scripted agent, report determinism.

These use the canonical sandbox root, so they need `python -m cbench fetch baseline`
(no network for baseline) and must not run concurrently with other cbench commands.
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
    for mod in ("cbench.grade", "cbench.live", "cbench.report"):
        importlib.reload(importlib.import_module(mod))
    yield tmp_path / "results"
    monkeypatch.delenv("CBENCH_RESULTS")
    importlib.reload(cbench.util)
    for mod in ("cbench.grade", "cbench.live", "cbench.report"):
        importlib.reload(importlib.import_module(mod))


def test_golden_tasks_are_valid():
    from cbench.grade import golden_check

    data = golden_check()
    assert data["tasks"], "no golden tasks found"
    for name, row in data["tasks"].items():
        assert row["valid"], name


def test_live_pipeline_with_scripted_agent_regrades_identically(scratch_results):
    from cbench import __main__ as cli
    from cbench.grade import regrade_all
    from cbench.util import canonical_json

    fake = str(BENCH / "tests" / "fake_agent.py")
    code = cli.main(["live", "--frameworks", "baseline", "--tasks", "T01-slugify-bugfix", "--trials", "1",
                     "--agent-cmd", fake, "--model", "claude-sonnet-5-5", "--yes"])
    assert code == 0
    record = json.loads((scratch_results / "runs/baseline/T01-slugify-bugfix/trial-01/record.json").read_text())
    assert record["files_changed"] == ["textkit/slug.py"]

    first = regrade_all()
    second = regrade_all()
    assert canonical_json(first) == canonical_json(second)
    run = first["runs"][0]
    assert run["resolved"] is True
    assert all(run["integrity"].values())
    assert run["cost_usd"] == "0.030700"


def test_tampered_patch_is_detected(scratch_results):
    from cbench import __main__ as cli
    from cbench.grade import regrade_all

    fake = str(BENCH / "tests" / "fake_agent.py")
    cli.main(["live", "--frameworks", "baseline", "--tasks", "T03-token-bucket", "--trials", "1",
              "--agent-cmd", fake, "--model", "claude-sonnet-5-5", "--yes"])
    patch = scratch_results / "runs/baseline/T03-token-bucket/trial-01/patch.diff"
    patch.write_text(patch.read_text().replace("self._tokens -= n", "self._tokens -= 0"))
    run = regrade_all()["runs"][0]
    assert run["integrity"]["patch"] is False
    assert run["resolved"] is False


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
