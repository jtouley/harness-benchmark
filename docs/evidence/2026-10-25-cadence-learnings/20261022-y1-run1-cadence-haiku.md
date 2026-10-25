RUN_BY_COMMAND: run-learnings
Run: 20261022-y1-run1-cadence-haiku
Cadence: 70ae163507b73634e129ce470b0a945f4b095dd2
Packet sha256: 241a91ebe958a02161603b23b3a4bba431e351a5344bee5a0ae1a62db1bb076c

# Learnings: 20261022-y1-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 20
- finding: 14
- fix-commit: 17
- gate: 64
- hard-stop: 1
- stop-point: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-9, E-19
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-14, E-16
- Rule: gate-repeat
- Key: gate-repeat|plan-review|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in P3: fail plan-review-round round # waits on plan-review; fail plan-review-round round # waits on adversarial-review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-90, E-93
- Rule: gate-repeat
- Key: gate-repeat|cadence|the
- Change: Before the return, run the `the` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail the run is open r# pr-comment.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-50
- Rule: late-gate
- Key: late-gate|spec-driven|pr-review-local-gate|pr-review-local no join
- Change: E1's phase gate runs the `pr-review-local-gate` measure `pr-review-local no join` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-60
- Rule: late-gate
- Key: late-gate|spec-driven|test-benchmark-gate-code|test-benchmark-pr no join
- Change: E1's phase gate runs the `test-benchmark-gate-code` measure `test-benchmark-pr no join` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-26, E-94
- Rule: redispatch
- Key: redispatch|spec-driven|E1
- Change: E1 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-42, E-57, E-64, E-72, E-86
- Rule: redispatch
- Key: redispatch|test-benchmark|R2
- Change: R2 was dispatched 5 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/pr-review-update.md
- Status: candidate
- Evidence: E-56, E-63, E-71, E-85
- Rule: redispatch
- Key: redispatch|pr-review-update|R4
- Change: R4 was dispatched 4 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-update@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=pr-review-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-45, E-46, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115, E-116, E-117
- Rule: review-finding
- Key: review-finding|spec-driven|core:x
- Change: E1 checks `core:x` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-47, E-48, E-59, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115, E-116, E-117
- Rule: review-finding
- Key: review-finding|spec-driven|references/review-rigor.md#R2
- Change: E1 checks `references/review-rigor.md#R2` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-66, E-77, E-79, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115, E-116, E-117
- Rule: review-finding
- Key: review-finding|spec-driven|ADR-0008
- Change: E1 checks `ADR-0008` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-67, E-75, E-78, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115, E-116, E-117
- Rule: review-finding
- Key: review-finding|spec-driven|ADR-0027
- Change: E1 checks `ADR-0027` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-13
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-74, E-76, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115, E-116, E-117
- Rule: review-finding
- Key: review-finding|spec-driven|F05
- Change: E1 checks `F05` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-14
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-98
- Rule: hard-stop
- Key: hard-stop|spec-driven|E1|retries
- Change: E1 recorded a `retries` hard stop: e# implement-gate fails phase # acceptance and regression has no phase. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@70ae163507b73634e129ce470b0a945f4b095dd2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-9 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-14 | gate | P3 | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review |
| E-16 | gate | P3 | FAIL plan-review-round: round 1 waits on adversarial-review |
| E-19 | gate | orchestrator | FAIL plan-review-round: round 1 has 17 must-fix rows |
| E-26 | dispatch | E1 | /spec-driven dispatched as E1 |
| E-42 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-45 | finding | R1 | A stored row with amount_cents -5 (add refuses it, but the file can hold it) exports as -1.95 instead of -0.05. Repro: budgetcli --file neg.json export on a file holding that row prints 2026-10-01,refund,-1.95 and exits 0. |
| E-46 | finding | R1 | The guard against --out naming the ledger uses Path.resolve(), which does not see a hard link. With hard.csv hard-linked to ledger.json, budgetcli --file ledger.json export --out hard.csv prints wrote 1 rows and replaces the ledger contents with the CSV. Repro in a scratch directory; the user tree was not touched. |
| E-47 | finding | R2 | Ledger file with amount_cents -5 exports as -1.95, expected -0.05. _amount floors negative values (cents // 100, cents % 100). No test covers a negative amount. |
| E-48 | finding | R2 | A note that does not encode (lone surrogate from argv via add --note, or U+D800 in a ledger file) makes export exit 1 with UnicodeEncodeError. The add path accepts the note. render_csv(...).encode("utf-8") has no error handler. No test covers it. |
| E-50 | gate | R1 | FAIL pr-review-local-gate |
| E-56 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-57 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-59 | finding | R2 | Mutant src/budgetcli/export.py:24 (the resolve() equality clause of _is_ledger set to False) survives all tests. With a missing ledger, export --out ledger.json writes the CSV over the ledger path (exit 0). The next add then fails with Expecting value. Existing test_out_refuses_ledger_path seeds the ledger first, so only the samefile clause is exercised. Kill: a parametrize row with a missing led… |
| E-60 | gate | R2 | FAIL test-benchmark-gate-code |
| E-63 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-64 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-66 | finding | R2 | test_shape.py --change: thin_files fail: tests/test_cli.py (1 tests of src/budgetcli/cli.py, also tested by tests/test_export.py). The file holds one test, test_totals_output_is_pinned. tests/test_ledger.py already holds the cli-layer test test_cli_add_then_totals and has 3 or more tests. |
| E-67 | finding | R2 | Mutant M16 (ledger.py expenses key=lambda e: e.day changed to key=lambda e: (e.day, e.category)) survives all 42 tests. The docstring promises a tie keeps ledger order. test_expenses_sorts_by_day_and_keeps_insertion_order_on_a_tie uses one category, food, for the two 2026-10-03 rows, so the mutant output is the same. Kill: add a 2026-10-03 food row added before a 2026-10-03 rent row and assert le… |
| E-71 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-72 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-74 | finding | R4 | Commit 04ad4ac moved the cli-level totals test (test_totals_output_is_pinned, line 75) and test_cli_add_then_totals (line 23) into tests/test_ledger.py, and deleted tests/test_cli.py. Both call budgetcli.cli.main. F05 (a110c98) required the totals test in the cli test module, so the layer fix is undone. test_layers.py checks only test_export.py and does not catch it. Fix: put both cli-level tests… |
| E-75 | finding | R4 | Mutant M16 (ledger.py expenses key=lambda e: e.day changed to key=lambda e: (e.day, e.category)) survives all 42 tests. The docstring promises a tie keeps ledger order. test_expenses_sorts_by_day_and_keeps_insertion_order_on_a_tie uses one category, food, for the two 2026-10-03 rows, so the mutant output is the same. Kill: add a 2026-10-03 food row added before a 2026-10-03 rent row and assert le… |
| E-76 | finding | R4 | Commit 04ad4ac moved the cli-level totals test (test_totals_output_is_pinned, line 75) and test_cli_add_then_totals (line 23) into tests/test_ledger.py, and deleted tests/test_cli.py. Both call budgetcli.cli.main. F05 (a110c98) required the totals test in the cli test module, so the layer fix is undone. test_layers.py checks only test_export.py and does not catch it. Fix: put both cli-level tests… |
| E-77 | finding | R2 | test_shape.py --change: thin_files fail: tests/test_cli.py (1 tests of src/budgetcli/cli.py, also tested by tests/test_export.py). The file holds one test, test_totals_output_is_pinned. tests/test_ledger.py already holds the cli-layer test test_cli_add_then_totals and has 3 or more tests. |
| E-78 | finding | R2 | Mutant M16 (ledger.py expenses key=lambda e: e.day changed to key=lambda e: (e.day, e.category)) survives all 42 tests. The docstring promises a tie keeps ledger order. test_expenses_sorts_by_day_and_keeps_insertion_order_on_a_tie uses one category, food, for the two 2026-10-03 rows, so the mutant output is the same. Kill: add a 2026-10-03 food row added before a 2026-10-03 rent row and assert le… |
| E-79 | finding | R2 | DRY score 6. Ledger seeding is duplicated: tests/test_export.py seeded_ledger (L50-L55) is shared by no other module, and tests/test_ledger.py builds ledgers inline with 16 ledger.add calls in 7 tests. The export argv ["--file", str(path), "export", ...] is built inline at 15 call sites in tests/test_export.py. test_shape.py reports helpers_reimplemented as unmeasured (no conftest.py), so the dup… |
| E-85 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-86 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-90 | gate | orchestrator | FAIL the run is open: R6 (pr-comment) has not passed. |
| E-93 | gate | orchestrator | FAIL the run is open: R6 (pr-comment) has not passed. |
| E-94 | dispatch | E1 | /spec-driven dispatched as E1 |
| E-98 | hard-stop | orchestrator | E1 implement-gate fails: phase 4 (Acceptance and regression) has no 'phase 4: red' commit. Its pinned totals test (commit 46fc187) passes at HEAD by design, and the peer re-run made no change. A red commit needs a plan decision or a history rewrite, which the run does not do on its own. PR draft, R1-R5 and the R6 comment are done. |
| E-101 | fix-commit | E1 | fix: feat-local-4-csv-export-F09 import order of the conftest import (ruff I001) |
| E-102 | fix-commit | E1 | fix: feat-local-4-csv-export-F09 seeded ledger helper moves to tests/conftest.py |
| E-103 | fix-commit | E1 | test: feat-local-4-csv-export-F09 seeded ledger helper lives in conftest (red) |
| E-104 | fix-commit | E1 | fix: feat-local-4-csv-export-800eb3b7-MF-3 cli tests move to a cli-layer module |
| E-105 | fix-commit | E1 | test: feat-local-4-csv-export-800eb3b7-MF-3 ledger tests do not call the cli (red) |
| E-106 | fix-commit | E1 | fix: feat-local-4-csv-export-F07 totals test moves to the ledger test module |
| E-107 | fix-commit | E1 | test: feat-local-4-csv-export-F08 expenses keeps ledger order within a day |
| E-108 | fix-commit | E1 | fix: feat-local-4-csv-export-F05 ledger and totals tests move to their layer modules |
| E-109 | fix-commit | E1 | test: feat-local-4-csv-export-F05 export tests hold no ledger or totals tests (red) |
| E-110 | fix-commit | E1 | test: feat-local-4-csv-export-F04 missing ledger path is refused |
| E-111 | fix-commit | E1 | fix: feat-local-4-csv-export share the ledger refusal assertion (R3 duplication) |
| E-112 | fix-commit | E1 | fix: feat-local-4-csv-export-F02 lone surrogate note is an error, not a traceback |
| E-113 | fix-commit | E1 | test: feat-local-4-csv-export-F02 lone surrogate note is an error, not a traceback (red) |
| E-114 | fix-commit | E1 | fix: feat-local-4-csv-export-MF-2 hard link to the ledger is refused |
| E-115 | fix-commit | E1 | test: feat-local-4-csv-export-MF-2 hard link to the ledger is refused (red) |
| E-116 | fix-commit | E1 | fix: feat-local-4-csv-export-MF-1 negative amount keeps its sign |
| E-117 | fix-commit | E1 | test: feat-local-4-csv-export-MF-1 negative amount keeps its sign (red) |
