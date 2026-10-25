RUN_BY_COMMAND: run-learnings
Run: 20261022-y3-run1-cadence-haiku
Cadence: 70ae163507b73634e129ce470b0a945f4b095dd2
Packet sha256: 372f5157768d0c3fa7bf5742ab644e1bf003957a15ad40639abea25ae270f359

# Learnings: 20261022-y3-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 9
- gate: 26
- hard-stop: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-9, E-16
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-22, E-25, E-31, E-35
- Rule: gate-repeat
- Key: gate-repeat|cadence|entry-invariant
- Change: Before the return, run the `entry-invariant` gate once and fix every class it names in one pass. In this run it failed 4 times in orchestrator: adversarial-review cycle limit reached # cycles; plan-review the plan changed after its review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-27, E-29, E-33
- Rule: gate-repeat
- Key: gate-repeat|cadence|adversarial-review-gate
- Change: Before the return, run the `adversarial-review-gate` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: adversarial-review cycle limit reached # cycles.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-17, E-23, E-28, E-32
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 4 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: SKILL.md
- Status: candidate
- Evidence: E-36
- Rule: hard-stop
- Key: hard-stop|cadence|P9|retries
- Change: P9 recorded a `retries` hard stop: p# fails adversarial-review carry at p# cycle limit is not written. three. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-9 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-16 | gate | orchestrator | FAIL plan-review-round: round 1 has 10 must-fix rows |
| E-17 | dispatch | P4 | /plan-update dispatched as P4 |
| E-22 | gate | orchestrator | FAIL entry-invariant |
| E-23 | dispatch | P4 | /plan-update dispatched as P4 |
| E-25 | gate | orchestrator | FAIL entry-invariant |
| E-27 | gate | orchestrator | FAIL adversarial-review-gate |
| E-28 | dispatch | P4 | /plan-update dispatched as P4 |
| E-29 | gate | orchestrator | FAIL adversarial-review-gate |
| E-31 | gate | orchestrator | FAIL entry-invariant |
| E-32 | dispatch | P4 | /plan-update dispatched as P4 |
| E-33 | gate | orchestrator | FAIL adversarial-review-gate |
| E-35 | gate | orchestrator | FAIL entry-invariant |
| E-36 | hard-stop | orchestrator | P9 fails: adversarial-review carry at P6 cycle limit is not written. Three /plan-update peer calls reported success, but the heading ## Carried adversarial findings is still missing. P9 entry-invariant stays FAIL. |
