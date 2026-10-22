"""The learning loop's run records: schema, append-only writes, the blob store, the plugin-tree check
and the driver (loop/)."""

from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from loop import check, driver, record, store

ROOT = Path(__file__).resolve().parents[1]


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                           *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def minimal(run_id: str = "20261021-P1-cadence-core-haiku-1", **over) -> dict:
    rec = {
        "schema": 1, "run_id": run_id, "kind": "benchmark", "batch": "2026-10-21-cadence-core-subscription",
        "provenance": {"source": "driver", "evidence": []}, "task": "P1", "request_id": "gh-1",
        "arm": "cadence-core", "cadence": None, "model_requested": "claude-haiku-5-5",
        "models_served": ["claude-haiku-5-5"], "command": ["true"], "started_at": "2026-10-21T00:00:00Z",
        "ended_at": "2026-10-21T00:01:00Z", "exit_code": 0, "cost": {"list_usd": "0.10", "reported_usd": 0.12},
        "stop_point": {"block": "E4", "reason": "credentials"}, "transcript": {"sha256": None, "missing": "x"},
        "tree": {"sha256": None, "missing": "x"}, "counts": {"counts": True, "why": "graded by the grader"},
    }
    rec.update(over)
    return rec


# --- schema -------------------------------------------------------------------------------------------

def test_a_complete_record_validates():
    assert record.validate(minimal(), record.RECORD_SCHEMA) == []


@pytest.mark.parametrize("run_id", ["run 3", "P1-haiku-1", "2026-10-21-P1", "20261021-", "20261021-P1_x",
                                    "20261021--P1"])
def test_a_run_id_must_be_a_date_then_dash_separated_words(run_id):
    assert record.validate(minimal(run_id), record.RECORD_SCHEMA)
    assert not record.RUN_ID.fullmatch(run_id)


def test_missing_fields_unknown_fields_and_wrong_types_are_refused():
    rec = minimal()
    del rec["models_served"]
    rec["graded_by_me"] = True
    rec["exit_code"] = "0"
    errors = record.validate(rec, record.RECORD_SCHEMA)
    assert any("models_served" in e for e in errors)
    assert any("graded_by_me" in e for e in errors)
    assert any("exit_code" in e for e in errors)


def test_a_score_must_name_the_harness_benchmark_grader_commit():
    score = {"run_id": "20261021-P1-x", "grader": {"repo": "jtouley/cadence", "commit": "abc1234", "tree": None},
             "reward": 0.0, "passed": 0, "total": 7, "idempotent": False, "stream_ok": True, "error": None,
             "source": "driver", "graded_at": None}
    assert any("grader.repo" in e for e in record.validate(score, record.SCORE_SCHEMA))
    score["grader"]["repo"] = "jtouley/harness-benchmark"
    assert record.validate(score, record.SCORE_SCHEMA) == []


# --- append-only writes -------------------------------------------------------------------------------

def test_a_record_is_written_once(tmp_path):
    path = record.write_record(tmp_path, minimal())
    assert json.loads(path.read_text())["run_id"] == "20261021-P1-cadence-core-haiku-1"
    with pytest.raises(record.RecordError, match="already exists"):
        record.write_record(tmp_path, minimal())


def test_an_invalid_record_is_not_written(tmp_path):
    with pytest.raises(record.RecordError, match="run_id"):
        record.write_record(tmp_path, minimal("P1-haiku-1"))
    assert not any(tmp_path.iterdir())


def test_scores_are_appended_and_need_a_record(tmp_path):
    score = {"run_id": "20261021-P1-cadence-core-haiku-1",
             "grader": {"repo": "jtouley/harness-benchmark", "commit": "abc1234", "tree": None},
             "reward": 0.0, "passed": 0, "total": 7, "idempotent": False, "stream_ok": True, "error": None,
             "source": "driver", "graded_at": None}
    with pytest.raises(record.RecordError, match="no record"):
        record.append_score(tmp_path, score)
    record.write_record(tmp_path, minimal())
    record.append_score(tmp_path, score)
    record.append_score(tmp_path, {**score, "source": "regrade", "reward": 0.5})
    rows = record.scores(tmp_path / "20261021-P1-cadence-core-haiku-1")
    assert [r["reward"] for r in rows] == [0.0, 0.5]
    with pytest.raises(record.RecordError, match="run_id"):
        record.append_score(tmp_path, {**score, "run_id": "20261021-P2-other"})


def test_the_check_refuses_a_changed_or_deleted_record_and_allows_new_ones_and_new_scores(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    runs = repo / "runs"
    record.write_record(runs, minimal())
    (runs / "20261021-P1-cadence-core-haiku-1" / "scores.jsonl").write_text('{"a": 1}\n')
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD")

    record.write_record(runs, minimal("20261021-P1-cadence-core-haiku-2"))
    with open(runs / "20261021-P1-cadence-core-haiku-1" / "scores.jsonl", "a") as f:
        f.write('{"b": 2}\n')
    assert check.append_only(repo, base) == []

    (runs / "20261021-P1-cadence-core-haiku-1" / "scores.jsonl").write_text('{"b": 2}\n')
    path = runs / "20261021-P1-cadence-core-haiku-1" / "record.json"
    path.write_text(path.read_text().replace('"E4"', '"R7"'))
    problems = check.append_only(repo, base)
    assert any("record.json" in p and "changed" in p for p in problems)
    assert any("scores.jsonl" in p and "rewritten" in p for p in problems)
    path.unlink()
    assert any("deleted" in p for p in check.append_only(repo, base))


def test_every_committed_record_validates():
    assert check.validate_tree(ROOT / "runs") == []


# --- the blob store -----------------------------------------------------------------------------------

def test_the_store_keeps_a_gzipped_copy_named_by_the_sha256_of_the_original(tmp_path):
    src = tmp_path / "transcript.jsonl"
    src.write_bytes(b'{"type":"result"}\n' * 100)
    blob = store.put(src, tmp_path / "store")
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    assert blob["sha256"] == digest and blob["bytes"] == src.stat().st_size
    assert blob["store"] == store.STORE and blob["path"] == f"blobs/{digest}.gz"
    assert gzip.decompress((tmp_path / "store" / blob["path"]).read_bytes()) == src.read_bytes()
    assert store.put(src, tmp_path / "store") == blob  # idempotent
    assert store.verify(blob, tmp_path / "store")


# --- the plugin tree ----------------------------------------------------------------------------------

@pytest.fixture
def plugin(tmp_path) -> Path:
    origin = tmp_path / "cadence.git"
    _git(tmp_path, "init", "-q", "--bare", str(origin))
    repo = tmp_path / "cadence"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "plugin.json").write_text("{}")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "c1")
    _git(repo, "remote", "add", "origin", str(origin))
    _git(repo, "push", "-q", "origin", "main")
    _git(repo, "fetch", "-q", "origin")
    return repo


def test_a_clean_published_plugin_tree_gives_its_commit(plugin):
    info = driver.plugin_commit(plugin)
    assert info["sha"] == _git(plugin, "rev-parse", "HEAD") and info["tree_clean"] is True
    assert info["published_in"] == ["origin/main"]


@pytest.mark.parametrize("change", ["modified", "untracked", "ignored", "unpublished", "subdir"])
def test_a_plugin_tree_that_differs_from_a_published_commit_is_refused(plugin, change):
    target = plugin
    if change == "modified":
        (plugin / "plugin.json").write_text('{"patched": true}')
    elif change == "untracked":
        (plugin / "hotfix.py").write_text("")
    elif change == "ignored":
        (plugin / ".gitignore").write_text("*.local\n")
        _git(plugin, "add", ".gitignore")
        _git(plugin, "commit", "-qm", "ignore")
        _git(plugin, "push", "-q", "origin", "main")
        _git(plugin, "fetch", "-q", "origin")
        (plugin / "patch.local").write_text("")
    elif change == "unpublished":
        (plugin / "plugin.json").write_text('{"local": true}')
        _git(plugin, "commit", "-qam", "local only")
    elif change == "subdir":
        (plugin / "sub").mkdir()
        target = plugin / "sub"
    with pytest.raises(driver.DriverError):
        driver.plugin_commit(target)


# --- the driver ---------------------------------------------------------------------------------------

TRANSCRIPT = [
    {"type": "system", "subtype": "init", "session_id": "s-1", "model": "claude-haiku-5-5",
     "claude_code_version": "2.1.307"},
    {"type": "assistant", "message": {"model": "claude-haiku-5-5", "content": []}},
    {"type": "assistant", "message": {"model": "claude-sonnet-5-5", "content": []}},
    {"type": "result", "session_id": "s-1", "total_cost_usd": 0.5,
     "modelUsage": {"claude-haiku-5-5": {"inputTokens": 1000000, "outputTokens": 0,
                                         "cacheCreationInputTokens": 0, "cacheReadInputTokens": 0}}},
]


def test_the_transcript_gives_the_models_actually_served_the_session_and_the_cost():
    facts = driver.transcript_facts([json.dumps(e) for e in TRANSCRIPT] + ["not json"])
    assert facts["models_served"] == ["claude-haiku-5-5", "claude-sonnet-5-5"]
    assert facts["session_id"] == "s-1" and facts["claude_version"] == "2.1.307"
    assert facts["cost"]["reported_usd"] == 0.5 and facts["cost"]["list_usd"] is not None


def _drive(tmp_path, plugin, extra=(), script="", grade=None):
    out = tmp_path / "trial"
    body = (f"mkdir -p {out} && printf '%s\\n' " + " ".join(f"'{json.dumps(e)}'" for e in TRANSCRIPT)
            + f" > {out}/transcript.jsonl" + (f" && echo '{json.dumps(grade)}' > {out}/grade.json" if grade else "")
            + (f" && {script}" if script else ""))
    argv = ["--run-id", "20261022-P1-cadence-haiku-1", "--kind", "stub", "--batch", "2026-10-22-stub",
            "--task", "P1", "--request-id", "gh-1", "--arm", "cadence", "--model", "claude-haiku-5-5",
            "--plugin-dir", str(plugin), "--runs", str(tmp_path / "runs"), "--store", str(tmp_path / "store"),
            "--transcript", str(out / "transcript.jsonl"), *extra, "--", "bash", "-c", body]
    return driver.main(argv), tmp_path / "runs" / "20261022-P1-cadence-haiku-1"


def test_the_driver_runs_the_command_and_writes_a_valid_record(tmp_path, plugin):
    rc, run = _drive(tmp_path, plugin)
    assert rc == 0
    rec = json.loads((run / "record.json").read_text())
    assert record.validate(rec, record.RECORD_SCHEMA) == []
    assert rec["provenance"]["source"] == "driver"
    assert rec["cadence"]["sha"] == _git(plugin, "rev-parse", "HEAD")
    assert rec["models_served"] == ["claude-haiku-5-5", "claude-sonnet-5-5"]
    assert rec["command"][:2] == ["bash", "-c"] and rec["exit_code"] == 0
    assert rec["started_at"] <= rec["ended_at"]
    assert store.verify(rec["transcript"], tmp_path / "store")
    # Eligibility only; a run is scored by the scores.jsonl lines the grader adds.
    assert rec["counts"]["counts"] is True
    assert not (run / "scores.jsonl").exists()


def test_the_driver_refuses_a_patched_plugin_before_running_anything(tmp_path, plugin):
    (plugin / "plugin.json").write_text('{"patched": true}')
    rc, run = _drive(tmp_path, plugin, script=f"touch {tmp_path}/ran")
    assert rc == 2 and not run.exists() and not (tmp_path / "ran").exists()


def test_the_driver_refuses_a_run_id_that_exists(tmp_path, plugin):
    assert _drive(tmp_path, plugin)[0] == 0
    assert _drive(tmp_path, plugin)[0] == 2


def test_a_grade_from_the_benchmark_grader_becomes_a_score_with_the_grader_identity(tmp_path, plugin):
    grade = {"reward": 0.4286, "passed": 3, "total": 7, "idempotent": True, "stream_ok": True}
    rc, run = _drive(tmp_path, plugin, extra=["--grade", str(tmp_path / "trial" / "grade.json"),
                                              "--grader-repo", str(ROOT)], grade=grade)
    assert rc == 0
    (score,) = record.scores(run)
    assert score["reward"] == 0.4286 and score["source"] == "driver"
    assert score["grader"]["commit"] == _git(ROOT, "rev-parse", "HEAD")
    assert score["grader"]["tree"] == _git(ROOT, "rev-parse", "HEAD:golden/pipeline/pipetask")


def test_the_driver_is_a_module_with_help():
    proc = subprocess.run([sys.executable, "-m", "loop.driver", "--help"], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0 and "--plugin-dir" in proc.stdout
