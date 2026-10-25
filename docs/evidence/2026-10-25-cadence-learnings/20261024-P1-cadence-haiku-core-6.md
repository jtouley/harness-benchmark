RUN_BY_COMMAND: run-learnings
Run: 20261024-P1-cadence-haiku-core-6
Cadence: 2100c6e6aa99d99309cfa8e7f8c5cee1018584b4
Packet sha256: 21ff330281389d8ce3681840cb7f4af07c0b939f88a0b3527a0183726f712b31

# Learnings: 20261024-P1-cadence-haiku-core-6

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- after-document: 8
- dispatch: 9
- finding: 14
- fix-commit: 13
- free-form-dispatch: 1
- gate: 32
- hard-stop: 1
- orchestrator-runner: 22
- stop-point: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-3, E-4
- Rule: gate-repeat
- Key: gate-repeat|cadence|validate-gate
- Change: Before the return, run the `validate-gate` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: vibe-test no artifact matching.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-64, E-79
- Rule: gate-repeat
- Key: gate-repeat|cadence|test-benchmark-gate-code
- Change: Before the return, run the `test-benchmark-gate-code` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: test-benchmark-code must-fix dimensions below # assertion_strength.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-30
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|bugs s# possible
- Change: E1's phase gate runs the `cognitive-complexity` measure `bugs s# possible` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-30
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|bugs.max is
- Change: E1's phase gate runs the `cognitive-complexity` measure `bugs.max is` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-30
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|types mypy report
- Change: E1's phase gate runs the `cognitive-complexity` measure `types mypy report` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-30
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|types.max is
- Change: E1's phase gate runs the `cognitive-complexity` measure `types.max is` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-30
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|fix step delegate
- Change: E1's phase gate runs the `cognitive-complexity` measure `fix step delegate` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-57
- Rule: late-gate
- Key: late-gate|spec-driven|test-benchmark-gate-code|test-benchmark-code must-fix dimensions
- Change: E1's phase gate runs the `test-benchmark-gate-code` measure `test-benchmark-code must-fix dimensions` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-53, E-76
- Rule: redispatch
- Key: redispatch|test-benchmark|R2
- Change: R2 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: SKILL.md
- Status: candidate
- Evidence: E-41
- Rule: free-form-dispatch
- Key: free-form-dispatch|cadence|free-form
- Change: The orchestrator sent 1 free-form subagent prompts. Dispatch each block and the fix round only from its packet (`/<command>` with the Block line).
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: SKILL.md
- Status: candidate
- Evidence: E-42, E-43, E-44, E-45, E-46, E-47, E-48, E-49, E-52, E-58, E-59, E-65, E-66, E-67, E-68, E-69, E-70, E-71, E-72, E-73, E-74, E-75
- Rule: orchestrator-runner
- Key: orchestrator-runner|cadence|runner
- Change: The orchestrator ran 22 project commands. It runs the manifest only; project commands run inside a block subagent or a gate.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-31, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101
- Rule: review-finding
- Key: review-finding|spec-driven|DECISIONS.md:Stream consumer and lake landing
- Change: E1 checks `DECISIONS.md:Stream consumer and lake landing` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-13
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-32, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101
- Rule: review-finding
- Key: review-finding|spec-driven|spec.md Rules: make build runs the batch part from the raw files
- Change: E1 checks `spec.md Rules: make build runs the batch part from the raw files` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-14
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-33, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101
- Rule: review-finding
- Key: review-finding|spec-driven|spec.md Amendment A (July 1, 2024 population; use latest earlier estimate where no 2024 estimate)
- Change: E1 checks `spec.md Amendment A (July 1, 2024 population; use latest earlier estimate where no 2024 estimate)` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-15
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-34, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101
- Rule: review-finding
- Key: review-finding|spec-driven|spec.md Rules: event time and windows are UTC
- Change: E1 checks `spec.md Rules: event time and windows are UTC` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-16
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-35, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101
- Rule: review-finding
- Key: review-finding|spec-driven|spec.md Rules: Test the keys of each model with dbt tests
- Change: E1 checks `spec.md Rules: Test the keys of each model with dbt tests` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-17
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-36, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor.md Bugs and types (R3): types record
- Change: E1 checks `review-rigor.md Bugs and types (R3): types record` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-18
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-37, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor.md test quality: no partial-success thresholds
- Change: E1 checks `review-rigor.md test quality: no partial-success thresholds` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-19
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-38, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension item 1 (reuse)
- Change: E1 checks `core:dry-extension item 1 (reuse)` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-20
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-39, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor.md Bugs and types (R3): bugs record
- Change: E1 checks `review-rigor.md Bugs and types (R3): bugs record` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-21
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-54, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor.md R2 test review: assertion strength and failure paths
- Change: E1 checks `review-rigor.md R2 test review: assertion strength and failure paths` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-22
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-55, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor.md R2 test review: assertion strength and coverage of behavior
- Change: E1 checks `review-rigor.md R2 test review: assertion strength and coverage of behavior` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-23
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-56, E-77, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor.md R2 test review: layer correctness
- Change: E1 checks `review-rigor.md R2 test review: layer correctness` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-24
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-78, E-89, E-90, E-91, E-92, E-93, E-94, E-95, E-96, E-97, E-98, E-99, E-100, E-101
- Rule: review-finding
- Key: review-finding|spec-driven|review-rigor.md R2 test review: assertion strength
- Change: E1 checks `review-rigor.md R2 test review: assertion strength` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-25
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-80
- Rule: hard-stop
- Key: hard-stop|test-benchmark|R2|retries
- Change: R2 recorded a `retries` hard stop: r# test-benchmark still fail after two fix rounds mean # floor. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-26
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|test-benchmark|R2|hard stop retries r# test-benchmark
- Change: The run stopped at R2: hard stop retries r# test-benchmark still fail after two fix rounds mean # floor. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | R2 | hard stop retries: R2 test-benchmark still FAIL after two fix rounds: mean 6.33 (floor 7), assertion_strength 6, layer_correctness 6, mutation not run. Open: spec-F04 (layer mix, rerun test in discovery), spec-F05 (live replay test prefix only). (FAIL no active cadence session) |
| E-3 | gate | orchestrator | FAIL validate-gate |
| E-4 | gate | orchestrator | FAIL validate-gate |
| E-30 | gate | R1 | FAIL cognitive-complexity |
| E-31 | finding | R1 | Probe with a JSON event whose length is a string, or whose timestamp is a string, makes StreamConsumer.run() raise (AttributeError, TypeError) and land nothing in that run; a non-JSON event or a JSON array is skipped with a log line. |
| E-32 | finding | R1 | With FY2024_485_Contracts zip removed from a copy of data/raw, load_batch lands 221 contract rows with no error; the same load with all four contract zips lands 416 rows. dbt oracles read the lake, so they do not catch it. |
| E-33 | finding | R1 | Thirteen award place codes have no 2024 row (09001 09003 09005 09009 09011 09013 plus seven territory codes). data/raw/census/co-est2021-alldata.csv holds POPESTIMATE2021 for 09001 (959768), 09003, 09005, 09009, 09011, 09013. The PR leaves all thirteen null and DECISIONS.md calls the fallback not needed. |
| E-34 | finding | R1 | cast(to_timestamp(epoch) as timestamp) follows the session TimeZone. With TZ=America/New_York, epoch 1792021600 gives event_time_utc 2026-10-14 19:46:40 (UTC is 23:46:40). late_events inherits the column. |
| E-35 | finding | R1 | mart_window_5min (key window_start, wiki, namespace, actor_type) and edits_by_wiki_actor (key wiki, actor_type) have no data_tests entry. The only unique_combination test is on the incremental window_5min model. |
| E-36 | finding | R1 | R3 types record verdict fail: mypy cannot check the files: Source file found twice under different module names: lateness and pipeline.lateness. Neither pipeline/ nor tests/ has an __init__.py. After adding empty __init__.py files the clash is gone. |
| E-37 | finding | R1 | test_consumer_replayAtLocalUrl_landsUniqueEdits asserts only len(raw) > 0 and uniqueness. It does not compare the landed ids with the ids the replay sent, so a consumer that lands one event of many passes. |
| E-38 | finding | R1 | read_ids and read_rows repeat the glob guard and dataset read of _read_column in pipeline/stream_consumer.py:99-102. The DLT_COLUMNS constant is also repeated in tests/check_rerun.py and tests/test_batch_load.py. |
| E-39 | finding | R1 | R3 bugs record verdict fail: tests/check_rerun.py:21 S608 Possible SQL injection vector through string-based query construction (ruff 0.17.0). Measure max is 0. |
| E-41 | free-form-dispatch | orchestrator | Fix the nine R1 must-fix items |
| E-42 | orchestrator-runner | orchestrator | timeout 300 uv run python -m unittest tests.test_stream_consumer 2>&1 \| tail -15 |
| E-43 | orchestrator-runner | orchestrator | timeout 580 uv run python -m unittest tests.test_batch_load 2>&1 \| tail -8 |
| E-44 | orchestrator-runner | orchestrator | timeout 590 make build > /tmp/mf3_build.log 2>&1; echo "EXIT=$?"; tail -25 /tmp/mf3_build.log \| cut -c1-260 |
| E-45 | orchestrator-runner | orchestrator | python3 - <<'EOF' import pathlib p = pathlib.Path("transform/models/star/fact_edit.sql") s = p.read_text() old = " cast(to_timestamp(l.event_epoch) as timestamp) as event_time_utc," new = " cast(timezone('UTC', to_timestamp(l.event_epoch)) as timestamp) as event_time_utc," assert s.count(old) == 1 p.write_text(s.replace(old, new)) EOF cat > transform/tests/test_event_time_utc_is_utc.sql <<'EOF' -… |
| E-46 | orchestrator-runner | orchestrator | python3 - <<'EOF' import pathlib, re def edit(path, old, new): p = pathlib.Path(path) s = p.read_text() assert s.count(old) == 1, (path, s.count(old), old[:70]) p.write_text(s.replace(old, new)) edit("tests/stream_harness.py", "import pyarrow.dataset as ds\n\n", "") p = pathlib.Path("tests/test_stream_consumer.py") s = p.read_text() s = re.sub(r'read_ids\(self\.lake, ("[^"]+")\)', r'read_column(s… |
| E-47 | orchestrator-runner | orchestrator | timeout 590 uv run python tests/check_rerun.py > /tmp/rerun.log 2>&1; echo "EXIT=$?"; tail -3 /tmp/rerun.log \| cut -c1-200 |
| E-48 | orchestrator-runner | orchestrator | timeout 590 make stream DURATION=30 > /tmp/stream1.log 2>&1; echo "EXIT=$?"; sed 's/\x1b\[[0-9;]*m//g' /tmp/stream1.log \| tail -4 \| cut -c1-200; echo ----; TZ=America/New_York timeout 300 uv run dbt test --project-dir transform --profiles-dir transform --select test_event_time_utc_is_utc 2>&1 \| sed 's/\x1b\[[0-9;]*m//g' \| tail -4 \| cut -c1-200; echo ----; timeout 300 uv run dbt test --project-dir… |
| E-49 | orchestrator-runner | orchestrator | git add transform/models/schema.yml && git -c user.name="Claude" -c user.email="[redacted-email]" commit -q -m "fix(MF-5): test the keys of the two stream marts The spec asks for a dbt key test on each model. mart_window_5min and edits_by_wiki_actor had none. Add unique_combination_of_columns to each. Co-Authored-By: Claude Haiku 5.5 <[redacted-email]>" && git log --oneline -1 && git st… |
| E-52 | orchestrator-runner | orchestrator | timeout 500 uv run python -m unittest tests.test_stream_consumer tests.test_lateness tests.test_batch_load 2>&1 \| tail -3 && git add pipeline/batch_load.py pipeline/stream_consumer.py tests/test_batch_load.py && git -c user.name="Claude" -c user.email="[redacted-email]" commit -q -m "fix(types): annotate the variables and class attributes mypy could not infer Mypy reported twelve findings on… |
| E-53 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-54 | finding | R2 | test_consumer_replayAtLocalUrl_landsUniqueEdits fails on HEAD: the consumer landed 17 fewer events than a second, separate 3-second read of the live replay sent (assertLessEqual 17 <= 1). The test compares two independent time-bounded reads of a live stream, so its result depends on timing and on the replay state, and it is not deterministic. The test also skips silently when the replay is down. |
| E-55 | finding | R2 | Only the contracts and assistance tables are checked against the source row count. census_county_estimates and sitematrix_sites are checked only for the presence of a parquet file (test_batchLoad_eachSource_landsInOwnFolder), so a load that drops most rows of either table passes. The census_county_estimates_2021 resource is never checked at all. |
| E-56 | finding | R2 | tests/check_rerun.py is a standalone script in the test directory, not a test case. It runs make build (a full batch load and dbt build) and compares mart snapshots. unittest discovery does not run it, so the rerun guarantee has no test that the suite runs. It also mixes an end-to-end build with the unit tests in one directory, and tests/test_batch_load.py runs the real batch load against data/ra… |
| E-57 | gate | R2 | FAIL test-benchmark-gate-code |
| E-58 | orchestrator-runner | orchestrator | python3 - <<'EOF' import pathlib def edit(path, old, new): p = pathlib.Path(path); s = p.read_text() assert s.count(old) == 1, (path, s.count(old), old[:70]); p.write_text(s.replace(old, new)) edit("tests/test_stream_consumer.py", ''' raw = read_column(self.lake / "stream_raw", "event_id") sent = list(dict.fromkeys(_replay_ids(url, seconds=3.0))) self.assertEqual(len(raw), len(set(raw))) self.ass… |
| E-59 | orchestrator-runner | orchestrator | export PATH="$HOME/.local/bin:$PATH"; ruff check tests pipeline --output-format concise 2>&1 \| tail -6; timeout 300 uv run python -m unittest tests.test_stream_consumer 2>&1 \| tail -3; timeout 590 uv run python -m unittest tests.test_rerun 2>&1 \| tail -3 |
| E-64 | gate | orchestrator | FAIL test-benchmark-gate-code |
| E-65 | orchestrator-runner | orchestrator | cat > tests/test_stream_parsing.py <<'EOF' """Stream parsing: SSE framing, the flat row of an event, the field rules, and the stream URL default.""" import pathlib import tempfile import unittest from pipeline.stream_consumer import _field_problem, flatten, iter_sse, read_stream_url class IterSseTest(unittest.TestCase): def test_iterSse_multiLineData_joinsWithNewline(self): lines = ["id: 7\n", "d… |
| E-66 | orchestrator-runner | orchestrator | python3 - <<'EOF' import pathlib p = pathlib.Path("tests/test_batch_load.py"); s = p.read_text() start = s.index(" def test_batchLoad_anySource_addsOnlyLoadMetadataColumns(self):") end = s.index('\n\nif __name__ == "__main__":') new = ''' def test_batchLoad_eachTable_addsOnlyLoadMetadataColumns(self): for name, header in _source_headers().items(): with self.subTest(table=name): self.assertEqual(s… |
| E-67 | orchestrator-runner | orchestrator | python3 - <<'EOF' import pathlib p = pathlib.Path("tests/test_batch_load.py"); s = p.read_text() s = s.replace(' """The source column names of each lake table. dlt lowercases them."""', ' """The source column names of each lake table. dlt lowercases them and turns hyphens into underscores."""') s = s.replace("{h.lower() for h in header} \| DLT_COLUMNS", "{_lake_name(h) for h in header} \| DLT_COLUM… |
| E-68 | orchestrator-runner | orchestrator | export PATH="$HOME/.local/bin:$PATH"; timeout 120 uv run python -c " from dlt.common.normalizers.naming import snake_case n = snake_case.NamingConvention() print(n.normalize_identifier('1862 Land Grant College'), '\|', n.normalize_identifier('period_of_performance_potential_end_date_(v_text)'), '\|', n.normalize_identifier('Obligated Amount-From')) " 2>&1 \| tail -3 |
| E-69 | orchestrator-runner | orchestrator | python3 - <<'EOF' import pathlib p = pathlib.Path("tests/test_batch_load.py"); s = p.read_text() s = s.replace('def _lake_name(header_name):\n return header_name.lower().replace("-", "_")\n', 'def _lake_name(header_name):\n return snake_case.NamingConvention().normalize_identifier(header_name)\n') s = s.replace(' """The source column names of each lake table. dlt lowercases them and turns hyphens… |
| E-70 | orchestrator-runner | orchestrator | export PATH="$HOME/.local/bin:$PATH"; timeout 300 uv run python -m unittest tests.test_batch_load 2>&1 \| grep -v "^ File" \| head -30 \| cut -c1-200 |
| E-71 | orchestrator-runner | orchestrator | python3 - <<'EOF' import pathlib, re p = pathlib.Path("tests/test_batch_load.py"); s = p.read_text() s = s.replace("from dlt.common.normalizers.naming import snake_case\n", "") s = re.sub(r"def _lake_name\(header_name\):\n return snake_case\.NamingConvention\(\)\.normalize_identifier\(header_name\)\n\n\n", "", s) s = s.replace(' """The source column names of each lake table, named as dlt names th… |
| E-72 | orchestrator-runner | orchestrator | export PATH="$HOME/.local/bin:$PATH"; timeout 300 uv run python -m unittest tests.test_batch_load 2>&1 \| grep -v "^ File" \| grep -A4 "^FAIL" \| cut -c1-220 |
| E-73 | orchestrator-runner | orchestrator | export PATH="$HOME/.local/bin:$PATH"; timeout 200 uv run python -c " import csv, io, zipfile, pathlib, glob, tempfile import pyarrow.dataset as ds from dlt.common.normalizers.naming import snake_case n = snake_case.NamingConvention() z = sorted(glob.glob('data/raw/usaspending/FY2024_*_Contracts_Full_*.zip'))[0] with zipfile.ZipFile(z) as a: with a.open(a.namelist()[0]) as h: hdr = next(csv.reader… |
| E-74 | orchestrator-runner | orchestrator | python3 - <<'EOF' import pathlib, re p = pathlib.Path("tests/test_batch_load.py"); s = p.read_text() start = s.index("def _source_headers():") end = s.index("def _zips(kind):") s = s[:start] + s[end:] start = s.index(" def test_batchLoad_eachTable_addsOnlyLoadMetadataColumns(self):") end = s.index('\n\nif __name__ == "__main__":') new = ''' def test_batchLoad_eachTable_addsOnlyLoadMetadataColumns… |
| E-75 | orchestrator-runner | orchestrator | export PATH="$HOME/.local/bin:$PATH"; timeout 590 uv run python -m unittest discover -s tests -p 'test_*.py' 2>&1 \| tail -5 |
| E-76 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-77 | finding | R2 | Layer is still mixed after the spec-F03 fix. The unit suite now runs make build (batch load plus dbt build, most of the 67 s suite run) through tests/test_rerun.py, and tests/test_batch_load.py runs the real batch load against data/raw. tests/check_rerun.py is still a script in the unit test directory. End-to-end and unit tests share one directory and one discovery run. |
| E-78 | finding | R2 | test_consumer_replayAtLocalUrl_landsUniqueEdits still skips silently when the replay is down (self.skipTest) and checks only a prefix of a second, independent live read, so it can pass with few events landed. spec-F01 named both gaps; the skip and the independent-read comparison remain at HEAD 998515a. |
| E-79 | gate | orchestrator | FAIL test-benchmark-gate-code |
| E-80 | hard-stop | orchestrator | R2 test-benchmark still FAIL after two fix rounds: mean 6.33 (floor 7), assertion_strength 6, layer_correctness 6, mutation not run. Open: spec-F04 (layer mix, rerun test in discovery), spec-F05 (live replay test prefix only). |
| E-89 | fix-commit | E1 | fix(R2-F03): run the rerun check from the test suite |
| E-90 | fix-commit | E1 | fix(R2-F02): check row counts for every batch table |
| E-91 | fix-commit | E1 | fix(R2-F01): keep the live replay test deterministic |
| E-92 | fix-commit | E1 | fix(MF-6): drop the unused noqa and sort the test imports |
| E-93 | fix-commit | E1 | fix(types): annotate the variables and class attributes mypy could not infer |
| E-94 | fix-commit | E1 | fix(MF-5): test the keys of the two stream marts |
| E-95 | fix-commit | E1 | fix(MF-4): convert event_epoch to UTC wall clock, not the session zone |
| E-96 | fix-commit | E1 | fix(MF-8): compare the replay test with the ids the replay sent |
| E-97 | fix-commit | E1 | fix(MF-6, MF-9): bind the rerun query path and share the table readers |
| E-98 | fix-commit | E1 | fix(MF-7): add package markers to pipeline and tests |
| E-99 | fix-commit | E1 | fix(MF-3): use the 2021 Census estimate for counties with no 2024 row |
| E-100 | fix-commit | E1 | fix(MF-2): fail the batch load when a listed USAspending zip is missing |
| E-101 | fix-commit | E1 | fix(MF-1): skip events with wrong-typed fields |
