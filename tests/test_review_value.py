"""scripts/review_value.py: do review cycles raise new findings that turn out to be real defects?"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("review_value", ROOT / "scripts" / "review_value.py")
rv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rv)


def _row(id_, stage, severity="must-fix", status="open", evidence=None, **extra):
    return {"id": id_, "stage": stage, "severity": severity, "class": "bug", "status": status,
            "evidence": evidence or f"distinct evidence for {id_}", **extra}


def _ledger(tmp_path, rows):
    path = tmp_path / "findings.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def _stage(result, name):
    return next(s for s in result["stages"] if s["stage"] == name)


# --- Ledger -------------------------------------------------------------------------------


def test_confirmed_defects_are_blocking_rows_closed_as_verified_only(tmp_path):
    rows = [
        _row("t-F1", "pr-review-local", status="verified"),
        _row("t-F2", "pr-review-local", status="rejected"),
        _row("t-F3", "pr-review-local", status="deferred"),
        _row("t-F4", "pr-review-local", severity="nit", status="verified"),
        _row("t-F5", "pr-review-local", severity="should-fix", status="verified"),
    ]
    s = _stage(rv.ledger_metrics(rv.read_ledger(_ledger(tmp_path, rows))), "pr-review-local")
    assert (s["raised"], s["blocking"], s["should_fix"], s["confirmed_defects"]) == (5, 3, 1, 1)
    assert s["status"] == {"verified": 3, "rejected": 1, "deferred": 1}


def test_the_last_row_of_an_id_holds_its_final_status(tmp_path):
    rows = [_row("t-F1", "plan-review", status="open"), _row("t-F1", "plan-review", status="verified")]
    result = rv.ledger_metrics(rv.read_ledger(_ledger(tmp_path, rows)))
    s = _stage(result, "plan-review")
    assert (s["raised"], s["confirmed_defects"]) == (1, 1)
    assert result["totals"]["raised"] == 1


def test_an_id_seen_at_an_earlier_stage_is_a_repeat_not_new(tmp_path):
    rows = [_row("t-F1", "plan-review"), _row("t-F1", "adversarial-review"), _row("t-F2", "adversarial-review")]
    result = rv.ledger_metrics(rv.read_ledger(_ledger(tmp_path, rows)))
    assert (_stage(result, "plan-review")["new"], _stage(result, "plan-review")["repeat_id"]) == (1, 0)
    adv = _stage(result, "adversarial-review")
    assert (adv["raised"], adv["new"], adv["repeat_id"]) == (2, 1, 1)


def test_boilerplate_evidence_across_tasks_counts_as_repeat_text(tmp_path):
    rows = [
        _row("cd-1-F1", "architecture-review-plan", severity="nit", evidence="decisions never mention cd-1; add one"),
        _row("cd-2-F1", "architecture-review-plan", severity="nit", evidence="decisions never mention cd-2; add one"),
        _row("cd-3-F1", "architecture-review-plan", severity="nit", evidence="a different problem"),
    ]
    s = _stage(rv.ledger_metrics(rv.read_ledger(_ledger(tmp_path, rows))), "architecture-review-plan")
    assert (s["raised"], s["new"], s["repeat_text"]) == (3, 2, 1)


@pytest.mark.parametrize(
    "text",
    ["the fix for F2 drops the guard", "found in the fix commit abc123", "introduced by 1a2b3c",
     "This came from my own earlier recommendation."],
)
def test_fix_induced_phrases_are_flagged(tmp_path, text):
    s = _stage(rv.ledger_metrics(rv.read_ledger(_ledger(tmp_path, [_row("t-F1", "pr-review-local", evidence=text)]))),
               "pr-review-local")
    assert s["fix_induced"] == 1


def test_fix_induced_reads_the_note_too_and_ignores_plain_fix_words(tmp_path):
    rows = [_row("t-F1", "pr-review-local", evidence="please fix the parser", note="nothing"),
            _row("t-F2", "pr-review-local", evidence="guard misses a case", note="introduced by F1's patch")]
    assert _stage(rv.ledger_metrics(rv.read_ledger(_ledger(tmp_path, rows))), "pr-review-local")["fix_induced"] == 1


def test_stages_keep_ledger_order(tmp_path):
    rows = [_row("a", "plan-review"), _row("b", "test-benchmark-pr"), _row("c", "adversarial-review")]
    result = rv.ledger_metrics(rv.read_ledger(_ledger(tmp_path, rows)))
    assert [s["stage"] for s in result["stages"]] == ["plan-review", "test-benchmark-pr", "adversarial-review"]


def test_malformed_and_blank_lines_are_counted_not_fatal(tmp_path):
    path = tmp_path / "findings.jsonl"
    path.write_text(json.dumps(_row("a", "plan-review")) + "\n\nnot json\n" + json.dumps({"id": "b"}) + "\n")
    rows, skipped = rv.read_ledger(path, with_skipped=True)
    assert [r["id"] for r in rows] == ["a"]
    assert skipped == 2


# --- Tokens -------------------------------------------------------------------------------


def test_cost_per_confirmed_defect_divides_stage_tokens_by_confirmed(tmp_path):
    rows = [_row("a", "pr-review-local", status="verified"), _row("b", "pr-review-local", status="verified"),
            _row("c", "plan-review", status="rejected")]
    csv = tmp_path / "tokens.csv"
    csv.write_text("stage,round,tokens\npr-review-local,1,3000\npr-review-local,2,1000\nplan-review,,500\n")
    result = rv.ledger_metrics(rv.read_ledger(_ledger(tmp_path, rows)), rv.read_tokens(csv))
    pr = _stage(result, "pr-review-local")
    assert (pr["tokens"], pr["tokens_per_confirmed_defect"]) == (4000, 2000.0)
    plan = _stage(result, "plan-review")
    assert (plan["tokens"], plan["tokens_per_confirmed_defect"]) == (500, None)


def test_without_tokens_the_cost_columns_are_absent(tmp_path):
    s = _stage(rv.ledger_metrics(rv.read_ledger(_ledger(tmp_path, [_row("a", "plan-review")]))), "plan-review")
    assert "tokens" not in s and "tokens_per_confirmed_defect" not in s


def test_tokens_csv_rejects_a_missing_column(tmp_path):
    csv = tmp_path / "tokens.csv"
    csv.write_text("stage,tokens\nplan-review,5\n")
    with pytest.raises(ValueError, match="round"):
        rv.read_tokens(csv)


# --- PR review reports --------------------------------------------------------------------

REVIEW = """RUN_BY_COMMAND: pr-review-local

# PR #7 review: something

## 4. Architectural risks

### Required

1. **[V] Required, guardrail-level: the gate passes with no checks.**
   - What: details.

2. **[V] Required, patch-level: the claim is stronger than the evidence.**

### Nit

3. **[V] Nit: a broken link.**

**O1 [L] Optional — jscpd penalizes configuration.** `guardrail-level`

## 9. Specific inline comments to paste into GitHub

1. **[V] Required: the gate passes with no checks.** (duplicate of #1, not a new finding)

## 10. Dropped findings

1. **[V] Required: dropped during verification.**

Verdict: **REQUEST CHANGES.** Two Required items.

---

## Update [2026-10-14 21:49]: Changes Since Last Review

#### Previous issues: Status update

**#1 [Required] Zero checks pass the gate**: ✅ Resolved, with a test.
**#2 [Required] The claim is too strong**: ❌ Not addressed.
**#3 [Nit] Broken link**: ✅ Resolved.

#### New issues found

**N1. [V] Should-fix, guardrail-level: a server outlives the run.**
- What: the fix for #1 no longer waits for setup children.

**N2. [V] Must-fix: a new crash in the parser.**

#### Dropped findings

<details>
1. "something dropped"
</details>

### Recommendations for next iteration

1. **Must fix before merge:** N2.

**Verdict: REQUEST CHANGES.** N2 is open.

---

## Update [2026-10-14 22:10]: Changes Since Last Review

#### Previous issues: Status update

**Original Required #2: the claim is too strong**
- ✅ **Resolved** in `abc1234`.

**N1 [Should-fix] Server outlives the run**: ✅ Resolved.

**N2: crash in the parser**
- ✅ **Resolved.** A test covers it.

#### New issues found
None.

### Verdict

**APPROVE.** All items are resolved.
"""


def _rounds(tmp_path, text=REVIEW, name="PR_REVIEW_#7.md"):
    d = tmp_path / "reviews"
    d.mkdir(exist_ok=True)
    (d / name).write_text(text)
    return rv.review_metrics(rv.read_reviews(d))["rounds"]


def test_each_update_section_is_one_round(tmp_path):
    rounds = _rounds(tmp_path)
    assert [(r["pr"], r["round"]) for r in rounds] == [(7, 0), (7, 1), (7, 2)]


def test_round_counts_skip_inline_comment_dropped_and_recommendation_sections(tmp_path):
    r0, r1, r2 = _rounds(tmp_path)
    assert (r0["raised"], r0["blocking"], r0["should_fix"]) == (4, 2, 1)
    assert (r1["raised"], r1["blocking"], r1["should_fix"]) == (2, 1, 1)
    assert (r2["raised"], r2["blocking"]) == (0, 0)


def test_verdict_is_read_per_round(tmp_path):
    assert [r["verdict"] for r in _rounds(tmp_path)] == ["REQUEST CHANGES", "REQUEST CHANGES", "APPROVE"]


@pytest.mark.parametrize(
    ("line", "verdict"),
    [("Verdict: APPROVE WITH CONDITIONS. Fix N1.", "APPROVE WITH CONDITIONS"),
     ("**Verdict: APPROVE WITH NITS (no Required open).**", "APPROVE WITH NITS"),
     ("Verdict: **Approve.** No Critical items.", "APPROVE"),
     ("**Verdict:** ready to merge from the review side.", "APPROVE"),
     ("## Verdict at 94243de\n\n**Merge-ready. 0 Critical, 0 Required.**", "APPROVE"),
     ("Verdict: **APPROVE WITH ONE SHOULD-FIX.** Every item.", "APPROVE WITH CONDITIONS"),
     ("## Verdict\n\n**Still needed. Not mergeable as is.**", "OTHER"),
     ("No verdict line here.", None)],
)
def test_verdict_forms_are_normalized(line, verdict):
    assert rv.parse_verdict(line) == verdict


def test_confirmed_defects_are_attributed_to_the_round_that_raised_them(tmp_path):
    r0, r1, r2 = _rounds(tmp_path)
    # #1 resolved in round 1, #2 in round 2: both raised in round 0. #3 is a nit, not a defect.
    assert r0["confirmed_defects"] == 2
    # N2 is blocking and resolved in round 2; N1 is should-fix.
    assert r1["confirmed_defects"] == 1
    assert r2["confirmed_defects"] == 0


def test_resolutions_are_counted_on_the_round_that_confirms_them(tmp_path):
    r0, r1, r2 = _rounds(tmp_path)
    assert (r0["resolved_confirmed"], r1["resolved_confirmed"], r2["resolved_confirmed"]) == (0, 2, 3)


def test_round_kind_says_whether_it_raised_new_findings(tmp_path):
    assert [r["kind"] for r in _rounds(tmp_path)] == ["new", "new", "confirm-only"]


def test_fix_induced_reads_the_finding_body(tmp_path):
    r0, r1, _ = _rounds(tmp_path)
    assert (r0["fix_induced"], r1["fix_induced"]) == (0, 1)


def test_a_finding_raised_again_in_a_later_round_is_a_repeat(tmp_path):
    text = REVIEW.replace("**N2. [V] Must-fix: a new crash in the parser.**",
                          "**N2. [V] Must-fix: the gate passes with no checks.**")
    _, r1, _ = _rounds(tmp_path, text)
    assert (r1["raised"], r1["new"], r1["repeat"]) == (2, 1, 1)


@pytest.mark.parametrize(
    "line",
    ["**R1 [V] Required — late is undefined.** `patch-level`",
     "**F1 — [V] Required — architecture-level: CI loses the gate.**",
     "**NEW-1 [V] Required, patch-level: contaminated is not always the agent.**",
     "### 4.1 [V] Required, guardrail-level: a stream appends a static table",
     "**R1 — [V] Required — guardrail-level.** `results/install.json` is stale.",
     "1. [V] Required, guardrail-level — T05 hidden tests check a value"],
)
def test_finding_line_forms_are_recognized_as_blocking(line):
    assert rv.parse_finding_line(line)["severity"] == "blocking"


@pytest.mark.parametrize(
    "line",
    ["### Required", "1. **Must fix before merge:** none.", "- What: Required by the spec.",
     '1. **"The totals may not match"** -- Dropped.'],
)
def test_non_finding_lines_are_ignored(line):
    assert rv.parse_finding_line(line) is None


def test_only_canonical_report_names_are_read(tmp_path):
    d = tmp_path / "reviews"
    d.mkdir()
    (d / "PR_REVIEW_#7.md").write_text(REVIEW)
    (d / "PR_REVIEW_#7.ceb1500.md").write_text(REVIEW)
    (d / "notes.md").write_text(REVIEW)
    assert [r["pr"] for r in rv.read_reviews(d)] == [7]


def test_review_tokens_key_on_pr_and_round(tmp_path):
    d = tmp_path / "reviews"
    d.mkdir()
    (d / "PR_REVIEW_#7.md").write_text(REVIEW)
    csv = tmp_path / "tokens.csv"
    csv.write_text("stage,round,tokens\nPR#7,0,8000\nPR#7,1,900\n")
    r0, r1, r2 = rv.review_metrics(rv.read_reviews(d), rv.read_tokens(csv))["rounds"]
    assert (r0["tokens"], r0["tokens_per_confirmed_defect"]) == (8000, 4000.0)
    assert (r1["tokens"], r1["tokens_per_confirmed_defect"]) == (900, 900.0)
    assert (r2["tokens"], r2["tokens_per_confirmed_defect"]) == (0, None)


# --- Report and CLI -----------------------------------------------------------------------


def test_markdown_has_one_row_per_stage_and_round(tmp_path):
    ledger = rv.ledger_metrics(rv.read_ledger(_ledger(tmp_path, [_row("a", "plan-review")])))
    d = tmp_path / "reviews"
    d.mkdir()
    (d / "PR_REVIEW_#7.md").write_text(REVIEW)
    md = rv.render_markdown({"ledger": ledger, "reviews": rv.review_metrics(rv.read_reviews(d))})
    assert "| plan-review |" in md
    assert md.count("| #7 |") == 3


def test_cli_writes_json_and_markdown_and_never_echoes_finding_text(tmp_path, capsys):
    secret = "UNIQUE-EVIDENCE-TEXT"
    path = _ledger(tmp_path, [_row("a", "plan-review", evidence=secret)])
    d = tmp_path / "reviews"
    d.mkdir()
    (d / "PR_REVIEW_#7.md").write_text(REVIEW.replace("a broken link", secret))
    out_json = tmp_path / "out.json"
    assert rv.main(["--findings", str(path), "--reviews", str(d), "--json", str(out_json)]) == 0
    printed = capsys.readouterr().out
    data = json.loads(out_json.read_text())
    assert set(data) == {"ledger", "reviews"}
    assert "| plan-review |" in printed
    assert secret not in printed and secret not in out_json.read_text()


def test_cli_needs_at_least_one_input(capsys):
    with pytest.raises(SystemExit):
        rv.main([])


def test_single_letter_ids_open_a_finding():
    assert rv.parse_finding_line("**A. [V] Required, patch-level: the arm's outputs are not allowed.**")["label"] == "A"


def test_status_items_may_be_bullets_and_single_letter_ids(tmp_path):
    text = """# PR #3 review

## 4. Architectural risks

**R1 [V] Required: one.**

**A. [V] Required: two.**

## Update [2026-10-14 10:00]: Changes Since Last Review

#### Previous issues: Status update

- **R1 direction of differences**: ✅ Resolved.
- **A** ✅ Resolved (W1, W2).
"""
    r0, r1 = _rounds(tmp_path, text, "PR_REVIEW_#3.md")
    assert (r0["confirmed_defects"], r1["resolved_confirmed"]) == (2, 2)


def test_a_status_remark_without_an_evidence_tag_is_not_a_finding():
    assert rv.parse_finding_line('- R1 Required "Delivered 3 of 3" is **fixed** in README L21.') is None


def test_section_qualified_references_resolve_to_the_numbered_item_of_that_section(tmp_path):
    text = """# PR #3 review

## 4. Architectural risks

1. [V] Required, guardrail-level — the hidden tests check an unstated behavior.

## 7. Testing and validation gaps

1. [V] Nit — a missing negative test.

## Update [2026-10-14 10:00]: Changes Since Last Review

#### Previous issues: Status update

**§7.1: missing negative test**
- ✅ **Resolved.**

**§4.1 / §9: unstated behavior**
- ✅ **Resolved** in `abc1234`.
"""
    r0, r1 = _rounds(tmp_path, text, "PR_REVIEW_#3.md")
    assert (r0["raised"], r0["blocking"], r0["confirmed_defects"], r1["resolved_confirmed"]) == (2, 1, 1, 2)
