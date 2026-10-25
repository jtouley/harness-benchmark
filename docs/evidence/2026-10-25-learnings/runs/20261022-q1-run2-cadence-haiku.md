RUN_BY_COMMAND: run-learnings
Run: 20261022-q1-run2-cadence-haiku
Cadence: fb0270d010cbfb284df5af992e1db36ed45cbeda
Packet sha256: 3429f62716cd068f5c3f57e1501567ca61827b12f657e989e6776516a909b163

# Learnings: 20261022-q1-run2-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 6
- finding: 7
- fix-commit: 20
- gate: 33
- hard-stop: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-32, E-33, E-34, E-39, E-42, E-46
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 6 times in orchestrator: feat-local-#-csv-# must-fix status fixed not terminal. verify; feat-local-#-csv-export-f# must-fix status fixed not terminal. verify.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-9
- Rule: late-gate
- Key: late-gate|spec-driven|pr-review-local-gate|pr-review-local no join
- Change: E1's phase gate runs the `pr-review-local-gate` measure `pr-review-local no join` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-3, E-21, E-30
- Rule: redispatch
- Key: redispatch|test-benchmark|R2
- Change: R2 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/pr-review-update.md
- Status: candidate
- Evidence: E-20, E-29
- Rule: redispatch
- Key: redispatch|pr-review-update|R4
- Change: R4 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-update@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=pr-review-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-6, E-7, E-8, E-24, E-48, E-49, E-50, E-51, E-52, E-53, E-54, E-55, E-56, E-57, E-58, E-59, E-60, E-61, E-62, E-63, E-64, E-65, E-66, E-67
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 4 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-10, E-11, E-12, E-48, E-49, E-50, E-51, E-52, E-53, E-54, E-55, E-56, E-57, E-58, E-59, E-60, E-61, E-62, E-63, E-64, E-65, E-66, E-67
- Rule: review-finding
- Key: review-finding|spec-driven|core:test-benchmark-pr
- Change: E1 checks `core:test-benchmark-pr` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: SKILL.md
- Status: candidate
- Evidence: E-47
- Rule: hard-stop
- Key: hard-stop|cadence|R5|retries
- Change: R5 recorded a `retries` hard stop: r# closure blocked ledger row feat-local-#-csv-# has a check that cannot pass. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-3 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-6 | finding | R1 | export --out F \| head -0 writes F then prints BrokenPipeError traceback (print(len(expenses)) outside the handler), exit 1. export >&- gives AttributeError (sys.stdout is None), exit 1. See PR_REVIEW_1.md MF-5. |
| E-7 | finding | R1 | Stored rows with wrong types export with exit 0 and wrong data: amount_cents 1.7 or true gives 0.01, 0.5 gives 0.00, note list prints [a], category null prints empty. See PR_REVIEW_1.md MF-6. |
| E-8 | finding | R1 | A deeply nested stored file raises RecursionError from json.loads, a traceback with exit 1. Not wrapped by the ValueError handler. See PR_REVIEW_1.md MF-7. |
| E-9 | gate | R1 | FAIL pr-review-local-gate |
| E-10 | finding | R2 | Surviving mutant M11: row.get("note", "") changed to row["note"] in src/budgetcli/ledger.py. The suite passes all 42 tests on the mutant. HEAD accepts a valid stored row with no note key: input [{"day":"2026-10-01","category":"food","amount_cents":250}] with export gives exit 0 and the line 2026-10-01,food,2.50, . The mutant gives exit 2 with error: row 1 is not an expense. Fix: add that row to a… |
| E-11 | finding | R2 | Surviving mutant M19: os.dup2(devnull, sys.stdout.fileno()) in src/budgetcli/cli.py changed to pass. The named test passes 3 of 3 runs on the mutant under the suite environment, so it does not pin the redirect. In a child started with env {PYTHONPATH, PATH} only, HEAD exits 1 with empty stderr, and the mutant exits 120 with the stderr line Exception ignored on flushing sys.stdout: BrokenPipeError… |
| E-12 | finding | R2 | Input: a ledger file that cannot be read. Simulated by patching pathlib.Path.read_text to raise PermissionError, because the suite and the host run as uid 0 and chmod 000 does not block them. Observed on HEAD: Traceback, PermissionError, exit 1 for export. Expected from the F04 commit (an unreadable ledger file is one error line, exit 2): one error: line, exit 2. ledger.py catches only ValueError… |
| E-20 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-21 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-24 | finding | R4 | A directory at the ledger path: Ledger.load tests is_file(), returns [] and export/totals exit 0 with header only or zero total. The F07 OSError handler is not reached. See PR_REVIEW_1.md MF-8 (Update 2026-10-22). |
| E-29 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-30 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-32 | gate | orchestrator | FAIL closure |
| E-33 | gate | orchestrator | FAIL closure |
| E-34 | gate | orchestrator | FAIL closure |
| E-39 | gate | orchestrator | FAIL closure |
| E-42 | gate | orchestrator | FAIL closure |
| E-46 | gate | orchestrator | FAIL closure |
| E-47 | hard-stop | orchestrator | R5 closure blocked: ledger row feat-local-4-csv-export-afbe8c91-MF-1 has a check that cannot pass. Its check runs export --out L (same path as --file L), and the fixed CLI refuses that with exit 2, so the && chain fails. Three fix rounds did not rewrite the check. Needed: a check that asserts the refusal (exit 2) and that a following add still works. Then verify all fixed rows and re-run R5, R6, … |
| E-48 | fix-commit | E1 | fix: MF-8 a directory at the ledger path is error exit 2 |
| E-49 | fix-commit | E1 | test: MF-8 a directory at the ledger path is error exit 2 (red) |
| E-50 | fix-commit | E1 | fix: MF-5 a closed output prints no traceback, with --out and with stdout closed |
| E-51 | fix-commit | E1 | test: MF-5 a closed output prints no traceback, with --out and with stdout closed (red) |
| E-52 | fix-commit | E1 | fix: F07 an unreadable ledger file is error exit 2 |
| E-53 | fix-commit | E1 | fix: MF-6 a stored row with a wrong value type is error exit 2 |
| E-54 | fix-commit | E1 | test: MF-6 a stored row with a wrong value type is error exit 2 (red) |
| E-55 | fix-commit | E1 | fix: MF-7 a deeply nested stored file is error exit 2 |
| E-56 | fix-commit | E1 | test: MF-7 a deeply nested stored file is error exit 2 (red) |
| E-57 | fix-commit | E1 | fix: F02 negative amounts print with the sign in front |
| E-58 | fix-commit | E1 | fix: F04 an unreadable ledger file is one error line, exit 2 |
| E-59 | fix-commit | E1 | fix: MF-4 a bad stored ledger row is one error line, exit 2 |
| E-60 | fix-commit | E1 | test: MF-4 a bad stored ledger row is error exit 2 (red) |
| E-61 | fix-commit | E1 | fix: MF-3 export to a closed pipe exits 1 without a traceback |
| E-62 | fix-commit | E1 | test: MF-3 export to a closed stdout pipe exits 1 without a traceback (red) |
| E-63 | fix-commit | E1 | fix: F03 export encodes the CSV once, before stdout or any file |
| E-64 | fix-commit | E1 | fix: MF-2 export --out encodes before it creates the file |
| E-65 | fix-commit | E1 | test: MF-2 export --out with an unencodable note writes no file (red) |
| E-66 | fix-commit | E1 | fix: MF-1 export --out refuses the ledger path before any write |
| E-67 | fix-commit | E1 | test: MF-1 export --out onto a missing ledger path is refused (red) |
