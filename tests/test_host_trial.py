"""scripts/host_trial.py: the host-method trial loop.driver runs (batch F). Unit parts only; a trial needs Claude Code."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

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


def test_a_batch_can_set_the_agent_cap(tmp_path):
    """Batch F caps the Cadence arm at 3 x the one-shot cap (21,600 s) instead of the 86,400 s backstop."""
    assert host_trial.agent_cap(Path("/srv/plugin"), 21600) == 21600
    assert host_trial.agent_cap(None, None) == 7200


@pytest.mark.parametrize("open_block, hard, expected", [
    ("A1", {"class": "a5-gap", "reason": "A5 vibe-test NOT READY"}, "A5"),   # run 20261023-P1-cadence-haiku-1-r2
    ("P4", {"class": "retries", "reason": "P4 failed three times"}, "P4"),   # a class that names no block
    ("A1", {"class": "retries", "reason": "A5 validate-gate fails after three vibe-test peer rounds: gap bodies "
                                          "cite another gap's A-n id"}, "A5"),  # 20261024-P1-cadence-haiku-it1-1-r2
    ("A1", {"class": "retries", "reason": "the gate failed three times"}, "A1"),  # no block anywhere: the open one
    ("A1", {"class": "retries", "reason": "AB5 is not a block"}, "A1"),
    ("E4", None, "E4"),
    (None, None, None),
])
def test_the_stop_is_the_block_where_the_hard_stop_started(open_block, hard, expected):
    """A hard stop sends the run back to A1, so headless `next` reports A1; the stop's class names the block
    that stopped it (review of #81), else a block id that opens its reason (`retries` names none)."""
    assert host_trial.stop_block(open_block, hard) == expected


def test_the_run_shape_goes_into_the_run_repos_cadence_config():
    """Two Cadence run shapes, compared head to head (owner, 2026-10-24): `--shape core|full` sets the run
    repo's .cadence.json `profile` (the key cadence PR 2 defines; coordinator to confirm). No shape, no key."""
    assert host_trial.cadence_config("core")["profile"] == "core"
    assert host_trial.cadence_config("full")["profile"] == "full"
    assert "profile" not in host_trial.cadence_config(None)
    assert host_trial.cadence_config("full")["adapter"] == "none"
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "host_trial.py"), "P1", "--out", "/tmp/x",
                           "--model", "m", "--shape", "medium"], capture_output=True, text=True)
    assert proc.returncode == 2 and "--shape" in proc.stderr


def test_nothing_for_a_verdict_judge_reaches_a_benchmark_run(monkeypatch, tmp_path):
    """Jev (the TypeSafe verdict judge) is not in the benchmark runs; nothing from a run leaves the machine
    (docs/rules.md, Owner's goals). Cadence main has no Jev path today; the agent's env keeps it that way."""
    monkeypatch.setenv("TYPESAFE_API_KEY", "fake")
    monkeypatch.setenv("TYPESAFE_URL", "https://example.invalid")
    env = host_trial.agent_env(tmp_path, Path("/srv/plugin"))
    assert not [k for k in env if k.startswith("TYPESAFE_")]


# Run 20261024-P2-cadence-haiku-core-1: stuck at R5 closure, the Stop hook refused the stop three times (transcript
# l.2061-2216), then the headless probe, run later in a copy with no live session, reported A1.
CORE_1_TAIL = [
    '{"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "Stop hook feedback:\\nBLOCKED '
    'early stop in review. Continue paceline: next R2 (test-benchmark-pr) via `/test-benchmark`"}]}}',
    '{"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "Stop hook feedback:\\nBLOCKED '
    'early stop in review. Continue paceline: next R5 (closure) via `python3 /x/plugin/scripts/closure.py`"}]}}',
    '{"type": "system", "subtype": "informational", "content": "Stop says: Cadence: stop refused 3 times \\u2014 '
    'escalate to user. Continue paceline: next R5 (closure) via `python3 /x/plugin/scripts/closure.py`"}',
]


def test_the_open_block_is_the_last_one_the_stop_hook_named():
    assert host_trial.open_block(CORE_1_TAIL) == {"block": "R5", "slug": "closure", "refused": 3}
    assert host_trial.open_block(CORE_1_TAIL[:1]) == {"block": "R2", "slug": "test-benchmark-pr", "refused": None}
    assert host_trial.open_block(['{"type": "result"}']) is None


@pytest.mark.parametrize("headless, hard, transcript, expected", [
    ("A1", None, CORE_1_TAIL, "R5"),                                        # the probe saw no session: the transcript wins
    ("A1", {"class": "a5-gap", "reason": "A5 vibe-test NOT READY"}, CORE_1_TAIL[:1], "A5"),  # a hard stop names its block
    ("E4", None, [], "E4"),                                                 # no Stop hook line: the probe's block
    (None, None, CORE_1_TAIL, None),                                        # the run finished: no stop at all
])
def test_the_stop_is_the_last_open_block_of_the_session(headless, hard, transcript, expected):
    stop = host_trial.choose_stop(headless, hard, host_trial.open_block(transcript), "FAIL  no active cadence session")
    assert stop["block"] == expected
    if expected == "R5":
        assert stop["reason"].startswith("open at R5 (closure): the Stop hook refused the stop 3 times")


def test_stop_only_needs_the_saved_run(tmp_path):
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "host_trial.py"), "P1", "--out", str(tmp_path),
                           "--model", "m", "--plugin-dir", str(tmp_path), "--stop-only"], capture_output=True, text=True)
    assert proc.returncode == 2 and "repo-as-left" in proc.stderr
