RUN_BY_COMMAND: run-learnings
Run: 20261024-P2-cadence-haiku-full-6
Cadence: 2100c6e6aa99d99309cfa8e7f8c5cee1018584b4
Packet sha256: 358f3a7d092f8ecfd62e79e7e5504db01e08ccf094e0862013aa6ffda7c78624

# Learnings: 20261024-P2-cadence-haiku-full-6

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- after-document: 9
- dispatch: 10
- finding: 18
- fix-commit: 4
- free-form-dispatch: 2
- gate: 35
- hard-stop: 1
- orchestrator-runner: 7
- stop-point: 1

## Proposals

### L-1
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-21, E-23, E-24
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 3 times in E1: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; fix step run r# without --check to.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-47, E-48
- Rule: gate-repeat
- Key: gate-repeat|cadence|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 2 times in free-form: _handler_for # new; changed code file s not measured; limit is # split each function or.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-63, E-72, E-73
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: spec-f# must-fix status open not terminal it; acceptance item # is not passed python.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: SKILL.md
- Status: candidate
- Evidence: E-46, E-59
- Rule: free-form-dispatch
- Key: free-form-dispatch|cadence|free-form
- Change: The orchestrator sent 2 free-form subagent prompts. Dispatch each block and the fix round only from its packet (`/<command>` with the Block line).
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: SKILL.md
- Status: candidate
- Evidence: E-50, E-51, E-52, E-53, E-54, E-55, E-61
- Rule: orchestrator-runner
- Key: orchestrator-runner|cadence|runner
- Change: The orchestrator ran 7 project commands. It runs the manifest only; project commands run inside a block subagent or a gate.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-11, E-64, E-84, E-85, E-86, E-87
- Rule: review-finding
- Key: review-finding|spec-driven|test-benchmark:layer
- Change: E1 checks `test-benchmark:layer` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-12, E-65, E-84, E-85, E-86, E-87
- Rule: review-finding
- Key: review-finding|spec-driven|test-benchmark:dry
- Change: E1 checks `test-benchmark:dry` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-13, E-67, E-84, E-85, E-86, E-87
- Rule: review-finding
- Key: review-finding|spec-driven|test-benchmark:assert
- Change: E1 checks `test-benchmark:assert` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-14, E-69, E-84, E-85, E-86, E-87
- Rule: review-finding
- Key: review-finding|spec-driven|test-benchmark:failure-paths
- Change: E1 checks `test-benchmark:failure-paths` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-40, E-41, E-44, E-84, E-85, E-86, E-87
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-42, E-43, E-57, E-58, E-66, E-68, E-84, E-85, E-86, E-87
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 6 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-70, E-84, E-85, E-86, E-87
- Rule: review-finding
- Key: review-finding|spec-driven|core:spec-gap
- Change: E1 checks `core:spec-gap` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-13
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-63, E-72
- Rule: open-at-close
- Key: open-at-close|pr-review-local|open-must-fix
- Change: The fix round returns only after `ledger_verify.py` marks each fixed must-fix item verified; R5 found open must-fix items 2 times.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-14
- Target: SKILL.md
- Status: candidate
- Evidence: E-74
- Rule: hard-stop
- Key: hard-stop|cadence|R5|retries
- Change: R5 recorded a `retries` hard stop: r# closure fails on acceptance row # the plan names the wrong. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-15
- Target: SKILL.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|cadence|R5|hard stop retries r# closure
- Change: The run stopped at R5: hard stop retries r# closure fails on acceptance row # the plan names the. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-16
- Target: commands/plan-create.md
- Status: candidate
- Evidence: E-76
- Rule: after-document
- Key: after-document|plan-create|P1
- Change: P1 made 3 tool calls after it wrote its document. The block writes its document last and then returns.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-create@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=plan-create@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-17
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-82
- Rule: after-document
- Key: after-document|pr-review-local|R1
- Change: R1 made 3 tool calls after it wrote its document. The block writes its document last and then returns.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | R5 | hard stop retries: R5 closure fails on acceptance row 4: the plan names the wrong test file, and the plan is frozen after P9 (FAIL no active cadence session) |
| E-11 | finding | P7 | Acceptance rows 1-7 do not state which layer each assertion reads (engine, dbt mart, or out/marts/); check 4 uses real data while the others use fixtures in the same files. Layer score 6. |
| E-12 | finding | P7 | Each check gets its own small fixture; no shared fixture module is named in Reuse and extension. DRY score 6. |
| E-13 | finding | P7 | A-17 test only compares pins with pyproject.toml; A-15 hour boundary has no named test. Assertions score 6. |
| E-14 | finding | P7 | Crash between Parquet write and manifest rename has no test id; no tests for corrupt or missing raw zip, corrupt manifest, replay server down, failed reconnect. Failure paths score 5; mean 6.0. |
| E-21 | gate | E1 | FAIL cognitive-complexity |
| E-23 | gate | E1 | FAIL cognitive-complexity |
| E-24 | gate | E1 | FAIL cognitive-complexity |
| E-40 | finding | R1 | make stream DURATION=60 ran past 290 s; consume(duration=30) on a resumed lake did not return in 200 s. Replay sends bare : heartbeat lines after the last event, so the loop never reaches the deadline check (engine/stream.py:157-188). |
| E-41 | finding | R1 | Valid JSON without meta.id raises KeyError and restarts repeat it (repro: KeyError id, twice). Non-UTF-8 bytes raise UnicodeDecodeError in engine/sse.py:27, not caught as OSError. |
| E-42 | finding | R1 | test_shape.py --change reports thin_files verdict fail: tests/test_stream_e2e.py has one test that duplicates tests/test_stream_restart.py. |
| E-43 | finding | R1 | cognitive_complexity_gate bugs record: value 6, max 0, verdict fail (S310 engine/sse.py:22,23; S608 engine/publish.py:30; S608 tests/test_marts_real_data.py:25,29,34). |
| E-44 | finding | R1 | cognitive_complexity_gate types record: value 50, max 0, verdict fail (engine/stream.py:149 None not callable; ** dict[str,float] passed to consume() in tests/test_stream_restart.py; typed fixtures). |
| E-46 | free-form-dispatch | orchestrator | Fix five must-fix review findings |
| E-47 | gate | free-form | FAIL cognitive-complexity |
| E-48 | gate | free-form | FAIL cognitive-complexity |
| E-50 | orchestrator-runner | orchestrator | git status --short && git log --oneline \| head -3 && rm -rf lake out && (time make build) 2>&1 \| tail -5 && (time make stream DURATION=240) 2>&1 \| tail -8; echo "STREAM_EXIT=${PIPESTATUS[0]}" |
| E-51 | orchestrator-runner | orchestrator | ls out/marts; ls lake/_manifest \| head; cat > /tmp/q_clean.py <<'EOF' import duckdb, glob con = duckdb.connect() def q(s): return con.sql(s).fetchall() print("fct_edit path check:", glob.glob("out/marts/*edit*")[:5]) EOF uv run python -I /tmp/q_clean.py |
| E-52 | orchestrator-runner | orchestrator | cat > /tmp/q_clean.py <<'EOF' import duckdb con = duckdb.connect() def q(s): return con.sql(s).fetchall() print("fct_edit rows/distinct:", q("select count(*), count(distinct edit_id) from read_parquet('out/marts/fct_edit/*.parquet')")) print("late_events:", q("select count(*) from read_parquet('out/marts/late_events/*.parquet')")) print("time range:", q("select min(event_time), max(event_time) fr… |
| E-53 | orchestrator-runner | orchestrator | cat > /tmp/q_clean2.py <<'EOF' import duckdb con = duckdb.connect() p = "read_parquet('out/marts/mart_edit_window_5min/*.parquet')" print(con.sql(f"describe select * from {p}").fetchall()[:8]) EOF uv run python -I /tmp/q_clean2.py 2>&1 \| tail -3 |
| E-54 | orchestrator-runner | orchestrator | cat > /tmp/q_clean3.py <<'EOF' import duckdb con = duckdb.connect() p = "read_parquet('out/marts/mart_edit_window_5min/*.parquet')" print(con.sql(f"select window_start, sum(edit_count) as e from {p} where wiki='en.wikipedia.org' group by window_start order by e desc limit 1").fetchall()) EOF uv run python -I /tmp/q_clean3.py 2>&1 \| tail -3 |
| E-55 | orchestrator-runner | orchestrator | cat > /tmp/q_clean3.py <<'EOF' import duckdb con = duckdb.connect() p = "read_parquet('out/marts/mart_edit_window_5min/*.parquet')" print(con.sql(f"select window_start, sum(edit_count) as e from {p} where domain='en.wikipedia.org' group by window_start order by e desc limit 1").fetchall()) print(con.sql(f"select wiki, domain, actor_type, sum(edit_count), sum(net_bytes) from {p} group by all order… |
| E-57 | finding | R2 | DRY: run_make_build() is defined twice (tests/test_build_publish.py:14, tests/test_build_idempotence.py:16); tests/test_marts_real_data.py:14 inlines the same make build call; module fixture db is defined twice (tests/test_stream_checks.py:15, tests/test_marts_fy2024.py:9). Move the shared helper and fixture into one module and import it. |
| E-58 | finding | R2 | Layer: test_pinned_libraries_import_at_pinned_versions checks installed package metadata, not engine behavior; test_dbt_contracts.py:22 checks engine source text; the make-build tests run the full real-data build in unit-test modules and share lake/ and out/, so test_marts_real_data.py depends on test order. |
| E-59 | free-form-dispatch | orchestrator | Resolve two HIGH test-benchmark findings |
| E-61 | orchestrator-runner | orchestrator | python3 - <<'EOF' from pathlib import Path p = Path("tests/test_dbt_contracts.py") s = p.read_text(encoding="utf-8") a = 'duckdb.sql(f"describe select * from read_parquet(\'{path}\')").fetchall()' b = 'duckdb.execute("describe select * from read_parquet(?)", [str(path)]).fetchall()' c = 'published = duckdb.sql(f"select count(*) from read_parquet(\'{tmp_path / \'out/mart_agency_copy/part-0.parquet… |
| E-63 | gate | orchestrator | FAIL closure |
| E-64 | finding | orchestrator | Acceptance rows 1-7 do not state which layer each assertion reads (engine, dbt mart, or out/marts/); check 4 uses real data while the others use fixtures in the same files. Layer score 6. |
| E-65 | finding | orchestrator | Each check gets its own small fixture; no shared fixture module is named in Reuse and extension. DRY score 6. |
| E-66 | finding | orchestrator | DRY: run_make_build() is defined twice (tests/test_build_publish.py:14, tests/test_build_idempotence.py:16); tests/test_marts_real_data.py:14 inlines the same make build call; module fixture db is defined twice (tests/test_stream_checks.py:15, tests/test_marts_fy2024.py:9). Move the shared helper and fixture into one module and import it. |
| E-67 | finding | orchestrator | A-17 test only compares pins with pyproject.toml; A-15 hour boundary has no named test. Assertions score 6. |
| E-68 | finding | orchestrator | Layer: test_pinned_libraries_import_at_pinned_versions checks installed package metadata, not engine behavior; test_dbt_contracts.py:22 checks engine source text; the make-build tests run the full real-data build in unit-test modules and share lake/ and out/, so test_marts_real_data.py depends on test order. |
| E-69 | finding | orchestrator | Crash between Parquet write and manifest rename has no test id; no tests for corrupt or missing raw zip, corrupt manifest, replay server down, failed reconnect. Failure paths score 5; mean 6.0. |
| E-70 | finding | orchestrator | Row 4 names tests/test_marts_fy2024.py::test_county_totals_sum_to_state_and_source. The test is in tests/test_marts_real_data.py:17. The plan is frozen after P9, so the row is not changed here. acceptance_checks.py pass --item 4 exits 4 (not found). |
| E-72 | gate | orchestrator | FAIL closure |
| E-73 | gate | orchestrator | FAIL closure |
| E-74 | hard-stop | orchestrator | R5 closure fails on acceptance row 4: the plan names the wrong test file, and the plan is frozen after P9 |
| E-76 | after-document | P1 | 3 tool calls after the block wrote its document |
| E-82 | after-document | R1 | 3 tool calls after the block wrote its document |
| E-84 | fix-commit | E1 | fix(types): type the stream consumer, replay server and test helpers |
| E-85 | fix-commit | E1 | fix: clear ruff bugs findings in sse, publish and real-data test |
| E-86 | fix-commit | E1 | fix(stream): skip and count events with bad shape or bytes |
| E-87 | fix-commit | E1 | fix(stream): stop at DURATION during heartbeat lines |
