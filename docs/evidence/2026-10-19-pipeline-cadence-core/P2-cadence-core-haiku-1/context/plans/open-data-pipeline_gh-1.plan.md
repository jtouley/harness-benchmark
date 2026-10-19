# Plan: open-data pipeline (batch and stream) from raw files to Parquet marts

RUN_BY_COMMAND: plan-create

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
**Local ticket:** gh-1, file `.context/issues/gh-1.md`
**Branch:** feature/gh-1-pipeline
**Status:** draft, not reviewed. Next step: `/plan-review .cursor/plans/open-data-pipeline_gh-1.plan.md`

## Step 0: problem, decisions, blast radius, acceptance

### Problem restated

Build two analyst answers from public data.

- Question A (batch): federal contract and grant obligations in FY2024, by state, county, awarding agency and month, with obligations per person.
- Question B (stream): Wikipedia edits per wiki, namespace and 5-minute window, split by human and bot, with net bytes.

Ship a small Python engine that runs the pipeline from YAML. Ship a dbt project for everything after the lake. Publish marts as Parquet under `out/marts/`.

### Goal

- `make build` runs the batch part from `data/raw/` and fills `lake/` and `out/marts/`.
- Running `make build` twice changes no output content.
- `make stream DURATION=<seconds>` consumes the replay for that long and updates stream tables.
- Each of the seven analyst checks in the issue runs against a table or view listed in `oracle_map.yml`.

### Non-goals

- No scheduler, orchestrator or BI tool setup.
- No live run against `stream.wikimedia.org` as an acceptance step. The code takes the URL from YAML, so a live demo needs no code change.
- No change to the raw files under `data/raw/`.
- No support for FY years other than 2024.

### Design decisions (each one goes into `DECISIONS.md` when made)

- D1. Place of performance, not recipient, sets state and county for Question A. Reason: the question asks where money went. Record the choice in `DECISIONS.md`.
- D2. Population uses the July 1, 2024 estimate (`POPESTIMATE2024`) from `co-est2024-alldata.csv`, per Amendment A. A county with a blank 2024 value uses its latest earlier non-blank value from the same file. The 2021 file is a fallback only when the 2024 file has no row for the county. Record each fallback county in `DECISIONS.md`.
- D3. Money uses fixed-point decimals (Arrow `decimal128(18,2)` or wider) end to end. No float sums. Totals use exact decimal arithmetic in DuckDB or DataFusion.
- D4. The "award" in checks 3 and 4 means one `award_id` (FAIN for assistance, PIID for contracts) within FY2024. The net obligation is the sum of `federal_action_obligation` over its FY2024 transactions. Record the key choice in `DECISIONS.md`.
- D5. The lake holds source values. The ingestion step may cast a type when the cast loses no value. Any cast that can lose value is a failure, not a silent change.
- D6. Stream exactly-once comes from one atomic checkpoint. Each micro-batch writes its data files first. Then the checkpoint file moves into place with the new consumer position, the stream max event time and the batch file names. A restart deletes lake files that the checkpoint does not name.
- D7. The consumer drops a duplicate event by `meta.id`. It checks against ids already in the lake for the same window. The checkpoint keeps no full id list.
- D8. Lateness uses stream time. The running maximum event time includes every event that arrived before, including late events. The consumer sets the late flag at first arrival and never recomputes it.
- D9. dbt reads the lake through `read_parquet` sources. Ingestion never writes to `out/`.
- D10. YAML validation uses `jsonschema` against a schema under `engine/schemas/`. The error line comes from the PyYAML node marks.

### Blast radius

- New code: `engine/`, `pipelines/`, `transform/models/`, `transform/tests/`, `tests/`, `oracle_map.yml`, `DECISIONS.md`.
- Changed: `Makefile` (stub today), `pyproject.toml` and `uv.lock` (new dependencies), `transform/dbt_project.yml` and `transform/profiles.yml` (model paths and materialization).
- Unchanged: `data/raw/`, `.gitignore` (already ignores `lake/`, `out/`, `.context/`).
- `.gitignore` gates on `Makefile` and `transform/`. The implement gate applies to every phase.

### Acceptance

- All phases below pass their exit criteria.
- `make build` runs twice. Row content of every mart matches between runs.
- `make stream DURATION=<s>` run twice, with one interruption, adds no duplicate and loses no event.
- The seven checks return the expected values from the lake and marts. The values appear in `outputs/summary.md`.

## Reuse and extension

Existing pieces reused:

- `pyproject.toml` pins: `pyarrow==26.0.0`, `polars==2.0.0`, `datafusion==55.0.0`, `dbt-core==1.11.6`, `dbt-duckdb==1.11.0`, `duckdb==1.5.6`, Python `3.12`.
- `transform/dbt_project.yml` and `transform/profiles.yml` (profile `open_data_pipeline`, DuckDB file `out/warehouse.duckdb`).
- `Makefile` targets `build` and `stream` (stubs). The plan keeps these two target names.
- Raw inputs under `data/raw/` and their README files.

Extension point added:

- Engine registries keyed by YAML name. Source kinds: `file` (CSV, JSON, CSV inside ZIP) and `sse`. Transform engines: `polars` and `datafusion`. Sink kinds: `parquet_lake` and `parquet_lake_stream`. A new source or mart of these kinds needs YAML only.

The plan adds no other extension point. The engine has no plugin loader.

## Open questions to resolve during execution (not blocking)

- Q-a. The natural key of a USAspending transaction row. Profile it in Phase 3 and record it in `DECISIONS.md`.
- Q-b. Whether the contracts and assistance CSVs share a column set. Profile in Phase 3. Map columns by name, not by position.
- Q-c. The replayed hour. Read the first and last event time in Phase 7. Use it for check 5.

## Phases

Each phase starts with a failing test (TDD) unless the phase is pure configuration.
Each phase ends when its exit criteria pass and the local phase commit exists.

### Phase 1: Dependencies, test harness and Makefile wiring

Goal: a runnable skeleton that every later phase builds on.

Work:

1. Add dev dependencies: `pytest`. Add runtime dependencies: `pyyaml`, `jsonschema`, `httpx`. Use `uv add`. Commit `uv.lock`.
2. Create `engine/__init__.py`, `engine/__main__.py` (CLI entry: `python -m engine run <pipeline.yml>`).
3. Create `tests/` with one passing smoke test.
4. Replace the stub `Makefile`. Keep `build` and `stream`. `build` runs `uv run python -m engine run pipelines/batch.yml` and then `uv run dbt build --project-dir transform --profiles-dir transform`. `stream` runs `uv run python -m engine run pipelines/stream.yml --duration $(DURATION)` and then the dbt stream models.

TDD notes: the smoke test imports `engine` and checks the CLI exit code for `--help`.

Exit criteria:

- `uv run pytest` passes with at least one test.
- `uv run python -m engine --help` exits 0.
- `make stream` without `DURATION` prints a usage line and exits non-zero.

### Phase 2: Engine core with YAML validation

Goal: the engine reads a pipeline YAML, checks it, and runs steps in order.

Work:

1. Write `engine/schemas/pipeline.schema.json`. It covers `sources`, `transforms` and `sinks`. Each transform names its engine: `polars` or `datafusion`.
2. Write the loader. It parses YAML with PyYAML, checks with `jsonschema`, and maps each error path to a line number from the PyYAML node marks.
3. Write the runner. Steps pass Arrow tables or record batches. Each step names its inputs by name.
4. Write the registries for source, transform and sink kinds. Unknown kinds fail validation.

TDD notes: write these failing tests first.

- A YAML with an unknown transform engine fails. The error names the file, the line and the problem.
- A YAML with a missing sink fails with the same format.
- A valid two-step pipeline with an in-memory source returns the expected Arrow table.

Exit criteria:

- `uv run pytest` passes.
- An invalid YAML file exits non-zero and prints `file:line: problem`.

### Phase 3: Batch ingestion into the lake

Goal: the batch sources land in `lake/` with exact types and load metadata.

Work:

1. Profile the USAspending CSVs (assistance and contracts, all eight zips). Check column names, the natural key (Q-a) and whether the two shapes match (Q-b). Record the results in `DECISIONS.md`.
2. Write the `file` source for CSV inside ZIP. It reads from the zip without writing the CSV to disk.
3. Write the `parquet_lake` sink. It writes each source to `lake/<source>/`, partitioned by `awarding_agency_code` for USAspending. It adds `_source_file` and `_loaded_at`. It overwrites the source folder on each build, so a rebuild cannot duplicate rows.
4. Load the census file and the sitematrix JSON. Flatten the numeric keys of `sitematrix` into one row per site. Keep the `dbname`, `code`, `url` and `closed` fields.
5. Write `pipelines/batch.yml`.

TDD notes: write these failing tests first.

- A fixture zip with two rows parses to two rows with `federal_action_obligation` as decimal.
- A value that cannot cast to decimal fails the run. It does not become null.
- Running the sink twice on the same input gives the same row content.

Exit criteria:

- `make build` (batch part only, before dbt exists) writes `lake/usaspending/`, `lake/census/` and `lake/wikimedia_sites/`.
- Row counts per source appear in `outputs/summary.md`.
- Total FY2024 `federal_action_obligation` per source file equals the sum of the raw CSV values, computed by a separate script.

### Phase 4: dbt foundation over the lake

Goal: dbt reads the lake and runs its tests.

Work:

1. Write `transform/models/sources.yml` with one source per lake folder. Use `read_parquet` with the lake path.
2. Write staging models `stg_usaspending_transactions`, `stg_census_county_estimates`, `stg_wiki_sites`. Each staging model documents its grain.
3. Add `unique` and `not_null` tests on each staging key.

TDD notes: write a dbt test that fails on a duplicate key before the staging model that would hide it.

Exit criteria:

- `uv run dbt test --project-dir transform --profiles-dir transform` passes.
- `dbt parse` shows no warnings for the staging models.

### Phase 5: Star schema and monthly mart for Question A

Goal: the Question A star schema and the monthly mart exist, with contracts enforced.

Work:

1. `dim_agency`: one row per awarding agency code (D-level choice of name source recorded in `DECISIONS.md`).
2. `dim_place`: one row per state and county, from the place-of-performance fields (D1). Include FIPS codes.
3. `dim_date`: one row per calendar day in FY2024 (from `action_date`).
4. `fct_award_transaction`: grain is one award transaction. Columns include the natural key, `federal_action_obligation` as decimal, and the three dimension keys. Materialized as table.
5. `mart_obligations_monthly`: grain is one month, state, county and agency. Columns: `net_obligations`, `population_2024`, `obligations_per_person` (decimal, rounded only at output).
6. Model contracts on both marts (column names and types enforced). Tests on each key.
7. `dim_place` and `mart_obligations_monthly` join population on FIPS. Apply D2 and record each fallback.

TDD notes: write these failing dbt tests first.

- A county without a 2024 value takes the fallback. The test checks that `DECISIONS.md` lists it.
- Net obligations for a state equals the sum of its county rows.

Exit criteria:

- `dbt build` passes for these models.
- `mart_obligations_monthly` has one row per month, state, county and agency with transactions.

### Phase 6: Batch checks and the idempotence proof

Goal: the batch answers the Question A checks, and a second build changes nothing.

Work:

1. Write `oracle_map.yml`. Map checks 1 to 4 to a table or view and a column.
2. Write the check queries as dbt singular tests or views. Check 3 counts awards with negative net obligation (D4).
3. Check 4 uses one month. County totals sum to state totals. State totals sum to the source total from Phase 3.
4. Write `tests/test_idempotence.py`. It runs the batch build twice in a temp directory and compares mart row content. It compares rows, not file bytes.
5. Write the check 2 query: top ten counties by obligations per person.

TDD notes: write a check 4 test that fails when one county row is dropped.

Exit criteria:

- `make build` passes twice in a row. The idempotence test passes.
- Checks 1 to 4 return values recorded in `outputs/summary.md`.

### Phase 7: Stream source and atomic micro-batch sink

Goal: the consumer reads the SSE stream, resumes after a disconnect and never counts an event twice.

Work:

1. Write the `sse` source with `httpx` streaming. It parses `id`, `event` and `data` lines. It keeps the last `id` value.
2. On disconnect, reconnect with the `Last-Event-ID` header set to the last committed id. Use backoff from YAML.
3. Write the `parquet_lake_stream` sink. Each micro-batch writes its data files first, into a temporary name. Then the sink writes `lake/_state/recentchange.json` by atomic rename. The file holds the consumer position, the stream max event time and the batch file names (D6).
4. On startup, the sink deletes lake files under the stream folders that the checkpoint does not name.
5. Dedup by `meta.id` against ids already in the lake for the same window (D7).
6. Write `pipelines/stream.yml`. The URL is a YAML value. The default is `http://localhost:8099/v2/stream/recentchange`.

TDD notes: write these failing tests first.

- A fake SSE server drops the connection after five events. The consumer resumes and the final count equals the number of events the server sent.
- A crash injected after the data write and before the checkpoint rename leaves no duplicate on restart.
- The consumer drops a duplicate `meta.id` from the server.

Exit criteria:

- `uv run pytest` passes these tests.
- `make stream DURATION=60` writes events to `lake/recentchange/` and a checkpoint to `lake/_state/`.

### Phase 8: Event time, windows and lateness

Goal: each stream event gets its window and its late flag at first arrival (D8).

Work:

1. Parse `meta.dt` as event time. Window start is `floor(ts / 300) * 300` in UTC. Window end is start plus 300 seconds.
2. Keep the running maximum event time in the checkpoint. Update it with every arrived event, late or not.
3. An event is late when the running maximum before it is more than 600 seconds after its window end. Set `is_late` at first arrival. Never change it later.
4. Late events go to `lake/recentchange_late/`. They are also kept in `lake/recentchange/` with `is_late = true`, so check 5 counts them.
5. Net bytes is `length.new - length.old` as an integer. A missing length gives null bytes. The event still counts (record in `DECISIONS.md`).
6. Actor type is `bot` when the `bot` field is true, otherwise `human`.

TDD notes: write these failing tests first.

- An event exactly 600 seconds after the window end is on time.
- An event 601 seconds after the window end is late, and a late event still moves the running maximum.
- Replaying the same sequence in two chunks gives the same flags as one chunk.

Exit criteria:

- The unit tests pass.
- The late-event count in the replay matches the count from a separate pass over the captured events.

### Phase 9: Stream dbt models

Goal: dbt builds the edit fact and the window mart from the lake, incrementally.

Work:

1. `fct_edit`: grain is one change event (`meta.id`). Includes `is_late`, `wiki` (dbname), `server_name`, `namespace`, `actor_type`, `net_bytes`. Incremental on `meta.id`, unique key.
2. `mart_edit_window_5min`: grain is one window, wiki, namespace and actor type. Counts and net bytes count on-time edits only (for check 6). Incremental. Each run recomputes the windows that the new batch touches.
3. Add a view or a second column for the all-edit count used by check 5, so check 5 counts late events.
4. `wiki` dimension joins `wiki_sites` on dbname, so `en.wikipedia.org` maps to `enwiki`. Record the mapping in `DECISIONS.md`.
5. Contracts and key tests on both models.

TDD notes: write a failing dbt test that a window total equals the sum of its on-time edits.

Exit criteria:

- `dbt build` passes after `make stream DURATION=<s>`.
- Running `dbt build` again with no new batch changes no row.

### Phase 10: End-to-end run, checks 5 to 7, and deliverables

Goal: the full pipeline runs, and the stream checks give the expected values.

Work:

1. Run `make build` twice. The row content of every mart must match.
2. Run `make stream DURATION=<s>` with one forced interruption. Compare the edit count with the number of events the replay sent.
3. Answer checks 5 to 7 from the stream tables. Check 5 counts all edits, late included. Check 6 uses on-time edits only on `en.wikipedia.org`. Check 7 counts late events.
4. Add check 5 to 7 rows to `oracle_map.yml`.
5. Write `DECISIONS.md` in full. Each D-number and each open question has an entry.
6. Write `outputs/summary.md` with the check values, the counts and the commands run. Write `outputs/PR.md` with the PR text. Run `ste-lint.py` on both files and fix each hard violation.

Exit criteria:

- `make build` twice matches. `make stream` with interruption matches the sent count.
- `uv run pytest` passes.
- `uv run dbt test --project-dir transform --profiles-dir transform` passes.
- `outputs/summary.md` and `outputs/PR.md` exist under the scratchpad outputs directory.

## Quality gate commands (repo)

- `make build`
- `make stream DURATION=<seconds>`
- `uv run pytest`
- `uv run dbt test --project-dir transform --profiles-dir transform`

These are the commands from the issue. The Makefile is a stub today. Check each command after Phase 1 replaces the stub.

## Footer

Next step: `/plan-review .cursor/plans/open-data-pipeline_gh-1.plan.md`.
Do not run `/plan-update` until a review file exists under `.context/reviews/`.

---

## Plan update 1 (2026-10-19)

RUN_BY_COMMAND: plan-update

**Source review:** `.context/reviews/plan_open-data-pipeline_gh-1.md` (Verdict: READY WITH CHANGES, six must-fix items).
**Scope:** this update applies MF-1 to MF-6. The notes N-1 to N-12 are not applied here.
**Precedence:** the text above stays unchanged. Where this section and an earlier phase differ, this section wins.

### MF-1: marts are written to `out/marts/`

- Phase 5 adds work item 8. The `Makefile` `build` target runs `mkdir -p out/marts`.
- A dbt `on-run-end` hook calls the macro `export_marts()`. The macro reads the list of mart models from the `dbt_project.yml` variable `export_marts`. For each mart, it runs `COPY <mart> TO 'out/marts/<mart>/part-0.parquet' (FORMAT PARQUET)`.
- dbt writes the marts. Ingestion does not write to `out/` (D9).
- Phase 9 adds `mart_edit_window_5min` and `late_events` to the `export_marts` list.
- Phase 10 exit criterion: after `make build`, each `out/marts/<mart>/part-0.parquet` exists. Its row count equals `select count(*)` of that mart in `out/warehouse.duckdb`.

### MF-2: the late-event table

- Lake: `lake/recentchange_late/` holds the late rows. Phase 8 item 4 writes them there, unchanged.
- dbt: the model `late_events` is a table over `read_parquet` of `lake/recentchange_late/`. Its grain is one late change event, keyed by `meta_id`. Its columns are the columns of `fct_edit` plus `window_start` and `window_end`.
- `fct_edit` keeps every event. Late events have `is_late = true` (Phase 9 item 1, unchanged). Record this choice in `DECISIONS.md`. It lets check 5 count all edits.
- `mart_edit_window_5min` counts on-time events only. A late event is not added to its window.
- Phase 10 item 4 adds these rows to `oracle_map.yml`:
  - Check 5: table `fct_edit`, count of `meta_id`, all edits.
  - Check 6: table `mart_edit_window_5min`, on-time count, wiki `enwiki`.
  - Check 7: table `late_events`, count of `meta_id`.

### MF-3: idempotence and `_loaded_at`

- Phase 3 item 3 changes. `_loaded_at` is the source file modification time in UTC, read with `os.stat`. It is not the wall clock. `_source_file` is the repo-relative path of the source file. A rebuild writes the same values.
- The idempotence rule covers lake rows and mart rows.
- Phase 3 TDD adds a failing test: two batch runs on the same input give identical lake rows, including `_loaded_at` and `_source_file`.
- Phase 6 item 4 compares lake rows and mart rows.
- The stream lake is outside this rule. Each `meta.id` is written once (D7).

### MF-4: rows without a place of performance

- Phase 5 item 2 adds one unknown member to `dim_place`: `state_fips = '00'`, `county_fips = '000'`, name `Unknown place`.
- A transaction with a blank or non-US state or county maps to this member. No row is dropped.
- Phase 5 TDD adds a failing test. The FY2024 sum of `federal_action_obligation` in `fct_award_transaction` equals the Phase 3 source total exactly. The state rows plus the unknown row equal that total. For every state, including `00`, the county sum equals the state sum.
- Record the rule in `DECISIONS.md` under D1.

### MF-5: unique key for the window mart

- Phase 9 item 2 adds the composite unique key `(window_start, wiki, namespace, actor_type)`.
- The incremental strategy is `delete+insert` on that key list. Each run deletes the rows for the windows the new batch touches, then inserts the recomputed rows.
- Phase 9 TDD adds a failing singular test, `transform/tests/assert_window_unique.sql`. It returns each key that appears more than once.

### MF-6: source of the sent count

- Phase 7 item 6 adds the key `replay_capture` to `pipelines/stream.yml`. Its value is a JSON Lines file path. The replay side writes one line per event sent, with `meta.id`.
- The Phase 7 fake SSE server writes the same file, so the unit tests use it.
- Phase 10 item 2: the sent count is the line count of the capture file. The distinct `meta_id` count in `fct_edit` for the replay window must equal it, and the duplicate count must be 0.
- Phase 10 exit criterion adds this equality check.
- If the replay server cannot write the capture file, the run fails. The plan accepts no count from another source. The blocker goes into `DECISIONS.md`.

### Carried review item map

| Item | Settled in |
|------|------------|
| MF-1 | Phase 5 item 8, Phase 9 `export_marts` list, Phase 10 exit criteria |
| MF-2 | Phase 8 item 4, Phase 9 item 1, Phase 10 item 4 |
| MF-3 | Phase 3 item 3 and its TDD notes, Phase 6 item 4 |
| MF-4 | Phase 5 item 2 and its TDD notes |
| MF-5 | Phase 9 item 2 and its TDD notes |
| MF-6 | Phase 7 item 6, Phase 10 item 2, Phase 10 exit criteria |

Next step: the orchestrator runs `/plan-review .cursor/plans/open-data-pipeline_gh-1.plan.md` on this plan.

---

## Plan update 2 (2026-10-19)

RUN_BY_COMMAND: plan-update

**Source review:** `.context/reviews/plan_open-data-pipeline_gh-1.md` (cycle 2, Verdict: READY WITH CHANGES, six must-fix items MF-1 to MF-6 of that review).
**Scope:** this update applies the six must-fix items of cycle 2. The notes N-1 to N-14 are not applied here. The labels MF-1 to MF-6 in this section are the cycle 2 labels. They are not the labels of plan update 1.
**Precedence:** the text above stays unchanged. Where this section and an earlier part differ, this section wins.

### MF-1 (cycle 2): command for the batch part in Phase 3

- The Phase 3 exit criterion that says `make build` (batch part only) is replaced by this criterion: `uv run python -m engine run pipelines/batch.yml` writes `lake/usaspending/`, `lake/census/` and `lake/wikimedia_sites/`.
- Phase 3 does not run `make build`. `make build` also runs `dbt build`, and no dbt model exists before Phase 4.
- From Phase 4 on, `make build` runs both parts, as Phase 1 item 4 states.

### MF-2 (cycle 2): checkpoint rules for startup cleanup

Phase 7 item 3 is replaced by these rules. D6 is read the same way.

- a. Each micro-batch writes its data files under a temporary name in the stream folder. Then it renames each file to its final name. All renames of the micro-batch finish before the checkpoint is written.
- b. The checkpoint `lake/_state/recentchange.json` names the final file name of every committed data file of the run. It does not name only the files of the latest micro-batch. The list grows with each micro-batch.
- c. The checkpoint never names a temporary name.
- d. The checkpoint rename is the last step of a micro-batch.

Phase 7 item 4 is read with these rules. On startup, the sink deletes every file under `lake/recentchange/` and `lake/recentchange_late/` that the checkpoint does not name. It also deletes every temporary name.

TDD addition (write it first): two micro-batches commit, then the sink restarts. Both batches keep their files. The lake row count equals the number of committed events.

### MF-3 (cycle 2): fields of the capture file

Each line of the replay capture file holds three fields:

- `meta.id`, the event id.
- `meta.dt`, the event time as sent.
- `seq`, the arrival sequence number. It is an integer that starts at 1 and counts the events in the order the server first sends them.

Phase 8 exit criterion, replaced: the late-event count from the replay equals the count from a separate pass over the capture file. The separate pass sorts the lines by `seq`. It applies the rule of Phase 8 item 3 with the running maximum. The code for this pass lives in `tests/test_late_count.py`.

### MF-4 (cycle 2): writer of the sent count

- The replay server at `localhost:8099` is the only writer of the sent count. The consumer does not write it.
- Each run writes one capture file at `.context/replay/recentchange_<run_id>.jsonl`. The `<run_id>` is the UTC start time of the run in the form `YYYYMMDDTHHMMSSZ`. The `.context/` folder is ignored by git, so the file stays out of git.
- The server writes one line when it first sends an event. A resend after a reconnect adds no line.
- The `make stream` target sets the `<run_id>`. It passes the capture path to the replay server and the `<run_id>` to the engine.
- `pipelines/stream.yml` key `replay_capture` names the directory `.context/replay/`. This replaces the file path of update 1, MF-6.
- The replay window of a run is the first and last `meta.dt` in its capture file. This answers Q-c for the stream checks.
- If the replay server cannot take the capture path, the run fails. The blocker goes into `DECISIONS.md`, as update 1 MF-6 states.

### MF-5 (cycle 2): two stream runs

- Each run writes its own capture file, as MF-4 states. The two runs share no capture file.
- The stream lake is shared. The lake keeps the rows of both runs. D7 keeps each `meta.id` once per window.
- Phase 10 item 2 is replaced by these steps:
  - Run 1: `make stream DURATION=<s>` with one forced interruption. The interruption kills the engine process once. The engine restarts with the same checkpoint.
  - Run 2: `make stream DURATION=<s>` with no interruption.
  - For each run, the replay window comes from its capture file (MF-4).
  - For each run, the distinct `meta_id` count in `fct_edit` for the replay window equals the line count of its capture file. Every `meta.id` of the capture file is in `fct_edit`.
  - The two replay windows must not overlap. If they overlap, the run fails and the blocker goes into `DECISIONS.md`.
- Phase 10 exit criteria add: both runs pass the check above, and the duplicate count in `fct_edit` for each window is 0.

### MF-6 (cycle 2): fallback test on the data

The Phase 5 TDD note "A county without a 2024 value takes the fallback. The test checks that `DECISIONS.md` lists it." is replaced by these data tests:

- Fixture: one county row in `co-est2024-alldata.csv` with a blank `POPESTIMATE2024` and non-blank values for earlier years. Assert that `population_2024` in `dim_place` and in `mart_obligations_monthly` for that county equals the value of the latest earlier non-blank `POPESTIMATE` column of the same row.
- Fixture: one county with no row in the 2024 file and a row in the 2021 file. Assert that its `population_2024` equals its 2021 value.
- The `DECISIONS.md` entry for each fallback county is a separate Phase 5 work item. It is not a test.

### Carried review item map (cycle 2)

| Item | Settled in |
|------|------------|
| MF-1 | Phase 3 exit criteria (this section) |
| MF-2 | Phase 7 items 3 and 4 (rules a to d), D6, the Phase 7 TDD addition |
| MF-3 | Phase 7 item 6 (capture fields), Phase 8 exit criteria, `tests/test_late_count.py` |
| MF-4 | MF-4 section, Phase 7 item 6, Phase 10 item 2 |
| MF-5 | Phase 10 item 2 and its exit criteria |
| MF-6 | Phase 5 TDD notes (this section) |

Next step: the orchestrator runs `/plan-review .cursor/plans/open-data-pipeline_gh-1.plan.md` in a new Agent call. This update does not run it.

---

## Plan update 3 (2026-10-19)

RUN_BY_COMMAND: plan-update

**Source review:** `.context/reviews/plan_open-data-pipeline_gh-1.md` (cycle 3, Verdict: READY WITH CHANGES, five must-fix items MF-1 to MF-5 of that review).
**Scope:** this update applies MF-1 to MF-5 of cycle 3. The notes N-a to N-p of cycle 3 are not applied here. The labels MF-1 to MF-5 in this section are the cycle 3 labels.
**Precedence:** the text above stays unchanged. Where this section and an earlier part differ, this section wins.

### MF-1 (cycle 3): the lake folder that `fct_edit` reads

- `fct_edit` reads `lake/recentchange/` only. It never reads `lake/recentchange_late/`.
- Phase 8 item 4 stays as written. A late event is written to both folders. The copy in `lake/recentchange/` is the one `fct_edit` reads. The copy in `lake/recentchange_late/` is the one `late_events` reads.
- Each `meta.id` appears once in `fct_edit`. Phase 7 item 5 (D7) is amended: the dedup check reads the ids in both `lake/recentchange/` and `lake/recentchange_late/` for the same window. A late event that the server resends is dropped in both folders.
- Phase 9 TDD adds a failing singular test, `transform/tests/assert_fct_edit_unique.sql`. It returns each `meta_id` that appears more than once in `fct_edit`. A second failing singular test, `transform/tests/assert_late_rows_match.sql`, returns each row where `is_late` differs from membership in `late_events`.
- `DECISIONS.md` records the rule: `lake/recentchange/` is the single source of `fct_edit`.

### MF-2 (cycle 3): replay control interface and capture writer

The plan does not name a control interface on the replay server at `localhost:8099`. The cycle 3 probe found none documented. The plan does not depend on one. This section replaces the writer rule of update 2 MF-4 and the capture rules of update 2 MF-3 and MF-5.

Fallback that the repo controls:

- The consumer (the engine) writes the capture. The replay server does not write it. The server sends events only. The server needs no new interface.
- The `make stream` target sets `RUN_ID` (UTC, `YYYYMMDDTHHMMSSZ`) once per run. It passes `RUN_ID` to the engine. A restart after a forced interruption passes the same `RUN_ID`.
- Each run writes its capture to the directory `.context/replay/<RUN_ID>/`. The directory is in `.context/`, which git ignores.
- Each micro-batch writes one segment file, `batch-<n>.jsonl`. It writes the segment under a temporary name first, then renames it to the final name. The rename happens before the checkpoint rename (update 2 MF-2 rules a to d apply).
- One line per distinct `meta.id` that the run receives for the first time. A resend after a reconnect adds no line. Each line holds `meta.id`, `meta.dt` and `seq`. `seq` starts at 1 for each run and counts in arrival order. The checkpoint holds the next `seq` value and the next segment number, so a restart inside the run keeps them.
- Sent-count rule, stated with its limit: the sent count is the line count of the run's capture. It counts the events the consumer received. It equals the number of events the server sent only if the server sends each event once and the connection loses none. The consumer cannot see the server's own count. So this fallback does not fully meet update 2 MF-4. `DECISIONS.md` records this as an open risk and as a decision the user must accept.
- If the server offers a control interface later, the implementer records it in `DECISIONS.md`. Then the plan may switch to it in a new update. This update does not depend on it.
- `pipelines/stream.yml` key `replay_capture` names the directory `.context/replay/`.

### MF-3 (cycle 3): replay start of each run

- Each run starts a new replay. At run start the engine sends no `Last-Event-ID` header. The engine sends `Last-Event-ID` only to reconnect inside one run. The checkpoint's consumer position from an earlier run is not used at run start.
- The engine does not choose where the replay starts. The replay starts at the position the server offers at connect time.
- If the server sends an event that the run's capture already holds, the sink drops it as a duplicate (D7). If the server returns an event that an earlier run already sent, that event is first in the current run's capture. Its `meta.id` is then in two captures. This is the overlap failure below.
- Overlap rule, checked at run end. A run fails, with a non-zero exit, when either test is true:
  - The run's replay window (first `meta.dt` to last `meta.dt` of its capture) intersects the window of an earlier run.
  - Any `meta.id` in the run's capture also appears in an earlier run's capture.
- On failure the engine writes the reason to `DECISIONS.md` as a blocker, as update 1 MF-6 requires.
- Phase 7 TDD adds a failing test: run 2 starts with an event that run 1 already sent. The run fails with the overlap message.

### MF-4 (cycle 3): check 5 model and net bytes

- Check 5 uses one model. It is the dbt view `v_check5_edits`, with grain one wiki and one `actor_type` in one replay window.
- Columns: `wiki`, `actor_type`, `edit_count` (count of `meta_id`, all edits, late included) and `net_bytes_sum` (sum of `net_bytes` over the same rows). Null `net_bytes` values add nothing to the sum. The event still counts in `edit_count` (Phase 8 item 5).
- The replay window of check 5 is the run's replay window (MF-3 above). The view filters `event_time` between the first and last `meta.dt` of that run. If `DURATION` is less than 3600 s, check 5 covers the shorter window. The output names the window. It does not say "one hour".
- Phase 9 item 3 is replaced. The view `v_check5_edits` replaces the "view or second column" choice.
- Phase 10 item 4 oracle rows for check 5 are replaced:
  - Check 5, edits: view `v_check5_edits`, sum of `edit_count` for the replay window.
  - Check 5, net bytes: view `v_check5_edits`, sum of `net_bytes_sum` for the replay window.
- Phase 9 TDD adds a failing singular test, `transform/tests/assert_check5_matches_lake.sql`. For one replay window, the sum of `net_bytes_sum` in `v_check5_edits` equals the sum of `net_bytes` computed directly from the lake rows in `lake/recentchange/` for the same window. It also checks that the sum of `edit_count` equals the count of those lake rows.

### MF-5 (cycle 3): one DataFusion transform

- Phase 3 item 5 is replaced by this list, with the same `pipelines/batch.yml` file:
  - One SQL transform with `engine: datafusion`, named `usaspending_map`. It runs on the USAspending source before the sink. It maps the source columns to the lake column names by name, not by position (Q-b). It casts `federal_action_obligation` to `decimal128(18,2)`. A cast that loses value fails the run (D5).
  - The `parquet_lake` sink writes `lake/usaspending/` from the output of `usaspending_map`.
  - The census and sitematrix steps keep their Polars or Python transforms, as Phase 3 item 4 states.
- Phase 3 TDD adds a failing test first: `tests/test_datafusion_map.py`. Two CSV files with the same columns in a different order map to the same lake schema. A value with more decimal places than the cast allows fails the run.
- Phase 2 item 4 already registers `datafusion`. No change there.

### Carried review item map (cycle 3)

| Item | Settled in |
|------|------------|
| MF-1 | Phase 7 item 5 (amended), Phase 9 TDD (two singular tests), `DECISIONS.md` rule |
| MF-2 | MF-2 section of this update (fallback capture, consumer writer, segment rules), Phase 7 item 6 |
| MF-3 | MF-3 section of this update (new run start, overlap rule), Phase 7 TDD, Phase 10 item 2 |
| MF-4 | MF-4 section of this update (`v_check5_edits`, net bytes test), Phase 9 item 3, Phase 10 item 4 |
| MF-5 | MF-5 section of this update (`usaspending_map`), Phase 3 item 5, Phase 3 TDD |

Phase 10 item 2 is read with update 2 MF-5 and the capture rules of MF-2 in this update. The sent count is the line count of the run's capture segments, not one capture file.

Next step: the orchestrator runs `/plan-review .cursor/plans/open-data-pipeline_gh-1.plan.md` in a new Agent call. This update does not run it.

---

## Plan update 4 (2026-10-19)

RUN_BY_COMMAND: plan-update

**Source review:** `.context/reviews/plan_open-data-pipeline_gh-1.md` (cycle 4, Verdict: READY WITH CHANGES, three must-fix items MF-1 to MF-3 of that review).
**Scope:** this update applies MF-1 to MF-3 of cycle 4. It also applies cycle 4 notes N-r, N-s and N-t. The labels MF-1 to MF-3 in this section are the cycle 4 labels. Cycle 3 notes N-a to N-p and cycle 4 note N-u are not applied here.
**Precedence:** the text above stays unchanged. Where this section and an earlier part differ, this section wins.

### MF-1 (cycle 4): order of capture and lake dedup

Phase 7 item 5 (D7, amended by update 3 MF-1) is replaced. Each arrived event runs these steps in this order:

1. If the `meta.id` is already in this run's capture, the event is a resend within this run. Drop it. Write no line.
2. Otherwise, write one capture line for the `meta.id` into the current segment (update 3 MF-2). This happens before any lake check.
3. Then run the lake dedup. Check the ids in `lake/recentchange/` and `lake/recentchange_late/` for the same window. If the id is already there, drop the event from the lake write. The capture line from step 2 stays.
4. Otherwise, add the event to the micro-batch.

Step 2 is the only step that writes a capture line. A lake drop in step 3 never removes a line.

Phase 7 TDD adds a failing test, written first: run 1 writes an event to the lake. Run 2 receives the same event. Run 2 must fail with the overlap message of update 3 MF-3. The `meta.id` must appear once in `fct_edit`.

### MF-2 (cycle 4): loss detection limit

The plan takes option (b) of cycle 4. The plan does not add an independent count, because the replay server offers no file that the repo can read.

- Step 0 acceptance, second bullet, is replaced: "`make stream DURATION=<s>` run twice, with one interruption, adds no duplicate. This plan does not detect loss of an event that the consumer never received. See D11."
- Phase 10 item 2 proves two things only: no duplicate, and every capture line is in the lake. It does not prove that no event was lost before the consumer received it.
- The summary in `outputs/summary.md` states this limit next to the check values.
- New decision D11, an open decision for the user: "Loss limit. The capture counts the events that the consumer received. A loss before the consumer receives an event is not detected. The user must accept this limit, or name an independent count source by a new plan update. E1 does not start until D11 is recorded in `DECISIONS.md`."

### MF-3 (cycle 4): replay start probe before the sink

Phase 7 gets a new item 2a. It runs before item 3, the sink write. Items 1 and 2 stay as written.

2a. Probe the replay start. Run one probe script:

- Connect to the stream URL with no `Last-Event-ID` header. Read the first event and record its `meta.id`. Close the connection.
- Connect again, again with no header. Record the first `meta.id` of this connect. Close the connection.
- Write both ids and both connect times to `DECISIONS.md`.

Decision rule:

- The two first ids differ. Result: CONTINUE. The server does not repeat the start position. Go on to item 3.
- The two first ids are the same. Result: BLOCKED. Two runs overlap by design (update 3 MF-3). Stop Phase 7 here. Do not write item 3 or later. Write the blocker and both ids to `DECISIONS.md`. Phases 8 to 10 do not start. The Phase 10 exit criteria are not met. The plan does not say otherwise.
- In the BLOCKED case, the user decides the next step. The user may choose one of these, by a new plan update: (i) drop the two-run exit criterion of Phase 10 and the overlap rule for the second run, or (ii) use a replay source or a replay control that starts at a new position. The implementer does not choose.

Phase 7 TDD adds two failing tests, written first, for the decision rule: two connects that return the same first id give BLOCKED. Two connects that return different first ids give CONTINUE.

### Notes applied

- N-r (check 5 window). Check 5 is a window check. The grader does not need `DURATION=3600`. The output states the window length in seconds, from the first to the last `meta.dt` of the replay. The output does not say "one hour".
- N-s (path for the line count). Phase 10 item 2 reads the sent count from the capture segments `.context/replay/<RUN_ID>/batch-*.jsonl`. It counts the lines of all segments of one run. The summary names this path.
- N-t (resend in another window). A resend carries the same `meta.dt` as the first copy. The window comes from `meta.dt` (Phase 8 item 1). So a resend falls in the same window as its first copy. The dedup of Phase 7 item 5 finds it there. No further rule is needed.

### Phase 10 changes (this section)

- Phase 10 item 2 is read with MF-1, MF-2 and MF-3 of this section and with the N-s path above.
- Phase 10 exit criterion "both runs pass the two-run check" applies only when the probe of item 2a returns CONTINUE.

### Carried review findings (update 4 table, superseded by update 5)

| Finding | Status | Settled in | Test or evidence |
|---------|--------|------------|------------------|
| MF-1 (cycle 4) | open until plan-review | Phase 7 item 5 (this section) | Phase 7 TDD: run 2 receives a run 1 event |
| MF-2 (cycle 4) | open until plan-review | Step 0 acceptance (this section), D11, Phase 10 item 2 | `DECISIONS.md` holds D11. `outputs/summary.md` states the limit |
| MF-3 (cycle 4) | open until plan-review | Phase 7 item 2a (this section) | Phase 7 TDD: two probe decision tests |

Next step: the orchestrator runs `/plan-review .cursor/plans/open-data-pipeline_gh-1.plan.md` in a new Agent call. This update does not run it.

---

## Plan update 5 (2026-10-19)

RUN_BY_COMMAND: plan-update

**Source review:** `.context/reviews/plan_open-data-pipeline_gh-1.md` (cycle 5, Verdict: READY WITH CHANGES, four must-fix items MF-1 to MF-4 of that review).
**Scope:** this update applies MF-1 to MF-4 of cycle 5. The labels MF-1 to MF-4 in this section are the cycle 5 labels. Cycle 5 notes N-a to N-f are not applied here.
**Precedence:** this section wins over all earlier text. The earlier text stays unchanged.
**Loop status:** this is the last plan update. Cycle 5 is the fifth review. No `/plan-review` run follows from this update.

### MF-1 (cycle 5): open micro-batch and uncommitted segments

- Micro-batch size and commit trigger. `pipelines/stream.yml` key `batch_size` sets the number of events in one micro-batch. The default is 50. A micro-batch commits when it holds `batch_size` events, before any reconnect, and at run end. The commit runs the rules of update 2 MF-2 (a to d) and the segment rules of update 3 MF-2.
- Phase 7 item 2 is amended. Before any reconnect inside a run, the engine commits the open micro-batch. Then it sends `Last-Event-ID` set to the last committed id. The reconnect point equals the last commit.
- Phase 7 item 3 is amended. The checkpoint also names the committed capture segments `.context/replay/<RUN_ID>/batch-<n>.jsonl` by their final names. The checkpoint never names a temporary name.
- Phase 7 item 4 is amended. On startup, the sink deletes each capture segment under `.context/replay/<RUN_ID>/` that the checkpoint does not name. It also deletes each lake file that the checkpoint does not name (update 2 MF-2). After this cleanup, the capture holds only committed lines.
- Phase 7 item 5 (update 4 MF-1) reads the capture after the startup cleanup. An event that the server resends after a crash is then not in the capture and not in the lake. The engine captures it and writes it.
- Phase 7 TDD adds two failing tests, written first:
  - `batch_size` is 3. A fake SSE server drops the connection after 5 events. The engine commits the first 3 events before it reconnects. The final `fct_edit` count equals the number of distinct events the server sent.
  - A crash happens after the capture write and before the checkpoint rename. On restart, the uncommitted segment is deleted. The server resends those events. The final `fct_edit` count equals the number of events the server sent.

### MF-2 (cycle 5): accepted loss limit and the BLOCKED path

- Step 0 acceptance, second bullet (update 4 MF-2), is replaced by: "`make stream DURATION=<s>` run twice, with one interruption, adds no duplicate. Every event that the consumer receives is in the lake. Loss before the consumer receives an event is not checked. D11 records this limit."
- The issue requires that the consumer counts no event twice and loses none. This plan checks duplicates and loss between capture and lake. It does not check loss before the consumer receives an event.
- D11 (update 4 MF-2) is replaced: "Loss limit. The plan does not check loss before the consumer receives an event. The implementer records this as the accepted default in `DECISIONS.md` and follows it. The user may review D11 after the run. The review is not a gate for E1, and it does not stop Phase 10."
- Phase 10 item 2 proves two things: no duplicate, and every capture line is in the lake. The summary in `outputs/summary.md` states the limit next to the check values.
- If a check cannot run, the summary marks it `NOT RUN` with the reason. The summary does not mark a check as passed when it did not run.
- The BLOCKED path of update 4 MF-3 is replaced. The implementer does not stop Phase 7 on BLOCKED. On BLOCKED, the implementer:
  - writes the blocker and both ids to `DECISIONS.md`,
  - applies the overlap warning rule of MF-3 below,
  - continues with Phase 7 item 3 and later, then Phases 8 to 10.
- Phase 7 TDD test for the probe (update 4 MF-3) is kept. Two connects with the same first id give BLOCKED. The run continues. The test checks the warning in `DECISIONS.md`.

### MF-3 (cycle 5): overlap is a warning, and the two-run check uses membership

- The overlap rule of update 3 MF-3 is replaced. An overlap between runs never fails a run. The engine writes a warning to `DECISIONS.md` and exits 0 when either test is true:
  - The run's replay window intersects the window of an earlier run.
  - A `meta.id` in the run's capture also appears in an earlier run's capture.
- The update 4 MF-1 test is replaced. Run 2 receives an event that run 1 wrote to the lake. Run 2 exits 0 and writes the overlap warning. The `meta.id` appears once in `fct_edit`.
- Phase 10 item 2, two-run check, is replaced. For each run, every `meta_id` in its capture segments is in `fct_edit`. The duplicate count in `fct_edit` is 0. The check does not compare a distinct count with a line count, because a second run may overlap the first.
- The two-run check runs for both probe results. The update 4 condition that limits it to CONTINUE is removed.

### MF-4 (cycle 5): acceptance window for checks 5 to 7

- The acceptance run for checks 5 to 7 is run 1 of Phase 10 item 2. Its command is `make stream DURATION=3600`.
- Check 5 covers the replay window of run 1, from the first to the last `meta.dt` of its capture. The view `v_check5_edits` filters on that window.
- `outputs/summary.md` states the window length in seconds. If the window is shorter than 3600 seconds, `DECISIONS.md` records the length and the reason. The output does not call the window "one hour".
- The note N-r (update 4) is replaced by this rule. The implementer does not make a claim about the grader.

## Carried review findings

This table replaces the update 4 table for the open findings. The cycle 4 findings are settled by update 4 and are not reopened.

| Finding | Status | Settled in | Test or evidence |
|---------|--------|------------|------------------|
| MF-1 (cycle 5) | carried to E1 | Phase 7 items 2, 3, 4 and 5 (update 5 MF-1), `batch_size` in `pipelines/stream.yml` | Phase 7 TDD: reconnect with an open micro-batch, crash before checkpoint rename |
| MF-2 (cycle 5) | carried to E1 | Step 0 acceptance (update 5 MF-2), D11, Phase 10 item 2 | `DECISIONS.md` holds D11 as the accepted default. `outputs/summary.md` states the limit |
| MF-3 (cycle 5) | carried to E1 | Update 5 MF-3, Phase 7 TDD (overlap warning), Phase 10 item 2 | Phase 7 TDD: run 2 exits 0 with the warning. Phase 10 membership check |
| MF-4 (cycle 5) | carried to E1 | Update 5 MF-4, Phase 10 item 3 | `DECISIONS.md` and `outputs/summary.md` state the replay window length of run 1 |
| MF-5 (cycle 2 label, cited in the cycle 5 review) | settled earlier, not reopened | Update 2 MF-5 (two stream runs), amended by update 5 MF-3 | Phase 10 item 2 membership check. No new test |

Heading note: the update 4 table above is now titled `###` so that the plan-update gate reads this table. Its rows are unchanged. The MF-5 row maps a label that the cycle 5 review cites in its text. The review does not list MF-5 as an open must-fix.

Next step: none for this plan update. This is the last plan update. The orchestrator reads the carried findings above. No `/plan-review` run follows from this update.
