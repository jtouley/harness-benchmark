"""docs/experiments/2026-10-13-pilot: the run scripts run from their committed path, and the report matches its records."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "docs" / "experiments" / "2026-10-13-pilot"
REPORT = ROOT / "docs" / "experiments" / "2026-10-13-pilot.md"
RECORDED_WORKSPACE = "/Users/jasontouleyrou/Projects/cadence-wt/cadence-workspace"
ARMS = ("opus_oneshot", "cadence_haiku", "cadence_haiku_opus")

STUB_CLAUDE = """#!/usr/bin/env bash
if [ "${1:-}" = "--version" ]; then echo "9.9.9 (Claude Code)"; exit 0; fi
{ printf '%s\\n' "$@"; } > "$PWD/../stub_argv.txt"
echo '{"stub": true}'
"""

needs_tools = pytest.mark.skipif(not (shutil.which("bash") and shutil.which("git")), reason="needs bash and git")


@pytest.fixture
def stub_env(tmp_path: Path) -> dict[str, str]:
    """PATH with a stub `claude` (no API call), and a fake Cadence source with the recorded base config."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    claude = bin_dir / "claude"
    claude.write_text(STUB_CLAUDE)
    claude.chmod(0o755)
    cadence = tmp_path / "cadence-src"
    cadence.mkdir()
    base = json.loads((PILOT / "cadence_haiku" / "cadence.config.json").read_text())
    base.pop("peer_models")
    (cadence / "cadence.config.json").write_text(json.dumps(base, indent=2) + "\n")
    env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", ANTHROPIC_API_KEY="stub", CADENCE_SRC=str(cadence))
    return env


def _run_arm(arm: str, workspace: Path, env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["bash", str(PILOT / "run_arm.sh"), arm, str(workspace)],
                          cwd=cwd, env=env, capture_output=True, text=True, timeout=120)


@needs_tools
@pytest.mark.parametrize("arm", ARMS)
def test_run_arm_from_committed_path_reproduces_recorded_prompt_and_config(arm: str, tmp_path: Path, stub_env):
    workspace = tmp_path / "ws"
    proc = _run_arm(arm, workspace, stub_env, cwd=tmp_path)

    assert proc.returncode == 0, proc.stderr
    run = workspace / "pilot" / arm
    prompt = (run / "prompt.txt").read_text().replace(str(workspace), RECORDED_WORKSPACE)
    assert prompt == (PILOT / arm / "prompt.txt").read_text()
    if arm != "opus_oneshot":
        assert json.loads((run / "cadence" / "cadence.config.json").read_text()) == json.loads(
            (PILOT / arm / "cadence.config.json").read_text())
    provenance = json.loads((run / "provenance.json").read_text())
    assert provenance["claude_version"] == "9.9.9 (Claude Code)"
    assert "cadence_sha" in provenance


@needs_tools
def test_run_arm_refuses_an_existing_run_and_leaves_no_files_in_the_repo(tmp_path: Path, stub_env):
    workspace = tmp_path / "ws"
    assert _run_arm("opus_oneshot", workspace, stub_env, cwd=tmp_path).returncode == 0

    again = _run_arm("opus_oneshot", workspace, stub_env, cwd=tmp_path)

    assert again.returncode == 1
    assert "exists:" in again.stderr
    assert not (ROOT / "docs" / "experiments" / "pilot").exists()


@pytest.mark.parametrize("script", ["run_arm.sh", "grade_arm.sh"])
def test_pilot_scripts_hard_code_no_machine_path(script: str):
    text = (PILOT / script).read_text()

    assert "/Users/" not in text
    assert "harness-benchmark-wt" not in text


def _report_rows() -> dict[str, list[str]]:
    rows = {}
    for line in REPORT.read_text().splitlines():
        m = re.match(r"\| `(\w+)` \|", line)
        if m and m.group(1) in ARMS and "$" in line:
            rows[m.group(1)] = [c.strip() for c in line.strip("|").split("|")]
    return rows


@pytest.mark.parametrize("arm", ARMS)
def test_pilot_report_cost_and_time_match_the_committed_records(arm: str):
    row = _report_rows()[arm]
    cost = json.loads((PILOT / arm / "cost.json").read_text())
    seconds = json.loads((PILOT / arm / "timing.json").read_text())["total_duration_seconds"]

    reported_cost = Decimal(re.search(r"\$(\d+\.\d\d)", row[5]).group(1))
    assert reported_cost == Decimal(cost["usd_total"]).quantize(Decimal("0.01"))
    reported_seconds = int(re.search(r"([\d,]+) s", row[4]).group(1).replace(",", ""))
    assert reported_seconds == round(seconds)
