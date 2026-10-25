RUN_BY_COMMAND: run-learnings
Run: 20261021-d1-run1-cadence-haiku
Cadence: unrecorded
Packet sha256: b9d36271583bb619d59887c668eb863aed2f94235279326ab6ee43f5c728fd3c

# Learnings: 20261021-d1-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 25
- gate: 49
- stop-point: 1
- stop-refusal: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-10, E-11, E-13
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-gate
- Change: Before the return, run the `plan-review-gate` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: plan-review no artifact matching; plan-review no file matched markers run_by_command plan-review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-16, E-20
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-update-gate
- Change: Before the return, run the `plan-update-gate` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: plan-update verdict is ready with changes cycle.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-27, E-35, E-38
- Rule: gate-repeat
- Key: gate-repeat|cadence|adversarial-review-gate
- Change: Before the return, run the `adversarial-review-gate` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: adversarial-review cycle limit reached # cycles; adversarial-review verdict is request changes cycle.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-52, E-54
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 2 times in E1: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; fix step run r# without --check to.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-68
- Rule: late-gate
- Key: late-gate|spec-driven|pr-review-local-gate|pr-review-local no peer-written
- Change: E1's phase gate runs the `pr-review-local-gate` measure `pr-review-local no peer-written` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-9, E-14, E-18, E-23, E-29, E-32, E-47
- Rule: redispatch
- Key: redispatch|plan-review|P3
- Change: P3 was dispatched 7 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@unrecorded --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-17, E-21, E-28, E-31, E-34, E-41
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 6 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@unrecorded --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-26, E-30, E-33
- Rule: redispatch
- Key: redispatch|de-adversarial-reviewer|P6
- Change: P6 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@unrecorded --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-40, E-43
- Rule: redispatch
- Key: redispatch|test-benchmark|P7
- Change: P7 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@unrecorded --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: SKILL.md
- Status: candidate
- Evidence: E-12
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in planning. continue
- Change: The hooks refused 1 times with `blocked early stop in planning. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-9 | dispatch | P3 | /plan-review dispatched as P3 |
| E-10 | gate | orchestrator | FAIL plan-review-gate |
| E-11 | gate | orchestrator | FAIL plan-review-gate |
| E-12 | stop-refusal | orchestrator | BLOCKED early stop in planning. Continue paceline: next P3 (plan-review) via `/plan-review` |
| E-13 | gate | orchestrator | FAIL plan-review-gate |
| E-14 | dispatch | P3 | /plan-review dispatched as P3 |
| E-16 | gate | orchestrator | FAIL plan-update-gate |
| E-17 | dispatch | P4 | /plan-update dispatched as P4 |
| E-18 | dispatch | P3 | /plan-review dispatched as P3 |
| E-20 | gate | orchestrator | FAIL plan-update-gate |
| E-21 | dispatch | P4 | /plan-update dispatched as P4 |
| E-23 | dispatch | P3 | /plan-review dispatched as P3 |
| E-26 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-27 | gate | orchestrator | FAIL adversarial-review-gate |
| E-28 | dispatch | P4 | /plan-update dispatched as P4 |
| E-29 | dispatch | P3 | /plan-review dispatched as P3 |
| E-30 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-31 | dispatch | P4 | /plan-update dispatched as P4 |
| E-32 | dispatch | P3 | /plan-review dispatched as P3 |
| E-33 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-34 | dispatch | P4 | /plan-update dispatched as P4 |
| E-35 | gate | orchestrator | FAIL adversarial-review-gate |
| E-38 | gate | orchestrator | FAIL adversarial-review-gate |
| E-40 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-41 | dispatch | P4 | /plan-update dispatched as P4 |
| E-43 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-47 | dispatch | P3 | /plan-review dispatched as P3 |
| E-52 | gate | E1 | FAIL cognitive-complexity |
| E-54 | gate | E1 | FAIL cognitive-complexity |
| E-68 | gate | R1 | FAIL pr-review-local-gate |
