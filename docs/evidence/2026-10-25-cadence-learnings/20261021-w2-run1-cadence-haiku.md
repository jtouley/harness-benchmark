RUN_BY_COMMAND: run-learnings
Run: 20261021-w2-run1-cadence-haiku
Cadence: dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451
Packet sha256: 978ccdc2ac4d0d1abc50c4433b74d346c49ed21fbecb785d5433a94261ace4ec

# Learnings: 20261021-w2-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 8
- gate: 35
- hard-stop: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-6, E-13
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-15, E-16, E-17
- Rule: gate-repeat
- Key: gate-repeat|plan-update|plan-update-gate
- Change: Before the return, run the `plan-update-gate` gate once and fix every class it names in one pass. In this run it failed 3 times in P4: plan-review review limit reached # cycles; plan-review-round the plan has no ## revision.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-32, E-37, E-38, E-40
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 4 times in E1: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; fix step run r# without --check to.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: SKILL.md
- Status: candidate
- Evidence: E-34, E-43
- Rule: gate-repeat
- Key: gate-repeat|cadence|implement-gate
- Change: Before the return, run the `implement-gate` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: implement-gate phase # of # csv rendering; implement-gate phase # of # acceptance and.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-30, E-35
- Rule: redispatch
- Key: redispatch|spec-driven|E1
- Change: E1 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-44
- Rule: hard-stop
- Key: hard-stop|spec-driven|E1|retries
- Change: E1 recorded a `retries` hard stop: e# phase # blocked by a defect in the pinned acceptance check. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@dd1b12b97ad66b6f0295e0083b7c78a4b3cc7451 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-6 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-13 | gate | orchestrator | FAIL plan-review-round: round 1 has 16 must-fix rows |
| E-15 | gate | P4 | FAIL plan-update-gate |
| E-16 | gate | P4 | FAIL plan-update-gate |
| E-17 | gate | P4 | FAIL plan-update-gate |
| E-30 | dispatch | E1 | /spec-driven dispatched as E1 |
| E-32 | gate | E1 | FAIL cognitive-complexity |
| E-34 | gate | orchestrator | FAIL implement-gate |
| E-35 | dispatch | E1 | /spec-driven dispatched as E1 |
| E-37 | gate | E1 | FAIL cognitive-complexity |
| E-38 | gate | E1 | FAIL cognitive-complexity |
| E-40 | gate | E1 | FAIL cognitive-complexity |
| E-43 | gate | orchestrator | FAIL implement-gate |
| E-44 | hard-stop | orchestrator | E1 phase 5 blocked by a defect in the pinned acceptance check: AC-1 and AC-4 expect CRLF (\\r\\n) in stdout and in the --out file, but subprocess text mode and read_text both translate CRLF to LF, so these checks cannot pass with any implementation. Needs a user decision: fix the check to read bytes (newline=''), or accept LF output (conflicts with RFC 4180). Phases 1-4 are committed. |
