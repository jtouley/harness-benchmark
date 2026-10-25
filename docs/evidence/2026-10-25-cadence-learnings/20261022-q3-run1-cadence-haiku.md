RUN_BY_COMMAND: run-learnings
Run: 20261022-q3-run1-cadence-haiku
Cadence: fb0270d010cbfb284df5af992e1db36ed45cbeda
Packet sha256: ae448b415b7fe5e59bf0405d50d9773f26545ce4e6d187adb418f919b5a85912

# Learnings: 20261022-q3-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: no
- transcript: yes

## Evidence counts

- finding: 5
- gate: 47
- stop-point: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-4, E-9, E-10
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix; fail plan-review-round the plan has no.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-18, E-19
- Rule: gate-repeat
- Key: gate-repeat|cadence|deferral-register
- Change: Before the return, run the `deferral-register` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: deferral-register deferral-review no ruling of the.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-40, E-41
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-43, E-44, E-45
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor:R2
- Change: E1 checks `review-rigor:R2` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-4 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-9 | gate | orchestrator | FAIL plan-review-round: round 1 has 12 must-fix rows |
| E-10 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review 380f2e33944e)` row for feat-local-4-csv-export-P7-F01, feat-local-4-csv-export-P7-F02 of round-1.md. Send /plan-update again |
| E-18 | gate | orchestrator | FAIL deferral-register |
| E-19 | gate | orchestrator | FAIL deferral-register |
| E-40 | finding | pr-review-local | --out with a note holding a lone surrogate exits 1 with UnicodeEncodeError traceback; _write_out catches only OSError. See PR_REVIEW_1.md Reproductions. |
| E-41 | finding | pr-review-local | amount_cents -5 prints -1.95 (format_amount divmod on negative). See PR_REVIEW_1.md Reproductions. |
| E-43 | finding | test-benchmark | format_amount uses divmod on a negative cent count, so the remainder is positive. A ledger row with amount_cents -5 prints -1.95 and -150 prints -2.50; expected -0.05 and -1.50. Exit 0. Ledger.load does not check the sign, so a hand-edited ledger reaches this path. No test covers a negative amount. Fix: add -5 and -150 rows to a parametrize table over format_amount, then fix the sign handling. |
| E-44 | finding | test-benchmark | _write_out catches OSError only. A note with a lone surrogate makes Path.write_text(encoding=utf-8) raise UnicodeEncodeError: a traceback, exit 1, and a partial output file left on disk. The tests expect error: with exit 2 and no traceback for write failures. Without --out, stdout writes the same note as raw byte 0x80 with exit 0, which is not valid UTF-8. Fix: handle UnicodeError in both paths, … |
| E-45 | finding | test-benchmark | With a closed stdout pipe, budgetcli export piped to head -0 prints a BrokenPipeError traceback and exits 1. Closed output pipe is a required input class (review-rigor). The feature prints error: lines without a traceback elsewhere. Fix: catch BrokenPipeError around the stdout write and add a test that asserts no Traceback in stderr. |
