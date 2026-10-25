RUN_BY_COMMAND: run-learnings
Run: 20261021-r4-run1-cadence-haiku
Cadence: unrecorded
Packet sha256: d914c2bf766826f0a50163199db797252b0e04cdd384fbf1b854b48a25731baa

# Learnings: 20261021-r4-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 20
- gate: 45
- hard-stop: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-10, E-17, E-19, E-26, E-29, E-34, E-39
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 7 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-41, E-42
- Rule: gate-repeat
- Key: gate-repeat|plan-review|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in P3: fail plan-review-round write the plan review of; fail plan-review-round round # waits on plan-review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@unrecorded --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-46, E-55, E-62, E-65
- Rule: gate-repeat
- Key: gate-repeat|cadence|test-benchmark-gate-plan
- Change: Before the return, run the `test-benchmark-gate-plan` gate once and fix every class it names in one pass. In this run it failed 4 times in orchestrator: test-benchmark-plan scores must be numbers must_fix_dimensions send; test-benchmark-plan scores must be numbers must_fix_dimensions dry_no_clone_setups.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-49, E-57, E-58, E-59, E-60
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 5 times in P7: fail plan-review-round no open round names test-benchmark-plan.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@unrecorded --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-11, E-20, E-30, E-40
- Rule: redispatch
- Key: redispatch|plan-review|P3
- Change: P3 was dispatched 4 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@unrecorded --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-12, E-21, E-31
- Rule: redispatch
- Key: redispatch|de-adversarial-reviewer|P6
- Change: P6 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@unrecorded --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-13, E-22, E-47, E-53, E-56, E-64
- Rule: redispatch
- Key: redispatch|test-benchmark|P7
- Change: P7 was dispatched 6 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@unrecorded --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-18, E-27, E-35, E-50, E-63
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 5 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@unrecorded --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-66
- Rule: hard-stop
- Key: hard-stop|test-benchmark|P7|retries
- Change: P7 recorded a `retries` hard stop: p# test-benchmark-gate-plan fails after # peer runs and # plan-update cycles the. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@unrecorded --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-10 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-11 | dispatch | P3 | /plan-review dispatched as P3 |
| E-12 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-13 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-17 | gate | orchestrator | FAIL plan-review-round: round 1 has 17 must-fix rows |
| E-18 | dispatch | P4 | /plan-update dispatched as P4 |
| E-19 | gate | orchestrator | FAIL plan-review-round: round 2 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-20 | dispatch | P3 | /plan-review dispatched as P3 |
| E-21 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-22 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-26 | gate | orchestrator | FAIL plan-review-round: round 2 has 4 must-fix rows |
| E-27 | dispatch | P4 | /plan-update dispatched as P4 |
| E-29 | gate | orchestrator | FAIL plan-review-round: round 3 waits on plan-review, adversarial-review |
| E-30 | dispatch | P3 | /plan-review dispatched as P3 |
| E-31 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-34 | gate | orchestrator | FAIL plan-review-round: round 3 has 2 must-fix rows |
| E-35 | dispatch | P4 | /plan-update dispatched as P4 |
| E-39 | gate | orchestrator | FAIL plan-review-round: round 4 waits on plan-review |
| E-40 | dispatch | P3 | /plan-review dispatched as P3 |
| E-41 | gate | P3 | FAIL plan-review-round: write the plan review of this plan first: its `Last reviewed plan sha256:` line names it |
| E-42 | gate | P3 | FAIL plan-review-round: round 4 waits on plan-review |
| E-46 | gate | orchestrator | FAIL test-benchmark-gate-plan |
| E-47 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-49 | gate | P7 | FAIL plan-review-round: no open round names test-benchmark-plan for this plan: run plan_wave.py first |
| E-50 | dispatch | P4 | /plan-update dispatched as P4 |
| E-53 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-55 | gate | orchestrator | FAIL test-benchmark-gate-plan |
| E-56 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-57 | gate | P7 | FAIL plan-review-round: no open round names test-benchmark-plan for this plan: run plan_wave.py first |
| E-58 | gate | P7 | FAIL plan-review-round: no open round names test-benchmark-plan for this plan: run plan_wave.py first |
| E-59 | gate | P7 | FAIL plan-review-round: no open round names test-benchmark-plan for this plan: run plan_wave.py first |
| E-60 | gate | P7 | FAIL plan-review-round: no open round names test-benchmark-plan for this plan: run plan_wave.py first |
| E-62 | gate | orchestrator | FAIL test-benchmark-gate-plan |
| E-63 | dispatch | P4 | /plan-update dispatched as P4 |
| E-64 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-65 | gate | orchestrator | FAIL test-benchmark-gate-plan |
| E-66 | hard-stop | orchestrator | P7 test-benchmark-gate-plan fails after 4 peer runs and 2 plan-update cycles: the benchmark JSON puts must_fix_dimensions inside scores, which the gate rejects (scores must be numbers). The peer repeats this shape. Peer verdicts still list must-fix rows (tb-F05, dry_no_clone_setups). Plan is READY TO EXECUTE per P3/P6. |
