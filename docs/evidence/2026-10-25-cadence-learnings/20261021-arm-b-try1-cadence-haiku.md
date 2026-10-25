RUN_BY_COMMAND: run-learnings
Run: 20261021-arm-b-try1-cadence-haiku
Cadence: db1bedea9cca31d219953b1c728b009983aeb9a5
Packet sha256: fd7a54a93a0215431123ae496d7e8e6987b0c147518c4a0fe4af125cc5378fc7

# Learnings: 20261021-arm-b-try1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 2
- gate: 11
- hard-stop: 1

## Proposals

### L-1
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-8, E-9, E-10, E-11
- Rule: gate-repeat
- Key: gate-repeat|plan-review|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 4 times in plan-review: fail plan-review-round stage must be one of; fail plan-review-round no open round names plan-review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-create.md
- Status: candidate
- Evidence: E-4, E-13
- Rule: redispatch
- Key: redispatch|plan-create|P1
- Change: P1 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-create@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=plan-create@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-14
- Rule: hard-stop
- Key: hard-stop|cadence|orchestrator|retries
- Change: orchestrator recorded a `retries` hard stop: local-# plan cannot reach e#. run # p# ready with changes mf. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-4 | dispatch | P1 | /plan-create dispatched as P1 |
| E-8 | gate | plan-review | FAIL plan-review-round: stage must be one of []: a peer of the plan round in stages.json |
| E-9 | gate | plan-review | FAIL plan-review-round: stage must be one of []: a peer of the plan round in stages.json |
| E-10 | gate | plan-review | FAIL plan-review-round: stage must be one of []: a peer of the plan round in stages.json |
| E-11 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-13 | dispatch | P1 | /plan-create dispatched as P1 |
| E-14 | hard-stop | orchestrator | LOCAL-4 plan cannot reach E1. Run 29080b6e: P3 READY WITH CHANGES (MF-1 CRLF on stdout, MF-2 acceptance-commit statement, MF-3 per-phase commits). P9 marker was written early by an out-of-order headless.py next run, and it freezes the plan. Run 720fff72: P1 stopped because existing P1 artifacts pin repo-map a58bd343e379 but the old plan pins 06a4b8b97fce. Needs user decision: regenerate P1 (overw… |
