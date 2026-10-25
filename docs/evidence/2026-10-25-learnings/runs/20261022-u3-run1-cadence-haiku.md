RUN_BY_COMMAND: run-learnings
Run: 20261022-u3-run1-cadence-haiku
Cadence: a3eb0aaf812e1f0be3e12aba48894ffc36983f5b
Packet sha256: 85865a325775995936282325608a47fc039e3ac388a12957636165a7fd4e26e3

# Learnings: 20261022-u3-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 23
- finding: 13
- fix-commit: 20
- gate: 62
- stop-point: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-12, E-19, E-21, E-22
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 4 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix; fail plan-review-round changed phase # which no.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-25, E-26
- Rule: gate-repeat
- Key: gate-repeat|plan-update|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in P4: fail plan-review-round changed phase # which no; fail plan-review-round cycle limit reached # cycles.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-58
- Rule: late-gate
- Key: late-gate|spec-driven|pr-review-local-gate|pr-review-local no join
- Change: E1's phase gate runs the `pr-review-local-gate` measure `pr-review-local no join` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-61
- Rule: late-gate
- Key: late-gate|spec-driven|test-benchmark-gate-code|test-benchmark-pr no join
- Change: E1's phase gate runs the `test-benchmark-gate-code` measure `test-benchmark-pr no join` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-20, E-23
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-33, E-35
- Rule: redispatch
- Key: redispatch|spec-driven|E1
- Change: E1 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-53, E-68, E-72, E-77, E-81, E-85, E-93
- Rule: redispatch
- Key: redispatch|test-benchmark|R2
- Change: R2 was dispatched 7 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/pr-review-update.md
- Status: candidate
- Evidence: E-67, E-76, E-84, E-92
- Rule: redispatch
- Key: redispatch|pr-review-update|R4
- Change: R4 was dispatched 4 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-update@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=pr-review-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-56, E-57, E-59, E-60, E-69, E-71, E-86, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115, E-116, E-117, E-118, E-119
- Rule: review-finding
- Key: review-finding|spec-driven|core:adversarial-inputs
- Change: E1 checks `core:adversarial-inputs` before E4: the review found 7 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-70, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115, E-116, E-117, E-118, E-119
- Rule: review-finding
- Key: review-finding|spec-driven|core:mutation-resilience
- Change: E1 checks `core:mutation-resilience` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-79, E-82, E-87, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115, E-116, E-117, E-118, E-119
- Rule: review-finding
- Key: review-finding|spec-driven|R2-mutation-resilience
- Change: E1 checks `R2-mutation-resilience` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-83, E-88, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114, E-115, E-116, E-117, E-118, E-119
- Rule: review-finding
- Key: review-finding|spec-driven|R2-adversarial-inputs
- Change: E1 checks `R2-adversarial-inputs` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@a3eb0aaf812e1f0be3e12aba48894ffc36983f5b --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-12 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-19 | gate | orchestrator | FAIL plan-review-round: round 1 has 12 must-fix rows |
| E-20 | dispatch | P4 | /plan-update dispatched as P4 |
| E-21 | gate | orchestrator | FAIL plan-review-round: /plan-update changed Phase 1, which no finding of round 1 names. Send /plan-update again: undo that change, and change only Phase 2, Phase 3, Phase 4, global. The change: - - Code: `Ledger.expenses(self, month: str \| None = None) -> list[Expense]` in `src/budgetcli/ledger.py`. It filters `self.load()` by the month prefix, then sorts with `sorted(..., key=lambda e: e.day)`.… |
| E-22 | gate | orchestrator | FAIL plan-review-round: cycle limit reached (1 cycles). Do not run P6 again. Run /plan-update. Add "## Carried adversarial findings (adversarial_feat-local-4-csv-export.md @ 484aba9ed8e6)" and map B-1, B-2, C-1, C-2, C-3, C-4, C-5 to the phase whose test settles each. Send /plan-update again with the round file |
| E-23 | dispatch | P4 | /plan-update dispatched as P4 |
| E-25 | gate | P4 | FAIL plan-review-round: /plan-update changed Phase 1, which no finding of round 1 names. Send /plan-update again: undo that change, and change only Phase 2, Phase 3, Phase 4, global. The change: - - Code: `Ledger.expenses(self, month: str \| None = None) -> list[Expense]` in `src/budgetcli/ledger.py`. It filters `self.load()` by the month prefix, then sorts with `sorted(..., key=lambda e: e.day)`.… |
| E-26 | gate | P4 | FAIL plan-review-round: cycle limit reached (1 cycles). Do not run P6 again. Run /plan-update. Add "## Carried adversarial findings (adversarial_feat-local-4-csv-export.md @ 484aba9ed8e6)" and map B-1, B-2, C-1, C-2, C-3, C-4, C-5 to the phase whose test settles each. Send /plan-update again with the round file |
| E-33 | dispatch | E1 | /spec-driven dispatched as E1 |
| E-35 | dispatch | E1 | /spec-driven dispatched as E1 |
| E-53 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-56 | finding | R1 | A stored row with a missing field (`[{"day":"2026-10-01","category":"x"}]`) makes `budgetcli export` exit 1 with a KeyError traceback. A stored amount of the wrong type (`"amount_cents":"abc"`) exits 1 with a ValueError traceback. The request says a bad input to export is an error: line and exit 2, never a traceback. Ledger.load is the reader. The same traceback exists for totals and add (pre-exi… |
| E-57 | finding | R1 | With a closed output pipe (`budgetcli export --file L \| head -0`) the command exits 1 with a BrokenPipeError traceback from sys.stdout.buffer.write. ADR-0027 requires the closed output pipe input for any change that writes data. |
| E-58 | gate | R1 | FAIL pr-review-local-gate |
| E-59 | finding | R2 | A stored row with a missing field (`[{"day":"2026-10-01","category":"x"}]`) makes `budgetcli export` exit 1 with a KeyError traceback. A stored amount of the wrong type (`"amount_cents":"abc"`) exits 1 with a ValueError traceback. The request says a bad input to export is an error: line and exit 2, never a traceback. Ledger.load is the reader. The same traceback exists for totals and add (pre-exi… |
| E-60 | finding | R2 | With a closed output pipe (`budgetcli export --file L \| head -0`) the command exits 1 with a BrokenPipeError traceback from sys.stdout.buffer.write. ADR-0027 requires the closed output pipe input for any change that writes data. |
| E-61 | gate | R2 | FAIL test-benchmark-gate-code |
| E-67 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-68 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-69 | finding | R4 | A stored file whose JSON top level is not a list still gives a traceback and exit 1 on budgetcli export: a file holding 5 or null makes the list comprehension in Ledger.load raise TypeError (int/NoneType is not iterable). The check of MF-1 covers only a bad row, not the file shape. The request says never a traceback for a bad export input (ADR-0027 class: a bad row in a stored file). Reproduced a… |
| E-70 | finding | R2 | Surviving mutant M24: the TypeError entry is removed from the except tuple in _expense (ledger.py). Run: python3 -m pytest -q in a copy of HEAD 71f3f21 with the mutant applied gives 40 passed, so the mutant survives. No test stores a row that is not an object (for example [5]) or a null day ({"day": null}). Both give TypeError inside date.fromisoformat or row["day"]; at HEAD they exit 2 with an e… |
| E-71 | finding | R2 | Input: stored row with "category": null, expected: error line and exit 2 (a stored row that is not a valid expense, the same class as R2-F03). Observed at HEAD 71f3f21: exit 0, output 2026-10-01,,0.05, (empty category written). With "category": 5 the output is 2026-10-01,5,0.05, and exit 0. No test covers a non-string stored category. Add the two inputs as rows of a parametrized test. |
| E-72 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-76 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-77 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-79 | finding | R2 | Surviving mutant M-top-list-dict-allowed: src/budgetcli/ledger.py line 52 changed from `if not isinstance(rows, list):` to `if not isinstance(rows, (list, dict)):`. Run in a git-archive copy of HEAD faeb680 under mktemp -d: 46 passed, mutant survives. Input: ledger file holding {} (a JSON object). At HEAD the CLI gives error line and exit 2 (correct). The mutant gives header-only output and exit … |
| E-81 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-82 | finding | R2 | Surviving mutant M-sigpipe-status-0: src/budgetcli/cli.py line 16 changed from `_SIGPIPE_STATUS = 141` to `_SIGPIPE_STATUS = 0`. Run in a git-archive copy of HEAD 09701aa under mktemp -d: `python3 -m pytest tests -q` gives 47 passed, the mutant survives. The test asserts only `code != 1`, so exit 0 passes. Observed at the real CLI: with the mutant, `export ... \| head -0` exits 0 where HEAD exits … |
| E-83 | finding | R2 | Surviving mutant M-int-coerce: src/budgetcli/ledger.py line 27 changed from `return int(value)` to `return int(float(value))`. Run in a git-archive copy of HEAD 09701aa under mktemp -d: `python3 -m pytest tests -q` gives 47 passed, the mutant survives. Input (ADR-0027 very large number): a stored row with amount_cents 9007199254740993. HEAD prints `2026-10-01,x,90071992547409.93,` exit 0 (correct… |
| E-84 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-85 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-86 | finding | R4 | A stored file whose JSON top level is not a list still gives a traceback and exit 1 on budgetcli export: a file holding 5 or null makes the list comprehension in Ledger.load raise TypeError (int/NoneType is not iterable). The check of MF-1 covers only a bad row, not the file shape. The request says never a traceback for a bad export input (ADR-0027 class: a bad row in a stored file). Reproduced a… |
| E-87 | finding | R4 | Same finding as F09 (ledger row feat-local-4-csv-export-F09). The closed-pipe test asserts only code != 1. Reproduced at HEAD 09701aa in a scratch copy: with _SIGPIPE_STATUS = 0 the suite gives 47 passed. The mutant survives. |
| E-88 | finding | R4 | Same finding as F10 (ledger row feat-local-4-csv-export-F10). A stored amount_cents of 9007199254740993 exports exactly at HEAD 09701aa (90071992547409.93). With int(float(value)) the export prints ...92 and the suite still gives 47 passed. No test covers a stored integer above 2^53. |
| E-92 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-93 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-100 | fix-commit | E1 | test: feat-local-4-csv-export-cf46e2fb-MF-5 stored integer above 2**53 exports exactly (pins; kills float-coercion mutant) |
| E-101 | fix-commit | E1 | test: feat-local-4-csv-export-cf46e2fb-MF-4 closed pipe exits 141 (pins; kills exit-0 mutant) |
| E-102 | fix-commit | E1 | test: feat-local-4-csv-export-F08 top-level JSON object is an error (kills M-top-list-dict-allowed) |
| E-103 | fix-commit | E1 | fix: feat-local-4-csv-export-cf46e2fb-F07 stored category must be a string |
| E-104 | fix-commit | E1 | test: feat-local-4-csv-export-cf46e2fb-F07 stored category that is not a string is an error (red) |
| E-105 | fix-commit | E1 | test: feat-local-4-csv-export-cf46e2fb-F06 row that is not an object or has a null day is an error (pins; kills M24) |
| E-106 | fix-commit | E1 | fix: feat-local-4-csv-export-cf46e2fb-MF-3 stored file whose top level is not a list is an error |
| E-107 | fix-commit | E1 | test: feat-local-4-csv-export-cf46e2fb-MF-3 top-level value that is not a list is an error (red) |
| E-108 | fix-commit | E1 | fix: R3 offenders of the export fix round, mypy types and duplicated error assertions |
| E-109 | fix-commit | E1 | test: feat-local-4-csv-export-cf46e2fb-R2-F05 --out UTF-8 check runs under a non-UTF-8 locale |
| E-110 | fix-commit | E1 | fix: feat-local-4-csv-export-cf46e2fb-R2-F01 --out refuses a hard link to the ledger |
| E-111 | fix-commit | E1 | test: feat-local-4-csv-export-cf46e2fb-R2-F01 --out refuses a hard link to the ledger (red) |
| E-112 | fix-commit | E1 | fix: feat-local-4-csv-export-cf46e2fb-R2-F02 corrupt ledger file exits 2 without a traceback |
| E-113 | fix-commit | E1 | test: feat-local-4-csv-export-cf46e2fb-R2-F02 corrupt ledger file is an error (red) |
| E-114 | fix-commit | E1 | fix: feat-local-4-csv-export-cf46e2fb-R2-F03 stored amount must be a whole number |
| E-115 | fix-commit | E1 | test: feat-local-4-csv-export-cf46e2fb-R2-F03 stored amount that is not a whole number is an error (red) |
| E-116 | fix-commit | E1 | fix: feat-local-4-csv-export-cf46e2fb-MF-1 export refuses a stored row with a missing field or wrong type |
| E-117 | fix-commit | E1 | test: feat-local-4-csv-export-cf46e2fb-MF-1 stored row with a bad field is an error, not a traceback (red) |
| E-118 | fix-commit | E1 | fix: feat-local-4-csv-export-cf46e2fb-MF-2 closed output pipe exits 141 without a traceback |
| E-119 | fix-commit | E1 | test: feat-local-4-csv-export-cf46e2fb-MF-2 closed output pipe gives no traceback (red) |
