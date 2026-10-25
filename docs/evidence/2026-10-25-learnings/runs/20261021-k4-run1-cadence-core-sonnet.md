RUN_BY_COMMAND: run-learnings
Run: 20261021-k4-run1-cadence-core-sonnet
Cadence: unrecorded
Packet sha256: 3889880e35515b0e1866d370090025e7f111b44592e8ecc76932f78cf0f5bd79

# Learnings: 20261021-k4-run1-cadence-core-sonnet

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 1
- fix-commit: 2
- gate: 24
- hard-stop: 1
- stop-refusal: 3

## Proposals

### L-1
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-13, E-15, E-17, E-18
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 4 times in spec-driven: types operator unsupported operand types for >; types.max is # fix each mypy finding; fix step run r# without --check to.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-9, E-30, E-31
- Rule: review-finding
- Key: review-finding|spec-driven|skills/test-benchmark/SKILL.md#dry
- Change: E1 checks `skills/test-benchmark/SKILL.md#dry` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-29
- Rule: hard-stop
- Key: hard-stop|cadence|R5|retries
- Change: R5 recorded a `retries` hard stop: r# closure blocked f# is fixed but its ledger check is invalid. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: SKILL.md
- Status: candidate
- Evidence: E-25, E-26
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 2 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: SKILL.md
- Status: candidate
- Evidence: E-27
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in review. continue
- Change: The hooks refused 1 times with `blocked early stop in review. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-9 | finding | test-benchmark | Plan test spec lists about 25 near-identical cases with no parametrize tables and no shared exit-2/error:/no-Traceback helper. See .context/benchmarks/feat-local-3-recurring-expenses_plan.json |
| E-13 | gate | spec-driven | FAIL cognitive-complexity |
| E-15 | gate | spec-driven | FAIL cognitive-complexity |
| E-17 | gate | spec-driven | FAIL cognitive-complexity |
| E-18 | gate | spec-driven | FAIL cognitive-complexity |
| E-25 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 993 characters; the limit is 300. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-26 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 490 characters; the limit is 300. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-27 | stop-refusal | orchestrator | BLOCKED early stop in review. Continue paceline: next R5 (closure) via `python3 /tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/core-plugin/scripts/closure.py` |
| E-29 | hard-stop | orchestrator | R5 closure blocked: F01 is fixed but its ledger check is invalid sh, so ledger_verify cannot mark it verified; append rejects a duplicate id and direct ledger writes are hook-blocked. Needs a person to confirm F01 (set-status --human) or repair the row. |
| E-30 | fix-commit | E1 | fix: feat-local-3-recurring-expenses-F01 share one clean-error assertion helper |
| E-31 | fix-commit | E1 | test: feat-local-3-recurring-expenses-F01 shared clean-error helper (red) |
