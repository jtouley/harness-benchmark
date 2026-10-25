RUN_BY_COMMAND: run-learnings
Run: 20261022-t1-run1-cadence-haiku
Cadence: e51cde2a59d4a02c881de00c5629433face342f2
Packet sha256: 588a16bb9d753be5dccda194dba274fb847a27f1804bdbd537ab655b61d64e8c

# Learnings: 20261022-t1-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 23
- finding: 10
- fix-commit: 8
- free-form-dispatch: 1
- gate: 65
- stop-point: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-10, E-17
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-52, E-61, E-67
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|acceptance
- Change: Before the return, run the `acceptance` gate once and fix every class it names in one pass. In this run it failed 3 times in spec-driven: acceptance ac-# has an open defect the.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-53, E-54, E-66, E-78
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 4 times in spec-driven: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; fix step run r# without --check to.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: SKILL.md
- Status: candidate
- Evidence: E-68, E-73, E-75
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: feat-local-#-csv-# must-fix status open not terminal; feat-local-#-csv-export-f# must-fix status fixed not terminal. verify; acceptance ac-# has an open defect the.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-49, E-57
- Rule: late-gate
- Key: late-gate|spec-driven|acceptance|acceptance ac-# has
- Change: E1's phase gate runs the `acceptance` measure `acceptance ac-# has` before E4, so the review phase does not find it first. It failed 2 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-51
- Rule: late-gate
- Key: late-gate|spec-driven|pr-review-local-gate|pr-review-local no join
- Change: E1's phase gate runs the `pr-review-local-gate` measure `pr-review-local no join` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-58, E-58, E-58
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|% duplicated
- Change: E1's phase gate runs the `cognitive-complexity` measure `% duplicated` before E4, so the review phase does not find it first. It failed 3 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-58
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|duplication.max_percent is
- Change: E1's phase gate runs the `cognitive-complexity` measure `duplication.max_percent is` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-58
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|fix step delegate
- Change: E1's phase gate runs the `cognitive-complexity` measure `fix step delegate` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-18, E-70
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: commands/commit-push-pr.md
- Status: candidate
- Evidence: E-35, E-36
- Rule: redispatch
- Key: redispatch|commit-push-pr|E4
- Change: E4 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=commit-push-pr@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=commit-push-pr@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-39, E-56, E-63, E-80, E-88, E-93
- Rule: redispatch
- Key: redispatch|test-benchmark|R2
- Change: R2 was dispatched 6 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-13
- Target: commands/pr-review-update.md
- Status: candidate
- Evidence: E-55, E-62, E-79, E-87, E-92
- Rule: redispatch
- Key: redispatch|pr-review-update|R4
- Change: R4 was dispatched 5 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-update@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=pr-review-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-14
- Target: SKILL.md
- Status: candidate
- Evidence: E-91
- Rule: free-form-dispatch
- Key: free-form-dispatch|cadence|free-form
- Change: The orchestrator sent 1 free-form subagent prompts. Dispatch each block and the fix round only from its packet (`/<command>` with the Block line).
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-15
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-42, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|ADR-0027 (data inputs); skills/test-benchmark/SKILL.md
- Change: E1 checks `ADR-0027 (data inputs); skills/test-benchmark/SKILL.md` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-16
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-43, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|ADR-0027 (bad row in a stored file); skills/test-benchmark/SKILL.md
- Change: E1 checks `ADR-0027 (bad row in a stored file); skills/test-benchmark/SKILL.md` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-17
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-44, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|ADR-0027 (closed output pipe); skills/test-benchmark/SKILL.md
- Change: E1 checks `ADR-0027 (closed output pipe); skills/test-benchmark/SKILL.md` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-18
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-47, E-48, E-59, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|ADR-0027
- Change: E1 checks `ADR-0027` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-19
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-50, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-20
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-64, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|ADR-0027 (data inputs and closed output); skills/test-benchmark/SKILL.md
- Change: E1 checks `ADR-0027 (data inputs and closed output); skills/test-benchmark/SKILL.md` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-21
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-83, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|ADR-0027 (output path is an input); skills/test-benchmark/SKILL.md
- Change: E1 checks `ADR-0027 (output path is an input); skills/test-benchmark/SKILL.md` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-22
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-84, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension; skills/test-benchmark/SKILL.md
- Change: E1 checks `core:dry-extension; skills/test-benchmark/SKILL.md` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-23
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-68, E-73, E-75
- Rule: open-at-close
- Key: open-at-close|pr-review-local|open-must-fix
- Change: The fix round returns only after `ledger_verify.py` marks each fixed must-fix item verified; R5 found open must-fix items 3 times.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-10 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-17 | gate | orchestrator | FAIL plan-review-round: round 1 has 10 must-fix rows |
| E-18 | dispatch | P4 | /plan-update dispatched as P4 |
| E-35 | dispatch | E4 | /commit-push-pr dispatched as E4 |
| E-36 | dispatch | E4 | /commit-push-pr dispatched as E4 |
| E-39 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-42 | finding | R2 | Stored note with a lone surrogate (ledger.json note "a\ud800b") -> `budgetcli export` exits 1 with UnicodeEncodeError: 'utf-8' codec can't encode character '\ud800'; same with --out (write_bytes(text.encode)). No test in tests/test_export.py covers it. |
| E-43 | finding | R2 | Stored rows with a bad value give tracebacks, exit 1, and no error line: corrupt JSON (`{bad`) -> JSONDecodeError; row without "day" -> KeyError: 'day'; amount_cents NaN -> ValueError: cannot convert float NaN to integer. No test covers any of these. |
| E-44 | finding | R2 | `python3 -m budgetcli.cli --file ok.json export \| head -0` -> BrokenPipeError: [Errno 32] Broken pipe, exit 1. No test covers a closed stdout. |
| E-47 | finding | R1 | budgetcli add food 1.00 --note $'\xff' exits 0 and stores the note as the lone surrogate \udcff. export --month 2026-10 then exits 1 with UnicodeEncodeError in _export (text.encode utf-8). One valid stored row makes the whole month unprintable. Repro: .context/prs/repro/repro_MF-1.py prints DEFECT at HEAD 34423ac. |
| E-48 | finding | R1 | export on a damaged stored ledger exits 1 with a traceback for: a row missing amount_cents (KeyError), a row with amount_cents as text (ValueError), amount_cents NaN (ValueError), and corrupt JSON (JSONDecodeError). The request requires an error line and no traceback for a bad input. Repro: .context/prs/repro/repro_MF-2.py prints DEFECT at HEAD 34423ac. |
| E-49 | gate | R1 | FAIL acceptance |
| E-50 | finding | R1 | The AC-4 check asserts only that a standalone 2 appears in stdout. Code that prints the constant 2 rows written for every export passes the check, so the row count of the claim is not proven. Defect recorded with acceptance.py defect --id AC-4. Repro: .context/prs/repro/repro_AC-4.py prints DEFECT at HEAD 34423ac. The plan peer must change the check with /plan-update --acceptance AC-4. |
| E-51 | gate | R1 | FAIL pr-review-local-gate |
| E-52 | gate | spec-driven | FAIL acceptance |
| E-53 | gate | spec-driven | FAIL cognitive-complexity |
| E-54 | gate | spec-driven | FAIL cognitive-complexity |
| E-55 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-56 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-57 | gate | R4 | FAIL acceptance |
| E-58 | gate | R4 | FAIL cognitive-complexity |
| E-59 | finding | R4 | export --out to a hard link of the ledger overwrites the ledger with CSV text. Repro at HEAD a9601dc: ledger.json and hl.csv share one inode; export --month 2026-10 --out hl.csv exits 0 and prints 1 rows written; ledger.json then holds the CSV header and row. _export compares paths with resolve(), which does not compare inodes, so the guard at line 28 misses it. The fix commits did not touch this… |
| E-61 | gate | spec-driven | FAIL acceptance |
| E-62 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-63 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-64 | finding | R2 | The closed-stdout test asserts only that stderr has no Traceback and that the exit code is 1. Mutant src/budgetcli/cli.py:35 removes the line `print("error: standard output is closed", file=sys.stderr)` (leaving `return 1`) and survives `python3 -m pytest -q tests` (29 passed). Run as `budgetcli --file ok.json export >&-`, the real output is `error: standard output is closed`, exit 1. The mutant … |
| E-66 | gate | spec-driven | FAIL cognitive-complexity |
| E-67 | gate | spec-driven | FAIL acceptance |
| E-68 | gate | orchestrator | FAIL closure |
| E-70 | dispatch | P4 | /plan-update dispatched as P4 |
| E-73 | gate | orchestrator | FAIL closure |
| E-75 | gate | orchestrator | FAIL closure |
| E-78 | gate | spec-driven | FAIL cognitive-complexity |
| E-79 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-80 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-83 | finding | R2 | Mutant src/budgetcli/cli.py:46 `args.out.resolve() == args.file.resolve()` -> `args.out == args.file` (samefile arm kept) survives python3 -m pytest -q tests (30 passed). The symlink row is now caught by the samefile arm, so it does not kill this mutant. Input with no ledger present: `--file x/../nope.json export --out nope.json` (x exists). Current code: error --out must not be the ledger file, … |
| E-84 | finding | R2 | The F10 fix commit 84e79b0 added test_export_to_a_closed_stdout_names_the_error_line as a copy of test_export_to_a_closed_stdout_prints_no_traceback: the same make_ledger call, env dict, command string and subprocess.run call, and the same exit check. Only the stderr assertion differs. The fix named the existing test for the assertion, and the copy duplicates its setup. Fix: add the startswith as… |
| E-87 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-88 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-91 | free-form-dispatch | orchestrator | Ignore .context in branch gitignore |
| E-92 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-93 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-101 | fix-commit | E1 | fix: F09 export to a closed stdout exits 1 with an error line |
| E-102 | fix-commit | E1 | fix: MF-4 export refuses a hard link of the ledger |
| E-103 | fix-commit | E1 | test: MF-4 export refuses a hard link of the ledger (red) |
| E-104 | fix-commit | E1 | fix: F03 export to a closed pipe exits 1 without a traceback |
| E-105 | fix-commit | E1 | fix: MF-2 F02 damaged stored ledger gives an error line, not a traceback |
| E-106 | fix-commit | E1 | test: MF-2 F02 export refuses a damaged stored row with an error line (red) |
| E-107 | fix-commit | E1 | fix: MF-1 F01 export prints an error line for a note that is not UTF-8 |
| E-108 | fix-commit | E1 | test: MF-1 F01 export refuses a note that is not UTF-8 (red) |
