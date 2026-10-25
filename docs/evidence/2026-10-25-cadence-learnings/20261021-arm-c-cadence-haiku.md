RUN_BY_COMMAND: run-learnings
Run: 20261021-arm-c-cadence-haiku
Cadence: db1bedea9cca31d219953b1c728b009983aeb9a5
Packet sha256: 0bec18c9eeccdbf5d0a0657da4277996d0430e558d188903efd6154c768ac9de

# Learnings: 20261021-arm-c-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 20
- finding: 9
- fix-commit: 10
- gate: 67
- hard-stop: 1
- stop-point: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-10, E-17
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-20, E-21
- Rule: gate-repeat
- Key: gate-repeat|cadence|deferral-register
- Change: Before the return, run the `deferral-register` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: deferral-register deferral-review no ruling of the; deferral-register deferral-amber the plan does not carry.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-61, E-74, E-83, E-84, E-92
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|test-benchmark-gate-code
- Change: Before the return, run the `test-benchmark-gate-code` gate once and fix every class it names in one pass. In this run it failed 5 times in spec-driven: test-benchmark-code must-fix dimensions below # dry; test-benchmark-code mean score # is below; test-benchmark-code scores holds only the dimension scores.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/pr-review-update.md
- Status: candidate
- Evidence: E-67, E-82
- Rule: gate-repeat
- Key: gate-repeat|pr-review-update|test-benchmark-gate-code
- Change: Before the return, run the `test-benchmark-gate-code` gate once and fix every class it names in one pass. In this run it failed 2 times in R4: test-benchmark-code mean score # is below; test-benchmark-code must-fix dimensions below # dry.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-update@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=pr-review-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-58
- Rule: late-gate
- Key: late-gate|spec-driven|pr-review-local-gate|pr-review-local no peer-written
- Change: E1's phase gate runs the `pr-review-local-gate` measure `pr-review-local no peer-written` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-67
- Rule: late-gate
- Key: late-gate|spec-driven|test-benchmark-gate-code|test-benchmark-code mean score
- Change: E1's phase gate runs the `test-benchmark-gate-code` measure `test-benchmark-code mean score` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-72, E-82
- Rule: late-gate
- Key: late-gate|spec-driven|test-benchmark-gate-code|test-benchmark-code must-fix dimensions
- Change: E1's phase gate runs the `test-benchmark-gate-code` measure `test-benchmark-code must-fix dimensions` before E4, so the review phase does not find it first. It failed 2 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-18, E-22, E-28
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-49, E-65, E-80, E-87, E-94
- Rule: redispatch
- Key: redispatch|test-benchmark|R2
- Change: R2 was dispatched 5 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: commands/pr-review-update.md
- Status: candidate
- Evidence: E-64, E-81, E-88, E-95
- Rule: redispatch
- Key: redispatch|pr-review-update|R4
- Change: R4 was dispatched 4 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-update@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=pr-review-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-52, E-53, E-54, E-55, E-69, E-70, E-71, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|core:test-benchmark-pr
- Change: E1 checks `core:test-benchmark-pr` before E4: the review found 7 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-56, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|core:standalone-package
- Change: E1 checks `core:standalone-package` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-13
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-57, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-14
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-98
- Rule: open-at-close
- Key: open-at-close|pr-review-local|open-must-fix
- Change: The fix round returns only after `ledger_verify.py` marks each fixed must-fix item verified; R5 found open must-fix items 1 times.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-15
- Target: commands/pr-review-update.md
- Status: candidate
- Evidence: E-97
- Rule: hard-stop
- Key: hard-stop|pr-review-update|R4|retries
- Change: R4 recorded a `retries` hard stop: r# final-consolidate must-fix f# stays open after # fix rounds round. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-update@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=pr-review-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-16
- Target: commands/pr-review-update.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|pr-review-update|R4|hard stop at r# a
- Change: The run stopped at R4: hard stop at r# a scorecard finding stayed open. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-update@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=pr-review-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | R4 | hard stop at R4: a scorecard finding stayed open |
| E-10 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-17 | gate | orchestrator | FAIL plan-review-round: round 1 has 12 must-fix rows |
| E-18 | dispatch | P4 | /plan-update dispatched as P4 |
| E-20 | gate | orchestrator | FAIL deferral-register |
| E-21 | gate | orchestrator | FAIL deferral-register |
| E-22 | dispatch | P4 | /plan-update dispatched as P4 |
| E-28 | dispatch | P4 | /plan-update dispatched as P4 |
| E-49 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-52 | finding | R2 | Mutant M1 writes the category as e.category.replace(",", ";"). Result: 26 passed in 0.10s. No test puts a comma in a category. test_export_csv_quotes_only_the_fields_that_need_quoting puts a comma only in the note field. |
| E-53 | finding | R2 | Mutant M6 changes in_month to compare e.day.month == mon only, so the year is ignored. Result: 26 passed in 0.10s. Every fixture date is in 2026, so export --month and list --month never see a same month in another year. |
| E-54 | finding | R2 | Adversarial input corrupt ledger: BUDGETCLI_DB holds {"not": json. Observed: error: Expecting value: line 1 column 9 (char 8), exit 2, no output file. No test pins this path for export. |
| E-55 | finding | R2 | Scorecard mean 6.67 is below the floor of 7. Scores: coverage 7, assertions 7, dry 7, layer 7, failure paths 6, mutation resilience 6. Mutants: 11 run, 9 killed, 2 survived (M1, M6). |
| E-56 | finding | R1 | export --out <ledger path> exits 0 and overwrites the ledger with CSV; list then fails. Reproduced on a scratch ledger. See .context/prs/reviews/PR_REVIEW_1.md MF-1. |
| E-57 | finding | R1 | --out writes through tempfile.mkstemp, so new and overwritten export files get mode 0600 (umask 0022 gives 0644). Reproduced. See .context/prs/reviews/PR_REVIEW_1.md MF-2. |
| E-58 | gate | R1 | FAIL pr-review-local-gate |
| E-61 | gate | spec-driven | FAIL test-benchmark-gate-code |
| E-64 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-65 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-67 | gate | R4 | FAIL test-benchmark-gate-code |
| E-69 | finding | R2 | DRY score 6 (below 7). The CRLF byte expectation of test_export_prints_the_month_as_crlf_csv_bytes restates OCTOBER_CSV inline, and the header bytes b"date,category,amount,note\r\n" are repeated in four tests. Use OCTOBER_CSV and one HEADER_BYTES constant. Records: helpers_reimplemented unmeasured (no conftest), thin_files pass. |
| E-70 | finding | R2 | Mutant M14 survived (31 passed): the month regex with its end anchor removed is not caught. The input 2026-10x is accepted by the mutant and rejected by the code. Add 2026-10x and 2026-010 as rows of the existing parametrize table. |
| E-71 | finding | R2 | Mutant M17 survived (31 passed): _is_ledger returns False for a hard link to the ledger, and no test fails. The samefile branch of the ledger refusal guard is not pinned. Add a hard-link case beside the refusal test and assert the ledger bytes are unchanged. |
| E-72 | gate | R2 | FAIL test-benchmark-gate-code |
| E-74 | gate | spec-driven | FAIL test-benchmark-gate-code |
| E-80 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-81 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-82 | gate | R4 | FAIL test-benchmark-gate-code |
| E-83 | gate | spec-driven | FAIL test-benchmark-gate-code |
| E-84 | gate | spec-driven | FAIL test-benchmark-gate-code |
| E-87 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-88 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-92 | gate | spec-driven | FAIL test-benchmark-gate-code |
| E-94 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-95 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-97 | hard-stop | orchestrator | R4 final-consolidate: must-fix F04 stays open after 4 fix rounds; round 4 changed nothing (HEAD and F04 unchanged). Per ADR-0021 do not send the same fix round again. |
| E-98 | gate | orchestrator | FAIL closure |
| E-99 | fix-commit | E1 | test: feat-local-4-csv-export-F08 route every export --out call through _export_out |
| E-100 | fix-commit | E1 | test: feat-local-4-csv-export-F09 export --out refuses the ledger path when the ledger is missing |
| E-101 | fix-commit | E1 | test: feat-local-4-csv-export-F05 share the CSV header bytes and OCTOBER_CSV; one ledger refusal helper |
| E-102 | fix-commit | E1 | test: feat-local-4-csv-export-F06 wrong month rejects a trailing character and a padded month |
| E-103 | fix-commit | E1 | test: feat-local-4-csv-export-F07 export --out refuses a hard link to the ledger |
| E-104 | fix-commit | E1 | test: feat-local-4-csv-export-F01 F02 F03 category comma, other year, corrupt ledger |
| E-105 | fix-commit | E1 | fix: feat-local-4-csv-export-89618664-MF-2 export --out writes the umask mode |
| E-106 | fix-commit | E1 | test: feat-local-4-csv-export-89618664-MF-2 export --out writes the umask mode (red) |
| E-107 | fix-commit | E1 | fix: feat-local-4-csv-export-89618664-MF-1 export --out refuses the ledger |
| E-108 | fix-commit | E1 | test: feat-local-4-csv-export-89618664-MF-1 export --out refuses the ledger (red) |
