RUN_BY_COMMAND: run-learnings
Run: 20261021-r5-run1-cadence-haiku
Cadence: unrecorded
Packet sha256: 2725d6a00384c02059e36c1930e24830d8b7048960f01111628525cabb4fdb44

# Learnings: 20261021-r5-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 14
- fix-commit: 9
- free-form-dispatch: 1
- gate: 88
- stop-point: 1
- stop-refusal: 2

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-5, E-6, E-22
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-9, E-10, E-11, E-12, E-13, E-15, E-16, E-17
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 8 times in test-benchmark: fail plan-review-round phase none is not a; fail plan-review-round a finding needs an id.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@unrecorded --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-30, E-45, E-58, E-61
- Rule: gate-repeat
- Key: gate-repeat|cadence|entry-invariant
- Change: Before the return, run the `entry-invariant` gate once and fix every class it names in one pass. In this run it failed 4 times in orchestrator: plan-review verdict is ready with changes cycle; adversarial-review verdict is request changes cycle; adversarial-review cycle limit reached # cycles.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-31, E-32, E-33, E-34, E-35, E-48, E-49, E-50, E-51
- Rule: gate-repeat
- Key: gate-repeat|de-adversarial-reviewer|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 9 times in de-adversarial-reviewer: fail plan-review-round no open round names adversarial-review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@unrecorded --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-38, E-39, E-40, E-41, E-42, E-43, E-53, E-54, E-55, E-56, E-63
- Rule: gate-repeat
- Key: gate-repeat|plan-review|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 11 times in plan-review: fail plan-review-round no open round names plan-review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@unrecorded --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-24
- Rule: free-form-dispatch
- Key: free-form-dispatch|cadence|free-form
- Change: The orchestrator sent 1 free-form subagent prompts. Dispatch each block and the fix round only from its packet (`/<command>` with the Block line).
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-76, E-89, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-82, E-91, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115
- Rule: review-finding
- Key: review-finding|spec-driven|references/review-rigor.md R2 (layer)
- Change: E1 checks `references/review-rigor.md R2 (layer)` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-83, E-92, E-98, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115
- Rule: review-finding
- Key: review-finding|spec-driven|references/review-rigor.md R2 (mean)
- Change: E1 checks `references/review-rigor.md R2 (mean)` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-84, E-93, E-97, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115
- Rule: review-finding
- Key: review-finding|spec-driven|references/review-rigor.md R2 (failure_paths)
- Change: E1 checks `references/review-rigor.md R2 (failure_paths)` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-90, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115
- Rule: review-finding
- Key: review-finding|spec-driven|references/review-rigor.md R2 DRY (ADR-0008)
- Change: E1 checks `references/review-rigor.md R2 DRY (ADR-0008)` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-94, E-95, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115
- Rule: review-finding
- Key: review-finding|spec-driven|references/review-rigor.md R2 (measures: thin_files)
- Change: E1 checks `references/review-rigor.md R2 (measures: thin_files)` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-13
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-96, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115
- Rule: review-finding
- Key: review-finding|spec-driven|references/review-rigor.md R2 (assertions)
- Change: E1 checks `references/review-rigor.md R2 (assertions)` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-14
- Target: SKILL.md
- Status: candidate
- Evidence: E-8
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked record each finding of your
- Change: The hooks refused 1 times with `blocked record each finding of your`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-15
- Target: SKILL.md
- Status: candidate
- Evidence: E-70
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked continue e# phase # check
- Change: The hooks refused 1 times with `blocked continue e# phase # check`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-5 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-6 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-8 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-r5/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-r5/scripts/plan_wave.py" done --stage test-benchm… |
| E-9 | gate | test-benchmark | FAIL plan-review-round: phase None is not a section of the plan: use one of Phase 1, Phase 2, Phase 3, Phase 4, global |
| E-10 | gate | test-benchmark | FAIL plan-review-round: phase None is not a section of the plan: use one of Phase 1, Phase 2, Phase 3, Phase 4, global |
| E-11 | gate | test-benchmark | FAIL plan-review-round: phase None is not a section of the plan: use one of Phase 1, Phase 2, Phase 3, Phase 4, global |
| E-12 | gate | test-benchmark | FAIL plan-review-round: phase None is not a section of the plan: use one of Phase 1, Phase 2, Phase 3, Phase 4, global |
| E-13 | gate | test-benchmark | FAIL plan-review-round: phase None is not a section of the plan: use one of Phase 1, Phase 2, Phase 3, Phase 4, global |
| E-15 | gate | test-benchmark | FAIL plan-review-round: a finding needs an id such as MF-1 and a severity of must-fix or nit |
| E-16 | gate | test-benchmark | FAIL plan-review-round: a finding needs an id such as MF-1 and a severity of must-fix or nit |
| E-17 | gate | test-benchmark | FAIL plan-review-round: a finding needs an id such as MF-1 and a severity of must-fix or nit |
| E-22 | gate | orchestrator | FAIL plan-review-round: round 1 has 11 must-fix rows |
| E-24 | free-form-dispatch | orchestrator | Wait-check: nothing (placeholder) |
| E-30 | gate | orchestrator | FAIL entry-invariant |
| E-31 | gate | de-adversarial-reviewer | FAIL plan-review-round: no open round names adversarial-review for this plan: run plan_wave.py first |
| E-32 | gate | de-adversarial-reviewer | FAIL plan-review-round: no open round names adversarial-review for this plan: run plan_wave.py first |
| E-33 | gate | de-adversarial-reviewer | FAIL plan-review-round: no open round names adversarial-review for this plan: run plan_wave.py first |
| E-34 | gate | de-adversarial-reviewer | FAIL plan-review-round: no open round names adversarial-review for this plan: run plan_wave.py first |
| E-35 | gate | de-adversarial-reviewer | FAIL plan-review-round: no open round names adversarial-review for this plan: run plan_wave.py first |
| E-38 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-39 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-40 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-41 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-42 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-43 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-45 | gate | orchestrator | FAIL entry-invariant |
| E-48 | gate | de-adversarial-reviewer | FAIL plan-review-round: no open round names adversarial-review for this plan: run plan_wave.py first |
| E-49 | gate | de-adversarial-reviewer | FAIL plan-review-round: no open round names adversarial-review for this plan: run plan_wave.py first |
| E-50 | gate | de-adversarial-reviewer | FAIL plan-review-round: no open round names adversarial-review for this plan: run plan_wave.py first |
| E-51 | gate | de-adversarial-reviewer | FAIL plan-review-round: no open round names adversarial-review for this plan: run plan_wave.py first |
| E-53 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-54 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-55 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-56 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-58 | gate | orchestrator | FAIL entry-invariant |
| E-61 | gate | orchestrator | FAIL entry-invariant |
| E-63 | gate | plan-review | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-70 | stop-refusal | orchestrator | BLOCKED: Continue E1: phase 4 (Check and close). Commit it as 'phase 4: <subject>' before the next phase. |
| E-76 | finding | pr-review-local | divmod floors negative cents: _amount(-5) gives -1.95 and _amount(-150) gives -2.50. Reachable by hand-editing ledger.json; add() blocks negative rows. Tests cover only positive amounts. Repro in PR_REVIEW_1.md Reproductions. |
| E-82 | finding | test-benchmark | Layer 6 < 7. Totals CLI test sits in the export test file. CLI export tests take expected bytes from _expected (to_csv, the module under test), so they check wiring only. Byte-exact expectations live only in test_header_and_rows. Scorecard .context/benchmarks/feat-local-4-csv-export_code.json. |
| E-83 | finding | test-benchmark | Mean 6.83 < floor 7. Verdict FAIL. Set by F02 (failure_paths 6) and F04 (layer 6). Scorecard .context/benchmarks/feat-local-4-csv-export_code.json. |
| E-84 | finding | test-benchmark | Corrupt ledger file holding not-json makes export exit 1 with a Python Traceback. Bad-input convention is one error line and exit 2. No test covers it. failure_paths 6 is below the floor of 7. Scorecard .context/benchmarks/feat-local-4-csv-export_code.json. |
| E-89 | finding | pr-review-update | divmod floors negative cents: _amount(-5) gives -1.95 and _amount(-150) gives -2.50. Reachable by hand-editing ledger.json; add() blocks negative rows. Tests cover only positive amounts. Repro in PR_REVIEW_1.md Reproductions. |
| E-90 | finding | pr-review-update | tests/test_export.py repeats main(["--file", str(ledger_file), "export", ...]) in about ten tests; to_csv(Ledger(ledger_file).expenses(...)) repeats four times; the header literal repeats in test_export_empty_month_is_header_only while HEADER exists. DRY scores 6, below the floor of 7. |
| E-91 | finding | pr-review-update | Layer 6 < 7. Totals CLI test sits in the export test file. CLI export tests take expected bytes from _expected (to_csv, the module under test), so they check wiring only. Byte-exact expectations live only in test_header_and_rows. Scorecard .context/benchmarks/feat-local-4-csv-export_code.json. |
| E-92 | finding | pr-review-update | Mean 6.83 < floor 7. Verdict FAIL. Set by F02 (failure_paths 6) and F04 (layer 6). Scorecard .context/benchmarks/feat-local-4-csv-export_code.json. |
| E-93 | finding | pr-review-update | Corrupt ledger file holding not-json makes export exit 1 with a Python Traceback. Bad-input convention is one error line and exit 2. No test covers it. failure_paths 6 is below the floor of 7. Scorecard .context/benchmarks/feat-local-4-csv-export_code.json. |
| E-94 | finding | pr-review-update | Fix commit 68cb9ea moved the totals test into a new file tests/test_cli.py that holds one test. test_shape --change at HEAD 68cb9ea: thin_files value 1, threshold 0, verdict fail (offender: tests/test_cli.py, 1 test of src/budgetcli/cli.py, also tested by tests/test_export.py). The R2 record at c78ee12 passed thin_files with 0. Fix direction: fold test_totals_output_is_unchanged into an existing … |
| E-95 | finding | pr-review-update | Fix commit 68cb9ea moved the totals test into a new file tests/test_cli.py that holds one test. test_shape --change at HEAD 68cb9ea: thin_files value 1, threshold 0, verdict fail (offender: tests/test_cli.py, 1 test of src/budgetcli/cli.py, also tested by tests/test_export.py). The R2 record at c78ee12 passed thin_files with 0. Fix direction: fold test_totals_output_is_unchanged into an existing … |
| E-96 | finding | test-benchmark | Mutant sorting by (day, note) survives: notes first and second sort in file order, so the test cannot tell a stable sort from a sort by note. Assertions score 6. Scorecard .context/benchmarks/feat-local-4-csv-export_code.json at 68cb9ea. |
| E-97 | finding | test-benchmark | Mutant with bare raise in Ledger.load survives. No test has a ledger row with a missing key. KeyError is handled only by the ValueError wrap, and no test pins it. Failure paths score 6. Scorecard .context/benchmarks/feat-local-4-csv-export_code.json at 68cb9ea. |
| E-98 | finding | test-benchmark | Mean 6.33 below floor 7. Verdict FAIL. Set by MF-2 (dry and layer 6), F07 (assertions 6), F08 (failure_paths 6). Scorecard .context/benchmarks/feat-local-4-csv-export_code.json at 68cb9ea. |
| E-107 | fix-commit | E1 | fix: feat-local-4-csv-export-595744b8-MF-2 totals test moves into test_ledger, thin file removed |
| E-108 | fix-commit | E1 | fix: feat-local-4-csv-export-F08 corrupt ledger test covers a missing key and a bad date |
| E-109 | fix-commit | E1 | fix: feat-local-4-csv-export-F07 same-day test uses notes that a sort by note would reorder |
| E-110 | fix-commit | E1 | fix: feat-local-4-csv-export-F04 export tests assert byte-exact output; totals test moves to test_cli |
| E-111 | fix-commit | E1 | fix: feat-local-4-csv-export-F02 corrupt ledger is one error line |
| E-112 | fix-commit | E1 | test: feat-local-4-csv-export-F02 corrupt ledger is an error line (red) |
| E-113 | fix-commit | E1 | fix: feat-local-4-csv-export-F01 export tests share one CLI helper and HEADER |
| E-114 | fix-commit | E1 | fix: feat-local-4-csv-export-595744b8-MF-1 negative amounts keep their sign |
| E-115 | fix-commit | E1 | test: feat-local-4-csv-export-595744b8-MF-1 negative amounts (red) |
