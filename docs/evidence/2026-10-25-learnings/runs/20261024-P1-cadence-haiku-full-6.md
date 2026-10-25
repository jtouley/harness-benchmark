RUN_BY_COMMAND: run-learnings
Run: 20261024-P1-cadence-haiku-full-6
Cadence: 2100c6e6aa99d99309cfa8e7f8c5cee1018584b4
Packet sha256: d672c11a438513a9cb6180bed2b6a93674d8d287eb9edddc442a406909cfa427

# Learnings: 20261024-P1-cadence-haiku-full-6

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- after-document: 16
- dispatch: 18
- finding: 29
- fix-commit: 4
- gate: 32
- orchestrator-runner: 9
- stop-point: 1
- stop-refusal: 3

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-34, E-51, E-82
- Rule: gate-repeat
- Key: gate-repeat|cadence|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: % duplicated # of # code lines; changed code file s not measured; duplication.max_percent is # reuse the code that.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-42, E-43, E-80
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|test-benchmark-gate-code
- Change: Before the return, run the `test-benchmark-gate-code` gate once and fix every class it names in one pass. In this run it failed 3 times in R2: test-benchmark-code scores must be numbers verdict fail; test-benchmark-code must-fix dimensions below # assertion_strength; test-benchmark-code must-fix dimensions below # dry_no_clone_setups.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-42
- Rule: late-gate
- Key: late-gate|spec-driven|test-benchmark-gate-code|test-benchmark-code scores must
- Change: E1's phase gate runs the `test-benchmark-gate-code` measure `test-benchmark-code scores must` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-43, E-80
- Rule: late-gate
- Key: late-gate|spec-driven|test-benchmark-gate-code|test-benchmark-code must-fix dimensions
- Change: E1's phase gate runs the `test-benchmark-gate-code` measure `test-benchmark-code must-fix dimensions` before E4, so the review phase does not find it first. It failed 2 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/commit-push-pr.md
- Status: candidate
- Evidence: E-24, E-25
- Rule: redispatch
- Key: redispatch|commit-push-pr|E4
- Change: E4 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=commit-push-pr@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=commit-push-pr@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-36, E-45, E-53, E-57, E-63, E-71, E-77, E-85
- Rule: redispatch
- Key: redispatch|test-benchmark|R2
- Change: R2 was dispatched 8 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: SKILL.md
- Status: candidate
- Evidence: E-44, E-50, E-55, E-61, E-68, E-70, E-75, E-81, E-84
- Rule: orchestrator-runner
- Key: orchestrator-runner|cadence|runner
- Change: The orchestrator ran 9 project commands. It runs the manifest only; project commands run inside a block subagent or a gate.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-11, E-12, E-13, E-109, E-110, E-111, E-112
- Rule: review-finding
- Key: review-finding|spec-driven|test-benchmark:plan
- Change: E1 checks `test-benchmark:plan` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-29, E-30, E-31, E-32, E-109, E-110, E-111, E-112
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 4 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-37, E-38, E-39, E-46, E-54, E-58, E-59, E-64, E-65, E-66, E-72, E-73, E-78, E-79, E-109, E-110, E-111, E-112
- Rule: review-finding
- Key: review-finding|spec-driven|test-benchmark:code
- Change: E1 checks `test-benchmark:code` before E4: the review found 14 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: SKILL.md
- Status: candidate
- Evidence: E-87, E-90, E-91
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in execution. progress
- Change: The hooks refused 3 times with `blocked early stop in execution. progress`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: commands/commit-push-pr.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|commit-push-pr|E4|open at e# draft-pr the
- Change: The run stopped at E4: open at e# draft-pr the stop hook refused the stop # times fail no. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=commit-push-pr@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=commit-push-pr@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-13
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-100
- Rule: after-document
- Key: after-document|pr-review-local|R1
- Change: R1 made 6 tool calls after it wrote its document. The block writes its document last and then returns.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | E4 | open at E4 (draft-pr): the Stop hook refused the stop 3 times (FAIL no active cadence session) |
| E-11 | finding | P7 | No expected values or independent oracle for checks 1-7 in the Acceptance checks table; assertion strength 5 below floor 7 |
| E-12 | finding | P7 | No shared test helper named for the fake SSE server or lake fixture in Reuse and extension; DRY 6 below floor 7 |
| E-13 | finding | P7 | Mean score 5.83 below floor 7; verdict FAIL |
| E-24 | dispatch | E4 | /commit-push-pr dispatched as E4 |
| E-25 | dispatch | E4 | /commit-push-pr dispatched as E4 |
| E-29 | finding | R1 | Edit with no server_name: window_key is NULL; dbt not_null_int_window_5min_window_key FAIL 5; window_5min skipped. |
| E-30 | finding | R1 | R3 bugs record fail: ruff B007 batch.py:84; S310 stream.py:111,114; S311 tests/fake_sse.py:147 (4 findings, record .context/gates/cognitive-complexity.json). |
| E-31 | finding | R1 | R3 types record fail: mypy union-attr stream.py:227; var-annotated tests/test_question_a.py:75, tests/test_stream_marts.py:73,81,96,103 (6 findings). |
| E-32 | finding | R1 | Check 3 names fct_award_transaction.federal_action_obligation (per transaction, needs sum per award_key); Check 6 names window_5min.edit_count (split by namespace and actor, needs sum). |
| E-34 | gate | orchestrator | FAIL cognitive-complexity |
| E-36 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-37 | finding | R2 | test_monthly_per_person_uses_july_2024 never checks July; it takes rows[0] of any non-zero row. Assertion strength below floor 7. |
| E-38 | finding | R2 | test_top_ten_counties_per_person checks only county order, not values; test_stream_marts_written_under_out_marts (tests/test_stream_marts.py:137) checks only file existence; test_running_max_survives_restart (tests/test_stream.py:44) checks only rows[40]. Assertion strength below floor 7. |
| E-39 | finding | R2 | Mean of six scores is 6.5, below floor 7. Must-fix items are spec-F04 and spec-F05. |
| E-42 | gate | R2 | FAIL test-benchmark-gate-code |
| E-43 | gate | R2 | FAIL test-benchmark-gate-code |
| E-44 | orchestrator-runner | orchestrator | timeout 1200 uv run pytest -q 2>&1 \| tail -25; echo "PYTEST_EXIT=${PIPESTATUS[0]}" |
| E-45 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-46 | finding | R2 | Probe at 908a8fd: StreamConsumer.run against http://127.0.0.1:9 (closed port) with duration 2 returns normally with no error and writes no batch. The run loop catches OSError and retries until the deadline. make stream then runs dbt on an empty stream with exit 0. A dead feed looks like a successful run. No suite test covers this path. |
| E-50 | orchestrator-runner | orchestrator | grep -n "def _consumer" -A4 tests/test_stream.py && grep -n "^import\\|^from" tests/test_stream.py && cat >> tests/test_stream.py <<'EOF' def test_offline_feed_fails_the_run(tmp_path): consumer = _consumer(tmp_path / "lake", tmp_path / "out", "http://127.0.0.1:9/recentchange", batch_rows=50) with pytest.raises(RuntimeError, match="unreachable"): consumer.run(duration_seconds=2) assert _state_files… |
| E-51 | gate | orchestrator | FAIL cognitive-complexity |
| E-53 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-54 | finding | R2 | Mean of six scores is 6.83, below floor 7 (failure_paths 6). The offline feed case is now tested (tests/test_stream.py:104). Two failure inputs still have no suite test: a missing RAW_DIR fails with AttributeError that does not name the input (spec-F10), and corrupt SSE payloads are not named in any test. Add parametrize rows for both. |
| E-55 | orchestrator-runner | orchestrator | cat >> tests/test_build.py <<'EOF' def test_empty_landing_names_the_table(tmp_path): @dlt.resource(name="empty_table") def empty(): yield from [] with pytest.raises(ValueError, match="no rows landed for table empty_table"): land(empty(), "empty_table", tmp_path / "staging", "empty_pipe") EOF export CADENCE_HOME=/var/tmp/run-one/20261024-P1-cadence-haiku-full-6/plugin && timeout 900 uv run pytest … |
| E-57 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-58 | finding | R2 | Mutant M6 (the Last-Event-ID header is not sent on resume) passes all of tests/test_stream.py (8 passed). The restart tests pass only because the dedupe set in _seen_meta_ids hides the replayed events. The fake server records last_event_ids but no test reads them, so the A-4 resume contract is not asserted. |
| E-59 | finding | R2 | Probe at 1bcfc68: StreamConsumer._accept given a payload with timestamp and server_name but no meta raises KeyError: meta. run() catches only OSError and HTTPException, so one malformed event aborts the whole stream run. No suite test covers this corrupt-event class; test_corrupt_event_data_is_skipped covers only unparseable or non-object data lines. |
| E-61 | orchestrator-runner | orchestrator | cat >> tests/test_stream.py <<'EOF' def test_resume_sends_last_event_id(tmp_path, fake_sse_server): events = build_events() server = fake_sse_server(events) lake, out = tmp_path / "lake", tmp_path / "out" _consumer(lake, out, server.url, batch_rows=50).run(duration_seconds=4, max_events=20) _consumer(lake, out, server.url, batch_rows=50).run(duration_seconds=4) assert server.last_event_ids[0] is … |
| E-63 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-64 | finding | R2 | Layer score 6 at b4237df, below floor 7. The oracle imports zip_csv_readers from pipeline.batch, the code under test, so a zip or CSV parse bug is shared by the marts and the oracle and the oracle cannot catch it. tests/test_question_a.py also holds test_oracle_map_names_aggregation_for_checks_3_and_6, a check of oracle_map.yml text, in the data-layer file. Same point as spec-F12, now must-fix be… |
| E-65 | finding | R2 | Assertion strength score 6 at b4237df, below floor 7. test_build_runs_dbt_models only checks that each mart parquet file exists, and test_make_stream_runs_dbt_models only checks that window_5min and fct_edit are non-empty, so a wrong mart passes both. test_monthly_per_person_uses_july_2024 checks every month, not July, so its name is wrong (see spec-F04). |
| E-66 | finding | R2 | Mean of six scores is 6.67 (40 / 6), below floor 7. Must-fix items are spec-F17 (layer 6) and spec-F18 (assertions 6). Verdict FAIL at b4237df. |
| E-68 | orchestrator-runner | orchestrator | uv run python -c "import yaml, pyarrow.parquet; print('yaml ok', yaml.__version__)" 2>&1 \| tail -1; python3 - <<'EOF' from pathlib import Path b = Path("tests/test_build.py") s = b.read_text(encoding="utf-8") s = s.replace("import dlt\nimport pytest\n\nfrom conftest import run_make\n", "import dlt\nimport pyarrow.parquet as pq\nimport pytest\nimport yaml\n\nfrom conftest import REPO, run_make\n",… |
| E-70 | orchestrator-runner | orchestrator | export GIT_AUTHOR_NAME=Claude GIT_AUTHOR_EMAIL=noreply@anthropic.com GIT_COMMITTER_NAME=Claude GIT_COMMITTER_EMAIL=noreply@anthropic.com && git add tests/raw_oracle.py tests/test_build.py tests/test_question_a.py tests/test_stream_marts.py tests/test_oracle_map.py && git commit -q -F - <<'EOF' test: make the oracle independent and check mart contents - Read the zips in the oracle with the stdlib,… |
| E-71 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-72 | finding | R2 | Layer correctness 6 at 191a216. tests/test_build.py holds a unit test of pipeline.landing.land next to make-build end-to-end tests. tests/test_question_a.py rewrites a raw census file and runs a full make build inside a Question A test file. Each file mixes layers, so a failure in one layer reads as a failure in another. |
| E-73 | finding | R2 | Assertion strength 6 at 191a216, below floor 7. test_wiki_key_is_server_name asserts a subset (<=), so an empty or wrong mart passes. test_stream_marts_written_under_out_marts asserts only non-empty. test_missing_namespace_is_minus_one checks one row by a single id. The values of these marts are not compared with the oracle. |
| E-75 | orchestrator-runner | orchestrator | python3 - <<'EOF' from pathlib import Path qa = Path("tests/test_question_a.py") s = qa.read_text(encoding="utf-8") start = s.index("def test_census_fallback_uses_popestimate2021") end = s.index("def test_fy_per_person_sums_twelve_months") moved = s[start:end] qa.write_text(s[:start] + s[end:], encoding="utf-8") header = '''"""Census fallback: a county with no 2024 estimate takes its 2021 populat… |
| E-77 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-78 | finding | R2 | At 0023145, _rows (census fallback and Question A) and _mart (stream marts) each read out/marts/<mart>/<mart>.parquet with the same body. test_shape.py does not flag them because they are not conftest names. DRY score 6, below floor 7. Move one reader into tests/conftest.py next to dirs_for and run_make and import it. |
| E-79 | finding | R2 | At 0023145 the scores are 7, 7, 6, 7, 6, 6. Mean 6.5, below floor 7, and DRY is below floor (spec-F24). Verdict FAIL. Mutants were not run at this HEAD, so mutation_resilience is scored from reading. |
| E-80 | gate | R2 | FAIL test-benchmark-gate-code |
| E-81 | orchestrator-runner | orchestrator | python3 - <<'EOF' import re from pathlib import Path # 1. shared mart reader in conftest c = Path("tests/conftest.py") s = c.read_text(encoding="utf-8") s = s.replace("import pytest\n\nfrom fake_sse", "import pyarrow.parquet as pq\nimport pytest\n\nfrom fake_sse", 1) s = s.replace('def dirs_for(base: Path) -> dict[str, Path]:\n return {"lake": base / "lake", "out": base / "out"}\n', 'def dirs_for… |
| E-82 | gate | orchestrator | FAIL cognitive-complexity |
| E-84 | orchestrator-runner | orchestrator | timeout 1200 uv run pytest -q 2>&1 \| tail -4; echo "PYTEST_EXIT=${PIPESTATUS[0]}" |
| E-85 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-87 | stop-refusal | orchestrator | BLOCKED early stop in execution. Progress unknown (run fc38687a-2e5d-4ed5-8d29-95452d73b1f9): a gate timed out or could not run. Continue paceline: next E4 (draft-pr) via `/commit-push-pr --draft` |
| E-90 | stop-refusal | orchestrator | BLOCKED early stop in execution. Progress unknown (run fc38687a-2e5d-4ed5-8d29-95452d73b1f9): a gate timed out or could not run. Continue paceline: next E4 (draft-pr) via `/commit-push-pr --draft` |
| E-91 | stop-refusal | orchestrator | BLOCKED early stop in execution. Progress unknown (run fc38687a-2e5d-4ed5-8d29-95452d73b1f9): a gate timed out or could not run. Continue paceline: next E4 (draft-pr) via `/commit-push-pr --draft` |
| E-100 | after-document | R1 | 6 tool calls after the block wrote its document |
| E-109 | fix-commit | E1 | fix: skip an event with no meta and test the resume header |
| E-110 | fix-commit | E1 | fix: name the table when a load lands no rows |
| E-111 | fix-commit | E1 | fix: fail the stream run when the feed never connects |
| E-112 | fix-commit | E1 | fix: address R1 must-fix findings MF-1 to MF-4 |
