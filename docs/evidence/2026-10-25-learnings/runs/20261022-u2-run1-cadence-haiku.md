RUN_BY_COMMAND: run-learnings
Run: 20261022-u2-run1-cadence-haiku
Cadence: a3eb0aaf812e1f0be3e12aba48894ffc36983f5b
Packet sha256: 759430f10c34a9394ef2c15f340950b00a7bc6e01b7641223fb1d768529180ea

# Learnings: 20261022-u2-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 16
- fix-commit: 12
- gate: 83
- stop-point: 1
- stop-refusal: 7

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-9, E-15
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-51, E-54
- Rule: gate-repeat
- Key: gate-repeat|pr-review-local|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 2 times in pr-review-local: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; fix step delegate with as its one.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-58, E-59
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 2 times in spec-driven: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; types union-attr item none of io bytes.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: SKILL.md
- Status: candidate
- Evidence: E-103, E-104
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: feat-local-#-csv-# must-fix status fixed not terminal. verify.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-37, E-38, E-39, E-40, E-41, E-42, E-65, E-66, E-67, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115, E-116, E-117, E-118, E-119
- Rule: review-finding
- Key: review-finding|spec-driven|core:test-benchmark-pr
- Change: E1 checks `core:test-benchmark-pr` before E4: the review found 9 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-45, E-46, E-52, E-53, E-84, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115, E-116, E-117, E-118, E-119
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 5 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-74, E-93, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115, E-116, E-117, E-118, E-119
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: SKILL.md
- Status: candidate
- Evidence: E-10, E-12
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked record each finding of your
- Change: The hooks refused 2 times with `blocked record each finding of your`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-21
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in planning. continue
- Change: The hooks refused 1 times with `blocked early stop in planning. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: SKILL.md
- Status: candidate
- Evidence: E-23
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in execution. continue
- Change: The hooks refused 1 times with `blocked early stop in execution. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: SKILL.md
- Status: candidate
- Evidence: E-81, E-90, E-95
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 3 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-9 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-10 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-u/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-u/scripts/plan_wave.py" done --stage test-benchmar… |
| E-12 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-u/scripts/plan_wave.py" add --stage plan-review --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-u/scripts/plan_wave.py" done --stage plan-review` (referen… |
| E-15 | gate | orchestrator | FAIL plan-review-round: round 1 has 9 must-fix rows |
| E-21 | stop-refusal | orchestrator | BLOCKED early stop in planning. Continue paceline: next P9 (entry-invariant) via `python3 /tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-u/scripts/entry_invariant.py --phase execution` |
| E-23 | stop-refusal | orchestrator | BLOCKED early stop in execution. Continue E1: send the `/spec-driven` peer the plan again. Its next open phase is phase 1 (Month filter and row order in the ledger). |
| E-37 | finding | test-benchmark | Mutant src/budgetcli/ledger.py:18 _MONTH.fullmatch(text) -> _MONTH.match(text) survives: python3 -m pytest -q tests passes 26 of 26 in a copy. Input 2026-10x: the real code raises ValueError, the mutant returns the text. Fix: add the row 2026-10x to the parametrize table of test_parse_month_refuses_partial_and_out_of_range. |
| E-38 | finding | test-benchmark | Input: python3 -m budgetcli.cli --file ledger.json export \| head -0 with 4 stored rows. Observed: BrokenPipeError traceback, exit 1. No test covers a closed output pipe. Expected: no traceback. Add a row to the export failure test in tests/test_cli_export.py. |
| E-39 | finding | test-benchmark | Input: a ledger file with the content {not json. Observed: export exits 1 with a JSONDecodeError traceback (totals does the same). No test covers a corrupt ledger. Expected: an error: line and exit 2, the rule AC-4 sets for export. |
| E-40 | finding | test-benchmark | Stored row {day 2026-10-01, category food} with no amount_cents: export exits 1 with KeyError traceback. Stored amount_cents NaN: export exits 1 with ValueError traceback. Stored day 2026-13-01: export exits 1 with ValueError traceback. No test covers a bad stored row. Expected: error: line and exit 2. |
| E-41 | finding | test-benchmark | Stored row with amount_cents as the string 12: export exits 0 and prints 2026-10-01,food,0.12, silently. Wrong type in a stored file gives wrong money output with no error. No test covers a wrong-type stored value. Expected: error: line and exit 2, or the row refused. |
| E-42 | finding | test-benchmark | Input: python3 -m budgetcli.cli --file s.json add food 1 --note with the bytes ED A0 80 (not valid UTF-8). add exits 0 and stores the note. Every later export exits 1 with UnicodeEncodeError traceback. The ledger cannot be exported. Expected: add refuses the note with an error: line, or export reports an error: line and exit 2. |
| E-45 | finding | pr-review-local | render_csv ends with buf.getvalue().encode('utf-8'). A note with a lone surrogate makes `budgetcli export` exit 1 with a UnicodeEncodeError traceback. Inputs: a ledger value \ud800, and an argv byte that is not UTF-8, for example `budgetcli add food 4 --note $'caf\xe9'`, which exits 0 and stores the note as caf\udce9. Reproduced in a scratch copy of the PR head. See ## Reproductions and ## Advers… |
| E-46 | finding | pr-review-local | AC-4 tests only 2026-1 and 2026-13. A mutant that accepts month 00 prints a header and exits 0 for --month 2026-00, and check_export_bad_month.py passes it (PASS). Recorded with acceptance.py defect --id AC-4 and acceptance/repro_AC-4.py. The plan peer fixes the check, then acceptance.py repin --id AC-4. |
| E-51 | gate | pr-review-local | FAIL cognitive-complexity |
| E-52 | finding | pr-review-local | Stored row with no amount_cents, or with amount_cents as the string 12: export exits 1 with KeyError traceback, or exits 0 and prints 2026-10-01,food,0.12 (silent wrong money). Corrupt JSON gives a JSONDecodeError traceback (same load path). Reproduced at 0357958 with acceptance/repro_MF-3.py (exit 1). |
| E-53 | finding | pr-review-local | python3 -m budgetcli.cli --file L export \| head -0 with 50000 rows: BrokenPipeError traceback on stderr, exit 1. Reproduced at 0357958 with acceptance/repro_MF-4.py (exit 1). Ledger F02 has the same defect. |
| E-54 | gate | pr-review-local | FAIL cognitive-complexity |
| E-58 | gate | spec-driven | FAIL cognitive-complexity |
| E-59 | gate | spec-driven | FAIL cognitive-complexity |
| E-65 | finding | test-benchmark | Mutant src/budgetcli/ledger.py: remove the clause ` or isinstance(cents, bool)` (line of _expense) survives: python3 -m pytest -q tests passes 35 of 35 on a copy of 9fbf608. Input: a stored row [{"day": "2026-10-01", "category": "food", "amount_cents": true}]. The mutant exports 2026-10-01,food,0.01 with exit 0. The real code exits 2 with error: ledger row 1: amount_cents must be an integer. Fix:… |
| E-66 | finding | test-benchmark | Mutant src/budgetcli/ledger.py: change the text check ` (day, category, note)` to ` (day, category)` survives: python3 -m pytest -q tests passes 35 of 35 on a copy of 9fbf608. Input: a stored row with note 7 (the number). The mutant exports 2026-10-01,food,0.05,7 with exit 0. The real code exits 2 with error: ledger row 1: day, category and note must be text. Fix: add a row with a non-text note t… |
| E-67 | finding | test-benchmark | Mutant src/budgetcli/ledger.py: change `if not isinstance(rows, list):` to `if False:` survives: python3 -m pytest -q tests passes 35 of 35 on a copy of 9fbf608. Input: a stored file that holds the JSON object {}. The mutant prints the header and exits 0. The real code exits 2 with error: ledger file must hold a list of expenses. Fix: add b"{}" to the parametrize table of test_export_bad_stored_l… |
| E-74 | finding | pr-review-local | python3 -m budgetcli.cli --file <missing> export > /dev/full: OSError [Errno 28] No space left on device traceback, exit 1. _write_stdout catches only BrokenPipeError. Reproduced at b2be4a2 by acceptance/repro_MF-5.py (DEFECT SHOWN, exit 1). |
| E-81 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 22 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-84 | finding | pr-review-local | Stdout closed (`budgetcli.cli ... export >&-`, or fd 1 closed with no output stream): sys.stdout is None, so sys.stdout.buffer raises AttributeError. Traceback on stderr, exit 1. Only OSError and BrokenPipeError are handled. Same output boundary as MF-4 and MF-5. Reproduced at 41b0df2 with acceptance/repro_MF-6.py (DEFECT SHOWN, exit 1). |
| E-90 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 10 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-93 | finding | pr-review-local | Hard link to the ledger passed as --out: `ln ledger.json alias.json; budgetcli --file ledger.json export --out alias.json` exits 0 and overwrites the ledger with CSV (ledger no longer valid JSON). The guard compares resolve() paths, so a hard link to the input passes it. Reproduced at c8ab34b with acceptance/repro_MF-7.py (DEFECT SHOWN, exit 1). Input class: output path that is also an input (rev… |
| E-95 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 19 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-103 | gate | orchestrator | FAIL closure |
| E-104 | gate | orchestrator | FAIL closure |
| E-108 | fix-commit | E1 | fix: MF-7 export through a hard link to the ledger is refused |
| E-109 | fix-commit | E1 | test: MF-7 export through a hard link to the ledger is refused (red) |
| E-110 | fix-commit | E1 | fix: MF-6 export with closed stdout gives error line and exit 2 |
| E-111 | fix-commit | E1 | test: MF-6 export with closed stdout gives error line and exit 2 (red) |
| E-112 | fix-commit | E1 | fix: MF-5 export to a full stdout gives error line and exit 2 |
| E-113 | fix-commit | E1 | test: MF-5 export to a full stdout gives error line and exit 2 (red) |
| E-114 | fix-commit | E1 | fix: F06 MF-1 note that is not UTF-8 gives error line and exit 2 |
| E-115 | fix-commit | E1 | test: F06 MF-1 note that is not UTF-8 gives error line and exit 2 (red) |
| E-116 | fix-commit | E1 | fix: F03 F04 F05 MF-3 bad stored ledger gives error line and exit 2 |
| E-117 | fix-commit | E1 | test: F03 F04 F05 MF-3 bad stored ledger gives error line and exit 2 (red) |
| E-118 | fix-commit | E1 | fix: F02 MF-4 closed output pipe exits without a traceback |
| E-119 | fix-commit | E1 | test: F02 MF-4 export to a closed pipe gives no traceback (red) |
