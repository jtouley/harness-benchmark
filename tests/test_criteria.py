"""docs/criteria.md rules hold in the files that carry them (PR #5 review N3)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

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


def test_v1_caps_are_fixed_history():
    """criteria v1 §6 Caps: v1 is history, so its caps stay 1800 s, $1.00 and $3.00."""
    assert re.search(r"agent timeout of \*\*(\d+) s\*\*", CRITERIA).group(1) == "1800"
    assert re.search(r"\*\*\$(\d+\.\d\d)\*\*\s+for Haiku arms", CRITERIA).group(1) == "1.00"
    assert re.search(r"\*\*\$(\d+\.\d\d)\*\* for the Sonnet baseline", CRITERIA).group(1) == "3.00"


def _v2_guard_cap_seconds() -> float | None:
    """The one-shot guard time cap that criteria v2 §5.3 records, or None while it is not recorded."""
    v2 = (ROOT / "docs" / "criteria-v2.md").read_text(encoding="utf-8")
    m = re.search(r"One-shot guard time cap: \*\*(\d+) s\*\*", v2)
    return float(m.group(1)) if m else None


def test_trial_caps_are_the_criteria_caps():
    """criteria v1 §6 Caps match the code.

    The live.sh dollar caps are always checked. The harbor timeout is checked against v1, and the
    check is skipped only when the code carries the timeout that criteria v2 §5.3 records.
    """
    m = re.search(r"agent timeout of \*\*(\d+) s\*\*", CRITERIA)
    haiku = re.search(r"\*\*\$(\d+\.\d\d)\*\*\s+for Haiku arms", CRITERIA)
    base = re.search(r"\*\*\$(\d+\.\d\d)\*\* for the Sonnet baseline", CRITERIA)
    harbor = (ROOT / "cbench" / "harbor.py").read_text(encoding="utf-8")
    live = (ROOT / "scripts" / "live.sh").read_text(encoding="utf-8")
    assert f'haiku_cap="${{HAIKU_CAP_USD:-{haiku.group(1)}}}"' in live
    assert f'base_cap="${{BASELINE_CAP_USD:-{base.group(1)}}}"' in live
    timeout = float(re.search(r'agent_timeout="([\d.]+)"', harbor).group(1))
    v2_cap = _v2_guard_cap_seconds()
    if v2_cap is not None and timeout == v2_cap and timeout != float(m.group(1)):
        pytest.skip("the code carries the criteria v2 §5.3 timeout; the v1 timeout is history")
    assert timeout == float(m.group(1))
