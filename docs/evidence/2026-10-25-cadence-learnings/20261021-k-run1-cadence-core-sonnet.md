RUN_BY_COMMAND: run-learnings
Run: 20261021-k-run1-cadence-core-sonnet
Cadence: unrecorded
Packet sha256: a6cc0256fc20458bf649f22f8ad398763cf7dda6dcc4a9d90aa7261669ff3975

# Learnings: 20261021-k-run1-cadence-core-sonnet

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: no
- transcript: yes

## Evidence counts

- gate: 19
- stop-point: 1
- stop-refusal: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-8, E-9
- Rule: gate-repeat
- Key: gate-repeat|cadence|entry-invariant
- Change: Before the return, run the `entry-invariant` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: adversarial-review conditions not in the plan under; plan-review the plan changed after its review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-7
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 1 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-7 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 3 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-8 | gate | orchestrator | FAIL entry-invariant |
| E-9 | gate | orchestrator | FAIL entry-invariant |
