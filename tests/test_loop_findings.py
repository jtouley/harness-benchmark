"""findings.jsonl: rows need runs, and a finding closes only by what later records show (loop/findings.py)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from loop import findings, record

ROOT = Path(__file__).resolve().parents[1]
FOUND = "20261021-P1-cadence-core-haiku-3"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                          cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def cadence(tmp_path) -> Path:
    """A cadence history: base, then the fix with its trailer, then a later commit."""
    repo = tmp_path / "cadence"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    for msg in ("base", "fix: a local PR record under adapter none\n\nFinding: F-1\nEvidence: " + FOUND, "later"):
        (repo / "f").write_text(msg)
        _git(repo, "add", "f")
        _git(repo, "commit", "-qm", msg)
    return repo


def _sha(repo: Path, back: int) -> str:
    return _git(repo, "rev-parse", f"HEAD~{back}")


def _run(runs: Path, run_id: str, *, sha: str, source="driver", block="R7", reason="done", reward=0.5,
         passed=4, kind="benchmark", task="P1", request="gh-1", started="2026-10-23T00:00:00Z",
         counts=True, clean=True) -> None:
    record.write_record(runs, {
        "schema": 1, "run_id": run_id, "kind": kind, "batch": "2026-10-23-test",
        "provenance": {"source": source, "evidence": []}, "task": task, "request_id": request, "arm": "cadence",
        "cadence": {"repo": "x", "sha": sha, "tree_clean": clean}, "model_requested": "claude-haiku-5-5",
        "models_served": ["claude-haiku-5-5"], "command": None, "started_at": started, "ended_at": None,
        "exit_code": 0, "cost": {"list_usd": None, "reported_usd": None},
        "stop_point": {"block": block, "reason": reason}, "transcript": {"sha256": None, "missing": "test"},
        "tree": {"sha256": None, "missing": "test"}, "counts": {"counts": counts, "why": "test"},
        "timing": {"agent_wall_seconds": None, "run_wall_seconds": None, "agent_active_seconds": None, "blocks": None},
        "isolation": None})
    record.append_score(runs, {"run_id": run_id, "grader": {"repo": "jtouley/harness-benchmark", "commit": "abc1234",
                                                          "tree": "a" * 40},
                               "reward": reward, "passed": passed, "total": 7, "idempotent": True,
                               "stream_ok": True, "error": None, "source": "driver", "graded_at": None})


ROW = {"id": "F-1", "title": "E4 needs a GitHub PR URL", "run_ids": [FOUND], "root_cause": "no local PR mode",
       "component": "cadence", "gone_when": {"stop_block_not": ["E4"]}, "status": "open"}


@pytest.fixture
def runs(tmp_path, cadence) -> Path:
    runs = tmp_path / "runs"
    _run(runs, FOUND, sha=_sha(cadence, 2), block="E4", reason="credentials", reward=0.0, passed=0,
         started="2026-10-22T00:00:00Z")
    return runs


def _write(tmp_path: Path, *rows: dict) -> Path:
    path = tmp_path / "findings.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


# --- rows

@pytest.mark.parametrize(("change", "message"), [
    ({"run_ids": []}, "no run id"),
    ({"run_ids": ["live run 3"]}, "is not a run id"),
    ({"run_ids": ["20261020-P1-nowhere"]}, "has no record"),
    ({"id": "F1"}, "F-<n>"),
    ({"status": "fixed"}, "open or closed"),
    ({"gone_when": {"looks_fine": True}}, "gone_when"),
])
def test_a_bad_row_is_refused(tmp_path, runs, cadence, change, message):
    problems = findings.check(_write(tmp_path, {**ROW, **change}), runs, cadence)
    assert any(message in p for p in problems), problems


def test_a_row_without_run_ids_is_refused():
    row = dict(ROW)
    del row["run_ids"]
    assert any("run_ids" in p for p in findings.row_problems(row, ROOT / "runs"))


# --- the close rule

def test_open_while_no_cadence_commit_has_the_trailer(runs, cadence):
    assert findings.compute({**ROW, "id": "F-2"}, runs, cadence)[0] == "open"


def test_the_trailer_finds_the_fix(cadence):
    assert findings.fix_commits(cadence, "F-1") == [_sha(cadence, 1)]
    assert findings.fix_commits(cadence, "F-10") == []


def test_closed_by_a_later_clean_benchmark_run_with_the_fix(runs, cadence):
    _run(runs, "20261023-P1-cadence-haiku-1", sha=_sha(cadence, 0), reward=0.5)
    status, why = findings.compute(ROW, runs, cadence)
    assert status == "closed", why
    assert "20261023-P1-cadence-haiku-1" in why


@pytest.mark.parametrize("kw", [
    {"source": "backfill"},              # not started by the driver
    {"sha": "BEFORE"},                   # a commit without the fix
    {"clean": None},                     # plugin tree not shown clean
    {"counts": False},                   # does not count
    {"kind": "live"},                    # not a benchmark run
    {"task": "P3"},                      # not in the task set
    {"started": "2026-10-21T00:00:00Z"},  # before the finding's run
])
def test_a_run_that_does_not_qualify_does_not_close_it(runs, cadence, kw):
    if kw.get("sha") == "BEFORE":
        kw = {**kw, "sha": _sha(cadence, 2)}
    _run(runs, "20261023-P1-cadence-haiku-1", **{"sha": _sha(cadence, 0), **kw})
    assert findings.compute(ROW, runs, cadence)[0] == "open"


def test_a_run_of_the_live_request_that_found_it_does_not_close_it(tmp_path, cadence):
    runs = tmp_path / "runs2"
    _run(runs, "20261022-live-cd-90", sha=_sha(cadence, 2), kind="live", request="cd-90", block="E4", reward=0.0,
         started="2026-10-22T00:00:00Z")
    _run(runs, "20261023-P1-cadence-haiku-1", sha=_sha(cadence, 0), request="cd-90")
    row = {**ROW, "run_ids": ["20261022-live-cd-90"]}
    assert findings.compute(row, runs, cadence)[0] == "open"
    _run(runs, "20261023-P2-cadence-haiku-1", sha=_sha(cadence, 0), task="P2")  # another request closes it
    assert findings.compute(row, runs, cadence)[0] == "closed"


def test_open_while_a_later_run_still_fails_the_same_way(runs, cadence):
    _run(runs, "20261023-P1-cadence-haiku-1", sha=_sha(cadence, 0), reward=0.5)
    _run(runs, "20261023-P2-cadence-haiku-1", sha=_sha(cadence, 0), task="P2", block="E4", reward=0.5)
    status, why = findings.compute(ROW, runs, cadence)
    assert status == "open" and "20261023-P2-cadence-haiku-1" in why


def test_open_when_the_failure_is_gone_but_the_score_fell(tmp_path, cadence):
    runs = tmp_path / "runs3"
    _run(runs, FOUND, sha=_sha(cadence, 2), block="E4", reward=0.7143, started="2026-10-22T00:00:00Z")
    _run(runs, "20261023-P1-cadence-haiku-1", sha=_sha(cadence, 0), reward=0.2857)
    status, why = findings.compute(ROW, runs, cadence)
    assert status == "open" and "fell" in why


def test_a_hand_set_close_is_refused_and_update_writes_the_computed_status(tmp_path, runs, cadence):
    path = _write(tmp_path, {**ROW, "status": "closed"})
    assert any("the records give 'open'" in p for p in findings.check(path, runs, cadence))
    findings.update(path, runs, cadence)
    assert findings.load(path)[0]["status"] == "open"
    assert findings.check(path, runs, cadence) == []


def test_the_committed_findings_resolve_to_records_and_are_open_without_a_fix():
    rows = findings.load()
    assert rows, "findings.jsonl is empty"
    assert [p for row in rows for p in findings.row_problems(row, ROOT / "runs")] == []
    assert findings.check(findings.FINDINGS, ROOT / "runs", None) == []
