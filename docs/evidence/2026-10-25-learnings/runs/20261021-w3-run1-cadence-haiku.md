RUN_BY_COMMAND: run-learnings
Run: 20261021-w3-run1-cadence-haiku
Cadence: dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451
Packet sha256: b1f507dc784afbe4a06c82db2552e0bfca4a246e1b486c495f707d0eb382e332

# Learnings: 20261021-w3-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 10
- gate: 34
- stop-refusal: 4

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-8, E-21, E-23
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix; fail plan-review-round changed phase # which no.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-12, E-13, E-14, E-16
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 4 times in P7: fail plan-review-round phase none is not a; fail plan-review-round a finding needs an id.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-22, E-24, E-32
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-37, E-45
- Rule: redispatch
- Key: redispatch|spec-driven|E1
- Change: E1 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: SKILL.md
- Status: candidate
- Evidence: E-43
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked continue e# phase # csv
- Change: The hooks refused 1 times with `blocked continue e# phase # csv`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-44, E-47, E-48
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in execution. continue
- Change: The hooks refused 3 times with `blocked early stop in execution. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-8 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-12 | gate | P7 | FAIL plan-review-round: phase None is not a section of the plan: use one of Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, global |
| E-13 | gate | P7 | FAIL plan-review-round: phase None is not a section of the plan: use one of Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, global |
| E-14 | gate | P7 | FAIL plan-review-round: phase None is not a section of the plan: use one of Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, global |
| E-16 | gate | P7 | FAIL plan-review-round: a finding needs an id such as MF-1 and a severity of must-fix or nit |
| E-21 | gate | orchestrator | FAIL plan-review-round: round 1 has 12 must-fix rows |
| E-22 | dispatch | P4 | /plan-update dispatched as P4 |
| E-23 | gate | orchestrator | FAIL plan-review-round: /plan-update changed Phase 5, which no finding of round 1 names. Send /plan-update again: undo that change, and change only Phase 1, Phase 2, Phase 3, Phase 4, global. The change: + Phase 5 has no code of its own, so it has no commit. It runs after the green commit of Phase 4. |
| E-24 | dispatch | P4 | /plan-update dispatched as P4 |
| E-32 | dispatch | P4 | /plan-update dispatched as P4 |
| E-37 | dispatch | E1 | /spec-driven dispatched as E1 |
| E-43 | stop-refusal | orchestrator | BLOCKED: Continue E1: phase 3 (CSV text). Commit it as 'phase 3: <subject>' before the next phase. |
| E-44 | stop-refusal | orchestrator | BLOCKED early stop in execution. Continue E1: send the `/spec-driven` peer the plan again. Its next open phase is phase 3 (CSV text). |
| E-45 | dispatch | E1 | /spec-driven dispatched as E1 |
| E-47 | stop-refusal | orchestrator | BLOCKED early stop in execution. Continue E1: send the `/spec-driven` peer the plan again. Its next open phase is phase 3 (CSV text). |
| E-48 | stop-refusal | orchestrator | BLOCKED early stop in execution. Continue E1: send the `/spec-driven` peer the plan again. Its next open phase is phase 3 (CSV text). |
