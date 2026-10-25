RUN_BY_COMMAND: run-learnings
Run: 20261021-k6-run2-cadence-core-sonnet
Cadence: unrecorded
Packet sha256: feac61512557626a41441c5b81ffccbd80320d9bb801045da74e3f7a3c87cfd6

# Learnings: 20261021-k6-run2-cadence-core-sonnet

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 8
- finding: 1
- fix-commit: 4
- gate: 18
- stop-point: 1

## Proposals

### L-1
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-10, E-11
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|test-benchmark-gate-code
- Change: Before the return, run the `test-benchmark-gate-code` gate once and fix every class it names in one pass. In this run it failed 2 times in R2: test-benchmark-code must-fix dimensions below # dry_no_clone_setups.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@unrecorded --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-21, E-23, E-25
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: feat-local-#-recurring-expenses-f# must-fix status fixed not terminal.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-10, E-11
- Rule: late-gate
- Key: late-gate|spec-driven|test-benchmark-gate-code|test-benchmark-code must-fix dimensions
- Change: E1's phase gate runs the `test-benchmark-gate-code` measure `test-benchmark-code must-fix dimensions` before E4, so the review phase does not find it first. It failed 2 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-9, E-15, E-17
- Rule: redispatch
- Key: redispatch|test-benchmark|R2
- Change: R2 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@unrecorded --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/pr-review-update.md
- Status: candidate
- Evidence: E-16, E-24
- Rule: redispatch
- Key: redispatch|pr-review-update|R4
- Change: R4 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-update@unrecorded --config new_skill=pr-review-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-12, E-29, E-30, E-31, E-32
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-9 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-10 | gate | R2 | FAIL test-benchmark-gate-code |
| E-11 | gate | R2 | FAIL test-benchmark-gate-code |
| E-12 | finding | R2 | recurring_file helper cloned in two test files; corrupt-payload tables and four single-case tests repeat rows. See .context/benchmarks/feat-local-3-recurring-expenses_p1_code.json |
| E-15 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-16 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-17 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-21 | gate | orchestrator | FAIL closure |
| E-23 | gate | orchestrator | FAIL closure |
| E-24 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-25 | gate | orchestrator | FAIL closure |
| E-29 | fix-commit | E1 | fix: feat-local-3-recurring-expenses-F01 share recurring_file in conftest, merge corrupt tables |
| E-30 | fix-commit | E1 | test: feat-local-3-recurring-expenses-F01 recurring_file helper and repeated corrupt cases (red) |
| E-31 | fix-commit | E1 | fix: phase 5 add uses _today(); clears ruff DTZ011 |
| E-32 | fix-commit | E1 | fix: F4 reject a budgets file of the wrong shape |
