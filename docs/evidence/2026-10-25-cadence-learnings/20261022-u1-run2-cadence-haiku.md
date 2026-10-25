RUN_BY_COMMAND: run-learnings
Run: 20261022-u1-run2-cadence-haiku
Cadence: a3eb0aaf812e1f0be3e12aba48894ffc36983f5b
Packet sha256: a700b79e1f874efa1e1f79e1eb34ce9f5f8582d1a0de12cfb6ed8a01c4b3fa67

# Learnings: 20261022-u1-run2-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 11
- finding: 19
- fix-commit: 19
- gate: 37
- stop-point: 1
- stop-refusal: 1

## Proposals

### L-1
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-32, E-33
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 2 times in spec-driven: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; types union-attr item none of io bytes.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-25
- Rule: late-gate
- Key: late-gate|spec-driven|pr-review-local-gate|pr-review-local no join
- Change: E1's phase gate runs the `pr-review-local-gate` measure `pr-review-local no join` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-19, E-37, E-53, E-60
- Rule: redispatch
- Key: redispatch|test-benchmark|R2
- Change: R2 was dispatched 4 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/pr-review-update.md
- Status: candidate
- Evidence: E-36, E-52, E-61
- Rule: redispatch
- Key: redispatch|pr-review-update|R4
- Change: R4 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-update@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=pr-review-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-22, E-23, E-24, E-40, E-70, E-71, E-72, E-73, E-74, E-75, E-76, E-77, E-78, E-79, E-80, E-81, E-82, E-83, E-84, E-85, E-86, E-87, E-88
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 4 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-26, E-27, E-41, E-42, E-46, E-47, E-48, E-55, E-56, E-57, E-70, E-71, E-72, E-73, E-74, E-75, E-76, E-77, E-78, E-79, E-80, E-81, E-82, E-83, E-84, E-85, E-86, E-87, E-88
- Rule: review-finding
- Key: review-finding|spec-driven|core:test-benchmark-pr
- Change: E1 checks `core:test-benchmark-pr` before E4: the review found 10 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-28, E-29, E-43, E-44, E-45, E-70, E-71, E-72, E-73, E-74, E-75, E-76, E-77, E-78, E-79, E-80, E-81, E-82, E-83, E-84, E-85, E-86, E-87, E-88
- Rule: review-finding
- Key: review-finding|spec-driven|ADR-0027
- Change: E1 checks `ADR-0027` before E4: the review found 5 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: SKILL.md
- Status: candidate
- Evidence: E-16
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 1 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-16 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-19 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-22 | finding | R1 | Stored amount_cents is not validated. amount_cents -5 exports as -1.95 (export.py _amount divmod on a negative value). amount_cents 12.5 is truncated by int() to 12 and exports as 0.12. Repro: scratchpad review-r1/repro.sh R1 and the float probe; MF-1 check fails at HEAD. |
| E-23 | finding | R1 | A stored note with a lone surrogate (JSON \ud800) makes render_csv raise UnicodeEncodeError outside the error handling of cmd_export. Exit 1 with a Traceback. Repro: review-r1/repro.sh R2. |
| E-24 | finding | R1 | A stored row without amount_cents (or category, day, note-less rows are fine) raises KeyError in Ledger.load, which export_rows does not catch. Exit 1 with a Traceback. Repro: review-r1/repro.sh R4. |
| E-25 | gate | R1 | FAIL pr-review-local-gate |
| E-26 | finding | R2 | Surviving mutant M01: key=lambda e: (e.day, e.category) passes python3 -m pytest -q (38 passed). Same-day fixture pair in tests/conftest.py LEDGER_ROWS is already alphabetical by category, so file order and category order agree. |
| E-27 | finding | R2 | Stored amount_cents -5 exports as -1.95 (expected -0.05). divmod(-5, 100) = (-1, 95). No negative-amount test in tests/test_export.py. |
| E-28 | finding | R2 | Stored note with lone surrogate makes budgetcli export exit 1 with UnicodeEncodeError traceback (expected error line, exit 2, or stated replacement). Not covered by tests. |
| E-29 | finding | R2 | budgetcli --file big.json export \| head -0 prints BrokenPipeError traceback and exits 1. Expected no traceback. Not covered by tests. |
| E-32 | gate | spec-driven | FAIL cognitive-complexity |
| E-33 | gate | spec-driven | FAIL cognitive-complexity |
| E-36 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-37 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-40 | finding | R4 | A stored row without amount_cents (or category, day, note-less rows are fine) raises KeyError in Ledger.load, which export_rows does not catch. Exit 1 with a Traceback. Repro: review-r1/repro.sh R4. |
| E-41 | finding | R4 | Surviving mutant M01: key=lambda e: (e.day, e.category) passes python3 -m pytest -q (38 passed). Same-day fixture pair in tests/conftest.py LEDGER_ROWS is already alphabetical by category, so file order and category order agree. |
| E-42 | finding | R4 | Stored amount_cents -5 exports as -1.95 (expected -0.05). divmod(-5, 100) = (-1, 95). No negative-amount test in tests/test_export.py. |
| E-43 | finding | R4 | Stored note with lone surrogate makes budgetcli export exit 1 with UnicodeEncodeError traceback (expected error line, exit 2, or stated replacement). Not covered by tests. |
| E-44 | finding | R4 | budgetcli --file big.json export \| head -0 prints BrokenPipeError traceback and exits 1. Expected no traceback. Not covered by tests. |
| E-45 | finding | R4 | A stored file whose top-level JSON is a scalar or null (5, null) makes budgetcli export and totals exit 1 with a TypeError Traceback. enumerate(rows) in Ledger.load is outside the per-row try. Repro: review-r4/mf_check.py MF-4 fails at HEAD. |
| E-46 | finding | R2 | Surviving mutant N07: except (TypeError, ValueError) changed to except ValueError (src/budgetcli/ledger.py line 41). Command: python3 -m pytest -q, 53 passed on the mutant copy. Input: a stored ledger file [1] (a non-object row). HEAD exits 2 with error: ledger row 1: int object is not subscriptable. The mutant exits 1 with a TypeError traceback. No test row holds a non-object row. |
| E-47 | finding | R2 | Surviving mutant N08: row.get("note", "") changed to row["note"] (src/budgetcli/ledger.py line 38). Command: python3 -m pytest -q, 53 passed on the mutant copy. Input: a stored row without a note key, [{"day":"2026-10-01","category":"food","amount_cents":500}]. HEAD exports it with exit 0 and an empty note (the note is optional). The mutant refuses it. No test row omits the note key, so the defau… |
| E-48 | finding | R2 | Surviving mutant N12: return 1 changed to return 0 in the BrokenPipeError handler (src/budgetcli/cli.py). Command: python3 -m pytest -q, 53 passed on the mutant copy. test_export_into_a_closed_pipe_prints_no_traceback asserts only that Traceback is absent from stderr; it does not check the exit status that the fix sets. |
| E-52 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-53 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-55 | finding | R2 | Surviving mutant N08: row.get("note", "") changed to row["note"] (src/budgetcli/ledger.py line 38). Command: python3 -m pytest -q, 53 passed on the mutant copy. Input: a stored row without a note key, [{"day":"2026-10-01","category":"food","amount_cents":500}]. HEAD exports it with exit 0 and an empty note (the note is optional). The mutant refuses it. No test row omits the note key, so the defau… |
| E-56 | finding | R2 | Surviving mutant N12: return 1 changed to return 0 in the BrokenPipeError handler (src/budgetcli/cli.py). Command: python3 -m pytest -q, 53 passed on the mutant copy. test_export_into_a_closed_pipe_prints_no_traceback asserts only that Traceback is absent from stderr; it does not check the exit status that the fix sets. |
| E-57 | finding | R2 | Surviving mutant E: src/budgetcli/ledger.py line 37 guard changed from `if not isinstance(rows, list):` to `if not isinstance(rows, (list, dict)):`. Command: python3 -m pytest -q gives 62 passed on the mutant copy (not killed). Input: a ledger file containing {} (top-level object). HEAD exits 2 with error: ledger must be a JSON list of rows. The mutant exits 0 and prints the header alone. tests/t… |
| E-60 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-61 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-70 | fix-commit | E1 | test: feat-local-4-csv-export-F08 a ledger whose top level is an object is refused (pins behavior; fails on the dict-guard mutant) |
| E-71 | fix-commit | E1 | test: feat-local-4-csv-export-F07 a closed pipe exits with the status the handler sets (pins behavior; fails on the return-0 mutant) |
| E-72 | fix-commit | E1 | test: feat-local-4-csv-export-F06 a stored row without a note key exports an empty note (pins behavior; fails on the row["note"] mutant) |
| E-73 | fix-commit | E1 | test: feat-local-4-csv-export-F05 a stored row that is not an object is refused (pins behavior; fails on the except-ValueError mutant) |
| E-74 | fix-commit | E1 | fix: feat-local-4-csv-export-MF-4 a ledger whose top level is not a list is refused |
| E-75 | fix-commit | E1 | test: feat-local-4-csv-export-MF-4 a ledger whose top level is not a list is refused (red) |
| E-76 | fix-commit | E1 | test: feat-local-4-csv-export MF-1 MF-2 MF-3 F04 share one stored-row fixture and one refusal test |
| E-77 | fix-commit | E1 | test: feat-local-4-csv-export-F01 same-day rows keep file order (pins behavior; fails on the category-sort mutant) |
| E-78 | fix-commit | E1 | fix: feat-local-4-csv-export-F04 a closed pipe ends the command without a traceback |
| E-79 | fix-commit | E1 | test: feat-local-4-csv-export-F04 export into a closed pipe prints no traceback (red) |
| E-80 | fix-commit | E1 | fix: feat-local-4-csv-export-MF-2 a note that UTF-8 cannot encode is refused |
| E-81 | fix-commit | E1 | test: feat-local-4-csv-export-MF-2 a note that UTF-8 cannot encode is refused (red) |
| E-82 | fix-commit | E1 | fix: feat-local-4-csv-export-MF-3 a stored row without an amount is refused |
| E-83 | fix-commit | E1 | test: feat-local-4-csv-export-MF-3 a stored row without an amount is refused (red) |
| E-84 | fix-commit | E1 | fix: feat-local-4-csv-export-MF-1 a stored amount that is not whole cents is refused |
| E-85 | fix-commit | E1 | test: feat-local-4-csv-export-MF-1 totals refuses a stored fractional amount (red) |
| E-86 | fix-commit | E1 | test: feat-local-4-csv-export-MF-1 a stored amount that is not whole cents is refused (red) |
| E-87 | fix-commit | E1 | fix: feat-local-4-csv-export-F02 negative amounts keep their sign |
| E-88 | fix-commit | E1 | test: feat-local-4-csv-export-F02 negative amounts print with a sign (red) |
