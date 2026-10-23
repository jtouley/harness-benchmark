"""The learning loop's run records: schema, append-only writes, the blob store, the plugin-tree check
and the driver (loop/)."""

from __future__ import annotations

import gzip
import hashlib
import json
import shlex
import shutil
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
        "timing": {"agent_wall_seconds": None, "run_wall_seconds": None, "agent_active_seconds": None, "blocks": None},
        "isolation": None,
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
             "grader": {"repo": "jtouley/harness-benchmark", "commit": "abc1234", "tree": "a" * 40},
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


def test_only_a_backfilled_score_may_leave_the_grader_unknown_and_it_says_why(tmp_path):
    record.write_record(tmp_path, minimal())
    score = {"run_id": "20261021-P1-cadence-core-haiku-1",
             "grader": {"repo": "jtouley/harness-benchmark", "commit": None, "tree": None},
             "reward": 0.0, "passed": 0, "total": 7, "idempotent": False, "stream_ok": True, "error": None,
             "source": "driver", "graded_at": None}
    with pytest.raises(record.RecordError, match="only a backfill"):
        record.append_score(tmp_path, score)
    with pytest.raises(record.RecordError, match="basis"):
        record.append_score(tmp_path, {**score, "source": "backfill"})
    record.append_score(tmp_path, {**score, "source": "backfill",
                                   "grader": {**score["grader"], "basis": "not recorded at grading time"}})


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
    {"type": "result", "session_id": "s-1", "duration_ms": 1500, "total_cost_usd": 0.4,
     "modelUsage": {"claude-haiku-5-5": {"inputTokens": 1, "outputTokens": 0,
                                         "cacheCreationInputTokens": 0, "cacheReadInputTokens": 0}}},
    {"type": "result", "session_id": "s-1", "duration_ms": 1000, "total_cost_usd": 0.5,
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
    if "--cwd" not in extra:  # a work folder and a HOME that hold no Cadence copy
        (tmp_path / "work").mkdir(exist_ok=True)
        argv[-4:-4] = ["--cwd", str(tmp_path / "work")]
    if "--fresh-home" not in extra:
        argv[-4:-4] = ["--fresh-home", str(tmp_path / f"home-{len(list(tmp_path.glob('home-*')))}")]
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
    # A stub never counts; a run is scored by the scores.jsonl lines the grader adds.
    assert rec["cadence"]["tree_clean"] is True and rec["counts"]["counts"] is False
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


def test_the_driver_refuses_a_grader_with_local_changes(tmp_path, plugin, capsys):
    """--grade needs a clean grader checkout: a modified file under golden/pipeline/pipetask means no commit
    names the grader that scored the run, so the driver refuses before anything runs."""
    grader = tmp_path / "grader"
    (grader / "golden" / "pipeline" / "pipetask").mkdir(parents=True)
    (grader / "golden" / "pipeline" / "pipetask" / "grade.py").write_text("ok = True\n")
    _git(grader, "init", "-q", "-b", "main")
    _git(grader, "add", "-A")
    _git(grader, "commit", "-qm", "grader")
    (grader / "golden" / "pipeline" / "pipetask" / "grade.py").write_text("ok = False\n")  # a local change
    rc, run = _drive(tmp_path, plugin, extra=["--grade", str(tmp_path / "trial" / "grade.json"),
                                              "--grader-repo", str(grader)], grade={"reward": 1.0})
    assert rc == 2 and "local changes" in capsys.readouterr().err
    assert not run.exists() and not (tmp_path / "trial").exists()  # refused before the command ran


def test_the_driver_is_a_module_with_help():
    proc = subprocess.run([sys.executable, "-m", "loop.driver", "--help"], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0 and "--plugin-dir" in proc.stdout


# --- a run that only compiles the plugin's Python still counts (review of #61)

def _with_hook(plugin: Path) -> Path:
    (plugin / "hooks").mkdir()
    (plugin / "hooks" / "guard.py").write_text("X = 1\n")
    _git(plugin, "add", "-A")
    _git(plugin, "commit", "-qm", "hook")
    _git(plugin, "push", "-q", "origin", "main")
    _git(plugin, "fetch", "-q", "origin")
    return plugin


def test_bytecode_written_into_the_plugin_during_the_run_does_not_make_it_unclean(tmp_path, plugin):
    _with_hook(plugin)
    leaves_bytecode = (f"mkdir -p {plugin}/hooks/__pycache__ && touch {plugin}/hooks/__pycache__/guard.cpython-312.pyc "
                       f"{plugin}/stray.pyc")
    rc, run = _drive(tmp_path, plugin, script=leaves_bytecode)
    rec = json.loads((run / "record.json").read_text())
    assert rc == 0 and rec["cadence"]["tree_clean"] is True


def test_the_command_runs_without_writing_bytecode(tmp_path, plugin):
    _with_hook(plugin)
    imports_the_hook = f"cd {plugin}/hooks && {sys.executable} -c 'import guard'"
    rc, run = _drive(tmp_path, plugin, script=imports_the_hook)
    assert rc == 0 and not (plugin / "hooks" / "__pycache__").exists()
    assert json.loads((run / "record.json").read_text())["cadence"]["tree_clean"] is True


@pytest.mark.parametrize("change", ["echo patched >> {p}/plugin.json", "touch {p}/hotfix.py"])
def test_a_run_that_changes_or_adds_plugin_source_does_not_count(tmp_path, plugin, change):
    rc, run = _drive(tmp_path, plugin, script=change.format(p=plugin))
    rec = json.loads((run / "record.json").read_text())
    assert rec["cadence"]["tree_clean"] is False and rec["counts"]["counts"] is False


def test_a_plugin_with_bytecode_before_the_run_is_still_refused(plugin):
    (plugin / "__pycache__").mkdir()
    (plugin / "__pycache__" / "x.pyc").write_text("")
    with pytest.raises(driver.DriverError):
        driver.plugin_commit(plugin)


# --- isolation: no other Cadence checkout the run can reach

def _cadence_copy(where: Path) -> Path:
    (where / ".claude-plugin").mkdir(parents=True)
    (where / ".claude-plugin" / "plugin.json").write_text('{"name": "cadence"}')
    return where


def test_other_cadence_checkouts_under_the_roots_are_found_and_the_plugin_is_not(tmp_path, plugin):
    (plugin / ".claude-plugin").mkdir()
    (plugin / ".claude-plugin" / "plugin.json").write_text('{"name": "cadence"}')
    home = tmp_path / "home"
    copy = _cadence_copy(home / ".cache" / "src" / "cadence-core@abc")
    _cadence_copy(home / "node_modules" / "x")  # skipped folder
    assert driver.other_checkouts([home, plugin], plugin) == [str(copy)]


def test_the_driver_refuses_a_run_that_can_reach_another_cadence_checkout(tmp_path, plugin):
    work = tmp_path / "work"
    _cadence_copy(work / "cadence-core")
    rc, run = _drive(tmp_path, plugin, extra=["--cwd", str(work)], script=f"touch {tmp_path}/ran")
    assert rc == 2 and not run.exists() and not (tmp_path / "ran").exists()


def test_a_fresh_home_is_empty_and_is_recorded(tmp_path, plugin):
    home = tmp_path / "fresh"
    rc, run = _drive(tmp_path, plugin, extra=["--fresh-home", str(home)], script=f'echo "$HOME" > {tmp_path}/home.txt')
    assert rc == 0 and (tmp_path / "home.txt").read_text().strip() == str(home)
    iso = json.loads((run / "record.json").read_text())["isolation"]
    assert iso["home"] == str(home) and iso["fresh_home"] is True and iso["other_cadence_checkouts"] == []


def test_a_fresh_home_that_exists_and_is_not_empty_is_refused(tmp_path, plugin):
    home = tmp_path / "fresh"
    home.mkdir()
    (home / ".bashrc").write_text("")
    assert _drive(tmp_path, plugin, extra=["--fresh-home", str(home)])[0] == 2


# --- timing: the same fields for a one-shot and a Cadence run

def test_the_record_has_time_per_block_from_the_runs_context(tmp_path, plugin):
    ctx = tmp_path / "ctx"
    (ctx / "attest").mkdir(parents=True)
    (ctx / "attest" / "r.calls.jsonl").write_text('{"tool_use_id": "t", "stage": "plan-review", "decision": "allow"}\n')
    (ctx / "attest" / "r.joins.jsonl").write_text('{"tool_use_id": "t", "agent_id": "a"}\n')
    (ctx / "attest" / "r.agents.jsonl").write_text('{"agent_id": "a", "event": "start", "at": 10}\n'
                                                   '{"agent_id": "a", "event": "stop", "at": 70}\n')
    rc, run = _drive(tmp_path, plugin, extra=["--context", str(ctx)])
    blocks = json.loads((run / "record.json").read_text())["timing"]["blocks"]
    assert blocks == {"plan-review": {"seconds": 60.0, "calls": 1, "unfinished": 0}}


def test_the_record_has_wall_agent_and_active_time(tmp_path, plugin):
    timing = tmp_path / "timing.json"
    timing.write_text('{"agent_seconds": 61.5}')
    rc, run = _drive(tmp_path, plugin, extra=["--timing", str(timing)])
    t = json.loads((run / "record.json").read_text())["timing"]
    assert t["agent_wall_seconds"] == 61.5
    assert t["run_wall_seconds"] >= 0
    assert t["agent_active_seconds"] == 2.5  # the transcript's result lines: 1500 + 1000 ms
    assert t["blocks"] is None


# --- the entry: the only prompt a Cadence run gets is `/cadence <spec path>` (owner, 2026-10-22)

def _spec(tmp_path) -> Path:
    spec = tmp_path / "spec" / "spec.md"
    spec.parent.mkdir(exist_ok=True)
    spec.write_text("Build the thing.\n\n1. It works.\n")
    return spec


def test_a_cadence_benchmark_run_without_a_spec_is_refused(tmp_path, plugin):
    rc, run = _drive(tmp_path, plugin, extra=["--kind", "benchmark"], script=f"touch {tmp_path}/ran")
    assert rc == 2 and not run.exists() and not (tmp_path / "ran").exists()


def test_a_command_that_gives_the_agent_other_prompt_text_is_refused(tmp_path, plugin):
    spec = _spec(tmp_path)
    rc, run = _drive(tmp_path, plugin, extra=["--kind", "benchmark", "--spec", str(spec)],
                     script=f"claude -p 'Use the cadence skill. /cadence {spec}' ; touch {tmp_path}/ran")
    assert rc == 2 and not run.exists() and not (tmp_path / "ran").exists()


def test_the_command_gets_exactly_slash_cadence_and_the_spec_path_and_the_record_has_the_spec(tmp_path, plugin):
    spec = _spec(tmp_path)
    rc, run = _drive(tmp_path, plugin, extra=["--kind", "benchmark", "--spec", str(spec),
                                              "--agent-argv", str(tmp_path / "argv.json")],
                     script=f'printf %s "$HB_AGENT_PROMPT" > {tmp_path}/prompt.txt')
    assert rc == 0
    assert (tmp_path / "prompt.txt").read_text() == f"/cadence {spec.resolve()}"
    rec = json.loads((run / "record.json").read_text())
    assert record.validate(rec, record.RECORD_SCHEMA) == []
    assert rec["spec"] == {"path": str(spec.resolve()), "sha256": hashlib.sha256(spec.read_bytes()).hexdigest(),
                           "prompt": f"/cadence {spec.resolve()}"}


def test_a_one_shot_gets_the_spec_text_as_its_prompt(tmp_path, plugin):
    spec = _spec(tmp_path)
    rc, run = _drive(tmp_path, plugin, extra=["--kind", "benchmark", "--arm", "one-shot", "--spec", str(spec)],
                     script=f'printf %s "$HB_AGENT_PROMPT" > {tmp_path}/prompt.txt')
    assert rc == 0 and (tmp_path / "prompt.txt").read_text() == spec.read_text()


def test_an_agent_that_ran_with_another_prompt_does_not_count(tmp_path, plugin):
    spec = _spec(tmp_path)
    argv_file = tmp_path / "trial" / "agent-argv.json"
    script = f"""echo '["claude", "-p", "/cadence {spec.resolve()} and be quick"]' > {argv_file}"""
    rc, run = _drive(tmp_path, plugin, extra=["--kind", "benchmark", "--spec", str(spec),
                                              "--agent-argv", str(argv_file)], script=script)
    assert rc == 0
    counts = json.loads((run / "record.json").read_text())["counts"]
    assert counts["counts"] is False and "the agent's argv" in counts["why"]


def test_an_exit_1_at_entry_is_the_recorded_result(tmp_path, plugin):
    """Until /cadence <spec path> works (F-9), the run records what the entry did: the driver adds nothing."""
    spec = _spec(tmp_path)
    stop = tmp_path / "trial" / "stop.json"
    script = f"""echo '{{"block": "A1", "reason": "Cannot determine task ID"}}' > {stop}; exit 1"""
    rc, run = _drive(tmp_path, plugin, extra=["--kind", "benchmark", "--spec", str(spec), "--stop-point-file",
                                              str(stop), "--agent-argv", str(tmp_path / "argv.json")], script=script)
    rec = json.loads((run / "record.json").read_text())
    assert rc == 0 and rec["exit_code"] == 1
    assert rec["stop_point"] == {"block": "A1", "reason": "Cannot determine task ID"}


@pytest.mark.parametrize("tool_input, hit", [
    ({"file_path": "/x/harness-benchmark/golden/pipeline/key/answer_key.json"}, "harness-benchmark"),
    ({"command": "cat ../golden/pipeline/P1/reference/oracle_map.yml"}, "golden/"),
    ({"pattern": "answer", "path": "/srv/pipetask"}, "pipetask"),
    ({"command": "ls /home/user/cadence-main/scripts"}, "/cadence-main"),
])
def test_a_transcript_that_touched_the_benchmark_or_another_checkout_does_not_count(tmp_path, plugin, tool_input, hit):
    event = {"type": "assistant", "message": {"model": "claude-haiku-5-5", "content": [
        {"type": "tool_use", "name": "Bash", "input": tool_input}]}}
    script = f"printf '%s\\n' '{json.dumps(event)}' >> {tmp_path}/trial/transcript.jsonl"
    rc, run = _drive(tmp_path, plugin, script=script)
    rec = json.loads((run / "record.json").read_text())
    assert rc == 0 and rec["counts"]["counts"] is False
    assert any(hit in h for h in rec["isolation"]["contact"]), rec["isolation"]["contact"]
    assert rec["isolation"]["method"] == "host"


def test_a_clean_transcript_records_no_contact():
    assert driver.contact([json.dumps(e) for e in TRANSCRIPT], plugin=Path("/srv/plugin-c458a46")) == []


def test_the_isolation_block_lists_what_the_cwd_held_before_the_run(tmp_path, plugin):
    work = tmp_path / "work"
    (work / "repo").mkdir(parents=True)
    (work / "spec").mkdir()
    rc, run = _drive(tmp_path, plugin, extra=["--cwd", str(work)], script=f"touch {work}/made-by-the-run")
    iso = json.loads((run / "record.json").read_text())["isolation"]
    assert rc == 0 and iso["cwd_contents"] == ["repo/", "spec/"]


@pytest.mark.parametrize("kind, counts", [("benchmark", True), ("live", True), ("stub", False)])
def test_whether_a_clean_run_counts_is_a_function_of_its_kind(tmp_path, plugin, kind, counts):
    """A stub is a probe the session wrote, not a graded run (review of #71); the other kinds may count."""
    rc, run = _drive(tmp_path, plugin, extra=["--kind", kind, "--arm", "one-shot"])
    rec = json.loads((run / "record.json").read_text())
    assert rc == 0 and rec["counts"]["counts"] is counts
    if not counts:
        assert rec["counts"]["why"] == "stub: a session's own probe, not graded"


def test_the_check_refuses_a_counting_record_of_a_kind_that_never_counts(tmp_path):
    runs = tmp_path / "runs"
    for rid, kind, counts in (("20261023-stub-ok", "stub", False), ("20261023-stub-bad", "stub", True),
                              ("20261023-bench-ok", "benchmark", True)):
        rec = minimal(rid, kind=kind, counts={"counts": counts, "why": "x"})
        (runs / rid).mkdir(parents=True)
        (runs / rid / "record.json").write_text(json.dumps(rec))
    problems = check.validate_tree(runs)
    assert problems == ["20261023-stub-bad/record.json: a stub run never counts (counts.counts is true)"]


def test_the_check_refuses_a_counting_backfilled_record_without_a_grader_score(tmp_path):
    """A backfilled record counts only with a score from the harness-benchmark grader (owner, 2026-10-23); its
    commit may be unrecorded (the 15 October baselines say why in grader.basis)."""
    runs = tmp_path / "runs"
    backfill = {"source": "backfill", "evidence": ["ec54dbc"]}
    for rid, score in (("20261015-graded", True), ("20261015-ungraded", False)):
        (runs / rid).mkdir(parents=True)
        (runs / rid / "record.json").write_text(json.dumps(
            minimal(rid, provenance=backfill, counts={"counts": True, "why": "x"})))
        if score:
            record.append_score(runs, {"run_id": rid, "grader": {"repo": "jtouley/harness-benchmark", "commit": None,
                                                              "tree": None, "basis": "not recorded"},
                                       "reward": 0.0, "passed": 0, "total": 7, "idempotent": True, "stream_ok": True,
                                       "error": None, "source": "backfill", "graded_at": None})
    assert check.validate_tree(runs) == [
        "20261015-ungraded/record.json: a backfilled record counts only with a score from the harness-benchmark grader"]


# --- review of #73: every way a claude call can carry other prompt text is refused

@pytest.mark.parametrize("call", [
    "echo hi | claude -p",                           # the prompt from stdin
    "claude 'do it'",                                # a positional prompt
    "claude -p {prompt} 'and more'",                 # a second, positional prompt
    "claude -p {prompt} --append-system-prompt be-quick",  # extra system prompt text
    "claude --print",                                # a bare print flag
])
def test_a_claude_call_with_any_other_prompt_text_is_refused(tmp_path, plugin, call):
    spec = _spec(tmp_path)
    prompt = shlex.quote(f"/cadence {spec.resolve()}")
    rc, run = _drive(tmp_path, plugin, extra=["--kind", "benchmark", "--spec", str(spec), "--agent-argv",
                                              str(tmp_path / "argv.json")],
                     script=f"{call.format(prompt=prompt)}; touch {tmp_path}/ran")
    assert rc == 2 and not run.exists() and not (tmp_path / "ran").exists()


def test_a_cadence_benchmark_run_must_report_the_agents_argv(tmp_path, plugin):
    spec = _spec(tmp_path)
    rc, run = _drive(tmp_path, plugin, extra=["--kind", "benchmark", "--spec", str(spec)], script=f"touch {tmp_path}/ran")
    assert rc == 2 and not run.exists() and not (tmp_path / "ran").exists()


@pytest.mark.parametrize("argv, counts", [
    (["claude", "-p", "{prompt}", "--model", "m", "--output-format", "stream-json", "--verbose"], True),
    (["claude", "-p", "{prompt}", "extra"], False),
    (["claude", "-p", "{prompt}", "--append-system-prompt", "x"], False),
    ([], False),                                     # no argv written: nothing shows what the agent got
])
def test_the_agents_reported_argv_must_be_the_one_prompt_and_known_flags(tmp_path, plugin, argv, counts):
    spec = _spec(tmp_path)
    prompt = f"/cadence {spec.resolve()}"
    argv_file = tmp_path / "trial" / "agent-argv.json"
    write = f"echo {shlex.quote(json.dumps([a.format(prompt=prompt) for a in argv]))} > {argv_file}" if argv else "true"
    rc, run = _drive(tmp_path, plugin, extra=["--kind", "benchmark", "--spec", str(spec), "--agent-argv",
                                              str(argv_file)], script=write)
    assert rc == 0 and json.loads((run / "record.json").read_text())["counts"]["counts"] is counts


@pytest.mark.parametrize("auth", ["proxy", "oauth-file"])
def test_the_isolation_block_names_the_auth_route(tmp_path, plugin, auth):
    rc, run = _drive(tmp_path, plugin, extra=["--auth", auth])
    assert rc == 0 and json.loads((run / "record.json").read_text())["isolation"]["auth"] == auth


def test_the_record_keeps_the_plugins_git_tree_as_well_as_its_commit(tmp_path, plugin):
    """The fingerprint guard and the trace match a plugin by its tree (coordinator, 2026-10-23)."""
    rc, run = _drive(tmp_path, plugin)
    cadence = json.loads((run / "record.json").read_text())["cadence"]
    assert rc == 0 and cadence["tree"] == _git(plugin, "rev-parse", "HEAD^{tree}")


# --- review of #73: a regrade needs a traceable cause, and a batch's scores its pinned grader

def _grader_repo(tmp_path) -> tuple[Path, str, str, str]:
    """A repository with two grader commits: (repo, first commit, its grader tree, second commit)."""
    repo = tmp_path / "hb"
    (repo / "golden/pipeline/pipetask").mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    (repo / "golden/pipeline/pipetask/trial.py").write_text("v = 1\n")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "grader 1")
    first = _git(repo, "rev-parse", "HEAD")
    (repo / "golden/pipeline/pipetask/trial.py").write_text("v = 2\n")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "grader 2")
    return repo, first, _git(repo, "rev-parse", f"{first}:golden/pipeline/pipetask"), _git(repo, "rev-parse", "HEAD")


def _score(commit: str, tree: str, source: str, passed: int, note: str | None = None) -> dict:
    row = {"run_id": "20261023-P1-oneshot-haiku-1", "grader": {"repo": "jtouley/harness-benchmark",
           "commit": commit, "tree": tree}, "reward": passed / 7, "passed": passed, "total": 7, "idempotent": True,
           "stream_ok": True, "error": None, "source": source, "graded_at": None}
    return {**row, "note": note} if note else row


def _run_with(repo: Path, *scores: dict, batch: str = "2026-10-23-batch-f") -> Path:
    runs = repo / "runs"
    run = runs / "20261023-P1-oneshot-haiku-1"
    run.mkdir(parents=True)
    (run / "record.json").write_text(json.dumps(minimal("20261023-P1-oneshot-haiku-1", batch=batch)))
    (run / "scores.jsonl").write_text("".join(json.dumps(s) + "\n" for s in scores))
    return runs


def test_a_forged_regrade_is_refused(tmp_path):
    repo, first, tree1, _ = _grader_repo(tmp_path)
    runs = _run_with(repo, _score(first, tree1, "driver", 0),
                     _score("f" * 40, "f" * 40, "regrade", 7, "looked wrong"))
    problems = check.validate_tree(runs, repo)
    assert any("not a commit of this repository's history" in p for p in problems), problems


def test_a_regrade_on_the_same_tree_needs_a_note_naming_a_grader_or_host_trial_commit(tmp_path):
    repo, first, tree1, second = _grader_repo(tmp_path)
    vague = _run_with(repo, _score(first, tree1, "driver", 0), _score(first, tree1, "regrade", 7, "looked wrong"))
    assert any("regrade without a traceable cause" in p for p in check.validate_tree(vague, repo))
    shutil.rmtree(vague)
    named = _run_with(repo, _score(first, tree1, "driver", 0),
                      _score(first, tree1, "regrade", 5, f"the grader fix {second[:7]}"))
    assert check.validate_tree(named, repo) == []


def test_a_regrade_on_a_new_grader_tree_is_its_own_cause(tmp_path):
    repo, first, tree1, second = _grader_repo(tmp_path)
    tree2 = _git(repo, "rev-parse", f"{second}:golden/pipeline/pipetask")
    runs = _run_with(repo, _score(first, tree1, "driver", 0), _score(second, tree2, "regrade", 5))
    assert check.validate_tree(runs, repo) == []


def test_a_counted_score_must_be_on_the_batch_pin_or_a_later_grader(tmp_path):
    repo, first, tree1, second = _grader_repo(tmp_path)
    tree2 = _git(repo, "rev-parse", f"{second}:golden/pipeline/pipetask")
    (repo / "batches").mkdir()
    (repo / "batches" / "2026-10-23-batch-f.json").write_text(json.dumps({"grader_commit": second}))
    early = _run_with(repo, _score(first, tree1, "driver", 5))
    assert any("not the batch's pinned grader" in p for p in check.validate_tree(early, repo))
    shutil.rmtree(early)
    assert check.validate_tree(_run_with(repo, _score(second, tree2, "driver", 5)), repo) == []


@pytest.mark.parametrize("result, counts", [
    ({"type": "result", "is_error": True, "api_error_status": 429, "api_error": "usage_limit_reached",
      "result": "You've hit your session limit"}, False),
    ({"type": "result", "is_error": True, "api_error_status": 529, "api_error": "overloaded_error"}, False),
    ({"type": "result", "is_error": False, "api_error_status": None, "result": "done"}, True),
])
def test_a_run_the_api_cut_off_is_an_infrastructure_loss_not_a_result(tmp_path, plugin, result, counts):
    """Batch F, 19:27 on 2026-10-23: the account's session limit failed every call with 429 in 2 s, and the
    driver recorded those runs as counted 0/7 results."""
    script = f"printf '%s\\n' {shlex.quote(json.dumps(result))} >> {tmp_path}/trial/transcript.jsonl"
    rc, run = _drive(tmp_path, plugin, extra=["--kind", "benchmark", "--arm", "one-shot"], script=script)
    rec = json.loads((run / "record.json").read_text())
    assert rc == 0 and rec["counts"]["counts"] is counts
    if not counts:
        assert rec["counts"]["why"].startswith("infrastructure loss: the API answered")
