RUN_BY_COMMAND: plan-create

Ticket: cd-1
Branch: feature/gh-1-pipeline
Input: .context/proposals/cd-1.md (sha256 c2553ecf081c2ba9d20c7c6c7d1ca63605ea570fc7ac945d77218681e7d41492)

# Plan: open data pipeline (gh-1)

## Step 0: problem, design, blast radius, acceptance

### Problem

Build a pipeline from raw public data to a Parquet lake, then to a dbt-duckdb star schema with two published marts:

- Question A: FY2024 federal obligations by state, county, agency and month, in total and per person (population at July 1, 2024).
- Question B: Wikipedia edits per 5-minute event-time window (UTC) by wiki, namespace, and human/bot, with edit count and net bytes. Late events go to a `late_events` table.

The consumer of the Wikimedia SSE stream resumes after a disconnect without loss and without double counting.

### Scope challenges (stated in plan text, not deferred)

- C1. The replay server at `http://localhost:8099/v2/stream/recentchange` is not in the repo. Its resume behavior is unknown. Phase 3 probes it first. If it does not honor `Last-Event-ID`, the consumer resumes from its persisted cursor and dedupes on `meta.id` against the persisted set of seen ids. The plan does not assume server-side resume.
- C2. The USAspending archive covers 4 agencies (417, 418, 474, 485), not all federal agencies. Question A covers those agencies only. `DECISIONS.md` and the summary say so.
- C3. The Census 2024 file has `POPESTIMATE2024`, the July 1, 2024 estimate. The fallback to an earlier vintage is not needed. The plan records that in `DECISIONS.md`. The 2021 file is not loaded.
- C4. Contracts and Assistance files have different column sets. The shared columns are mapped in staging. Field names are taken from the header rows, not from the data dictionary alone.
- C5. "Late" is decided at first arrival. Arrival order is a property of the consumer, so the rule is computed in Python at ingest and stored with each event. dbt does not recompute it.

### Constraints

- Python 3.12. Dependencies are pinned in `pyproject.toml` and `uv.lock`. Do not change pinned versions. Do not add dependencies. Tests use stdlib `unittest`, and dbt tests cover the models.
- Money is exact. No `float` or `DOUBLE` in any money column or ratio.
- No GitHub or Linear calls. PR and ticket text go to `outputs/PR.md`.
- `make build` is idempotent. `make stream DURATION=<s>` runs the consumer for `<s>` seconds, then flushes and exits.

### Non-goals

- No Airflow, no orchestrator, no dashboard.
- No change to `pyproject.toml`, `uv.lock`, `.gitignore` rules for `lake/` and `out/`.
- No reprocessing of late events into already-published windows.

### Blast radius

- New: `pipeline/` (dlt sources and the SSE consumer), `tests/`, `transform/models/**`, `transform/macros/` if needed, `oracle_map.yml`, `DECISIONS.md`, `outputs/summary.md`, `outputs/PR.md`.
- Edited: `Makefile` (the two stub targets become real), `transform/dbt_project.yml` (model config only), `transform/profiles.yml` only if the target path must change.
- Generated, never committed: `lake/`, `out/`, `out/warehouse.duckdb`, `transform/target/`.
- Gated prefixes that this plan touches: `pipeline/`, `transform/`, `Makefile`. The E1 gate applies to all of them.

### Success signals

- S1. `make build` exits 0 on a clean checkout. A second run leaves `lake/` and `out/marts/` byte-identical in row content.
- S2. `make stream DURATION=60` against the replay server exits 0. Killing the replay server mid-run and restarting it leaves the set of stored `meta.id` values equal to an uninterrupted run over the same replay.
- S3. Question A totals equal an independent sum of the raw CSV rows, exact to the cent.
- S4. Question B window counts plus `late_events` rows equal the distinct events in the replay.
- S5. All 7 checks in `oracle_map.yml` pass.
- S6. `dbt build` passes, including contract enforcement and key tests.

### Acceptance

The plan is accepted when every phase has its exit criteria met, `DECISIONS.md` covers each design decision in the decision records, and `outputs/PR.md` and `outputs/summary.md` exist.

## Quality gate commands (real, from this repo)

Run from the repo root. `transform/profiles.yml` writes `out/warehouse.duckdb` relative to the working directory, so dbt runs from the root.

- `uv sync --locked` (checks that `uv.lock` matches `pyproject.toml`)
- `uv run python -m unittest discover -s tests -t .`
- `uv run dbt parse --project-dir transform --profiles-dir transform`
- `uv run dbt build --project-dir transform --profiles-dir transform`
- `make build`
- `make stream DURATION=60`

The current `Makefile` has `build` and `stream` stubs that exit 1. Phase 1 replaces them. No other make targets are assumed.

## TDD notes (apply to every phase)

Write the failing test first in `tests/`, then the code. Tests use `unittest` with fixtures under `tests/fixtures/`. The fixtures are small slices copied from the real raw files. Each phase names its test file.

## Reuse and extension

Existing helpers reused:

- `transform/dbt_project.yml` and `transform/profiles.yml` (the dbt project and the DuckDB target are kept).
- `Makefile` targets `build` and `stream` (names kept, bodies replaced).
- `pyproject.toml` pinned set: `dlt[parquet]==1.31.0`, `dbt-core==1.11.6`, `dbt-duckdb==1.11.0`, `duckdb==1.5.6`. No new dependency.
- The dbt model layering `staging -> intermediate -> marts` is the extension point. New models plug into it.
- dlt sources in `pipeline/` are one resource per raw input. The filesystem destination writes Parquet to `lake/`.

Adds no shared helper module. The extension point used is the dbt model layering above. A decision record covers the choice (see `Decision records`).

## Phases

### Phase 1: Toolchain and Makefile skeleton

Goal: the environment resolves and the make targets exist and fail clearly until later phases fill them.

- Run `uv sync --locked`. Confirm it succeeds without changing `uv.lock`.
- Replace the stubs in `Makefile`. `build` runs the phases in order: raw load, dbt build. `stream` runs the consumer with `DURATION`. Both targets fail when `DURATION` is missing or not a positive integer.
- Create `tests/` with a `test_makefile.py` that checks the targets exist and that `stream` rejects a missing `DURATION`.

Exit criteria:

- `uv sync --locked` exits 0.
- `make stream` with no `DURATION` exits non-zero with a message.
- `uv run python -m unittest discover -s tests -t .` passes.

### Phase 2: Batch sources to the lake

Goal: sitematrix, Census county population and USAspending FY2024 prime awards load into Parquet under `lake/raw/`.

- `pipeline/batch.py`: three dlt resources.
  - `sitematrix`: flatten `data/raw/sitematrix.json` to one row per site, with `dbname`, `code` (wiki, wiktionary and so on), `url`, `language_code`, `closed`.
  - `census_county`: read `co-est2024-alldata.csv`. Keep `SUMLEV = 050`. Columns: `STATE`, `COUNTY`, `STNAME`, `CTYNAME`, `POPESTIMATE2024`. Population is an integer.
  - `usaspending_awards`: read each zip in `data/raw/usaspending/` by streaming the CSV from the zip. Contracts and Assistance have different column names. Map to one shape: `source_file`, `award_type` (contract or assistance), `toptier_agency_code`, `action_date`, `action_date_fiscal_year`, `federal_action_obligation` as text, `place_state_fips`, `place_county_fips`, `place_state_name`, `place_county_name`, `awarding_agency_code`, `awarding_agency_name`. Keep `federal_action_obligation` as the source string and parse it to `DECIMAL(18,2)` in staging. The parse fails when a value has more than two decimal places.
- Write mode: `replace` per run. Re-running `build` gives the same rows.
- Filter: keep rows with `action_date_fiscal_year = 2024`. Count rows per zip and record them.

Tests: `tests/test_batch.py`. Fixture: a 3-row CSV per type plus a zip built in the test with `zipfile`. Check the column mapping and the fiscal-year filter. Check that `SUMLEV` filtering keeps only counties.

Exit criteria:

- `lake/raw/` holds one Parquet set per resource.
- Row count per zip is recorded in the run log.
- Tests pass.

### Phase 3: SSE consumer with resume and dedupe

Goal: `make stream DURATION=<s>` reads the replay stream, stores events, resumes after a disconnect, and stops on time.

First step (probe): connect to `http://localhost:8099/v2/stream/recentchange` and record the event fields, the `id:` line format, and whether a reconnect with `Last-Event-ID` replays from that id. Write the result into `pipeline/README.md`. Phase 3 design follows the probe result.

Design (holds whether or not the server supports `Last-Event-ID`):

- Cursor: the last `id:` value and the `meta.dt` of the last stored event, saved to a state file under `lake/state/` after each committed batch.
- Dedupe key: `meta.id` (the event UUID). Stored in `lake/raw/stream_events` with a unique key. Before a write, the consumer checks the persisted set of seen ids for the current replay window.
- Reconnect: exponential backoff, capped. On reconnect, send `Last-Event-ID` when the server supports it. Dedupe covers any replay.
- Late-event rule (computed at arrival, see Phase 5): the consumer keeps `max_event_time_seen` as a running value in the state file. For each first-arrival event it stores `arrival_seq`, `arrival_ts`, `max_event_time_before`.
- Stop: after `DURATION` seconds, flush, save the cursor, exit 0.

Module: `pipeline/stream.py` with pure functions for parsing SSE frames and computing the late flag. The I/O wrapper is separate so the functions are testable.

Tests: `tests/test_stream.py`. Cases: frame parsing with split lines; dedupe of a replayed id; late flag at the boundary (exactly 10 min after window end is not late, 10 min plus one second is late); cursor resume after a simulated disconnect in an in-process fake server (no network). Also a fake-server test where the server replays the last 3 events after reconnect, to check no double count.

Exit criteria:

- Unit tests pass.
- `make stream DURATION=60` against the live replay exits 0 and writes `lake/raw/stream_events`.
- Killing the replay server mid-run and restarting it: the stored id set equals an uninterrupted run over the same replay (S2).

### Phase 4: Staging and star schema in dbt-duckdb

Goal: staging models read the lake, and a star schema holds conformed dimensions and facts with keys and grain documented.

- Sources: `transform/models/sources.yml` defines the lake Parquet as external sources (`read_parquet` on `lake/raw/**`).
- Staging (`stg_`):
  - `stg_usaspending__awards`: parse `federal_action_obligation` with `CAST(... AS DECIMAL(18,2))`. Keep the source row key. Filter to FY2024.
  - `stg_census__county_population`: county FIPS `state || county` (5 characters). Population integer.
  - `stg_wiki__sites`: one row per `dbname`.
  - `stg_wiki__recentchange`: from the stream table. Event time from `meta.dt`, UTC. Namespace id, bot flag (`bot`), `length.new - length.old` for net bytes (null when either side is missing: counted as 0 net bytes and flagged).
- Star schema (intermediate and marts):
  - `dim_geography` (state, county): key `county_fips`, grain one row per county.
  - `dim_agency`: key `agency_code`, grain one row per agency.
  - `dim_date_month` and `dim_wiki`: keys `month_start`, `dbname`.
  - `fct_obligation_monthly`: grain county x agency x month. Measures: `obligation_total` (`DECIMAL(18,2)`), `award_count`.
  - `fct_wiki_edit_5min`: grain window x wiki x namespace x is_bot. Measures: `edit_count`, `net_bytes`.
- Contracts: `contract: {enforced: true}` on every mart. Column types declared in YAML.
- Tests: `unique` and `not_null` on every key, `relationships` from facts to dimensions. Grain documented in each model's `description`.

Tests: dbt tests are the tests for this phase. Add one singular test in `transform/tests/` that checks the `stg_usaspending__awards` total against the independent sum from the raw CSV.

Exit criteria:

- `dbt parse` and `dbt build` pass for staging and intermediate models.
- Key tests pass on every model.

### Phase 5: Marts, late events, and external publication

Goal: Question A and Question B marts publish to `out/marts/` as Parquet.

- Question A mart `mart_obligations_by_geo_agency_month`: `obligation_total`, `obligation_per_person` (`DECIMAL(18,4)`, computed as `obligation_total / population` with half-up rounding), `population` (from `dim_geography`), `award_count`. Grain county x agency x month. Also a state-level rollup view `mart_obligations_by_state_month` with the same measures. State totals equal the sum of county totals (oracle check).
- Question B windows: `fct_wiki_edit_5min` counts only on-time events (see late rule). Window: `[start, start + 5 min)`, UTC, by `meta.dt`.
- Late rule (decided at arrival in Phase 3, read here): an event is late when `max_event_time_before - window_end > 10 min`. Late events are written to the `late_events` table (`lake/raw/late_events`, published in `out/marts/late_events`). They are excluded from `fct_wiki_edit_5min`. The rule uses `max_event_time_before`, stored per event, so dbt does not recompute arrival order.
- Materialization: marts use dbt-duckdb `external` materialization with `location` under `out/marts/`. Check the plugin version behavior in dbt-duckdb 1.11.0 at the start of this phase. If the location option differs, the phase records the working form in `DECISIONS.md`.

Tests: dbt tests for both marts: grain uniqueness, `not_null` on measures, `accepted_values` on `is_bot`, and an `assert` singular test that state totals equal the county sum. `tests/test_late_rule.py` covers the arrival rule in Python against the same fixtures as Phase 3.

Exit criteria:

- `out/marts/` holds the Question A and Question B Parquet files and `late_events`.
- All mart tests pass.
- `dbt build` is green.

### Phase 6: Oracle map, idempotence, and end-to-end run

Goal: `oracle_map.yml` defines 7 checks, each runnable, and `make build` is idempotent.

`oracle_map.yml` checks (each has an id, a query or script, and the expected result):

1. `raw_row_conservation`: rows in `lake/raw/usaspending_awards` for FY2024 equal the row counts recorded per zip in Phase 2.
2. `obligation_total_exact`: sum of `obligation_total` in the Question A mart equals an independent sum over the raw CSV rows, exact to the cent (S3).
3. `state_equals_county`: each state-month total equals the sum of its county-month totals.
4. `per_person_recompute`: `obligation_per_person` equals `obligation_total / population` recomputed in Python with `Decimal`, for every row.
5. `stream_no_duplicate_ids`: `count(*) = count(distinct meta.id)` in `lake/raw/stream_events`.
6. `window_conservation`: sum of `edit_count` in `fct_wiki_edit_5min` plus rows in `late_events` equals distinct stored events in the replay window (S4).
7. `resume_equivalence`: the id set from a run killed and resumed equals the id set from an uninterrupted run over the same replay (S2).

Idempotence: run `make build` twice. Compare row counts and a sorted-row hash for each mart. Both must match.

Tests: `tests/test_oracle.py` runs the checks 1 to 5 on fixtures. Checks 6 and 7 run as scripts under `make stream` in the verification step, because they need the replay server.

Exit criteria:

- All 7 oracle checks pass.
- Second `make build` leaves marts unchanged.

### Phase 7: Documentation and PR text

Goal: deliverables and the PR text exist.

- `DECISIONS.md` at the repo root: each decision record summarized, the population vintage choice (C3), the four-agency limit (C2), the replay-server probe result (C1), the external materialization form (Phase 5), and each assumption A1 to A6 below.
- `outputs/summary.md`: what was built, the oracle results, the known limits.
- `outputs/PR.md`: PR title and body. No GitHub call.

Assumptions (the request does not say these; each one is built and then settled in the phase named):

- A1. The replay server may not support `Last-Event-ID`. Settled by the Phase 3 probe.
- A2. "By county" uses the prime award transaction place of performance (`prime_award_transaction_place_of_performance_county_fips_code`, state FIPS). Settled in Phase 2 and Phase 4.
- A3. "Agency" uses `awarding_agency_code` and `awarding_agency_name`. Settled in Phase 4.
- A4. Late events are excluded from the 5-minute aggregates and kept only in `late_events`. Settled in Phase 5.
- A5. The 2024 population file is the July 1, 2024 vintage. Settled in Phase 2 and DECISIONS.md.
- A6. Money uses `DECIMAL(18,2)` for totals and `DECIMAL(18,4)` for per-person values, with half-up rounding. Settled in Phase 4 and Phase 5.

Exit criteria:

- `DECISIONS.md`, `outputs/summary.md`, `outputs/PR.md` exist.
- `make build` and `make stream DURATION=60` both pass from a clean state.

## Decision records

Written to `.context/proposals/` with the ticket `cd-1`:

- `cd-1-lake-parquet-dlt` (storage format for raw lake: Parquet via dlt filesystem destination; rejects loading raw straight into the DuckDB file)
- `cd-1-sse-resume-dedupe` (consumer resume: persisted cursor plus dedupe on `meta.id`; rejects offset-only resume and at-most-once delivery)
- `cd-1-late-rule-at-arrival` (late flag set at first arrival from max event time seen before; rejects a dbt recompute on event time)
- `cd-1-money-decimal` (money as `DECIMAL(18,2)`, per person as `DECIMAL(18,4)`; rejects `DOUBLE`)
- `cd-1-marts-external-parquet` (marts published by dbt-duckdb external materialization to `out/marts/`; rejects a warehouse table only)
- `cd-1-no-new-dependencies` (tests use stdlib `unittest` and dbt tests; rejects adding pytest or dbt packages to avoid changing `pyproject.toml`)
- `cd-1-population-2024-vintage` (population from the July 1, 2024 file; rejects a fallback to the 2021 file)

No vibe-test report is pinned in the packet. No `G-n` gaps exist, so no deferral register is written.

## Ticket

Ticket: cd-1

## Next step

`/plan-review .context/plans/cd-1-gh-1-pipeline.plan.md`

RUN_BY_COMMAND: plan-update

## Plan update 2026-10-22

Input review: `.context/reviews/plan_cd-1-gh-1-pipeline.md` (sha256 b0f4e3dbf2a268b147c4731bd570d835a3bcffab5797a061ec50846c6f361a02), verdict READY WITH CHANGES.
Input plan before this update: sha256 9bb2c1ab74b4f339d84ba1f127632e8305762c694e4a70a45f246875e3fbbe36.

This section answers the four must-fix items MF-1 to MF-4. Where this section and the text of Phases 2 to 5 conflict, this section governs. The prior text above is kept.

### MF-1: resume when the server does not replay (Phase 3, S2)

The Phase 3 probe result sets one of two modes. The probe records the mode in `pipeline/README.md`.

- Mode R (the server replays from `Last-Event-ID`): dedupe on `meta.id` covers the replay. S2 is tested as written.
- Mode N (the server does not replay): after a reconnect the server sends only live events. Events emitted while the consumer was disconnected are never received. The plan does not recover them.
  - The consumer writes each disconnect interval (start and end, UTC, and the last cursor) to `lake/state/gaps.json`.
  - `outputs/summary.md` and `outputs/PR.md` state that S2 is NOT MET and list the gaps.
  - Mode N fails the Phase 3 exit criterion for S2. The plan's acceptance is not met, and the PR is not marked ready.
  - Oracle check 7 (`resume_equivalence`) runs in mode R only. In mode N it is recorded as failed with the reason `no replay`.

The claim "the design holds whether or not the server supports `Last-Event-ID`" in Phase 3 applies to dedupe only. The no-loss claim of Problem and S2 holds in mode R only.

### MF-2: where the seen-id set lives (Phase 3, S2, oracle check 5)

- Scope: all stored `meta.id` values in `lake/raw/stream_events`. The "current replay window" bound is removed.
- Store of record: the stored Parquet rows. At startup the consumer reads the `meta.id` column of `lake/raw/stream_events` into an in-memory set. The state file does not hold the seen set.
- Write disposition: dlt `append`, one write per committed batch. The filesystem Parquet destination does not enforce a unique key, so the consumer enforces uniqueness before the write. It drops every id already in the set. Within one batch it keeps the first occurrence only.
- Commit order for each batch:
  1. Write the new rows to `lake/raw/stream_events` and to `lake/raw/late_events` (see MF-3).
  2. Add the new ids to the in-memory set.
  3. Write the cursor to a temp file in `lake/state/` and rename it over the state file.
- A kill after step 1 and before step 3 leaves the cursor behind the stored rows. On restart the set is reloaded from the stored rows, so replayed events are dropped. No id is stored twice.

### MF-3: late events, one definition and one writer (Phase 3, Phase 4, Phase 5)

- One definition: `pipeline/stream.py` holds the constant `LATE_AFTER = timedelta(minutes=10)` and the function `is_late(window_end, max_event_time_before)`. It returns `max_event_time_before - window_end > LATE_AFTER`. No other file defines the threshold.
- `window_start` is `meta.dt` floored to 5 minutes, UTC. `window_end` is `window_start + 5 minutes`.
- Columns in `lake/raw/stream_events`, one row per first-arrival event: `meta.id`, `meta.dt`, `window_start`, `window_end`, `max_event_time_before`, `arrival_seq`, `arrival_ts`, `is_late` (boolean, computed by `is_late()` at arrival).
- Writer of `lake/raw/late_events`: the consumer commit step in `pipeline/stream.py` (MF-2 step 1). It writes the rows of the same batch where `is_late` is true, with the same columns.
- dbt does not compute the late flag. It reads `is_late` as stored.
  - `transform/models/sources.yml` defines two sources: `stream_events` (`read_parquet` on `lake/raw/stream_events/**`) and `late_events` (`read_parquet` on `lake/raw/late_events/**`).
  - `stg_wiki__recentchange` reads `stream_events` and passes `is_late` through.
  - `fct_wiki_edit_5min` filters `where not is_late`.
  - The Phase 5 phrase "uses `max_event_time_before`" is replaced by "reads `is_late`".
- Publication: the `late_events` model is materialized to `out/marts/late_events` as in Phase 5.

### MF-4: row key for USAspending awards (Phase 2, Phase 4)

- Phase 2 shape adds three columns to `lake/raw/usaspending_awards`:
  - `source_file`: the zip file name, then `/`, then the CSV member name.
  - `source_row`: the 1-based data row number in that member, header excluded. It is counted before the FY2024 filter, so it does not change when the filter changes.
  - `award_row_key`: `source_file || '#' || source_row`. This is the unique key.
- Phase 2 records row counts per member before the filter and FY2024 row counts after it.
- Phase 4: `stg_usaspending__awards` keeps `award_row_key`. The `unique` and `not_null` key tests in Phase 4 apply to `award_row_key`. The row counts compared from Phase 1 to Phase 6 are counts of distinct `award_row_key`.

### Carry

No `MF-n` is carried. No P6 report applies. No P7 scorecard is pinned.

## Revision ledger (review b0f4e3dbf2a2)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-1 | Probe result sets mode R or N. Mode N fails S2 and acceptance, and records disconnect gaps in `lake/state/gaps.json`. The no-loss claim is limited to mode R. | Plan update 2026-10-22, MF-1; Phase 3 | `tests/test_stream.py::test_no_replay_records_gap`; oracle check 7 recorded as failed in mode N |
| MF-2 | Seen-id set is all stored `meta.id` values in `lake/raw/stream_events`, reloaded at startup, enforced by the consumer before a `append` write. Commit order makes a kill between write and cursor save safe. | Plan update 2026-10-22, MF-2; Phase 3 | `tests/test_stream.py::test_kill_between_write_and_cursor_no_duplicate`; oracle check 5 `stream_no_duplicate_ids` |
| MF-3 | One threshold `LATE_AFTER` and one function `is_late()` in `pipeline/stream.py`. Writer of `lake/raw/late_events` is the consumer commit step. dbt reads `is_late` and does not recompute it. `sources.yml` adds `late_events`. | Plan update 2026-10-22, MF-3; Phase 3, Phase 4, Phase 5 | `tests/test_late_rule.py` boundary cases; `grep -rn "LATE_AFTER\|minutes=10" pipeline transform/models` returns only the definition in `pipeline/stream.py` |
| MF-4 | Phase 2 shape adds `source_file`, `source_row`, `award_row_key`. Phase 4 key tests apply to `award_row_key`. | Plan update 2026-10-22, MF-4; Phase 2, Phase 4 | `tests/test_batch.py::test_award_row_key_unique_per_member`; dbt `unique` and `not_null` on `award_row_key` in the staging schema |

## Plan update 2026-10-22

Input review: `.context/reviews/plan_cd-1-gh-1-pipeline.md` (sha256 ef75c715e884b90f1937976e589f1d8217643daba3a3bd0dbee4bf5018528f96), verdict READY WITH CHANGES. This is the newest review. Its open item is MF-5. MF-1 to MF-4 are closed in that review and are not changed here.
Input plan before this update: sha256 aa3e04ecaedc1870b8a89ef6c09882385a5df149bc4a6a92c9c0a537331179ea.

This section governs over the Phase 3 bullets it names. The prior text above is kept.

### MF-5: max event time after a restart (Phase 3, S2, MF-3 `is_late`)

- Single source: at startup the consumer derives `max_event_time_seen` as `max(meta.dt)` over all rows in `lake/raw/stream_events`. This is the same read that MF-2 uses for the id set. The state file does not hold `max_event_time_seen`, and nothing reads it as a source of that value. The state file holds the last `id:` value only. The Phase 3 bullet that keeps `max_event_time_seen` in the state file, and the `meta.dt` of the last stored event in the cursor, are superseded by this text.
- Why the stored rows give the uninterrupted value: `lake/raw/stream_events` holds one row for every first-arrival event, late events included (MF-3). A replayed event is dropped before the write (MF-2), so it adds no new value. The maximum over the stored rows is therefore the maximum over all first-arrival events seen so far.
- Empty store: when `lake/raw/stream_events` has no rows, `max_event_time_seen` is null. The first event gets `max_event_time_before` null, and `is_late` is false for it.
- Within a batch: events are handled in arrival order. For each first-arrival event, `max_event_time_before` is the in-memory `max_event_time_seen` before that event. After the event, the in-memory value becomes the larger of itself and the event's `meta.dt`. Dropped duplicates do not change it. The value is written to disk only through the rows of MF-2 step 1.
- Restart: at startup the consumer reads the id set and `max_event_time_seen` from the same stored rows. A kill after MF-2 step 1 leaves those rows ahead of the cursor. The restart reads them, so the maximum includes their events, and the replayed copies are dropped. Every first-arrival event then gets the same `max_event_time_before`, and so the same `is_late`, as in an uninterrupted run.
- Test: `tests/test_stream.py::test_kill_between_write_and_cursor_same_is_late`. The fake server serves one fixed replay fixture. The fixture includes at least one event more than 10 minutes behind the running maximum, so some rows have `is_late` true. Run A is uninterrupted. Run B is killed by the test after MF-2 step 1 of one batch, then restarted on the same lake and the same fixture. The test asserts that the sets of (`meta.id`, `max_event_time_before`, `is_late`) from run A and run B are equal.

### Carry

No `MF-n` is carried. No P6 report applies. No P7 scorecard is pinned.

### Review notes not applied

The review notes N-1 to N-9 are not must-fix items and are not applied in this update, except as follows. The ledger heading uses the first 12 characters of the review sha256, as the plan-update contract requires, not the full value that N-1 asks for. N-4 (whether `make build` runs the stream, and how the stream sources behave when empty) is still open and needs a decision before E1 runs Phase 4.

## Revision ledger (review ef75c715e884)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-5 | `max_event_time_seen` is derived at startup as `max(meta.dt)` over `lake/raw/stream_events`, the same store as the id set. The state file holds the cursor only. A kill between the write and the cursor gives the same `is_late` as an uninterrupted run. | Plan update 2026-10-22, MF-5; Phase 3 | `tests/test_stream.py::test_kill_between_write_and_cursor_same_is_late` |

## Plan update 2026-10-22

Input review: `.context/reviews/plan_cd-1-gh-1-pipeline.md` (sha256 62d0005f60b729346303d42d57e1e2e05f977f5142c12166d5bba0fe08d55909), verdict READY WITH CHANGES. This is the newest review. Its open item is MF-6. MF-1 to MF-5 are closed in that review and are not changed here.
Input plan before this update: sha256 89ea8f7596788b63f2eaf19f480677bbf47604a94c2fd1c1a8ad8a09c99197a9.

This section governs over the Phase 3, Phase 4 and Phase 5 bullets it names, and over the MF-3 writer bullet. The prior text above is kept.

### MF-6: one writer for late events (Phase 3, Phase 4, Phase 5, S4, oracle check 6)

Rule: `late_events` is derived, not written. Its only source is the `is_late = true` rows of `lake/raw/stream_events`, and dbt builds it at publication. The consumer writes one store, `lake/raw/stream_events`. No second write exists that a kill can split from the first.

- Phase 3 commit order: MF-2 step 1 writes the new rows to `lake/raw/stream_events` only. Steps 2 and 3 are unchanged. The MF-3 bullet that names the consumer as writer of `lake/raw/late_events` is superseded. The consumer writes no file under `lake/raw/late_events/`.
- Phase 4: `transform/models/sources.yml` defines one source, `stream_events`. The `late_events` source named in MF-3 is removed.
- Phase 5: `late_events` is a dbt model. It selects the `is_late = true` rows of `stg_wiki__recentchange` with the same columns as the stream rows. It is materialized by dbt-duckdb `external` to `out/marts/late_events`, as Phase 5 already says. Grain: one row per `meta.id`, with `unique` and `not_null` on `meta.id`.
- Phase 5: `fct_wiki_edit_5min` keeps `where not is_late` (MF-3).
- Oracle check 6 (`window_conservation`) reads `out/marts/late_events` and the `fct_wiki_edit_5min` table in the same `dbt build`, so both sides come from the same stored rows.

Restart: the late set is a function of the stored rows only. MF-5 makes those rows the same after a kill and restart as in an uninterrupted run, so the late set is the same too.

- Test: `tests/test_stream.py::test_kill_between_write_and_cursor_same_is_late` is extended, not replaced. After the kill and restart, it asserts that the `meta.id` set of rows with `is_late` true in `lake/raw/stream_events` for run B equals the same set for run A. This is the `late_events` set of run B, since that set is the `is_late = true` subset of `stream_events`. The MF-5 assertion stays.

Carry: no `MF-n` is carried. No P6 report applies. No P7 scorecard is pinned.

Review notes not applied: N-1 to N-9 are not must-fix items and are not applied in this update. N-4 is still open and needs a decision before E1 runs Phase 4.

## Revision ledger (review 62d0005f60b7)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-6 | `late_events` is a dbt model over the `is_late = true` rows of `lake/raw/stream_events`, built at publication. The consumer writes only `stream_events`, so a kill cannot split late rows from stream rows. The MF-3 writer and source for `lake/raw/late_events` are removed. | Plan update 2026-10-22, MF-6; Phase 3, Phase 4, Phase 5 | `tests/test_stream.py::test_kill_between_write_and_cursor_same_is_late` (run B late set equals run A late set); oracle check 6 `window_conservation`; `grep -rn "lake/raw/late_events" pipeline transform` returns no match |

## Plan update 2026-10-22

Input review: `.context/reviews/plan_cd-1-gh-1-pipeline.md` (sha256 751fc55a25abda9993ec5d2076b39a29a13f03f2837e51f1e3548594c3b6d5d6), verdict READY WITH CHANGES. This is the newest review. Its open item is MF-7. MF-1 to MF-6 are closed in that review and are not changed here.
Input plan before this update: sha256 069e47c78f154da980f620ce4a47dc2b73e54d4d27779e56d5e7e80ff787720c.

RUN_BY_COMMAND: plan-update

This section governs over the Phase 6 sentence that runs check 6 under `make stream`, and over the MF-6 bullet that reads check 6 "in the same `dbt build`". The prior text above is kept.

### MF-7: oracle check 6 run point (Phase 6, S4, oracle check 6)

Check 6 (`window_conservation`) has one run point. It is the S4 verification step, in this order:

1. `make stream DURATION=<s>` appends the rows to `lake/raw/stream_events`.
2. `make build` runs the raw load and the `dbt build`. That dbt build writes `out/marts/late_events` and `fct_wiki_edit_5min` from those stored rows.
3. Check 6 runs and reads `out/marts/late_events` and `fct_wiki_edit_5min` as written by step 2.

No `make stream` runs after step 2 in that step. Check 6 has no other run point, so it never compares marts from one run with stored rows from another.

- Check 7 (`resume_equivalence`) is not changed. It needs the replay server, so it stays under `make stream` in the verification step.
- Phase 6 "Tests" bullet: check 6 is not listed as a `make stream` script. It is listed under the S4 verification step above.

Carry: no `MF-n` is carried. No P6 report applies. No P7 scorecard is pinned.

Review notes not applied: N-1 to N-11 are not must-fix items and are not applied in this update. N-4 (whether `make build` runs the stream, and how the stream sources behave when empty) is still open and needs a decision before E1 runs Phase 4.

## Revision ledger (review 751fc55a25ab)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-7 | Check 6 `window_conservation` runs once, after `make build` in the S4 verification step, and reads the marts that build wrote from the stored rows. No `make stream` runs after that build. Check 7 stays under `make stream`. | Plan update 2026-10-22, MF-7; Phase 6 (oracle checks, verification step), S4 | Oracle check 6 `window_conservation` run as the step after `make build` in the S4 verification step; the verification order lists no `make stream` after `make build` |
