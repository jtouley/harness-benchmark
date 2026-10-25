RUN_BY_COMMAND: run-learnings
Run: 20261021-w1-run1-cadence-haiku
Cadence: dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451
Packet sha256: 9c631fbc2f19fb8f51818aa63435cebdf053c5b9d0cc2b4dbba907d5f0064c1e

# Learnings: 20261021-w1-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- gate: 23
- hard-stop: 2
- stop-refusal: 7

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-8, E-13
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-15, E-17
- Rule: gate-repeat
- Key: gate-repeat|cadence|deferral-register
- Change: Before the return, run the `deferral-register` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: deferral-register deferral-review no ruling of the.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-31
- Rule: hard-stop
- Key: hard-stop|spec-driven|E1|retries
- Change: E1 recorded a `retries` hard stop: e# phase # csv rendering blocked the peer needs the owner to. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-32
- Rule: hard-stop
- Key: hard-stop|spec-driven|E1|retries
- Change: E1 recorded a `retries` hard stop: e# phase # blocked the implementation peer needs the owner to accept. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: SKILL.md
- Status: candidate
- Evidence: E-10, E-23, E-26, E-29
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 4 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-25, E-27, E-30
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in execution. continue
- Change: The hooks refused 3 times with `blocked early stop in execution. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-8 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-10 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-13 | gate | orchestrator | FAIL plan-review-round: round 1 has 17 must-fix rows |
| E-15 | gate | orchestrator | FAIL deferral-register |
| E-17 | gate | orchestrator | FAIL deferral-register |
| E-23 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 7 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-25 | stop-refusal | orchestrator | BLOCKED early stop in execution. Continue E1: send the `/spec-driven` peer the plan again. Its next open phase is phase 2 (CSV rendering). |
| E-26 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-27 | stop-refusal | orchestrator | BLOCKED early stop in execution. Continue E1: send the `/spec-driven` peer the plan again. Its next open phase is phase 2 (CSV rendering). |
| E-29 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 417 characters; the limit is 300. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-30 | stop-refusal | orchestrator | BLOCKED early stop in execution. Continue E1: send the `/spec-driven` peer the plan again. Its next open phase is phase 2 (CSV rendering). |
| E-31 | hard-stop | orchestrator | E1 phase 2 (CSV rendering) blocked: the peer needs the owner to accept the quoting record (status: proposed in .context/implementation/feat-local-4-csv-export_stage4.md). Four peer runs stopped on the same condition; no retry can clear it. Resume with activate_session.py --from-branch --resume after the owner accepts the record. |
| E-32 | hard-stop | orchestrator | E1 phase 2 blocked: the implementation peer needs the owner to accept the quoting record (still proposed). Four peer runs stopped on the same condition; no retry can clear it. Resume after the owner accepts the record. |
