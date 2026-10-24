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
                    CADENCE_SHA="085bfdcd00254594ed5f22387e4316f667e59ec7")
    assert proc.returncode == 2 and "is not the pin" in proc.stderr and "d3c2ffe" in proc.stderr
    assert not work.exists()
    proc = _run_one(tmp_path, "20261024-P1-cadence-haiku-core-9", "--dry-run", RUN_ONE_WORK=str(work),
                    BATCH="2026-10-24-no-such-batch")
    assert proc.returncode == 2 and "batches/2026-10-24-no-such-batch.json" in proc.stderr
