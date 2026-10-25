RUN_BY_COMMAND: run-learnings
Run: 20261021-arm-a-cadence-haiku
Cadence: db1bedea9cca31d219953b1c728b009983aeb9a5
Packet sha256: c17e4f44100c15b12f0da94f91a63a09edddb5ef0181a0b6249e8152e9742bd8

# Learnings: 20261021-arm-a-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- gate: 29
- hard-stop: 1
- stop-point: 1
- stop-refusal: 5

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-5, E-7, E-8, E-11, E-15
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 5 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix; fail plan-review-round changed global which no finding.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-9, E-10
- Rule: gate-repeat
- Key: gate-repeat|plan-update|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in plan-update: fail plan-review-round changed global which no finding; fail plan-review-round round # waits on plan-review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-13, E-14, E-17, E-18, E-19, E-20, E-21, E-22, E-23, E-24, E-25, E-26, E-27, E-28, E-29, E-30, E-33, E-34
- Rule: gate-repeat
- Key: gate-repeat|plan-review|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 18 times in plan-review: fail plan-review-round no open round names plan-review; fail plan-review-round write the plan review of; fail plan-review-round round # waits on plan-review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-36
- Rule: hard-stop
- Key: hard-stop|plan-review|P3|retries
- Change: P3 recorded a `retries` hard stop: p# plan review round # cannot close done counts the pinned round. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: SKILL.md
- Status: candidate
- Evidence: E-12, E-16, E-32
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked record each finding of your
- Change: The hooks refused 3 times with `blocked record each finding of your`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-31, E-35
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in planning. continue
- Change: The hooks refused 2 times with `blocked early stop in planning. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|plan-review|P3|retries hard stop at p
- Change: The run stopped at P3: retries hard stop at p# round # said request changes and the gate did. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | P3 | retries hard stop at P3: round 2 said REQUEST CHANGES and the gate did not read it; no code |
| E-5 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review |
| E-7 | gate | orchestrator | FAIL plan-review-round: round 1 has 2 must-fix rows |
| E-8 | gate | orchestrator | FAIL plan-review-round: /plan-update changed global, which no finding of round 1 names. Send /plan-update again: undo that change, and change only Phase 1, Phase 2 |
| E-9 | gate | plan-update | FAIL plan-review-round: /plan-update changed global, which no finding of round 1 names. Send /plan-update again: undo that change, and change only Phase 1, Phase 2 |
| E-10 | gate | plan-update | FAIL plan-review-round: round 2 waits on plan-review |
| E-11 | gate | orchestrator | FAIL plan-review-round: round 2 waits on plan-review |
| E-12 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/c6d1ea46-c870-51fa-ab2e-339fb5a9722d/scratchpad/xp/cadence-a/scripts/plan_wave.py" add --stage plan-review --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/c6d1ea46-c870-51fa-ab2e-339fb5a9722d/scratchpad/xp/cadence-a/scripts/plan_wave.py" done --stage plan-review` (references/plan-review-… |
| E-13 | gate | plan-review | FAIL plan-review-round: write the plan review of this plan first: its `Last reviewed plan sha256:` line names it |
| E-14 | gate | plan-review | FAIL plan-review-round: write the plan review of this plan first: its `Last reviewed plan sha256:` line names it |
| E-15 | gate | orchestrator | FAIL plan-review-round: round 2 waits on plan-review |
| E-16 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/c6d1ea46-c870-51fa-ab2e-339fb5a9722d/scratchpad/xp/cadence-a/scripts/plan_wave.py" add --stage plan-review --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/c6d1ea46-c870-51fa-ab2e-339fb5a9722d/scratchpad/xp/cadence-a/scripts/plan_wave.py" done --stage plan-review` (references/plan-review-… |
| E-17 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-18 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-19 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-20 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-21 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-22 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-23 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-24 | gate | plan-review | FAIL plan-review-round: the run has no plan. Run P1 (/plan-create) first |
| E-25 | gate | plan-review | FAIL plan-review-round: round 2 waits on plan-review |
| E-26 | gate | plan-review | FAIL plan-review-round: round 2 waits on plan-review |
| E-27 | gate | plan-review | FAIL plan-review-round: in round 2 a must-fix may target only a section that the update changed, or one where plan-review still had a must-fix: Phase 1, Phase 2. Record a finding in Phase 3 as a nit |
| E-28 | gate | plan-review | FAIL plan-review-round: write the plan review of this plan first: its `Last reviewed plan sha256:` line names it |
| E-29 | gate | plan-review | FAIL plan-review-round: write the plan review of this plan first: its `Last reviewed plan sha256:` line names it |
| E-30 | gate | plan-review | FAIL plan-review-round: round 2 waits on plan-review |
| E-31 | stop-refusal | orchestrator | BLOCKED early stop in planning. Continue paceline: next P3 (plan-review) via `send these peers in one message, in parallel: /plan-review .context/plans/feat-local-4-csv-export.plan.md`: plan-review-round: round 2 waits on plan-review. |
| E-32 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/c6d1ea46-c870-51fa-ab2e-339fb5a9722d/scratchpad/xp/cadence-a/scripts/plan_wave.py" add --stage plan-review --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/c6d1ea46-c870-51fa-ab2e-339fb5a9722d/scratchpad/xp/cadence-a/scripts/plan_wave.py" done --stage plan-review` (references/plan-review-… |
| E-33 | gate | plan-review | FAIL plan-review-round: in round 2 a must-fix may target only a section that the update changed, or one where plan-review still had a must-fix: Phase 1, Phase 2. Record a finding in global as a nit |
| E-34 | gate | plan-review | FAIL plan-review-round: write the plan review of this plan first: its `Last reviewed plan sha256:` line names it |
| E-35 | stop-refusal | orchestrator | BLOCKED early stop in planning. Continue paceline: next P3 (plan-review) via `send these peers in one message, in parallel: /plan-review .context/plans/feat-local-4-csv-export.plan.md`: plan-review-round: round 2 waits on plan-review. |
| E-36 | hard-stop | orchestrator | P3 plan review round 2 cannot close: plan_wave.py done counts the pinned round-1 review file (sha 7c17b618), which must name plan sha ccc5013a. Three reviewer attempts recorded findings (MF-1 in Phase 1, open) and stopped. Needs a gate fix or an explicit user ruling on the pinned file. |
