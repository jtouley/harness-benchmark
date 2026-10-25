RUN_BY_COMMAND: run-learnings
Run: 20261021-k3-run1-cadence-core-sonnet
Cadence: unrecorded
Packet sha256: 00545628cf9a38092d39034815845a89a9c6cfd6287c8eb0af3625d00f31a7c9

# Learnings: 20261021-k3-run1-cadence-core-sonnet

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 3
- fix-commit: 4
- gate: 23
- hard-stop: 2
- stop-refusal: 5

## Proposals

### L-1
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-4, E-6
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 2 times in spec-driven: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; fix step run r# without --check to.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-17, E-19, E-21, E-22
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|test-benchmark-gate-code
- Change: Before the return, run the `test-benchmark-gate-code` gate once and fix every class it names in one pass. In this run it failed 4 times in test-benchmark: helpers_reimplemented no under the test directories set; computes these lists import the conftest helper; test-benchmark-code must-fix dimensions below # dry.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@unrecorded --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-24, E-25, E-26, E-29, E-33
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 5 times in orchestrator: feat-local-#-recurring-expenses-f# must-fix status fixed not terminal.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-12, E-13, E-34, E-35, E-36, E-37
- Rule: review-finding
- Key: review-finding|spec-driven|test-benchmark:mutation-resilience
- Change: E1 checks `test-benchmark:mutation-resilience` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-18, E-34, E-35, E-36, E-37
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-31
- Rule: hard-stop
- Key: hard-stop|cadence|R5|retries
- Change: R5 recorded a `retries` hard stop: r# closure f# is fixed but its recorded check python# --change is. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: SKILL.md
- Status: candidate
- Evidence: E-32
- Rule: hard-stop
- Key: hard-stop|cadence|R5|retries
- Change: R5 recorded a `retries` hard stop: r# closure finding f# is fixed but its recorded check command is. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: SKILL.md
- Status: candidate
- Evidence: E-15, E-16, E-20, E-28
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 4 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-30
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in review. continue
- Change: The hooks refused 1 times with `blocked early stop in review. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-4 | gate | spec-driven | FAIL cognitive-complexity |
| E-6 | gate | spec-driven | FAIL cognitive-complexity |
| E-12 | finding | test-benchmark | 4 mutants of _parse_item survive (amount<=0, id<1, day range, bool as int); add parametrize rows |
| E-13 | finding | test-benchmark | mutants survive: parse_amount 1e15 cap removed, parse_category CR check removed; add REJECTED rows |
| E-15 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 308 characters; the limit is 300. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-16 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 10 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-17 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-18 | finding | test-benchmark | test_shape.py helpers_reimplemented did not run: no conftest.py under tests/. The strict profile fails an unmeasured measure, so the R2 gate fails. The literal l.json.recurring.json repeats 6 times in tests/test_cli_recurring.py and tests/test_recurring.py. Add tests/conftest.py with the shared helper, or set test_shape.layout.conftest. |
| E-19 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-20 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 14 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-21 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-22 | gate | test-benchmark | FAIL test-benchmark-gate-code |
| E-24 | gate | orchestrator | FAIL closure |
| E-25 | gate | orchestrator | FAIL closure |
| E-26 | gate | orchestrator | FAIL closure |
| E-28 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 8 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-29 | gate | orchestrator | FAIL closure |
| E-30 | stop-refusal | orchestrator | BLOCKED early stop in review. Continue paceline: next R5 (closure) via `python3 /tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/core-plugin/scripts/closure.py` |
| E-31 | hard-stop | orchestrator | R5 closure: F04 is fixed but its recorded check (python3 scripts/test_shape.py --change) is a relative path that does not resolve in this repo, so ledger_verify cannot promote it. Fix rounds are used up and two fix peers left the check unchanged. Fix needs a correction of the ledger check by the user. |
| E-32 | hard-stop | orchestrator | R5 closure: finding F04 is fixed, but its recorded check command is a relative path that does not resolve in this repo, so the ledger verify step cannot promote it. Fix rounds are used up and two fix peers left the check unchanged. The ledger check needs a correction by the user. |
| E-33 | gate | orchestrator | FAIL closure |
| E-34 | fix-commit | E1 | fix: feat-local-3-recurring-expenses-F04 shared sidecar_path fixture in tests/conftest.py |
| E-35 | fix-commit | E1 | test: feat-local-3-recurring-expenses-F04 shared sidecar_path fixture (red) |
| E-36 | fix-commit | E1 | test: feat-local-3-recurring-expenses-F02 amount cap and CR category rejected (red against mutants) |
| E-37 | fix-commit | E1 | test: feat-local-3-recurring-expenses-F01 _parse_item rejects bad amount, id, day, bool (red against mutants) |
