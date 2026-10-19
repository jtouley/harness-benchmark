# Plan: open data pipeline (gh-1)

RUN_BY_COMMAND: plan-create

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Task: gh-1. Local ticket file: `.context/tickets/gh-1.md`.
Branch: `feature/gh-1-pipeline`. Base: `origin/main`.

## Step 0: problem, design, blast radius, acceptance

### Problem

Build one pipeline with two parts.

- Question A (batch): federal FY2024 award money by state, county, agency and month, in total and per person.
- Question B (stream): Wikipedia edits per wiki, namespace and 5-minute window, split by human and bot, with net bytes.

The pipeline writes a Parquet lake, a dbt project that builds star schemas and marts, and published marts under `out/marts/`.

### Current state

The repository is a skeleton.

- `Makefile` has `build` and `stream` targets. Both print "not implemented" and exit 1.
- `pyproject.toml` pins `dlt[parquet]==1.31.0`, `dbt-core==1.11.6`, `dbt-duckdb==1.11.0`, `duckdb==1.5.6`. Do not change these pins.
- `.python-version` is `3.12`. The host `python3` is 3.13. Run every Python step through `uv` with Python 3.12.
- `transform/` has `dbt_project.yml`, `profiles.yml` (DuckDB at `out/warehouse.duckdb`) and an empty `models/`.
- `data/raw/` holds the USAspending zips (8 files, 4 agencies, assistance and contracts), the Census county files (2024 and 2021 vintages), and `sitematrix.json`.
- The replay stream answers at `http://localhost:8099/v2/stream/recentchange`. It sends SSE comment lines (`:ok`) and `id` values that are JSON arrays.
- `.gitignore` already ignores `lake/`, `out/` and `transform/target/`.
- `.cadence.json` puts `pipeline/`, `transform/` and `Makefile` under the gated prefixes. Code for this run goes under `pipeline/` and `transform/`.

### Blast radius

Files that change:

- `pipeline/` (new): batch ingestion, stream consumer, shared helpers, tests.
- `transform/models/` (new): sources, staging, star schema, marts, checks.
- `transform/` config only if the dbt-duckdb external location needs it.
- `Makefile`: implement `build` and `stream`. Add no other target.
- `oracle_map.yml` (new, repository root).
- `DECISIONS.md` (new, repository root).

Files that do not change: `pyproject.toml`, `uv.lock`, `.python-version`, `data/raw/**`, `.cadence.json`.

Generated and ignored: `lake/`, `out/`, `transform/target/`, `transform/logs/`.

### Non-goals

- No BI tool, dashboard or chart.
- No new Python or dbt dependency. Use the standard library for tests (`unittest`) and the pinned stack for everything else.
- No live run against `stream.wikimedia.org` as a gate. The replay is the test target. A live run is an optional demo.
- No CI, scheduler or deployment.

### Scope challenges and default decisions

The ticket leaves choices open. Each default below goes into `DECISIONS.md` with the reason. Change a default only with a reason that the plan review accepts.

- D1. Place is the place of performance (`pop_state_code`, `pop_county_code`), not the recipient location. The ticket says "where the money went".
- D2. Transactions with no county or state code, or with a foreign place code, go to an `UNKNOWN` place member. Without it, state and county totals do not reconcile to the source total (check 4).
- D3. Population is the `POPESTIMATE2024` value (July 1, 2024) from the 2024 vintage file. Amendment A says to use the latest earlier estimate when a county has none. Fallback order: `POPESTIMATE2023`, `POPESTIMATE2022` from the 2024 file, then `POPESTIMATE2021` from the 2021 file. Record each county that uses a fallback. Never use `ESTIMATESBASE2020` or `POPESTIMATE2020` as the population.
- D4. Only summary level 050 (county) rows are used. State rows (040) are not used as county rows.
- D5. Per person is a ratio. A state's per-person value is state obligations divided by the sum of its county populations. Never sum a per-person column across rows.
- D6. A stream "edit" has `type` `edit` or `new`. Other types (`log`, `categorize`) are not edits. They still count for the watermark (D7).
- D7. The lateness watermark uses the event time of every consumed event, all types. Dropping non-edit events from the watermark would change which edits are late.
- D8. A late edit is kept in `fct_edit` with `is_late = true` and copied to `late_events`. The window mart counts only on-time edits. Check 5 reads `fct_edit` and so counts late edits too. Check 7 counts late edits.
- D9. Event time is `meta.dt`, parsed as UTC. Phase 0 checks that `meta.dt` matches the `timestamp` field for sampled events.
- D10. A null `length.new` or `length.old` adds 0 bytes and still counts as one edit. Record how many events have a null length.
- D11. Dedupe key for stream events is `meta.id`. The first arrival wins.
- D12. Money uses `DECIMAL`. Phase 0 checks that the source amounts fit `DECIMAL(18,2)` without rounding. If not, the plan widens the type and records it in `DECISIONS.md`.
- D13. Stateful incremental models live in the DuckDB file `out/warehouse.duckdb`. Published marts are external Parquet. Every incremental model must give the same result after a full refresh.

### Acceptance signals

- `make build` runs the batch part from raw files without manual steps.
- Two consecutive `make build` runs produce marts with identical content. Compare rows and hashes of the mart columns, not file bytes, because load metadata changes each run.
- `make stream DURATION=<n>` consumes the replay for `n` seconds and updates the stream tables.
- A consumer killed in the middle and restarted produces the same `fct_edit` row set as an uninterrupted run. No `meta.id` appears twice in `fct_edit`, and no event is missing.
- Each of the seven checks in the ticket returns a result. `oracle_map.yml` names the table or view for each one.
- Every dbt model has a documented grain. Every key has a dbt `unique` and `not_null` test. Mart contracts are enforced.
- The unit tests and `dbt build` pass.

## Quality-gate commands

Run these from the repository root. These are the real commands in this repository.

- `uv sync --locked --python 3.12`
- `uv run --python 3.12 python -m unittest discover -s pipeline/tests -p "test_*.py"`
- `uv run dbt parse --project-dir transform --profiles-dir transform`
- `uv run dbt build --project-dir transform --profiles-dir transform`
- `make build`
- `make stream DURATION=60`

Run dbt from the repository root. The `profiles.yml` path `out/warehouse.duckdb` resolves from the working directory. Check this in Phase 0.

## Phases

Each phase starts with failing tests where the phase has code. Each phase ends at its exit criteria. Do not start a phase before the previous exit criteria pass.

### Phase 0: Check contracts and record facts

Goal: check the library APIs and the source facts that the design uses. No pipeline code yet.

Work:

- Run `uv sync --locked --python 3.12`.
- Read the dlt 1.31.0 filesystem destination docs in the installed package. Find how to write Parquet, how to set `write_disposition` to `replace`, and how to control the file layout.
- Read the dbt-duckdb 1.11.0 docs in the installed package. Check the `external` materialization options (location, format), the incremental strategies (`delete+insert`, `merge`) and how `profiles.yml` relative paths resolve.
- Open the 8 USAspending zips with Python `zipfile`. Read the CSV header of each. Do not extract into the repository.
- Record these columns: the award identifier, the transaction identifier, the action date, the place-of-performance state and county, the awarding agency, and the obligation.
- Check that the transaction key is unique per file.
- Check that obligation values fit `DECIMAL(18,2)` with no sub-cent digits (D12).
- Read the 2024 and 2021 Census files. Check the summary level column, the FIPS columns, and that `POPESTIMATE2024` exists for each county row.
- Capture 200 events from the replay. Check `meta.id`, `meta.dt`, `timestamp`, `wiki`, `namespace`, `bot`, `type`, `server_name`, and `length.old`/`length.new`. Check that `meta.dt` matches `timestamp` (D9). Count the nulls in `length` (D10).
- Check that the replay honors the `Last-Event-ID` request header. Send the `id` of event 100 and check that the first event returned is event 101.
- Check that `cwd` controls the DuckDB path in `profiles.yml`.

Exit criteria:

- `DECISIONS.md` has a "Verified facts" section with each value above and its source.
- Any gap in D9, D10, D12 or the replay resume behavior is recorded and resolved in `DECISIONS.md` before Phase 1.

Notes: Facts only. Do not write pipeline code in this phase.

### Phase 1: Batch ingestion to the lake

Goal: land the three batch sources in `lake/` with dlt.

Work:

- Write `pipeline/batch.py`. Add one dlt resource per source table.
  - `usaspending_transactions`: read each CSV from its zip with `zipfile`. Keep source column names. Keep amounts and dates as source strings. Add `_source_file` and load metadata columns.
  - `census_county_population`: the 2024 and 2021 files. Keep only summary level 050 (D4).
  - `wiki_sites`: flatten `sitematrix.json` to one row per site (`dbname`, `code`, `url`, `sitename`, `closed`, language code).
- Use `write_disposition="replace"` for every batch resource. Append disposition duplicates rows on each run.
- Write each source to `lake/<table>/` as Parquet.
- Wire `make build` to run `uv run python -m pipeline.batch`. Use `uv run` with Python 3.12.

TDD:

- Write `pipeline/tests/test_batch.py` first. Test these items.
  - The row count per USAspending file equals the CSV data row count.
  - The county resource has no summary level other than 050.
  - Two runs write the same row set.
  - The flattened site rows include `aawiki` with URL `https://aa.wikipedia.org`.

Exit criteria:

- Unit tests pass.
- `lake/usaspending_transactions/`, `lake/census_county_population/` and `lake/wiki_sites/` exist.
- Row counts match the Phase 0 counts.

### Phase 2: dbt sources and staging

Goal: type the lake data in dbt with no business logic.

Work:

- Write `transform/models/sources.yml`. Read the lake Parquet files with `read_parquet` through the dbt-duckdb source definitions or a macro. Use the path from D13.
- Write staging models.
  - `stg_usaspending_transactions`: one row per transaction. Cast the obligation to `DECIMAL(18,2)`. Parse the action date. Keep the source transaction key.
  - `stg_census_county_population`: one row per county FIPS per vintage. Columns `county_fips`, `vintage_year`, `population`.
  - `stg_wiki_sites`: one row per wiki database name.
- Add `unique` and `not_null` tests on each key.
- Document the grain of each model in its `.yml` description.

Exit criteria:

- `uv run dbt build --project-dir transform --profiles-dir transform --select staging` passes.

### Phase 3: Star schema for Question A

Goal: build the fact and dimensions for awards.

Work:

- `dim_agency`: one row per awarding agency in the four toptier codes.
- `dim_place`: one row per state and county pair in the population file, plus the `UNKNOWN` member (D2). Carry the county population for the chosen 2024 value (D3). Add `population_source_year` and `is_population_fallback`.
- `dim_date`: one row per calendar day that FY2024 covers (2023-10-01 to 2024-09-30). Add `month_start`.
- `fct_award_transaction`: grain is one prime award transaction. Columns: transaction key, agency key, place key, date key, `obligation_amount` (DECIMAL), `is_negative_obligation`, and the award identifier from Phase 0.
- Apply the place rules (D1, D2) and the population rules (D3, D4) here.

TDD:

- Write dbt singular tests first for these rules.
  - Every transaction maps to one place key, including `UNKNOWN`.
  - Sum of `obligation_amount` in the fact equals the sum in staging.
  - The `UNKNOWN` member has a null population.
  - Each county with a fallback population sets `is_population_fallback = true`.

Exit criteria:

- `dbt build --select dim_agency dim_place dim_date fct_award_transaction` passes, with contracts enforced on the dimensions and the fact.
- Every fact key relates to a dimension row (`relationships` tests).

### Phase 4: Monthly mart for Question A

Goal: publish the monthly mart and the Question A checks.

Work:

- `mart_obligations_monthly`: grain is one month, one state, one county, one agency. Columns: `month_start`, `state_fips`, `county_fips`, `agency_code`, `net_obligations` (DECIMAL), `population`, `obligations_per_person` (D5).
- Materialize it with dbt-duckdb `external` into `out/marts/mart_obligations_monthly.parquet`.
- Add a model contract with column names and types.
- Write these check views in `transform/models/checks/`.
  - `chk_fy2024_obligations_by_agency` (check 1).
  - `chk_top10_counties_per_person` (check 2). Use counties with a known population only.
  - `chk_negative_award_count` (check 3). Count awards, not transactions, whose net obligation is negative.
  - `chk_month_reconciliation` (check 4). For one fixed month, sum counties by state, sum states, and compare with the source total from staging.
  - `chk_state_per_person` for the per-state per-person output (D5).

TDD:

- Write the reconciliation test first. It must fail when `UNKNOWN` is excluded and pass with it.

Exit criteria:

- The Parquet mart exists under `out/marts/`.
- The reconciliation view returns zero differences for the chosen month.

### Phase 5: Stream capture

Goal: consume the SSE stream with resume and land micro-batches.

Work:

- Write `pipeline/stream_consumer.py`.
  - Read the SSE format. Ignore lines that start with `:`. Read `id` and `data` fields. Join multi-line `data`.
  - On disconnect, reconnect with the `Last-Event-ID` header set to the last stored `id`. Back off between retries.
  - Stop after `DURATION` seconds. Finish the current micro-batch before exit.
- Land each micro-batch as one Parquet file in `lake/stream_recentchange/`. Each row keeps `meta_id`, `meta_dt`, `arrival_seq`, `wiki`, `server_name`, `namespace`, `bot`, `type`, `title`, `length_old`, `length_new`, and `_batch_id`.
- `arrival_seq` increases by one for each consumed event, in arrival order. Store it in the checkpoint.
- Store the checkpoint in `lake/_state/stream.json`: last `id`, last `arrival_seq`, last batch id.
- Commit order: write the batch file to a temporary name, rename it, then update the checkpoint. On start, delete any batch file whose id the checkpoint does not record.
- Use a lock file under `lake/_state/` to stop two consumers from running together.
- Wire `make stream` to run `uv run python -m pipeline.stream_consumer --duration $(DURATION)`, then run the stream models from Phase 6.

TDD:

- Write a local fake SSE server in `pipeline/tests/`. Use `http.server` in a thread. Do not use the replay for unit tests. The fake server must disconnect after N events, send `:ok` comments, and send duplicate ids on reconnect.
- Test these behaviors.
  - Reconnect sends the right `Last-Event-ID`.
  - A kill between the batch rename and the checkpoint write does not lose events. The restart delivers them again and no event is missing.
  - Non-consecutive `arrival_seq` values do not appear.

Exit criteria:

- Unit tests pass against the fake server.
- `make stream DURATION=20` runs against the replay at `localhost:8099` and writes batch files.

### Phase 6: Stream models for Question B

Goal: build the edit fact, late events and the 5-minute window mart.

Work:

- `stg_recentchange`: typed staging over `lake/stream_recentchange/`. Derive `event_time` from `meta_dt` (UTC) and `window_start = floor to 5 minutes`, `window_end = window_start + 5 minutes`.
- `stream_arrivals` (incremental, `unique_key` `meta_id`): one row per distinct event of any type. Columns `meta_id`, `arrival_seq`, `event_time`. This table holds the watermark source (D7).
- `fct_edit` (incremental, `unique_key` `meta_id`): one row per change event of type `edit` or `new` (D6). Keep the first arrival (D11). Compute `watermark_before` as the maximum `event_time` over arrivals with a smaller `arrival_seq`. Set `is_late = watermark_before > window_end + 10 minutes` (strict, D8). Columns include `wiki`, `namespace`, `is_bot`, `window_start`, `net_bytes` (D10), `is_late`.
- `late_events` (view over `fct_edit`): rows where `is_late = true`.
- `mart_edit_windows_5min` (incremental, `unique_key` on `window_start`, `wiki`, `namespace`, `is_bot`): counts on-time edits only. Re-aggregate every window touched by the new batch, because an on-time event can arrive after its window closed (D8). Publish with `external` into `out/marts/mart_edit_windows_5min.parquet`.
- Stream checks in `transform/models/checks/`.
  - `chk_stream_edits_by_wiki` (check 5). Edits and net bytes per wiki, split by human and bot, from `fct_edit`, late edits included.
  - `chk_top_windows_enwiki` (check 6). On-time edits on `en.wikipedia.org` (use `server_name`, or map `wiki` through `stg_wiki_sites`).
  - `chk_late_event_count` (check 7).
- `is_bot` is `coalesce(bot, false)`. Record the count of null `bot` values in `DECISIONS.md`.

TDD:

- Write a fixture of about 12 events with known event times and arrival order before any SQL.
- The fixture includes these cases.
  - An on-time event.
  - A late event at exactly 10 minutes.
  - A late event beyond 10 minutes.
  - A duplicate `meta_id`.
  - A non-edit event that raises the watermark.
- Write singular dbt tests that assert the expected `is_late` values and window counts for this fixture.
- Write a test that a full refresh of the incremental models equals the incremental result (D13).

Exit criteria:

- `dbt build --select stream` passes with the fixture tests.
- A full refresh gives the same `fct_edit` row set and the same window mart as the incremental run.

### Phase 7: Wire the two pipelines and prove idempotence

Goal: make `build` and `stream` safe to run repeatedly.

Work:

- `make build`: run the batch ingestion, `dbt build` for the batch models, and the batch mart publish. Do not touch `lake/stream_recentchange/`.
- `make stream DURATION=<n>`: run the consumer, then `dbt build --select stream`. Do not rebuild batch models.
- Write a repeatability check. Hash the mart columns (not load metadata) after each `make build`. The two hashes must match.
- Write a resume check. Run `make stream DURATION=20`, then `make stream DURATION=20` again. The second run must not add rows for events already in `fct_edit`.

Exit criteria:

- Two `make build` runs give equal mart hashes.
- Two `make stream` runs give no duplicate `meta_id` in `fct_edit`.

### Phase 8: Oracle map and decisions

Goal: finish the documentation the ticket requires.

Work:

- Write `oracle_map.yml` at the repository root. For each check 1 to 7, record the question, the table or view, the column or columns, and the test that covers it.
- Finish `DECISIONS.md`. Each entry has the decision, the chosen value, the reason, and the source. Include D1 to D13 and each fact from Phase 0 that changed a default.
- Record each county that uses a population fallback (D3).
- Record the count of null `bot` and null `length` values (D10, the `is_bot` rule).

Exit criteria:

- Every check in `oracle_map.yml` names a model that exists in `dbt ls`.
- `DECISIONS.md` covers every item in the ticket that left a choice open.

### Phase 9: Acceptance run

Goal: run the whole pipeline from a clean state and report the results.

Work:

- Delete `lake/` and `out/` from the working directory.
- Run `make build`, then `make build` again. Check the hashes match.
- Run `make stream DURATION=60` against the replay at `localhost:8099`.
- Kill a second consumer run in the middle. Restart it. Check that `fct_edit` has no duplicate `meta_id` and no gap in `arrival_seq`.
- Run the seven checks and record their results.
- Write `outputs/summary.md` with each pipeline stage and its result. Write `outputs/PR.md` with the PR title and body. Save both under the outputs directory from the task environment.

Exit criteria:

- All quality-gate commands pass.
- Each acceptance signal above has evidence in `outputs/summary.md`.

## Reuse and extension

- Existing helpers: the dbt project in `transform/` (`dbt_project.yml`, `profiles.yml`) and the pinned stack in `pyproject.toml`. The plan reuses both as they are.
- Extension point used: dlt resources in `pipeline/batch.py` and the stream consumer are the ingestion extension points. dbt model layers (staging, dimensions, facts, marts, checks) are the modelling extension points.
- Extension point added: `pipeline/` is a new Python package. Its first module is `batch.py`.

## Open risks

- The 2021 Census file may use different county codes from the 2024 file for some counties. Check in Phase 0. Record any mismatch in `DECISIONS.md`.
- The replay may send events faster than real time. Lateness must use event time only (D7, D8).
- An incremental window mart can drift from a full refresh if a late-arriving on-time event touches an old window. Phase 6 covers this with the full-refresh test.

## Footer

Next step: `/plan-review .cursor/plans/open-data-pipeline_gh-1.plan.md`.
Do not run `/plan-update` until a review file exists.

---

## Update 1 (2026-10-19): applies plan review cycle 1

RUN_BY_COMMAND: plan-update

Review applied: `.context/reviews/plan_open-data-pipeline_gh-1.md` (Verdict: READY WITH CHANGES, cycle 1).
This section adds the contracts for the six must-fix items. Where it conflicts with the text above, this section wins.
The text above is kept unchanged.

### MF-1 (Phase 5): `make stream` wiring

- Phase 5 wires `make stream` to run the consumer only:
  `uv run python -m pipeline.stream_consumer --duration $(DURATION)`.
- The stream dbt step is not in Phase 5. Phase 7 adds it: `make stream` runs the consumer, then `dbt build --select stream`.
- Phase 5 exit `make stream DURATION=20` passes with the consumer step only.

### MF-2 (Phase 5, 7, 9): lock release

- The stream lock is an OS advisory lock: `fcntl.flock` on `lake/_state/stream.lock`, held for the consumer process lifetime.
- The kernel releases the lock when the process exits, including after a kill. A leftover lock file does not block a restart.
- The consumer acquires the lock with a non-blocking call. If it fails, the consumer exits with a message that names the lock file.
- Test (Phase 5 TDD): create a lock file with no holder, start the consumer, and check that it runs. Add a test that a kill during a run leaves no lock held.

### MF-3 (Phase 6, D8): `late_events` is a table

- `late_events` is a materialized table (dbt `table` materialization), not a view.
- It is built from `fct_edit` in the same stream run, after `fct_edit`, with the filter `is_late = true`.
- A full refresh rebuilds it from `fct_edit`. It is therefore always in step with `fct_edit` after each stream run.
- D8 reads: a late edit is kept in `fct_edit` with `is_late = true`, and copied to the `late_events` table. The window mart counts only on-time edits.

### MF-4 (Phase 6, D11): incremental first-arrival rule

- For `stream_arrivals` and `fct_edit`, each incremental run selects only `meta_id` values not already in the target table:
  `{% if is_incremental() %} where meta_id not in (select meta_id from {{ this }}) {% endif %}`.
- An existing row is never rewritten. The first arrival stays.
- `watermark_before` reads the full `stream_arrivals` table, not only the new batch. Earlier arrivals still count for lateness.
- Fixture (Phase 6 TDD) adds this case: a `meta_id` arrives in batch 1 and again in batch 2. The test asserts that the batch 1 row is kept, with its original `arrival_seq`, `is_late` and window counts.

### MF-5 (Phase 3, D2, D3): place codes and missing populations

- Place code rule: a transaction whose state or county code has no `dim_place` row maps to the `UNKNOWN` member. This covers absent codes, foreign codes and codes absent from both population files.
- `dim_place` rows come from the county rows of the 2024 and 2021 population files (summary level 050 only, D4).
- Population fallback chain for a county: `POPESTIMATE2024`, then `POPESTIMATE2023`, `POPESTIMATE2022` (2024 file), then `POPESTIMATE2021` (2021 file). `POPESTIMATE2020` and `ESTIMATESBASE2020` are never used (D3).
- A county with no allowed estimate has `population = null`, `population_source_year = null` and `is_population_fallback = true`.
- `is_population_fallback` is true when `population_source_year` is not 2024, or when `population` is null.
- Per-person values (D5) are null when population is null. Check 2 uses known populations only (already stated).
- State per person (D5) uses only counties with a known population, in both the numerator and the denominator.
- Check 4 reconciles with `UNKNOWN` included. The Phase 3 test for `UNKNOWN` (null population) still applies.
- Test (Phase 3 TDD): a transaction with a valid state code and a county code absent from both population files maps to `UNKNOWN`. The reconciliation returns zero difference with `UNKNOWN` included.

### MF-6 (Phase 5 TDD): fault seam

- The commit function takes an optional hook: `fault_hook: Callable[[str], None] | None = None`.
- The commit function calls `fault_hook("after_rename")` after the batch rename and before the checkpoint write. It calls no other hook.
- The test "a kill between the batch rename and the checkpoint write does not lose events" passes a hook that raises at `"after_rename"`. The test then restarts the consumer with no hook. The restart delivers the events again, and no event is missing.
- The test is deterministic because the raise happens at a named point, not at a timing point.

### Notes not applied

- The non-blocking notes in the review (replay rate in Phase 0, commit per phase exit, rollback line in Step 0, absolute outputs path, fixture route, `arrival_seq` on reconnect duplicates, `dbt parse` in Phase 2) are not in this update.
  The next plan review can raise them again.

---

## Update 2 (2026-10-19): applies plan review cycle 2

RUN_BY_COMMAND: plan-update

Review applied: `.context/reviews/plan_open-data-pipeline_gh-1.md` (Verdict: READY WITH CHANGES, cycle 2).
This section adds the contracts for the two new must-fix items, MF-7 and MF-8. Where it conflicts with the text above or Update 1, this section wins.
The text above and Update 1 are kept unchanged.

### MF-7 (Phase 6, and the grain and key rules in the acceptance signals): grains, key tests, contract

Scope. Every dbt model and check view under `transform/models/` must have a grain line in its `.yml` description. This covers the batch models from Phases 2 to 4 and the stream models from Phase 6. Phase 2 requires the grain for staging only. This rule extends it to all layers.

Grain lines for the stream models:

- `stg_recentchange`: one row per landed stream event, as stored in `lake/stream_recentchange/`. Duplicates are kept.
- `stream_arrivals`: one row per distinct `meta_id`.
- `fct_edit`: one row per `meta_id` of type `edit` or `new`, first arrival only (D6, D11).
- `late_events`: one row per `fct_edit` row with `is_late = true`.
- `mart_edit_windows_5min`: one row per `window_start`, `wiki`, `namespace`, `is_bot`.

Key tests for the stream models (Phase 6):

- `stream_arrivals`: `unique` and `not_null` on `meta_id`.
- `fct_edit`: `unique` and `not_null` on `meta_id`.
- `late_events`: `unique` and `not_null` on `meta_id`. Add a `relationships` test from `late_events.meta_id` to `fct_edit.meta_id`.
- `mart_edit_windows_5min`: `not_null` on each of `window_start`, `wiki`, `namespace`, `is_bot`. dbt has no native composite `unique` test, and this plan adds no package (see Non-goals). Add a singular test in `transform/tests/` that groups by the four key columns and fails on any group with a count above 1.

Model contract (Phase 6):

- `mart_edit_windows_5min` has a model contract. The contract lists every column with its type: `window_start` (TIMESTAMP), `window_end` (TIMESTAMP), `wiki` (VARCHAR), `namespace` (INTEGER), `is_bot` (BOOLEAN), `edits_ontime` (BIGINT), `net_bytes` (BIGINT).
- The contract is enforced. A `dbt build --select stream` run fails if the output shape changes.

Key tests for the batch models (Phases 2 to 4). These apply the same acceptance rule to the batch keys:

- `dim_agency`, `dim_place`, `dim_date`: `unique` and `not_null` on the surrogate key of each.
- `fct_award_transaction`: `unique` and `not_null` on the transaction key from Phase 0.
- `mart_obligations_monthly`: `not_null` on each of `month_start`, `state_fips`, `county_fips`, `agency_code`. Add a singular test that fails on any duplicate of these four columns, as for the window mart.

Test (Phase 6 TDD): write a singular test that reads `mart_edit_windows_5min` and fails if any key column is null or any key group has a count above 1. Write it before the mart SQL. It must fail on a deliberately duplicated fixture row, then pass on the correct build.

### MF-8 (Phase 9, acceptance signal 4; Phase 5 test list): restart equals uninterrupted

The check compares row sets over a common prefix. It does not compare total counts. A run with `DURATION=60` consumes a different number of events in each run, so counts differ.

Phase 0 addition (gate for the Phase 9 check):

- Check that the replay is deterministic. Open two fresh connections with no `Last-Event-ID`. Read the first 200 event ids from each. Record whether both lists are identical and in the same order.
- If the lists are identical, the Phase 9 replay comparison below runs as written.
- If the lists differ, record the fact in `DECISIONS.md`. The Phase 9 replay comparison is then not a valid proof. The proof is the Phase 5 fake-server test below. Phase 9 still runs the replay comparison, and records its result as a smoke check only.

Phase 5 TDD addition (deterministic proof):

- The fake SSE server sends a fixed list of 30 events with known `id` values, then closes the stream after the last event.
- Run A: consume all 30 events with no fault. Record the `meta_id` values of the final `fct_edit` table ordered by `arrival_seq`. Call this list R.
- Run B: start with a clean lake and state. Pass a `fault_hook` that raises at `"after_rename"` after the 12th batch. Restart with no hook. Consume to the end of the fake list. Record the same list. Call this list K.
- Assert: K has no duplicate `meta_id`. The `arrival_seq` values of K are contiguous from 1 to N. Over the common prefix, the set of `meta_id` values in K equals the set in R.

Phase 9 work list (replay check, after Phase 0 passes the determinism check):

1. Delete `lake/stream_recentchange/`, `lake/_state/` and the stream tables in `out/warehouse.duckdb`, or run `dbt build --select stream --full-refresh` after the delete.
2. Run `make stream DURATION=60` to completion. Save the `meta_id` list of `fct_edit` ordered by `arrival_seq` to the scratch directory of the run. Call this list R.
3. Repeat step 1. Start `make stream DURATION=60`. Send SIGKILL to the consumer process after about 20 seconds. Restart `make stream DURATION=60` to completion. Save the same list. Call this list K.
4. Let m be the smaller of the lengths of R and K. Assert all of the following:
   - K has no duplicate `meta_id`.
   - K has no gap in `arrival_seq` from 1 to m.
   - The set of `meta_id` values in K with `arrival_seq` at most m equals the set in R with `arrival_seq` at most m.
5. Record m, the lengths of R and K, and the result of each assert in `outputs/summary.md`.

Notes on this check:

- The check uses the `arrival_seq` values from the checkpoint, not wall-clock time. A restart continues the sequence (Phase 5).
- The kill in step 3 is an external SIGKILL. The deterministic kill point is the Phase 5 seam. Phase 9 does not need it.

## Notes not applied

- The non-blocking notes in the cycle 2 review are not in this update. The cycle 1 notes that remain open are also not in this update. The next plan review can raise them again.

---

## Update 3 (2026-10-19): applies plan review cycle 3

RUN_BY_COMMAND: plan-update

Review applied: `.context/reviews/plan_open-data-pipeline_gh-1.md` (Verdict: READY WITH CHANGES, cycle 3).
This section adds the contracts for the three new must-fix items, MF-9, MF-10 and MF-11.
Where it conflicts with the text above or with Update 1 or Update 2, this section wins.
The text above and Updates 1 and 2 are kept unchanged.

### MF-9 (Phase 6, D13): two objects for the window mart

The name `mart_edit_windows_5min` names one published object. The incremental state is a separate object.

- `edit_windows_5min_state`: incremental model with `unique_key` on `window_start`, `wiki`, `namespace` and `is_bot`. It is a table in `out/warehouse.duckdb` (D13). It counts on-time edits, with the re-aggregation rule from Phase 6. Its `.yml` description states its grain (MF-7).
- `mart_edit_windows_5min`: published mart. It selects all rows from `edit_windows_5min_state`. It is materialized with dbt-duckdb `external` into `out/marts/mart_edit_windows_5min.parquet`.

Rules for the two objects:

- The model contract (MF-7) applies to `mart_edit_windows_5min` only.
- The key tests (`not_null` on the four key columns) and the singular duplicate test (MF-7) apply to `mart_edit_windows_5min` only.
- The duplicate-fixture test (Phase 6 TDD, MF-7) reads `mart_edit_windows_5min`.
- The D13 full-refresh test compares `mart_edit_windows_5min` after an incremental run with `mart_edit_windows_5min` after `dbt build --select stream --full-refresh`. The two row sets must be equal.
- The Phase 0 library check also records whether the `external` materialization enforces a model contract. Record the result in `DECISIONS.md` before Phase 6.
- Phase 9 step 1 also deletes `edit_windows_5min_state` from `out/warehouse.duckdb`.
- Phase 7 repeatability hashes use `mart_edit_windows_5min`.

### MF-10 (Phase 5 work list, Phase 5 TDD, MF-6 seam, MF-8 proof): micro-batch rule

Phase 5 work list, added rule:

- A micro-batch closes after `batch_size` events. `batch_size` is a parameter of the consumer. Its default is 500.
- There is no time-based flush.
- A partial batch closes when the consumer stops, at the end of `DURATION` or when the stream closes.

Phase 5 TDD, MF-8 proof, with this rule:

- The test sets `batch_size=2`.
- Run A consumes the 30 events with no fault. Run A writes 15 batches.
- Run B passes a fault hook. The hook receives only the point name, so the test counts its calls. The test raises on the 12th call to `"after_rename"`.
- Batch 12 holds events 23 and 24. Its file is renamed, but the checkpoint still records batch 11 (events 1 to 22).
- The restart resumes after event 22. The restart deletes the unrecorded batch 12 file and writes batches 12 to 15 again.
- The test asserts 15 batches for Run A and the batch numbers and event ranges above for Run B.

### MF-11 (Phase 9, work list step 4, Update 2 MF-8): branch on the Phase 0 result

This section replaces the heading condition of the Phase 9 work list in Update 2, and the sentence "Assert all of the following" in its step 4. Phase 9 always runs the work list. The Phase 0 determinism result, recorded in `DECISIONS.md`, sets the status of step 4.

- If Phase 0 found identical lists, the step 4 asserts are hard gates. A failed assert fails Phase 9.
- If Phase 0 found different lists, the step 4 asserts are a smoke check. Record each assert result in `outputs/summary.md`. A failed assert does not fail Phase 9. The Phase 5 fake-server test is the proof of acceptance signal 4.
- In both cases, `outputs/summary.md` states the Phase 0 result and the branch taken.

## Notes not applied

- The non-blocking notes in the cycle 3 review are not in this update.
- The cycle 1 and cycle 2 notes that remain open are not in this update.
- The next plan review can raise them again.

---

## Update 4 (2026-10-19): applies plan review cycle 4

RUN_BY_COMMAND: plan-update

Review applied: `.context/reviews/plan_open-data-pipeline_gh-1.md` (Verdict: READY WITH CHANGES, cycle 4).
This section adds the contracts for the two new must-fix items, MF-12 and MF-13.
Where it conflicts with the text above or with Updates 1, 2 and 3, this section wins.
The text above and Updates 1 to 3 are kept unchanged.

### MF-12 (Phase 5 TDD, MF-8 proof; Phase 9): the Phase 5 proof reads lake files, not `fct_edit`

Phase 5 has no dbt run. `fct_edit` does not exist when Phase 5 runs. The Update 2 proof is replaced as follows.

- Run A and Run B build their lists from the lake batch files under `lake/stream_recentchange/`, not from `fct_edit`.
- Read the batch files in `_batch_id` order. Each row gives `meta_id` and `arrival_seq`.
- Assert on all rows read from the batch files, before any dedupe: no `meta_id` appears twice (K has no duplicate `meta_id`), and the `arrival_seq` values run contiguously from 1 to N.
- Build the list from the rows, keeping the first arrival of each `meta_id` (D11). Order the kept rows by `arrival_seq`. Call this list R for Run A and K for Run B.
- Assert that the set of `meta_id` values in K equals the set in R over their common prefix.
- The `fct_edit` comparison is not part of Phase 5. It runs in Phase 9 (Update 2 work list, steps 2 and 4), where `fct_edit` exists.

### MF-13 (Phase 5 work list, Phase 5 TDD, MF-10 and MF-8 proof): resume and drop rule

Phase 5 work list, added rule:

- The consumer drops an event when its `id` is at or before the `id` in the checkpoint (`lake/_state/stream.json`). A dropped event gets no `arrival_seq`, is not written to any batch, and does not count toward `batch_size` (MF-10).
- The checkpoint stores the last `id` only. The "at or before" test is the total order of `id` values. Phase 0 records that order for the replay ids (the replay `id` values are JSON arrays). Phase 0 exit fails until `DECISIONS.md` states the order, or states a fallback rule. The Phase 5 fixture uses integer ids 1 to 30, so its order is numeric.

Phase 5 TDD, changes to the fake SSE server and the tests:

- The fake SSE server honors `Last-Event-ID`. On reconnect it sends only the events after the event with that `id`.
- The fake server has a second mode for the duplicate test. In this mode it also resends events 1 to 5 on reconnect, after the resume.
- The Run B restart receives events 23 to 30 only, because the checkpoint holds event 22. Under MF-10 the restart writes batches 12 to 15. Batch 12 holds events 23 and 24, batch 13 holds 25 and 26, batch 14 holds 27 and 28, and batch 15 holds 29 and 30. The test asserts exactly these four batches and their event ranges.
- The duplicate test is separate from the Run B test. In duplicate mode, the fake resends events 1 to 5 after the reconnect. The test asserts that all five are dropped: no lake row, no change to the batch count, and no change to the `arrival_seq` sequence.
- The MF-8 proof in Update 2 and Update 3 keeps its other rules: Run A writes 15 batches, and the fault hook raises on the 12th call to `"after_rename"`.

### Notes not applied

- The non-blocking notes in the cycle 4 review are not in this update.
- The cycle 1 to cycle 3 notes that remain open are not in this update.
- The next plan review can raise them again.

---

## Update 5 (2026-10-19): applies plan review cycle 5 (cycle limit)

RUN_BY_COMMAND: plan-update

Review applied: `.context/reviews/plan_open-data-pipeline_gh-1.md` (Verdict: READY WITH CHANGES, cycle 5, the cycle limit).
This section adds the contracts for the two must-fix items, MF-14 and MF-15.
Where it conflicts with the text above or with Updates 1 to 4, this section wins.
The text above and Updates 1 to 4 are kept unchanged.
This is the last plan update. No further plan review runs. The open ids are listed under `## Carried review findings`.

### MF-14 (Phase 5 work list, Phase 5 TDD, MF-10 and MF-12 proof): one stop rule

Phase 5 work list, added rule. The consumer takes one optional argument, `duration` (seconds, or `None`).

- When the stream closes, the consumer checks the next connection. The fake server answers any reconnect after its list is done with HTTP 204. A 204 response ends the run. The consumer does not reconnect after a 204. This follows the SSE rule that a 204 response stops reconnects.
- Any other close or connection error starts a reconnect with backoff.
- With `duration=None`, the run ends only on a 204 response. The run then closes the partial batch and exits.
- With `duration` set, the run reconnects until `duration` seconds pass. It then closes the partial batch and exits. A 204 response also ends the run early.
- Production `make stream DURATION=<n>` passes `duration=n`.

Phase 5 TDD, arguments for each test run:

- Run A: `duration=None`, `batch_size=2`, fake mode normal. The fake sends events 1 to 30, closes, and then answers the reconnect with 204. The run ends after batch 15.
- Run B, first part: `duration=None`, `batch_size=2`, fake mode normal, with the fault hook. The hook raises on the 12th call to `"after_rename"`. The run ends with the exception.
- Run B, restart: `duration=None`, `batch_size=2`, fake mode normal, no hook. The fake sends events 23 to 30 (the checkpoint holds event 22), then answers 204. The run ends after batch 15.
- The test for MF-10 partial batches uses the same rule. With `duration=None`, a partial batch closes only on the 204 end.

### MF-15 (Phase 5 TDD, duplicate test, MF-13): disconnect point for duplicate mode

- In duplicate mode the fake server disconnects after event 10. The first connection sends events 1 to 10, then closes.
- The reconnect sends `Last-Event-ID: 10`. The fake sends events 11 to 30. Then it resends events 1 to 5. Then it closes.
- The next reconnect gets 204. The run ends.
- The fake server keeps a counter of reconnects that receive events. The 204 response is not counted. The test asserts that the counter is 1. This proves that the disconnect and the resend happened.
- The test asserts the MF-13 result for the resend: the five resent events are dropped. The lake has 30 unique `meta_id` rows, the batch count is 15, and the `arrival_seq` values run from 1 to 30 with no gap.

## Carried review findings

The cycle limit is reached. The gate checks these ids. Each id names the phase whose test settles it.

- MF-14: Phase 5. Settled by the Run A and Run B tests above. Those tests pass only when the stop rule runs as written, with no hang.
- MF-15: Phase 5. Settled by the duplicate test above. The test passes only when the reconnect count is 1 and the five resent events are dropped.

### Notes not applied

- The non-blocking notes in the cycle 5 review are not in this update. They are the check-view grains, the mart contract fallback, rollback, commit checkpoints, the Phase 6 fixture route, the dbt selector, the Phase 7 check locations, the replay rate, the `arrival_seq` on reconnect duplicates, the older text under the updates, check 4, the outputs path, and the Phase 4 month.
- E1 decides these items in `DECISIONS.md` where a choice is needed.
