"""Isolated runner (runner/): one disposable container per trial, with its own Docker daemon.

The Docker tests build the runner image and run stub trials (no API call, no cost). They run only with
HB_RUNNER_DOCKER_TESTS=1, one container at a time. Every container they create is labelled
`hb.runner` and removed; they never list or touch other containers, images or volumes.
"""
from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import time
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "runner"
RUN_TRIAL = RUNNER / "run_trial.sh"
FIXTURES = Path(__file__).resolve().parent / "runner_fixtures"
IMAGE = os.environ.get("HB_RUNNER_IMAGE", "harness-benchmark/runner:local")
PROBE_IMAGE = "alpine:latest"
FAKE_KEY = "sk-ant-fake-" + uuid.uuid4().hex

docker_tests = pytest.mark.skipif(
    os.environ.get("HB_RUNNER_DOCKER_TESTS") != "1",
    reason="builds an image and runs privileged containers; set HB_RUNNER_DOCKER_TESTS=1",
)


def sh(*args: str, check: bool = True, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), capture_output=True, text=True, check=check, **kw)


# --- without Docker -------------------------------------------------------------------------------

def test_help_documents_every_input():
    out = sh(str(RUN_TRIAL), "--help").stdout
    for flag in ("--repo", "--prompt", "--grader", "--out", "--model", "--plugin-dir", "--suffix"):
        assert flag in out


@pytest.mark.parametrize("args", [[], ["--repo", "/nonexistent"], ["--bogus"]])
def test_bad_arguments_fail_before_docker_is_called(args, tmp_path):
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    (tmp_path / "docker").write_text("#!/bin/sh\necho docker-called >&2\nexit 99\n")
    (tmp_path / "docker").chmod(0o755)
    r = sh(str(RUN_TRIAL), *args, check=False, env=env)
    assert r.returncode == 2
    assert "docker-called" not in r.stderr


def test_api_key_reaches_the_container_only_through_stdin():
    """The key is never an argument (visible in `ps`) or container configuration (`docker inspect`)."""
    lines = [ln for ln in RUN_TRIAL.read_text().splitlines()
             if "ANTHROPIC_API_KEY" in ln and not ln.lstrip().startswith("#")]
    assert lines == ["printf '%s\\n' \"${ANTHROPIC_API_KEY:-}\" | docker start --attach --interactive "
                     "\"$NAME\" >\"$OUT/runner.log\" 2>&1 &"]
    assert "ANTHROPIC_API_KEY" not in (RUNNER / "Dockerfile").read_text()


# --- with Docker ----------------------------------------------------------------------------------

def vm_process_count(marker: str) -> int:
    """Processes in the Docker VM whose command line holds `marker` (counted, never printed)."""
    r = sh("docker", "run", "--rm", "--label", "hb.runner=probe", "--pid=host", PROBE_IMAGE,
           "sh", "-c", f"ps -o args | grep -c '[{marker[0]}]{marker[1:]}' || true")
    return int(r.stdout.strip())


def make_task(tmp_path: Path, tag: str, hold: bool) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "TAG").write_text(tag)
    if hold:
        (repo / "HOLD").write_text("")
    git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
    sh(*git[:3], "init", "-q", "-b", "main")
    sh(*git, "add", "-A")
    sh(*git, "commit", "-qm", "base")
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Do the task.")
    return repo, prompt


def start_trial(tmp_path: Path, name: str, repo: Path, prompt: Path) -> subprocess.Popen:
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    env["ANTHROPIC_API_KEY"] = FAKE_KEY
    return subprocess.Popen(
        [str(RUN_TRIAL), "--repo", str(repo), "--prompt", str(prompt), "--suffix", "Be brief.",
         "--grader", str(FIXTURES / "stub_grader.sh"), "--agent-cmd", str(FIXTURES / "stub_agent.sh"),
         "--model", "stub-model", "--out", str(tmp_path / "out"), "--name", name, "--image", IMAGE],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )


def wait_for(predicate, seconds: float = 120) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(1)
    return False


def container_exists(name: str) -> bool:
    return bool(sh("docker", "ps", "-a", "-q", "--filter", f"name=^{name}$").stdout.strip())


def volume_exists(volume: str) -> bool:
    return sh("docker", "volume", "inspect", volume, check=False).returncode == 0


def host_processes_naming(name: str) -> int:
    return len(sh("pgrep", "-f", name, check=False).stdout.split())


@pytest.fixture(scope="module")
def image():
    sh("docker", "build", "-q", "-t", IMAGE, str(RUNNER), timeout=1800)
    return IMAGE


@docker_tests
def test_image_carries_the_trial_toolchain(image):
    r = sh("docker", "run", "--rm", "--label", "hb.runner=probe", "--entrypoint", "bash", image, "-c",
           "uname -m; claude --version; uv --version; dockerd --version; docker compose version; "
           "python3 --version; git --version")
    host_arch = sh("uname", "-m").stdout.strip()
    first = r.stdout.splitlines()[0]
    assert first == {"arm64": "aarch64"}.get(host_arch, host_arch)
    assert "(Claude Code)" in r.stdout and "uv " in r.stdout and "Docker Compose" in r.stdout


@docker_tests
def test_trial_runs_inside_one_container_and_leaves_only_its_outputs(image, tmp_path):
    tag = uuid.uuid4().hex[:12]
    name = f"hb-trial-test-{tag}"
    repo, prompt = make_task(tmp_path, tag, hold=True)
    proc = start_trial(tmp_path, name, repo, prompt)
    try:
        # While the trial holds: the inner service and the agent's background process are running.
        assert wait_for(lambda: vm_process_count(f"hb-stray-{tag}") == 1), "agent process not seen"
        assert wait_for(lambda: vm_process_count(f"hbmarker-{tag}") == 1), "inner service not seen"
        info = json.loads(sh("docker", "inspect", name).stdout)[0]
        assert FAKE_KEY not in json.dumps(info), "API key is in the container configuration"
        assert info["HostConfig"]["Binds"] in (None, []), "the trial must not mount host paths"
        volumes = [m["Name"] for m in info["Mounts"] if m["Type"] == "volume"]
        assert [m["Destination"] for m in info["Mounts"]] == ["/var/lib/docker"]
        sh("docker", "exec", name, "touch", "/tmp/release")
        _, err = proc.communicate(timeout=300)
    finally:
        if proc.poll() is None:
            proc.kill()
    assert proc.returncode == 0, err

    out = tmp_path / "out"
    result = json.loads((out / "result.json").read_text())
    grade = json.loads((out / "grade.json").read_text())
    timing = json.loads((out / "timing.json").read_text())
    # The agent got the key, the model and the prompt with the arm's suffix.
    assert result["key_sha256"] == hashlib.sha256(FAKE_KEY.encode()).hexdigest()
    assert result["model"] == "stub-model"
    assert result["grader_visible"] is False
    assert result["prompt_sha256"] == hashlib.sha256(b"Do the task. Be brief.").hexdigest()
    # The grader saw the inner service, no agent process, no key, and the agent's commit.
    assert grade == {"inner_service_running": True, "inner_service_body": f"served-{tag}",
                     "agent_processes_left": 0, "grader_sees_api_key": False, "commits": 2}
    assert timing["agent_exit"] == 0 and timing["leftover_agent_processes_killed"] >= 1
    assert (out / "agent" / "summary.md").read_text() == "stub summary\n"
    # The key is in no output; the host repository is untouched.
    for f in out.rglob("*"):
        if f.is_file():
            assert FAKE_KEY not in f.read_text(errors="replace"), f
    assert not (repo / "answer.txt").exists()

    # Nothing is left: container, its volume, the inner service, the agent's process, host processes.
    assert not container_exists(name)
    assert volumes and not any(volume_exists(v) for v in volumes)
    assert vm_process_count(f"hbmarker-{tag}") == 0
    assert vm_process_count(f"hb-stray-{tag}") == 0
    assert host_processes_naming(name) == 0


@docker_tests
def test_interrupted_trial_is_deleted_with_everything_it_started(image, tmp_path):
    tag = uuid.uuid4().hex[:12]
    name = f"hb-trial-test-{tag}"
    repo, prompt = make_task(tmp_path, tag, hold=True)
    proc = start_trial(tmp_path, name, repo, prompt)
    try:
        assert wait_for(lambda: vm_process_count(f"hbmarker-{tag}") == 1), "inner service not seen"
        volumes = [m["Name"] for m in json.loads(sh("docker", "inspect", name).stdout)[0]["Mounts"]]
        proc.send_signal(signal.SIGTERM)
        proc.communicate(timeout=120)
    finally:
        if proc.poll() is None:
            proc.kill()
    assert proc.returncode != 0
    assert not container_exists(name)
    assert not any(volume_exists(v) for v in volumes)
    assert vm_process_count(f"hbmarker-{tag}") == 0
    assert vm_process_count(f"hb-stray-{tag}") == 0
    assert host_processes_naming(name) == 0


@docker_tests
def test_default_agent_starts_claude_code_with_the_arms_plugin_and_no_key(image, tmp_path):
    """No key is given, so Claude Code stops at login: no API request is made."""
    repo, prompt = make_task(tmp_path, uuid.uuid4().hex[:12], hold=False)
    grader = tmp_path / "grader.sh"
    grader.write_text('#!/bin/sh\necho \'{"graded": true}\'\n')
    grader.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    out = tmp_path / "out"
    sh(str(RUN_TRIAL), "--repo", str(repo), "--prompt", str(prompt), "--grader", str(grader),
       "--plugin-dir", str(ROOT / "harnesses" / "reviewloop"), "--model", "claude-haiku-5-5",
       "--agent-timeout", "120", "--out", str(out), "--image", image, env=env)
    events = [json.loads(line) for line in (out / "transcript.jsonl").read_text().splitlines()]
    init = events[0]
    assert init["type"] == "system" and init["model"] == "claude-haiku-5-5"
    assert "reviewloop" in [p["name"] for p in init["plugins"]]
    result = json.loads((out / "result.json").read_text())
    assert result["is_error"] is True and result["total_cost_usd"] == 0
    assert json.loads((out / "grade.json").read_text()) == {"graded": True}
