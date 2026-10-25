RUN_BY_COMMAND: run-learnings
Run: 20261022-s2-run1-cadence-haiku
Cadence: cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5
Packet sha256: 41a898e5d7a5427f8f01c307b9bb24a72e0d43228fa90d087899223cb012a0e3

# Learnings: 20261022-s2-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 10
- fix-commit: 10
- gate: 61
- hard-stop: 1
- stop-refusal: 2

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-9, E-16
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-20, E-21, E-22
- Rule: gate-repeat
- Key: gate-repeat|cadence|entry-invariant
- Change: Before the return, run the `entry-invariant` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: plan-review review limit reached # cycles; adversarial-review cycle limit reached # cycles.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-46, E-66
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|test-benchmark-gate-code
- Change: Before the return, run the `test-benchmark-gate-code` gate once and fix every class it names in one pass. In this run it failed 2 times in test-benchmark: test-benchmark-code verdict is fail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-49, E-50
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 2 times in spec-driven: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; fix step run r# without --check to.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: SKILL.md
- Status: candidate
- Evidence: E-72, E-73
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: feat-local-#-csv-# must-fix status fixed not terminal. verify; feat-local-#-csv-export-f# must-fix status fixed not terminal. verify.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-37, E-38, E-39, E-40, E-41, E-42, E-56, E-75, E-76, E-77, E-78, E-79, E-80, E-81, E-82, E-83, E-84
- Rule: review-finding
- Key: review-finding|spec-driven|core:plan-conformance
- Change: E1 checks `core:plan-conformance` before E4: the review found 7 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-45, E-57, E-75, E-76, E-77, E-78, E-79, E-80, E-81, E-82, E-83, E-84
- Rule: review-finding
- Key: review-finding|spec-driven|core:test-benchmark
- Change: E1 checks `core:test-benchmark` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-65, E-75, E-76, E-77, E-78, E-79, E-80, E-81, E-82, E-83, E-84
- Rule: review-finding
- Key: review-finding|spec-driven|skills/test-benchmark/SKILL.md
- Change: E1 checks `skills/test-benchmark/SKILL.md` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-74
- Rule: hard-stop
- Key: hard-stop|cadence|R5|retries
- Change: R5 recorded a `retries` hard stop: r# closure fails. ledger row feat-local-#-csv-export-f# has check path which does not. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: SKILL.md
- Status: candidate
- Evidence: E-10
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked record each finding of your
- Change: The hooks refused 1 times with `blocked record each finding of your`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: SKILL.md
- Status: candidate
- Evidence: E-58
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 1 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-9 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-10 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-s/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-s/scripts/plan_wave.py" done --stage test-benchmar… |
| E-16 | gate | orchestrator | FAIL plan-review-round: round 1 has 8 must-fix rows |
| E-20 | gate | orchestrator | FAIL entry-invariant |
| E-21 | gate | orchestrator | FAIL entry-invariant |
| E-22 | gate | orchestrator | FAIL entry-invariant |
| E-37 | finding | pr-review-local | Reproduced at ba8b805: a stored amount_cents of -5 prints 2026-10-01,food,-1.95 (exit 0) and a stored 12.5 prints 0.12 (exit 0). format_amount uses divmod, so negative cents print wrong, and Ledger.load int() truncates a float. Expected: the right amount or a clean error line. Output of: python3 /tmp/claude-0/-tmp-claude-0--home-user-412420db-14a2-5603-8fea-cbe5692ee926-scratchpad-e2e-s2-budgetcl… |
| E-38 | finding | pr-review-local | Reproduced at ba8b805: a note with a lone surrogate (\ud800) makes export raise UnicodeEncodeError on stdout (traceback, exit 1). With --out, the same error leaves the file truncated to the 27-byte header and exits 1 with a traceback, because only OSError is caught in cli.py:55-58. Expected: error line and exit 2, no traceback, no partial file. Output of: python3 /tmp/claude-0/-tmp-claude-0--home… |
| E-39 | finding | pr-review-local | Reproduced at ba8b805: a ledger file that is not JSON, or a row with no amount_cents, makes export exit 1 with a traceback (ledger.py:38-39, ledger.expenses is outside the try in cli.py). tests/test_cli_export.py:93 pins pytest.raises(ValueError) for the corrupt-ledger case, so the suite treats the traceback as expected. Expected: error line and exit 2, --out file kept. Output of: python3 /tmp/cl… |
| E-40 | finding | pr-review-local | Reproduced at ba8b805: a stored amount_cents of -5 prints 2026-10-01,food,-1.95 (exit 0) and a stored 12.5 prints 0.12 (exit 0). format_amount uses divmod, so negative cents print wrong, and Ledger.load int() truncates a float. Expected: the right amount or a clean error line. Output of: python3 /tmp/claude-0/-tmp-claude-0--home-user-412420db-14a2-5603-8fea-cbe5692ee926-scratchpad-e2e-s2-budgetcl… |
| E-41 | finding | pr-review-local | Reproduced at ba8b805: a note with a lone surrogate (\ud800) makes export raise UnicodeEncodeError on stdout (traceback, exit 1). With --out, the same error leaves the file truncated to the 27-byte header and exits 1 with a traceback, because only OSError is caught in cli.py:55-58. Expected: error line and exit 2, no traceback, no partial file. Output of: python3 /tmp/claude-0/-tmp-claude-0--home… |
| E-42 | finding | pr-review-local | Reproduced at ba8b805: a ledger file that is not JSON, or a row with no amount_cents, makes export exit 1 with a traceback (ledger.py:38-39, ledger.expenses is outside the try in cli.py). tests/test_cli_export.py:93 pins pytest.raises(ValueError) for the corrupt-ledger case, so the suite treats the traceback as expected. Expected: error line and exit 2, --out file kept. Output of: python3 /tmp/cl… |
| E-45 | finding | test-benchmark | Mutant M4: the guard at cli.py:43 `parse_month(args.month) if args.month is not None else None` changed to `if args.month` survives the suite (34 passed, tests/test_cli_export.py and the rest). Effect: `export --month ""` exits 0 and prints every row, where the code exits 2 with an error line. No test passes an empty --month. Kill it with a new row in a parametrize table in tests/test_cli_export.… |
| E-46 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-49 | gate | spec-driven | FAIL cognitive-complexity |
| E-50 | gate | spec-driven | FAIL cognitive-complexity |
| E-56 | finding | pr-review-update | Reproduced at 3841d56: a stored row with category null prints an empty category in export (exit 0): 2026-10-01,,1.00, . A row with category 5 prints 5 (exit 0). The same ledger makes totals exit 1 with a traceback (TypeError in sorted at cli.py:75). _expense_from_row checks amount_cents but not category, so the MF-3 class (a stored row of the wrong type) is not closed for export or totals. Expect… |
| E-57 | finding | test-benchmark | Surviving mutant M1 at src/budgetcli/cli.py:32: the --out guard changed from resolve() equality to plain path equality. Command: python3 -m pytest -q, result 48 passed. With the mutant, export --out link.json (a symlink to the JSON ledger) overwrites the ledger with CSV text, exit 0. At HEAD 3841d56 the same input exits 2 with refusing to write over the ledger file, and the ledger is unchanged. N… |
| E-58 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 14 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-65 | finding | test-benchmark | Surviving mutant N01 at src/budgetcli/ledger.py:36 (added in 6f59185, changed since prior head 3841d56): `if note is not None and type(note) is not str:` changed to `if type(note) is not str:`. Command: python3 -m pytest -q, result 55 passed at 06dd56e. Input: stored row {"day": "2026-10-01", "category": "food", "amount_cents": 100, "note": null}. Expected at HEAD: `date,category,amount,note` hea… |
| E-66 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-72 | gate | orchestrator | FAIL closure |
| E-73 | gate | orchestrator | FAIL closure |
| E-74 | hard-stop | orchestrator | R5 closure fails. Ledger row feat-local-4-csv-export-F04 has check path SCRATCH/r2_f04_check.py, which does not exist. Two peer rewrites did not repair it. Code fix is at HEAD; R1 and R2 pass. |
| E-75 | fix-commit | E1 | fix: MF-4 stored category or note of wrong type is an error line |
| E-76 | fix-commit | E1 | test: MF-4 stored row of wrong type is an error line (red) |
| E-77 | fix-commit | E1 | fix: MF-3 malformed ledger is an error line for export and totals |
| E-78 | fix-commit | E1 | test: MF-3 malformed ledger rows are an error line for export and totals (red) |
| E-79 | fix-commit | E1 | fix: MF-1 non-integer stored amount is an error line |
| E-80 | fix-commit | E1 | test: MF-1 non-integer stored amount is an error line (red) |
| E-81 | fix-commit | E1 | fix: MF-2 note that does not encode is an error line |
| E-82 | fix-commit | E1 | test: F03 MF-3 corrupt ledger is an error line, not a traceback (red) |
| E-83 | fix-commit | E1 | test: MF-2 note that does not encode is an error line (red) |
| E-84 | fix-commit | E1 | fix: F02 negative amount prints a sign |
