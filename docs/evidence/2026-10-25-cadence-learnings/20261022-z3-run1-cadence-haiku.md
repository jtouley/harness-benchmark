RUN_BY_COMMAND: run-learnings
Run: 20261022-z3-run1-cadence-haiku
Cadence: 99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27
Packet sha256: 5a41d37e598552a05c5bdc4e9dbc1e1e38192179fb8905ba08a99e7d62b3161d

# Learnings: 20261022-z3-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 21
- fix-commit: 27
- gate: 62
- hard-stop: 1
- stop-refusal: 3

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-8, E-14, E-23
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix; fail plan-review-round changed phase # which no.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-46, E-72, E-77
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|test-benchmark-gate-code
- Change: Before the return, run the `test-benchmark-gate-code` gate once and fix every class it names in one pass. In this run it failed 3 times in test-benchmark: test-benchmark-code verdict is fail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-44, E-45, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor R2 adversarial inputs
- Change: E1 checks `review-rigor R2 adversarial inputs` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-47, E-48, E-49, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|ADR-0027
- Change: E1 checks `ADR-0027` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-50, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|references/deferral-framework.md
- Change: E1 checks `references/deferral-framework.md` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-60, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|core:x
- Change: E1 checks `core:x` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-61, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor R2 mutation resilience and closed output pipe
- Change: E1 checks `review-rigor R2 mutation resilience and closed output pipe` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-62, E-69, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor R2 mutation resilience, stored value of the wrong type
- Change: E1 checks `review-rigor R2 mutation resilience, stored value of the wrong type` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-70, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor R2 mutation resilience, --out naming the ledger
- Change: E1 checks `review-rigor R2 mutation resilience, --out naming the ledger` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-71, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor R2 adjacent id, changed CLI
- Change: E1 checks `review-rigor R2 adjacent id, changed CLI` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-73, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor R2 mutation resilience and wrong-type stored value
- Change: E1 checks `review-rigor R2 mutation resilience and wrong-type stored value` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-74, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor R2 mutation resilience, optional stored field
- Change: E1 checks `review-rigor R2 mutation resilience, optional stored field` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-13
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-75, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|ADR-0027 wrong-type stored value
- Change: E1 checks `ADR-0027 wrong-type stored value` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-14
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-76, E-82, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor R2 mutation resilience, encoding of the stdout path
- Change: E1 checks `review-rigor R2 mutation resilience, encoding of the stdout path` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-15
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-83, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|ADR-0027 bad stored file path; review-rigor R2 failure paths
- Change: E1 checks `ADR-0027 bad stored file path; review-rigor R2 failure paths` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-16
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-84, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor R2 mutation resilience; ADR-0027 encoding of --out
- Change: E1 checks `review-rigor R2 mutation resilience; ADR-0027 encoding of --out` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-17
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-85, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor R2 mutation resilience; boundary of a value check
- Change: E1 checks `review-rigor R2 mutation resilience; boundary of a value check` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-18
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-86, E-88, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101, E-102, E-103, E-104, E-105, E-106, E-107, E-108, E-109, E-110, E-111, E-112, E-113, E-114
- Rule: review-finding
- Key: review-finding|spec-driven|ADR-0027 wrong-type stored value (note)
- Change: E1 checks `ADR-0027 wrong-type stored value (note)` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-19
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-87
- Rule: hard-stop
- Key: hard-stop|test-benchmark|R2|retries
- Change: R2 recorded a `retries` hard stop: r# test-benchmark still fail after three fix rounds on pr # five. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-20
- Target: SKILL.md
- Status: candidate
- Evidence: E-4, E-21, E-58
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 3 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@99d28e4a38cfbcabfdc0dcfbda9a8df65c4aaa27 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-4 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-8 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-14 | gate | orchestrator | FAIL plan-review-round: round 1 has 14 must-fix rows |
| E-21 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 357 characters; the limit is 300. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-23 | gate | orchestrator | FAIL plan-review-round: /plan-update changed Phase 5, which no finding of round 1 names. Send /plan-update again: undo that change, and change only Phase 2, Phase 3, global. The change: + ### Phase 5: the LOCAL-9 upload, up to the portal call \| + The `/deferral-review` ruling on the LOCAL-9 row is RED (criterion 1), so this change builds the upload. The \| + live call to the portal is not built or… |
| E-44 | finding | test-benchmark | export --file L --out L overwrites the ledger with CSV text, exit 0; no test covers --out equal to --file. Mutant and input in .context/benchmarks/feat-local-4-csv-export_code.json. |
| E-45 | finding | test-benchmark | Corrupt ledger (not json) and a row without amount_cents make export exit 1 with a traceback; the error-line and exit-2 contract has no test for stored-file errors. See .context/benchmarks/feat-local-4-csv-export_code.json. |
| E-46 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-47 | finding | pr-review-local | export --file ledger.json --out ledger.json prints 2 rows written to ledger.json, exit 0; the JSON ledger is replaced by CSV text |
| E-48 | finding | pr-review-local | budgetcli --file ledger.json export \| head -0 prints BrokenPipeError traceback, exit 1 |
| E-49 | finding | pr-review-local | a ledger note with a lone surrogate (bad \ud800 note): export prints UnicodeEncodeError traceback, exit 1; with --out the same traceback at cli.py:43 leaves a 0-byte file |
| E-50 | finding | pr-review-local | Approved deferrals: none. The request line 6 asks to record two deferrals. The LOCAL-9 row is RED in the deferral review and the plan leaves it OPEN for the orchestrator before E1 |
| E-58 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-60 | finding | pr-review-update | A hard link to the ledger passes the path check: budgetcli --file l3.json export --out l2.json, where l2.json and l3.json are hard links to one inode, prints 2 rows written and exit 0. Both names now hold the CSV text. The ledger is destroyed. The check compares path names, not files. Reproduced at 17def46. |
| E-61 | finding | test-benchmark | Removing the _drop_stdout() call keeps python3 -m pytest -q tests at 24 passed. With the real closed pipe, export \| head -0 gives rc=2 and one stderr line (real code), but rc=120 and an extra Exception ignored on flushing sys.stdout: BrokenPipeError line (mutant). The test stub does not reach the interpreter exit flush. Evidence and fix in .context/benchmarks/feat-local-4-csv-export_code.json. |
| E-62 | finding | test-benchmark | Removing TypeError from the except tuple keeps python3 -m pytest -q tests at 24 passed. A stored row with amount_cents null gives an error line and rc=2 in the real code, and a traceback with rc=1 under the mutant. No test row has a null amount. Evidence and fix in .context/benchmarks/feat-local-4-csv-export_code.json. |
| E-69 | finding | test-benchmark | Mutant M06 removes TypeError from READ_ERRORS. Command: python3 -m pytest -q tests (29 passed, mutant survives). Input: ledger [{"day": null, "category": "f", "amount_cents": 1, "note": ""}], command budgetcli --file nd.json export. Real code: error line, rc=2. Mutant: traceback, rc=1. No test row has a null day. Evidence in .context/benchmarks/feat-local-4-csv-export_code.json. |
| E-70 | finding | test-benchmark | Mutant M11a removes the path check in _names_ledger. Command: python3 -m pytest -q tests (29 passed, mutant survives). Input: no ledger file, command budgetcli --file new.json export --out new.json. Real code: refused, rc=2, no file. Mutant: writes CSV to new.json, rc=0. The suite names an existing ledger only. Evidence in .context/benchmarks/feat-local-4-csv-export_code.json. |
| E-71 | finding | test-benchmark | Input: ledger holding 2026-10-05 food 1250 and 2026-09-30 food 300, command budgetcli --file ledger.json totals --month 2026-1. Observed: food 12.50, rc=0 (October total for an adjacent id). Same input on export: error line, rc=2. totals --month October: empty output, rc=0. No test covers totals --month. Evidence in .context/benchmarks/feat-local-4-csv-export_code.json. |
| E-72 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-73 | finding | test-benchmark | Mutant: type(value) is not int changed to not isinstance(value, int). Stored row {"day":"2026-10-03","category":"food","amount_cents":true,"note":""}: HEAD prints error line, exit 2. Mutant prints 2026-10-03,food,0.01, exit 0. Suite still 29 passed. No test stores a boolean amount_cents. Mutant run: python3 -m pytest -q -p no:cacheprovider tests on the mutated copy. |
| E-74 | finding | test-benchmark | Mutant: r.get("note", "") changed to r["note"]. Stored row {"day":"2026-10-03","category":"food","amount_cents":100} (note optional, Expense.note defaults to ""): HEAD prints 2026-10-03,food,1.00, exit 0. Mutant prints error: cannot read the ledger ...: 'note', exit 2. Suite still 29 passed; no export test stores a row without note. Mutant run: python3 -m pytest -q -p no:cacheprovider tests on th… |
| E-75 | finding | test-benchmark | Stored row with category null: {"day":"2026-10-03","category":null,"amount_cents":100,"note":""}. HEAD export prints a header and 2026-10-03,,1.00, exit 0 (a silent empty category). Stored row with category 7 prints 2026-10-03,7,1.00, exit 0. Expected: error line and exit 2, as for a wrong-type amount_cents. No test covers a wrong-type category. Reproduce: budgetcli --file ledger.json export on t… |
| E-76 | finding | test-benchmark | Mutant: encoding = "utf-8" if args.out is not None else sys.stdout.encoding or "utf-8" changed to encoding = "utf-8". Stored note "café" with PYTHONIOENCODING=ascii: HEAD prints error: the export text does not encode as UTF-8, exit 2. Mutant prints a Python traceback (UnicodeEncodeError at cli.py sys.stdout.write), exit 1. Suite still 29 passed; the stdout encoding check has no test. Mutant run: … |
| E-77 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-82 | finding | test-benchmark | Mutant: encoding = "utf-8" if args.out is not None else sys.stdout.encoding or "utf-8" changed to encoding = "utf-8". Stored note "café" with PYTHONIOENCODING=ascii: HEAD prints error: the export text does not encode as UTF-8, exit 2. Mutant prints a Python traceback (UnicodeEncodeError at cli.py sys.stdout.write), exit 1. Suite still 29 passed; the stdout encoding check has no test. Mutant run: … |
| E-83 | finding | test-benchmark | Ledger path that is a directory: $ budgetcli --file DIR export prints the header and exits 0; budgetcli --file DIR totals prints nothing and exits 0. A directory is not a missing ledger, so the silent empty result hides a bad --file. Mutant ledger.py is_file() changed to exists(): exits 2 with an error line, and no test fails (37 passed). No test passes a directory as --file. |
| E-84 | finding | test-benchmark | Mutant cli.py: encoding = sys.stdout.encoding or "utf-8" for every export (the --out path too). Run with PYTHONIOENCODING=ascii, stored note "café": export --out o.csv exits 0 and writes the file on HEAD; the mutant prints error: the export text does not encode as UTF-8, exit 2 and writes no file. The mutant survives: 37 passed. The real-process encoding test (test_a_note_the_stdout_encoding_cann… |
| E-85 | finding | test-benchmark | Mutant ledger.py: if expense.amount_cents <= 0 changed to == 0. Command: budgetcli --file n.json add food -5. HEAD: error: amount must be positive, exit 2, no row written. Mutant: exit 0 and writes a -500 row. Survives: 37 passed. test_a_non_positive_amount_is_refused (tests/test_ledger.py) passes only 0, so no negative amount is tested. |
| E-86 | finding | test-benchmark | On HEAD dc9e5d0, stored rows with a note that is not text export with exit 0: note null gives 2026-10-03,food,1.00, (silent empty note); note 7 gives ...,7; note false gives ...,False; note ["a"] gives ...,['a'] (Python repr). Expected: error line and exit 2, as for category (F12) and amount_cents. Reproduce: budgetcli --file n.json export, with a row whose note is false. No test stores a non-tex… |
| E-87 | hard-stop | orchestrator | R2 test-benchmark still FAIL after three fix rounds on PR 1: five open must-fix findings F05, F14, F15, F16, F17 (mean 6.83). No retries left. |
| E-88 | fix-commit | E1 | fix: feat-local-4-csv-export-F12 a stored category that is not text is an error line |
| E-89 | fix-commit | E1 | test: feat-local-4-csv-export-F12 a stored category that is not text is an error line (red) |
| E-90 | fix-commit | E1 | fix: feat-local-4-csv-export-F09 totals refuses a partial month |
| E-91 | fix-commit | E1 | test: feat-local-4-csv-export-F09 totals with a partial month is an error line (red) |
| E-92 | fix-commit | E1 | test: feat-local-4-csv-export-F13 a note the stdout encoding cannot show is an error line |
| E-93 | fix-commit | E1 | test: feat-local-4-csv-export-F08 --out naming a missing ledger file is refused |
| E-94 | fix-commit | E1 | test: feat-local-4-csv-export-F11 a stored row without a note exports an empty note |
| E-95 | fix-commit | E1 | test: feat-local-4-csv-export-F10 a stored boolean amount_cents is an error line |
| E-96 | fix-commit | E1 | test: feat-local-4-csv-export-F07 a stored null day is an error line |
| E-97 | fix-commit | E1 | fix: R3 types in cli.main and the pipe test |
| E-98 | fix-commit | E1 | test: feat-local-4-csv-export-F05 a closed pipe in a real process is an error line and exit 2 |
| E-99 | fix-commit | E1 | test: feat-local-4-csv-export-F06 a stored null amount is an error line |
| E-100 | fix-commit | E1 | fix: feat-local-4-csv-export-F04 a stored amount that is not a whole number is an error line |
| E-101 | fix-commit | E1 | test: feat-local-4-csv-export-F04 a stored amount that is text is an error line (red) |
| E-102 | fix-commit | E1 | fix: feat-local-4-csv-export-F03 an amount too large for a number is an error line |
| E-103 | fix-commit | E1 | test: feat-local-4-csv-export-F03 a stored amount too large for a number is an error line (red) |
| E-104 | fix-commit | E1 | fix: feat-local-4-csv-export-c5d95f5c-MF-5 a hard link to the ledger is refused |
| E-105 | fix-commit | E1 | test: feat-local-4-csv-export-c5d95f5c-MF-5 --out naming a hard link to the ledger is refused (red) |
| E-106 | fix-commit | E1 | fix: R3 cognitive complexity of cli.main |
| E-107 | fix-commit | E1 | fix: feat-local-4-csv-export-F02 a corrupt stored ledger is an error line |
| E-108 | fix-commit | E1 | test: feat-local-4-csv-export-F02 a corrupt stored ledger is an error line (red) |
| E-109 | fix-commit | E1 | fix: feat-local-4-csv-export-c5d95f5c-MF-3 text that does not encode writes nothing |
| E-110 | fix-commit | E1 | test: feat-local-4-csv-export-c5d95f5c-MF-3 a note that does not encode is an error line (red) |
| E-111 | fix-commit | E1 | fix: feat-local-4-csv-export-c5d95f5c-MF-2 closed stdout pipe is an error line |
| E-112 | fix-commit | E1 | test: feat-local-4-csv-export-c5d95f5c-MF-2 closed stdout pipe is an error line (red) |
| E-113 | fix-commit | E1 | fix: feat-local-4-csv-export-F01 MF-1 --out naming the ledger is refused |
| E-114 | fix-commit | E1 | test: feat-local-4-csv-export-F01 MF-1 --out naming the ledger is refused (red) |
