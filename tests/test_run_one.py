"""scripts/run_one.sh: one benchmark run from a fresh container. Only the parts that run before any clone."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_one(tmp_path, *args, **env):
    return subprocess.run(["bash", str(ROOT / "scripts" / "run_one.sh"), *args], capture_output=True, text=True,
                          env={**os.environ, "HOME": str(tmp_path / "home"), **env})


def test_the_work_folder_is_never_under_home(tmp_path):
    """Run 20261024-P1-cadence-haiku-core-1r: the work folder was $HOME/run-one, so its plugin clone sat under
    HOME, where the driver's other-checkout scan finds it, and the driver tests that scan HOME refused to run
    in the publish step's ci_local (test_the_driver_refuses_p4_without_holdout and the postmortem test)."""
    proc = _run_one(tmp_path, "20261024-P1-cadence-haiku-core-9", "--dry-run",
                    RUN_ONE_WORK=str(tmp_path / "home" / "run-one"))
    assert proc.returncode == 2 and "under HOME" in proc.stderr
    assert not (tmp_path / "home" / "run-one").exists()


def test_the_default_work_folder_is_outside_home():
    text = (ROOT / "scripts" / "run_one.sh").read_text(encoding="utf-8")
    assert 'WORK=${RUN_ONE_WORK:-/var/tmp/run-one}/$RID' in text


def test_a_run_id_without_a_shape_is_refused(tmp_path):
    proc = _run_one(tmp_path, "20261024-P1-cadence-haiku-1")
    assert proc.returncode == 2 and "core|full" in proc.stderr


def test_the_cadence_commit_comes_from_the_batch_pin_by_shape(tmp_path):
    """batches/2026-10-24-shapes.json pins a cadence commit per shape; run_one.sh takes its CADENCE_SHA from it
    and refuses another one before anything is cloned."""
    work = tmp_path / "work"
    proc = _run_one(tmp_path, "20261024-P1-cadence-haiku-full-9", "--dry-run", RUN_ONE_WORK=str(work),
                    CADENCE_SHA="085bfdcd00254594ed5f22387e4316f667e59ec7", BATCH="2026-10-24-shapes")
    assert proc.returncode == 2 and "is not the pin" in proc.stderr and "d3c2ffe" in proc.stderr
    for shape in ("core", "full"):  # the default batch, round 2: one commit for both shapes
        proc = _run_one(tmp_path, f"20261024-P1-cadence-haiku-{shape}-4", "--dry-run", RUN_ONE_WORK=str(work),
                        CADENCE_SHA="085bfdcd00254594ed5f22387e4316f667e59ec7")
        assert proc.returncode == 2 and "2026-10-24-shapes-r2.json" in proc.stderr
        assert "2100c6e6aa99d99309cfa8e7f8c5cee1018584b4" in proc.stderr
    assert not work.exists()
    proc = _run_one(tmp_path, "20261024-P1-cadence-haiku-core-9", "--dry-run", RUN_ONE_WORK=str(work),
                    BATCH="2026-10-24-no-such-batch")
    assert proc.returncode == 2 and "batches/2026-10-24-no-such-batch.json" in proc.stderr


def test_the_grader_is_the_batch_pins_grader_commit_not_the_harness_head(tmp_path):
    """Every 2026-10-24-shapes-r2 score names grader c344bea, the harness HEAD the run was cloned at, while the
    batch pins 10172ce: run_one.sh graded with HB_SHA. The grader is a worktree at the pin, the grade runs it
    (host_trial --grader-root) and the driver records it (--grader-repo); another GRADER_SHA is refused."""
    work = tmp_path / "work"
    proc = _run_one(tmp_path, "20261024-P1-cadence-haiku-core-9", "--dry-run", RUN_ONE_WORK=str(work),
                    GRADER_SHA="c344bea44951cfc5a3a3a99aaa598fdaaedabba8")
    assert proc.returncode == 2 and "is not the grader_commit" in proc.stderr
    assert "10172ce8e7564d61b9ff17a3fe2b625269b0e37c" in proc.stderr
    assert not work.exists()
    text = (ROOT / "scripts" / "run_one.sh").read_text(encoding="utf-8")
    assert '--grader-repo "$GRADER"' in text and '--grader-root "$GRADER"' in text
    assert 'worktree add -q --detach "$GRADER" "$GRADER_SHA"' in text
    assert '--grader-repo "$WORK/hb"' not in text


def test_finish_needs_the_runs_saved_directory(tmp_path):
    proc = _run_one(tmp_path, "20261024-P2-cadence-haiku-core-9", "--finish", RUN_ONE_WORK=str(tmp_path / "work"))
    assert proc.returncode == 2 and "--finish: no" in proc.stderr and "transcript.jsonl" in proc.stderr
    assert _run_one(tmp_path, "20261024-P2-cadence-haiku-core-9", "--bogus").returncode == 2


def test_again_only_goes_with_finish(tmp_path):
    proc = _run_one(tmp_path, "20261024-P2-cadence-haiku-core-9", "--dry-run", "--again")
    assert proc.returncode == 2 and "--again goes with --finish" in proc.stderr
    assert _run_one(tmp_path, "20261024-P2-cadence-haiku-core-9", "--finish", "--twice").returncode == 2


# --- --detach and --wait (2026-10-24: the Bash tool's 2 h timeout killed P1 core-1 and core-3 with their
# process group; a detached run is in its own session and a caller waits for it in steps of at most 110 min)

RID = "20261024-P2-cadence-haiku-core-9"


def _detach(tmp_path, cmd: str, **env):
    work = tmp_path / "work"
    env = {"RUN_ONE_WORK": str(work), "RUN_ONE_DETACH_CMD": cmd, **env}
    return work / RID, _run_one(tmp_path, RID, "--detach", **env), env


def test_a_detached_run_leaves_its_caller_and_wait_reports_it_running_then_finished(tmp_path):
    flag = tmp_path / "go"
    work, proc, env = _detach(tmp_path, f"while [ ! -e {flag} ]; do sleep 0.2; done; echo 'P2: 4/7, stop R7'")
    assert proc.returncode == 0, proc.stderr
    pid = int((work / "run.pid").read_text())
    assert os.getsid(pid) == pid != os.getsid(0)   # its own session: a killed caller's process group is not its
    still = _run_one(tmp_path, RID, "--wait", RUN_ONE_WAIT_SECONDS="1", RUN_ONE_POLL_SECONDS="0.2", **env)
    assert still.returncode == 75 and "still running" in still.stdout
    flag.touch()
    done = _run_one(tmp_path, RID, "--wait", RUN_ONE_WAIT_SECONDS="30", RUN_ONE_POLL_SECONDS="0.2", **env)
    assert done.returncode == 0, done.stderr
    assert "finished, exit 0" in done.stdout and "P2: 4/7, stop R7" in done.stdout
    assert "P2: 4/7, stop R7" in (work / "run.log").read_text()


def test_wait_passes_on_the_runs_own_exit_code_in_its_report_and_a_second_detach_is_refused(tmp_path):
    work, proc, env = _detach(tmp_path, "echo 'run_one: a check before publishing failed'; exit 3")
    assert proc.returncode == 0
    done = _run_one(tmp_path, RID, "--wait", RUN_ONE_POLL_SECONDS="0.2", **env)
    assert done.returncode == 0 and "finished, exit 3" in done.stdout
    again = _run_one(tmp_path, RID, "--detach", **env)
    assert again.returncode == 2 and "exists" in again.stderr


def test_wait_without_a_detached_run_and_a_killed_run_are_errors(tmp_path):
    env = {"RUN_ONE_WORK": str(tmp_path / "work")}
    assert _run_one(tmp_path, RID, "--wait", **env).returncode == 2
    work = tmp_path / "work" / RID
    work.mkdir(parents=True)
    dead = subprocess.Popen(["true"])
    dead.wait()
    (work / "run.pid").write_text(f"{dead.pid}\n")
    proc = _run_one(tmp_path, RID, "--wait", RUN_ONE_POLL_SECONDS="0.2", **env)
    assert proc.returncode == 1 and "ended without an exit code" in proc.stdout


def test_the_detached_run_itself_may_start_in_the_folder_detach_made(tmp_path):
    """The detached command is run_one.sh itself: it refuses an existing $WORK unless that holds only run.pid
    and run.log (it then stops at the next setup check, here the unset proxy)."""
    work = tmp_path / "work" / RID
    work.mkdir(parents=True)
    (work / "run.pid").write_text("1\n")
    (work / "run.log").write_text("")
    env = {"RUN_ONE_WORK": str(tmp_path / "work"), "RUN_ONE_DETACHED": "1", "HTTPS_PROXY": ""}
    proc = _run_one(tmp_path, RID, **env)
    assert proc.returncode == 2 and "exists" not in proc.stderr and "HTTPS_PROXY" in proc.stderr
    (work / "stray").write_text("")
    proc = _run_one(tmp_path, RID, **env)
    assert proc.returncode == 2 and "exists" in proc.stderr


# --- the summary line (run 20261024-P1-cadence-haiku-core-4, PR #115: passed 2, reward 0.0, stream_ok false; the
# scoreboard showed 0.00 MISS while the finished line, the commit message and pr.md printed "2/7")

def _voided_record(tmp_path) -> Path:
    import json
    run = tmp_path / "runs" / "20261024-P1-cadence-haiku-core-4"
    run.mkdir(parents=True)
    (run / "record.json").write_text(json.dumps({
        "run_id": run.name, "batch": "2026-10-24-shapes-r2",
        "stop_point": {"block": "R2", "reason": "hard stop retries: R2 test-benchmark gate FAIL"},
        "timing": {"agent_wall_seconds": 4278.3}, "counts": {"counts": True, "why": "driver run"},
        "cadence": {"sha": "2100c6e6aa99", "tree": "be0094b1"}}))
    (run / "scores.jsonl").write_text(json.dumps({"passed": 2, "total": 7, "reward": 0.0, "stream_ok": False,
                                                  "idempotent": True, "run_id": run.name}) + "\n")
    return run


def test_the_summary_headline_is_the_scoreboard_score_not_the_passed_count(tmp_path):
    """A run with passed > 0 and reward 0 reads score 0/7 (round(reward x total), scoreboard._passed), then the
    grader's own passed, reward, stream_ok and idempotent. run_one.sh prints it the way the publish step runs it:
    the system python3 with this checkout on PYTHONPATH."""
    from loop import scoreboard
    run = _voided_record(tmp_path)
    proc = subprocess.run(["python3", "-m", "loop.run_summary", str(run)], capture_output=True, text=True,
                          env={**os.environ, "PYTHONPATH": str(ROOT)}, cwd=tmp_path)
    assert proc.returncode == 0, proc.stderr
    line = proc.stdout.strip()
    assert line.startswith("20261024-P1-cadence-haiku-core-4: score 0/7; passed 2/7, reward 0.0, stream_ok false, "
                           "idempotent true; stop R2 (hard stop retries")
    assert ": 2/7" not in line
    assert scoreboard._passed({"passed": 2, "total": 7, "reward": 0.0}) == 0
    text = (ROOT / "scripts" / "run_one.sh").read_text(encoding="utf-8")
    assert 'SUMMARY=$(PYTHONPATH="$(cd "$(dirname "$0")/.." && pwd)" python3 -m loop.run_summary "$REC")' in text
    assert "s[-1]['passed']" not in text
    for use in ('-m "$BATCH: $RID\n\n$SUMMARY"', "**Score:** $SUMMARY", 'echo "$SUMMARY"'):
        assert use in text   # the commit message, pr.md and the last log line (what --wait prints) all use it


def test_a_full_score_and_a_missing_reward_keep_passed(tmp_path):
    from loop import run_summary
    assert run_summary.score_text({"passed": 5, "total": 7, "reward": 0.7143, "stream_ok": True,
                                   "idempotent": True}).startswith("score 5/7; passed 5/7, reward 0.7143")
    assert run_summary.score_text({"passed": 3, "total": 7}).startswith("score 3/7; passed 3/7, reward None")
    assert run_summary.score_text(None).startswith("score none")


def test_correct_record_text_replaces_only_the_score_line(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("correct_record_text", ROOT / "scripts" / "correct_record_text.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    from loop import run_summary
    summary = run_summary.summary(_voided_record(tmp_path))
    old = "Record of batch b.\n\n**Score:** 20261024-P1-cadence-haiku-core-4: 2/7, stop R2 (x)\n\nRan on cadence c.\n"
    new = mod.corrected_body(old, summary)
    assert new == old.replace("20261024-P1-cadence-haiku-core-4: 2/7, stop R2 (x)", summary)
    assert mod.corrected_body("no score here", summary).startswith(f"**Score:** {summary}\n\n")
    message = mod.commit_message("2026-10-24-shapes-r2", "20261024-P1-cadence-haiku-core-4", summary)
    assert message.startswith("2026-10-24-shapes-r2: 20261024-P1-cadence-haiku-core-4: score text corrected\n\n"
                              "20261024-P1-cadence-haiku-core-4: score 0/7; passed 2/7")
    source = (ROOT / "scripts" / "correct_record_text.py").read_text(encoding="utf-8")
    assert "--force" not in source.replace('"worktree", "remove", "--force"', "") and "+HEAD" not in source
