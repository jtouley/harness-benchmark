RUN_BY_COMMAND: run-learnings
Run: 20261022-s3-run1-cadence-haiku
Cadence: cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5
Packet sha256: aa133bf872b09969222ce9e8300fb815fdf5adad3d9f0386fc940f640b3a4a9a

# Learnings: 20261022-s3-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 14
- finding: 8
- fix-commit: 10
- gate: 54
- hard-stop: 1
- orchestrator-runner: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-9, E-16
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-20, E-25
- Rule: gate-repeat
- Key: gate-repeat|cadence|deferral-register
- Change: Before the return, run the `deferral-register` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: deferral-register deferral-review no ruling of the; deferral-register deferral-review does not rule on as.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-22, E-26, E-28
- Rule: gate-repeat
- Key: gate-repeat|cadence|entry-invariant
- Change: Before the return, run the `entry-invariant` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: adversarial-review cycle limit reached # cycles; deferral-register deferral-review does not rule on as.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-68, E-70
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 2 times in spec-driven: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; fix step run r# without --check to.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-66
- Rule: late-gate
- Key: late-gate|spec-driven|pr-review-local-gate|pr-review-local no join
- Change: E1's phase gate runs the `pr-review-local-gate` measure `pr-review-local no join` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-67
- Rule: late-gate
- Key: late-gate|spec-driven|test-benchmark-gate-code|test-benchmark-pr no join
- Change: E1's phase gate runs the `test-benchmark-gate-code` measure `test-benchmark-pr no join` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-17, E-23, E-29
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-56, E-73
- Rule: redispatch
- Key: redispatch|test-benchmark|R2
- Change: R2 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-78
- Rule: orchestrator-runner
- Key: orchestrator-runner|cadence|runner
- Change: The orchestrator ran 1 project commands. It runs the manifest only; project commands run inside a block subagent or a gate.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-58, E-60, E-61, E-79, E-80, E-81, E-82, E-83, E-84, E-85, E-86, E-87, E-88
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-59, E-79, E-80, E-81, E-82, E-83, E-84, E-85, E-86, E-87, E-88
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-62, E-63, E-64, E-65, E-79, E-80, E-81, E-82, E-83, E-84, E-85, E-86, E-87, E-88
- Rule: review-finding
- Key: review-finding|spec-driven|core:test-benchmark
- Change: E1 checks `core:test-benchmark` before E4: the review found 4 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-13
- Target: commands/pr-review-update.md
- Status: candidate
- Evidence: E-77
- Rule: hard-stop
- Key: hard-stop|pr-review-update|R4|retries
- Change: R4 recorded a `retries` hard stop: r# final-consolidate open must-fix feat-local-#-csv-export-f# helper copies dry # . two fix. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-update@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=pr-review-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-9 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-16 | gate | orchestrator | FAIL plan-review-round: round 1 has 7 must-fix rows |
| E-17 | dispatch | P4 | /plan-update dispatched as P4 |
| E-20 | gate | orchestrator | FAIL deferral-register |
| E-22 | gate | orchestrator | FAIL entry-invariant |
| E-23 | dispatch | P4 | /plan-update dispatched as P4 |
| E-25 | gate | orchestrator | FAIL deferral-register |
| E-26 | gate | orchestrator | FAIL entry-invariant |
| E-28 | gate | orchestrator | FAIL entry-invariant |
| E-29 | dispatch | P4 | /plan-update dispatched as P4 |
| E-56 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-58 | finding | R1 | Stored amount_cents -5 exports as -1.95 (exit 0). Cents split with // and % gives a wrong value for a negative amount. ADR-0027 negative-number input. |
| E-59 | finding | R1 | A note with a lone surrogate (from --note with a non-UTF-8 argv byte, or a stored \ud800) makes export die with UnicodeEncodeError, exit 1, traceback. add accepts the same note. ADR-0027 text that does not encode. |
| E-60 | finding | R1 | export piped into a closed reader (export \| head -0) ends with BrokenPipeError traceback. ADR-0027 closed output pipe. |
| E-61 | finding | R1 | --out checks only resolve() equality, so a hard link to the ledger passes. export --out <hardlink> overwrites the ledger with CSV (data loss). Symlink case is caught (exit 2). ADR-0027 output path that is also an input. |
| E-62 | finding | R2 | No test renders a negative amount_cents. A stored amount_cents of -5 exports as -1.95 (exit 0), not -0.05. Add a parametrize row for each negative value in tests/test_export.py. Same defect as ledger row feat-local-4-csv-export-4154a99a-MF-1. |
| E-63 | finding | R2 | Closed stdout pipe: budgetcli export --month 2026-10 piped to head -0 prints a BrokenPipeError traceback and exits 1. No test covers a closed output pipe (ADR-0027 input class). Add a row to the export test in tests/test_cli_export.py. |
| E-64 | finding | R2 | Five acceptance files each copy the same cli() helper and BOOT string, and AC-1, AC-3 and AC-4 copy the same seed list. The change adds these copies. Merge them into one shared helper (ADR-0008 DRY). Scorecard DRY 5. |
| E-65 | finding | R2 | A stored note with a lone surrogate, for example a backslash-udc80 escape in the JSON, makes export fail with UnicodeEncodeError, exit 1, on stdout and on --out. No test covers it (ADR-0027 input class). Same defect as ledger row feat-local-4-csv-export-4154a99a-MF-2. |
| E-66 | gate | R1 | FAIL pr-review-local-gate |
| E-67 | gate | R2 | FAIL test-benchmark-gate-code |
| E-68 | gate | spec-driven | FAIL cognitive-complexity |
| E-70 | gate | spec-driven | FAIL cognitive-complexity |
| E-73 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-77 | hard-stop | orchestrator | R4 final-consolidate: open must-fix feat-local-4-csv-export-F01 (acceptance/ helper copies, DRY 5). Two fix rounds since R1: round 1 closed MF-1..4, F02, F03, F04 (awaiting verify); round 2 changed nothing. HEAD 0b51aa9. Draft PR open. R5, R6, R7 not run. |
| E-78 | orchestrator-runner | orchestrator | (python3 -m pytest -q 2>&1 \| tail -6); echo "PYTEST_EXIT=${PIPESTATUS[0]}"; printf 'x' >/dev/null; python3 -m budgetcli --help >/dev/null 2>&1; echo; ls src; cat README.md |
| E-79 | fix-commit | E1 | refactor: export CLI tests share helpers (R3 duplication, feat-local-4-csv-export-F04) |
| E-80 | fix-commit | E1 | fix: feat-local-4-csv-export-4154a99a-MF-4 out through hard link to ledger refused by samefile |
| E-81 | fix-commit | E1 | test: feat-local-4-csv-export-4154a99a-MF-4 out through hard link to ledger refused (red) |
| E-82 | fix-commit | E1 | fix: feat-local-4-csv-export-4154a99a-MF-3 feat-local-4-csv-export-F03 closed stdout pipe exits 1 without traceback |
| E-83 | fix-commit | E1 | test: feat-local-4-csv-export-4154a99a-MF-3 feat-local-4-csv-export-F03 closed stdout pipe exits without traceback (red) |
| E-84 | fix-commit | E1 | fix: feat-local-4-csv-export-4154a99a-MF-2 feat-local-4-csv-export-F04 unencodable note refused by add and export |
| E-85 | fix-commit | E1 | test: feat-local-4-csv-export-4154a99a-MF-2 unencodable note refused (red) |
| E-86 | fix-commit | E1 | fix: feat-local-4-csv-export-F02 feat-local-4-csv-export-4154a99a-MF-1 negative amount formats with sign |
| E-87 | fix-commit | E1 | test: feat-local-4-csv-export-4154a99a-MF-1 negative stored amount through export (red) |
| E-88 | fix-commit | E1 | test: feat-local-4-csv-export-F02 negative cents format with sign (red) |
