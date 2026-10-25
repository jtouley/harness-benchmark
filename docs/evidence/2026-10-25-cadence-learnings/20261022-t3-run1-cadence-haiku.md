RUN_BY_COMMAND: run-learnings
Run: 20261022-t3-run1-cadence-haiku
Cadence: e51cde2a59d4a02c881de00c5629433face342f2
Packet sha256: c6cbadfaf4fa3cc72c773106be32a77c98ed8180f5760ca2c642be10e07dc277

# Learnings: 20261022-t3-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 8
- fix-commit: 18
- gate: 51
- hard-stop: 1
- stop-refusal: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-5, E-9
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-16, E-17
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|entry-invariant
- Change: Before the return, run the `entry-invariant` gate once and fix every class it names in one pass. In this run it failed 2 times in spec-driven: entry-invariant no cadence run in this worktree.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-34, E-48
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|test-benchmark-gate-code
- Change: Before the return, run the `test-benchmark-gate-code` gate once and fix every class it names in one pass. In this run it failed 2 times in test-benchmark: test-benchmark-code verdict is fail; test-benchmark-code must-fix dimensions below # assert.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-37, E-40, E-51, E-60
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|acceptance
- Change: Before the return, run the `acceptance` gate once and fix every class it names in one pass. In this run it failed 4 times in spec-driven: acceptance ac-# has an open defect the.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-38, E-58, E-59
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 3 times in spec-driven: fix step run r# without --check to; % duplicated # of # code lines; duplication.max_percent is # reuse the code that.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-41, E-53
- Rule: gate-repeat
- Key: gate-repeat|cadence|acceptance
- Change: Before the return, run the `acceptance` gate once and fix every class it names in one pass. In this run it failed 2 times in pr-review-update: acceptance ac-# has an open defect the.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-42, E-54, E-62, E-63, E-64, E-65, E-66, E-67, E-68, E-69, E-70, E-71, E-72, E-73, E-74, E-75, E-76, E-77, E-78, E-79
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-44, E-45, E-46, E-47, E-56, E-57, E-62, E-63, E-64, E-65, E-66, E-67, E-68, E-69, E-70, E-71, E-72, E-73, E-74, E-75, E-76, E-77, E-78, E-79
- Rule: review-finding
- Key: review-finding|spec-driven|references/review-rigor.md R2
- Change: E1 checks `references/review-rigor.md R2` before E4: the review found 6 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-61
- Rule: hard-stop
- Key: hard-stop|cadence|orchestrator|retries
- Change: orchestrator recorded a `retries` hard stop: pr review loop did not converge after # fix rounds r# test-quality. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: SKILL.md
- Status: candidate
- Evidence: E-49
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 1 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@e51cde2a59d4a02c881de00c5629433face342f2 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-5 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-9 | gate | orchestrator | FAIL plan-review-round: round 1 has 9 must-fix rows |
| E-16 | gate | spec-driven | FAIL entry-invariant |
| E-17 | gate | spec-driven | FAIL entry-invariant |
| E-34 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-37 | gate | spec-driven | FAIL acceptance |
| E-38 | gate | spec-driven | FAIL cognitive-complexity |
| E-40 | gate | spec-driven | FAIL acceptance |
| E-41 | gate | pr-review-update | FAIL acceptance |
| E-42 | finding | pr-review-update | export without --out writes the text to stdout with no encode guard: a note holding a lone surrogate (U+D800) raises UnicodeEncodeError, traceback, exit 1 at HEAD e49dadd. The MF-2 fix covers only --out. The R4 round before this one said the stdout path does not crash; that was wrong here (reproduced at e90b55b and e49dadd). |
| E-44 | finding | test-benchmark | note with lone surrogate: export --out gives UnicodeEncodeError traceback, exit 1; stdout exits 0 on the same input |
| E-45 | finding | test-benchmark | A stored row with a value of the wrong type is accepted and printed as a wrong value, exit 0. amount_cents 12.5 prints 2026-10-02,food,0.12. amount_cents true prints 0.01. category 5 prints 5. note ["a"] prints the Python list text. Expected: error: line and exit 2 (review-rigor.md adversarial list: a value of the wrong type). Only NaN and text amount_cents are tested. |
| E-46 | finding | test-benchmark | Closed-pipe test asserts only that no Traceback text is in stderr. Mutant src/budgetcli/cli.py:25 (os.dup2 line removed) survives: python3 -m pytest -q passes. Mutant cli.py:26 (return 1 changed to return 0) survives: the exit code is never asserted. Fix: assert the exit code and that stderr is empty, in this test or in a parametrize table. |
| E-47 | finding | test-benchmark | Mutant ledger.py:29 with TypeError removed from the except tuple survives: python3 -m pytest -q passes. The TypeError branch has no input. Input [5] (a row that is an int) gives error: line, exit 2 on HEAD. Fix: add [5] and a day of null to the bad-row parametrize table in tests/test_export.py. |
| E-48 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-49 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 3 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-51 | gate | spec-driven | FAIL acceptance |
| E-53 | gate | pr-review-update | FAIL acceptance |
| E-54 | finding | pr-review-update | totals calls Ledger.load, which raises ValueError for a stored float, bool, number category or list note (F05 fix). totals does not catch it: traceback, exit 1 (12.5 amount). At e49dadd the same row printed a wrong total with exit 0. export and add give an error: line and exit 2. Same reader as MF-3. |
| E-56 | finding | test-benchmark | Surviving mutant: ledger.py:117 day slice, date.fromisoformat(day) replaced by date.fromisoformat(day[:10]); python3 -m pytest -q passes (38 passed). Input: stored day "2026-10-02T10:00". HEAD gives error: line and exit 2 (Invalid isoformat string). The mutant gives a row printed as 2026-10-02 with exit 0. No row in the bad-row parametrize table of tests/test_export.py holds a malformed day. Fix:… |
| E-57 | finding | test-benchmark | Surviving mutant: cli.py:21 sys.stdout.flush() removed (replaced by pass); python3 -m pytest -q passes (38 passed). In the closed-pipe scenario of test_export_to_a_closed_pipe_prints_no_traceback the mutant gives the same result as HEAD (exit 1, empty stderr), so the test does not show that the flush inside the BrokenPipeError handler ran. The EPIPE path is not pinned, and the earlier card noted … |
| E-58 | gate | spec-driven | FAIL cognitive-complexity |
| E-59 | gate | spec-driven | FAIL cognitive-complexity |
| E-60 | gate | spec-driven | FAIL acceptance |
| E-61 | hard-stop | orchestrator | PR review loop did not converge after 3 fix rounds: R2 test-quality holds assert at 6 (needs 7) in every round; R4 consolidate has open must-fix F08 and F09; R3 scans untracked .context/ scratch files (repro_MF.py) because .context/ is not in .gitignore. Draft PR is open. Resume with: activate_session.py --from-branch --resume |
| E-62 | fix-commit | E1 | fix: feat-local-4-csv-export-5f5b7546-MF-6 totals of a bad stored row is an error line |
| E-63 | fix-commit | E1 | test: feat-local-4-csv-export-5f5b7546-MF-6 totals of a bad stored row is an error line (red) |
| E-64 | fix-commit | E1 | fix: feat-local-4-csv-export-MF-5 export to stdout refuses text that is not UTF-8 |
| E-65 | fix-commit | E1 | test: feat-local-4-csv-export-MF-5 export to stdout refuses text that is not UTF-8 (red) |
| E-66 | fix-commit | E1 | fix: feat-local-4-csv-export-F05 a stored value of the wrong type is an error line |
| E-67 | fix-commit | E1 | test: feat-local-4-csv-export-F05 stored value of the wrong type is an error line (red) |
| E-68 | fix-commit | E1 | fix: feat-local-4-csv-export-F06 drop the devnull guard that no run observes |
| E-69 | fix-commit | E1 | test: feat-local-4-csv-export-F07 non-object row and null day are error lines |
| E-70 | fix-commit | E1 | test: feat-local-4-csv-export-F06 closed pipe asserts exit 1 and empty stderr |
| E-71 | fix-commit | E1 | fix: feat-local-4-csv-export-5f5b7546-MF-4 export to a closed pipe exits without a traceback |
| E-72 | fix-commit | E1 | test: feat-local-4-csv-export-5f5b7546-MF-4 export to a closed pipe prints no traceback (red) |
| E-73 | fix-commit | E1 | fix: feat-local-4-csv-export-5f5b7546-MF-3 a bad stored row is an error line and exit 2 |
| E-74 | fix-commit | E1 | test: feat-local-4-csv-export-5f5b7546-MF-3 a bad stored row is an error line (red) |
| E-75 | fix-commit | E1 | fix: feat-local-4-csv-export-5f5b7546-MF-2 export --out encodes before it opens the file |
| E-76 | fix-commit | E1 | test: feat-local-4-csv-export-5f5b7546-MF-2 export --out refuses a note that is not UTF-8 (red) |
| E-77 | fix-commit | E1 | fix: feat-local-4-csv-export-5f5b7546-MF-1 negative amounts keep the sign and the value |
| E-78 | fix-commit | E1 | test: feat-local-4-csv-export-5f5b7546-MF-1 negative amount keeps its value (red) |
| E-79 | fix-commit | E1 | test: feat-local-4-csv-export-F01 parse_month pins months 01 and 12 |
