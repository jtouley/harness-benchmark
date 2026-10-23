"""The live-run records (loop.backfill_live) count for nothing, point at the evidence and reproduce from it."""

from __future__ import annotations

import gzip
import json
import os
from pathlib import Path

import pytest

from loop import backfill_live, check, record

ROOT = Path(__file__).resolve().parents[1]
CADENCE = Path(os.environ.get("HB_CADENCE_CHECKOUT", ROOT.parent / "cadence"))
LIVE = sorted(p for p in (ROOT / "runs").iterdir() if (p / "record.json").exists()
              and record.load(p)["kind"] == "live" and record.load(p)["provenance"]["source"] == "backfill")


def test_the_committed_live_records_count_for_nothing_and_name_their_evidence():
    assert len(LIVE) == 55
    for run in LIVE:
        rec = record.load(run)
        assert rec["counts"] == {"counts": False, "why": backfill_live.WHY}, run.name
        assert not (run / "scores.jsonl").exists(), run.name
        assert rec["batch"] in (backfill_live.BATCH_E2E, backfill_live.BATCH_ARMS)
        assert any(e.startswith("jtouley/cadence@") for e in rec["provenance"]["evidence"]), run.name
        assert "claimed by the session that ran it" in rec["provenance"]["note"], run.name
        if rec["task"] in ("d1", "d2", "d3", "d4", "P1", "P2"):
            assert (ROOT / "golden" / "cadence" / f"{rec['task']}.md").exists(), run.name
        for blob in (rec["transcript"], rec["tree"]):
            assert blob["sha256"] is None or blob["store"].startswith("git:jtouley/cadence@"), run.name


def test_the_e2e_batch_has_the_51_runs_and_the_arms_batch_the_four():
    batches = {}
    for run in LIVE:
        batches.setdefault(record.load(run)["batch"], []).append(run.name)
    assert len(batches[backfill_live.BATCH_E2E]) == 51
    assert len(batches[backfill_live.BATCH_ARMS]) == 4
    assert {n.split("-", 1)[1].rsplit("-cadence", 1)[0] for n in batches[backfill_live.BATCH_E2E]} >= {
        "d1-run1", "d2-run1", "d3-run1", "d4-run1", "q1-run2", "u1-run2", "z3-run1", "k6-run2"}


def test_parsing_the_evidence_tables():
    requests = backfill_live.parse_requests("# x\n\n## Request 3\n\nUsed by: d1-run1.sh, q1-run1.sh\n\n```text\nA\n```\n"
                                            "\n## Request 7\n\nUsed by: q1-run2.sh\n\n```text\nB\n```\n")
    assert requests == {"d1-run1.sh": 3, "q1-run1.sh": 3, "q1-run2.sh": 7}
    rows = backfill_live.parse_records_table(
        "| Run | Model | Cost USD | Exit | R7 | Request | Edge | Scope | Deferral | Script note |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        "| d1/run1 | claude-haiku-5-5 | 0.56 | claude exit 0 | True | 10/10 | 8/11 | 1/1 | 1/2 | cadence e2e d1 |\n"
        "| c/run1 | claude-sonnet-5-5 | 4.25 | claude exit 0 | True | - | - | - | - | note |\n")
    assert rows["d1-run1"]["r7"] is True and rows["d1-run1"]["edge"] == "8/11"
    assert rows["c-run1"]["request"] == "-"
    driver = backfill_live.parse_driver('#!/bin/bash\n# header\nPROMPT=\'secret\'\nclaude -p "$PROMPT" --model haiku '
                                        '--plugin-dir "$E/cadence-plugin-d1" --dangerously-skip-permissions '
                                        '--output-format stream-json --verbose > out 2> err < /dev/null\n')
    assert driver == {"copy": "cadence-plugin-d1", "model_flag": "haiku",
                      "flags": ["--dangerously-skip-permissions", "--output-format", "stream-json", "--verbose"]}
    assert "secret" not in json.dumps(driver)
    assert backfill_live.named_commit("# cadence-plugin-q: driver scripts name ['fb0270d']") == "fb0270d"
    assert backfill_live.named_commit("# cadence-plugin-d1: driver scripts name no commit") is None
    assert backfill_live.exit_code("x\nclaude exit 0\n") == 0 and backfill_live.exit_code("exit 2\n2026") == 2
    assert backfill_live.exit_code("") is None
    lines = ['{"type":"system","timestamp":"2026-10-21T13:00:28.387Z"}', "not json",
             '{"type":"result","timestamp":"2026-10-21T13:36:53.035Z","duration_ms":10}']
    assert backfill_live.transcript_times(lines) == ("2026-10-21T13:00:28Z", "2026-10-21T13:36:53Z")
    assert backfill_live.wall_seconds("2026-10-21T13:00:28Z", "2026-10-21T13:36:53Z") == 2185.0
    assert backfill_live.wall_seconds(None, "2026-10-21T13:36:53Z") is None


@pytest.mark.skipif(not backfill_live.available(CADENCE), reason="no jtouley/cadence checkout with the evidence "
                    "commits (set HB_CADENCE_CHECKOUT; git fetch origin evidence/7058c2b0 evidence/08495c94)")
def test_the_committed_live_records_are_reproduced_from_the_evidence(tmp_path):
    assert backfill_live.main(["--cadence", str(CADENCE), "--runs", str(tmp_path)]) == 0
    built = sorted(p.name for p in tmp_path.iterdir())
    assert built == [p.name for p in LIVE]
    for name in built:
        assert (tmp_path / name / "record.json").read_text() == (ROOT / "runs" / name / "record.json").read_text(), name
    assert check.validate_tree(tmp_path) == []
    # A record names the transcript it was read from by sha256 of the original bytes.
    rec = record.load(tmp_path / "20261021-d1-run1-cadence-haiku")
    raw = backfill_live._show(CADENCE, backfill_live.E2E, rec["transcript"]["path"])
    assert len(gzip.decompress(raw)) == rec["transcript"]["bytes"]
