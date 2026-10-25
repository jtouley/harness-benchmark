RUN_BY_COMMAND: run-learnings
Run: 20261022-u1-run1-cadence-haiku
Cadence: a3eb0aaf812e1f0be3e12aba48894ffc36983f5b
Packet sha256: 6dab32bed448dbac689502ede422d4d34809f5bbfe53ef6ae0132ded664b0a0b

# Learnings: 20261022-u1-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: no
- transcript: yes

## Evidence counts

- dispatch: 11
- gate: 35
- hard-stop: 1
- stop-point: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-11, E-23, E-25, E-26, E-28, E-30
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 6 times in orchestrator: fail plan-review-round cycle limit reached # cycles; fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-15, E-18, E-19, E-21
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 4 times in P7: fail plan-review-round round # waits on plan-review; fail plan-review-round no open round names test-benchmark-plan; fail plan-review-round the run has no plan.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-35, E-40, E-45
- Rule: gate-repeat
- Key: gate-repeat|cadence|deferral-register
- Change: Before the return, run the `deferral-register` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: deferral-register deferral-core-of-request approved deferral ## the item.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-24, E-27, E-29, E-32, E-36, E-43
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 6 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: SKILL.md
- Status: candidate
- Evidence: E-48
- Rule: hard-stop
- Key: hard-stop|cadence|P8|retries
- Change: P8 recorded a `retries` hard stop: p# deferral-register fails deferral-core-of-request approved deferral ## local-# upload has request trace. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-11 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-15 | gate | P7 | FAIL plan-review-round: no open round names test-benchmark-plan for this plan: run plan_wave.py first |
| E-18 | gate | P7 | FAIL plan-review-round: the run has no plan. Run P1 (/plan-create) first |
| E-19 | gate | P7 | FAIL plan-review-round: round 1 waits on plan-review, test-benchmark-plan |
| E-21 | gate | P7 | FAIL plan-review-round: round 1 waits on plan-review |
| E-23 | gate | orchestrator | FAIL plan-review-round: round 1 has 10 must-fix rows |
| E-24 | dispatch | P4 | /plan-update dispatched as P4 |
| E-25 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review 39804273299f)` row for feat-local-4-csv-export-F01, feat-local-4-csv-export-F02, feat-local-4-csv-export-F03, feat-local-4-csv-export-F04, feat-local-4-csv-export-F05 of round-1.md. Send /plan-update again |
| E-26 | gate | orchestrator | FAIL plan-review-round: cycle limit reached (1 cycles). Do not run P6 again. Run /plan-update. Add "## Carried adversarial findings (adversarial_feat-local-4-csv-export.md @ 86cd26d8367a)" and map B-1, C-1, C-2 to the phase whose test settles each. Send /plan-update again with the round file |
| E-27 | dispatch | P4 | /plan-update dispatched as P4 |
| E-28 | gate | orchestrator | FAIL plan-review-round: cycle limit reached (1 cycles). Do not run P6 again. Run /plan-update. Add "## Carried adversarial findings (adversarial_feat-local-4-csv-export.md @ 86cd26d8367a)" and map B-1, C-1, C-2 to the phase whose test settles each. Send /plan-update again with the round file |
| E-29 | dispatch | P4 | /plan-update dispatched as P4 |
| E-30 | gate | orchestrator | FAIL plan-review-round: cycle limit reached (1 cycles). Do not run P6 again. Run /plan-update. Add "## Carried adversarial findings (adversarial_feat-local-4-csv-export.md @ 86cd26d8367a)" and map B-1, C-1, C-2 to the phase whose test settles each. Send /plan-update again with the round file |
| E-32 | dispatch | P4 | /plan-update dispatched as P4 |
| E-35 | gate | orchestrator | FAIL deferral-register |
| E-36 | dispatch | P4 | /plan-update dispatched as P4 |
| E-40 | gate | orchestrator | FAIL deferral-register |
| E-43 | dispatch | P4 | /plan-update dispatched as P4 |
| E-45 | gate | orchestrator | FAIL deferral-register |
| E-48 | hard-stop | orchestrator | P8 deferral-register fails deferral-core-of-request: approved deferral #1 (LOCAL-9 upload) has Request trace text, not 'none'. Three /plan-update rounds did not change the cell. Resume at P8 after the register row is fixed to trace 'none' with the request's words as blocked-by evidence. |
