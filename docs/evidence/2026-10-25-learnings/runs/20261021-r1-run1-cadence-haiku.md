RUN_BY_COMMAND: run-learnings
Run: 20261021-r1-run1-cadence-haiku
Cadence: unrecorded
Packet sha256: a542870a569782323dddea171db4013d148a3366df883a70dd4d5882ec6d8afb

# Learnings: 20261021-r1-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 20
- gate: 54
- hard-stop: 1
- stop-refusal: 7

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-7, E-14, E-15, E-16, E-22, E-24, E-25, E-28, E-31, E-32, E-34, E-42, E-44, E-47, E-48, E-50, E-51, E-56, E-57, E-59, E-62, E-69, E-72, E-74, E-79, E-81
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 26 times in orchestrator: fail plan-review-round the plan has no; fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-17, E-18, E-19, E-40
- Rule: gate-repeat
- Key: gate-repeat|plan-review|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 4 times in P3: fail plan-review-round no open round names plan-review; fail plan-review-round the run has no plan; fail plan-review-round round # waits on plan-review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@unrecorded --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-26, E-27, E-33, E-52, E-53, E-54, E-60, E-61
- Rule: gate-repeat
- Key: gate-repeat|plan-update|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 8 times in P4: fail plan-review-round the plan has no; fail plan-review-round round # waits on plan-review; fail plan-review-round the run has no plan.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@unrecorded --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-8, E-35, E-64, E-75
- Rule: redispatch
- Key: redispatch|plan-review|P3
- Change: P3 was dispatched 4 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@unrecorded --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-9, E-36, E-65, E-76
- Rule: redispatch
- Key: redispatch|de-adversarial-reviewer|P6
- Change: P6 was dispatched 4 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@unrecorded --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-10, E-37, E-66
- Rule: redispatch
- Key: redispatch|test-benchmark|P7
- Change: P7 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@unrecorded --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-23, E-30, E-46, E-49, E-58, E-73, E-80
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 7 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@unrecorded --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-82
- Rule: hard-stop
- Key: hard-stop|de-adversarial-reviewer|P6|retries
- Change: P6 recorded a `retries` hard stop: p# adversarial plan review is past its cycle limit three cycles in. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@unrecorded --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-21, E-29, E-38, E-45, E-55, E-63, E-71
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 7 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-7 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-8 | dispatch | P3 | /plan-review dispatched as P3 |
| E-9 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-10 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-14 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review |
| E-15 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review |
| E-16 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review |
| E-17 | gate | P3 | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-18 | gate | P3 | FAIL plan-review-round: the run has no plan. Run P1 (/plan-create) first |
| E-19 | gate | P3 | FAIL plan-review-round: round 1 waits on plan-review |
| E-21 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-22 | gate | orchestrator | FAIL plan-review-round: round 1 has 14 must-fix rows |
| E-23 | dispatch | P4 | /plan-update dispatched as P4 |
| E-24 | gate | orchestrator | FAIL plan-review-round: the run has no plan. Run P1 (/plan-create) first |
| E-25 | gate | orchestrator | FAIL plan-review-round: the run has no plan. Run P1 (/plan-create) first |
| E-26 | gate | P4 | FAIL plan-review-round: the run has no plan. Run P1 (/plan-create) first |
| E-27 | gate | P4 | FAIL plan-review-round: the plan has no `## Revision ledger (review )` row for B-1, B-2, C-1, C-2, C-3, C-4, MF-1, MF-2, MF-3, MF-4, TB-F01, TB-F02, TB-F03, TB-F04 of round-1.md. Send /plan-update again |
| E-28 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review )` row for B-1, B-2, C-1, C-2, C-3, C-4, MF-1, MF-2, MF-3, MF-4, TB-F01, TB-F02, TB-F03, TB-F04 of round-1.md. Send /plan-update again |
| E-29 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 3 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-30 | dispatch | P4 | /plan-update dispatched as P4 |
| E-31 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review )` row for B-1, B-2, C-1, C-2, C-3, C-4, MF-1, MF-2, MF-3, MF-4, TB-F01, TB-F02, TB-F03, TB-F04 of round-1.md. Send /plan-update again |
| E-32 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review )` row for B-1, B-2, C-1, C-2, C-3, C-4, MF-1, MF-2, MF-3, MF-4, TB-F01, TB-F02, TB-F03, TB-F04 of round-1.md. Send /plan-update again |
| E-33 | gate | P4 | FAIL plan-review-round: round 2 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-34 | gate | orchestrator | FAIL plan-review-round: round 2 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-35 | dispatch | P3 | /plan-review dispatched as P3 |
| E-36 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-37 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-38 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 426 characters; the limit is 300. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-40 | gate | P3 | FAIL plan-review-round: round 2 waits on adversarial-review, test-benchmark-plan |
| E-42 | gate | orchestrator | FAIL plan-review-round: round 2 waits on test-benchmark-plan |
| E-44 | gate | orchestrator | FAIL plan-review-round: round 2 has 5 must-fix rows |
| E-45 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-46 | dispatch | P4 | /plan-update dispatched as P4 |
| E-47 | gate | orchestrator | FAIL plan-review-round: /plan-update changed Phase 1, Phase 2, which no finding of round 2 names. Send /plan-update again: undo that change, and change only Phase 3, Phase 4, global |
| E-48 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review )` row for B-1, B-2, C-1, C-2, TB-F07 of round-2.md. Send /plan-update again |
| E-49 | dispatch | P4 | /plan-update dispatched as P4 |
| E-50 | gate | orchestrator | FAIL plan-review-round: /plan-update changed Phase 1, Phase 2, which no finding of round 2 names. Send /plan-update again: undo that change, and change only Phase 3, Phase 4, global |
| E-51 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review )` row for B-1, B-2, C-1, C-2, TB-F07 of round-2.md. Send /plan-update again |
| E-52 | gate | P4 | FAIL plan-review-round: /plan-update changed Phase 1, Phase 2, which no finding of round 2 names. Send /plan-update again: undo that change, and change only Phase 3, Phase 4, global |
| E-53 | gate | P4 | FAIL plan-review-round: the plan has no `## Revision ledger (review )` row for B-1, B-2, C-1, C-2, TB-F07 of round-2.md. Send /plan-update again |
| E-54 | gate | P4 | FAIL plan-review-round: the plan has no `## Revision ledger (review )` row for B-1, B-2, C-1, C-2, TB-F07 of round-2.md. Send /plan-update again |
| E-55 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 332 characters; the limit is 300. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-56 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review )` row for B-1, B-2, C-1, C-2, TB-F07 of round-2.md. Send /plan-update again |
| E-57 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review )` row for B-1, B-2, C-1, C-2, TB-F07 of round-2.md. Send /plan-update again |
| E-58 | dispatch | P4 | /plan-update dispatched as P4 |
| E-59 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review )` row for B-1, B-2, C-1, C-2, TB-F07 of round-2.md. Send /plan-update again |
| E-60 | gate | P4 | FAIL plan-review-round: the plan has no `## Revision ledger (review )` row for B-1, B-2, C-1, C-2, TB-F07 of round-2.md. Send /plan-update again |
| E-61 | gate | P4 | FAIL plan-review-round: round 3 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-62 | gate | orchestrator | FAIL plan-review-round: round 3 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-63 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 383 characters; the limit is 300. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-64 | dispatch | P3 | /plan-review dispatched as P3 |
| E-65 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-66 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-69 | gate | orchestrator | FAIL plan-review-round: round 3 waits on test-benchmark-plan |
| E-71 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-72 | gate | orchestrator | FAIL plan-review-round: round 3 has 4 must-fix rows |
| E-73 | dispatch | P4 | /plan-update dispatched as P4 |
| E-74 | gate | orchestrator | FAIL plan-review-round: round 4 waits on plan-review, adversarial-review |
| E-75 | dispatch | P3 | /plan-review dispatched as P3 |
| E-76 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-79 | gate | orchestrator | FAIL plan-review-round: round 4 has 4 must-fix rows |
| E-80 | dispatch | P4 | /plan-update dispatched as P4 |
| E-81 | gate | orchestrator | FAIL plan-review-round: round 5 waits on adversarial-review |
| E-82 | hard-stop | orchestrator | P6 adversarial plan review is past its cycle limit (three cycles in references/error-recovery.md). Round 5 of plan_wave.py still asks for a P6 review while the round-4 must-fix rows are open. P3 is READY TO EXECUTE on round 4. |
