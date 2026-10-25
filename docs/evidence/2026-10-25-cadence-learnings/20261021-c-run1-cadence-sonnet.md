RUN_BY_COMMAND: run-learnings
Run: 20261021-c-run1-cadence-sonnet
Cadence: unrecorded
Packet sha256: 9b733b35bfa973efffd61eb2b366822cc54130d5419a458cde3ad192f20fc73a

# Learnings: 20261021-c-run1-cadence-sonnet

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: no
- transcript: yes

## Evidence counts

- finding: 1
- gate: 19
- stop-point: 1
- stop-refusal: 2

## Proposals

### L-1
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-6
- Rule: review-finding
- Key: review-finding|spec-driven|test-benchmark:dry
- Change: E1 checks `test-benchmark:dry` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-20, E-22
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 2 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-6 | finding | test-benchmark | Plan names no shared helper, fixture or shared case table. The wrong-shape cases repeat in three tests and the Phase 2 bad inputs have no parametrize table. CLI run and Traceback check repeat in every test. |
| E-20 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 3 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-22 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 11 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
