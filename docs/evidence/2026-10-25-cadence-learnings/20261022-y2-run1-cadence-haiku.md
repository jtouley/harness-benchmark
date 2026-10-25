RUN_BY_COMMAND: run-learnings
Run: 20261022-y2-run1-cadence-haiku
Cadence: 70ae163507b73634e129ce470b0a945f4b095dd2
Packet sha256: a4d659cd30159982165df14700e38fa550963733f16877a0ca37062c412747fb

# Learnings: 20261022-y2-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 15
- gate: 39
- hard-stop: 1
- orchestrator-runner: 1
- stop-refusal: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-9, E-17, E-33, E-40
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 4 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-20, E-45
- Rule: gate-repeat
- Key: gate-repeat|cadence|deferral-register
- Change: Before the return, run the `deferral-register` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: deferral-register deferral-review no ruling of the.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: skills/vibe-test/SKILL.md
- Status: candidate
- Evidence: E-5, E-31
- Rule: redispatch
- Key: redispatch|vibe-test|A5
- Change: A5 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=vibe-test@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=vibe-test@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/plan-create.md
- Status: candidate
- Evidence: E-6, E-32
- Rule: redispatch
- Key: redispatch|plan-create|P1
- Change: P1 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-create@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=plan-create@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-10, E-34
- Rule: redispatch
- Key: redispatch|plan-review|P3
- Change: P3 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-11, E-35
- Rule: redispatch
- Key: redispatch|de-adversarial-reviewer|P6
- Change: P6 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-12, E-36
- Rule: redispatch
- Key: redispatch|test-benchmark|P7
- Change: P7 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-18, E-27, E-41
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-23, E-48
- Rule: redispatch
- Key: redispatch|spec-driven|E1
- Change: E1 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: SKILL.md
- Status: candidate
- Evidence: E-56
- Rule: orchestrator-runner
- Key: orchestrator-runner|cadence|runner
- Change: The orchestrator ran 1 project commands. It runs the manifest only; project commands run inside a block subagent or a gate.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-57
- Rule: hard-stop
- Key: hard-stop|spec-driven|E1|retries
- Change: E1 recorded a `retries` hard stop: e# gate fails at phase # the plan s phase # is. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: SKILL.md
- Status: candidate
- Evidence: E-26
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 1 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-5 | dispatch | A5 | /vibe-test dispatched as A5 |
| E-6 | dispatch | P1 | /plan-create dispatched as P1 |
| E-9 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-10 | dispatch | P3 | /plan-review dispatched as P3 |
| E-11 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-12 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-17 | gate | orchestrator | FAIL plan-review-round: round 1 has 13 must-fix rows |
| E-18 | dispatch | P4 | /plan-update dispatched as P4 |
| E-20 | gate | orchestrator | FAIL deferral-register |
| E-23 | dispatch | E1 | /spec-driven dispatched as E1 |
| E-26 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 2 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-27 | dispatch | P4 | /plan-update dispatched as P4 |
| E-31 | dispatch | A5 | /vibe-test dispatched as A5 |
| E-32 | dispatch | P1 | /plan-create dispatched as P1 |
| E-33 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-34 | dispatch | P3 | /plan-review dispatched as P3 |
| E-35 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-36 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-40 | gate | orchestrator | FAIL plan-review-round: round 1 has 21 must-fix rows |
| E-41 | dispatch | P4 | /plan-update dispatched as P4 |
| E-45 | gate | orchestrator | FAIL deferral-register |
| E-48 | dispatch | E1 | /spec-driven dispatched as E1 |
| E-56 | orchestrator-runner | orchestrator | (python3 -m pytest -q 2>&1 \| tail -5); echo "---"; ls src/budgetcli tests; echo "--- manual check"; python3 -m budgetcli export --month 2026-10 2>&1 \| head -5; echo "exit=$?"; python3 -m budgetcli export --month 2026-13 ; echo "exit=$?"; git status --short \| head |
| E-57 | hard-stop | orchestrator | E1 gate fails at phase 1: the plan's Phase 1 is tests-only, its tests pass at HEAD, and no honest phase 1 commit exists. Plan frozen after P9. A fresh run gave the same phase order. The plan needs a change to Phase 1 (merge into Phase 2, or allow a red-only phase). |
