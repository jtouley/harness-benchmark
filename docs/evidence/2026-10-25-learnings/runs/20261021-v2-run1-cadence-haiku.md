RUN_BY_COMMAND: run-learnings
Run: 20261021-v2-run1-cadence-haiku
Cadence: ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e
Packet sha256: ac42af6f4f9adb5d9bd0570e4d3bd313a190c02576f3454edc5e29605d057f54

# Learnings: 20261021-v2-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 1
- fix-commit: 2
- free-form-dispatch: 1
- gate: 76
- hard-stop: 1
- stop-refusal: 5

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-8, E-13, E-15, E-38, E-39, E-40, E-41
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 7 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix; fail plan-review-round changed phase # which no.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-17, E-18, E-19, E-20, E-21, E-22, E-24, E-25, E-27, E-30, E-32, E-33, E-35, E-37
- Rule: gate-repeat
- Key: gate-repeat|plan-review|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 14 times in plan-review: fail plan-review-round no open round names plan-review; fail plan-review-round round # waits on adversarial-review; fail plan-review-round the run has no plan.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-26, E-29, E-44, E-49, E-50, E-51, E-52, E-53
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 8 times in test-benchmark: fail plan-review-round no open round names test-benchmark-plan; fail plan-review-round the run has no plan; fail plan-review-round in round # a must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: SKILL.md
- Status: candidate
- Evidence: E-47, E-55
- Rule: gate-repeat
- Key: gate-repeat|cadence|test-benchmark-gate-plan
- Change: Before the return, run the `test-benchmark-gate-plan` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: test-benchmark-plan must-fix dimensions below # dry; test-benchmark-plan must-fix dimensions below # assertion_strength.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: SKILL.md
- Status: candidate
- Evidence: E-81, E-82, E-83
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: feat-local-#-csv-export-f# must-fix status fixed not terminal.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-4
- Rule: free-form-dispatch
- Key: free-form-dispatch|cadence|free-form
- Change: The orchestrator sent 1 free-form subagent prompts. Dispatch each block and the fix round only from its packet (`/<command>` with the Block line).
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-72, E-85, E-86
- Rule: review-finding
- Key: review-finding|spec-driven|skills/test-benchmark/SKILL.md mutation resilience; review-rigor.md adversarial inputs (missing)
- Change: E1 checks `skills/test-benchmark/SKILL.md mutation resilience; review-rigor.md adversarial inputs (missing)` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: SKILL.md
- Status: candidate
- Evidence: E-84
- Rule: hard-stop
- Key: hard-stop|cadence|R5|retries
- Change: R5 recorded a `retries` hard stop: r# closure finding feat-local-#-csv-export-f# stays status fixed not verified after one fix. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-9, E-16, E-23, E-43
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked record each finding of your
- Change: The hooks refused 4 times with `blocked record each finding of your`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: SKILL.md
- Status: candidate
- Evidence: E-78
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 1 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-4 | free-form-dispatch | orchestrator | Wait on vibe-test peer result |
| E-8 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-9 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" done --stage test-benchmar… |
| E-13 | gate | orchestrator | FAIL plan-review-round: round 1 has 11 must-fix rows |
| E-15 | gate | orchestrator | FAIL plan-review-round: round 2 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-16 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" add --stage plan-review --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" done --stage plan-review` (referen… |
| E-17 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-18 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-19 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-20 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-21 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-22 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-23 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" done --stage test-benchmar… |
| E-24 | gate | plan-review | FAIL plan-review-round: the run has no plan. Run P1 (/plan-create) first |
| E-25 | gate | plan-review | FAIL plan-review-round: round 2 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-26 | gate | test-benchmark | FAIL plan-review-round: no open round names test-benchmark-plan for this plan: run plan_wave.py first |
| E-27 | gate | plan-review | FAIL plan-review-round: in round 2 a must-fix may target only a section that the update changed, or one where plan-review still had a must-fix: Phase 1, Phase 2, Phase 3. Record a finding in global as a nit |
| E-29 | gate | test-benchmark | FAIL plan-review-round: the run has no plan. Run P1 (/plan-create) first |
| E-30 | gate | plan-review | FAIL plan-review-round: round 2 waits on adversarial-review, test-benchmark-plan |
| E-32 | gate | plan-review | FAIL plan-review-round: add a row for each must-fix item of the review: MF-2 |
| E-33 | gate | plan-review | FAIL plan-review-round: round 2 waits on adversarial-review |
| E-35 | gate | plan-review | FAIL plan-review-round: plan_feat-local-4-csv-export.md reviews this plan, but its verdict `READY TO EXECUTE` is not a plan-review verdict: write `Verdict:` and one of `READY TO EXECUTE`, `NOT READY`, `READY WITH CHANGES`, `REQUEST CHANGES` |
| E-37 | gate | plan-review | FAIL plan-review-round: round 2 has 6 must-fix rows |
| E-38 | gate | orchestrator | FAIL plan-review-round: round 2 has 6 must-fix rows |
| E-39 | gate | orchestrator | FAIL plan-review-round: /plan-update changed Phase 2, which no finding of round 2 names. Send /plan-update again: undo that change, and change only Phase 1, Phase 3. The change: - - 1250 cents prints `12.50`. 5 cents prints `0.05`. 0 cents prints `0.00`. -5 cents prints `-0.05`. -1250 cents prints `-12.50`. \| + - One `pytest.mark.parametrize` table of amounts, each row a cents value and its exact… |
| E-40 | gate | orchestrator | FAIL plan-review-round: /plan-update changed Phase 2, which no finding of round 2 names. Send /plan-update again: undo that change, and change only Phase 1, Phase 3. The change: - - 1250 cents prints `12.50`. 5 cents prints `0.05`. 0 cents prints `0.00`. -5 cents prints `-0.05`. -1250 cents prints `-12.50`. \| + - One `pytest.mark.parametrize` table of amounts, each row a cents value and its exact… |
| E-41 | gate | orchestrator | FAIL plan-review-round: round 3 waits on adversarial-review, test-benchmark-plan |
| E-43 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" done --stage test-benchmar… |
| E-44 | gate | test-benchmark | FAIL plan-review-round: in round 3 a must-fix may target only a section that the update changed, or one where test-benchmark-plan still had a must-fix: Phase 1, Phase 3. Record a finding in Phase 2 as a nit |
| E-47 | gate | orchestrator | FAIL test-benchmark-gate-plan |
| E-49 | gate | test-benchmark | FAIL plan-review-round: no open round names test-benchmark-plan for this plan: run plan_wave.py first |
| E-50 | gate | test-benchmark | FAIL plan-review-round: no open round names test-benchmark-plan for this plan: run plan_wave.py first |
| E-51 | gate | test-benchmark | FAIL plan-review-round: no open round names test-benchmark-plan for this plan: run plan_wave.py first |
| E-52 | gate | test-benchmark | FAIL plan-review-round: no open round names test-benchmark-plan for this plan: run plan_wave.py first |
| E-53 | gate | test-benchmark | FAIL plan-review-round: no open round names test-benchmark-plan for this plan: run plan_wave.py first |
| E-55 | gate | orchestrator | FAIL test-benchmark-gate-plan |
| E-72 | finding | test-benchmark | Refusal test for --out naming the ledger never starts with the ledger missing. Deleting the resolve() equality guard in src/budgetcli/cli.py _names_ledger_file survives 39 passing tests. Real CLI with guard deleted: export --out missing.json exits 0 and writes the CSV into the ledger path, then add exits 2 (Expecting value). Fix: add a missing-ledger row to the existing parametrize table. |
| E-78 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 9 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-81 | gate | orchestrator | FAIL closure |
| E-82 | gate | orchestrator | FAIL closure |
| E-83 | gate | orchestrator | FAIL closure |
| E-84 | hard-stop | orchestrator | R5 closure: finding feat-local-4-csv-export-F01 stays status=fixed, not verified, after one fix round, R2 re-score PASS, R4 close pass, and two pr-review-update runs. No retries left on this path; ledger transition needs a person to check. |
| E-85 | fix-commit | E1 | fix: feat-local-4-csv-export-F01 missing ledger is refused as --out |
| E-86 | fix-commit | E1 | test: feat-local-4-csv-export-F01 missing ledger is refused as --out (red) |
