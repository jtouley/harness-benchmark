RUN_BY_COMMAND: run-learnings
Run: 20261022-q1-run1-cadence-haiku
Cadence: fb0270d010cbfb284df5af992e1db36ed45cbeda
Packet sha256: 49f2a3fb72f369f593a1d85d82c795f885cf57336861c380c8e7b28e0d9b341d

# Learnings: 20261022-q1-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: no
- transcript: yes

## Evidence counts

- finding: 4
- gate: 45
- stop-refusal: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-9, E-14
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-48, E-49
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 2 times in spec-driven: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; types union-attr item none of io bytes.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-40
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-43, E-44, E-45
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: SKILL.md
- Status: candidate
- Evidence: E-7
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 1 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-7 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 3 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-9 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-14 | gate | orchestrator | FAIL plan-review-round: round 1 has 11 must-fix rows |
| E-40 | finding | pr-review-local | --out equal to a missing ledger path writes CSV into the ledger; next add fails (Expecting value). See PR_REVIEW_1.md Reproductions MF-1. |
| E-43 | finding | pr-review-local | UnicodeEncodeError escapes except OSError; empty output file left behind, exit 1. Ledger note with lone surrogate. See PR_REVIEW_1.md MF-2. |
| E-44 | finding | pr-review-local | closed stdout pipe gives BrokenPipeError traceback, exit 1. See PR_REVIEW_1.md MF-3. |
| E-45 | finding | pr-review-local | bad stored row (missing amount_cents) gives KeyError traceback in export. See PR_REVIEW_1.md MF-4. |
| E-48 | gate | spec-driven | FAIL cognitive-complexity |
| E-49 | gate | spec-driven | FAIL cognitive-complexity |
