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


def test_the_fresh_home_gets_exactly_what_the_auth_route_needs(tmp_path):
    """proxy (this host): the proxy adds the credentials, so HOME gets no credential file. oauth-file (the
    owner's machine): HOME gets the one OAuth file, mode 0600, and nothing else."""
    proxy_home, oauth_home = tmp_path / "p", tmp_path / "o"
    proxy_home.mkdir()
    oauth_home.mkdir()
    source = tmp_path / "operator" / ".credentials.json"
    source.parent.mkdir()
    source.write_text('{"claudeAiOauth": "fake"}')
    host_trial.prepare_home(proxy_home, "proxy", None)
    assert sorted(p.relative_to(proxy_home).as_posix() for p in proxy_home.rglob("*")) == []
    host_trial.prepare_home(oauth_home, "oauth-file", source)
    files = sorted(p.relative_to(oauth_home).as_posix() for p in oauth_home.rglob("*") if p.is_file())
    assert files == [".claude/.credentials.json"]
    assert (oauth_home / ".claude" / ".credentials.json").read_text() == source.read_text()
    assert (oauth_home / ".claude" / ".credentials.json").stat().st_mode & 0o777 == 0o600


def test_the_agent_environment_carries_no_api_key_or_token(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "fake")
    env = host_trial.agent_env(tmp_path, None)
    assert "ANTHROPIC_API_KEY" not in env and "ANTHROPIC_AUTH_TOKEN" not in env


def test_the_grader_runs_from_the_task_repository_as_in_the_container(tmp_path):
    """oracle.py allows DuckDB the repository's out/marts/ by absolute path; an oracle_map that names
    `out/marts/...` resolves against the grader's working directory. The container runner grades from
    /trial/repo; host_trial graded from golden/pipeline, so every relative path was refused (run
    20261023-P1-oneshot-haiku-1: 0/7 here, 5/7 from the repository)."""
    argv, cwd, env = host_trial.grade_command(tmp_path / "repo", tmp_path / "out")
    assert cwd == tmp_path / "repo"
    assert env["PYTHONPATH"].split(os.pathsep)[0] == str(host_trial.GP)
    for flag in ("--key", "--capture"):
        assert Path(argv[argv.index(flag) + 1]).is_absolute()
    assert argv[argv.index("--repo") + 1] == str(tmp_path / "repo")
