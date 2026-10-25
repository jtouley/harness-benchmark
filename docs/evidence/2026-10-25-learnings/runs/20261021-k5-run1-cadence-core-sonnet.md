RUN_BY_COMMAND: run-learnings
Run: 20261021-k5-run1-cadence-core-sonnet
Cadence: unrecorded
Packet sha256: 93465400e4c2c733288f7a0ae5075500636288a3610ba9b558228e27ff2ffd83

# Learnings: 20261021-k5-run1-cadence-core-sonnet

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 5
- fix-commit: 3
- gate: 23
- hard-stop: 1
- stop-refusal: 6

## Proposals

### L-1
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-18, E-36, E-37, E-38
- Rule: review-finding
- Key: review-finding|spec-driven|skills/test-benchmark/SKILL.md: DRY
- Change: E1 checks `skills/test-benchmark/SKILL.md: DRY` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-23, E-29, E-36, E-37, E-38
- Rule: review-finding
- Key: review-finding|spec-driven|skills/test-benchmark/SKILL.md: DRY (thin_files)
- Change: E1 checks `skills/test-benchmark/SKILL.md: DRY (thin_files)` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-25, E-36, E-37, E-38
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-30, E-36, E-37, E-38
- Rule: review-finding
- Key: review-finding|spec-driven|skills/test-benchmark/SKILL.md: mutation resilience
- Change: E1 checks `skills/test-benchmark/SKILL.md: mutation resilience` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: SKILL.md
- Status: candidate
- Evidence: E-35
- Rule: hard-stop
- Key: hard-stop|cadence|orchestrator|retries
- Change: orchestrator recorded a `retries` hard stop: review_fix_rounds # used r# test-benchmark still fail with open must-fix f# mutation. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-19, E-22, E-28, E-31, E-33
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 5 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: SKILL.md
- Status: candidate
- Evidence: E-34
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in review. continue
- Change: The hooks refused 1 times with `blocked early stop in review. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-18 | finding | test-benchmark | No conftest in the repo tests (helpers_reimplemented unmeasured, record verdict fail); GOOD item, bad-sidecar tables and tmp-path fixtures duplicated across the two files. DRY score 6, floor 7. |
| E-19 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 383 characters; the limit is 300. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-22 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 9 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-23 | finding | test-benchmark | test_shape.py --change: thin_files 1, limit 0, verdict fail. tests/test_shared_fixtures.py has 2 tests of src/budgetcli/ledger.py, also tested by tests/test_ledger.py. |
| E-25 | finding | pr-review-update | New file tests/test_shared_fixtures.py (fix commit 3982f72) duplicates existing coverage: test_conftest_badSidecar_isRejectedByStore repeats the 24-case assertion of test_load_rejectsBadShape in tests/test_recurring.py, and the good_item test is covered by every store.add test. test_shape.py --change reports thin_files value 1 vs threshold 0 (verdict fail), a regression from the fix; before the f… |
| E-28 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 9 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-29 | finding | test-benchmark | test_shape.py --change: thin_files 1, limit 0, verdict fail. tests/test_shared_fixtures.py has 2 tests of src/budgetcli/ledger.py, also tested by tests/test_ledger.py. |
| E-30 | finding | test-benchmark | mutation_resilience 4, floor 7: 8 of 13 hand-made mutants survive (id prefix remove, remove keeping id<item_id, next_id as max+1, day 28 never accepted, // 100 in list and totals, id 0 accepted in a sidecar). Fix with rows in existing parametrize tables. |
| E-31 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 529 characters; the limit is 300. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-33 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-34 | stop-refusal | orchestrator | BLOCKED early stop in review. Continue paceline: next R2 (test-benchmark-pr) via `/test-benchmark` |
| E-35 | hard-stop | orchestrator | review_fix_rounds (2) used; R2 test-benchmark still FAIL with open must-fix F06 (mutation resilience 4/7) and F01 (plan-stage DRY, likely addressed by conftest). Deferral needs a real ticket; none provided. |
| E-36 | fix-commit | E1 | fix: feat-local-3-recurring-expenses-3402dc32-MF-1 remove redundant shared-fixtures test file |
| E-37 | fix-commit | E1 | fix: feat-local-3-recurring-expenses-F03 shared conftest for fixtures and bad-sidecar table |
| E-38 | fix-commit | E1 | test: feat-local-3-recurring-expenses-F03 shared conftest fixtures (red) |
