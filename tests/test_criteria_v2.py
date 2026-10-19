"""docs/method/criteria-v2.md pins: load-bearing constants and wording (PR #20 review R1-R8, N2-N4, O1, NEW-1-NEW-8, N-8).

Like tests/test_criteria.py does for v1, each test reads the document as committed and fails when a
decision input changes without a deliberate edit here.
"""

from __future__ import annotations

import itertools
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2 = (ROOT / "docs" / "method" / "criteria-v2.md").read_text(encoding="utf-8")


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


def _bootstrap(a: list[float], b: list[float], reps: int = 10_000) -> tuple[float, float]:
    """5th and 95th percentiles of mean(a) − mean(b), resampled within each cell (§8.1)."""
    rng = random.Random(20261010)
    out = sorted(
        sum(rng.choice(a) for _ in a) / len(a) - sum(rng.choice(b) for _ in b) / len(b)
        for _ in range(reps)
    )
    return out[int(0.05 * reps)], out[int(0.95 * reps)]


def _bootstrap_95th(a: list[float], b: list[float]) -> float:
    return _bootstrap(a, b)[1]


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
    assert "**Every `contaminated` verdict** counts against the arm" in gate
    assert "**attempted run that is not delivered** (§8.1). It is not run again." in gate


def test_host_loaded_instruction_files_are_allowlisted_not_excused():
    """NEW-7 (b): no setup-fault exception for host-loaded files; stage 0 allowlists them instead."""
    gate = _flat(_section("### 5.2 Clean-room gating"))
    assert "**Setup faults** are infrastructure errors: `exposed` and `unassessable`." in gate
    assert "There is no exception for instruction files that the host loads" in gate
    assert "stage 0 adds **each arm's host-loaded instruction paths**" in gate
    assert "to its `--allow-path`" in gate
    assert "whose only causes are instruction files" not in gate


def test_stage_zero_requires_a_clean_smoke_run_per_arm():
    """NEW-1: stage 0 needs a `clean` verdict with the run-set allowlists, not only a skill listing."""
    gate = _flat(_section("### 5.2 Clean-room gating"))
    assert "Each arm then runs one smoke run in the Harbor container" in gate
    assert "The arm is admitted only when that run gets a **`clean` verdict**." in gate
    assert "The clean smoke run checks that the allowlists cover the setup" in gate  # N-10
    assert "`contaminated` verdict is treated as coming from the agent" in gate
    assert "memory files if any" in gate
    assert "proves" not in gate
    assert "Stage-0 transcript check" not in V2


def test_rerun_cap_counts_graded_runs_and_covers_container_losses():
    """NEW-5: the cap ends at fewer than 5 graded runs; §5.3 infrastructure losses share it."""
    gate = _flat(_section("### 5.2 Clean-room gating"))
    assert "still has **fewer than 5 graded runs**" in gate
    assert "Infrastructure losses under §5.3 (for example a container-runtime failure) share the same 2 reruns" in gate
    assert "It shares the cell's 2 reruns of §5.2" in _flat(_section("### 5.3 Caps and the run-set budget"))


def test_budget_stop_schedules_round_robin_and_reports_incomplete():
    """R4: round-robin scheduling; a short cell makes the class result 'incomplete'."""
    caps = _flat(_section("### 5.3 Caps and the run-set budget"))
    assert "Run k of every cell starts before run k+1 of any cell" in caps
    unit = _flat(_section("### 8.1 Units and interval"))
    assert "H's result for that comparison is **\"incomplete\"**" in unit


def test_incomplete_is_scoped_to_the_arm_and_its_comparator():
    """NEW-3: a short cell blocks only the claims that use it; §8.5 needs every matching arm complete."""
    unit = _flat(_section("### 8.1 Units and interval"))
    assert (
        "needs H's cells and its comparator's cells of that class (the Haiku one-shot for comparison A, "
        "the bar for comparisons B and C) at n = 5 attempted runs"
    ) in unit
    assert "A short cell of another arm does not block H's claim." in unit
    assert "every cell of that class" not in unit


def test_model_rules_are_scoped_as_the_source_scopes_them():
    """R5: [OD] scopes Opus and Sonnet to Cadence; the wider rule is [v2] with §2.2 as the exception."""
    arms = _flat(_section("## 2. Arms"))
    assert "Opus never orchestrates a Cadence run [OD]" in arms
    assert "Sonnet 5.5 runs no Cadence arm [OD]" in arms
    assert "except the §2.2 review-loop comparison arm [v2]" in arms  # NEW-4
    assert "only exceptions" not in arms
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
        "follow-up success (higher is better), then edit radius (smaller is better), then duplicated "
        "lines on new code (lower is better)"
    ) in answer
    assert "Two arms **tie** on a measure when the 90% interval of their difference includes 0." in answer  # NEW-6


def test_top_design_tier_test_is_one_sided():
    """NEW-2: an arm leaves the tier only when it is worse beyond noise, never when it is better."""
    answer = _flat(_section("### 8.5 The answer"))
    assert "The test is **one-sided**" in answer
    assert "oriented so that a positive value is worse for that measure" in answer
    assert "**5th percentile of that interval is ≤ 0** for every measure" in answer
    assert "includes 0) [v2]" not in answer  # the two-sided rule is gone


def test_one_sided_tier_keeps_an_arm_that_is_better_on_a_later_measure():
    """NEW-2 witness: much smaller edit radius than the best arm (smaller is better)."""
    best, arm = [40.0, 42, 38, 41, 39], [10.0, 12, 9, 11, 10]
    lo, hi = _bootstrap(arm, best)        # arm − best; positive is worse for edit radius
    assert lo <= 0                        # one-sided rule: stays in the tier
    assert not (lo <= 0 <= hi)            # the old two-sided rule would have dropped it


def test_guard_cap_hit_is_an_attempted_run():
    """R8: a one-shot that hits the guard cap is attempted and not delivered, also tallied separately."""
    unit = _flat(_section("### 8.1 Units and interval"))
    assert "a one-shot run that hits the guard time cap (§5.3)" in unit
    assert "a guard-cap run are attempted runs that are not delivered" in unit


def test_reviewer_picks_await_owner_confirmation():
    """§11 lists every review pick as proposed, not decided."""
    open_items = _flat(_section("## 11. Open before the first v2 run set"))
    assert "**Proposed, owner to confirm**" in open_items
    for topic in ("§3.1", "§5.2, §8.1", "§5.3, §8.1", "§2.1, §2.5", "(§8.1)", "(§8.5)",
                  "must get a `clean` verdict for each arm", "the tier test is one-sided"):
        assert topic in open_items, topic
    assert "Status: **draft**" in V2


def test_tool_gate_coverage_is_new_code_lines_only():
    """N2: the gate is new-code line coverage; whole-package line and branch coverage is reported."""
    gate = _section("### 4.2 Layer 2: the tool gate")
    assert "| New-code line coverage | ≥ 80% | `new_code_coverage_at_least_80` |" in gate
    assert "| Line and branch coverage of the whole package | Reported, not gated | none |" in gate


def test_every_gate_key_in_quality_metrics_has_a_row_in_the_tool_gate():
    """NEW-9: each key of the `gate` dict in scripts/quality_metrics.py is a row of §4.2, and back."""
    code = (ROOT / "scripts" / "quality_metrics.py").read_text(encoding="utf-8")
    block = re.search(r'result\["gate"\] = \{(.*?)\n    \}', code, re.S).group(1)
    keys = set(re.findall(r'^\s*"(\w+)":', block, re.M))
    assert "new_code_duplication_at_most_3" in keys
    gate = _section("### 4.2 Layer 2: the tool gate")
    rows = set(re.findall(r"^\|[^|]*\|[^|]*\| `(\w+)` \|", gate, re.M))
    assert rows == keys


def test_duplication_is_gated_and_ranked_and_built_scripts_are_not_open():
    """NEW-9: §4.2 gates duplication at 3%; §4.3 ranks it; §11 no longer lists built scripts."""
    gate = _section("### 4.2 Layer 2: the tool gate")
    assert "| Duplicated lines on new code (`jscpd`, §4.3) | ≤ 3% | `new_code_duplication_at_most_3` |" in gate
    design = _flat(_section("### 4.3 Layer 3: design fit and the owner criteria"))
    assert "Both a layer-2 gate condition (≤ 3%, §4.2) and a layer-3 ranking measure (§8.5)" in design
    assert "`edit_radius.package` in `quality_metrics.py`" in design
    open_items = _flat(_section("## 11. Open before the first v2 run set"))
    assert "`jscpd` duplication, the import-graph coupling script, the edit radius" not in open_items


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
    docs = ROOT / "docs" / "method"
    for target in re.findall(r"\]\(([^)\s]+)\)", V2):
        if target.startswith(("http://", "https://")):
            continue
        path, _, anchor = target.partition("#")
        dest = (docs / path).resolve() if path else docs / "criteria-v2.md"
        assert dest.exists(), target
        if anchor:
            assert anchor in _github_slugs(dest.read_text(encoding="utf-8")), target


# NEW-8: the best arm is chosen against the current leader (§8.5 step 2).
# Each measure: (name, higher_is_better). Witness data from the PR #20 re-review (cycle.py).
_MEASURES = [("follow_up", True), ("edit_radius", False)]
_CYCLE = {
    "A": {"follow_up": [1.0, 1, 1, 1, 1], "edit_radius": [40.0, 41, 39, 40, 40]},
    "B": {"follow_up": [1.0, 1, 1, 1, 0], "edit_radius": [25.0, 26, 24, 25, 25]},
    "C": {"follow_up": [1.0, 1, 0, 0, 0], "edit_radius": [10.0, 11, 9, 10, 10]},
}


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def _tie(a: list[float], b: list[float]) -> bool:
    lo, hi = _bootstrap(a, b)
    return lo <= 0 <= hi


def _best_arm(arms: dict, order: list[str]) -> str:
    """§8.5 step 2 as written: keep the leader and its ties, measure by measure."""
    kept = list(order)
    leader = kept[0]
    for name, higher in _MEASURES:
        sign = 1 if higher else -1
        leader = max(kept, key=lambda arm: sign * _mean(arms[arm][name]))
        kept = [arm for arm in kept if arm == leader or _tie(arms[arm][name], arms[leader][name])]
        if len(kept) == 1:
            return kept[0]
    return leader


def _pairwise_winner(arms: dict, x: str, y: str) -> str:
    """The old rule: the first measure that does not tie decides between two arms."""
    for name, higher in _MEASURES:
        if not _tie(arms[x][name], arms[y][name]):
            better = _mean(arms[x][name]) > _mean(arms[y][name])
            return x if better == higher else y
    return x


def test_pairwise_lexicographic_order_cycles_on_the_witness():
    """NEW-8 witness: with interval ties, the pairwise order is A < B < C < A."""
    assert _pairwise_winner(_CYCLE, "A", "B") == "B"
    assert _pairwise_winner(_CYCLE, "B", "C") == "C"
    assert _pairwise_winner(_CYCLE, "A", "C") == "A"


def test_best_arm_against_the_leader_is_unique_on_the_witness():
    """NEW-8: the leader rule gives one best arm, whatever order the arms are listed in."""
    results = {_best_arm(_CYCLE, list(order)) for order in itertools.permutations(_CYCLE)}
    assert results == {"B"}


def test_best_arm_rule_wording():
    answer = _flat(_section("### 8.5 The answer"))
    assert "The **best arm** is chosen **step by step against the current leader**" in answer
    assert "keep the leader and every kept arm that ties with the leader, and drop the others" in answer
    assert "lexicographic" not in answer
    assert "the best arm is chosen step by step against the current leader" in _flat(
        _section("## 11. Open before the first v2 run set")
    )


def test_incomplete_arm_is_listed_beside_the_answer():
    """N-8: an arm with an incomplete B or C result does not leave §8.5 silently."""
    answer = _flat(_section("### 8.5 The answer"))
    assert 'It is listed beside the answer as "incomplete".' in answer
    assert 'If it could still change the answer, the answer is "incomplete"' in answer


def test_no_measure_is_decided_by_judgment():
    """#41: code decides every measure; a reviewer may only propose tests that code confirms."""
    measures = _flat(_section("## 4. Measures"))
    assert "**No measure is decided by a model's or a person's judgment**" in measures
    assert "Blind reviewers" not in measures and "Pairwise judging (two or three LLM judges" not in measures
    assert "Design checklist |" not in measures
    checks = _flat(_section("## 6. Defect checks"))
    assert "fails on at least one wrong variant" in checks and "sha256 is recorded" in checks
    # The reviewer is kept in line: tests only, confirmed by code, run against every arm, severity by rule.
    assert "Its only output is executable reproduction tests" in checks
    assert "use the task's public interface" in checks and "does not count as failing" in checks
    assert "a second, independently written correct solution committed with the task" in checks
    assert "Every kept test runs against every arm's code" in checks
    assert "count as one defect, however many the reviewer wrote" in checks
    assert "A failing kept test is a major defect, never critical" in checks
    assert "The reviewer's own words about severity are not used" in checks
    assert "test-confirmed" not in _flat(_section("### 4.4 Reliability (pass^k)"))
    assert "reports success" not in _flat(_section("### 8.1 Units and interval"))
    audit = _flat(_section("## 7. Traceability: the audit protocol"))
    assert "a script scores its answers, and no person or model scores them" in audit
    assert "the first commit where the check gives the trap's stored wrong answer" in audit
    assert "spot check" not in audit
    assert "design-checklist" not in _flat(_section("### 8.5 The answer"))
    # Every ranking and report beside the answer has a rule a script can apply.
    answer = _flat(_section("### 8.5 The answer"))
    assert "rank on traceability (§7), by the same step-by-step procedure and tie rule" in answer
    assert "Origin accuracy is reported, not ranked" in answer
    assert "A script reports which declared items exist" in _flat(_section("### 4.7 Auditability (M10)"))
    assert "a kept test that fails on exactly the same runs as a frozen check is dropped" in checks
