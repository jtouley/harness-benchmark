RUN_BY_COMMAND: run-learnings
Run: 20261021-c2-run1-cadence-sonnet
Cadence: unrecorded
Packet sha256: e07072b45743c1518ff6f2d5723d872d12c0c8c57dcc7baff428969aaefc2d56

# Learnings: 20261021-c2-run1-cadence-sonnet

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 18
- finding: 1
- fix-commit: 3
- gate: 36
- hard-stop: 1
- stop-refusal: 2

## Proposals

### L-1
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-43, E-44
- Rule: gate-repeat
- Key: gate-repeat|pr-review-local|pr-review-local-gate
- Change: Before the return, run the `pr-review-local-gate` gate once and fix every class it names in one pass. In this run it failed 2 times in R1: pr-review-local must-fix item mf-# of has no.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@unrecorded --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-50, E-51, E-53, E-54, E-58
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 5 times in orchestrator: feat-local-#-recurring-# must-fix status fixed not terminal.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-43, E-44
- Rule: late-gate
- Key: late-gate|spec-driven|pr-review-local-gate|pr-review-local must-fix item
- Change: E1's phase gate runs the `pr-review-local-gate` measure `pr-review-local must-fix item` before E4, so the review phase does not find it first. It failed 2 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-10, E-12, E-15, E-25
- Rule: redispatch
- Key: redispatch|plan-review|P3
- Change: P3 was dispatched 4 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@unrecorded --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-11, E-14, E-18
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@unrecorded --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-13, E-16
- Rule: redispatch
- Key: redispatch|de-adversarial-reviewer|P6
- Change: P6 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@unrecorded --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/commit-push-pr.md
- Status: candidate
- Evidence: E-36, E-38
- Rule: redispatch
- Key: redispatch|commit-push-pr|E4
- Change: E4 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=commit-push-pr@unrecorded --config new_skill=commit-push-pr@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-46, E-59, E-60, E-61
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-57
- Rule: hard-stop
- Key: hard-stop|cadence|R5|retries
- Change: R5 recorded a `retries` hard stop: r# mf-# is fixed in # and r# re-review is merge-ready but. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: SKILL.md
- Status: candidate
- Evidence: E-37
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in execution. continue
- Change: The hooks refused 1 times with `blocked early stop in execution. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: SKILL.md
- Status: candidate
- Evidence: E-56
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in review. continue
- Change: The hooks refused 1 times with `blocked early stop in review. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-10 | dispatch | P3 | /plan-review dispatched as P3 |
| E-11 | dispatch | P4 | /plan-update dispatched as P4 |
| E-12 | dispatch | P3 | /plan-review dispatched as P3 |
| E-13 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-14 | dispatch | P4 | /plan-update dispatched as P4 |
| E-15 | dispatch | P3 | /plan-review dispatched as P3 |
| E-16 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-18 | dispatch | P4 | /plan-update dispatched as P4 |
| E-25 | dispatch | P3 | /plan-review dispatched as P3 |
| E-36 | dispatch | E4 | /commit-push-pr dispatched as E4 |
| E-37 | stop-refusal | orchestrator | BLOCKED early stop in execution. Continue paceline: next E4 (draft-pr) via `/commit-push-pr --draft` |
| E-38 | dispatch | E4 | /commit-push-pr dispatched as E4 |
| E-43 | gate | R1 | FAIL pr-review-local-gate |
| E-44 | gate | R1 | FAIL pr-review-local-gate |
| E-46 | finding | R1 | RecurringStore.due_in duplicates the from_month <= month rule of merge_recurring; no src caller; only 2 tests use it |
| E-50 | gate | orchestrator | FAIL closure |
| E-51 | gate | orchestrator | FAIL closure |
| E-53 | gate | orchestrator | FAIL closure |
| E-54 | gate | orchestrator | FAIL closure |
| E-56 | stop-refusal | orchestrator | BLOCKED early stop in review. Continue paceline: next R5 (closure) via `python3 /tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin/scripts/closure.py` |
| E-57 | hard-stop | orchestrator | R5: MF-1 is fixed in 8e50c64 and R1 re-review is MERGE-READY, but its ledger check (-k dueIn) selects no tests (pytest exit 5), so ledger_verify cannot promote it. Fix budget used. A person must confirm with findings_io set-status --human --by <name>. |
| E-58 | gate | orchestrator | FAIL closure |
| E-59 | fix-commit | E1 | fix: MF-1 delete dead due_in, test the due rule on merge_recurring |
| E-60 | fix-commit | E1 | test: MF-1 due rule has one copy (red) |
| E-61 | fix-commit | E1 | fix: feat-local-3-recurring-expenses-F3 shared CLI helper checks no Traceback, one cannot-read assertion |
