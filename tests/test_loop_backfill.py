"""The backfilled run records are what loop.backfill builds from the committed evidence, byte for byte."""

from __future__ import annotations

from pathlib import Path

import pytest

from loop import backfill, check

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(not backfill.available(), reason="the evidence commits are not fetched "
                                "(git fetch origin ccr-3d2e0c73-lr6bdt ccr-35b43d50-uw8iyb)")


def test_the_committed_backfill_is_reproduced_from_the_evidence(tmp_path):
    assert backfill.main(["--runs", str(tmp_path)]) == 0
    built = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file())
    committed = sorted(p.relative_to(ROOT / "runs").as_posix() for p in (ROOT / "runs").rglob("*")
                       if p.is_file() and p.parent != ROOT / "runs" and p.name in ("record.json", "scores.jsonl")
                       and p.parent.name[:8] in ("20261015", "20261019", "20261021", "20261022"))
    assert built == committed
    for rel in built:
        assert (tmp_path / rel).read_text() == (ROOT / "runs" / rel).read_text(), rel
    assert check.validate_tree(tmp_path) == []


def test_no_backfilled_run_counts_without_a_grader_score():
    for rec, scores in backfill.build():
        if rec["counts"]["counts"]:
            assert scores, rec["run_id"]
        assert rec["provenance"]["source"] == "backfill"
        assert all(s["source"] == "backfill" for s in scores)
