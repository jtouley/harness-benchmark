RUN_BY_COMMAND: run-learnings
Run: 20261021-r3-run1-cadence-haiku
Cadence: unrecorded
Packet sha256: 55e57605b2f9232335c5d31ea40994d187b79ae62ea932bad0743a7e66a8d33d

# Learnings: 20261021-r3-run1-cadence-haiku

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
- Evidence: E-4, E-11, E-13, E-17, E-18, E-19, E-20
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 7 times in orchestrator: fail plan-review-round changed global which no finding; fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-21
- Rule: hard-stop
- Key: hard-stop|plan-update|P4|retries
- Change: P4 recorded a `retries` hard stop: p# plan-update for review round # failed the plan_wave gate three times. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@unrecorded --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-5
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked record each finding of your
- Change: The hooks refused 1 times with `blocked record each finding of your`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: SKILL.md
- Status: candidate
- Evidence: E-12
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 1 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-4 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-5 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-r3/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-r3/scripts/plan_wave.py" done --stage test-benchm… |
| E-11 | gate | orchestrator | FAIL plan-review-round: round 1 has 7 must-fix rows |
| E-12 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 18 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-13 | gate | orchestrator | FAIL plan-review-round: round 2 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-17 | gate | orchestrator | FAIL plan-review-round: round 2 has 4 must-fix rows |
| E-18 | gate | orchestrator | FAIL plan-review-round: /plan-update changed global, which no finding of round 2 names. Send /plan-update again: undo that change, and change only Phase 3, Phase 4 |
| E-19 | gate | orchestrator | FAIL plan-review-round: /plan-update changed global, which no finding of round 2 names. Send /plan-update again: undo that change, and change only Phase 3, Phase 4 |
| E-20 | gate | orchestrator | FAIL plan-review-round: /plan-update changed global, which no finding of round 2 names. Send /plan-update again: undo that change, and change only Phase 3, Phase 4 |
| E-21 | hard-stop | orchestrator | P4 plan-update for review round 2 failed the plan_wave gate three times: each update changed the global section, which no round-2 finding names. Plan review round 2 (P3 READY TO EXECUTE, P7 PASS) is otherwise clean; P6 round 2 has 4 must-fix rows. |
