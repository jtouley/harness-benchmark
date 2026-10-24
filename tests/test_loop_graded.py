"""The stored tree bundle holds the exact commit the grader graded (loop.graded), for every arm.

Run 20261023-P1-oneshot-haiku-1 scored 5/7 on work the agent never committed; the driver bundled only the
refs of repo-as-left, so its bundle holds the starting skeleton alone. Here a run whose work is uncommitted
is graded by the real grader (pipetask.trial --snapshot-worktree, as host_trial runs it), recorded by the
driver, and graded again from the stored bundle.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from loop import check, driver, graded, record, store
from pipetask import trial
from test_loop_record import ROOT, _drive, minimal, plugin  # noqa: F401  (plugin is a fixture)
from test_pipeline_trial import CAPTURE, delivered, key, port  # noqa: F401  (key, port: fixtures)

sys.path.insert(0, str(ROOT / "scripts"))
import host_trial  # noqa: E402
import regrade_host_run  # noqa: E402

RUN_ID = "20261022-P1-cadence-haiku-1"  # the run id test_loop_record._drive records


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=repo, check=True,
                          capture_output=True, text=True).stdout.strip()


def _grade(repo: Path, key: dict, logs: Path, port: int) -> dict:
    """The grader as host_trial runs it (--snapshot-worktree), fast: a replay at speed 6000."""
    return trial.trial(repo, key, CAPTURE, seed=key["stream"]["seed"], port=port, speed=6000.0, durations=(1, 1),
                       build_timeout=60, logs=logs, keepalive=0.2, snapshot_worktree=True)


def _uncommitted_run(tmp_path: Path, key: dict, port: int) -> Path:
    """A repository whose pipeline works only with the agent's uncommitted changes: the marts the build copies
    are untracked (work/) and the Makefile that reads them is modified, not committed."""
    repo = delivered(tmp_path, key, port)
    _git(repo, "rm", "-rq", "--cached", "fixture")
    _git(repo, "commit", "-qm", "the agent's last commit: no marts in it")
    (repo / "fixture").rename(repo / "work")
    (repo / "Makefile").write_text((repo / "Makefile").read_text().replace("fixture/", "work/"))
    return repo


def test_uncommitted_work_is_in_the_bundles_graded_ref_and_a_regrade_from_the_bundle_gives_the_same_score(
        tmp_path, plugin, key, port, monkeypatch):  # noqa: F811
    repo = _uncommitted_run(tmp_path, key, port)
    agent_head = _git(repo, "rev-parse", "HEAD")
    as_left = tmp_path / "repo-as-left"
    shutil.copytree(repo, as_left, symlinks=True)  # host_trial copies it before grading
    first = _grade(repo, key, tmp_path / "logs", port)
    assert first["reward"] == 1.0 and first["snapshot"]["files"] >= 2, first
    (tmp_path / "trial").mkdir()
    (tmp_path / "trial" / "grade.json").write_text(json.dumps(first))

    rc, run = _drive(tmp_path, plugin, extra=["--tree", str(as_left), "--graded-repo", str(repo),
                                              "--grade", str(tmp_path / "trial" / "grade.json"),
                                              "--grader-repo", str(ROOT)])
    assert rc == 0
    rec = record.load(run)
    assert record.validate(rec, record.RECORD_SCHEMA) == [] and check.graded_problem(rec, RUN_ID) is None
    assert rec["graded"] == {"commit": first["snapshot"]["commit"], "ref": f"refs/graded/{RUN_ID}"}
    assert rec["graded"]["commit"] != agent_head

    bundle = tmp_path / "store" / rec["tree"]["path"]
    heads = graded.heads(bundle)
    assert heads[f"refs/graded/{RUN_ID}"] == rec["graded"]["commit"]
    assert heads["refs/heads/" + _git(as_left, "branch", "--show-current")] == agent_head  # the agent's refs too
    checkout = tmp_path / "from-bundle"
    assert graded.checkout(bundle, RUN_ID, checkout) == rec["graded"]["commit"]
    assert (checkout / "work").is_dir() and "work/" in (checkout / "Makefile").read_text()  # the uncommitted work
    assert _git(checkout, "show", f"{agent_head}:Makefile").count("work/") == 0  # which no agent commit has
    assert _git(checkout, "ls-tree", "-r", "--name-only", agent_head, "--", "work", "fixture") == ""
    assert graded.audit(tmp_path / "runs", tmp_path / "store") == []

    # The regrade script, graded from the bundle; the grader it calls runs fast here, on the port the
    # delivered Makefile names.
    def fast_grade(repo_copy: Path, out: Path) -> int:
        (out / "grade.json").write_text(json.dumps(_grade(repo_copy, key, out / "logs", port)))
        return 0

    monkeypatch.setattr(host_trial, "grade", fast_grade)
    assert regrade_host_run.main([RUN_ID, "--bundle", str(bundle), "--why", "test", "--runs",
                                  str(tmp_path / "runs")]) == 0
    driver_score, regrade = record.scores(run)
    assert (regrade["reward"], regrade["passed"], regrade["total"]) == \
        (driver_score["reward"], driver_score["passed"], driver_score["total"]) == (1.0, 7, 7)


def test_the_bundle_of_the_refs_alone_would_have_lost_the_graded_work(tmp_path, key, port):  # noqa: F811
    """The old bundle (`bundle create --all` of repo-as-left): graded from it, the same run scores 0."""
    repo = _uncommitted_run(tmp_path, key, port)
    old = tmp_path / "old.bundle"
    _git(repo, "bundle", "create", "-q", str(old), "--all")
    clone = tmp_path / "clone"
    _git(tmp_path, "clone", "-q", str(old), str(clone))
    assert _grade(clone, key, tmp_path / "logs", port)["reward"] == 0.0
    with pytest.raises(graded.GradedError):
        graded.checkout(old, RUN_ID, tmp_path / "nope")


def _old_style_record(tmp_path: Path, run_id: str, *, agent_commit: bool) -> None:
    """A record stored before this fix: a bundle of the refs only, no `graded`, a grader score."""
    repo = tmp_path / run_id
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "README").write_text("skeleton\n")
    _git(repo, "add", "-A")
    subprocess.run(["git", "-c", "user.name=cbench", "-c", "user.email=c@b", "commit", "-qm", "cadence config for "
                    "the trial"], cwd=repo, check=True)
    if agent_commit:
        (repo / "pipeline.py").write_text("x = 1\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", "the agent's commit")
    bundle = tmp_path / f"{run_id}.bundle"
    _git(repo, "bundle", "create", "-q", str(bundle), "--all")
    rec = minimal(run_id, tree=store.put(bundle, tmp_path / "store"))
    record.write_record(tmp_path / "runs", rec)
    record.append_score(tmp_path / "runs", {
        "run_id": run_id, "grader": {"repo": record.GRADER_REPO, "commit": "a" * 40, "tree": "b" * 40},
        "reward": 0.7143, "passed": 5, "total": 7, "idempotent": True, "stream_ok": True, "error": None,
        "source": "driver", "graded_at": "2026-10-23T00:00:00Z"})


def test_the_audit_lists_records_whose_bundle_lacks_the_graded_work_and_changes_nothing(tmp_path, capsys):
    _old_style_record(tmp_path, "20261023-P1-oneshot-haiku-1", agent_commit=False)
    _old_style_record(tmp_path, "20261024-P1-cadence-haiku-core-4", agent_commit=True)
    ungraded = minimal("20261024-P1-cadence-haiku-core-9")  # no grader score: not this check's
    record.write_record(tmp_path / "runs", ungraded)
    before = {p: p.read_bytes() for p in (tmp_path / "runs").rglob("*") if p.is_file()}
    found = dict(graded.audit(tmp_path / "runs", tmp_path / "store"))
    assert set(found) == {"20261023-P1-oneshot-haiku-1", "20261024-P1-cadence-haiku-core-4"}
    assert "only the starting repository" in found["20261023-P1-oneshot-haiku-1"]
    assert "1 commit(s) of the agent's" in found["20261024-P1-cadence-haiku-core-4"]
    assert graded.main(["--store", str(tmp_path / "store"), "--runs", str(tmp_path / "runs")]) == 1
    assert capsys.readouterr().out.count("\n") == 2
    assert graded.main(["--store", str(tmp_path / "store"), "--runs", str(tmp_path / "runs"),
                        "--run", "20261024-P1-cadence-haiku-core-9"]) == 0
    assert before == {p: p.read_bytes() for p in (tmp_path / "runs").rglob("*") if p.is_file()}


@pytest.mark.parametrize(("info", "problem"), [
    (None, None),
    ({"commit": None, "ref": None, "missing": "no graded commit"}, None),
    ({"commit": "c" * 40, "ref": "refs/graded/20261021-P1-cadence-core-haiku-1"}, "no tree bundle"),
    ({"commit": "c" * 40, "ref": "refs/graded/another-run"}, "not 'refs/graded/20261021-P1-cadence-core-haiku-1'"),
    ({"commit": None, "ref": "refs/graded/20261021-P1-cadence-core-haiku-1"}, "graded.commit is not"),
])
def test_the_check_holds_the_graded_ref_to_the_run_id_and_a_commit(info, problem):
    rec = minimal(graded=info)
    assert record.validate(rec, record.RECORD_SCHEMA) == []
    why = check.graded_problem(rec, rec["run_id"])
    assert (why is None) if problem is None else (problem in why), why


def test_a_grade_without_a_snapshot_graded_the_head_and_a_failed_snapshot_graded_nothing(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "one")
    assert graded.graded_commit({"reward": 0.0}, repo) == (_git(repo, "rev-parse", "HEAD"), None)
    assert graded.graded_commit({"snapshot": {"commit": "d" * 40}}, None) == ("d" * 40, None)
    assert graded.graded_commit({"snapshot": {"error": "lock"}, "error": "lock"}, repo)[0] is None
    assert graded.graded_commit(None, repo)[0] is None


def test_the_bundle_keeps_every_ref_and_a_detached_head_as_bundle_create_all_did(tmp_path):
    tree = tmp_path / "tree"
    tree.mkdir()
    _git(tree, "init", "-q", "-b", "main")
    _git(tree, "commit", "-q", "--allow-empty", "-m", "one")
    _git(tree, "branch", "feature")
    _git(tree, "checkout", "-q", "--detach")
    _git(tree, "commit", "-q", "--allow-empty", "-m", "on no branch")
    old, new = tmp_path / "old.bundle", tmp_path / "new.bundle"
    _git(tree, "bundle", "create", "-q", str(old), "--all")
    info = graded.bundle(tree, new, "20261024-P1-x-1", _git(tree, "rev-parse", "HEAD"), [])
    assert info == {"commit": _git(tree, "rev-parse", "HEAD"), "ref": "refs/graded/20261024-P1-x-1"}
    assert graded.heads(new) == {**graded.heads(old), "refs/graded/20261024-P1-x-1": info["commit"]}
