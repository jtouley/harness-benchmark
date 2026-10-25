RUN_BY_COMMAND: run-learnings
Run: 20261021-v1-run1-cadence-haiku
Cadence: ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e
Packet sha256: 046b75db668b60841d3ddfe730c9e35ffe40beb3df37f204d4b0f676a3d1ee45

# Learnings: 20261021-v1-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 1
- fix-commit: 2
- gate: 79
- hard-stop: 1
- stop-refusal: 9

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-5, E-10, E-11, E-12, E-15, E-20, E-21, E-25, E-34, E-35, E-39, E-41, E-45, E-48, E-50, E-51, E-53, E-54
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 18 times in orchestrator: fail plan-review-round round # has # must-fix; fail plan-review-round round # waits on plan-review; fail plan-review-round round # waits on test-benchmark-plan.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-7, E-26, E-42, E-44
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 4 times in test-benchmark: fail plan-review-round round # waits on plan-review; fail plan-review-round round # waits on test-benchmark-plan; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-22, E-23, E-46
- Rule: gate-repeat
- Key: gate-repeat|plan-update|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 3 times in plan-update: fail plan-review-round the plan has no; fail plan-review-round round # waits on plan-review; fail plan-review-round round # waits on test-benchmark-plan.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-29, E-32
- Rule: gate-repeat
- Key: gate-repeat|de-adversarial-reviewer|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in de-adversarial-reviewer: fail plan-review-round in round # a must-fix; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-62, E-64, E-65, E-67
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 4 times in spec-driven: fix step run r# without --check to; types union-attr item none of io bytes; % duplicated # of # code lines.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-75, E-78
- Rule: gate-repeat
- Key: gate-repeat|cadence|pr-review-local-gate
- Change: Before the return, run the `pr-review-local-gate` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: pr-review-local no peer-written review of this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: SKILL.md
- Status: candidate
- Evidence: E-86, E-87, E-89
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: feat-local-#-csv-# must-fix status fixed not terminal.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-77, E-91, E-92
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-90
- Rule: hard-stop
- Key: hard-stop|cadence|R5|retries
- Change: R5 recorded a `retries` hard stop: r# closure fails mf-# stays status fixed not verified. fix commit. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: SKILL.md
- Status: candidate
- Evidence: E-16, E-28, E-52, E-55
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked record each finding of your
- Change: The hooks refused 4 times with `blocked record each finding of your`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: SKILL.md
- Status: candidate
- Evidence: E-33
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in planning. continue
- Change: The hooks refused 1 times with `blocked early stop in planning. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: SKILL.md
- Status: candidate
- Evidence: E-69, E-73, E-79, E-88
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 4 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-5 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-7 | gate | test-benchmark | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review |
| E-10 | gate | orchestrator | FAIL plan-review-round: round 1 has 15 must-fix rows |
| E-11 | gate | orchestrator | FAIL plan-review-round: /plan-update changed global, which no finding of round 1 names. Send /plan-update again: undo that change, and change only Phase 1, Phase 2, Phase 3 |
| E-12 | gate | orchestrator | FAIL plan-review-round: /plan-update changed global, which no finding of round 1 names. Send /plan-update again: undo that change, and change only Phase 1, Phase 2, Phase 3 |
| E-15 | gate | orchestrator | FAIL plan-review-round: round 2 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-16 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" done --stage test-benchmar… |
| E-20 | gate | orchestrator | FAIL plan-review-round: round 2 has 8 must-fix rows |
| E-21 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review 7cdf0ca71df4)` row for feat-local-4-csv-export-F09, feat-local-4-csv-export-F10, feat-local-4-csv-export-F11 of round-2.md. Send /plan-update again |
| E-22 | gate | plan-update | FAIL plan-review-round: the plan has no `## Revision ledger (review 7cdf0ca71df4)` row for feat-local-4-csv-export-F09, feat-local-4-csv-export-F10, feat-local-4-csv-export-F11 of round-2.md. Send /plan-update again |
| E-23 | gate | plan-update | FAIL plan-review-round: round 3 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-25 | gate | orchestrator | FAIL plan-review-round: round 3 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-26 | gate | test-benchmark | FAIL plan-review-round: round 3 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-28 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" add --stage plan-review --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" done --stage plan-review` (referen… |
| E-29 | gate | de-adversarial-reviewer | FAIL plan-review-round: in round 3 a must-fix may target only a section that the update changed, or one where adversarial-review still had a must-fix: Phase 1, Phase 2, Phase 3. Record a finding in global as a nit |
| E-32 | gate | de-adversarial-reviewer | FAIL plan-review-round: round 3 has 8 must-fix rows |
| E-33 | stop-refusal | orchestrator | BLOCKED early stop in planning. Continue paceline: next P3 (plan-review) via `send the peer `/plan-update .context/plans/feat-local-4-csv-export.plan.md --from-review .context/plan-findings/round-3.md`: plan-review-round: round 3 has 8 must-fix rows. |
| E-34 | gate | orchestrator | FAIL plan-review-round: round 3 has 8 must-fix rows |
| E-35 | gate | orchestrator | FAIL plan-review-round: round 4 waits on plan-review, test-benchmark-plan |
| E-39 | gate | orchestrator | FAIL plan-review-round: round 4 has 3 must-fix rows |
| E-41 | gate | orchestrator | FAIL plan-review-round: round 5 waits on test-benchmark-plan |
| E-42 | gate | test-benchmark | FAIL plan-review-round: round 5 waits on test-benchmark-plan |
| E-44 | gate | test-benchmark | FAIL plan-review-round: round 5 has 1 must-fix rows |
| E-45 | gate | orchestrator | FAIL plan-review-round: round 5 has 1 must-fix rows |
| E-46 | gate | plan-update | FAIL plan-review-round: round 6 waits on test-benchmark-plan |
| E-48 | gate | orchestrator | FAIL plan-review-round: round 6 waits on test-benchmark-plan |
| E-50 | gate | orchestrator | FAIL plan-review-round: round 6 has 1 must-fix rows |
| E-51 | gate | orchestrator | FAIL plan-review-round: round 7 waits on test-benchmark-plan |
| E-52 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" done --stage test-benchmar… |
| E-53 | gate | orchestrator | FAIL plan-review-round: round 7 has 2 must-fix rows |
| E-54 | gate | orchestrator | FAIL plan-review-round: round 8 waits on test-benchmark-plan |
| E-55 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-v/scripts/plan_wave.py" done --stage test-benchmar… |
| E-62 | gate | spec-driven | FAIL cognitive-complexity |
| E-64 | gate | spec-driven | FAIL cognitive-complexity |
| E-65 | gate | spec-driven | FAIL cognitive-complexity |
| E-67 | gate | spec-driven | FAIL cognitive-complexity |
| E-69 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 10 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-73 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 3 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-75 | gate | orchestrator | FAIL pr-review-local-gate |
| E-77 | finding | pr-review-local | --out onto an existing file with mode 600 leaves it at 644 after the export. Repro on c7b6365 (scratch copy of the PR head): printf old > mode.csv; chmod 600 mode.csv; budgetcli --file ledger.json export --out mode.csv; stat -c %a mode.csv prints 644. _write_atomic chmods the new temp file to 0o666 & ~umask and replaces the target, so the mode of an existing file is not kept. The ledger holds per… |
| E-78 | gate | orchestrator | FAIL pr-review-local-gate |
| E-79 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-86 | gate | orchestrator | FAIL closure |
| E-87 | gate | orchestrator | FAIL closure |
| E-88 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 372 characters; the limit is 300. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-89 | gate | orchestrator | FAIL closure |
| E-90 | hard-stop | orchestrator | R5 closure fails: MF-1 stays status=fixed, not verified. Fix commit 2d94e17 exists. Two pr-review-update passes and one pr-review-local retry did not move the row. A fresh pr-review-local could not run: the peer was denied Bash permission. |
| E-91 | fix-commit | E1 | fix: feat-local-4-csv-export-4a976922-MF-1 overwrite keeps existing file mode |
| E-92 | fix-commit | E1 | test: feat-local-4-csv-export-4a976922-MF-1 overwrite keeps existing file mode (red) |
