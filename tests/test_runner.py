"""Isolated runner (runner/): one disposable container per trial, with its own Docker daemon.

The Docker tests build the runner image and run stub trials (no API call, no cost). They run only with
HB_RUNNER_DOCKER_TESTS=1, one container at a time. Every container they create is labelled
`hb.runner` and removed; they never list or touch other containers, images or volumes.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
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
    for flag in ("--repo", "--prompt", "--grader", "--out", "--model", "--plugin-dir", "--suffix", "--replay",
                 "--replay-seed", "--grader-arg"):
        assert flag in out


@pytest.mark.parametrize("args", [[], ["--repo", "/nonexistent"], ["--bogus"]])
def test_bad_arguments_fail_before_docker_is_called(args, tmp_path):
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    (tmp_path / "docker").write_text("#!/bin/sh\necho docker-called >&2\nexit 99\n")
    (tmp_path / "docker").chmod(0o755)
    r = sh(str(RUN_TRIAL), *args, check=False, env=env)
    assert r.returncode == 2
    assert "docker-called" not in r.stderr


@pytest.mark.parametrize("args, message", [
    (["--plugin-dir", "PLUGIN", "--agent-timeout", "60"], "a harness arm (--plugin-dir) has no time cap"),
    (["--agent-timeout", "1h"], "--agent-timeout must be a whole number of seconds"),
])
def test_a_harness_arm_cannot_be_given_a_time_cap(args, message, tmp_path):
    """Criteria v2 section 5.3: only a one-shot keeps a guard cap; the runner refuses one for a harness arm."""
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    (tmp_path / "docker").write_text("#!/bin/sh\necho docker-called >&2\nexit 99\n")
    (tmp_path / "docker").chmod(0o755)
    (tmp_path / "plugin").mkdir()
    prompt = tmp_path / "prompt.md"
    prompt.write_text("task")
    args = [str(tmp_path / "plugin") if a == "PLUGIN" else a for a in args]
    r = sh(str(RUN_TRIAL), "--repo", str(tmp_path), "--prompt", str(prompt), "--grader", str(RUN_TRIAL),
           "--out", str(tmp_path / "out"), *args, check=False, env=env)
    assert r.returncode == 2 and message in r.stderr
    assert "docker-called" not in r.stderr


def test_the_agent_runs_under_a_time_limit_only_when_it_has_one():
    """entrypoint.sh wraps the agent in `timeout` only for a positive cap (HB_AGENT_TIMEOUT=0: none)."""
    text = (RUNNER / "entrypoint.sh").read_text()
    assert '[ "$agent_timeout" -gt 0 ] && limit=(timeout --kill-after=30 "$agent_timeout")' in text
    assert 'exec "${limit[@]}" setpriv' in text
    assert "exec timeout" not in text


KEY_VARIABLES = ("ANTHROPIC_API_KEY", "HB_API_KEY")
# Shell builtins: their arguments are in no process's command line.
KEY_SAFE_BUILTINS = {"read", "export", "unset", "[", "printf"}
REDACTED = "[REDACTED:ANTHROPIC_API_KEY]"


def key_commands(script: Path) -> list[str]:
    """Simple commands of `script` that name a key variable (comments and here-documents skipped)."""
    found, heredoc_end = [], None
    for line in script.read_text().splitlines():
        stripped = line.strip()
        if heredoc_end is not None:
            heredoc_end = None if stripped == heredoc_end else heredoc_end
            continue
        if stripped.startswith("#"):
            continue
        for segment in re.split(r"&&|\|\||;|\|", stripped):
            segment = segment.strip().lstrip("( ").rstrip(") ")
            if any(name in segment for name in KEY_VARIABLES):
                found.append(segment)
        if m := re.search(r"<<-?'?(\w+)'?", stripped):
            heredoc_end = m.group(1)
    return found


def key_is_only_held_or_given_to_builtins(command: str) -> bool:
    words = command.split()
    while words and re.fullmatch(r"[A-Za-z_]\w*=\S*", words[0]):
        name = words[0].split("=", 1)[0]
        if any(k in words[0] for k in KEY_VARIABLES) and name not in KEY_VARIABLES:
            return False  # the key is copied into another variable (an array, a list of arguments)
        words = words[1:]
    return not words or words[0] in KEY_SAFE_BUILTINS


@pytest.mark.parametrize("script", ["run_trial.sh", "entrypoint.sh"])
def test_api_key_is_never_a_process_argument(script):
    """The key moves only through builtins and the key variables (never `ps`, never `docker inspect`)."""
    commands = key_commands(RUNNER / script)
    assert commands, "the script must handle the key"
    assert [c for c in commands if not key_is_only_held_or_given_to_builtins(c)] == []
    assert "ANTHROPIC_API_KEY" not in (RUNNER / "Dockerfile").read_text()


FAKE_DOCKER = r"""#!/usr/bin/env bash
# Fake docker CLI: the trial "runs" at once; copying /trial/out produces outputs that hold the key.
case "$1" in
  create|exec|rm) exit 0 ;;
  inspect) echo 0 ;;
  start) cat >/dev/null; echo "[trial] agent phase done; waiting for the grader" ;;
  cp)
    src="${@: -2:1}" dst="${@: -1}"
    case "$src" in *:/trial/out/.)
      mkdir -p "$dst/claude-projects/p"
      printf '{"text":"key is %s"}
{"text":"clean"}
' "$ANTHROPIC_API_KEY" >"$dst/transcript.jsonl"
      printf '%s%s
' "$ANTHROPIC_API_KEY" "$ANTHROPIC_API_KEY" >"$dst/claude-projects/p/s.jsonl"
      chmod 0444 "$dst/claude-projects/p/s.jsonl"
      echo nothing >"$dst/clean.txt"
      ln -s "$HB_FAKE_OUTSIDE" "$dst/link" ;;
    esac ;;
esac
"""


def test_outputs_are_scanned_and_the_key_is_redacted_without_printing_it(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "docker").write_text(FAKE_DOCKER)
    (bin_dir / "docker").chmod(0o755)
    outside = tmp_path / "outside.txt"  # a host file outside --out: the scan must not follow links
    outside.write_text(FAKE_KEY)
    repo, prompt, grader, out = tmp_path / "repo", tmp_path / "prompt.txt", tmp_path / "g.sh", tmp_path / "out"
    repo.mkdir()
    prompt.write_text("p")
    grader.write_text("#!/bin/sh\n")
    grader.chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "ANTHROPIC_API_KEY": FAKE_KEY,
           "HB_FAKE_OUTSIDE": str(outside)}
    r = sh(str(RUN_TRIAL), "--repo", str(repo), "--prompt", str(prompt), "--grader", str(grader),
           "--out", str(out), "--name", "hb-fake", check=False, env=env)
    assert r.returncode == 0, r.stderr.replace(FAKE_KEY, "<key>")
    assert FAKE_KEY not in r.stdout + r.stderr
    for f in out.rglob("*"):
        if f.is_file() and not f.is_symlink():
            assert FAKE_KEY not in f.read_text(), f.name
    assert (out / "transcript.jsonl").read_text() == f'{{"text":"key is {REDACTED}"}}\n{{"text":"clean"}}\n'
    assert (out / "claude-projects/p/s.jsonl").read_text() == REDACTED * 2 + "\n"
    assert (out / "clean.txt").read_text() == "nothing\n"
    assert outside.read_text() == FAKE_KEY
    assert json.loads((out / "host.json").read_text())["api_key_redacted_files"] == 2


def test_trial_outputs_are_not_tracked_by_git():
    r = sh("git", "-C", str(ROOT), "check-ignore", "-q", "results/runs/t1/transcript.jsonl", check=False)
    assert r.returncode == 0, "results/runs/ must be in .gitignore (the repository is public)"


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
                     "agent_processes_left": 0, "grader_sees_api_key": False, "commits": 2,
                     "root_git": "refused"}
    # The agent's environment is the runner's list only; the container's own variables stay out.
    assert "ANTHROPIC_API_KEY" in result["env_names"]
    assert set(result["env_names"]) <= {
        "PATH", "HOME", "USER", "TERM", "LANG", "DISABLE_AUTOUPDATER", "HB_OUTPUTS", "HB_MODEL",
        "HB_PERMISSION_MODE", "ANTHROPIC_API_KEY", "PWD", "OLDPWD", "SHLVL", "_"}, result["env_names"]
    assert timing["agent_exit"] == 0 and timing["leftover_agent_processes_killed"] >= 1
    assert timing["agent_processes_left_after_kill"] == 0
    # agent_seconds is the agent's own run time: not the kill step, not the wait for the grader.
    assert abs(timing["agent_seconds"] - result["stub_seconds"]) < 0.5, (timing, result["stub_seconds"])
    assert (out / "agent" / "summary.md").read_text() == "stub summary\n"
    # The agent printed its key; the host outputs hold the redaction mark instead.
    assert REDACTED in (out / "transcript.jsonl").read_text()
    assert REDACTED in (out / "claude-projects" / "stub" / "session.jsonl").read_text()
    assert json.loads((out / "host.json").read_text())["api_key_redacted_files"] >= 2
    # The key is in no output; the host repository is untouched.
    for f in out.rglob("*"):
        if f.is_file():
            assert FAKE_KEY not in f.read_text(errors="replace"), f.name
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
       "--out", str(out), "--image", image, env=env)
    assert json.loads((out / "timing.json").read_text())["agent_timeout"] == 0  # a harness arm: no cap
    events = [json.loads(line) for line in (out / "transcript.jsonl").read_text().splitlines()]
    init = events[0]
    assert init["type"] == "system" and init["model"] == "claude-haiku-5-5"
    assert "reviewloop" in [p["name"] for p in init["plugins"]]
    result = json.loads((out / "result.json").read_text())
    assert result["is_error"] is True and result["total_cost_usd"] == 0
    assert json.loads((out / "grade.json").read_text()) == {"graded": True}


# --- the pipeline family's wiring (golden/pipeline/README.md, "A trial on the isolated runner") -------

PIPELINE_IMAGE = os.environ.get("HB_PIPELINE_IMAGE", "harness-benchmark/runner-pipeline:py")
# What the candidate's make can see while the grader runs it (written by `make build`).
MAKE_PROBE = ("{ id -un; echo $$HOME; test -e $$HOME/.dlt && echo dev-state || echo no-dev-state; "
              "cat /opt/hb-grader/grader >/dev/null 2>&1 && echo grader-readable || echo grader-unreadable; "
              "find / -xdev -name answer_key.json 2>/dev/null | wc -l; "
              "curl -s -m 5 -o /dev/null https://pypi.org/simple/ && echo net-open || echo net-blocked; "
              "} > /trial/out/agent/make-probe.txt")


@pytest.fixture(scope="module")
def pipeline_image(image):
    sh(str(RUNNER / "pipeline" / "build.sh"), "py", timeout=3600)
    return PIPELINE_IMAGE


@docker_tests
def test_pipeline_trial_isolates_the_grader_from_the_candidates_make(pipeline_image, tmp_path):
    """The dev replay serves the agent and is unreadable; the grader's make runs as the agent user with a
    fresh HOME and no network, and cannot read the grader (which holds the key); the trial still scores."""
    import sys
    sys.path.insert(0, str(ROOT / "golden" / "pipeline"))
    from pipetask import bundle
    from test_pipeline_trial import COPY_MARTS, KEY_PATH, delivered

    key = json.loads(KEY_PATH.read_text(encoding="utf-8"))
    repo = delivered(tmp_path, key, 8099, build=f"{MAKE_PROBE} && {COPY_MARTS}")
    dist = tmp_path / "dist"
    bundle.bundle(dist)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Build the pipeline.")
    out = tmp_path / "out"
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    args = [str(RUN_TRIAL), "--repo", str(repo), "--prompt", str(prompt), "--grader", str(dist / "grader.pyz"),
            "--replay", str(dist / "replay.pyz"), "--agent-cmd", str(FIXTURES / "pipeline_stub_agent.sh"),
            "--model", "stub-model", "--out", str(out), "--image", pipeline_image, "--grader-timeout", "600"]
    for a in ("--make-user", "agent", "--make-env-file", "/opt/hb/toolchain.env", "--logs",
              "/trial/out/grade-logs", "--speed", "6000", "--durations", "1,1", "--snapshot-worktree"):
        args += ["--grader-arg", a]
    sh(*args, env=env, timeout=1200)

    agent = json.loads((out / "agent" / "agent-probe.json").read_text())
    assert agent["dev_frames"] > 0 and agent["replay_readable"] is False
    assert agent["uv_offline"] == "1" and agent["python3"].startswith("3.12.")
    user, home, state, grader, keys, net = (out / "agent" / "make-probe.txt").read_text().split()
    assert user == "agent" and home not in ("/home/agent", "/root") and state == "no-dev-state"
    assert grader == "grader-unreadable" and keys == "0" and net == "net-blocked"
    timing = json.loads((out / "timing.json").read_text())
    assert timing["dev_replay"] is True and timing["agent_network_during_grading"] == "blocked"
    grade = json.loads((out / "grade.json").read_text())
    assert grade["make_user"] == "agent" and grade["make_fresh_home"] is True
    assert grade["reward"] == 1.0, grade
    # The stub agent wrote its probe file in the repository and never committed it: the snapshot took it.
    assert grade["snapshot"]["files"] >= 1 and (out / "repo" / "agent-was-here.txt").exists()
    assert not (out / "repo" / ".git").exists()
    # The core.fsmonitor hook the agent planted in .git/config never ran as root (nor at all).
    ran = out / "agent" / "fsmonitor-ran"
    assert not ran.exists(), ran.read_text()


@docker_tests
def test_a_grader_killed_at_its_cap_still_leaves_a_json_grade(image, tmp_path):
    repo, prompt = make_task(tmp_path, uuid.uuid4().hex[:12], hold=False)
    grader = tmp_path / "slow.sh"
    grader.write_text("#!/bin/sh\nsleep 600\n")
    grader.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    out = tmp_path / "out"
    sh(str(RUN_TRIAL), "--repo", str(repo), "--prompt", str(prompt), "--grader", str(grader),
       "--agent-cmd", str(FIXTURES / "pipeline_stub_agent.sh"), "--model", "stub-model",
       "--grader-timeout", "3", "--out", str(out), "--image", image, env=env, timeout=600)
    grade = json.loads((out / "grade.json").read_text())
    assert grade["reward"] == 0.0 and "cap of 3s" in grade["error"]
