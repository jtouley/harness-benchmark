RUN_BY_COMMAND: run-learnings
Run: 20261022-z2-run1-cadence-haiku
Cadence: 99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27
Packet sha256: 2e926b40ce7653ab23170ff0ff45a777a6daed868dc8d6d1de092a8d224ebc4e

# Learnings: 20261022-z2-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 28
- finding: 23
- fix-commit: 23
- gate: 86
- hard-stop: 1
- stop-refusal: 2

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-8, E-15, E-17
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix; fail plan-review-round the plan has no.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-56, E-138
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: feat-local-#-csv-export-f# must-fix status fixed not terminal. verify; feat-local-#-csv-# must-fix status open not terminal.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-65, E-79, E-81
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|acceptance
- Change: Before the return, run the `acceptance` gate once and fix every class it names in one pass. In this run it failed 3 times in spec-driven: acceptance ac-# has an open defect the.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: SKILL.md
- Status: candidate
- Evidence: E-82, E-85, E-86, E-87, E-134
- Rule: gate-repeat
- Key: gate-repeat|cadence|acceptance
- Change: Before the return, run the `acceptance` gate once and fix every class it names in one pass. In this run it failed 5 times in orchestrator: acceptance changed after p#. a change to; acceptance ac-# has an open defect. after; acceptance ac-# has an open defect the.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-46
- Rule: late-gate
- Key: late-gate|spec-driven|pr-review-local-gate|pr-review-local no join
- Change: E1's phase gate runs the `pr-review-local-gate` measure `pr-review-local no join` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-128
- Rule: late-gate
- Key: late-gate|spec-driven|test-benchmark-gate-code|test-benchmark-pr no join
- Change: E1's phase gate runs the `test-benchmark-gate-code` measure `test-benchmark-pr no join` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-16, E-18, E-57, E-61, E-67, E-83, E-89, E-132
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 8 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-40, E-115
- Rule: redispatch
- Key: redispatch|pr-review-local|R1
- Change: R1 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-41, E-73, E-93, E-105, E-116, E-126
- Rule: redispatch
- Key: redispatch|test-benchmark|R2
- Change: R2 was dispatched 6 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: commands/pr-review-update.md
- Status: candidate
- Evidence: E-72, E-92, E-104, E-125, E-139
- Rule: redispatch
- Key: redispatch|pr-review-update|R4
- Change: R4 was dispatched 5 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-update@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=pr-review-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-43, E-44, E-48, E-141, E-142, E-143, E-144, E-145, E-146, E-147, E-148, E-149, E-150, E-151, E-152, E-153, E-154, E-155, E-156, E-157, E-158, E-159, E-160, E-161, E-162, E-163
- Rule: review-finding
- Key: review-finding|spec-driven|unspecified
- Change: E1 checks `unspecified` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-45, E-47, E-141, E-142, E-143, E-144, E-145, E-146, E-147, E-148, E-149, E-150, E-151, E-152, E-153, E-154, E-155, E-156, E-157, E-158, E-159, E-160, E-161, E-162, E-163
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-13
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-49, E-50, E-51, E-76, E-96, E-97, E-98, E-107, E-108, E-109, E-110, E-117, E-118, E-141, E-142, E-143, E-144, E-145, E-146, E-147, E-148, E-149, E-150, E-151, E-152, E-153, E-154, E-155, E-156, E-157, E-158, E-159, E-160, E-161, E-162, E-163
- Rule: review-finding
- Key: review-finding|spec-driven|core:test-benchmark-pr
- Change: E1 checks `core:test-benchmark-pr` before E4: the review found 13 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-14
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-52, E-75, E-99, E-121, E-122, E-141, E-142, E-143, E-144, E-145, E-146, E-147, E-148, E-149, E-150, E-151, E-152, E-153, E-154, E-155, E-156, E-157, E-158, E-159, E-160, E-161, E-162, E-163
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 5 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-15
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-56, E-138
- Rule: open-at-close
- Key: open-at-close|pr-review-local|open-must-fix
- Change: The fix round returns only after `ledger_verify.py` marks each fixed must-fix item verified; R5 found open must-fix items 2 times.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-16
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-140
- Rule: hard-stop
- Key: hard-stop|pr-review-local|R1|retries
- Change: R1 recorded a `retries` hard stop: r# must-fix mf-# ac-# check stays open at head #. the ac. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-17
- Target: SKILL.md
- Status: candidate
- Evidence: E-63, E-88
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 2 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-8 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-15 | gate | orchestrator | FAIL plan-review-round: round 1 has 11 must-fix rows |
| E-16 | dispatch | P4 | /plan-update dispatched as P4 |
| E-17 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review e60472ff68a6)` row for feat-local-4-csv-export-F01 of round-1.md. Send /plan-update again |
| E-18 | dispatch | P4 | /plan-update dispatched as P4 |
| E-40 | dispatch | R1 | /pr-review-local dispatched as R1 |
| E-41 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-43 | finding | R2 | check_ac4 matches a standalone 3 anywhere in stdout; wrote 2 rows to /tmp/tmp3ab9xq/october.csv passes |
| E-44 | finding | R2 | main() gets a second branch; the claimed subparser table does not exist; core:dry-extension item 4 forbids a branch for a second case |
| E-45 | finding | R1 | AC-4 regex (?<!\d)3(?!\d) passes a wrong row count when the out path holds a 3. Mutant printing len(rows)-1 passed with TMPDIR containing 3. Review: .context/prs/reviews/PR_REVIEW_1.md, MF-1 |
| E-46 | gate | R1 | FAIL pr-review-local-gate |
| E-47 | finding | R2 | AC-4 regex (?<!\d)3(?!\d) passes a wrong row count when the out path holds a 3. Mutant printing len(rows)-1 passed with TMPDIR containing 3. Review: .context/prs/reviews/PR_REVIEW_1.md, MF-1 |
| E-48 | finding | R2 | plan waits on the user to decide note quoting; plan-review-round forbids person waits; deferral-framework criterion 1 says the run does not ask the user |
| E-49 | finding | R2 | Lone surrogate note: export --out raises UnicodeEncodeError, exit 1, no error line; stdout export of stored \ud800 note also exit 1. Scorecard: .context/benchmarks/feat-local-4-csv-export_code.json |
| E-50 | finding | R2 | Stored row missing category: KeyError traceback, exit 1. amount_cents 1e400: OverflowError traceback, exit 1. Contract: error line and exit 2. Scorecard: .context/benchmarks/feat-local-4-csv-export_code.json |
| E-51 | finding | R2 | Mutant encode(ascii) survives: 19 passed. No export test uses a non-ASCII note. Scorecard: .context/benchmarks/feat-local-4-csv-export_code.json |
| E-52 | finding | R2 | Same 3-line setup written 8 times in one file. helpers_reimplemented unmeasured (no conftest), thin_files pass. Scorecard: .context/benchmarks/feat-local-4-csv-export_code.json |
| E-56 | gate | orchestrator | FAIL closure |
| E-57 | dispatch | P4 | /plan-update dispatched as P4 |
| E-61 | dispatch | P4 | /plan-update dispatched as P4 |
| E-63 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 573 characters; the limit is 300. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-65 | gate | spec-driven | FAIL acceptance |
| E-67 | dispatch | P4 | /plan-update dispatched as P4 |
| E-72 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-73 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-75 | finding | R2 | Three tests write a one-row JSON ledger with the same inline json.dumps([{day, category, amount_cents, note}]) pattern and repeat the capsys.readouterr() and export call. The DRY measure of scripts/test_shape.py does not cover clones inside one file, so the clone is not measured. DRY score 6. Fix: one helper in tests/test_cli_export.py that writes a ledger from a list of rows, used by the three t… |
| E-76 | finding | R2 | Mutant ledger.py line 64 `if cents < 0` changed to `if cents < -1`: python3 -m pytest -q tests in a copy outside the worktree prints 22 passed (survived). The CLI then prints `2026-10-01,food,-1.99,` and exits 0 for a stored amount_cents of -1; the real code prints `error: amount must not be negative` and exits 2. The test table uses -5 and -1250 only. Fix: add -1 to the refusal table in test_for… |
| E-79 | gate | spec-driven | FAIL acceptance |
| E-81 | gate | spec-driven | FAIL acceptance |
| E-82 | gate | orchestrator | FAIL acceptance |
| E-83 | dispatch | P4 | /plan-update dispatched as P4 |
| E-85 | gate | orchestrator | FAIL acceptance |
| E-86 | gate | orchestrator | FAIL acceptance |
| E-87 | gate | orchestrator | FAIL acceptance |
| E-88 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-89 | dispatch | P4 | /plan-update dispatched as P4 |
| E-92 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-93 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-96 | finding | R2 | Mutant cli.py line 25 `if args.month is not None else None` changed to `if args.month else None`: python3 -m pytest -q tests in a copy outside the worktree prints 22 passed (survived). Input `budgetcli --file l.json export --month ""` prints every expense and exits 0; the contract needs an error line and exit 2 (parse_month rejects the empty month on the real code). The wrong-month test has no em… |
| E-97 | finding | R2 | Input `budgetcli --file l.json export \| head -0` on a 3-row ledger: a BrokenPipeError traceback is printed (File "cli.py", line 33, sys.stdout.write(text)), and the pipeline exits 1. The export path has no closed-pipe test. Contract: AC-5 and review-rigor adversarial input `a closed output pipe` require no traceback. Fix: catch BrokenPipeError around the stdout write, or add a test that runs expo… |
| E-98 | finding | R2 | Mutant ledger.py line 64 `if cents < 0` changed to `if cents <= 0`: python3 -m pytest -q tests in a copy outside the worktree prints 22 passed (survived). A stored row with amount_cents 0 prints `2026-10-01,x,0.00,` on the real code and the mutant refuses it, so the zero-amount path is not pinned by any test. Fix: add format_cents(0) == "0.00" to test_format_cents_has_two_decimals, or a refusal r… |
| E-99 | finding | R4 | The MF-1 fix adds acceptance/check_export_ac4.py, which copies ENV, HEADER, budgetcli, seed and parse from acceptance/check_export.py. The weak AC-4 check (regex (?<!\d)3(?!\d) at line 94) stays in check_export.py and in CHECKS, so check_export.py AC-4 still passes a mutant that prints len(rows)-1 when TMPDIR holds a 3. Fix: merge the strict check into check_export.py, delete check_export_ac4.py,… |
| E-104 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-105 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-107 | finding | R2 | Closed-pipe test asserts stderr only, not returncode. Mutant cli.py return 1 to return 0 survives: 23 passed. Real code exits 1 on budgetcli export \| head -0. Fix: assert result.returncode == 1. |
| E-108 | finding | R2 | Mutant drops TypeError from the load except clause; 23 passed. Input: ledger file holding the JSON object {"day": "2026-10-01"}. Real code: error line, exit 2. Mutant: traceback from run_export. Fix: add the object row to the bad_rows table. |
| E-109 | finding | R2 | Stored amount_cents 5.5 prints 0.05 exit 0 (int truncates). Stored true prints 0.01 exit 0. Review-rigor wrong-type row expects error line and exit 2. No test row covers float or bool. Fix: refuse non-integer amounts in Ledger.load and add the rows to bad_rows. |
| E-110 | finding | R2 | Removing the dup2 line survives 23 passed. A 2000-row closed-pipe probe is silent with and without the line. The line is unpinned: remove it with a reason, or add a test that fails without it. |
| E-115 | dispatch | R1 | /pr-review-local dispatched as R1 |
| E-116 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-117 | finding | R2 | Removing the dup2 line survives 23 passed. A 2000-row closed-pipe probe is silent with and without the line. The line is unpinned: remove it with a reason, or add a test that fails without it. |
| E-118 | finding | R2 | Mutants export.py category .strip() and note .rstrip() both survive python3 -m pytest -q tests (23 passed). Input category `food ` with note `x\n`: output keeps the bytes, exit 0, which is correct per RFC 4180, but no test pins it. Fix: add one row to the parametrize table in tests/test_export.py with a trailing space in category and a trailing newline in note, asserting the exact CSV line. |
| E-121 | finding | R1 | sys.stdout.write(text) in run_export raises UnicodeEncodeError when stdout is not UTF-8. PYTHONIOENCODING=ascii with note café: traceback, exit 1. Only BrokenPipeError is caught. Expected: no traceback (an error: line with exit 2, or the encoded bytes written to sys.stdout.buffer). Review .context/prs/reviews/PR_REVIEW_1.md, Must-fix items, MF-3. |
| E-122 | finding | R1 | Ledger.load does not type-check category or note. Stored row {"day":"2026-10-01","category":5,"amount_cents":100} prints 2026-10-01,5,1.00, exit 0. category null prints an empty field, exit 0. note 7 prints 7, exit 0. Expected: error line and exit 2, as a wrong-type amount_cents gives. Review .context/prs/reviews/PR_REVIEW_1.md, Must-fix items, MF-4. |
| E-125 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-126 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-128 | gate | R2 | FAIL test-benchmark-gate-code |
| E-132 | dispatch | P4 | /plan-update dispatched as P4 |
| E-134 | gate | orchestrator | FAIL acceptance |
| E-138 | gate | orchestrator | FAIL closure |
| E-139 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-140 | hard-stop | orchestrator | R1 must-fix MF-2 (AC-4 check) stays open at HEAD 1f5b5f3. The AC-4 check file acceptance/check_export.py is shared by AC-1, AC-2, AC-3 and AC-5, so the one-check repin refuses any change to it. The AC-4 run already calls acceptance/check_export_ac4.py, and the reviewer still reads the old AC-4 branch in check_export.py as must-fix. Repin passes, but closure (R5) fails on MF-1 and MF-2. Resume: fi… |
| E-141 | fix-commit | E1 | test: feat-local-4-csv-export-F14 trailing whitespace in category and note is kept |
| E-142 | fix-commit | E1 | fix: feat-local-4-csv-export-ae392096-MF-3 non-utf8 stdout writes the utf-8 bytes |
| E-143 | fix-commit | E1 | test: feat-local-4-csv-export-ae392096-MF-3 a non-ascii note to an ascii stdout has no traceback (red) |
| E-144 | fix-commit | E1 | fix: feat-local-4-csv-export-ae392096-MF-4 a wrong-type category or note is a bad row |
| E-145 | fix-commit | E1 | test: feat-local-4-csv-export-ae392096-MF-4 a wrong-type category or note is a bad row (red) |
| E-146 | fix-commit | E1 | fix: feat-local-4-csv-export-F12 a non-integer stored amount is a bad row |
| E-147 | fix-commit | E1 | test: feat-local-4-csv-export-F12 a float or boolean amount is a bad row (red) |
| E-148 | fix-commit | E1 | test: feat-local-4-csv-export-F11 a JSON object as the ledger is a bad row |
| E-149 | fix-commit | E1 | fix: feat-local-4-csv-export-F13 drop the devnull dup2 on a closed pipe |
| E-150 | fix-commit | E1 | test: feat-local-4-csv-export-F10 closed pipe exits 1 |
| E-151 | fix-commit | E1 | fix: feat-local-4-csv-export-F08 export to a closed pipe exits 1 with no traceback |
| E-152 | fix-commit | E1 | test: feat-local-4-csv-export-F08 export to a closed pipe prints no traceback (red) |
| E-153 | fix-commit | E1 | test: feat-local-4-csv-export-F09 a stored amount of zero prints 0.00 |
| E-154 | fix-commit | E1 | test: feat-local-4-csv-export-F07 an empty month is an error line and exit 2 |
| E-155 | fix-commit | E1 | test: feat-local-4-csv-export-F06 a stored amount of -1 cent is refused |
| E-156 | fix-commit | E1 | fix: feat-local-4-csv-export-F05 the three ledger-writing export tests share one helper |
| E-157 | fix-commit | E1 | test: feat-local-4-csv-export-ae392096-MF-1 AC-4 passes a wrong row count (repro) |
| E-158 | fix-commit | E1 | fix: feat-local-4-csv-export-F04 seeded_ledger helper for the export test setup |
| E-159 | fix-commit | E1 | test: feat-local-4-csv-export-F03 non-ASCII note is written as UTF-8 |
| E-160 | fix-commit | E1 | fix: feat-local-4-csv-export-F02 bad stored row is an error line, exit 2 |
| E-161 | fix-commit | E1 | test: feat-local-4-csv-export-F02 bad stored row is an error line (red) |
| E-162 | fix-commit | E1 | fix: feat-local-4-csv-export-F01 lone surrogate note is an error line, exit 2 |
| E-163 | fix-commit | E1 | test: feat-local-4-csv-export-F01 lone surrogate note is an error line (red) |
