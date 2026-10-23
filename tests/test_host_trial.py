"""scripts/host_trial.py: the host-method trial loop.driver runs (batch F). Unit parts only; a trial needs Claude Code."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import host_trial  # noqa: E402


def test_without_the_drivers_prompt_it_refuses_to_start(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "HB_AGENT_PROMPT"}
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "host_trial.py"), "P1", "--out", str(tmp_path),
                           "--model", "m"], env=env, capture_output=True, text=True)
    assert proc.returncode == 2 and "HB_AGENT_PROMPT" in proc.stderr
    assert not (tmp_path / "repo").exists()


def test_the_agent_gets_its_own_session_and_not_this_repositorys_environment(monkeypatch, tmp_path):
    venv = str(ROOT / ".venv")
    monkeypatch.setenv("VIRTUAL_ENV", venv)
    monkeypatch.setenv("PATH", os.pathsep.join([f"{venv}/bin", "/usr/bin", str(ROOT / "scripts")]))
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "the-operators")
    monkeypatch.setenv("HB_AGENT_PROMPT", "/cadence /x/spec.md")
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", venv)
    env = host_trial.agent_env(tmp_path / "home", Path("/srv/plugin"))
    assert env["PATH"] == "/usr/bin"
    for name in ("VIRTUAL_ENV", "CLAUDE_CODE_SESSION_ID", "HB_AGENT_PROMPT", "UV_PROJECT_ENVIRONMENT"):
        assert name not in env
    assert env["HOME"] == str(tmp_path / "home") and env["CADENCE_HOME"] == "/srv/plugin"
    assert "CADENCE_HOME" not in host_trial.agent_env(tmp_path / "home", None)


def test_a_one_shot_gets_the_guard_cap_and_a_cadence_arm_only_the_backstop():
    """Criteria v2 section 5.3, runner/pipeline/caps.json: a one-shot stops at agent_timeout; a harness arm
    has no guard cap, only the backstop."""
    import json
    caps = json.loads((ROOT / "runner" / "pipeline" / "caps.json").read_text())
    assert host_trial.agent_cap(None) == caps["agent_timeout"] == 7200
    assert host_trial.agent_cap(Path("/srv/plugin")) == caps["harness_backstop"]["default"]["seconds"] == 86400
