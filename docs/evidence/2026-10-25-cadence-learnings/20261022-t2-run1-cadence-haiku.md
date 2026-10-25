RUN_BY_COMMAND: run-learnings
Run: 20261022-t2-run1-cadence-haiku
Cadence: e51cde2a59d4a02c881de00c5629433face342f2
Packet sha256: 79e1737aec7058e9d6cf4878e13b91fad212c47b54e5ecc200a56df17d5291e8

# Learnings: 20261022-t2-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 14
- fix-commit: 21
- gate: 68
- stop-point: 1
- stop-refusal: 4

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-9, E-13, E-15
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # waits on adversarial-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-52, E-62, E-64, E-66
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|acceptance
- Change: Before the return, run the `acceptance` gate once and fix every class it names in one pass. In this run it failed 4 times in spec-driven: acceptance ac-# has an open defect the.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-53, E-61
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 2 times in spec-driven: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; types union-attr item none of io bytes.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-41, E-42, E-43, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-44, E-45, E-46, E-47, E-48, E-57, E-58, E-67, E-68, E-77, E-78, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor:R2
- Change: E1 checks `review-rigor:R2` before E4: the review found 11 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-8, E-55, E-59
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 3 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: SKILL.md
- Status: candidate
- Evidence: E-70
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in execution. progress
- Change: The hooks refused 1 times with `blocked early stop in execution. progress`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-8 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 3 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-9 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-13 | gate | orchestrator | FAIL plan-review-round: round 1 waits on adversarial-review |
| E-15 | gate | orchestrator | FAIL plan-review-round: round 1 has 14 must-fix rows |
| E-41 | finding | pr-review-local | budgetcli export --month 2026-10 \| head -0 exits 1 with BrokenPipeError traceback (run_export writes sys.stdout.buffer without handling a closed pipe). Request: a closed output pipe is an input class of ADR-0027. |
| E-42 | finding | pr-review-local | budgetcli add food 5 --note $'caf\xe9' then export --month 2026-10 exits 1 with UnicodeEncodeError traceback. render_csv encodes utf-8 with no error handler, so a note that does not encode crashes export instead of giving an error line. |
| E-43 | finding | pr-review-local | A stored row with a missing category, a NaN amount_cents or an impossible day (2026-02-30) makes export exit 1 with KeyError, ValueError traceback. The export has no error line for a bad ledger, unlike the wrong month of AC-5. Load is shared with totals, so the fix may sit in load. |
| E-44 | finding | test-benchmark | Input: add food 5.00 --day 2026-10-03 --note with the byte 0xff (surrogateescape). add exits 0 and stores the lone surrogate. Then export --month 2026-10 exits 1 with UnicodeEncodeError (surrogates not allowed) at export.py:28. No test covers a lone surrogate. Expected: one line on stderr and exit 2, never a traceback. |
| E-45 | finding | test-benchmark | Input: export \| head -0 on a two-row ledger. The reader closes the pipe and export exits 1 with BrokenPipeError traceback. No test covers a closed output pipe. Expected: no traceback on a closed stdout. |
| E-46 | finding | test-benchmark | Corrupt stored ledger: a row missing amount_cents gives KeyError; a non-JSON file gives JSONDecodeError; amount_cents NaN gives ValueError. Each exits 1 with a traceback from export. No test covers a bad stored row. Expected: one error line on stderr and exit 2, never a traceback. |
| E-47 | finding | test-benchmark | Surviving mutant: run_export calls ledger.export_rows(None) instead of export_rows(month). Killed by: python3 -m pytest tests/test_export.py -q (42 passed, mutant survives). test_export_month_prints_csv_to_stdout uses backdated_ledger, whose three rows are all in 2026-10, so --month filters nothing. Fix: add a row outside October to a CLI month test and assert it is absent. |
| E-48 | finding | test-benchmark | Surviving mutant: export_rows filters with e.day.month == month[1] (year ignored). Killed by: python3 -m pytest tests/test_export.py -q (42 passed, mutant survives). test_export_month_matches_year_and_month_exactly has only 2026 rows, so no row from another year in the same month. Fix: add a 2025-10 row and assert it is excluded. |
| E-52 | gate | spec-driven | FAIL acceptance |
| E-53 | gate | spec-driven | FAIL cognitive-complexity |
| E-55 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 8 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-57 | finding | test-benchmark | Input: stored row with amount_cents 1.5 (a float). int() truncates it silently: export exits 0 and writes 2026-10-03,food,0.01 (wrong output, expected a one-line error and exit 2). Mutant ledger.py:41 int(r["amount_cents"]) -> int(float(r["amount_cents"])) survives python3 -m pytest tests/test_export.py -q (47 passed), so no test pins the amount type. Real run, PYTHONPATH=copy of src. |
| E-58 | finding | test-benchmark | Input: stored row with amount_cents 1e400 (JSON number that overflows to infinity). int(inf) raises OverflowError, which run_export does not catch (it catches KeyError, TypeError, ValueError). Export exits 1 with an OverflowError traceback: cannot convert float infinity to integer. Expected: one error: line and exit 2, as for NaN. No test covers it. Real run. |
| E-59 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-61 | gate | spec-driven | FAIL cognitive-complexity |
| E-62 | gate | spec-driven | FAIL acceptance |
| E-64 | gate | spec-driven | FAIL acceptance |
| E-66 | gate | spec-driven | FAIL acceptance |
| E-67 | finding | test-benchmark | Input: stored rows with amount_cents "5" (a string) and true (a boolean). The guard at ledger.py:44 checks only float, so int() coerces both. Real runs: export of "5" exits 0 and writes 2026-10-03,food,0.05; export of true exits 0 and writes 2026-10-03,food,0.01. Expected: one error: line on stderr and exit 2, as for amount_cents null in the bad-row table. Mutant: none of the suite fails when the… |
| E-68 | finding | test-benchmark | Input: stored row with amount_cents 1e300 (a whole float, so the guard at ledger.py:44 accepts it). export exits 0 and prints a 300-digit number ending in .60: the binary value of the float, not the amount the author wrote. A float above 2**53 cannot hold every cent, so the output is wrong by the F06 rule (silent coercion of a float stored amount). Expected: one error: line on stderr and exit 2, … |
| E-70 | stop-refusal | orchestrator | BLOCKED early stop in execution. Progress unknown (run feef0875-9adf-471c-9105-74b53c5a5b56): a gate timed out or could not run. Continue paceline: next E1 (implement) via `/spec-driven` |
| E-77 | finding | test-benchmark | Input: stored row with amount_cents 1152921504606846976 (2**60, a JSON int, so type(amount) is int passes the guard at ledger.py:44). Real run at HEAD c573657: export exits 0 and prints 11529215046068469.76 (exact). totals exits 0 and prints 11529215046068470.00 (cli.py:49 uses cents / 100 in float, which rounds). The two commands disagree on the same stored value. The F10 rule applies: above 2**… |
| E-78 | finding | test-benchmark | Mutants run in mktemp copies of src, tests and pyproject.toml, outside the worktree, deleted after each run. Baseline at HEAD c573657: python3 -m pytest tests/test_export.py tests/test_ledger.py -q gives 57 passed. Survivors: (a) bound changed to abs(amount) < 2**53: 57 passed; no row pins a float of exactly 9007199254740992.0 (accepted by the rule). (b) bound changed to abs(amount) <= 2**54: 57 … |
| E-88 | fix-commit | E1 | test: feat-local-4-csv-export-F12 pin both sides of the 2**53 bound |
| E-89 | fix-commit | E1 | fix: feat-local-4-csv-export-F11 a stored int above 2**53 is an error, as a float is |
| E-90 | fix-commit | E1 | test: feat-local-4-csv-export-F11 stored int above 2**53 is an error (red) |
| E-91 | fix-commit | E1 | fix: feat-local-4-csv-export-F10 a stored float above 2**53 is an error, not a rounded value |
| E-92 | fix-commit | E1 | test: feat-local-4-csv-export-F10 stored amount 1e300 is an error (red) |
| E-93 | fix-commit | E1 | fix: feat-local-4-csv-export-F09 a stored amount must be a number of cents, not a string or boolean |
| E-94 | fix-commit | E1 | test: feat-local-4-csv-export-F09 stored amount "5" and true are errors (red) |
| E-95 | fix-commit | E1 | fix: feat-local-4-csv-export-F06 totals reports a fractional stored amount as an error line |
| E-96 | fix-commit | E1 | test: feat-local-4-csv-export-F06 totals on a fractional stored amount is an error line (red) |
| E-97 | fix-commit | E1 | refactor: feat-local-4-csv-export-F08 share the ledger-path refusal test for a hard link |
| E-98 | fix-commit | E1 | fix: feat-local-4-csv-export-F08 export --out refuses a hard link to the ledger |
| E-99 | fix-commit | E1 | test: feat-local-4-csv-export-F08 export --out refuses a hard link to the ledger (red) |
| E-100 | fix-commit | E1 | fix: feat-local-4-csv-export-F06 F07 a stored amount must be a whole number of cents |
| E-101 | fix-commit | E1 | test: feat-local-4-csv-export-F06 stored amount 1.5 is an error, not truncated (red) |
| E-102 | fix-commit | E1 | test: feat-local-4-csv-export-F07 stored amount 1e400 is an error (red) |
| E-103 | fix-commit | E1 | fix: F03 MF-3 export reports a bad stored row as an error |
| E-104 | fix-commit | E1 | test: F03 MF-3 export of a bad stored row is an error (red) |
| E-105 | fix-commit | E1 | fix: F01 MF-2 export reports a note that is not UTF-8 as an error |
| E-106 | fix-commit | E1 | test: F01 MF-2 export of a lone surrogate note is an error (red) |
| E-107 | fix-commit | E1 | fix: F02 MF-1 export ignores a closed output pipe |
| E-108 | fix-commit | E1 | test: F02 MF-1 export to a closed pipe exits without traceback (red) |
