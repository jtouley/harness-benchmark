RUN_BY_COMMAND: run-learnings
Run: 20261021-d3-run1-cadence-haiku
Cadence: unrecorded
Packet sha256: 4ccfc6ea164c50637b240cae2fd97780079bc90f1bc40fb03533b9a52a9ce7e0

# Learnings: 20261021-d3-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 19
- gate: 7

## Proposals

### L-1
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-6, E-9, E-11, E-14, E-17, E-26
- Rule: redispatch
- Key: redispatch|plan-review|P3
- Change: P3 was dispatched 6 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@unrecorded --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-7, E-10, E-13, E-16, E-19, E-21, E-22
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 7 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@unrecorded --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-12, E-15, E-18
- Rule: redispatch
- Key: redispatch|de-adversarial-reviewer|P6
- Change: P6 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@unrecorded --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-6 | dispatch | P3 | /plan-review dispatched as P3 |
| E-7 | dispatch | P4 | /plan-update dispatched as P4 |
| E-9 | dispatch | P3 | /plan-review dispatched as P3 |
| E-10 | dispatch | P4 | /plan-update dispatched as P4 |
| E-11 | dispatch | P3 | /plan-review dispatched as P3 |
| E-12 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-13 | dispatch | P4 | /plan-update dispatched as P4 |
| E-14 | dispatch | P3 | /plan-review dispatched as P3 |
| E-15 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-16 | dispatch | P4 | /plan-update dispatched as P4 |
| E-17 | dispatch | P3 | /plan-review dispatched as P3 |
| E-18 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-19 | dispatch | P4 | /plan-update dispatched as P4 |
| E-21 | dispatch | P4 | /plan-update dispatched as P4 |
| E-22 | dispatch | P4 | /plan-update dispatched as P4 |
| E-26 | dispatch | P3 | /plan-review dispatched as P3 |
