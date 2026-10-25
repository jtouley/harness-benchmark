RUN_BY_COMMAND: run-learnings
Run: 20261022-x1-run1-cadence-haiku
Cadence: 9c2505a78ef6f6d74e057975cc9f3919db2e4dc5
Packet sha256: 81bc2b480d834b3629a7910a949990a1081d110826475f0a1cf60c2d9eb2d39c

# Learnings: 20261022-x1-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- gate: 51
- hard-stop: 1
- stop-refusal: 4

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-10, E-15
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-32, E-33, E-35, E-39, E-46, E-47, E-53
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 7 times in spec-driven: types index value of type reader is; types.max is # fix each mypy finding; fix step run r# without --check to.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-36, E-38, E-45, E-50
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|acceptance
- Change: Before the return, run the `acceptance` gate once and fix every class it names in one pass. In this run it failed 4 times in spec-driven: acceptance ac-# has an open defect check_rfc#_quoting; acceptance ac-# failed exit # . claim.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: SKILL.md
- Status: candidate
- Evidence: E-41, E-48, E-54
- Rule: gate-repeat
- Key: gate-repeat|cadence|implement-gate
- Change: Before the return, run the `implement-gate` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: implement-gate acceptance ac-# has an open defect.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-56
- Rule: hard-stop
- Key: hard-stop|spec-driven|E1|retries
- Change: E1 recorded a `retries` hard stop: e# failed three times on ac-# acceptance check defect . clearing it. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-11
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked record each finding of your
- Change: The hooks refused 1 times with `blocked record each finding of your`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: SKILL.md
- Status: candidate
- Evidence: E-43, E-49, E-55
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in execution. continue
- Change: The hooks refused 3 times with `blocked early stop in execution. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-10 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-11 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-x/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-x/scripts/plan_wave.py" done --stage test-benchmar… |
| E-15 | gate | orchestrator | FAIL plan-review-round: round 1 has 12 must-fix rows |
| E-32 | gate | spec-driven | FAIL cognitive-complexity |
| E-33 | gate | spec-driven | FAIL cognitive-complexity |
| E-35 | gate | spec-driven | FAIL cognitive-complexity |
| E-36 | gate | spec-driven | FAIL acceptance |
| E-38 | gate | spec-driven | FAIL acceptance |
| E-39 | gate | spec-driven | FAIL cognitive-complexity |
| E-41 | gate | orchestrator | FAIL implement-gate |
| E-43 | stop-refusal | orchestrator | BLOCKED early stop in execution. Continue paceline: next E1 (implement) via `/spec-driven` |
| E-45 | gate | spec-driven | FAIL acceptance |
| E-46 | gate | spec-driven | FAIL cognitive-complexity |
| E-47 | gate | spec-driven | FAIL cognitive-complexity |
| E-48 | gate | orchestrator | FAIL implement-gate |
| E-49 | stop-refusal | orchestrator | BLOCKED early stop in execution. Continue paceline: next E1 (implement) via `/spec-driven` |
| E-50 | gate | spec-driven | FAIL acceptance |
| E-53 | gate | spec-driven | FAIL cognitive-complexity |
| E-54 | gate | orchestrator | FAIL implement-gate |
| E-55 | stop-refusal | orchestrator | BLOCKED early stop in execution. Continue paceline: next E1 (implement) via `/spec-driven` |
| E-56 | hard-stop | orchestrator | E1 failed three times on AC-3 (acceptance check defect). Clearing it changes the plan after P9, which needs user approval. Options: approve /plan-update --acceptance AC-3, or start a fresh run. |
