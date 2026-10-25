RUN_BY_COMMAND: run-learnings
Run: 20261024-P2-cadence-haiku-full-5
Cadence: 2100c6e6aa99d99309cfa8e7f8c5cee1018584b4
Packet sha256: 64ee1078e8322a076751ed53f3d8bd6c5cf1ce7a550298873746a21379330aeb

# Learnings: 20261024-P2-cadence-haiku-full-5

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- after-document: 11
- dispatch: 12
- finding: 16
- fix-commit: 13
- free-form-dispatch: 3
- gate: 34
- hard-stop: 1
- orchestrator-runner: 1
- stop-point: 1
- stop-refusal: 1

## Proposals

### L-1
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-27, E-28, E-30
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 3 times in E1: % duplicated # of # code lines; changed code file s not measured; fail cognitive-complexity.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-65, E-68
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: spec-f# must-fix status open not terminal it; must-fix status open not terminal it; acceptance item # is not passed python.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-39
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|types mypy report
- Change: E1's phase gate runs the `cognitive-complexity` measure `types mypy report` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-39
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|types.max is
- Change: E1's phase gate runs the `cognitive-complexity` measure `types.max is` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-39
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|fix step delegate
- Change: E1's phase gate runs the `cognitive-complexity` measure `fix step delegate` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-53
- Rule: late-gate
- Key: late-gate|spec-driven|test-benchmark-gate-code|test-benchmark-code must-fix dimensions
- Change: E1's phase gate runs the `test-benchmark-gate-code` measure `test-benchmark-code must-fix dimensions` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-48, E-55, E-59
- Rule: redispatch
- Key: redispatch|test-benchmark|R2
- Change: R2 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: SKILL.md
- Status: candidate
- Evidence: E-47, E-54, E-58
- Rule: free-form-dispatch
- Key: free-form-dispatch|cadence|free-form
- Change: The orchestrator sent 3 free-form subagent prompts. Dispatch each block and the fix round only from its packet (`/<command>` with the Block line).
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-63
- Rule: orchestrator-runner
- Key: orchestrator-runner|cadence|runner
- Change: The orchestrator ran 1 project commands. It runs the manifest only; project commands run inside a block subagent or a gate.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-12, E-13, E-14, E-81, E-82, E-83, E-84, E-85, E-86, E-87, E-88, E-89, E-90, E-91, E-92, E-93
- Rule: review-finding
- Key: review-finding|spec-driven|test-benchmark:plan
- Change: E1 checks `test-benchmark:plan` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-40, E-41, E-81, E-82, E-83, E-84, E-85, E-86, E-87, E-88, E-89, E-90, E-91, E-92, E-93
- Rule: review-finding
- Key: review-finding|spec-driven|R3:types
- Change: E1 checks `R3:types` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-42, E-43, E-81, E-82, E-83, E-84, E-85, E-86, E-87, E-88, E-89, E-90, E-91, E-92, E-93
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-13
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-44, E-45, E-81, E-82, E-83, E-84, E-85, E-86, E-87, E-88, E-89, E-90, E-91, E-92, E-93
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-14
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-49, E-50, E-51, E-52, E-56, E-57, E-81, E-82, E-83, E-84, E-85, E-86, E-87, E-88, E-89, E-90, E-91, E-92, E-93
- Rule: review-finding
- Key: review-finding|spec-driven|test-benchmark:code
- Change: E1 checks `test-benchmark:code` before E4: the review found 6 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-15
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-64, E-81, E-82, E-83, E-84, E-85, E-86, E-87, E-88, E-89, E-90, E-91, E-92, E-93
- Rule: review-finding
- Key: review-finding|spec-driven|spec-gap
- Change: E1 checks `spec-gap` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-16
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-65
- Rule: open-at-close
- Key: open-at-close|pr-review-local|open-must-fix
- Change: The fix round returns only after `ledger_verify.py` marks each fixed must-fix item verified; R5 found open must-fix items 1 times.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-17
- Target: SKILL.md
- Status: candidate
- Evidence: E-69
- Rule: hard-stop
- Key: hard-stop|cadence|R5|retries
- Change: R5 recorded a `retries` hard stop: r# closure fails. items # and # name but the tests live. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-18
- Target: SKILL.md
- Status: candidate
- Evidence: E-66
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in execution. progress
- Change: The hooks refused 1 times with `blocked early stop in execution. progress`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-19
- Target: SKILL.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|cadence|R5|hard stop retries r# closure
- Change: The run stopped at R5: hard stop retries r# closure fails. items # and # name but the tests. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-20
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-72
- Rule: after-document
- Key: after-document|test-benchmark|P7
- Change: P7 made 3 tool calls after it wrote its document. The block writes its document last and then returns.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-21
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-75
- Rule: after-document
- Key: after-document|plan-update|P4
- Change: P4 made 3 tool calls after it wrote its document. The block writes its document last and then returns.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-22
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-77
- Rule: after-document
- Key: after-document|pr-review-local|R1
- Change: R1 made 4 tool calls after it wrote its document. The block writes its document last and then returns.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-23
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-80
- Rule: after-document
- Key: after-document|test-benchmark|R2
- Change: R2 made 3 tool calls after it wrote its document. The block writes its document last and then returns.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | R5 | hard stop retries: R5 closure fails. Items 5 and 6 name tests/test_checks.py, but the tests live in tests/test_stream_checks.py (spec-F12). Findings spec-F01 to spec-F03 check scripts/test_benchmark_gate.py, which is missing from the repo. No retries left. (FAIL no active cadence session) |
| E-12 | finding | P7 | Plan test spec: no shared home for fixture zips, SSE fake or stream fixture (dry 6). Source: .context/benchmarks/spec_plan.json spec-F01 |
| E-13 | finding | P7 | Plan test spec: checks 1-7 are computed from marts or a fixed fixture with no independent expected values (assertions 6). Source: .context/benchmarks/spec_plan.json spec-F02 |
| E-14 | finding | P7 | Plan test spec: Assumptions cite tests (test_new_source_needs_yaml_only, test_make_targets_call_engine, test_error_names_file_line_problem, test_money_columns_are_decimal in test_marts.py) that no phase plans or places. Source: .context/benchmarks/spec_plan.json spec-F03 |
| E-27 | gate | E1 | FAIL cognitive-complexity |
| E-28 | gate | E1 | FAIL cognitive-complexity |
| E-30 | gate | E1 | FAIL cognitive-complexity |
| E-39 | gate | R1 | FAIL cognitive-complexity |
| E-40 | finding | R1 | R3 types record fails: mypy fatal Source file found twice under different module names oracle and tests.oracle (tests/oracle.py). Add tests/__init__.py. |
| E-41 | finding | R1 | mypy var-annotated on added lines: engine/stream_source.py:60, engine/stream_store.py:66 (x2), tests/oracle.py:66,73,80,91. Annotate the containers. |
| E-42 | finding | R1 | R2 helpers_reimplemented 1: local write_pipeline copies tests/conftest.py:185. Use the conftest fixture. |
| E-43 | finding | R1 | R2 thin_files 1: tests/test_lake.py has 2 tests of engine/run.py also tested by tests/test_engine_schema.py. Move them into test_engine_schema.py. |
| E-44 | finding | R1 | One invalid UTF-8 message raises UnicodeDecodeError and aborts the stream run. DECISIONS.md says malformed and cut messages are skipped with a warning; no test covers the cut case. Repro: /tmp/rv-repro/repro_stream.py. |
| E-45 | finding | R1 | A JSON message that is not an event object (data: 42) or lacks meta.dt aborts the run at commit (TypeError, KeyError). Check the event shape in decode() and skip with a warning. Repro: /tmp/rv-repro/repro_commit.py. |
| E-47 | free-form-dispatch | orchestrator | Fix R1 must-fix items round |
| E-48 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-49 | finding | R2 | _tree_hash (test_star.py) and hash_tree (test_engine_schema.py) are one sha256 tree-hash helper under two names. Gate helpers_reimplemented is 0 because it compares only with conftest. DRY score 6. Source: .context/benchmarks/spec_code.json spec-code-F01 |
| E-50 | finding | R2 | Stream tests sit in test_marts.py and test_checks.py. Makefile target tests and an end-to-end make run sit in test_engine_schema.py and test_star.py beside unit checks. Layer score 6. Source: .context/benchmarks/spec_code.json spec-code-F02 |
| E-51 | finding | R2 | Corrupt zip (non-zip bytes) raises BadZipFile File is not a zip file with no file name. No test covers a corrupt zip. Failure paths score 6. Source: .context/benchmarks/spec_code.json spec-code-F03 |
| E-52 | finding | R2 | Mutant running_max_ms = event_ms (instead of max) survives tests/test_stream.py and is killed only by the dbt-backed check 5 test. Mutant WINDOW_MS 6 min also survives the unit layer. Source: .context/benchmarks/spec_code.json spec-code-F04 |
| E-53 | gate | R2 | FAIL test-benchmark-gate-code |
| E-54 | free-form-dispatch | orchestrator | Fix R2 must-fix test findings |
| E-55 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-56 | finding | R2 | Layer 6. tests/test_stream.py mixes in-process unit tests with three warehouse-backed tests that use the stream_build fixture (test_actor_type_from_bot_flag, test_missing_length_adds_zero_bytes, test_window_mart_has_no_late_event). Stream checks 5 and 6 sit in tests/test_stream_checks.py while other stream checks in tests/test_checks.py read the same warehouse. Source: .context/benchmarks/spec_co… |
| E-57 | finding | R2 | Failure paths 6. The missing-zip-glob error (EngineError: no file matches <glob>) and the CSV row with 2 of 3 fields (EngineError: <zip>/x.csv: line 3 has 2 fields, header has 3) both name the file and the problem, but no test covers either. Verified by probe at head d1e5c07. Source: .context/benchmarks/spec_code.json (head d1e5c07) |
| E-58 | free-form-dispatch | orchestrator | Fix R2 layer and failure-path findings |
| E-59 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-63 | orchestrator-runner | orchestrator | cat .context/evidence/item-1.txt \| tail -5; grep -n "pytest\\|uv run" .context/plans/spec.plan.md \| head -5; cat .cadence.json \| head -3 |
| E-64 | finding | orchestrator | acceptance item 5 exit 4: test_checks.py::test_stream_edits_and_bytes_per_wiki not found. The test is in tests/test_stream_checks.py:4. Item 6 has the same gap at tests/test_stream_checks.py:21. |
| E-65 | gate | orchestrator | FAIL closure |
| E-66 | stop-refusal | orchestrator | BLOCKED early stop in execution. Progress unknown (run abc1eff9-3d0f-47f9-9fff-b8a1e0421a80): a gate timed out or could not run. Continue paceline: next E4 (draft-pr) via `/commit-push-pr --draft` |
| E-68 | gate | orchestrator | FAIL closure |
| E-69 | hard-stop | orchestrator | R5 closure fails. Items 5 and 6 name tests/test_checks.py, but the tests live in tests/test_stream_checks.py (spec-F12). Findings spec-F01 to spec-F03 check scripts/test_benchmark_gate.py, which is missing from the repo. No retries left. |
| E-72 | after-document | P7 | 3 tool calls after the block wrote its document |
| E-75 | after-document | P4 | 3 tool calls after the block wrote its document |
| E-77 | after-document | R1 | 4 tool calls after the block wrote its document |
| E-80 | after-document | R2 | 3 tool calls after the block wrote its document |
| E-81 | fix-commit | E1 | fix(R3): annotate the totals dict in sum_by_key |
| E-82 | fix-commit | E1 | fix(spec-F11): test the missing zip glob and the short CSV row errors |
| E-83 | fix-commit | E1 | fix(spec-F10): move the warehouse-backed stream tests to the checks file |
| E-84 | fix-commit | E1 | fix(spec-F07): cover the running maximum in a batch and the window length in the unit layer |
| E-85 | fix-commit | E1 | fix(spec-F06): name the file when a zip is not a valid zip |
| E-86 | fix-commit | E1 | fix(spec-F05): move stream and make tests to the files that match their layer |
| E-87 | fix-commit | E1 | fix(spec-F04): keep one tree_hash helper and run make build once per session |
| E-88 | fix-commit | E1 | fix(MF-6): skip a message that is not an event object |
| E-89 | fix-commit | E1 | fix(MF-5): skip a message with invalid UTF-8 and count it |
| E-90 | fix-commit | E1 | fix(MF-4): merge the two lake tests into test_engine_schema.py |
| E-91 | fix-commit | E1 | fix(MF-3): reuse the conftest write_pipeline fixture in schema tests |
| E-92 | fix-commit | E1 | fix(MF-2): annotate the five empty containers mypy reports |
| E-93 | fix-commit | E1 | fix(MF-1): make tests a package so mypy reads each file once |
