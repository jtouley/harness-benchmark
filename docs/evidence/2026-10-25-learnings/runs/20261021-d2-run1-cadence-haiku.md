RUN_BY_COMMAND: run-learnings
Run: 20261021-d2-run1-cadence-haiku
Cadence: unrecorded
Packet sha256: 3433d6ddeee611a4dd104c2c6603ab4bb8e4d47ccca22a9a55ecaf5b609d7c7e

# Learnings: 20261021-d2-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 29
- finding: 1
- fix-commit: 2
- gate: 25
- orchestrator-runner: 2
- stop-point: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-13, E-21
- Rule: gate-repeat
- Key: gate-repeat|cadence|adversarial-review-gate
- Change: Before the return, run the `adversarial-review-gate` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: adversarial-review verdict is request changes cycle; adversarial-review cycle limit reached # cycles.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-48, E-50
- Rule: gate-repeat
- Key: gate-repeat|pr-review-local|pr-review-local-gate
- Change: Before the return, run the `pr-review-local-gate` gate once and fix every class it names in one pass. In this run it failed 2 times in R1: pr-review-local no peer-written review of this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@unrecorded --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-48, E-50
- Rule: late-gate
- Key: late-gate|spec-driven|pr-review-local-gate|pr-review-local no peer-written
- Change: E1's phase gate runs the `pr-review-local-gate` measure `pr-review-local no peer-written` before E4, so the review phase does not find it first. It failed 2 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-8, E-10, E-15, E-18, E-34
- Rule: redispatch
- Key: redispatch|plan-review|P3
- Change: P3 was dispatched 5 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@unrecorded --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-9, E-12, E-14, E-17, E-20, E-22, E-28, E-31, E-33, E-35
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 10 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@unrecorded --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-11, E-16, E-19
- Rule: redispatch
- Key: redispatch|de-adversarial-reviewer|P6
- Change: P6 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@unrecorded --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-26, E-30, E-32
- Rule: redispatch
- Key: redispatch|test-benchmark|P7
- Change: P7 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@unrecorded --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-45, E-49
- Rule: redispatch
- Key: redispatch|pr-review-local|R1
- Change: R1 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@unrecorded --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-57, E-58
- Rule: orchestrator-runner
- Key: orchestrator-runner|cadence|runner
- Change: The orchestrator ran 2 project commands. It runs the manifest only; project commands run inside a block subagent or a gate.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-47, E-59, E-60
- Rule: review-finding
- Key: review-finding|spec-driven|core:standalone-package
- Change: E1 checks `core:standalone-package` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-8 | dispatch | P3 | /plan-review dispatched as P3 |
| E-9 | dispatch | P4 | /plan-update dispatched as P4 |
| E-10 | dispatch | P3 | /plan-review dispatched as P3 |
| E-11 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-12 | dispatch | P4 | /plan-update dispatched as P4 |
| E-13 | gate | orchestrator | FAIL adversarial-review-gate |
| E-14 | dispatch | P4 | /plan-update dispatched as P4 |
| E-15 | dispatch | P3 | /plan-review dispatched as P3 |
| E-16 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-17 | dispatch | P4 | /plan-update dispatched as P4 |
| E-18 | dispatch | P3 | /plan-review dispatched as P3 |
| E-19 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-20 | dispatch | P4 | /plan-update dispatched as P4 |
| E-21 | gate | orchestrator | FAIL adversarial-review-gate |
| E-22 | dispatch | P4 | /plan-update dispatched as P4 |
| E-26 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-28 | dispatch | P4 | /plan-update dispatched as P4 |
| E-30 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-31 | dispatch | P4 | /plan-update dispatched as P4 |
| E-32 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-33 | dispatch | P4 | /plan-update dispatched as P4 |
| E-34 | dispatch | P3 | /plan-review dispatched as P3 |
| E-35 | dispatch | P4 | /plan-update dispatched as P4 |
| E-45 | dispatch | R1 | /pr-review-local dispatched as R1 |
| E-47 | finding | R1 | Ledger read raises PermissionError (OSError) during export; _export catches only (ValueError, KeyError, TypeError). Repro: patched Path.read_text to raise PermissionError for ledger.json, main([--file, ledger.json, export]) gives traceback and exit 1, no error line. PR body states bad input exits 2 with one error line. Fix: add OSError to the except tuple and add an assert_refused test row for an… |
| E-48 | gate | R1 | FAIL pr-review-local-gate |
| E-49 | dispatch | R1 | /pr-review-local dispatched as R1 |
| E-50 | gate | R1 | FAIL pr-review-local-gate |
| E-57 | orchestrator-runner | orchestrator | cd /tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/d2-budgetcli (uv run --quiet pytest -q 2>&1 \|\| python3 -m pytest -q 2>&1) \| tail -8 echo "--- smoke" PYTHONPATH=src python3 -m budgetcli export --month 2026-10 2>&1 \| head -12; echo "exit ${PIPESTATUS[0]}" PYTHONPATH=src python3 -m budgetcli export --month 2026-13 2>&1 \| head -3; echo "bad-month exit ${PIPESTATUS[0]}" |
| E-58 | orchestrator-runner | orchestrator | cd /tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/d2-budgetcli grep -A3 "scripts" pyproject.toml uv run --quiet budgetcli export --month 2026-10 2>&1 \| head -12; echo "exit ${PIPESTATUS[0]}" |
| E-59 | fix-commit | E1 | fix: feat-local-4-csv-export-595b6f90-MF-1 export reports an unreadable ledger as one error line |
| E-60 | fix-commit | E1 | test: feat-local-4-csv-export-595b6f90-MF-1 unreadable ledger exits 2 with one error line (red) |
