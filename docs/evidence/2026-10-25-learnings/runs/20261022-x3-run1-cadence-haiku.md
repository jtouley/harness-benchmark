RUN_BY_COMMAND: run-learnings
Run: 20261022-x3-run1-cadence-haiku
Cadence: 9c2505a78ef6f6d74e057975cc9f3919db2e4dc5
Packet sha256: d1c4983e5e7fdbc55e43240c0dcc33f8bfb1dabb0f9cddaff392d973f4435291

# Learnings: 20261022-x3-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- gate: 18
- hard-stop: 1
- stop-refusal: 2

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-6, E-11, E-12, E-13, E-14, E-16, E-18
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 7 times in orchestrator: fail plan-review-round the plan has no; fail plan-review-round round # has # must-fix; fail plan-review-round round # waits on plan-review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-15, E-19
- Rule: gate-repeat
- Key: gate-repeat|plan-update|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in plan-update: fail plan-review-round the plan has no.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-21
- Rule: hard-stop
- Key: hard-stop|plan-update|P4|retries
- Change: P4 recorded a `retries` hard stop: p# plan-update failed the plan_wave round-# ledger gate four times. lines. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: SKILL.md
- Status: candidate
- Evidence: E-7
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked record each finding of your
- Change: The hooks refused 1 times with `blocked record each finding of your`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: SKILL.md
- Status: candidate
- Evidence: E-20
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 1 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-6 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-7 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-x/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-x/scripts/plan_wave.py" done --stage test-benchmar… |
| E-11 | gate | orchestrator | FAIL plan-review-round: round 1 has 14 must-fix rows |
| E-12 | gate | orchestrator | FAIL plan-review-round: /plan-update changed Phase 3, which no finding of round 1 names. Send /plan-update again: undo that change, and change only Phase 1, Phase 2, global. The change: - 3. Check that `git status` lists only the files named in the blast radius, plus `.context/`. \| + 3. Check that `git diff --quiet 26ba57c -- acceptance/check_export.py` passes. The acceptance script is not change… |
| E-13 | gate | orchestrator | FAIL plan-review-round: round 2 has 1 must-fix rows |
| E-14 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review ce1bd65a507d)` row for B-1, B-2, C-1, C-2, C-3, C-4, MF-1, MF-2, MF-3, W-1, W-2, W-3, feat-local-4-csv-export-P7-F01, feat-local-4-csv-export-P7-F02 of round-1.md. Send /plan-update again |
| E-15 | gate | plan-update | FAIL plan-review-round: the plan has no `## Revision ledger (review ce1bd65a507d)` row for B-1, B-2, C-1, C-2, C-3, C-4, MF-1, MF-2, MF-3, W-1, W-2, W-3, feat-local-4-csv-export-P7-F01, feat-local-4-csv-export-P7-F02 of round-1.md. Send /plan-update again |
| E-16 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review ce1bd65a507d)` row for B-1, B-2, C-1, C-2, C-3, C-4, MF-1, MF-2, MF-3, W-1, W-2, W-3, feat-local-4-csv-export-P7-F01, feat-local-4-csv-export-P7-F02 of round-1.md. Send /plan-update again |
| E-18 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review ce1bd65a507d)` row for B-1, B-2, C-1, C-2, C-3, C-4, MF-1, MF-2, MF-3, W-1, W-2, W-3, feat-local-4-csv-export-P7-F01, feat-local-4-csv-export-P7-F02 of round-1.md. Send /plan-update again |
| E-19 | gate | plan-update | FAIL plan-review-round: the plan has no `## Revision ledger (review ce1bd65a507d)` row for B-1, B-2, C-1, C-2, C-3, C-4, MF-1, MF-2, MF-3, W-1, W-2, W-3, feat-local-4-csv-export-P7-F01, feat-local-4-csv-export-P7-F02 of round-1.md. Send /plan-update again |
| E-20 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-21 | hard-stop | orchestrator | P4 plan-update failed the plan_wave round-2 ledger gate four times. plan_wave.py lines 307-308 pop round 2 when no reviewer started, then require the round-1 revision ledger ce1bd65a507d. The plan answers W-1, but the gate still fails. Needs a fix to plan_wave.py or a manual ledger row. |
