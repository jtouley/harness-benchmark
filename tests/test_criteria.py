"""docs/criteria.md rules hold in the files that carry them (PR #5 review N3)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRITERIA = (ROOT / "docs" / "criteria.md").read_text(encoding="utf-8")


def test_baseline_drive_prompt_is_the_issue_only():
    """criteria §2: the baseline gets the task text and nothing about how to work."""
    lock = json.loads((ROOT / "frameworks.lock.json").read_text(encoding="utf-8"))
    assert lock["frameworks"]["baseline"]["drive_prompt"] == "{issue}"


def test_live_tier_defers_to_the_criteria_decision_rule():
    assert "criteria.md" in (ROOT / "docs" / "live-tier.md").read_text(encoding="utf-8")


def test_live_tier_trial_count_is_the_criteria_sample():
    n = int(re.search(r"runs exactly \*\*(\d+) times\*\*", CRITERIA).group(1))
    live = (ROOT / "scripts" / "live.sh").read_text(encoding="utf-8")
    assert int(re.search(r'trials="\$\{TRIALS:-(\d+)\}"', live).group(1)) == n


def test_live_tier_runs_every_golden_task():
    live = (ROOT / "scripts" / "live.sh").read_text(encoding="utf-8")
    listed = set(re.search(r"^tasks=\(([^)]*)\)", live, re.M).group(1).split())
    golden = {p.parent.name.lower() for p in (ROOT / "golden" / "tasks").glob("*/task.json")}
    assert listed == golden
