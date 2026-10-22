"""GitHub-hosted CI is off (billing blocks every hosted runner): verify.yml runs only by hand, and
scripts/ci_local.sh runs its steps on this machine before each push."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = yaml.safe_load((ROOT / ".github" / "workflows" / "verify.yml").read_text(encoding="utf-8"))
SCRIPT_PATH = ROOT / "scripts" / "ci_local.sh"
SCRIPT = SCRIPT_PATH.read_text(encoding="utf-8")
STEPS = [s for s in WORKFLOW["jobs"]["verify"]["steps"] if "run" in s]


def test_verify_runs_only_by_hand():
    triggers = WORKFLOW.get("on", WORKFLOW.get(True))  # PyYAML reads the key `on` as True
    assert list(triggers) == ["workflow_dispatch"]


def _command(run: str) -> str:
    """A one-line run: step with the workflow's expressions written as the script's variables."""
    return re.sub(r"\$\{\{ steps\.access\.outputs\.(\w+) \}\}", lambda m: f'${m.group(1).upper()}', run.strip())


def drift(steps: list[dict], script: str) -> list[str]:
    """Each run: step of the workflow with no `== <name>` section, or a one-line command that differs."""
    problems = []
    for step in steps:
        name = step.get("name") or step["run"].strip()
        if f"== {name}" not in script:
            problems.append(f"no '== {name}' section in scripts/ci_local.sh")
        elif "\n" not in step["run"].strip() and _command(step["run"]) not in script:
            problems.append(f"{name}: the command differs from verify.yml")
    return problems


def test_every_run_step_of_verify_is_in_the_local_script():
    assert drift(STEPS, SCRIPT) == []


def test_a_new_or_changed_run_step_fails_the_drift_check():
    assert drift([*STEPS, {"name": "Lint", "run": "uv run ruff check ."}], SCRIPT) == [
        "no '== Lint' section in scripts/ci_local.sh"]
    changed = [{**s, "run": s["run"] + " --strict"} if s.get("name") == "Regenerate the report" else s for s in STEPS]
    assert drift(changed, SCRIPT) == ["Regenerate the report: the command differs from verify.yml"]


def test_the_local_script_is_executable_stops_on_the_first_failure_and_prints_its_budget():
    assert SCRIPT_PATH.stat().st_mode & 0o111
    assert "set -euo pipefail" in SCRIPT
    assert "HB_TEST_WALL_BUDGET" in SCRIPT and "HB_TEST_TOTAL_BUDGET" in SCRIPT and "budget:" in SCRIPT


def test_the_local_budget_is_the_ci_budget_times_the_documented_factor():
    env = {**os.environ, "CI_LOCAL_ONLY_BUDGET": "1"}
    env.pop("HB_TEST_WALL_BUDGET", None)
    env.pop("HB_TEST_TOTAL_BUDGET", None)
    out = subprocess.run([str(SCRIPT_PATH)], env=env, capture_output=True, text=True, check=True).stdout
    assert "budget: wall 110 s, total 380 s (2 x the CI budget of wall 55 s, total 190 s)" in out
    env.update(HB_TEST_WALL_BUDGET="70", HB_TEST_TOTAL_BUDGET="300")
    out = subprocess.run([str(SCRIPT_PATH)], env=env, capture_output=True, text=True, check=True).stdout
    assert "budget: wall 70 s, total 300 s (set in the environment)" in out


def test_skipped_steps_are_printed_with_why():
    for marker in ("skipped:", "uv run --frozen --with tokenizers python -m cbench verify"):
        assert marker in SCRIPT
