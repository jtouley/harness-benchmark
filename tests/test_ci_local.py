"""GitHub-hosted CI is off (billing blocks every hosted runner): verify.yml runs only by hand, and
scripts/ci_local.sh runs the steps of it that need no framework checkout, before each push."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = yaml.safe_load((ROOT / ".github" / "workflows" / "verify.yml").read_text(encoding="utf-8"))
SCRIPT = (ROOT / "scripts" / "ci_local.sh").read_text(encoding="utf-8")


def test_verify_runs_only_by_hand():
    triggers = WORKFLOW.get("on", WORKFLOW.get(True))  # PyYAML reads the key `on` as True
    assert list(triggers) == ["workflow_dispatch"]


def test_the_local_script_runs_the_test_and_report_steps_of_verify():
    steps = {s.get("name"): s for s in WORKFLOW["jobs"]["verify"]["steps"]}
    for name in ("Unit and pipeline tests", "Regenerate the report"):
        assert steps[name]["run"].strip() in SCRIPT, name
    assert 'HB_TEST_BUDGET=1' in SCRIPT and "git diff --exit-code results/" in SCRIPT


def test_the_local_script_is_executable_and_stops_on_the_first_failure():
    assert (ROOT / "scripts" / "ci_local.sh").stat().st_mode & 0o111
    assert "set -euo pipefail" in SCRIPT
