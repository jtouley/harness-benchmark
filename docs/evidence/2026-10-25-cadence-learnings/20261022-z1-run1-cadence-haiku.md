RUN_BY_COMMAND: run-learnings
Run: 20261022-z1-run1-cadence-haiku
Cadence: 99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27
Packet sha256: 17502c4ae2bb8a940effe19b91cc3be3be3c93ed6f531e61b820709a9d3c96ee

# Learnings: 20261022-z1-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 20
- fix-commit: 19
- gate: 65
- hard-stop: 1
- stop-refusal: 3

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-10, E-15
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-20, E-23, E-26, E-30
- Rule: gate-repeat
- Key: gate-repeat|cadence|entry-invariant
- Change: Before the return, run the `entry-invariant` gate once and fix every class it names in one pass. In this run it failed 4 times in orchestrator: adversarial-review cycle limit reached # cycles; plan-review the plan changed after its review; deferral-register deferral-review no ruling of the.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-42, E-72, E-81
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 3 times in spec-driven: fix step run r# without --check to; types.max is # fix each mypy finding; types union-attr item none of io bytes.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-70, E-88
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|test-benchmark-gate-code
- Change: Before the return, run the `test-benchmark-gate-code` gate once and fix every class it names in one pass. In this run it failed 2 times in test-benchmark: test-benchmark-code verdict is fail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-53, E-54, E-63, E-64, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 4 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-56, E-57, E-58, E-59, E-65, E-66, E-67, E-68, E-69, E-77, E-78, E-79, E-84, E-85, E-86, E-87, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|skills/test-benchmark/SKILL.md
- Change: E1 checks `skills/test-benchmark/SKILL.md` before E4: the review found 16 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-89
- Rule: hard-stop
- Key: hard-stop|test-benchmark|R2|retries
- Change: R2 recorded a `retries` hard stop: r# test-benchmark still fail after three fix rounds f# not reproduced and. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: SKILL.md
- Status: candidate
- Evidence: E-11
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked record each finding of your
- Change: The hooks refused 1 times with `blocked record each finding of your`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-17, E-29
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 2 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-10 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-11 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-z/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-z/scripts/plan_wave.py" done --stage test-benchmar… |
| E-15 | gate | orchestrator | FAIL plan-review-round: round 1 has 9 must-fix rows |
| E-17 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 17 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-20 | gate | orchestrator | FAIL entry-invariant |
| E-23 | gate | orchestrator | FAIL entry-invariant |
| E-26 | gate | orchestrator | FAIL entry-invariant |
| E-29 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 17 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-30 | gate | orchestrator | FAIL entry-invariant |
| E-42 | gate | spec-driven | FAIL cognitive-complexity |
| E-53 | finding | pr-review-local | stored amount_cents 12.5 prints 0.12, 1e30 prints a 30-digit amount, category null prints empty; export exits 0 (see PR_REVIEW_1.md Reproductions) |
| E-54 | finding | pr-review-local | export --out <ledger path> overwrites the ledger with CSV and exits 0 (reproduced in a scratch copy of d9a1e4f; see .context/prs/reviews/PR_REVIEW_1.md Reproductions) |
| E-56 | finding | test-benchmark | --out equal to the --file ledger path overwrites the ledger (run for real: exit 0, then the ledger is CSV text and the next export exits 2). No test covers this input. See .context/benchmarks/feat-local-4-csv-export_code.json findings. |
| E-57 | finding | test-benchmark | Surviving mutant if cents <= 0 in format_amount: python3 -m pytest -q gives 24 passed. No test calls format_amount(0). |
| E-58 | finding | test-benchmark | Surviving mutant sort key (e.day, e.note): python3 -m pytest -q gives 24 passed. The tie test uses notes that are already in alphabetical order. |
| E-59 | finding | test-benchmark | Surviving mutant return day[5:7] == month[5:7]: python3 -m pytest -q gives 24 passed. No fixture row from another year in the same month. |
| E-63 | finding | pr-review-update | export --out naming a hard link to the ledger overwrites the ledger with CSV and exits 0; the MF-1 check compares resolved paths only (reproduced at a27eee2; see .context/prs/reviews/PR_REVIEW_1.md Update 2026-10-22) |
| E-64 | finding | pr-review-update | stored whole-number amount_cents 10^31 prints a 30-digit amount with exit 0; the MF-2 fix checks type only, not range (reproduced at a27eee2; see .context/prs/reviews/PR_REVIEW_1.md Update 2026-10-22) |
| E-65 | finding | test-benchmark | Input: --file names a directory (mkdir dirledger.json). Expected: exit 2 with error:, the path is not an absent ledger. Observed (run for real on HEAD a27eee2): exit 0, stdout header only. Ledger.load treats a non-file path as an absent ledger, so export reports an empty ledger. Surviving mutant src/budgetcli/ledger.py line 24 if not self.path.is_file() changed to if not self.path.exists(): gives… |
| E-66 | finding | test-benchmark | Surviving mutant src/budgetcli/export.py line 14 if cents < 0 changed to if cents < -1: gives 32 passed under python3 -m pytest -q. format_amount(-1) then returns -1.99 instead of raising. test_format_amount_refuses_negative_cents (tests/test_export.py line 23) checks only -500. Fix: add -1 to the refusal parametrize row, as a new row in the existing table. |
| E-67 | finding | test-benchmark | Surviving mutant src/budgetcli/cli.py line 22 fullmatch changed to match: 32 passed under python3 -m pytest -q. The wrong-month test (tests/test_export.py line 85) has no value with trailing text. Real code on HEAD refuses --month 2026-10x (exit 2); the mutant would accept it. Fix: add 2026-10x to the wrong-month parametrize row. |
| E-68 | finding | test-benchmark | Surviving mutant src/budgetcli/ledger.py line 62 row.get("note", "") changed to row.get("note", "x"): 32 passed under python3 -m pytest -q. No stored row in the tests omits the note key, so the default is not pinned. A stored row without note prints x in the CSV with the mutant. Fix: add one row without note to the export parametrize table and assert the empty note field. |
| E-69 | finding | test-benchmark | Surviving mutant src/budgetcli/cli.py line 25 same-path check changed to compare file names only (Path(out).name == ledger.path.name): 32 passed under python3 -m pytest -q. No test writes --out to another directory with the same file name. Real code on HEAD writes it (run for real: exit 0, wrote 1 rows). The mutant would refuse it. Fix: add a row to the out-success table with a same-name file in … |
| E-70 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-72 | gate | spec-driven | FAIL cognitive-complexity |
| E-77 | finding | test-benchmark | Surviving mutant src/budgetcli/ledger.py line 66 if amount > MAX_AMOUNT_CENTS changed to if amount >= MAX_AMOUNT_CENTS: python3 -m pytest -q gives 41 passed. Stored amount_cents of exactly 10**12 is accepted by the real code (run for real on HEAD 8466609: exit 0, prints 10000000000.00). The only stored-amount test uses 10**31 (test_export_refuses_stored_amount_above_maximum). Fix: add a row for 1… |
| E-78 | finding | test-benchmark | Surviving mutant src/budgetcli/cli.py line 24 same-path check if out.resolve() == ledger.resolve() replaced by if False: python3 -m pytest -q gives 41 passed. Real effect (run for real with the mutant): export --file new.json --out new.json with no ledger file exits 0 and writes a CSV into new.json, the ledger path. The real code on HEAD refuses it with exit 2 and creates no file. The same-path t… |
| E-79 | finding | test-benchmark | Input: a closed stdout pipe, export \| head -0 with a ledger of one row (run for real on HEAD 8466609). Observed: stderr error: [Errno 32] Broken pipe, then Exception ignored on flushing sys.stdout: BrokenPipeError, and exit status 120. Expected: exit 2 with error: on stderr and no Exception ignored line. No test writes to a closed stdout; the suite has 41 passing tests with no subprocess test. Fi… |
| E-81 | gate | spec-driven | FAIL cognitive-complexity |
| E-84 | finding | test-benchmark | Input: a closed stdout pipe, export \| head -0 with a ledger of one row (run for real on HEAD 8466609). Observed: stderr error: [Errno 32] Broken pipe, then Exception ignored on flushing sys.stdout: BrokenPipeError, and exit status 120. Expected: exit 2 with error: on stderr and no Exception ignored line. No test writes to a closed stdout; the suite has 41 passing tests with no subprocess test. Fi… |
| E-85 | finding | test-benchmark | Surviving mutant add-side maximum check >= instead of >: python3 -m pytest -q -p no:cacheprovider gives 44 passed. Input: budgetcli --file L.json add food 10000000000 --day 2026-10-01 (exactly 10**12 cents). Expected exit 0; observed exit 0 on HEAD 959981a. Only test_an_amount_above_the_maximum_is_refused exists and it uses 10**12 + 1. Fix: add a row at 10**12 expecting no error. |
| E-86 | finding | test-benchmark | Surviving mutant that refuses an empty stored category: python3 -m pytest -q -p no:cacheprovider gives 44 passed. Input: stored row category empty string. Expected exit 0 with the row printed (the code comment keeps an empty category). Observed on HEAD: exit 0, 2026-10-01,,0.05, . No test has an empty category. Fix: add a row to the stored-row table expecting exit 0. |
| E-87 | finding | test-benchmark | Input: stored row with note null. Observed on HEAD 959981a: exit 0, 2026-10-01,food,0.05, . The stored-row type checks cover the amount and the category, not the note. Expected exit 2 with error: as for a null category, or a pinned decision that null notes are accepted. No test covers a null note. Fix: add a null-note row to the wrong-type table and fix the code or pin the decision. |
| E-88 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-89 | hard-stop | orchestrator | R2 test-benchmark still FAIL after three fix rounds; F12 not reproduced and open. PR 1 is a draft and MERGE-READY on R1. Resume: /test-benchmark 1 after F12 is fixed or ticketed. |
| E-90 | fix-commit | E1 | test: feat-local-4-csv-export-F12 narrow the Popen pipes for mypy |
| E-91 | fix-commit | E1 | test: feat-local-4-csv-export-F12 export to a closed stdout exits 2 with no exception at exit |
| E-92 | fix-commit | E1 | test: feat-local-4-csv-export-F11 --out naming an absent ledger is refused (kills same-path mutant) |
| E-93 | fix-commit | E1 | test: feat-local-4-csv-export-F10 stored amount at the maximum is accepted (kills >= mutant) |
| E-94 | fix-commit | E1 | refactor: feat-local-4-csv-export-F05 rename totals variable that shadowed the subparser (mypy) |
| E-95 | fix-commit | E1 | test: feat-local-4-csv-export-F06 F07 F08 F09 surviving-mutant gaps (red against cents < -1, fullmatch to match, note default, same-name path) |
| E-96 | fix-commit | E1 | fix: feat-local-4-csv-export-78cb20b8-MF-4 refuse an amount above the maximum on read and on add |
| E-97 | fix-commit | E1 | test: feat-local-4-csv-export-78cb20b8-MF-4 stored and added amount above the maximum is refused (red) |
| E-98 | fix-commit | E1 | fix: feat-local-4-csv-export-78cb20b8-MF-3 refuse --out that is a hard link to the ledger |
| E-99 | fix-commit | E1 | test: feat-local-4-csv-export-78cb20b8-MF-3 --out naming a hard link to the ledger is refused (red) |
| E-100 | fix-commit | E1 | fix: feat-local-4-csv-export-F05 ledger path that is a directory is an error |
| E-101 | fix-commit | E1 | test: feat-local-4-csv-export-F05 ledger path that is a directory is refused (red) |
| E-102 | fix-commit | E1 | test: feat-local-4-csv-export-78cb20b8-F04 month filter ignores same month of another year (red against month[5:7] compare) |
| E-103 | fix-commit | E1 | test: feat-local-4-csv-export-78cb20b8-F03 tie keeps insertion order when notes sort otherwise (red against note sort key) |
| E-104 | fix-commit | E1 | test: feat-local-4-csv-export-78cb20b8-F02 format_amount of zero cents (red against cents <= 0) |
| E-105 | fix-commit | E1 | fix: feat-local-4-csv-export-78cb20b8-MF-2 refuse stored amount or category of wrong type |
| E-106 | fix-commit | E1 | test: feat-local-4-csv-export-78cb20b8-MF-2 stored row of wrong type is refused (red) |
| E-107 | fix-commit | E1 | fix: feat-local-4-csv-export-MF-1 refuse --out that names the ledger |
| E-108 | fix-commit | E1 | test: feat-local-4-csv-export-MF-1 --out naming the ledger is refused (red) |
