RUN_BY_COMMAND: run-learnings
Run: 20261021-c3-run1-cadence-sonnet
Cadence: unrecorded
Packet sha256: 7ad0760ce5773e801b056cfc6c34c080f1c3297138df4e009292ec045ee905ed

# Learnings: 20261021-c3-run1-cadence-sonnet

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 16
- finding: 1
- gate: 21
- stop-point: 1
- stop-refusal: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-3, E-4, E-5
- Rule: gate-repeat
- Key: gate-repeat|cadence|validate-gate
- Change: Before the return, run the `validate-gate` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: missing **tracker ** line; vibe-test orchestrator unknown activate through the bash.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-17, E-20, E-22
- Rule: gate-repeat
- Key: gate-repeat|cadence|entry-invariant
- Change: Before the return, run the `entry-invariant` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: plan-review the plan changed after its review; adversarial-review conditions not in the plan under.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-8, E-10, E-16, E-21
- Rule: redispatch
- Key: redispatch|plan-review|P3
- Change: P3 was dispatched 4 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@unrecorded --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-9, E-14, E-18
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@unrecorded --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-13
- Rule: review-finding
- Key: review-finding|spec-driven|test-benchmark:dry
- Change: E1 checks `test-benchmark:dry` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-35
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 1 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-3 | gate | orchestrator | FAIL validate-gate |
| E-4 | gate | orchestrator | FAIL validate-gate |
| E-5 | gate | orchestrator | FAIL validate-gate |
| E-8 | dispatch | P3 | /plan-review dispatched as P3 |
| E-9 | dispatch | P4 | /plan-update dispatched as P4 |
| E-10 | dispatch | P3 | /plan-review dispatched as P3 |
| E-13 | finding | P7 | No shared CLI test helper or parametrised tables planned for about 40 CLI cases; DRY score 6. |
| E-14 | dispatch | P4 | /plan-update dispatched as P4 |
| E-16 | dispatch | P3 | /plan-review dispatched as P3 |
| E-17 | gate | orchestrator | FAIL entry-invariant |
| E-18 | dispatch | P4 | /plan-update dispatched as P4 |
| E-20 | gate | orchestrator | FAIL entry-invariant |
| E-21 | dispatch | P3 | /plan-review dispatched as P3 |
| E-22 | gate | orchestrator | FAIL entry-invariant |
| E-35 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 3 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
