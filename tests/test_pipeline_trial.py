"""The trial: what a delivered repository must do for its checks to count.

Each repository here is a tiny git repo whose Makefile stands in for a pipeline: `make build` copies a
committed set of marts (built from the key's own answers, so the checks pass) into out/marts/, and
`make stream` reads the grading replay (READS: resuming with Last-Event-ID, to the end) or not, and
exits with whatever the test needs. The committed marts stand for output left from development, so
only reading the grading stream makes the stream checks count. The replay server runs fast (speed 6000, DURATION=1),
so a trial takes a few seconds. The full P1 reference trial is in test_pipeline_reference.py.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
from pathlib import Path

import pytest

from pipetask import trial
from test_pipeline_grader import KEY_PATH, answers, write_candidate

CAPTURE = KEY_PATH.parents[1] / "data" / "capture" / "recentchange.jsonl.gz"
COPY_MARTS = "rm -rf out/marts && mkdir -p out/marts && cp -R fixture/marts/. out/marts/"
READS = "python3 read_stream.py {port}"
READ_STREAM = """\
import sys, urllib.request
port, limit = int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 0
last, n = None, 0
while True:
    headers = {"Last-Event-ID": last} if last else {}
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v2/stream/recentchange", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        for raw in resp:
            line = raw.decode("utf-8").rstrip("\\n")
            if line == ":":
                sys.exit(0)  # idle: the replay has sent everything
            if line.startswith("id: "):
                last, n = line[4:], n + 1
                if n == limit:
                    sys.exit(0)
"""


@pytest.fixture(scope="module")
def key():
    return json.loads(KEY_PATH.read_text(encoding="utf-8"))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def delivered(tmp_path: Path, key: dict, port: int, *, build: str = COPY_MARTS, stream: str = READS,
              commit_outputs: bool = False) -> Path:
    """A committed repository: fixture/marts/ (correct marts), oracle_map.yml, read_stream.py and the
    Makefile. `{port}` in the stream recipe is the grading replay's port."""
    src = write_candidate(tmp_path / "src", key, answers(key))
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copytree(src / "out" / "marts", repo / "fixture" / "marts")
    shutil.copy2(src / "oracle_map.yml", repo / "oracle_map.yml")
    if commit_outputs:
        shutil.copytree(src / "out", repo / "out")
        (repo / "lake").mkdir()
        (repo / "lake" / "state.json").write_text("{}")
    (repo / "read_stream.py").write_text(READ_STREAM)
    (repo / "Makefile").write_text(f"build:\n\t{build}\nstream:\n\t{stream.replace("{port}", str(port))}\n")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "delivered")
    return repo


@pytest.fixture
def port() -> int:
    return _free_port()


def run_trial(repo: Path, key: dict, tmp_path: Path, port: int) -> dict:
    return trial.trial(repo, key, CAPTURE, seed=key["stream"]["seed"], port=port,
                       speed=6000.0, durations=(1, 1), build_timeout=60, logs=tmp_path / "logs")


@pytest.mark.parametrize(("stream", "reward"), [
    (READS, 1.0),
    ("test -e .resumed || { touch .resumed; exit 1; }; " + READS, 1.0),  # the second run reads it all
    (READS + "; exit 1", 0.0),  # reads, but no run exits 0
    ("true", 0.0),  # exits 0 without reading the grading stream: the marts are from development
    (READS + " 5", 0.0),  # reads a few frames only, not up to the late batch
])
def test_the_stream_checks_count_only_when_a_run_reads_the_grading_stream_and_exits_0(
        key, tmp_path, port, stream, reward):
    result = run_trial(delivered(tmp_path, key, port, stream=stream), key, tmp_path, port)
    assert result["idempotent"] and result["passed"] == 7
    assert result["reward"] == reward


def test_a_second_build_that_changes_an_output_scores_zero(key, tmp_path, port):
    adds_a_file_each_run = ("mkdir -p out/marts && cp -R fixture/marts/. out/marts/ && "
                            "cp fixture/marts/negative_awards/data.parquet out/marts/negative_awards/run-$$$$.parquet")
    result = run_trial(delivered(tmp_path, key, port, build=adds_a_file_each_run), key, tmp_path, port)
    assert not result["idempotent"] and result["changed_by_second_build"] == ["negative_awards"]
    assert result["reward"] == 0.0


def test_outputs_and_state_from_development_are_removed_before_the_first_build(key, tmp_path, port):
    repo = delivered(tmp_path, key, port, build="true", commit_outputs=True)
    (repo / "state").mkdir()
    (repo / "state" / "checkpoint.json").write_text("{}")  # untracked consumer state
    result = run_trial(repo, key, tmp_path, port)
    assert not any((repo / name).exists() for name in ("out", "lake", "state"))
    assert result["passed"] == 0 and result["reward"] == 0.0


def test_a_repository_that_is_not_a_git_checkout_is_not_graded(key, tmp_path, port):
    repo = delivered(tmp_path, key, port)
    shutil.rmtree(repo / ".git")
    result = run_trial(repo, key, tmp_path, port)
    assert result["reward"] == 0.0 and "git clean" in result["error"]


def test_an_occupied_port_gives_a_json_error_not_a_traceback(key, tmp_path, capsys):
    repo = delivered(tmp_path, key, _free_port())
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        trial.main(["--repo", str(repo), "--capture", str(CAPTURE), "--port", str(busy.getsockname()[1]),
                    "--seed", str(key["stream"]["seed"]), "--speed", "6000", "--durations", "1,1",
                    "--logs", str(tmp_path / "logs")], key=key)
    result = json.loads(capsys.readouterr().out)
    assert result["reward"] == 0.0 and "port" in result["error"]


# --- how the runner runs the candidate's make (golden/pipeline/README.md, runner wiring) -------------

def test_make_gets_a_fresh_home_and_only_the_toolchain_environment(key, tmp_path, port, monkeypatch):
    """State under $HOME (dlt's ~/.dlt/pipelines/) must not survive from development, and the grader's
    own variables must not reach the candidate's make."""
    seen = tmp_path / "seen"
    seen.mkdir()
    monkeypatch.setenv("HB_GRADER_ONLY_PROBE", "secret")
    record = (f'test -z "$$(ls -A $$HOME)" -o -e $$HOME/.mine; echo $$HOME >> {seen}/homes; '
              f'touch $$HOME/.mine; env | cut -d= -f1 | sort -u > {seen}/env')
    repo = delivered(tmp_path, key, port, build=f"{record} && {COPY_MARTS}",
                     stream=f"{record} && {READS}")
    make_env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HB_TOOLCHAIN_PROBE": "1"}
    result = trial.trial(repo, key, CAPTURE, seed=key["stream"]["seed"], port=port, speed=6000.0,
                         durations=(1, 1), build_timeout=60, logs=tmp_path / "logs", make_env=make_env)
    assert result["reward"] == 1.0, result
    homes = set((seen / "homes").read_text().split())
    assert len(homes) == 1  # one HOME for the whole grading run: its builds and stream runs share it
    home = homes.pop()
    assert home != str(Path.home()) and not Path(home).exists()  # fresh, and removed afterwards
    names = set((seen / "env").read_text().split())
    assert {"HOME", "PATH", "HB_TOOLCHAIN_PROBE"} <= names
    assert "HB_GRADER_ONLY_PROBE" not in names
    assert names <= {"HOME", "PATH", "HB_TOOLCHAIN_PROBE", "USER", "LOGNAME", "PWD", "OLDPWD", "SHLVL",
                     "_", "MAKEFLAGS", "MAKELEVEL", "MFLAGS", "MAKE_TERMOUT", "MAKE_TERMERR", "MAKEOVERRIDES",
                     "DURATION",  # set by make itself
                     "MANPATH", "__CF_USER_TEXT_ENCODING"}, names  # added by macOS to every process


def test_a_stream_run_is_killed_after_its_duration_plus_the_grace(key, tmp_path, port):
    repo = delivered(tmp_path, key, port, stream="sleep 60")
    result = trial.trial(repo, key, CAPTURE, seed=key["stream"]["seed"], port=port, speed=6000.0,
                         durations=(1, 1), build_timeout=60, logs=tmp_path / "logs", stream_grace=2)
    assert [s["exit"] for s in result["stream"]] == [-9, -9]
    assert all(s["seconds"] < 10 for s in result["stream"])
    assert result["reward"] == 0.0


def test_make_user_needs_root(key, tmp_path, port):
    if os.geteuid() == 0:
        pytest.skip("runs as root")
    result = trial.trial(delivered(tmp_path, key, port), key, CAPTURE, seed=key["stream"]["seed"],
                         port=port, speed=6000.0, durations=(1, 1), build_timeout=60,
                         logs=tmp_path / "logs", make_user="agent")
    assert result["reward"] == 0.0 and "root" in result["error"]


def test_make_env_file_reads_name_value_lines(tmp_path):
    f = tmp_path / "toolchain.env"
    f.write_text("# toolchain\nPATH=/opt/hb/bin:/usr/bin\n\nUV_OFFLINE=1\nSBT_OPTS=-Da=b -Dc=d\n")
    assert trial.read_env_file(f) == {"PATH": "/opt/hb/bin:/usr/bin", "UV_OFFLINE": "1",
                                      "SBT_OPTS": "-Da=b -Dc=d"}
    f.write_text("not a variable\n")
    with pytest.raises(ValueError):
        trial.read_env_file(f)
