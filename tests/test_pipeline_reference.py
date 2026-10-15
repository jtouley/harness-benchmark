"""The P1 reference passes the grader end to end (the proof that the task is solvable and the key right).

Slow (about three minutes: a virtual environment, two builds, two stream runs against the replay
server), so it runs only with HB_PIPELINE_REFERENCE=1. Needs make and uv on the PATH.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from pipetask import assemble, trial

PIPELINE = Path(__file__).resolve().parents[1] / "golden" / "pipeline"

pytestmark = pytest.mark.skipif(os.environ.get("HB_PIPELINE_REFERENCE") != "1",
                                reason="set HB_PIPELINE_REFERENCE=1 to run the P1 reference trial")


def test_the_p1_reference_passes_every_check_and_rebuilds_identically(tmp_path):
    key = json.loads((PIPELINE / "key" / "answer_key.json").read_text(encoding="utf-8"))
    repo = assemble.assemble("P1", tmp_path / "repo", with_reference=True)
    result = trial.trial(repo, key, PIPELINE / "data" / "capture" / "recentchange.jsonl.gz",
                         seed=key["stream"]["seed"], port=8099, speed=60.0, durations=(30, 90),
                         build_timeout=1800, logs=tmp_path / "logs")
    failed = {n: c for n, c in result["checks"].items() if not c["pass"]}
    assert result["idempotent"], result["changed_by_second_build"]
    assert failed == {}
    assert result["reward"] == 1.0
