---
RUN_BY_COMMAND: plan-create
---

# Plan: gh-1 open-data pipeline (cd-1)

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Ticket: cd-1
Pipeline-Run: 0f84b2cc-3cf4-4553-b890-6f79e87e0cd2
Source: `.context/proposals/cd-1.md` (the request as written). Input vibe test: `.context/vibetest/cd-1_2026-10-21.md` (verdict NOT READY FOR PLANNING, blocking gaps G-1 to G-8).

Every blocking gap is settled here by an assumption. Each assumption has a decision record in `.context/proposals/` and a row in `.context/deferrals/cd-1_deferral-register.md`.

## Step 0: problem, decisions, blast radius, acceptance

### Problem

Two analyst questions over public data, from raw files to Parquet marts that a BI tool reads directly:

- Question A (batch): FY2024 federal contract and grant obligations, in total and per resident, by state, county, awarding agency and month. Source: USAspending prime transactions (4 agencies), Census county population (July 1, 2024 estimate).
- Question B (stream): Wikipedia edits per wiki, namespace and 5-minute window, split human and bot, with net bytes. Source: Wikimedia EventStreams recentchange, replayed at `localhost:8099`.

### Constraints

- Python 3.12. Packages pinned in `pyproject.toml`: pyarrow 26.0.0, polars 2.0.0, datafusion 55.0.0, dbt-core 1.11.6, dbt-duckdb 1.11.0, duckdb 1.5.6.
- Ingestion: the Python engine (`engine/`) reads `pipelines/*.yml`. Polars for dataframe transforms, DataFusion for SQL transforms. Sinks write Parquet under `lake/`.
- Everything after the lake: dbt project in `transform/`, dbt-duckdb reading `lake/`, marts published as Parquet to `out/marts/`.
- `make build` runs the batch from raw files. A second run changes no output.
- `make stream DURATION=<s>` consumes the stream and resumes after a disconnect, with no event counted twice and none lost.
- Windows: 5 minutes, UTC, aligned to multiples of 5 minutes, placed by event time (`meta.dt`).
- Lateness: at first arrival, the highest event time among earlier arrivals is more than 10 minutes after the window end. Stream time, not wall clock.
- Money: exact sums. Decimal, no floats.
- Every model documents its grain. Every mart has an enforced contract. Keys are tested in dbt.
- Amendment A: per person uses the July 1, 2024 estimate. A county without a 2024 estimate uses the latest earlier estimate, noted in `DECISIONS.md`.
- No GitHub, no Linear. PR and ticket text goes to `outputs/PR.md`.

### Non-goals

- No web UI, no scheduler, no orchestration service.
- No new vibe-test or spec rework. The gaps are settled by assumptions, not by a new spec.
- No changes to the raw files under `data/raw/`.
- No `make` targets beyond `build` and `stream`, which exist in the Makefile. The plan adds no new make target.

### Blast radius

- New: `engine/`, `pipelines/batch.yml`, `pipelines/stream.yml`, `transform/models/**`, `transform/macros/**` (publish hook), `transform/models/**/*.yml` (contracts and tests), `tests/**`, `oracle_map.yml`, `DECISIONS.md`.
- Changed: `Makefile` (fill the `build` and `stream` recipes), `pyproject.toml` (add `pyyaml`, `jsonschema`, `pytest` through `uv add`), `transform/dbt_project.yml` (model paths, materialization defaults).
- Generated, ignored by `.gitignore` already: `lake/`, `out/`, `transform/target/`.
- Not touched: `data/raw/`, `.cadence.json`, `.context/` (except the new plan, decision records and register).

### Assumptions for the blocking gaps

| Gap | Settled here | Decision record |
|---|---|---|
| G-1 dedup key and resume position | Dedup key is `meta.id`. Resume position is the SSE `id` of the last committed event, sent back as `Last-Event-ID`. | `cd-1-stream-dedup-resume` |
| G-2 running max event time across restarts | The running max is stored in the checkpoint with every commit. dbt reads it from the lake's landed events, so no separate state is needed. | `cd-1-stream-commit-manifest` |
| G-3 late events in the edit fact | `fact_edit` holds every consumed edit with `is_late`. The window mart counts only on-time edits. `late_events` is the subset with `is_late = true`. | `cd-1-late-event-placement` |
| G-4 FY2024 bounds and month field | FY2024 is `action_date` from 2023-10-01 to 2024-09-30 inclusive. Month is the calendar month of `action_date`. | `cd-1-fy-and-month-basis` |
| G-5 place basis and missing place | Place is the place of performance (`primary_place_of_performance_*`). Missing state or county maps to an explicit `UNKNOWN` member, so totals reconcile. | `cd-1-place-basis` |
| G-6 award key for the negative count | Award key is the prime award unique key. A negative award is one whose FY2024 net obligation sum is below zero. | `cd-1-negative-award-key` |
| G-7 load metadata in outputs | Load metadata is deterministic: source file name, source SHA-256, row number, and a batch sequence. No wall-clock time in lake or out. | `cd-1-load-metadata` |
| G-8 ownership of dedup and late split | The engine lands and dedups events and assigns `arrival_seq`. dbt computes lateness, windows and the late split. | `cd-1-stage-ownership` |
| N-1 event time field | `meta.dt`. | `cd-1-stage-ownership` |
| N-2 population layout | Use the `POPESTIMATE<year>` columns and `STATE`/`COUNTY` FIPS from the census README layout. | `cd-1-population-fallback` |
| N-4 server_name to wiki | Join `server_name` to the `url` host in sitematrix, then take `dbname` and `code`. | `cd-1-stage-ownership` |
| N-6 money scale | `DECIMAL(18,2)`. A test fails when a value has more than 2 decimal places. | `cd-1-money-scale` |
| N-8 net obligations field | `federal_action_obligation`. | `cd-1-fy-and-month-basis` |

Non-blocking N-3 (tie-break for top windows), N-5 (reconnect backoff, replay ends early), N-7 (engine tests) are settled in Phases 5 and 1, and recorded in `DECISIONS.md`.

### Acceptance

The run is accepted when all of these hold:

1. `make build` and `make stream DURATION=60` exit 0 on a clean checkout (`lake/` and `out/` removed).
2. A second `make build` leaves every file under `out/marts/` byte-identical (compare `sha256sum`).
3. A stream run with a forced disconnect, then a resume, produces the same `fact_edit` `meta.id` set as an uninterrupted run over the same replay window. No duplicate `meta.id` in the lake. No gap.
4. Checks 1 to 7 from `.context/proposals/cd-1.md` run from `oracle_map.yml` and return a value. Check 4 closes: county sums equal state sums, and state sums equal the source total, for the chosen month.
5. `dbt build` passes: contracts enforced, key tests on every model, no warning on a key test.
6. `uv run pytest` passes. Engine YAML errors name file, line and problem.

## Phases

Phase order follows the dependency chain: engine core, then batch landing, then dbt batch, then stream landing, then dbt stream, then verification and docs.

### Phase 1: Engine core and YAML validation

Build the engine skeleton. No source is wired yet.

- `engine/__main__.py`: `uv run python -m engine <yml>...`. Exits non-zero on any error.
- `engine/config.py`: load YAML with line numbers (PyYAML node positions). Validate against a JSON Schema (`engine/schema/pipeline.schema.json`) with `jsonschema`. Each error prints `file:line: problem`.
- Schema: `sources` (kind `file` or `sse`), `transforms` (`engine: polars` or `datafusion`, with `sql` or `steps`), `sinks` (kind `parquet_lake`, `path` under `lake/`). Unknown keys are errors.
- `engine/registry.py`: maps kind names to Python classes. The YAML names kinds; the engine never imports pipeline-specific code.
- Interfaces: `Source.batches() -> Iterator[pyarrow.RecordBatch]`, `Transform.run(table) -> pyarrow.Table`, `Sink.write(table, batch_seq)`. Data moves as Arrow.

TDD notes:
- Red first: `tests/test_config_errors.py` with one YAML fixture per error class (unknown key, wrong enum, missing sink path, path outside `lake/`). Each asserts the message contains the file and the line number.
- Red: a valid fixture passes validation and builds an empty plan.

Exit: `uv run pytest tests/test_config_errors.py` passes. `uv run python -m engine pipelines/*.yml` reports `file:line` for a broken fixture.

### Phase 2: Batch sources and lake landing

- `engine/sources/file.py`: reads a CSV from a zip (`zipfile`) or a plain CSV, by glob. Streams with `pyarrow.csv` in batches. Adds `_source_file`, `_source_sha256` and `_row_number` (G-7). Money columns are read as strings and cast later.
- Sources in `pipelines/batch.yml`: the 8 USAspending zips (`data/raw/usaspending/*.zip`, assistance and contracts), `data/raw/census/co-est2024-alldata.csv`, `data/raw/census/co-est2021-alldata.csv`, `data/raw/sitematrix.json` (needs a JSON-to-table transform step, see below).
- `engine/sinks/parquet_lake.py`: writes `lake/<table>/` with one folder per source table. Writes to `lake/<table>.tmp-<uuid>/` and renames to `lake/<table>/` atomically. The rebuild replaces the table, so a repeat run is idempotent.
- Partitioning: `usaspending_awards` partitioned by `agency_code` (toptier code) and `kind` (contracts or assistance). Other tables are single folders.
- Sitematrix: a Polars step flattens `sitematrix.*.site[]` to `(dbname, url, code, sitename, closed)` rows, and `url` host to `server_name`.

TDD notes:
- Red: `tests/test_file_source.py` with a 3-row zip fixture. Asserts `_row_number` is 1..3 and `_source_sha256` matches `hashlib`.
- Red: `tests/test_lake_sink.py`. Writing twice gives identical file bytes. No leftover `.tmp-` folder.
- Red: `tests/test_sitematrix.py`. A fixture with one closed and one open site flattens to 2 rows with the expected `server_name`.

Exit: `uv run python -m engine pipelines/batch.yml --only landing` lands all source tables under `lake/`. Row count for `usaspending_awards` equals the sum of data lines in the 8 zips (command in `DECISIONS.md`).

### Phase 3: Batch clean tables (Polars and DataFusion transforms)

Transforms that land clean source tables. These are the engine's last batch step; everything after is dbt.

- Polars step `to_decimal`: casts `federal_action_obligation` and `total_dollars_obligated` to `DECIMAL(18,2)`. Fails the run when a value has more than 2 decimal places (N-6).
- DataFusion SQL step `fy2024_awards`: filters `action_date` to FY2024 bounds (G-4) and keeps the columns the star schema needs. Writes `lake/usaspending_fy2024/`.
- Population: DataFusion step `population_2024`: one row per `(state_fips, county_fips)` with `population_2024` from `POPESTIMATE2024`. For counties missing from the 2024 file, the fallback takes the latest earlier estimate from the 2021 file (`POPESTIMATE2021`), with a `population_as_of` column (N-2, Amendment A).

TDD notes:
- Red: `tests/test_money.py`. `"12345.675"` fails. `"-0.10"` passes and stays exact after sum.
- Red: `tests/test_fy_filter.py`. Rows on 2023-09-30, 2023-10-01, 2024-09-30, 2024-10-01 keep the two inside.
- Red: `tests/test_population_fallback.py`. A county present only in the 2021 file gets `population_as_of = 2021`.

Exit: `uv run pytest tests/test_money.py tests/test_fy_filter.py tests/test_population_fallback.py` passes. The fallback county count is written to `DECISIONS.md`.

### Phase 4: dbt batch models and publish

- Project: `transform/dbt_project.yml` sets models to `staging`, `marts`. Profile `transform/profiles.yml` already uses `out/warehouse.duckdb`. Run from the repo root: `uv run dbt build --project-dir transform --profiles-dir transform`.
- Sources: `source('lake', ...)` reads `read_parquet('lake/<table>/**/*.parquet', hive_partitioning=true)`.
- Staging: `stg_usaspending_awards` (grain: one prime award transaction), `stg_census_population` (grain: county per year), `stg_sitematrix` (grain: one site).
- Star schema: `fct_award_transaction` (grain: one award transaction; `award_key`, `agency_key`, `place_key`, `date_key`, `federal_action_obligation`); `dim_agency`, `dim_place` (state and county, with `UNKNOWN` members, G-5), `dim_date` (calendar month, fiscal year).
- Mart: `mart_obligations_monthly` (grain: month, state, county, agency): `net_obligations`, `population_2024`, `obligations_per_person` (decimal, rounded to 2 places at output only).
- Mart: `mart_county_ranking_fy2024` for check 2 (grain: county, FY2024).
- Views for the checks: `check_agency_totals`, `check_county_state_source`, `check_negative_awards` (G-6).
- Contracts: `contract: {enforced: true}` on every mart. Column types declared.
- Tests: `unique` and `not_null` on each model key. `relationships` from facts to dims. A singular test for check 4: county sum = state sum = source sum.
- Publish: a dbt `on-run-end` macro writes each mart to `out/marts/<mart>/part-0.parquet` with `COPY ... TO ... (FORMAT parquet)`. The decision record `cd-1-publish-format` covers the format choice.

TDD notes:
- Red: dbt singular test `check_county_state_source` fails on a fixture where one county is dropped. Passes on the full fixture.
- Red: a contract test: a mart with a wrong column type fails `dbt build`.

Exit: `make build` runs the engine batch then `dbt build`, and writes `out/marts/`. Running it twice gives identical bytes (`sha256sum out/marts/**`).

### Phase 5: Stream source and micro-batch sink

- `engine/sources/sse.py`: HTTP GET with `Accept: text/event-stream`, parses `id:`, `event:`, `data:` lines. Sends `Last-Event-ID` on reconnect. Reconnect with capped backoff (1, 2, 4, 8, 16 s, cap 16 s; N-5). Stops at `DURATION` seconds of wall time, or when the replay ends, whichever comes first, then commits what it has.
- `engine/sinks/stream_lake.py`: buffers events and writes a micro-batch when 500 events or 5 seconds have passed. Each batch:
  1. Drops any event whose `meta.id` is in the checkpoint's landed-id index for the current batch file set (G-1).
  2. Assigns `arrival_seq` (global, monotonic, from the checkpoint).
  3. Writes the batch to `lake/stream_recentchange/batch-<seq>.parquet` through a temp name, then renames.
  4. Commits the manifest `lake/_state/stream_manifest.json` through a temp file and rename. The manifest holds: last committed SSE `id`, `last_arrival_seq`, the list of committed batch files, and `max_event_time` (G-2).
- Crash safety: a batch file not in the manifest is an orphan. On start, the sink deletes orphans. The position is committed only together with the list of batch files (G-1, G-2, `cd-1-stream-commit-manifest`).
- Event columns: `meta_id`, `meta_dt` (event time, `TIMESTAMP`), `meta_domain`, `server_name`, `wiki`, `namespace`, `bot`, `title`, `type`, `length_old`, `length_new` (NULL when absent), `arrival_seq`, `batch_seq`.

TDD notes:
- Red: `tests/test_stream_resume.py` with a local SSE fixture server that drops after event 500 and expects `Last-Event-ID` = id of event 500. Asserts no duplicates and no gaps after reconnect.
- Red: `tests/test_stream_commit.py`. Kill the sink between the batch rename and the manifest commit (injected fault). On restart, the orphan file is removed and the events are re-read once.
- Red: a dedup test: the same `meta.id` sent twice in one connection lands once.

Exit: `uv run pytest tests/test_stream_*.py` passes. `uv run python -m engine pipelines/stream.yml --duration 20` against the replay lands batches and writes the manifest.

### Phase 6: dbt stream models and window mart

- `stg_recentchange`: grain one change event (`meta_id`). Reads `lake/stream_recentchange/*.parquet` through an incremental filter on `arrival_seq > max(arrival_seq)` in the target.
- `dim_wiki`: from `stg_sitematrix`, joined on `server_name` to `url` host (N-4). Grain one wiki (`dbname`).
- `fact_edit` (incremental, `unique_key = meta_id`): grain one change event. Columns: `meta_id`, `meta_dt`, `wiki_key`, `namespace`, `actor_type` (`bot` if `bot = true`, else `human`), `arrival_seq`, `window_start` (`time_bucket` of 5 minutes on `meta_dt` in UTC), `window_end`, `is_late`, `net_bytes` (`length_new - length_old`, NULL length gives 0 and a flag).
  - Lateness (G-3, G-8): `is_late = (prior_max_event_time - window_end) > INTERVAL 10 MINUTE`. `prior_max_event_time` is the max of `meta_dt` over earlier `arrival_seq` values, in the batch and in the target (the target max is taken from `fact_edit` before the merge).
- `late_events`: view of `fact_edit` where `is_late`. Grain one late change event.
- `mart_edit_window_5min` (incremental, `unique_key = (window_start, wiki, namespace, actor_type)`): counts on-time edits only, plus `net_bytes`. Windows touched by the new batch are recomputed.
- Check views: `check_edits_replay_hour` (check 5, counts all of `fact_edit` per wiki and actor type); `check_top_windows_en` (check 6, on-time edits, `en.wikipedia.org`, ties broken by earliest `window_start` (N-3)); `check_late_count` (check 7).
- Publish: the same `on-run-end` macro writes `mart_edit_window_5min` to `out/marts/mart_edit_window_5min/` (decision `cd-1-publish-format`).

TDD notes:
- Red: `transform/tests/` singular test with a fixture: one event 9 min after its window end is on time. One event 11 min after is late and is absent from the window mart and present in `late_events`.
- Red: `unique` test on `fact_edit.meta_id`. Fails when the same event lands twice.
- Red: incremental run: run once on batch 1, then batch 2 with a late event. The window mart equals a full-refresh run on batches 1 and 2.

Exit: `make stream DURATION=60` followed by `dbt build --select stream` passes and updates `out/marts/mart_edit_window_5min/`.

### Phase 7: Makefile wiring, oracle map, DECISIONS and end-to-end checks

- `Makefile`: `build` runs `uv run python -m engine pipelines/batch.yml` then `uv run dbt build --project-dir transform --profiles-dir transform`. `stream` runs `uv run python -m engine pipelines/stream.yml --duration $(DURATION)` then the dbt stream selection. No other targets.
- `oracle_map.yml`: for each of checks 1 to 7, the table and column (or view) that answers it, plus the SQL text used by the analysts.
- `DECISIONS.md`: each decision record, the Amendment A fallback counts, the N-3 to N-5 choices, the replay commands, and the dependency decision.

TDD notes:
- Red: `tests/test_e2e_build.py` runs `make build` twice on a fixture subset and compares hashes. Marked slow; the full FY2024 run is the acceptance run, not a unit test.
- Red: `tests/test_stream_e2e.py` runs `make stream DURATION=20` with a forced drop, then compares the `meta.id` set to an uninterrupted run.

Exit: the Acceptance list at the top of this plan passes, with the outputs of each check recorded in `DECISIONS.md` or `outputs/summary.md`.

## Reuse and extension

Existing helpers and modules reused:

- `pyarrow.csv` and `zipfile` (stdlib) for the file source. No custom CSV parser.
- `pyarrow.parquet` for the lake sink. The sink rename pattern is the one place that writes atomically.
- `polars` for the sitematrix flatten and the decimal cast.
- `datafusion.SessionContext` for SQL steps.
- `dbt-duckdb` `read_parquet` for the lake reads. No copy of the lake into DuckDB tables before the dbt models.
- `dbt_utils` is not added. Key tests use dbt built-in tests only.

Extension points added:

- The engine registry (`engine/registry.py`): a new source, transform or sink kind is one class and one registry line. Pipelines are YAML only, as the request requires.
- The `on-run-end` publish macro in `transform/macros/publish.sql`: a new mart is published by adding it to a list in `dbt_project.yml`.

## Quality gates (real commands in this repo)

- `uv sync` installs the pinned set. `uv add pyyaml jsonschema` and `uv add --dev pytest` add the engine's dependencies (recorded in `cd-1-engine-dependencies`).
- `uv run pytest` runs the unit and integration tests in `tests/`.
- `uv run python -m engine pipelines/batch.yml pipelines/stream.yml` validates the YAML without running.
- `make build`, `make stream DURATION=<s>` (the Makefile targets, filled in Phase 7).
- `uv run dbt build --project-dir transform --profiles-dir transform`.
- `sha256sum` on `out/marts/**` for the idempotence check.

No linter is pinned in `pyproject.toml`. This plan adds none.

## Risks

- R-1: The replay server's Last-Event-ID support is unknown. Phase 5's test uses a local fixture server. The live replay check is the first step of Phase 5's exit, and any mismatch goes to `DECISIONS.md`.
- R-2: USAspending zips are large. Phase 2 streams in batches and does not hold a full CSV in memory.
- R-3: The fallback counties (Phase 3) may be few or none. The count is recorded whether it is zero or not.
- R-4: The incremental window mart is the most complex model. Phase 6's full-refresh equality test is the guard.

## Footer

Next step: `/plan-review .context/plans/cd-1-pipeline.plan.md`. The review file must exist before any `/plan-update` runs.

## Plan update 2026-10-21

RUN_BY_COMMAND: plan-update

Applies review `.context/reviews/plan_cd-1-pipeline.md` (sha256 d582bdd42ba1..., verdict READY WITH CHANGES, cycle 1 of 5). The text above stays as written. Where this section gives a different rule, this section wins. "Replaces" lines name the earlier text they override.

### MF-1: one source for the running max event time

Choice: dbt is the only source. The manifest does not store `max_event_time`. The running max is `max(meta_dt)` over the events already in `fact_edit` (the target, read before the merge) and over the earlier rows of the batch. Why: `fact_edit` and the lake hold every committed event, and orphan batch files are deleted on start, so the derived max matches the committed state. A stored copy can drift from it.

Replaces:
- Phase 5, the manifest field list (line 159): the manifest holds the last committed SSE `id`, `last_arrival_seq` and the list of committed batch files. It does not hold `max_event_time`.
- Phase 6, `is_late` (line 175): for each row, `prior_max_event_time` is the greater of (a) the target max of `meta_dt` from `fact_edit` before the merge and (b) the max of `meta_dt` over the batch rows with a smaller `arrival_seq`. The batch is ordered by `arrival_seq` before this maximum is computed (N-d). `is_late = (prior_max_event_time - window_end) > INTERVAL 10 MINUTE`.
- G-2 row of the plan table (line 57) stays. It is now exact: no separate state exists.

Tests:
- Phase 5 `tests/test_stream_commit.py`: after the restart case, the manifest JSON has no `max_event_time` key, and the committed batch list equals the files in the lake.
- Phase 6 `transform/tests/test_late_after_restart.sql` (red first): batch 1 holds an event with `meta_dt` at T+12 min. A new process then lands batch 2, and `fact_edit` in the target has max `meta_dt` T+12 min. An event with `window_end` = T is late (12 min > 10 min). An event with `window_end` = T+5 min is on time (7 min).

### MF-2: dedup scope covers every committed batch file

Choice: the landed-id index covers every committed batch file, not only the current run. On start, after orphan deletion, the sink reads `meta_id` of every batch file listed in the manifest into the landed-id index. An incoming event is dropped when its `meta_id` is in that index.

Replaces: Phase 5 step 1 (line 156): "drops any event whose `meta.id` is in the landed-id index of all committed batch files in the manifest."

Test (red first): `tests/test_stream_dedup_restart.py`. Run 1 lands an event X in a committed batch and stops. Run 2, a new process, receives X again from the fixture server. Assert X appears once in the lake and run 2 writes no new batch for it.

### MF-3: event-bounded comparison

Choice: the stream source takes a `max_events` key, which is a new key in the Phase 1 schema. The source stops after it has yielded `max_events` distinct `meta_id` values in the run. A re-delivered id does not count. The `DURATION` wall-time cap still applies. The run records its stop reason (`max_events` or `duration` or `replay_end`) in the log.

Replaces: Phase 5 stop rule (line 154): "Stops after `max_events` distinct events, or at `DURATION` seconds of wall time, or at replay end, whichever comes first, then commits what it has."

Acceptance 3 (line 78) is replaced by: a stream run with a forced disconnect and a resume, and an uninterrupted run, both with the same `max_events` and the same replay, produce the same `fact_edit` `meta_id` set. Both runs end with stop reason `max_events`. No duplicate `meta_id` in the lake. No gap.

Test (Phase 7, `tests/test_stream_e2e.py`): the two runs use `max_events: 2000` and a `DURATION` cap of 600 s. The test fails when either run's stop reason is not `max_events`.

### MF-4: derived data leaves the lake

Choice: the engine lands raw source tables only, and adds load metadata (G-7). The engine keeps one typed step, `to_decimal`. It changes the type only, keeps every row and value, and fails on a value with more than 2 decimal places (N-6). The FY2024 row filter and the population fallback move to dbt.

Replaces:
- Phase 2 landing tables: `lake/usaspending_awards/` (all rows and all years, partitioning as before), `lake/census_county_2024/` (from `co-est2024-alldata.csv`), `lake/census_county_2021/` (from `co-est2021-alldata.csv`), `lake/sitematrix/` (the flattened sites, N-a).
- Phase 3: the DataFusion steps `fy2024_awards` and `population_2024` are removed. Phase 3 keeps `to_decimal` only. Its TDD notes keep `test_money.py` and drop `test_fy_filter.py` and `test_population_fallback.py`. Its exit is `uv run pytest tests/test_money.py`.
- Phase 4 adds these dbt models:
  - `stg_census_population` (grain: county per year): reads `lake/census_county_2024/` and `lake/census_county_2021/` and takes `POPESTIMATE<year>` with the `STATE` and `COUNTY` FIPS codes (N-2). It replaces the line 137 text.
  - `int_county_population_2024` (grain: county): `population_2024` and `population_as_of`. It takes the 2024 row when one exists, and the 2021 row otherwise, with `population_as_of` = 2024 or 2021. `mart_obligations_monthly` joins to this model.
  - `stg_usaspending_awards` filters `action_date` to 2023-10-01 through 2024-09-30 inclusive (G-4).
- Phase 4 dbt tests (N-b): all dbt singular tests live in `transform/tests/`. Python tests live in `tests/`. The Phase 6 singular test is in `transform/tests/`.
  - `transform/tests/test_fy2024_bounds.sql`: rows dated 2023-09-30 and 2024-10-01 are absent from `stg_usaspending_awards`. Rows dated 2023-10-01 and 2024-09-30 are present.
  - `transform/tests/test_population_fallback.sql`: a county present only in the 2021 file has `population_as_of` = 2021. The count of fallback counties is written to `DECISIONS.md` from a query on `int_county_population_2024`.
- Phase 4 publish (N-c): the `on-run-end` macro writes each mart to `out/.marts-staging/<mart>/part-0.parquet`. After every COPY succeeds, it renames `out/marts` to `out/marts.prev`, then renames `out/.marts-staging` to `out/marts`, then removes `out/marts.prev`. A failure before the first rename leaves the old `out/marts/` in place. If the second rename fails, the macro renames `out/marts.prev` back to `out/marts`. A failed run that leaves `out/marts.prev` in place is restored by renaming that folder to `out/marts`.

Test that the rule holds: `grep -rn "usaspending_fy2024\|population_2024" engine/` finds no write step. Phase 3 exit covers this.

### Notes applied (not blocking)

- N-a: lake table names are set in MF-4 above.
- N-b: dbt tests in `transform/tests/`, Python tests in `tests/` (MF-4 above).
- N-c: publish rollback (MF-4 above).
- N-d: batch order by `arrival_seq` before the in-batch max (MF-1 above).

### Decision records and register

- `.context/proposals/cd-1-stream-dedup-resume.md`: the choice adds the dedup scope of MF-2.
- `.context/proposals/cd-1-stream-commit-manifest.md`: the choice drops `max_event_time` (MF-1).
- `.context/proposals/cd-1-stage-ownership.md`: the choice adds that the engine casts types only and dbt holds the row filter and the fallback (MF-4).
- `.context/proposals/cd-1-population-fallback.md`: the choice adds that the fallback runs in dbt (MF-4).
- `.context/deferrals/cd-1_deferral-register.md`: the assumption rows for G-1, G-2 and G-4 name the new tests. No deferral is proposed, so `## Approved deferrals` is unchanged.

## Revision ledger (review d582bdd42ba1)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-1 | dbt is the one source of the running max. The manifest drops `max_event_time`. Lateness after restart is tested. | Plan update 2026-10-21, MF-1; Phase 5 manifest; Phase 6 `is_late` | `transform/tests/test_late_after_restart.sql`; `tests/test_stream_commit.py` asserts no `max_event_time` key in the manifest |
| MF-2 | The landed-id index covers every committed batch file. A restart duplicate test is added. | Plan update 2026-10-21, MF-2; Phase 5 step 1 | `tests/test_stream_dedup_restart.py` |
| MF-3 | The stream source takes `max_events`. Acceptance 3 and the Phase 7 test compare runs bounded by it. | Plan update 2026-10-21, MF-3; Phase 1 schema; Phase 5 stop rule; Acceptance 3; Phase 7 | `tests/test_stream_e2e.py` asserts both stop reasons are `max_events` and the two id sets are equal |
| MF-4 | The FY2024 filter and the population fallback move to dbt. The engine lands raw tables and casts types only. | Plan update 2026-10-21, MF-4; Phase 2; Phase 3; Phase 4 | `transform/tests/test_fy2024_bounds.sql`; `transform/tests/test_population_fallback.sql`; `grep -rn "usaspending_fy2024\|population_2024" engine/` finds no write step |

## Plan update 2026-10-21 (cycle 2)

RUN_BY_COMMAND: plan-update

Applies review `.context/reviews/plan_cd-1-pipeline.md` (sha256 5482c703558efc7de71393b715812cbbd95241ef3f4d95f6426675fa00b97732, verdict READY WITH CHANGES, cycle 2 of 5). Open items: MF-4 (carried, verification missing), MF-5, MF-6. The text above and the earlier update stay as written. Where this section gives a different rule, this section wins. "Replaces" lines name the earlier text they override, quoted exactly.

### MF-4: the verification is a test (carried)

Choice: the test that the lake holds no derived table is `tests/test_lake_tables.py`. It runs the landing on a fixture pipeline (`tests/fixtures/landing.yml`, the same four sinks over the small fixture files) and asserts that the folder names under `lake/` equal `usaspending_awards`, `census_county_2024`, `census_county_2021` and `sitematrix`. It also parses `pipelines/batch.yml` and asserts that its sink names are the same four. A fixture run that writes a derived folder such as `usaspending_fy2024` fails the test.

Phase 2 exit gains `uv run pytest tests/test_lake_tables.py`.

Replaces: the MF-4 test sentence (line 291): "Test that the rule holds: `grep -rn "usaspending_fy2024\|population_2024" engine/` finds no write step. Phase 3 exit covers this." The grep is not the check. The test above is.

### MF-5: the sitematrix step is a reshape

Choice: option (b). The engine keeps the sitematrix flatten as a reshape step named `sitematrix_flatten`. It turns `sitematrix.*.site[]` into `(dbname, url, code, sitename, closed)` rows and adds no derived column. The `server_name` derivation (the host of `url`) moves to dbt, in `stg_sitematrix`. Why: the request allows transforms that land clean source tables (`.context/proposals/cd-1.md` line 58). The numbered keys of `sitematrix.json` have no fixed Arrow schema, so the raw file cannot be landed as it is.

Replaces: the MF-4 choice sentence (line 277): "The engine lands raw source tables only, and adds load metadata (G-7)." The engine now lands four source tables. Each row keeps its source values and gets the load metadata of G-7. The engine has two steps that change shape or type: `sitematrix_flatten` (above) and `to_decimal` (N-6). Neither derives a value. `to_decimal` runs in the landing pipeline before its sink, so each lake folder is written once.

Phase 2 changes:
- Replaces line 109: "- Sitematrix: a Polars step flattens `sitematrix.*.site[]` to `(dbname, url, code, sitename, closed)` rows, and `url` host to `server_name`." The new text: the Polars step `sitematrix_flatten` flattens `sitematrix.*.site[]` to `(dbname, url, code, sitename, closed)` rows. It adds no column.
- Replaces the Phase 2 TDD note at line 114: "- Red: `tests/test_sitematrix.py`. A fixture with one closed and one open site flattens to 2 rows with the expected `server_name`." The new text: a fixture with one closed and one open site flattens to 2 rows, and the columns are exactly `(dbname, url, code, sitename, closed)`.

Phase 4 adds: `stg_sitematrix` (grain: one site) derives `server_name` as the host of `url`. Test `transform/tests/test_sitematrix_server_name.sql`: each row's `server_name` equals the host of its `url`, and none is null.

### MF-6: the publish states

Choice: the file renames move out of the dbt macro into the engine, as two steps: `python -m engine publish prepare`, run before `dbt build`, and `python -m engine publish swap`, run after it. The dbt macro only writes the staging folder. Why: the plan's dbt stack has no file rename, and the states need a test that calls the renames directly. The engine's CLI dispatches on `publish` as its first argument. The `<yml>...` form stays.

Replaces: the MF-4 publish rule (line 289), from "After every COPY succeeds," to the end of the line: "After every COPY succeeds, it renames `out/marts` to `out/marts.prev`, then renames `out/.marts-staging` to `out/marts`, then removes `out/marts.prev`. A failure before the first rename leaves the old `out/marts/` in place. If the second rename fails, the macro renames `out/marts.prev` back to `out/marts`. A failed run that leaves `out/marts.prev` in place is restored by renaming that folder to `out/marts`."

The rule is now:
- The `on-run-end` macro runs COPY for every mart in the publish list of `transform/dbt_project.yml`, to `out/.marts-staging/<mart>/part-0.parquet`. It does not rename. It copies every listed mart, not only the selected ones, from `out/warehouse.duckdb`. So a `make stream` run leaves the batch marts unchanged.
- `publish prepare` runs before dbt build, on the state of `out/` it finds:
  - P1: `out/marts` and `out/marts.prev` both exist. The last swap stopped after its second rename. Delete `out/marts.prev`. `out/marts` is the newest complete output.
  - P2: `out/marts.prev` exists and `out/marts` does not. The last swap stopped after its first rename. Rename `out/marts.prev` to `out/marts`. The old output is restored.
  - P3: `out/.marts-staging` exists, in any state. It is a failed COPY or an interrupted swap. Delete it. A staging folder is renamed only when it is complete, so a leftover is never published.
  - None of these: nothing to do (first build).
- `publish swap` runs only when dbt build exits 0:
  - S1: `out/marts` exists. Rename it to `out/marts.prev`. When it does not exist (first build), skip this step.
  - S2: rename `out/.marts-staging` to `out/marts`. If this rename fails, rename `out/marts.prev` to `out/marts` when it exists, and exit non-zero.
  - S3: delete `out/marts.prev` if it exists.
  Any failure exits non-zero, so `make` stops.

Makefile (replaces the Phase 7 bullet, line 190: "- `Makefile`: `build` runs `uv run python -m engine pipelines/batch.yml` then `uv run dbt build --project-dir transform --profiles-dir transform`. `stream` runs `uv run python -m engine pipelines/stream.yml --duration $(DURATION)` then the dbt stream selection. No other targets."). The recipes are now:
- `build`: `uv run python -m engine pipelines/batch.yml`, `uv run python -m engine publish prepare`, `uv run dbt build --project-dir transform --profiles-dir transform`, `uv run python -m engine publish swap`.
- `stream`: `uv run python -m engine pipelines/stream.yml --duration $(DURATION)`, `uv run python -m engine publish prepare`, `uv run dbt build --project-dir transform --profiles-dir transform --select stream`, `uv run python -m engine publish swap`.
No new target. The recipes are the only change.

Tests: `tests/test_publish_states.py` calls `engine.publish.prepare(out_dir)` and `engine.publish.swap(out_dir)` on a temporary `out/` tree.
- P1: prepare deletes `out/marts.prev` and leaves `out/marts` unchanged.
- P2: prepare restores `out/marts` from `out/marts.prev`, and the folder bytes equal the old output.
- P3: a staging folder with a stray file from a failed COPY is deleted by prepare. After a complete COPY, swap publishes exactly the new files and not the stray file.
- S1: a first build (no `out/marts`) swaps with no error.
- S2: a fault injected into the second rename leaves `out/marts` equal to the old output, and swap exits non-zero.
- Phase 6 exit gains: the batch mart folders are byte-identical (`sha256sum`) before and after `make stream DURATION=60`.

### Phase 1 and Phase 3 edits

- The Phase 1 schema list (line 93) gains the `max_events` key of the `sse` source (MF-3). The key is an integer of at least 1.
- DataFusion has no step in this plan after MF-4. The pin stays in `pyproject.toml`. The Reuse line for `datafusion.SessionContext` (line 207) applies only if a SQL step is added later.

### Plan table and decision records

- Replaces the G-2 row sentence (line 57): "The running max is stored in the checkpoint with every commit. dbt reads it from the lake's landed events, so no separate state is needed." The new sentence: "The running max event time is not stored. dbt derives it from fact_edit and the earlier rows of the batch." The decision record `cd-1-stream-commit-manifest` and the register row G-2 use the same words.
- `.context/proposals/cd-1-stage-ownership.md`: the choice names the `sitematrix_flatten` step (MF-5) and the dbt `server_name` derivation.
- `.context/proposals/cd-1-stream-commit-manifest.md`: the choice uses the G-2 words above.
- `.context/proposals/cd-1-publish-format.md`: the choice names the staging path and the engine's publish steps (MF-6).
- `.context/deferrals/cd-1_deferral-register.md`: the G-2 row already has the words above. No deferral is proposed, so `## Approved deferrals` is unchanged.

### Errata and notes (not blocking)

- N-1: applied above.
- N-2: the MF-2 and MF-3 quotes did not match the original. The original line 156 reads "  1. Drops any event whose `meta.id` is in the checkpoint's landed-id index for the current batch file set (G-1)." The original stop rule (line 154) reads "Stops at `DURATION` seconds of wall time, or when the replay ends, whichever comes first, then commits what it has." The replacements in MF-2 and MF-3 apply as written.
- N-3: the ledger heading below uses the sha256 of the review file, first 12 characters.
- N-4: applied above (Phase 1 `max_events`).
- N-5: the key-absence assertion in `tests/test_stream_commit.py` stays. The behavioral check is `transform/tests/test_late_after_restart.sql`.

## Revision ledger (review 5482c703558e)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-4 | The lake holds only the four source tables. The check is a test, not a grep. | Plan update 2026-10-21 (cycle 2), MF-4; Phase 2 exit | `tests/test_lake_tables.py` (folder names under `lake/` equal the four landed source tables) |
| MF-5 | Option (b): `sitematrix_flatten` is a reshape with no derived column. `server_name` moves to dbt `stg_sitematrix`. | Plan update 2026-10-21 (cycle 2), MF-5; Phase 2 (line 109 and line 114); Phase 4 `stg_sitematrix`; decision `cd-1-stage-ownership` | `tests/test_sitematrix.py` (exact column list, no `server_name`); `transform/tests/test_sitematrix_server_name.sql` |
| MF-6 | Publish is `engine publish prepare` (states P1 to P3) and `engine publish swap` (steps S1 to S3). Every state has an action. | Plan update 2026-10-21 (cycle 2), MF-6; Phase 4 publish; Phase 6 exit; Phase 7 Makefile | `tests/test_publish_states.py` (P1, P2, P3, S1 and the S2 fault); Phase 6 exit batch-mart `sha256sum` check |


## Plan update 2026-10-21 (cycle 3)

RUN_BY_COMMAND: plan-update

Applies review `.context/reviews/plan_cd-1-pipeline.md` (sha256 df2686da3441..., verdict READY WITH CHANGES, cycle 3 of 5). Open items: MF-7, MF-8, MF-9. The text above and the earlier updates stay as written. Where this section gives a different rule, this section wins. "Replaces" lines name the earlier text they override.

### MF-7: `to_decimal` lands with the batch

Choice: the Polars step `to_decimal` runs in the Phase 2 landing pipeline, before the `usaspending_awards` sink. The lake folder is written once, with the money columns already `DECIMAL(18,2)`. No later step rewrites a lake folder. Phase 3 has no engine step left, so Phase 3 is retired. Its test moves to Phase 2.

Replaces:
- Phase 3, the Polars step line (line 122) and the Phase 3 TDD note on `tests/test_money.py` (line 127), and the Phase 3 exit (line 131): these now belong to Phase 2 (see below). Phase 3 keeps its heading so earlier references resolve. Its exit is retired.
- MF-4 text (line 281): "Phase 3 keeps `to_decimal` only. Its TDD notes keep `test_money.py` and drop ... Its exit is `uv run pytest tests/test_money.py`." The step and test are in Phase 2.
- Phase 2 exit (line 116, and line 327): `uv run python -m engine pipelines/batch.yml --only landing` lands all source tables. The exit is also `uv run pytest tests/test_lake_tables.py tests/test_money.py`.

Phase 2 gains:
- Step `to_decimal` on `federal_action_obligation` and `total_dollars_obligated` of `usaspending_awards`, before the sink. It casts to `DECIMAL(18,2)` and fails on a value with more than 2 decimal places (N-6). It keeps every row.
- TDD note (red first): `tests/test_money.py`. `"12345.675"` fails. `"-0.10"` passes and stays exact after sum. A landed fixture folder has `decimal128(18,2)` in both money columns and the same row count as its input.

### MF-8: the join keys are typed

Choice: every FIPS code is read and kept as text, with its leading zeros. The census county key is `STATE || COUNTY` (5 characters). Census rows with `SUMLEV = '040'` are state summary rows and are excluded from every county grain.

Replaces:
- Phase 2 file source (line 105): "Money columns are read as strings and cast later." The new text: the file source takes a `string_columns` list in the YAML. The listed columns are read as text with `pyarrow.csv` `ConvertOptions(column_types=...)`. `string_columns` is a new key of the Phase 1 schema (of kind `file`). The source reads as text: `STATE` and `COUNTY` of both census files, and the USAspending place columns `prime_award_transaction_place_of_performance_state_fips_code` and `prime_award_transaction_place_of_performance_county_fips_code`. The money columns are read as text too, then cast by `to_decimal` (MF-7).
- Phase 2 `pipelines/batch.yml` sources: each USAspending source sets `string_columns` to the four FIPS columns above and the two money columns.
- Plan line 60, the place basis of G-5: the place is the place of performance, and its FIPS columns are the two named above (the `primary_place_of_performance_*` names are replaced by them).
- Phase 4 `stg_census_population` (line 283): the grain is county per year. It filters `SUMLEV = '050'`. Its key is `state_fips` (from `STATE`) and `county_fips5` (`STATE || COUNTY`).
- Phase 4 `dim_place` (line 138): the county key is `county_fips5`, from the two place FIPS columns above. The join from a place to a population row is on `county_fips5`.

Tests:
- `tests/test_census_keys.py` (red first, fixture with `01` and `001`): the landed `STATE` and `COUNTY` values are text, `01` stays `01`, `001` stays `001`, and the USAspending FIPS columns are text too.
- `transform/tests/test_census_county_grain.sql`: no row of `stg_census_population` has `SUMLEV` other than `050`. `(year, state_fips, county_fips5)` is unique. Every `county_fips5` is 5 digits.
- `transform/tests/test_place_population_join.sql`: a place with a county FIPS code and no population row fails the test. The places that match no population row are listed for review.

### MF-9: Connecticut is counted once

Choice: the 2024 file has nine planning regions for Connecticut (state `09`, county codes `110` to `190`) in place of its eight counties. The data has no crosswalk between them. The county grain therefore uses the eight 2021 Connecticut counties, with `population_as_of = 2021`. The nine planning-region rows are not a county grain and are excluded.

Replaces:
- Phase 4 `int_county_population_2024` (line 284). The new rule, for each county key of the county grain:
  - The county grain is the county keys of the 2021 file, plus any 2024 county key (`SUMLEV = '050'`) that is not in the 2021 file, except the Connecticut planning regions (state `09`, county `110` to `190`), which are dropped.
  - `population_2024` and `population_as_of` take the 2024 row when one exists for the key, and the 2021 row otherwise, with `population_as_of` = 2024 or 2021.
  - Each of the eight Connecticut counties has no 2024 row, so it takes the 2021 row.
- R-3 (line 231): the fallback count is 8 for this data (the eight Connecticut counties), not "few or none". The count from the query on `int_county_population_2024` is written to `DECISIONS.md` and must equal the number of fallback rows.
- Decision record `.context/proposals/cd-1-population-fallback.md`: the choice adds the Connecticut rule above (MF-9).

Tests (Phase 4, in `transform/tests/`):
- `transform/tests/test_population_no_double_count.sql` (red first, on the real build): `(state_fips, county_fips5)` is unique in `int_county_population_2024`. No row has state `09` and county `110` to `190`. The state `09` total equals the sum of the eight 2021 Connecticut county rows.
- `transform/tests/test_population_fallback.sql` (replaces the test of line 288): a county present only in the 2021 file has `population_as_of` = 2021, and the eight Connecticut counties are among them.

Known risk, not settled here: if the FY2024 USAspending place rows for Connecticut carry the planning-region codes, the `test_place_population_join.sql` test fails for those places. The next review decides whether a crosswalk is needed. This update does not map them silently.

### Notes applied (not blocking)

- N-1: the sink does not rename a folder onto an existing folder. Phase 2 writes `lake/<table>.tmp-<uuid>/`, renames the old `lake/<table>/` to `lake/<table>.old-<uuid>/` when it exists, renames the new folder to `lake/<table>/`, then deletes the old folder. `tests/test_lake_sink.py` writes twice: the second write succeeds, the bytes are identical, and no `.tmp-` or `.old-` folder remains.
- N-2: each mart's `COPY` in the `on-run-end` macro uses `ORDER BY` on the mart's grain columns, so the parquet bytes do not depend on thread scheduling.
- N-5: `tests/test_publish_states.py` gains S3: a failure after the first swap rename, with `out/marts.prev` left in place, is restored or removed by the next `publish prepare` (P1 or P2).
- N-3 and N-4 are not changed by this update.

### Decision records and register

- `.context/proposals/cd-1-population-fallback.md`: the choice adds the Connecticut rule (MF-9).
- `.context/deferrals/cd-1_deferral-register.md`: no approved deferral is proposed, so `## Approved deferrals` is unchanged. The assumption rows for G-1 to G-8 are unchanged.

## Revision ledger (review df2686da3441)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-7 | `to_decimal` moves into the Phase 2 landing before its sink. Phase 3 is retired. Its test moves to Phase 2. | Plan update 2026-10-21 (cycle 3), MF-7; Phase 2; Phase 2 exit | `tests/test_money.py` (landed folder is `decimal128(18,2)`, row count unchanged); Phase 2 exit runs it |
| MF-8 | FIPS and money codes are read as text. Census county key is `STATE || COUNTY`. `SUMLEV = '050'` filter. USAspending place FIPS columns named. | Plan update 2026-10-21 (cycle 3), MF-8; Phase 2 file source; Phase 4 `stg_census_population`, `dim_place` | `tests/test_census_keys.py` (leading zeros kept); `transform/tests/test_census_county_grain.sql`; `transform/tests/test_place_population_join.sql` |
| MF-9 | Connecticut planning regions are dropped and the eight 2021 Connecticut counties are used. Fallback count is 8. R-3 corrected. | Plan update 2026-10-21 (cycle 3), MF-9; Phase 4 `int_county_population_2024`; R-3 | `transform/tests/test_population_no_double_count.sql` (one row per key, no planning-region row, state `09` total equals the 2021 county sum); `transform/tests/test_population_fallback.sql` (eight Connecticut counties have `population_as_of` = 2021) |

## Plan update 2026-10-21 (cycle 4)

RUN_BY_COMMAND: plan-update

Applies review `.context/reviews/plan_cd-1-pipeline.md` (sha256 e21870f18089..., verdict READY WITH CHANGES, cycle 4 of 5). Open items: MF-10. The text above and the earlier updates stay as written. Where this section gives a different rule, this section wins. "Replaces" lines name the earlier text they override.

### MF-10: Connecticut planning-region places

Choice: no crosswalk. A place whose county code is one of the nine 2024 Connecticut planning regions (state `09`, county `09110` to `09190`) keeps its state `09` and takes the county member `UNKNOWN`. Its code as read is kept in `source_county_fips5`. No crosswalk is used, because `data/raw/` holds no planning-region-to-county source, and a crosswalk would assign dollars to counties with no source for it. Why: the planning-region code cannot sit in the county grain. G-5 already gives such rows the `UNKNOWN` member. The state totals stay exact, and the county totals include the state's `UNKNOWN` county, so they reconcile to the state total.

Rule, applied in dbt when a place is read (`stg_usaspending_awards`, then `dim_place`):
- `county_fips5` is `UNKNOWN` when the county code is missing, or when the state is `09` and the county code is `09110` to `09190`.
- Otherwise `county_fips5` is the place county column as it is (5 characters). No `STATE || COUNTY` concatenation is applied to USAspending places (N-2). The concatenation applies only to the census files (MF-8).
- `source_county_fips5` keeps the county code as read.

Replaces:
- Phase 4 `dim_place` (line 138): the county member is `UNKNOWN` per state. It holds the missing-county places and the planning-region places of the rule above. `source_county_fips5` keeps the code as read.
- Plan table, G-5 row (line 60): add "Connecticut planning-region county codes (`09110` to `09190`) also map to the state's `UNKNOWN` county (MF-10)."
- Plan line 438 (MF-8 test text, "a place with a county FIPS code and no population row fails the test. The places that match no population row are listed for review."): replaced by the test below. A place with `UNKNOWN` county has no population row by design and is not joined.
- Plan line 456 ("Known risk, not settled here"): removed. This section settles it.
- Acceptance 4 (line 79), check 4: the county sum of a state includes that state's `UNKNOWN` county row. For Connecticut, the county sum is the eight 2021 counties plus the `UNKNOWN` county, and it equals the state `09` sum.
- Phase 4 `mart_obligations_monthly`: `population_2024` and `population_as_of` are NULL for the `UNKNOWN` county, so `obligations_per_person` is NULL there.

Tests (each written red first on a fixture, then run on the real build):
- `transform/tests/test_place_population_join.sql` (replaces the line 438 text): fails when a place's `county_fips5` is not `UNKNOWN` and has no row in `int_county_population_2024`, or when a non-`UNKNOWN` `county_fips5` is not 5 characters. Red fixture: a place with county `09999` fails; a place with county `09110` maps to `UNKNOWN` and passes. Real build: the count of `UNKNOWN`-county places and their FY2024 dollars, by state, is written to `DECISIONS.md`.
- `transform/tests/test_connecticut_planning_region.sql` (new): fails when any row of `dim_place` or `mart_obligations_monthly` has a county in `09110` to `09190`. Red fixture: a place row with county `09110` and no mapping fails; the same row with the mapping passes. Real build: the state `09` net obligations of the mart for the FY2024 months equal the sum of `fct_award_transaction` rows with state `09`.

### Phase 4 notes (cycle 3 notes N-3 and N-4)

- N-3 (red run per dbt test, cycle 3 review): the two MF-9 tests get a fixture. `transform/tests/test_population_no_double_count.sql` is red on a fixture with a duplicate `(state_fips, county_fips5)` key and a `09110` row. `transform/tests/test_population_fallback.sql` is red on a fixture with a 2021-only county whose `population_as_of` is 2024. Both then run on the real build.
- N-4: the mart column `population_2024` keeps its name. For the eight Connecticut counties it holds the 2021 figure, with `population_as_of` = 2021. `DECISIONS.md` states this for consumers of the mart.

### Notes applied (not blocking)

- N-1: the Phase 1 schema list (line 93) gains the `string_columns` key of kind `file`, a list of column names read as text (MF-8). The Phase 1 edit list (lines 375-378) gains the same key.
- N-2: applied in the MF-10 rule above.
- N-5 and N-6: no change. They are notes, and the review does not require them.

### Decision records and register

- `.context/proposals/cd-1-place-basis.md`: the choice adds the MF-10 rule (planning-region codes map to `UNKNOWN`, no crosswalk).
- `.context/deferrals/cd-1_deferral-register.md`: the G-5 row names `transform/tests/test_connecticut_planning_region.sql` and `transform/tests/test_place_population_join.sql`. No deferral is proposed, so `## Approved deferrals` is unchanged.

## Revision ledger (review e21870f18089)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-10 | Connecticut planning-region county codes map to the state's `UNKNOWN` county. No crosswalk. The join test fails only on a real miss. | Plan update 2026-10-21 (cycle 4), MF-10; Phase 4 `dim_place`, `mart_obligations_monthly`; plan table G-5; Acceptance 4 | `transform/tests/test_place_population_join.sql`; `transform/tests/test_connecticut_planning_region.sql`; check 4 in `oracle_map.yml` (county sum including `UNKNOWN` equals state sum) |

## Plan update 2026-10-21 (cycle 5)

RUN_BY_COMMAND: plan-update

Applies review `.context/reviews/plan_cd-1-pipeline.md` (sha256 fa84fbb4b889..., verdict READY WITH CHANGES, cycle 5 of 5). Open items: MF-11. MF-10 stays closed (review status table). This is the last update of the loop: the review is the fifth blocking review, so no further review is requested. The carry is under `## Carried review findings`. Where this section gives a different rule, this section wins.

### MF-11: places in the territories

Choice: the five territory states with no county rows in the census files keep their state and take the county member `UNKNOWN`. They are `60` (American Samoa), `66` (Guam), `69` (Northern Mariana Islands), `72` (Puerto Rico) and `78` (U.S. Virgin Islands). Their county code as read is kept in `source_county_fips5`. No population is joined, so their population columns are NULL. Why: `data/raw/census/` holds no `SUMLEV = '050'` rows for these states, so no county population exists. The rule is the MF-10 rule applied to these states. Option 2 (an exclusion in the join test) was rejected: it would drop 23 FY2024 rows from the source total, so check 4 could not reconcile to it.

Rule, applied in dbt when a place is read (`stg_usaspending_awards`, then `dim_place`). `county_fips5` is `UNKNOWN` when any of these holds:
- the county code is missing;
- the state code is `09` and the county code is `09110` to `09190` (MF-10);
- the state code is `60`, `66`, `69`, `72` or `78` (MF-11).

A missing state code maps the state key to `UNKNOWN` as well, so the state key of `dim_place` is never null. A place with a missing state has a missing county too (N-6). Otherwise `county_fips5` is the county column as it is. `source_county_fips5` keeps the code as read.

Replaces:
- The first bullet of the MF-10 rule (the `county_fips5` rule) is replaced by the list above. The MF-10 text otherwise stands.
- Phase 4 `dim_place` (line 138) and the MF-10 line for `dim_place`: the county member `UNKNOWN` covers the three cases above.

Tests (each written red first on a fixture, then run on the real build):
- `transform/tests/test_place_population_join.sql` (MF-10 text, unchanged): red fixture: a place with state `72` and county `72127` fails before the rule, because it has no population row. It passes after the rule maps it to `UNKNOWN`.
- `transform/tests/test_territory_places.sql` (new): fails when a row of `dim_place` with state in `60`, `66`, `69`, `72` or `78` has `county_fips5` other than `UNKNOWN`, or when a row of `mart_obligations_monthly` for those states has a non-NULL `population_2024` or `population_as_of`. Red fixture: a `dim_place` row with state `72` and county `72127` fails; the same row with county `UNKNOWN` passes.
- Real build: the count of FY2024 place rows with a territory state, by state, is written to `DECISIONS.md`. Expected from the review's check: Puerto Rico (`72`) 11, Guam (`66`) 5, U.S. Virgin Islands (`78`) 4, Northern Mariana Islands (`69`) 2, American Samoa (`60`) 1; 23 rows in total. A different count is written as found, and the plan does not change to match it.
- Acceptance 4 (check 4), for a territory state: its county sum is its `UNKNOWN` county row, and it equals the state sum.

### Phase 4 notes (cycle 4 review notes N-5 and N-6)

- N-5: `transform/tests/test_connecticut_planning_region.sql` (MF-10 text) scans the column `county_fips5` by name. It fails when a row of `dim_place` has `county_fips5` in `09110` to `09190`, or when a row of `mart_obligations_monthly` has a county in that range. The code kept in `source_county_fips5` is not scanned.
- N-6: applied in the rule above (the missing-state rule).

### Notes applied (not blocking)

- N-7 and N-8: no change. The review records them as checked, or as not blocking.

### Decision records and register

- `.context/proposals/cd-1-place-basis.md`: the choice adds the territory rule (MF-11) and the missing-state rule (N-6).
- `.context/deferrals/cd-1_deferral-register.md`: the G-5 row names `transform/tests/test_territory_places.sql`. No deferral is proposed, so `## Approved deferrals` is unchanged.

## Carried review findings

- MF-11 -> Phase 4 (test: `transform/tests/test_place_population_join.sql` red on state `72` county `72127`; `transform/tests/test_territory_places.sql`; count by state in `DECISIONS.md` from the real build)

## Revision ledger (review fa84fbb4b889)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-11 | Territory states `60`, `66`, `69`, `72`, `78` map to the `UNKNOWN` county, keep their state, and take no population. A missing state maps to the `UNKNOWN` state (N-6). | Plan update 2026-10-21 (cycle 5), MF-11; Phase 4 `dim_place`, `mart_obligations_monthly`; plan table G-5; Acceptance 4 | `transform/tests/test_place_population_join.sql`; `transform/tests/test_territory_places.sql`; check 4 in `oracle_map.yml` (territory county sum equals state sum); `DECISIONS.md` count by state (23 rows) |

## Plan update 2026-10-21 (P6 round 1)

RUN_BY_COMMAND: plan-update

Applies the newest P6 report of this run, `.context/adversarial/adversarial_cd-1-pipeline.md` (Mode: plan-gate, round 1, verdict REQUEST CHANGES, plan sha256 d19f6f11705f). Takes in blocking items B-1 and B-2, and conditions C-1 to C-4. P6 is below its limit (three cycles), so each B-n is applied here, not carried. The P3 review fa84fbb4b889 stays as the carry of the cycle 5 section, with MF-11 mapped under `## Carried review findings`. P3 is at its limit, so no `/plan-review` follows this update. The orchestrator runs `/de-adversarial-reviewer plan-gate` next. Where this section gives a different rule, this section wins. "Replaces" lines name the text they override.

### B-1: `max_events` counts the logical run

Choice: `max_events` counts the committed run, not the process. The count is the `meta_id` values in the batch files that `lake/_state/stream_manifest.json` lists, plus the distinct ids this process has yielded. The source stops when the count reaches `max_events`. A re-delivered id does not count.

Stop reasons, logged by the engine: `max_events`, `duration`, `replay_end`, `interrupted`. `interrupted` is the reason of a process that receives SIGTERM. On SIGTERM the sink flushes its buffer, commits the manifest, logs `interrupted` and exits 0.

Replaces:
- Phase 5 stop rule (the MF-3 text): "The source stops after it has yielded `max_events` distinct `meta_id` values in the run." The new rule is the logical count above.
- Acceptance 3 (the MF-3 text): replaced by the test below.

Acceptance 3, new text: a run with a forced interruption, then a resume, and an uninterrupted run, both over the same replay window with `max_events` = N (N is set by C-4). The harness sends SIGTERM to the first process after its manifest commit of the 500th distinct id. Then:
- the interrupted process ends with stop reason `interrupted`;
- the resumed process ends with stop reason `max_events`, and it lands N - 500 new ids;
- the uninterrupted run ends with stop reason `max_events`;
- both runs have N committed ids in the manifest;
- the `meta_id` set of the resumed run equals the set of the uninterrupted run, and no `meta_id` appears twice in the lake.

Test: `tests/test_stream_e2e.py` (Phase 7) asserts each stop reason and each set equality. Phase 5 `tests/test_stream_resume.py` adds the SIGTERM case: the process logs `interrupted` and its manifest lists every batch it wrote.

### B-2: dbt reads only committed batch files

Choice: `stg_recentchange` reads the batch files that the manifest lists, and no others. dbt reads `lake/_state/stream_manifest.json`, takes its committed batch list, and reads only those files. The incremental filter on `arrival_seq` stays.

Why: a crash leaves orphan batch files that the manifest does not list. A direct `dbt build --select stream` after the crash then never sees them. The MF-1 claim now holds for every dbt run, not only for the `make stream` path, because the orphans are never read.

Replaces:
- Phase 6 `stg_recentchange` (the text "Reads `lake/stream_recentchange/*.parquet`..."): the new text is the rule above.
- MF-1 Choice sentence "orphan batch files are deleted on start": it stays true, and the dbt rule above adds that orphans are never read.

Test (red first): `transform/tests/test_orphan_batch_excluded.sql`. A fixture lake holds batch 1 (listed in the manifest) and batch 2 (an orphan, not listed), each with its own `meta_id` values. The test fails when any `meta_id` of batch 2 appears in `stg_recentchange` or `fact_edit`. It passes when only batch 1 ids appear.

### C-1: superseded text and its replacement

The body keeps the superseded text. Before any execution, read the rows below. Where a row names an update, that update's text wins.

| Section (body text) | Superseded by |
|---|---|
| Phase 2, file source: "Money columns are read as strings and cast later" | MF-8 (`string_columns`), MF-7 |
| Phase 2, sitematrix bullet (the `server_name` derivation) | MF-5 (`sitematrix_flatten`); `server_name` in dbt `stg_sitematrix` |
| Phase 2, exit | MF-7 |
| Phase 3, all steps, TDD notes and exit | MF-4 and MF-7 (no engine step; Phase 3 keeps its heading) |
| Phase 4, staging and fallback text | MF-4 (`int_county_population_2024`) and MF-9 |
| Phase 4, `dim_place` | MF-8, MF-10, MF-11 |
| Phase 4, `mart_obligations_monthly` and checks 2 and 4 | C-2 (this update) |
| Phase 4, publish macro with renames | MF-6 (the macro only writes staging) |
| Phase 5, stop rule | MF-3, B-1 (this update) |
| Phase 5, dedup step 1 | MF-2 |
| Phase 5, manifest field list | MF-1 |
| Phase 5, exit | C-3 (this update) |
| Phase 6, `stg_recentchange` | B-2 (this update) |
| Phase 6, `is_late` | MF-1 |
| Phase 7, Makefile recipes | MF-6 |
| Phase 7, `tests/test_stream_e2e.py` note | B-1 and C-4 (this update) |
| Acceptance 3 | MF-3, B-1 (this update) |
| Reuse, `datafusion.SessionContext` line | MF-4 and MF-5 (no SQL step in this plan) |
| R-1 (Last-Event-ID support) | C-3 (this update) |
| R-3 (fallback counties "few or none") | MF-9 (count is 8) |

### C-2: `population_2024` is not additive

Choice: `population_2024` in `mart_obligations_monthly` is the value of its county. It repeats on every agency and month row of that county. The contract text of the mart says so: "not additive; sum obligations, never sum this column".

Check views:
- Check 2 (`mart_county_ranking_fy2024`) aggregates obligations per county from the mart, and takes the population once per county from `int_county_population_2024`.
- Check 4 (`check_county_state_source`) sums obligations only. Its population is never summed.

Tests (red first): `transform/tests/test_population_not_additive.sql`. A fixture county with 2 agencies and 2 months has the population of `int_county_population_2024` once in check 2, not four times. The test also fails when a county key has more than one `population_2024` value across the mart.

### C-3: the Last-Event-ID path is decided before Phase 5

Choice: a live check on `localhost:8099` is the first step of Phase 5, before any Phase 5 code. The check opens a stream, reads 500 events, then reconnects with `Last-Event-ID` set to the 500th id. The first event received must be the 501st. The result and the path are written to `.context/proposals/cd-1-stream-dedup-resume.md` and to `DECISIONS.md` before Phase 5 starts.

Paths:
- The replay supports `Last-Event-ID`: resume uses it (G-1).
- The replay does not support it: dedup-only resume. The reconnect has no `Last-Event-ID`, the replay starts again from the beginning, and the landed-id index (MF-2) drops every re-delivered `meta_id`. The result is exact because the drop is by `meta_id`. Acceptance 3 still holds.
- The replay does not answer: Phase 5 does not start, and the reason is recorded in `DECISIONS.md`.

Replaces:
- R-1 (the live check as "the first step of Phase 5's exit", and "any mismatch goes to DECISIONS.md"): the check is the Phase 5 entry step above.
- Phase 5 exit: the gate result and the chosen path are recorded before the exit runs.

### C-4: the replay supplies N distinct events

Choice: before Phase 7, a live run at the planned `DURATION` records in `DECISIONS.md` the count of distinct `meta_id` values in the replay window and the event rate. N = 2000 when the replay has at least 2000 distinct events. Otherwise N is the recorded count. The `max_events` of Acceptance 3 and of `tests/test_stream_e2e.py` is N.

The test runs with a 600 s cap. The recorded rate must show that N events arrive before the cap, with margin. A run that ends with `duration` fails the test.

Replaces:
- Acceptance 3 and the Phase 7 test text, which fix `max_events: 2000`: the value is N.

### Decision records and register

- `.context/proposals/cd-1-stream-dedup-resume.md`: the choice adds the stop rule of B-1 and the path chosen by C-3 once the live check runs.
- `.context/proposals/cd-1-stream-commit-manifest.md`: the choice adds that the manifest is the read list for dbt (B-2).
- `DECISIONS.md` (Phase 7): the population rule of C-2 for consumers of the mart, the live check result of C-3, and the replay count and rate of C-4.
- `.context/deferrals/cd-1_deferral-register.md`: no deferral is proposed, so `## Approved deferrals` is unchanged. The assumption rows for G-1 to G-8 are unchanged.

### Carried review findings

No change. MF-11 stays mapped as written in the cycle 5 section.

## Plan update 2026-10-21 (P6 round 2)

RUN_BY_COMMAND: plan-update

Applies the newest P6 report of this run, `.context/adversarial/adversarial_cd-1-pipeline_r2.md` (Mode: plan-gate, round 2, verdict REQUEST CHANGES, plan sha256 029d83d41d80...). Takes in blocking items B-1, B-2 and B-3 of that report, and conditions C-1 and C-2. The B-n of round 1 keep their text, and the round 1 section stays as written. Round 2 is below the P6 limit: the limit resolves to `adversarial_cycles` = 3 (`scripts/cadence_config.py resolve`; no config layer lowers it), so each B-n is applied here, not carried. The P3 limit is reached (`plan_review_cycles` = 5, the fifth blocking review is `.context/reviews/plan_cd-1-pipeline.md`, sha256 fa84fbb4b889...). So no `/plan-review` follows this update. The orchestrator runs `/de-adversarial-reviewer plan-gate` next. That is round 3, the last P6 round: if it is blocking, its items are carried. Where this section gives a different rule, this section wins. "Replaces" lines name the text they override. The P3 review fa84fbb4b889 stays as applied in the cycle 5 section, with MF-11 mapped below.

### B-1 (round 2): the `max_events` count is a set union

Choice: the count is the size of a union, not a sum. Let M be the set of `meta_id` values in the batch files that `lake/_state/stream_manifest.json` lists when the process starts, and updated on each manifest commit. Let Y be the distinct `meta_id` values this process has yielded. The source stops when `|M ∪ Y|` reaches `max_events`. An id in both sets counts once. A re-delivered id does not count, for the same reason.

Effect on the resumed run: after a dedup-only restart (C-3, path 2), the replay yields the committed ids first. They are in M, so they add nothing to the union and are dropped by the landed-id index (MF-2). The process lands `max_events - K` new ids, where K = `|M|` at the start of the resumed process (B-2 below).

Replaces:
- The B-1 choice sentence of round 1 ("plus the distinct ids this process has yielded"): the count is the union `|M ∪ Y|`, not M plus Y.

Test (red first): `tests/test_stream_resume.py`, case `test_restart_from_beginning_counts_union`. A fixture server replays from the first event. The manifest holds K = 500 committed ids. With `max_events` = 2000 the process lands exactly 1500 new ids and logs `max_events`. A sum-based count stops after 1000 new ids, so the test is red on that count and green on the union.

### B-2 (round 2): the committed count at interruption is read, not assumed

Choice: the harness sends SIGTERM after the manifest commit of the 500th distinct id, as before. It does not assume that exactly 500 ids are committed. The sink flushes and commits on SIGTERM (B-1 of round 1), so the committed count K can be above 500. After the interrupted process exits, the harness reads K = the number of distinct `meta_id` values in the batch files that the manifest lists. It asserts K >= 500. The resumed run must then land exactly N - K new ids.

Replaces:
- Acceptance 3 (B-1 of round 1): "the resumed process ends with stop reason `max_events`, and it lands N - 500 new ids" becomes "it lands N - K new ids, where K is read from the manifest after the interrupted process exits". The rest of Acceptance 3 stands.

Tests:
- `tests/test_stream_e2e.py` asserts K >= 500, and that the resumed run lands N - K new ids, and that both runs end with `max_events` (round 1 B-1).
- `tests/test_stream_resume.py`, SIGTERM case: the set of `meta_id` values in the manifest's batch files equals K, and the process logs `interrupted`.

### B-3 (round 2): the replay window is fixed before Phase 5

Choice: the replay window is the first N distinct events of the replay stream from its start, with no clock-based cut. The live check of C-3 (round 1) records two results before Phase 5 starts, in `.context/proposals/cd-1-stream-dedup-resume.md`:
- (a) two fresh connections to `GET http://localhost:8099/v2/stream/recentchange` (`Accept: text/event-stream`) return the same first 2000 `meta_id` values in the same order;
- (b) a reconnect with `Last-Event-ID` set to the `id:` line of the 500th event returns the 501st event first. The `id:` value is an opaque composite JSON array. The engine stores it as text and sends it back unchanged. G-1 holds with this reading.

If (a) fails, the window is a recorded capture. The harness captures the first N events once through the live server into `tests/fixtures/replay_window.jsonl`, and both runs of Acceptance 3 read that file through a local SSE fixture server. The choice is written to the proposal and to `DECISIONS.md`.

Replaces:
- Acceptance 3 (round 1 text): "over the same replay window" becomes "over the window of B-3 of round 2".
- C-3 (round 1): the check is the Phase 5 entry step, with checks (a) and (b) above added to the recorded result.

Tests: the check is a recorded probe, and its output is the record. The set-equality assertion is `tests/test_stream_e2e.py` (Phase 7), which runs over the window chosen here.

### C-1 (round 2 condition): the lake scope names the stream tables

Choice: the lake holds the four landed source tables and the stream's raw event state. The stream scope is `lake/stream_recentchange/` (raw event batches) and `lake/_state/` (the stream manifest). Both are raw data or position state, not derived tables, so the MF-4 rule holds.

Replaces:
- The MF-4 cycle 2 rule ("The lake holds only the four source tables"): the rule covers the batch landing. The stream adds the scope above.
- The test text of `tests/test_lake_tables.py` (cycle 2 MF-4, line 325): it asserts that the folder names under `lake/` are a subset of `usaspending_awards`, `census_county_2024`, `census_county_2021`, `sitematrix`, `stream_recentchange` and `_state`, and that a fixture run writes no folder outside that set. The fixture batch run writes the four source folders, so the subset test holds for it, and the Phase 2 exit is unchanged.

### C-2 (round 2 condition): the cycle limits are recorded

Recorded from `python3 scripts/cadence_config.py resolve`: `plan_review_cycles` = 5 and `adversarial_cycles` = 3. No config layer lowers either value. P6 round 2 is below the limit. Round 3 is the last P6 round. If round 3 is `REQUEST CHANGES`, its blocking items are carried under its heading and not applied.

### Decision records and register

- `.context/proposals/cd-1-stream-dedup-resume.md`: the choice adds the union count (B-1), the window of B-3 and the result of checks (a) and (b).
- `.context/proposals/cd-1-stream-commit-manifest.md`: the choice adds that K is read from the manifest after the interrupted process exits (B-2), and that dbt reads the manifest's batch list (round 1 B-2).
- `DECISIONS.md` (Phase 7): the window result, the K of the SIGTERM run, and the lake scope of C-1.
- `.context/deferrals/cd-1_deferral-register.md`: no deferral is proposed, so `## Approved deferrals` is unchanged. The assumption rows for G-1 and G-2 name the tests above.

### Carried review findings

- MF-11 -> Phase 4 (same as the cycle 5 section: test `transform/tests/test_place_population_join.sql` red on state `72` county `72127`; `transform/tests/test_territory_places.sql`; count by state in `DECISIONS.md` from the real build)

## Revision ledger (review fa84fbb4b889)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-11 | Territory states `60`, `66`, `69`, `72`, `78` map to the `UNKNOWN` county, keep their state, and take no population. A missing state maps to the `UNKNOWN` state (N-6). Restated in this update, no change of rule. | Plan update 2026-10-21 (cycle 5), MF-11; Plan update 2026-10-21 (P6 round 2), Carried review findings; Phase 4 `dim_place`, `mart_obligations_monthly`; plan table G-5; Acceptance 4 | `transform/tests/test_place_population_join.sql`; `transform/tests/test_territory_places.sql`; check 4 in `oracle_map.yml` (territory county sum equals state sum); `DECISIONS.md` count by state (23 rows) |

## Plan update 2026-10-21 (P7 scorecard 0ae7415cacae)

RUN_BY_COMMAND: plan-update

Applies the newest P7 scorecard of this run, `.context/benchmarks/cd-1_plan.json` (sha256 0ae7415cacae..., verdict FAIL, must-fix F01 to F09). The review fa84fbb4b889 is restated at the end (MF-11, no change of rule). The P3 limit is reached, so no `/plan-review` follows this update. After this update the orchestrator sends `/test-benchmark plan` again. Where this section gives a different rule, this section wins. "Replaces" lines name the text they override. The P6 round 3 carry is not part of this update.

### F01: one SSE fixture server and one lake tree builder

Choice: `tests/conftest.py` holds two shared helpers. `sse_fixture_server` serves a fixed event list over `Accept: text/event-stream`. It honors `Last-Event-ID`, drops the connection after a set number of events, refuses the first connections when asked, and can send a malformed `data:` line. `build_lake_tree` writes a `lake/` tree and an `out/` tree from a list of batch files and a manifest. Every stream test and the e2e test use these two helpers. No test defines its own SSE server or lake tree.

Replaces:
- Phase 5 TDD note 1 (`tests/test_stream_resume.py` "with a local SSE fixture server"): the server is `sse_fixture_server` from `tests/conftest.py`.
- Reuse and extension gains the two helper names above.

### F02: one singular test for the UNKNOWN county rule

Choice: the three singular files of the MF-10 and MF-11 text become one file, `transform/tests/test_place_county_unknown.sql`. Its fixture holds one place row per rule. Each row is red before its rule and green after it, except the join row, which fails by design:
- state `09`, county `09999`: fails. It is a real miss: not `UNKNOWN`, and no population row.
- state `09`, county `09110`: `county_fips5` is `UNKNOWN` (Connecticut rule, MF-10).
- state `72`, county `72127`: `county_fips5` is `UNKNOWN` (territory rule, MF-11), with NULL population.
- state `01`, county missing: `county_fips5` is `UNKNOWN` (missing-county rule).

The same file fails when a row of `dim_place` or `mart_obligations_monthly` has `county_fips5` in `09110` to `09190` (N-5 column name), or when a row for state `60`, `66`, `69`, `72` or `78` has a non-NULL `population_2024` or `population_as_of`.

Replaces:
- MF-10 tests: `transform/tests/test_place_population_join.sql` and `transform/tests/test_connecticut_planning_region.sql` are replaced by `transform/tests/test_place_county_unknown.sql`.
- MF-11 tests: `transform/tests/test_territory_places.sql` is replaced by `transform/tests/test_place_county_unknown.sql`. The carry under `## Carried review findings` names the new file.
- The recorded real-build counts (MF-10 and MF-11) stay in `DECISIONS.md`. They are recorded steps, not pytest.

### F03: the MF-2 restart case is a row of a parametrize table

Replaces the MF-2 test text (`tests/test_stream_dedup_restart.py`, Phase 5 test list): the case is row `restart_redelivers_committed_id` of the parametrize table in `tests/test_stream_resume.py`. Run 1 lands event X in a committed batch and stops. Run 2 receives X again from `sse_fixture_server`. X appears once in the lake, and run 2 writes no batch for it. `tests/test_stream_dedup_restart.py` is not created.

### F04: the e2e test reads a captured replay window

Choice: before Phase 5 starts, a recorded probe captures the first N distinct events of the live replay into `tests/fixtures/replay_window.jsonl`. Every pytest test reads that file through `sse_fixture_server`. No pytest test connects to `localhost:8099`. The results of the probes (C-3 checks (a) and (b), and the C-4 count and rate) are recorded in `.context/proposals/cd-1-stream-dedup-resume.md` and `DECISIONS.md`. The 600 s cap of C-4 stays as a safety cap on the e2e run. A stop reason of `duration` still fails the test.

Replaces:
- B-3 (round 2): "If (a) fails, the window is a recorded capture" is replaced by "The window is always the capture". Checks (a) and (b) still run as recorded probes.
- B-1 and C-4 test text (Phase 7 `tests/test_stream_e2e.py`): the test reads the capture, not the live server.

### F05: the engine-then-dbt harness

Choice: `tests/conftest.py` gets `run_engine_then_dbt(fixture_dir, engine_runs=1)`. For each run it runs `uv run python -m engine` with `--lake-root <fixture_dir>/lake`. Then it runs `uv run dbt test --project-dir transform --profiles-dir transform --select <test name>` with the dbt var `lake_dir=<fixture_dir>/lake` and the environment variable `CD1_WAREHOUSE=<fixture_dir>/out/warehouse.duckdb`. A new file, `tests/test_stream_dbt_after_engine.py`, holds two tests that call it. One runs `test_late_after_restart` with `engine_runs=2` (the first run is the SIGTERM run of B-1). The other runs `test_orphan_batch_excluded` with `engine_runs=1` and an orphan batch file written by the fixture. The two singular files in `transform/tests/` only assert the warehouse state. They start no engine.

Replaces:
- Phase 1: the engine takes `--lake-root` (default `lake`). The sink's rule "path under `lake/`" is checked against that root.
- Phase 4 sources: `read_parquet('lake/<table>/**/*.parquet')` becomes `read_parquet('{{ var('lake_dir', 'lake') }}/<table>/**/*.parquet')`. The manifest read of B-2 uses the same var.
- Phase 4 profile: the DuckDB path is `env_var('CD1_WAREHOUSE', 'out/warehouse.duckdb')`.

### F06 to F08: rows of the window rules

Choice: one new singular file, `transform/tests/test_edit_window_rules.sql`, holds the rows of the window rules. The 9-minute and 11-minute rows of Phase 6 TDD move into this file. Each row is red before its rule and green after it:
- lateness, F06: an event with lateness of exactly 10 minutes is on time. An event with lateness of 10 minutes and 1 second is late. Rule: `is_late = (prior_max_event_time - window_end) > INTERVAL 10 MINUTE`.
- alignment, F07: `meta_dt` at `HH:MM:00` and at `HH:MM:04:59` both give `window_start` `HH:MM`. `meta_dt` at `HH:MM:05:00` gives `HH:MM` plus 5 minutes. The windows are UTC.
- `net_bytes`, F08 (1): `length_old` NULL gives `net_bytes` 0 and `net_bytes_missing` = true. `length_new` NULL gives the same. `net_bytes_missing` is the flag column that Phase 6 names as "a flag"; it is added to `fact_edit`.
- `actor_type`, F08 (2): `bot` = true gives `bot`. `bot` = false gives `human`.
- tie-break, F08 (3): two windows with the same on-time count in `check_top_windows_en`. The window with the earlier `window_start` ranks first (N-3).
- wiki coverage, F08 (dim_wiki): an event whose `server_name` matches no `url` host of `stg_sitematrix` has a NULL `wiki_key`. The file fails when any `fact_edit` row has a NULL `wiki_key`. The real build must have zero such rows.

Replaces:
- Phase 6 TDD note 1 (the 9-minute and 11-minute fixture): the rows are in `transform/tests/test_edit_window_rules.sql`.

### F09: stream reader rows

Choice: these rows are added to the parametrize tables of `tests/test_stream_resume.py`:
- stop reasons `duration` (the `DURATION` cap comes first) and `replay_end` (the fixture ends early). Each row asserts the logged stop reason.
- backoff: the reconnect delays are 1, 2, 4, 8, 16 and 16 s. The source takes an injected `sleep` callable, so the test does not wait on the clock.
- connection refused: the first two connections are refused. The source reconnects and lands every event once.
- malformed `data:` line: the line is dropped, counted in the log as `malformed_lines`, and the stream continues. This choice is recorded in `DECISIONS.md`.

### Not changed (notes)

- F10: `tests/test_stream_commit.py` keeps its key assertion. The scorecard marks it as a note, not a must-fix.
- F11: no mutation run is added. The scorecard marks it as a note, and plan mode names no mutants.

### Decision records and register

- No new decision record. The malformed-line choice of F09 is recorded in `DECISIONS.md` (Phase 7 list).
- `.context/deferrals/cd-1_deferral-register.md`: the G-1 row names `tests/test_stream_resume.py` (the MF-2 row). The G-5 row names `transform/tests/test_place_county_unknown.sql`. No deferral is proposed, so `## Approved deferrals` is unchanged.

## Revision ledger (scorecard 0ae7415cacae)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| cd-1-F01 | One `sse_fixture_server` and one `build_lake_tree` in `tests/conftest.py`; no test defines its own | Plan update (P7 scorecard 0ae7415cacae), F01; Phase 5; Reuse and extension | `grep -n "def sse_fixture_server\|def build_lake_tree" tests/conftest.py`; no other `def` of either name under `tests/` |
| cd-1-F02 | Three singular files become `transform/tests/test_place_county_unknown.sql`, one row per rule | Plan update (P7 scorecard), F02; Phase 4 `dim_place` | Red and green rows of `transform/tests/test_place_county_unknown.sql` on its fixture; real-build counts in `DECISIONS.md` |
| cd-1-F03 | MF-2 restart case is row `restart_redelivers_committed_id` in `tests/test_stream_resume.py`; `tests/test_stream_dedup_restart.py` not created | Plan update (P7 scorecard), F03; Phase 5 | `pytest tests/test_stream_resume.py -k restart_redelivers_committed_id` |
| cd-1-F04 | e2e test reads `tests/fixtures/replay_window.jsonl` through `sse_fixture_server`; the capture is always used | Plan update (P7 scorecard), F04; Phase 7 | `grep -rn "localhost:8099" tests/` returns nothing; `tests/test_stream_e2e.py` reads the capture |
| cd-1-F05 | `run_engine_then_dbt` in `tests/conftest.py`; `tests/test_stream_dbt_after_engine.py` runs the two singular tests; Phase 1 `--lake-root`, Phase 4 `lake_dir` var | Plan update (P7 scorecard), F05; Phase 1; Phase 4 sources | `pytest tests/test_stream_dbt_after_engine.py`; singular files under `transform/tests/` hold no engine call |
| cd-1-F06 | Lateness rows at exactly 10 minutes (on time) and 10 minutes 1 second (late) in `transform/tests/test_edit_window_rules.sql` | Plan update (P7 scorecard), F06; Phase 6 `is_late` | Red and green rows of `transform/tests/test_edit_window_rules.sql` |
| cd-1-F07 | Alignment rows at `HH:MM:00`, `HH:MM:04:59` and `HH:MM:05:00` in `transform/tests/test_edit_window_rules.sql` | Plan update (P7 scorecard), F07; Phase 6 `window_start` | Red and green rows of `transform/tests/test_edit_window_rules.sql` |
| cd-1-F08 | Rows for `net_bytes` NULL (flag `net_bytes_missing`), `actor_type`, the N-3 tie-break and the unmatched wiki, in `transform/tests/test_edit_window_rules.sql` | Plan update (P7 scorecard), F08; Phase 6 `fact_edit`, `check_top_windows_en` | Red and green rows of `transform/tests/test_edit_window_rules.sql`; zero NULL `wiki_key` in the real build |
| cd-1-F09 | Rows for stop reasons `duration` and `replay_end`, the backoff schedule, connection refused, and malformed `data:` line in `tests/test_stream_resume.py` | Plan update (P7 scorecard), F09; Phase 5 | `pytest tests/test_stream_resume.py` lists each new row |
| cd-1-F10 | not changed: note only. The key assertion in `tests/test_stream_commit.py` stays | Phase 5 `tests/test_stream_commit.py` | none (note) |
| cd-1-F11 | not changed: note only. No mutation run is added | Quality gates | none (note) |

## Plan update 2026-10-21 (P3 review restated)

RUN_BY_COMMAND: plan-update

Restates the review `.context/reviews/plan_cd-1-pipeline.md` (sha256 fa84fbb4b889..., READY WITH CHANGES, cycle 5 of 5). Its only open item is MF-11, applied in the cycle 5 section. No change of rule.

## Revision ledger (review fa84fbb4b889)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-11 | Territory states `60`, `66`, `69`, `72`, `78` map to the `UNKNOWN` county, keep their state, and take no population. A missing state maps to the `UNKNOWN` state (N-6). Restated in this update, no change of rule. | Plan update 2026-10-21 (cycle 5), MF-11; Plan update (P7 scorecard), F02; Phase 4 `dim_place`, `mart_obligations_monthly`; plan table G-5; Acceptance 4 | `transform/tests/test_place_county_unknown.sql`; check 4 in `oracle_map.yml` (territory county sum equals state sum); `DECISIONS.md` count by state (23 rows) |
