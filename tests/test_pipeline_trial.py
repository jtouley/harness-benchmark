"""The trial: what a delivered repository must do for its checks to count.

Each repository here is a tiny git repo whose Makefile stands in for a pipeline: `make build` copies a
committed set of marts (built from the key's own answers, so the checks pass) into out/marts/, and
`make stream` exits with whatever the test needs. The replay server runs fast (speed 6000, DURATION=1),
so a trial takes a few seconds. The full P1 reference trial is in test_pipeline_reference.py.
"""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
from pathlib import Path

import pytest

from pipetask import trial
from test_pipeline_grader import KEY_PATH, answers, write_candidate

CAPTURE = KEY_PATH.parents[1] / "data" / "capture" / "recentchange.jsonl.gz"
COPY_MARTS = "rm -rf out/marts && mkdir -p out/marts && cp -R fixture/marts/. out/marts/"


@pytest.fixture(scope="module")
def key():
    return json.loads(KEY_PATH.read_text(encoding="utf-8"))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def delivered(tmp_path: Path, key: dict, *, build: str = COPY_MARTS, stream: str = "true",
              commit_outputs: bool = False) -> Path:
    """A committed repository: fixture/marts/ (correct marts), oracle_map.yml and the Makefile."""
    src = write_candidate(tmp_path / "src", key, answers(key))
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copytree(src / "out" / "marts", repo / "fixture" / "marts")
    shutil.copy2(src / "oracle_map.yml", repo / "oracle_map.yml")
    if commit_outputs:
        shutil.copytree(src / "out", repo / "out")
        (repo / "lake").mkdir()
        (repo / "lake" / "state.json").write_text("{}")
    (repo / "Makefile").write_text(f"build:\n\t{build}\nstream:\n\t{stream}\n")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "delivered")
    return repo


def run_trial(repo: Path, key: dict, tmp_path: Path, port: int | None = None) -> dict:
    return trial.trial(repo, key, CAPTURE, seed=key["stream"]["seed"], port=port or _free_port(),
                       speed=6000.0, durations=(1, 1), build_timeout=60, logs=tmp_path / "logs")


@pytest.mark.parametrize(("stream", "reward"), [
    ("true", 1.0),
    ("test -e .resumed || { touch .resumed; exit 1; }", 1.0),  # the second run exits 0
    ("exit 1", 0.0),
])
def test_the_reward_counts_only_when_some_stream_run_exits_0(key, tmp_path, stream, reward):
    result = run_trial(delivered(tmp_path, key, stream=stream), key, tmp_path)
    assert result["idempotent"] and result["passed"] == 7
    assert result["reward"] == reward


def test_a_second_build_that_changes_an_output_scores_zero(key, tmp_path):
    adds_a_file_each_run = ("mkdir -p out/marts && cp -R fixture/marts/. out/marts/ && "
                            "cp fixture/marts/negative_awards/data.parquet out/marts/negative_awards/run-$$$$.parquet")
    result = run_trial(delivered(tmp_path, key, build=adds_a_file_each_run), key, tmp_path)
    assert not result["idempotent"] and result["changed_by_second_build"] == ["negative_awards"]
    assert result["reward"] == 0.0


def test_outputs_and_state_from_development_are_removed_before_the_first_build(key, tmp_path):
    repo = delivered(tmp_path, key, build="true", commit_outputs=True)
    (repo / "state").mkdir()
    (repo / "state" / "checkpoint.json").write_text("{}")  # untracked consumer state
    result = run_trial(repo, key, tmp_path)
    assert not any((repo / name).exists() for name in ("out", "lake", "state"))
    assert result["passed"] == 0 and result["reward"] == 0.0


def test_a_repository_that_is_not_a_git_checkout_is_not_graded(key, tmp_path):
    repo = delivered(tmp_path, key)
    shutil.rmtree(repo / ".git")
    result = run_trial(repo, key, tmp_path)
    assert result["reward"] == 0.0 and "git clean" in result["error"]


def test_an_occupied_port_gives_a_json_error_not_a_traceback(key, tmp_path, capsys):
    repo = delivered(tmp_path, key)
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        trial.main(["--repo", str(repo), "--capture", str(CAPTURE), "--port", str(busy.getsockname()[1]),
                    "--seed", str(key["stream"]["seed"]), "--speed", "6000", "--durations", "1,1",
                    "--logs", str(tmp_path / "logs")], key=key)
    result = json.loads(capsys.readouterr().out)
    assert result["reward"] == 0.0 and "port" in result["error"]
