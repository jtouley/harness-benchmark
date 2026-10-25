RUN_BY_COMMAND: run-learnings
Run: 20261021-arm-b-cadence-haiku
Cadence: db1bedea9cca31d219953b1c728b009983aeb9a5
Packet sha256: f1b074cece10704610e6afd0b33cdff6f50ed21f490d01ae3ca040f85ce3a33d

# Learnings: 20261021-arm-b-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 3
- fix-commit: 5
- gate: 48
- stop-point: 1
- stop-refusal: 5

## Proposals

### L-1
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-25, E-34, E-35
- Rule: gate-repeat
- Key: gate-repeat|pr-review-local|pr-review-local-gate
- Change: Before the return, run the `pr-review-local-gate` gate once and fix every class it names in one pass. In this run it failed 3 times in pr-review-local: pr-review-local no peer-written review of this run; pr-review-local no artifact matching.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-26, E-27, E-29, E-30
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|test-benchmark-gate-code
- Change: Before the return, run the `test-benchmark-gate-code` gate once and fix every class it names in one pass. In this run it failed 4 times in test-benchmark: test-benchmark-code verdict is fail must-fix finding #-#a#-#d-b#c-#-f; test-benchmark-code verdict is fail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-45, E-48, E-50, E-53, E-55, E-57
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 6 times in orchestrator: feat-local-#-csv-# must-fix status fixed not terminal; feat-local-#-csv-export-f# must-fix status fixed not terminal.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-28, E-58, E-59, E-60, E-61, E-62
- Rule: review-finding
- Key: review-finding|spec-driven|skills/test-benchmark/SKILL.md
- Change: E1 checks `skills/test-benchmark/SKILL.md` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-32, E-33, E-58, E-59, E-60, E-61, E-62
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-10
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in execution. continue
- Change: The hooks refused 1 times with `blocked early stop in execution. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: SKILL.md
- Status: candidate
- Evidence: E-31
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 1 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: SKILL.md
- Status: candidate
- Evidence: E-49, E-54, E-56
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in review. continue
- Change: The hooks refused 3 times with `blocked early stop in review. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|cadence|R5|stopped at r# three findings
- Change: The run stopped at R5: stopped at r# three findings stayed fixed not verified. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@db1bedea9cca31d219953b1c728b009983aeb9a5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | R5 | stopped at R5: three findings stayed fixed, not verified |
| E-10 | stop-refusal | orchestrator | BLOCKED early stop in execution. Continue E1: send the `/spec-driven` peer the plan again. Its next open phase is phase 1 (CSV text in the ledger module). |
| E-25 | gate | pr-review-local | FAIL pr-review-local-gate |
| E-26 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-27 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-28 | finding | test-benchmark | _export prints text.count(CRLF) - 1 as the row count. A note with CRLF inflates the count: export --month 2026-10 --out o.csv prints 4 for 3 data rows. No test covers a CRLF note. Fix: count the rows written, add a parametrize row with a CRLF note. |
| E-29 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-30 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-31 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-32 | finding | pr-review-local | export --out prints text.count("\r\n") - 1, which counts a CRLF inside a quoted note. Repro: add --amount 3 --note $'a\r\nb' then export --month 2026-10 --out FILE prints 2 for one row. Expected 1. See .context/prs/reviews/PR_REVIEW_1.md Reproductions R-2. |
| E-33 | finding | pr-review-local | export raises decimal.InvalidOperation (traceback, exit 1) for a stored amount that add accepts, such as 1e999. main catches only ValueError. The request says a bad input is an error: line and exit 2, never a traceback. See .context/prs/reviews/PR_REVIEW_1.md Reproductions R-3. |
| E-34 | gate | pr-review-local | FAIL pr-review-local-gate |
| E-35 | gate | pr-review-local | FAIL pr-review-local-gate |
| E-45 | gate | orchestrator | FAIL closure |
| E-48 | gate | orchestrator | FAIL closure |
| E-49 | stop-refusal | orchestrator | BLOCKED early stop in review. Continue paceline: next R5 (closure) via `python3 /tmp/claude-0/-home-user/c6d1ea46-c870-51fa-ab2e-339fb5a9722d/scratchpad/xp/cadence-b/scripts/closure.py` |
| E-50 | gate | orchestrator | FAIL closure |
| E-53 | gate | orchestrator | FAIL closure |
| E-54 | stop-refusal | orchestrator | BLOCKED early stop in review. Continue paceline: next R5 (closure) via `python3 /tmp/claude-0/-home-user/c6d1ea46-c870-51fa-ab2e-339fb5a9722d/scratchpad/xp/cadence-b/scripts/closure.py` |
| E-55 | gate | orchestrator | FAIL closure |
| E-56 | stop-refusal | orchestrator | BLOCKED early stop in review. Continue paceline: next R5 (closure) via `python3 /tmp/claude-0/-home-user/c6d1ea46-c870-51fa-ab2e-339fb5a9722d/scratchpad/xp/cadence-b/scripts/closure.py` |
| E-57 | gate | orchestrator | FAIL closure |
| E-58 | fix-commit | E1 | refactor: feat-local-4-csv-export-MF-2 share the error-line assertion |
| E-59 | fix-commit | E1 | fix: feat-local-4-csv-export-MF-2 export prints an error line for an unrenderable amount |
| E-60 | fix-commit | E1 | test: feat-local-4-csv-export-MF-2 export of an unrenderable stored amount is an error line (red) |
| E-61 | fix-commit | E1 | fix: feat-local-4-csv-export-F01 count the rows written, not CRLF pairs |
| E-62 | fix-commit | E1 | test: feat-local-4-csv-export-F01 CRLF note counts one row (red) |
