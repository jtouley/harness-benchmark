RUN_BY_COMMAND: plan-create
Pipeline-Run: c11abad2-208f-4d85-bb55-2a95c021b556
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Ticket: cd-1
Spec: gh-1 (the issue text in .context/proposals/cd-1.md, sha256 854df8ca189270382db9a0bb3df3bad60e8e1ec3dcee6a9a691eb2758e2074fb)
Branch: feature/gh-1-pipeline

# Plan: gh-1 open-data pipeline (engine, Parquet lake, dbt marts, stream)

## Goal

Build a pipeline from the raw files and the Wikimedia edit stream to columnar tables that a BI tool can read:

- Question A (batch): FY2024 federal contract and grant money, in total and per resident, by state, county, awarding agency and month.
- Question B (stream): Wikipedia edits per wiki, namespace and 5-minute window, split human and bot, with net bytes added.

A small Python 3.12 engine reads `pipelines/*.yml` and runs ingestion into a Parquet lake under `lake/`. dbt (dbt-duckdb) builds everything after the lake and publishes marts under `out/marts/`. `make build` runs the batch path. `make stream DURATION=<seconds>` runs the stream path.

## Non-goals

- No commit, push, PR or ticket write in this block. Those are E4 and later.
- No change to `data/raw/`.
- No run against `stream.wikimedia.org`. The target is the replay at `http://localhost:8099/v2/stream/recentchange`.
- No dbt adapter for DataFusion. DataFusion and Polars run on the ingestion side only.
- No BI connection. Consumers read Parquet under `out/marts/`.

## Step 0

### Restated problem

The repo holds the P2 skeleton only:

- `Makefile`: `build` and `stream` exit 1 with "not implemented".
- `transform/`: `dbt_project.yml` and `profiles.yml` (duckdb at `out/warehouse.duckdb`), `models/` holds only `.gitkeep`.
- `pyproject.toml` pins `pyarrow`, `polars`, `datafusion`, `dbt-core`, `dbt-duckdb`, `duckdb`. No YAML library, no test runner.
- `.gitignore` already ignores `lake/`, `out/`, `transform/target/`, `transform/logs/`, `transform/dbt_packages/`.
- Data: four USAspending agencies (417, 418, 474, 485), each with an Assistance zip and a Contracts zip (eight zips, one CSV each). The two layouts differ (for example, the Contracts file names `primary_place_of_performance_state_code` and the Assistance file names `primary_place_of_performance_state_name`; the award key differs too). Census `co-est2024-alldata.csv` (2020 to 2024 estimates) and `co-est2021-alldata.csv` (2020 and 2021 only). `sitematrix.json` (1073 wikis, nested `site` lists).

### Design decisions

Each decision has a record in `.context/proposals/cd-1-<slug>.md`:

| Slug | Decision |
|---|---|
| `cd-1-lake-layout` | Parquet folders per table, atomic replace per write, load metadata without wall-clock time |
| `cd-1-money-decimal` | Money is `decimal128`, never float; per-person values are rounded at the last step only |
| `cd-1-yaml-validation` | JSON Schema (Draft 2020-12) validation with PyYAML node marks for file:line errors |
| `cd-1-engine-interface` | Sources, transforms and sinks are registries keyed by `kind`; transforms name `polars` or `datafusion` |
| `cd-1-population-vintage` | Per-person denominator is the July 1, 2024 estimate, with a defined fallback |
| `cd-1-geography-basis` | Geography is the recipient location; missing location goes to a sentinel place, never dropped |
| `cd-1-stream-commit` | One manifest file per micro-batch commits data and consumer position together |
| `cd-1-event-identity` | Dedupe key `meta.id`, first arrival wins; which events are edits |
| `cd-1-late-events` | Lateness by stream time, computed at ingest in arrival order, watermark persisted in the manifest |

### Blast radius

- `pyproject.toml`, `uv.lock`: add `pyyaml`, `jsonschema`, and `pytest` (dev).
- `Makefile`: `build` and `stream` become real targets. No other target is added.
- `engine/` (new package; the path is a gated prefix).
- `pipelines/build.yml`, `pipelines/stream.yml` (new).
- `tests/` (new): engine tests, fixture zips and fixture SSE server.
- `transform/models/` (sources, staging, dims, facts, marts, tests), `transform/dbt_project.yml` (model config only).
- `DECISIONS.md`, `oracle_map.yml` at the repo root (new).
- Generated, not committed: `lake/`, `out/`.

### Weak scope, challenged

1. The 2021 Census file cannot supply a July 1, 2024 estimate. It is a fallback only for a county that the 2024 file does not list at all. Phase 3 measures how often that fallback is used and records the count. The fallback is not a reason to read the 2021 file in the normal path.
2. Census county codes and USAspending county FIPS may not match for every county. Connecticut is the known case to check, because Census moved Connecticut to planning regions for recent vintages. Phase 3 measures join coverage in obligation dollars. Unmatched rows stay in the sentinel place (decision `cd-1-geography-basis`). They are never dropped, or Check 4 cannot reconcile.
3. "Net negative obligation per award" (Check 3) needs an award key. The Contracts and Assistance layouts name their award keys differently. Phase 3 picks the key per file type and records the choice in `DECISIONS.md`.
4. The request does not say what happens to the stream on a disconnect. The plan assumes SSE `Last-Event-ID` resume plus dedupe on `meta.id`. Phase 5 checks this against the replay server and records the result.
5. `make build` must give the same output when run twice. Load metadata must not hold wall-clock times. Otherwise every run changes the lake (decision `cd-1-lake-layout`).
6. Lateness depends on arrival order. A restart must not reset the watermark. The engine therefore computes `is_late` at ingest and persists the watermark in the commit manifest. dbt cannot recover arrival order later.

### Acceptance (mapped to the spec rules)

- A1. `make build` twice: the second run leaves the lake and `out/marts/` with the same row content (compared after sorting on the keys, with equal schemas). Byte equality is recorded where the writer is deterministic.
- A2. `make stream DURATION=<s>` stopped and restarted at least three times on the replay: no lost event and no double-counted event. The totals match an uninterrupted run over the same replay.
- A3. Windows use event time (`timestamp`, UTC, 5-minute windows starting on multiples of 5 minutes). Boundary tests pass for the late rule.
- A4. No float type on any money column in the lake or the marts (schema test).
- A5. dbt: `unique` and `not_null` on every model key, and `contract: enforced: true` on every mart.
- A6. An invalid pipeline YAML fails with file, line and problem.
- A7. A new source or mart of an existing kind needs YAML only. A test adds a fixture YAML and runs it with no Python change.
- A8. `oracle_map.yml` maps Checks 1 to 7 to a table and column or view. `DECISIONS.md` records each choice and the measured values from Phase 3. The seven checks run and their results go to `outputs/summary.md`.

## Quality gate commands (real in this repo)

- `uv sync` (Python 3.12, `.python-version`, `uv.lock`).
- `uv run pytest` (pytest is added in Phase 0).
- `uv run dbt parse --project-dir transform --profiles-dir transform`.
- `uv run dbt build --project-dir transform --profiles-dir transform`.
- `make build` and `make stream DURATION=<seconds>` (stubs today, real from Phase 7).

No other make target is assumed.

## Phases

### Phase 0: Dependencies and package skeleton

Exit criteria:
- `pyyaml`, `jsonschema` in `[project] dependencies`. `pytest` in a dev group. `uv.lock` updated.
- Package `engine/` with `__init__.py` and a `__main__.py` that prints usage and exits 2.
- `tests/` with one smoke test that imports `engine`.
- `uv run pytest` is green.

TDD note: the smoke test is written first and fails until `engine/` exists.

### Phase 1: Pipeline YAML loading and schema validation

Exit criteria:
- `engine/schema/pipeline.schema.json` (Draft 2020-12). Top-level keys: `sources`, `transforms`, `sinks`. Each entry has a `kind` from a fixed enum. A transform has `engine` in `{polars, datafusion}`. Unknown keys are errors.
- `python -m engine validate <file>` exits 0 on a valid file. On an invalid file it prints `<file>:<line>:<col>: <problem>` for each problem and exits 1.
- Line numbers come from PyYAML composed nodes (decision `cd-1-yaml-validation`).

TDD notes: fixtures in `tests/fixtures/yaml/`, one per error class: YAML syntax, unknown `kind`, missing `engine`, unknown key, wrong type for `partition_by`. Each test asserts the file, line and column.

### Phase 2: Engine core and Parquet lake sink

Exit criteria:
- The engine builds a graph from `inputs:` names and runs steps in dependency order. Each step's output is an Arrow table or a record batch reader (decision `cd-1-engine-interface`).
- Sink `parquet_lake` writes `lake/<table>/` with `partition_by` columns. It writes to a temp folder, then renames it over the table folder. A crash mid-write leaves the previous table readable.
- Load metadata columns are `_source_file` (path relative to the repo) and `_source_row` (integer). No wall-clock column.

TDD notes: test that two runs over the same input give equal content. Test that a failure injected between write and rename leaves the old table intact.

### Phase 3: File sources and clean source tables

Exit criteria:
- Source `usaspending_awards`: reads each of the eight zips with `zipfile` and `pyarrow.csv`. Every column is read as a string. Then money columns are cast to `decimal128(18,2)`. An unparseable cell fails the build with file and row number. The two layouts are mapped to one schema by a column map in YAML.
- Source `census_county_population`: long table of `county_fips` (5 characters, `STATE` + `COUNTY`), `year`, `population` from `co-est2024`. The 2021 file is read only for a county missing from the 2024 file (decision `cd-1-population-vintage`).
- Source `wiki_sites`: flattens `sitematrix.json` to one row per wiki (`dbname`, `code`, `url`, `closed`, language code, project).
- Measurements written to `DECISIONS.md`: rows per zip; count and dollars with blank recipient county FIPS; county codes present in USAspending and absent from Census (the Connecticut check); count of fallback population uses; the award key chosen for each file type.

TDD notes: small generated fixture zips with both layouts. Tests check the column map, decimal casts, and the failing-cell error.

### Phase 4: Polars and DataFusion transforms

Exit criteria:
- Transform `engine: polars` (dataframe and row-wise steps): for example, normalize FIPS to 5 characters, parse `action_date`, explode the wiki site list.
- Transform `engine: datafusion` (SQL text in the YAML): for example, filter `action_date_fiscal_year = 2024`, union the two layouts into the common schema.
- Both engines take and return Arrow data. The YAML names the engine. No Python change is needed to add a SQL transform.

TDD notes: each transform has a small input table and an expected output table. A test checks that the YAML `engine` key selects the right runner.

### Phase 5: Stream source and micro-batch stream sink

Exit criteria:
- Source `sse`: reads the SSE URL with `Last-Event-ID` on reconnect. Reconnect backoff starts at 0.5 s and caps at 10 s. It yields Arrow record batches, closed by a count (`batch_events`) or a time limit (`batch_seconds`), whichever comes first.
- The first 5 events of the replay are saved as a fixture and checked for the fields used (`meta.id`, `timestamp`, `wiki`, `namespace`, `bot`, `type`, `length`). Field names and units are recorded in `DECISIONS.md`.
- Sink `stream_lake` (decision `cd-1-stream-commit`): writes the batch file under `lake/stream_recentchange/`, then writes the manifest `lake/_commits/stream_recentchange/<seq>.json` with the SSE position, the watermark, the arrival sequence and the batch file list. The manifest is written to a temp name and renamed. On start, the sink reads the newest manifest, resumes from its position, and deletes batch files that no manifest lists.

TDD notes: a fake SSE server in `tests/` (random local port) drops the connection every K events. Fault injection kills the consumer after the data write and before the manifest, and after the manifest. Assertions: no lost event and no repeated event after three restarts.

### Phase 6: Event identity, edit rule and late events

Exit criteria:
- Dedupe on `meta.id`. The first arrival is kept. Later copies are dropped and counted in the manifest.
- `arrival_seq` is assigned in arrival order and is kept in the lake.
- Edit rule (decision `cd-1-event-identity`): `type` in `edit` or `new` is an edit. `net_bytes = length.new - coalesce(length.old, 0)`, with a null `length.new` counted as 0. Other types stay in the raw table and are not in the edit fact.
- Window: `window_start = floor(timestamp / 300) * 300`, `window_end = window_start + 300`.
- Late rule (decision `cd-1-late-events`): an event is late when, at its first arrival, the highest `timestamp` among earlier first arrivals is strictly greater than `window_end + 600`. A late event gets `is_late = true`, a row in `late_events`, and it is excluded from the window mart. The watermark is the highest `timestamp` seen, and it is persisted in the manifest.

TDD notes: boundary fixtures. An event whose max prior time equals `window_end + 600` is on time. One at `window_end + 601` is late. An out-of-order event that is not beyond the bound stays on time. A duplicate redelivery after reconnect is dropped and does not move the watermark.

### Phase 7: Pipeline YAML files and make targets

Exit criteria:
- `pipelines/build.yml`: sources `usaspending_awards`, `census_county_population`, `wiki_sites`; the transforms they need; sink `parquet_lake`.
- `pipelines/stream.yml`: source `sse` (URL from the YAML, with the replay URL as the default); sink `stream_lake`.
- `Makefile`: `build` runs `uv run python -m engine run pipelines/build.yml`, then `uv run dbt build --project-dir transform --profiles-dir transform`. `stream` requires `DURATION` (it fails with a message if it is empty), runs `uv run python -m engine run pipelines/stream.yml --duration $(DURATION)`, then `uv run dbt build --project-dir transform --profiles-dir transform --select tag:stream`.
- A1 check: two runs of `make build` give equal lake and mart content.

TDD notes: a test runs the build YAML on the fixture zips and asserts two runs give equal sorted content.

### Phase 8: dbt batch models: staging, star schema, Question A mart

Exit criteria:
- `transform/models/sources.yml`: lake tables read with `read_parquet` through the `lake_dir` var (default `lake`). The fixture lake is used by tests.
- Staging views for each source.
- Dimensions: `dim_agency` (awarding agency code and name), `dim_place` (state code, state FIPS, county FIPS, county name, with sentinel row `UNK` / `00000`), `dim_date` (FY2024 calendar dates, month key).
- Fact `fact_award_transaction`: grain is one source row of one award transaction. Key `transaction_key` is a hash of `_source_file` and `_source_row`. Columns: agency key, place key, date key, `federal_action_obligation` (decimal), award key.
- Mart `mart_fy2024_monthly_county_agency`: grain is month x state x county x awarding agency. Columns: `net_obligations` (decimal(18,2), exact sum), `population` (July 1, 2024 estimate), `obligations_per_person` (decimal(18,4), net obligations divided by population, half-even at the last step).
- Contracts enforced on the mart. Key tests on every model.

TDD notes: `dbt build` against the fixture lake first (red), then the real lake.

### Phase 9: dbt stream models: edit fact and 5-minute window mart

Exit criteria:
- `stream_edit_fact` (incremental, `unique_key = meta_id`, tag `stream`): one row per consumed edit, on time or late, with `is_late`, `wiki`, `namespace`, `actor_type` (`bot` or `human`), `window_start`, `net_bytes`. Incremental filter on `arrival_seq` above the current maximum.
- `mart_wiki_window_5min` (incremental, tag `stream`): grain is window_start x wiki x namespace x actor_type. `edit_count` and `net_bytes_added` (bigint). Built from on-time edits only (`is_late = false`).
- `late_events` is written by the engine. A view of it is available to dbt.
- Keys tested with `unique` and `not_null`.

TDD notes: run the stream models on batch 1, then batch 2. The count after batch 2 equals a full rebuild.

### Phase 10: Oracle map, decisions file, checks, and acceptance run

Exit criteria:
- `oracle_map.yml`: Checks 1 to 7 each mapped to a table and column, or to a SQL view.
- Check queries in `tests/checks/` (SQL against `out/warehouse.duckdb` or `out/marts/`):
  1. FY2024 net obligations per awarding agency.
  2. Ten counties with the highest FY2024 obligations per person.
  3. Count of awards with a negative net obligation in FY2024.
  4. One month: county totals equal state totals, and state totals equal the source total (the sum of `federal_action_obligation` for FY2024 over the lake).
  5. Edits and net bytes per wiki for the replayed hour, human and bot, with late events included.
  6. The 5-minute windows with the most on-time edits on `en.wikipedia.org`.
  7. Count of late events.
- `DECISIONS.md`: each record from `.context/proposals/cd-1-*.md` in plain words, with the measured values from Phases 3 and 5.
- Acceptance A1 and A2 run and recorded in `outputs/summary.md`. If the replay at `localhost:8099` is not reachable, A2 is recorded as blocked with the error. It is not marked passed.

## Phase order and risks

- Phase 3 measurements can change the award key and the fallback. Those changes are logged in `DECISIONS.md` and do not change the phase order.
- The replay format can differ from the spec. Phase 5 records the real field names before Phase 6 uses them.
- Stream volume for one hour is unknown. Batch size is a YAML value, so the size can be tuned without code change.

## Decision records to write (P1 output)

- `.context/proposals/cd-1-lake-layout.md`
- `.context/proposals/cd-1-money-decimal.md`
- `.context/proposals/cd-1-yaml-validation.md`
- `.context/proposals/cd-1-engine-interface.md`
- `.context/proposals/cd-1-population-vintage.md`
- `.context/proposals/cd-1-geography-basis.md`
- `.context/proposals/cd-1-stream-commit.md`
- `.context/proposals/cd-1-event-identity.md`
- `.context/proposals/cd-1-late-events.md`

## Reuse and extension

Reuses existing parts, with no new helper in the repo (the repo has no code yet):

- `pyarrow` (Arrow tables, Parquet writer, `pyarrow.csv`, `zipfile` input).
- `polars` and `datafusion` for transforms.
- `dbt-duckdb` reads the lake with `read_parquet`.
- `uv` and `uv.lock` for dependencies.
- Existing `Makefile` targets `build` and `stream` (names kept).
- Existing `transform/dbt_project.yml` and `transform/profiles.yml` (kept; models are added).
- Layouts documented in `data/raw/*/README.md`.

Extension points added (YAML selects the kind; no Python change to add a source or mart of an existing kind):

- Source kinds: `usaspending_zip_csv`, `csv`, `sitematrix_json`, `sse`.
- Transform engines: `polars`, `datafusion`.
- Sink kinds: `parquet_lake`, `stream_lake`.

Phase 7 and the fixture-YAML test cover the "YAML only" rule (A7).

## Footer

Next step: `/plan-review .context/plans/cd-1-gh-1-pipeline.plan.md`.

## Plan update 2026-10-21

Source: `.context/reviews/plan_cd-1-gh-1-pipeline.md` (cycle 1, `Verdict: READY WITH CHANGES`, review sha256 6698473c665c...). The prior text above is unchanged. The amendments below replace the named text for their phase. Where a phase below says "replaces", the earlier sentence no longer applies.

Open items: MF-1 to MF-5. The non-blocking notes (rollback, rounding function, shared test helpers) are not applied in this update.

### Phase 2 amendment (MF-1): atomic table swap

Replaces "It writes to a temp folder, then renames it over the table folder." Per table, the sink writes `lake/.tmp-<table>-<run_id>/` and then:

1. If `lake/<table>/` exists, rename it to `lake/.old-<table>-<run_id>/`.
2. Rename `lake/.tmp-<table>-<run_id>/` to `lake/<table>/`.
3. Delete `lake/.old-<table>-<run_id>/`.

Recovery runs at the start of every `engine run`, before any write or read of a table:

- A `lake/.old-<table>-*/` with no `lake/<table>/` is renamed back to `lake/<table>/`.
- A `lake/.old-<table>-*/` next to a `lake/<table>/` is deleted.
- Every `lake/.tmp-*/` is deleted.

The table path is empty only between steps 1 and 2. A crash in that window leaves the previous table intact under `.old-`, and dbt reads it only after the next `engine run` restores it. `make build` runs the engine before dbt, so dbt never reads the empty path.

TDD additions:
- Failure injected after the write and before step 1: the old table is unchanged, and the next run deletes the `.tmp-` folder.
- Failure injected between step 1 and step 2: the next run restores the old table, and its content equals the content before the crash.
- Failure after step 2: the new table is present, and the next run deletes the `.old-` folder.

### Phase 5 amendment (MF-2, MF-5): stream dedupe state and replay fixture

Seen set (MF-2). The sink keeps the set of `meta.id` values for the whole stream in memory. On start, after it reads the newest manifest and deletes the batch files that no manifest lists, it rebuilds the set from the `meta.id` column of every batch file the newest manifest lists. The manifest also records `duplicates_dropped` as a running total. The set is therefore derived from committed batch files, with no separate state file. An event in an uncommitted batch is absent from the rebuilt set, so its redelivery is a first arrival. It is kept once because its batch was deleted.

Replay fixture (MF-5). The field names come from a checked-in capture, not from a live read in each test:

- When the replay at `localhost:8099` is reachable at the start of Phase 5, capture the first 5 events as raw SSE into `tests/fixtures/sse/recentchange_first5.txt`. Record the capture date and the source URL in `DECISIONS.md`.
- The fake SSE server in `tests/` replays the checked-in fixture events. Phase 5 and Phase 6 tests do not need the live replay.
- When the replay is not reachable and no capture exists, Phase 5 and Phase 6 are blocked. Their exit is not marked passed, as with A2. Phases 0 to 4 and 8 continue.

### Phase 6 amendment (MF-2): dedupe scope tests

Added to the TDD notes:
- A redelivery of an event from a committed batch, after a restart, is dropped and counted in `duplicates_dropped`.
- A redelivery of an event from an uncommitted batch, after a restart, is kept exactly once.
- A dropped duplicate does not move the watermark.

### Phase 7 amendment (MF-3): A1 scope and stream dbt line

Replaces the Phase 7 exit line "A1 check: two runs of `make build` give equal lake and mart content." The Phase 7 A1 check covers the lake only: two runs of `make build` give equal lake content, compared on sorted keys with equal schemas. The mart part of A1 moves to the Phase 8 exit.

The `make stream` line `dbt build ... --select tag:stream` is valid from Phase 9 on, when the `stream` tag selects models. Phase 7 checks only the engine line of `make stream`.

### Phase 8 amendment (MF-3): mart A1 check

Added to the exit criteria: two runs of `make build` give equal `out/marts/` content, compared on sorted keys with equal schemas.

### Phase 9 amendment (MF-4): incremental rule for `mart_wiki_window_5min`

Replaces "incremental, tag `stream`" for this model with this rule. The model is incremental on the grain key `window_start`, `wiki`, `namespace`, `actor_type`, with `incremental_strategy = 'delete+insert'`. An incremental run:

1. Selects the grain keys of the `stream_edit_fact` rows with `arrival_seq` above the current maximum and `is_late = false`.
2. Recomputes `edit_count` and `net_bytes_added` for those keys from all on-time rows of `stream_edit_fact`.
3. Deletes the existing rows with those keys and inserts the recomputed rows.

`is_late` is fixed at first arrival and never changes, so a window's on-time rows do not change class after they are written. The recomputed values therefore equal a full rebuild.

Added TDD note: after batch 2, a key touched by both batches has exactly one row, and its values equal a full rebuild.

### Revision ledger (review 6698473c665c)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-1 | Atomic swap: rename the old table to `.old-`, rename the temp folder in, delete the old folder. Recovery at the start of each `engine run` restores the old table after a crash between the renames. | Phase 2 amendment (MF-1) | `test_swap_crash_between_renames_restores_old_table`, plus the failure-before-swap and failure-after-swap tests in the Phase 2 TDD additions |
| MF-2 | The dedupe seen set is rebuilt on start from the `meta.id` column of the batch files listed by the newest manifest. `duplicates_dropped` is kept in the manifest. | Phase 5 amendment (MF-2); Phase 6 amendment (MF-2) | `test_restart_drops_redelivered_committed_event` and `test_restart_keeps_redelivered_uncommitted_event_once` |
| MF-3 | The mart A1 check moves to the Phase 8 exit. The Phase 7 A1 check covers the lake only. The `make stream` dbt line is valid from Phase 9 on. | Phase 7 amendment (MF-3); Phase 8 amendment (MF-3) | `test_make_build_twice_lake_equal` (Phase 7) and `test_make_build_twice_marts_equal` (Phase 8) |
| MF-4 | `mart_wiki_window_5min` recomputes the affected grain keys from on-time rows and uses delete+insert on the grain key. | Phase 9 amendment (MF-4) | `test_window_mart_batch2_equals_full_rebuild` |
| MF-5 | The replay is captured once into `tests/fixtures/sse/recentchange_first5.txt`, and the fake SSE server replays it. Phases 5 and 6 are blocked when no capture exists and the replay is unreachable. | Phase 5 amendment (MF-5) | `test_sse_fixture_fields_match_decisions` (fixture fields match the `DECISIONS.md` record) |

RUN_BY_COMMAND: plan-update

## Plan update 2026-10-21 (cycle 2)

Source: `.context/reviews/plan_cd-1-gh-1-pipeline.md` (cycle 2, delta review, `Verdict: READY WITH CHANGES`, review sha256 `aea71577045f7cc98725d52a34f02f190fe4438c00c24db26936a53b6d0a2614`). The prior text and the earlier update above are unchanged. The amendments below replace the named text for their phase.

Open items: MF-6 and MF-7. The non-blocking notes of the review are not applied in this update.

Blocked path, used by MF-5 and MF-7: the replay at `localhost:8099` is not reachable at the start of Phase 5, and `tests/fixtures/sse/recentchange_first5.txt` does not exist.

### Phase 9 amendment (MF-6): high-water mark for `mart_wiki_window_5min`

Replaces step 1 of the incremental rule in the Phase 9 amendment (MF-4), which selected rows with "`arrival_seq` above the current maximum". Steps 2 and 3 of that rule stand.

- `stream_edit_fact` stores `arrival_seq` (bigint). Its own incremental filter selects `arrival_seq` above the maximum already in `{{ this }}`.
- The mart stores its mark in a column `last_arrival_seq` (bigint) on each row. For a key, `last_arrival_seq` is the highest `arrival_seq` among the on-time fact rows of that key. The column is part of the mart contract.
- The mark is `coalesce(max(last_arrival_seq), 0)`, read from `{{ this }}`. On the first run the table is empty and the mark is 0. `arrival_seq` starts at 1, so the first run selects every on-time row.
- An incremental run:
  1. Selects the grain keys of the `stream_edit_fact` rows with `arrival_seq > mark` and `is_late = false`.
  2. Recomputes `edit_count`, `net_bytes_added` and `last_arrival_seq` for those keys from all on-time rows of `stream_edit_fact`.
  3. Deletes the existing rows with those keys and inserts the recomputed rows.
- Why the mark is safe: `arrival_seq` is assigned in arrival order, and committed batches are in order, so a new row always has an `arrival_seq` above every earlier committed row. The mark cannot pass an unprocessed on-time row, because it is the maximum over on-time rows already written. The mark can lag (a late-only batch does not advance it). A lag only re-selects keys whose recomputed values do not change.
- Empty increment: when step 1 selects no keys, the run deletes and inserts nothing. The rows and the mark stay. This is not an error. A batch with only late events produces this case.

TDD additions:
- `test_window_mart_first_run_mark_zero`: on an empty mart, every on-time row is selected, and the result equals a full rebuild.
- `test_window_mart_no_new_on_time_rows_is_noop`: after batch 2, run the model again with no new batch. Rows, values and `last_arrival_seq` are equal before and after.
- `test_window_mart_late_only_batch_is_noop`: batch 2 holds only late events. The mart rows equal the batch 1 result. The late events are in `stream_edit_fact` with `is_late = true` and are not in the mart.

### Phase 7 amendment (MF-7): Phase 7 split under the blocked path

The Phase 7 exit splits into two parts with two statuses.

- Part A, continues on the blocked path: `pipelines/build.yml`, the `make build` target, and the batch lake check (two runs of `make build` give equal lake content, compared on sorted keys with equal schemas). Part A passes with no stream.
- Part B, blocked with Phase 5: `pipelines/stream.yml`, the `make stream` target (the `DURATION` guard and the engine line), and any check of them. Part B is not marked passed while Phase 5 is blocked.

### Phase 9 amendment (MF-7): Phase 9 status

Phase 9 is blocked when Phase 5 or Phase 6 is blocked. Its models read `lake/stream_recentchange/` (written by Phase 5) and `late_events` (written by Phase 6). Every Phase 9 exit line is blocked: `stream_edit_fact`, `mart_wiki_window_5min`, the `late_events` view, the key tests, and the `dbt build --select tag:stream` line. The Phase 9 TDD additions above also wait for the stream data.

### Phase 10 amendment (MF-7): checks and acceptance under the blocked path

Continues on the blocked path:
- Checks 1 to 4 and their `oracle_map.yml` entries. The batch part of `DECISIONS.md` (Phase 3 measurements).
- A1 for the lake and for the marts of the batch models.
- A4, A5 for the batch models, A6, and A7 for batch kinds.
- A8 for Checks 1 to 4.

Blocked:
- Checks 5, 6 and 7, which read the stream tables and `late_events`. Their `oracle_map.yml` entries and A8 entries stay open.
- A2, recorded as blocked with the error, as the plan already says.
- A3, which depends on the Phase 6 event-time windows and late rule.
- A5 for the stream models, and the Phase 5 replay record in `DECISIONS.md`.

`outputs/summary.md` lists Checks 5 to 7, A2 and A3 as blocked on this path, and does not mark them passed.

### Phase status summary (MF-7)

| Phase | Status on the blocked path |
|---|---|
| 0 to 4 | continue |
| 5 | blocked |
| 6 | blocked |
| 7 | Part A continues; Part B blocked |
| 8 | continues |
| 9 | blocked |
| 10 | Checks 1 to 4 and batch A-items continue; Checks 5 to 7 and A2, A3 blocked |

### Revision ledger (review aea71577045f)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-6 | The window mart keeps its high-water mark in the column `last_arrival_seq`. The increment selects keys with `arrival_seq` above that mark. An empty or late-only increment is a no-op. | Phase 9 amendment (MF-6) | `test_window_mart_first_run_mark_zero`, `test_window_mart_no_new_on_time_rows_is_noop`, `test_window_mart_late_only_batch_is_noop` |
| MF-7 | Blocked path: Phases 5, 6 and 9 blocked. Phase 7 split into Part A (continues) and Part B (blocked). Phase 10 Checks 5 to 7, A2 and A3 blocked. | Phase 7 amendment (MF-7); Phase 9 amendment (MF-7); Phase 10 amendment (MF-7); Phase status summary | `tests/checks/test_blocked_path.py` asserts that `outputs/summary.md` lists Checks 5 to 7, A2 and A3 as blocked when the replay is unreachable and no capture exists |

RUN_BY_COMMAND: plan-update


## Plan update 2026-10-21 (cycle 3)

Review read: `.context/reviews/plan_cd-1-gh-1-pipeline.md` (sha256 `6135ad33f49e...`, verdict READY WITH CHANGES). Its only open item is MF-8. MF-6 and MF-7 are closed in that review. The non-blocking notes of the review are not applied in this update.

Why: MF-8 found that `tests/checks/test_blocked_path.py` (MF-7 ledger row) reads `outputs/summary.md`. `outputs/` is outside the repo, no phase scheduled the test, and a word check passes with a wrong status. This update moves the check inside the repo: the acceptance run writes a status file, and the test asserts the status values and the absence of the stream tables.

### Phase 10 amendment (MF-8): blocked-path status file and test

- The acceptance run writes `out/run_status.json`. `out/` is inside the repo and gitignored. The file holds:
  - `checks`: a map from check id `1` to `7` to `passed`, `blocked` or `not_run`.
  - `acceptance`: a map from `A2` and `A3` to `passed`, `blocked` or `not_run`.
  - `stream_tables`: `built` or `skipped`. The run writes `skipped` when the Phase 9 models are not built.
- Test `tests/checks/test_blocked_path.py::test_blocked_path_status` is a Phase 10 exit line. It runs after the acceptance run on the blocked path. It reads `out/run_status.json` and asserts:
  1. `checks` has `blocked` for `5`, `6` and `7`, and `acceptance` has `blocked` for `A2` and `A3`. None of these has the value `passed`.
  2. `stream_tables` is `skipped`.
  3. `out/warehouse.duckdb` has no table or view named `stream_edit_fact`, `mart_wiki_window_5min` or `late_events`. The test queries `information_schema.tables`.
- TDD addition: the test is written before the acceptance run. It fails until the run writes the status file.

### Revision ledger (review 6135ad33f49e)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-8 | The blocked-path check moves inside the repo. It reads `out/run_status.json`, which the acceptance run writes. It asserts the `blocked` status of Checks 5 to 7, A2 and A3, and the absence of `stream_edit_fact`, `mart_wiki_window_5min` and `late_events` in `out/warehouse.duckdb`. | Phase 10 amendment (MF-8) | `tests/checks/test_blocked_path.py::test_blocked_path_status` |
