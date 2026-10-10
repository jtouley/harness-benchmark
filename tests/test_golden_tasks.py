"""Golden-task hygiene that golden-check does not cover."""

from __future__ import annotations

from cbench.grade import task_dirs, task_digest
from cbench.util import GOLDEN_DIR

LEDGERLITE = ("T04-ledgerlite-multicurrency", "T05-ledgerlite-budgets", "T06-ledgerlite-audit-undo")


def test_ledgerlite_tasks_share_one_base_repo():
    """T04-T06 compare harnesses on the same starting code. A drift in one copy breaks that."""
    digests = {name: task_digest(GOLDEN_DIR / "tasks" / name / "repo") for name in LEDGERLITE}
    assert len(set(digests.values())) == 1, digests


def test_ledgerlite_tasks_share_one_hidden_fixture():
    texts = {(GOLDEN_DIR / "tasks" / n / "hidden" / "_cli.py").read_text(encoding="utf-8") for n in LEDGERLITE}
    assert len(texts) == 1


def test_reference_patches_hold_no_run_notes():
    """Rule 4 in docs/methodology.md: the patch is the solution only."""
    for task in task_dirs():
        patch = (task / "reference.patch").read_text(encoding="utf-8")
        assert "diff --git a/docs/adr/" not in patch, task.name
        assert ".context/" not in patch, task.name
