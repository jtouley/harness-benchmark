RUN_BY_COMMAND: run-learnings
Run: 20261021-k6-run1-cadence-core-sonnet
Cadence: unrecorded
Packet sha256: 8640c5dc9ff41e22b3b583ac0caf04b223d3cfefa856ca826d48b39e08e2868c

# Learnings: 20261021-k6-run1-cadence-core-sonnet

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: no
- transcript: yes

## Evidence counts

- dispatch: 15
- gate: 6
- hard-stop: 1
- stop-point: 1

## Proposals

### L-1
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-6, E-8, E-11, E-16
- Rule: redispatch
- Key: redispatch|plan-review|P3
- Change: P3 was dispatched 4 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@unrecorded --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-7, E-10, E-14
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@unrecorded --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-9, E-12
- Rule: redispatch
- Key: redispatch|de-adversarial-reviewer|P6
- Change: P6 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@unrecorded --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-13, E-15
- Rule: redispatch
- Key: redispatch|test-benchmark|P7
- Change: P7 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@unrecorded --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/commit-push-pr.md
- Status: candidate
- Evidence: E-23
- Rule: hard-stop
- Key: hard-stop|commit-push-pr|E4|destructive
- Change: E4 recorded a `destructive` hard stop: e# push rejected already holds # different commits of local-# #..# overwriting. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=commit-push-pr@unrecorded --config new_skill=commit-push-pr@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-6 | dispatch | P3 | /plan-review dispatched as P3 |
| E-7 | dispatch | P4 | /plan-update dispatched as P4 |
| E-8 | dispatch | P3 | /plan-review dispatched as P3 |
| E-9 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-10 | dispatch | P4 | /plan-update dispatched as P4 |
| E-11 | dispatch | P3 | /plan-review dispatched as P3 |
| E-12 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-13 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-14 | dispatch | P4 | /plan-update dispatched as P4 |
| E-15 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-16 | dispatch | P3 | /plan-review dispatched as P3 |
| E-23 | hard-stop | orchestrator | E4 push rejected: origin/feat/LOCAL-3-recurring-expenses already holds 5 different commits of LOCAL-3 (cbeb151..ca6b80b); overwriting needs force-push, owner must choose |
