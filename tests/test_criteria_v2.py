"""docs/criteria-v2.md pins: load-bearing constants and wording (PR #20 review R1-R8, N2-N4, O1).

Like tests/test_criteria.py does for v1, each test reads the document as committed and fails when a
decision input changes without a deliberate edit here.
"""

from __future__ import annotations

import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2 = (ROOT / "docs" / "criteria-v2.md").read_text(encoding="utf-8")


def _section(heading: str) -> str:
    """The text from `heading` to the next heading of the same or a higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    start = V2.index(heading)
    nxt = re.search(rf"^#{{1,{level}}} ", V2[start + len(heading):], re.M)
    return V2[start: start + len(heading) + (nxt.start() if nxt else len(V2))]


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def test_decision_constants_are_v1s():
    """§8.1-§8.3: seed, resamples, interval, task minimum, A thresholds and the B margin."""
    rule = _flat(_section("## 8. Decision rule"))
    for fixed in (
        "10,000 times, seed 20261010",
        "5th and 95th percentiles (a 90% percentile interval)",
        "at least **3 tasks**",
        "by at least 0.5",
        "a tolerance of 0.05",
        "minus 10 points",
        "more than 10× the cost",
        "a margin of **0.25**",
    ):
        assert fixed in rule, fixed


def test_live_tier_trial_count_is_the_v2_cell_size():
    """§4.4: n = 5 per cell, and scripts/live.sh runs that many trials."""
    n = int(re.search(r"runs exactly \*\*(\d+) times\*\*", V2).group(1))
    live = (ROOT / "scripts" / "live.sh").read_text(encoding="utf-8")
    assert int(re.search(r'trials="\$\{TRIALS:-(\d+)\}"', live).group(1)) == n == 5


def test_every_difference_has_a_fixed_direction():
    """R1: §8.1 fixes the subtraction order per comparison, and §8.2-§8.4 use it."""
    unit = _flat(_section("### 8.1 Units and interval"))
    assert "Comparison A (§8.2), defects: **mean(Haiku one-shot) − mean(H)**" in unit
    assert "Comparison B (§8.3), defects: **mean(H) − mean(bar)**" in unit
    assert "Comparison C (§8.4), pass rate: **pass rate(H) − pass rate(bar)**" in unit
    assert "mean(Haiku one-shot) − mean(H) is entirely above 0" in _flat(_section("### 8.2 "))
    assert "mean(H) − mean(bar) stays under that margin" in _flat(_section("### 8.3 "))
    assert "pass rate(H) − pass rate(bar) is entirely above 0" in _flat(_section("### 8.4 "))


def _bootstrap_95th(a: list[int], b: list[int], reps: int = 10_000) -> float:
    """95th percentile of mean(a) − mean(b), resampled within each cell (§8.1)."""
    rng = random.Random(20261010)
    out = sorted(
        sum(rng.choice(a) for _ in a) / len(a) - sum(rng.choice(b) for _ in b) / len(b)
        for _ in range(reps)
    )
    return out[int(0.95 * reps)]


def test_noninferiority_direction_rejects_a_worse_harness():
    """R1: with mean(H) − mean(bar), a harness with 0.8 defects/run fails against a defect-free bar."""
    bar, harness = [0, 0, 0, 0, 0], [1, 1, 1, 1, 0]
    assert _bootstrap_95th(harness, bar) > 0.25   # the pinned order: not non-inferior
    assert _bootstrap_95th(bar, harness) < 0.25   # the reversed order would wrongly pass


def test_calibration_has_one_try_count_for_both_classes():
    """R2: §3.1 fixes 5 tries; both §3.2 thresholds are over those 5; §10 matches."""
    assert "exactly **5 tries** per task" in _flat(_section("### 3.1 Calibration"))
    classes = _flat(_section("### 3.2 The two task classes"))
    assert "passes at most **2 of 5** calibration tries" in classes
    assert "passes **5 of 5** calibration tries" in classes
    assert "1 of 3" not in classes
    assert "Under §3.2 (at most 2 of 5) they are beyond candidates" in _flat(_section("## 10. "))


def test_non_clean_verdicts_split_by_cause_with_a_rerun_cap():
    """R3: setup verdicts rerun at most 2 per cell; contaminated is attempted, not delivered."""
    gate = _flat(_section("### 5.2 Clean-room gating"))
    assert "at most **2 reruns per cell**" in gate
    assert 'reported as **"unassessable"**' in gate
    assert "**`contaminated`** (caused by an agent action" in gate
    assert "is an **attempted run that is not delivered** (§8.1). It is not run again." in gate
    assert "**Stage-0 transcript check.**" in gate


def test_budget_stop_schedules_round_robin_and_reports_incomplete():
    """R4: round-robin scheduling; a short cell makes the class result 'incomplete'."""
    caps = _flat(_section("### 5.3 Caps and the run-set budget"))
    assert "Run k of every cell starts before run k+1 of any cell" in caps
    unit = _flat(_section("### 8.1 Units and interval"))
    assert "every cell of that class at n = 5 attempted runs" in unit
    assert 'the class result is **"incomplete"**' in unit


def test_model_rules_are_scoped_as_the_source_scopes_them():
    """R5: [OD] scopes Opus and Sonnet to Cadence; the wider rule is [v2] with §2.2 as the exception."""
    arms = _flat(_section("## 2. Arms"))
    assert "Opus never orchestrates a Cadence run [OD]" in arms
    assert "Sonnet 5.5 runs no Cadence arm [OD]" in arms
    assert "the §2.2 arms are the only exceptions [v2]" in arms
    assert "never runs a harness arm" not in arms
    assert "runs no harness arm" not in arms


def test_cadence_arm_is_gated_on_deferral_review():
    """R6: the deferral reviewer is a harness requirement, so Cadence also waits for #68."""
    assert "jtouley/cadence#68 (deferral review, §2.5)" in _section("### 2.1 Arms in the v2 run set")
    assert "the deferral review is a harness requirement" in _flat(_section("### 2.5 Deferral review"))


def test_top_design_tier_has_an_order_and_a_scope():
    """R7: §8.5 is per class and ranks design lexicographically."""
    answer = _flat(_section("### 8.5 The answer"))
    assert "The answer is computed **per class**" in answer
    assert (
        "follow-up success (higher is better), then edit radius (smaller is better), then the share of "
        "design-checklist items answered yes (higher is better), then duplicated lines on new code "
        "(lower is better)"
    ) in answer


def test_guard_cap_hit_is_an_attempted_run():
    """R8: a one-shot that hits the guard cap is attempted and not delivered, also tallied separately."""
    unit = _flat(_section("### 8.1 Units and interval"))
    assert "a one-shot run that hits the guard time cap (§5.3)" in unit
    assert "a guard-cap run are attempted runs that are not delivered" in unit


def test_reviewer_picks_await_owner_confirmation():
    """§11 lists every review pick as proposed, not decided."""
    open_items = _flat(_section("## 11. Open before the first v2 run set"))
    assert "**Proposed, owner to confirm**" in open_items
    for topic in ("§3.1", "§5.2, §8.1", "§5.3, §8.1", "§2.1, §2.5", "(§8.1)", "(§8.5)"):
        assert topic in open_items, topic
    assert "Status: **draft**" in V2


def test_tool_gate_coverage_is_new_code_lines_only():
    """N2: the gate is new-code line coverage; whole-package line and branch coverage is reported."""
    gate = _section("### 4.2 Layer 2: the tool gate")
    assert "| New-code line coverage | ≥ 80% |" in gate
    assert "| Line and branch coverage of the whole package | Reported, not gated |" in gate


def test_pass_one_is_the_beyond_decision_input():
    """N4: §4.4 says that pass^1 decides §8.4."""
    assert 'pass^1 is the pass rate that decides "beyond the bar" (§8.4)' in _flat(
        _section("### 4.4 Reliability (pass^k)")
    )


def _github_slugs(md: str) -> set[str]:
    """GitHub heading anchors: lowercase, punctuation dropped, spaces to hyphens."""
    slugs = set()
    for heading in re.findall(r"^#{1,6} (.+)$", md, re.M):
        slugs.add(re.sub(r"\s", "-", re.sub(r"[^\w\- ]", "", heading.strip().lower())))
    return slugs


def test_every_relative_link_and_anchor_resolves():
    """N3: every relative link in v2 points at a file, and every anchor at a GitHub heading slug."""
    docs = ROOT / "docs"
    for target in re.findall(r"\]\(([^)\s]+)\)", V2):
        if target.startswith(("http://", "https://")):
            continue
        path, _, anchor = target.partition("#")
        dest = (docs / path).resolve() if path else docs / "criteria-v2.md"
        assert dest.exists(), target
        if anchor:
            assert anchor in _github_slugs(dest.read_text(encoding="utf-8")), target
