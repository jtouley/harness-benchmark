RUN_BY_COMMAND: run-learnings
Run: 20261024-P2-cadence-haiku-core-4
Cadence: 2100c6e6aa99d99309cfa8e7f8c5cee1018584b4
Packet sha256: d1e9c85e771824821423b9d2b7312fef08fac70d57f0ce9479f9865234012b33

# Learnings: 20261024-P2-cadence-haiku-core-4

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- after-document: 7
- dispatch: 8
- finding: 5
- fix-commit: 1
- free-form-dispatch: 1
- gate: 32
- stop-point: 1
- stop-refusal: 3

## Proposals

### L-1
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-15, E-18, E-21
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 3 times in E1: limit is # split each function or; fix step run r# without --check to; changed code file s not measured.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-43, E-45, E-46
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: must-fix status open not terminal it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-30, E-30
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|bugs s# audit
- Change: E1's phase gate runs the `cognitive-complexity` measure `bugs s# audit` before E4, so the review phase does not find it first. It failed 2 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-30
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|bugs s# standard
- Change: E1's phase gate runs the `cognitive-complexity` measure `bugs s# standard` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-30
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|bugs.max is
- Change: E1's phase gate runs the `cognitive-complexity` measure `bugs.max is` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-37
- Rule: free-form-dispatch
- Key: free-form-dispatch|cadence|free-form
- Change: The orchestrator sent 1 free-form subagent prompts. Dispatch each block and the fix round only from its packet (`/<command>` with the Block line).
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-31, E-33, E-34, E-35, E-58
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 4 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-32, E-58
- Rule: review-finding
- Key: review-finding|spec-driven|core:plan-conformance
- Change: E1 checks `core:plan-conformance` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-43, E-45, E-46
- Rule: open-at-close
- Key: open-at-close|pr-review-local|open-must-fix
- Change: The fix round returns only after `ledger_verify.py` marks each fixed must-fix item verified; R5 found open must-fix items 3 times.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: SKILL.md
- Status: candidate
- Evidence: E-47, E-49, E-50
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in execution. progress
- Change: The hooks refused 3 times with `blocked early stop in execution. progress`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: commands/commit-push-pr.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|commit-push-pr|E4|open at e# draft-pr the
- Change: The run stopped at E4: open at e# draft-pr the stop hook refused the stop # times fail no. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=commit-push-pr@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=commit-push-pr@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: commands/commit-push-pr.md
- Status: candidate
- Evidence: E-55
- Rule: after-document
- Key: after-document|commit-push-pr|E4
- Change: E4 made 3 tool calls after it wrote its document. The block writes its document last and then returns.
- Eval: pending. python -m revieweval.compare layout --config old_skill=commit-push-pr@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=commit-push-pr@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-13
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-56
- Rule: after-document
- Key: after-document|pr-review-local|R1
- Change: R1 made 3 tool calls after it wrote its document. The block writes its document last and then returns.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | E4 | open at E4 (draft-pr): the Stop hook refused the stop 3 times (FAIL no active cadence session) |
| E-15 | gate | E1 | FAIL cognitive-complexity |
| E-18 | gate | E1 | FAIL cognitive-complexity |
| E-21 | gate | E1 | FAIL cognitive-complexity |
| E-30 | gate | R1 | FAIL cognitive-complexity |
| E-31 | finding | R1 | read_file_source reads only paths[0] for csv and sitematrix_json, but load.source_files and load.source_sha256 cover every matched file. With data/raw/part*.csv matching part1.csv (2 rows) and part2.csv (1 row), it read 2 rows, not 3, and the metadata lists both files. |
| E-32 | finding | R1 | batch_size: 500 passes the schema, but no code reads it. cli.stream passes batch_size=None to default_handlers, and stream_micro_batch_sink takes its size only from that argument. With batch_size: 1 in a copy of the YAML the sink still commits in 500-row batches. Spec A-20 needs YAML-only extension, so a YAML key that does nothing breaks that rule. |
| E-33 | finding | R1 | R3 bugs record fails: ruff S310 at engine/sse.py:60 and :62 (URL opened without a scheme check), and S311 at tests/conftest.py:151. bugs.max is 0. |
| E-34 | finding | R1 | R3 types record fails: mypy var-annotated at tests/test_oracle.py lines 14, 18, 26, 50, 76, 77, 82, 109, 116, 129, 135. types.max is 0. |
| E-35 | finding | R1 | test_late_events_published_to_marts ends with assert len(published) > 0, a partial-success threshold. The test already checks published == lake_late, but a published set that is non-empty and wrong still passes the len check when the fixture is changed. The contract forbids partial-success thresholds. |
| E-37 | free-form-dispatch | orchestrator | Fix round for R1 must-fix items |
| E-43 | gate | orchestrator | FAIL closure |
| E-45 | gate | orchestrator | FAIL closure |
| E-46 | gate | orchestrator | FAIL closure |
| E-47 | stop-refusal | orchestrator | BLOCKED early stop in execution. Progress unknown (run 92fc64a0-d0dd-4e2b-b30d-d4702591cbaf): a gate timed out or could not run. Continue paceline: next E4 (draft-pr) via `/commit-push-pr --draft` |
| E-49 | stop-refusal | orchestrator | BLOCKED early stop in execution. Progress unknown (run 92fc64a0-d0dd-4e2b-b30d-d4702591cbaf): a gate timed out or could not run. Continue paceline: next E4 (draft-pr) via `/commit-push-pr --draft` |
| E-50 | stop-refusal | orchestrator | BLOCKED early stop in execution. Progress unknown (run 92fc64a0-d0dd-4e2b-b30d-d4702591cbaf): a gate timed out or could not run. Continue paceline: next E4 (draft-pr) via `/commit-push-pr --draft` |
| E-55 | after-document | E4 | 3 tool calls after the block wrote its document |
| E-56 | after-document | R1 | 3 tool calls after the block wrote its document |
| E-58 | fix-commit | E1 | fix: fail closed on multi-match single-file sources, honor YAML batch_size, clear R3 findings |
