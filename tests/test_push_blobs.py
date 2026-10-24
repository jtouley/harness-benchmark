"""scripts/push_blobs.sh: parallel runs push their blobs to one runs-store branch and none is lost."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
       "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}


def _git(cwd: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")} | GIT
    return subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True).stdout


def _store(tmp_path: Path) -> str:
    seed = tmp_path / "seed"
    (seed / "blobs").mkdir(parents=True)
    (seed / "blobs" / "old.gz").write_text("old")
    _git(tmp_path, "init", "-q", "-b", "runs-store", str(seed))
    _git(seed, "add", "-A")
    _git(seed, "commit", "-q", "-m", "seed")
    _git(tmp_path, "clone", "-q", "--bare", str(seed), str(tmp_path / "origin.git"))
    return f"file://{tmp_path / 'origin.git'}"


def _clone(tmp_path: Path, url: str, name: str, blob: str) -> Path:
    clone = tmp_path / name
    _git(tmp_path, "clone", "-q", "--single-branch", "--branch", "runs-store", "--depth", "1", url, str(clone))
    (clone / "blobs" / blob).write_text(blob)
    return clone


def _push(clone: Path, rid: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")} | GIT | {"PUSH_BLOBS_BACKOFF": "0"}
    return subprocess.run(["bash", str(ROOT / "scripts" / "push_blobs.sh"), str(clone), rid, "4"], env=env,
                          capture_output=True, text=True)


def test_a_run_that_lost_the_race_pushes_on_the_new_tip_and_no_blob_is_lost(tmp_path):
    """Two runs cloned the same tip; the second push is not a fast-forward. It is retried on the new tip, and
    both runs' blobs, and the older ones, end up on runs-store."""
    url = _store(tmp_path)
    first, second = _clone(tmp_path, url, "a", "x.gz"), _clone(tmp_path, url, "b", "y.gz")
    assert _push(first, "run-a").returncode == 0
    proc = _push(second, "run-b")
    assert proc.returncode == 0, proc.stderr
    assert "every blob is on runs-store" in proc.stderr
    files = _git(tmp_path / "origin.git", "ls-tree", "-r", "--name-only", "runs-store").split()
    assert sorted(files) == ["blobs/old.gz", "blobs/x.gz", "blobs/y.gz"]


def test_a_run_with_no_new_blobs_pushes_nothing(tmp_path):
    url = _store(tmp_path)
    head = _git(tmp_path / "origin.git", "rev-parse", "runs-store")
    clone = tmp_path / "a"
    _git(tmp_path, "clone", "-q", "--single-branch", "--branch", "runs-store", "--depth", "1", url, str(clone))
    proc = _push(clone, "run-a")
    assert proc.returncode == 0 and "no new blobs" in proc.stderr
    assert _git(tmp_path / "origin.git", "rev-parse", "runs-store") == head


def test_a_push_that_never_lands_fails(tmp_path):
    url = _store(tmp_path)
    clone = _clone(tmp_path, url, "a", "x.gz")
    _git(clone, "remote", "set-url", "origin", f"file://{tmp_path / 'nowhere.git'}")
    proc = _push(clone, "run-a")
    assert proc.returncode == 1 and "failed 4 times" in proc.stderr
