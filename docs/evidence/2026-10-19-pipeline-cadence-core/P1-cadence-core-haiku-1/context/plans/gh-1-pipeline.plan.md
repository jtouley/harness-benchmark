# Plan: gh-1 open data pipeline

RUN_BY_COMMAND: plan-create

**Task:** gh-1
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
**Local ticket:** `.context/issues/gh-1.md`
**Branch:** `feature/gh-1-pipeline`

## Status

Plan only. Nothing is implemented. Next step: `/plan-review .context/plans/gh-1-pipeline.plan.md`.

## Step 0: problem restated

The repo has a skeleton. `make build` and `make stream` are stubs that exit 1. The `transform/` project has no models. The `data/raw/` inputs are present. The pipeline must build two answers from raw files and a stream:

- Question A (batch): FY2024 federal contract and grant money, in total and per resident, by state, county, agency and month.
- Question B (stream): Wikipedia edits per wiki, namespace and 5-minute window, split by human and bot, with net bytes added.

The path is: raw files, then a Parquet lake (dlt), then dbt-duckdb models, then Parquet marts under `out/marts/`.

## Design decisions

These decisions follow the ticket. Each open choice also goes to `DECISIONS.md` in Phase 9.

1. **Money.** Store amounts as `DECIMAL(18,2)`. Sum with SQL `SUM` on decimals. Never cast to `DOUBLE` before a sum.
2. **Per person.** Use the July 1, 2024 estimate (Amendment A). Compute `obligations_per_person` as a decimal division at the mart level only. Keep the sums exact.
3. **Place.** Use the place of performance (state and county FIPS). The ticket asks "where money went", so the award's place of performance is the best fit. Recipient location is not used.
4. **Missing county.** Transactions with no county go to an explicit "unknown county" row in `dim_place`. This keeps county sums equal to state sums and state sums equal to the source total (check 4).
5. **Award-level counts.** The fact grain is one transaction. Check 3 counts awards, so it runs on a view at the award grain.
6. **Population fallback.** When a county has no 2024 estimate, use the latest earlier estimate. Record the year used in a `population_year` column so the fallback is visible.
7. **Edit scope.** Count `type` in (`edit`, `new`). Exclude `log` and `categorize`. Record this in `DECISIONS.md`.
8. **Null lengths.** Treat a null `length.old` or `length.new` as 0 when it computes net bytes. Record this in `DECISIONS.md`.
9. **Event time.** Use the `timestamp` field (Unix seconds). Windows are `floor(ts / 300) * 300` in UTC.
10. **Late rule in SQL.** Event `e` is late when `W_before(e) > window_end(e) + 600`. `W_before(e)` is the maximum event time over all earlier first arrivals. This includes late events. The rule runs in dbt, not in the consumer.
11. **Fact and late table split.** `fct_edit` holds on-time first arrivals only. `late_events` holds late first arrivals only. Check 5 unions both tables.
12. **Dedupe.** The key is the event `meta.id`. Replays after a reconnect add no new rows.
13. **Arrival order.** The consumer adds one load-metadata column, `arrival_seq`. It is monotonic across restarts. It is stored in the lake next to the raw events. `W_before` depends on it.

## Blast radius

- New code: `pipeline/` (Python: ingestion, stream consumer, publish helpers), `transform/models/` (dbt), `transform/macros/` (shared SQL), `tests/` (Python tests and dbt singular tests), `oracle_map.yml`, `DECISIONS.md`.
- Changed files: `Makefile` (replace the two stubs), `transform/dbt_project.yml` (add model paths and config), `.gitignore` only if a new generated path appears.
- Not changed: `pyproject.toml` pins and `uv.lock`. The ticket says do not change the pinned versions. Test tooling runs with `uv run --with pytest`, so no new dependency is added.
- Generated, never committed: `lake/`, `out/`, `transform/target/`. `.gitignore` already lists them.

## Acceptance

- `make build` runs the batch path from the raw files. A second run produces the same marts.
- `make stream DURATION=<seconds>` consumes the stream for that time and updates the stream tables. Stop and restart does not double count or lose an event.
- All seven checks in the ticket return a result from the published marts or the oracle views.
- Every model has a documented grain. Every model key has a dbt `unique` and `not_null` test.
- Mart contracts are enforced for column names and types, or the gap is recorded in `DECISIONS.md` (see Risk R1).

## Quality-gate commands

Use only commands that exist in this repo.

- Environment: `uv sync` (Python 3.12, from `.python-version`).
- dbt parse: `uv run dbt parse --project-dir transform --profiles-dir transform`
- dbt build: `uv run dbt build --project-dir transform --profiles-dir transform`
- Python tests: `uv run --with pytest pytest tests/`
- Batch: `make build`, then `make build` again, then compare the published marts with `sha256sum` of a sorted content dump (see Phase 5).
- Stream: `make stream DURATION=60` against the replay at `http://localhost:8099/v2/stream/recentchange` when it is reachable. Otherwise run it against the local test server from Phase 6.
- Text: `python3 $CADENCE_HOME/skills/asd-ste100/scripts/ste-lint.py <file>` on `DECISIONS.md` and on `PR.md`. Fix each hard violation.

`make build` and `make stream` are the only Makefile targets. The Makefile has no other targets to call.

## Phases

### Phase 1: Environment and source checks

Work:

- Run `uv sync`. Check that `dlt`, `dbt-core`, `dbt-duckdb` and `duckdb` import on Python 3.12.
- Run `dbt debug` with the repo profile. Check that the DuckDB path `out/warehouse.duckdb` resolves from the repo root.
- Read the header of one CSV from each USAspending zip (eight zips, one CSV each). Record the column names for: transaction id, action date, federal action obligation, awarding agency code and name, place of performance state code and county FIPS.
- Read the Census 2024 file. Check the state and county key columns, the `SUMLEV` filter for county rows, and which counties lack `POPESTIMATE2024`.
- Read `data/raw/sitematrix.json` keys. Check that the `dbname` field maps a wiki id to a project.
- If `localhost:8099` answers, capture 20 lines of the SSE stream. Check the `event:` and `id:` fields and the `timestamp`, `meta.id`, `server_name`, `namespace`, `type`, `bot` and `length` fields.

Exit criteria:

- `uv sync` and `dbt debug` pass.
- `DECISIONS.md` has a "source findings" section with the column names and the missing-county list.
- The replay check result is recorded: reachable, or not reachable with the reason.

TDD notes: No code in this phase. Each finding is a stated fact with its source (file and line or the command output).

### Phase 2: Batch ingestion to the lake

Work:

- Create `pipeline/` with one entry module for the batch path, for example `pipeline/batch.py`.
- Add one dlt resource function that reads a CSV from a zip and yields rows. Use it for the contracts and the assistance files. Pass the file type as a parameter. Do not write two loaders.
- Add one resource function for the Census county file (both vintages). Filter `SUMLEV = 50` (county rows).
- Add one resource function for the site matrix.
- Use the dlt filesystem destination with Parquet files under `lake/`. One folder per source table.
- Use `write_disposition="replace"` for batch sources. Each `make build` replaces the lake folder, so a second run does not add rows.
- Keep only dlt load metadata columns beyond the source columns.
- Add the `build` target to the Makefile for this step. It calls `uv run python -m pipeline.batch`.

Exit criteria:

- `make build` writes `lake/` folders for USAspending contracts, USAspending assistance, census county population (both vintages) and the site matrix.
- The row count of each lake table equals the row count of its source CSV (counted with `wc -l` minus header, or with a Python `csv` reader).
- Test: a pytest test for the zip reader on a small generated zip in `tests/` reads all rows and keeps the header-based field names.

TDD notes: Write the row-count test first against a 3-row fixture zip. Then write the reader.

### Phase 3: dbt project and staging models

Work:

- Declare the lake folders as dbt sources in `transform/models/sources.yml`. Use the dbt-duckdb external location setting for each source.
- Add `transform/models/staging/` models: `stg_usaspending_transactions` (union of the contract and assistance files, one common column set, typed amounts as `DECIMAL(18,2)`), `stg_census_county_population`, `stg_sitematrix_wikis`.
- Add a `transform/macros/` file for shared SQL (for example the FIPS code padding and the amount cast). Use it from every staging model that needs it.
- Add `unique` and `not_null` tests on each staging key in `schema.yml`.
- Document the grain of each model in its description.

Exit criteria:

- `uv run dbt build --project-dir transform --profiles-dir transform --select staging` passes.
- Staging row counts equal the lake row counts.
- The amount column has no floating-point type.

TDD notes: Add a singular test that asserts zero rows where the amount is not a decimal. Run it before writing the cast.

### Phase 4: Question A star schema

Work:

- Build `fct_award_transaction` at the grain of one award transaction. Key: the transaction id from the source. Keep the agency, place and action-date foreign keys.
- Build `dim_agency` (toptier code, name), from the source columns.
- Build `dim_place` (state, county FIPS, state name, county name). Add the "unknown county" row (Decision 4) and an "unknown state" row for transactions with no place.
- Build `dim_date` (day grain, with fiscal year and calendar month). Cover FY2024 only.
- Add a dbt model contract on each mart-facing model (column names and types enforced).
- Add key tests: `unique` and `not_null` on each primary key. Add `relationships` tests from the fact to each dimension.

Exit criteria:

- `dbt build --select fct_award_transaction+ dim_*` passes.
- A singular test shows that the sum of `fct_award_transaction` amounts equals the sum of `stg_usaspending_transactions` amounts, with no rows lost to the joins.

TDD notes: Write the singular test for "no row lost to the joins" first. It must fail on a join that drops the unknown rows.

### Phase 5: Question A marts, oracle views and publish

Work:

- Build `dim_population_county_2024`: one row per county. Use `POPESTIMATE2024`. When it is missing, use the latest earlier estimate and set `population_year`. Use the Phase 1 list to test the fallback.
- Build `mart_obligations_monthly` at the grain of one month, state, county and agency. Columns: `month`, `state_code`, `county_fips`, `agency_code`, `net_obligations` (decimal sum), `population`, `population_year`, `obligations_per_person` (decimal division, scale 2).
- Build the oracle views for checks 1 to 4:
  - Check 1: `v_fy2024_obligations_by_agency`.
  - Check 2: `v_fy2024_top10_counties_per_person`.
  - Check 3: `v_fy2024_award_net` (grain: one award) and its count of awards with a negative net.
  - Check 4: a singular test and a view `v_month_reconciliation` that shows county totals, state totals and the source total for each month.
- Publish the marts with the dbt-duckdb `external` materialization under `out/marts/<mart_name>/`. One folder per mart.
- Add the publish step to `make build` after `dbt build`.

Exit criteria:

- `make build` completes. Each mart folder exists under `out/marts/`.
- Check 4 passes for every month (the singular test returns zero failing rows).
- Idempotence: run `make build` twice. Compare a sorted content dump of each mart (for example `duckdb -c "select * from read_parquet(...) order by all"` piped to `sha256sum`). The hashes match. Raw file hashes are not compared, because Parquet metadata can differ between runs.
- The oracle views return values for checks 1, 2 and 3.

TDD notes: Write the reconciliation test first. Then build the mart.

### Phase 6: Stream consumer and lake landing

Work:

- Add `pipeline/stream.py`. It opens the Server-Sent Events stream at the URL from an environment variable, with `http://localhost:8099/v2/stream/recentchange` as the default.
- Parse each `data:` line as JSON. Keep the `id:` line for resume.
- Reconnect after a drop. Send the last seen `id` in the `Last-Event-ID` header.
- Assign each event an `arrival_seq` from a counter. Store the counter in the pipeline state so it continues after a restart.
- Write micro-batches to the lake with dlt (Parquet, append disposition). Commit the cursor (last `id` and last `arrival_seq`) only after the batch file is written.
- Run for `DURATION` seconds, then stop cleanly. Flush the last batch on stop.
- Add the `stream` target to the Makefile: `make stream DURATION=<seconds>` runs the consumer for that time, then runs `dbt build` for the stream models.
- Add a local test server in `tests/` that replays a fixed list of events. It can close the connection after N events and it can repeat events after a reconnect.

Exit criteria:

- Test: a run stops after 30 events and restarts. The lake then holds 60 rows with no duplicate `meta.id`, even when the replay sends overlap.
- Test: a forced disconnect in the middle of a batch does not lose events.
- `make stream DURATION=60` runs against the replay, if reachable, or the local test server.

TDD notes: Write the stop-and-restart test first, against the local test server. It fails until the cursor commit works.

### Phase 7: Stream models

Work:

- Build `stg_recentchange` (incremental, view over the lake). Keep `event_id = meta.id`, `event_ts`, `wiki = server_name`, `namespace`, `actor_type` (`bot` when `bot` is true, else `human`), `type`, `old_length`, `new_length`.
- Build `first_arrivals` (incremental). Keep the earliest `arrival_seq` per `event_id`. Drop all later rows with the same id.
- Build `watermark` logic in one macro. The macro computes `W_before` with a window: the maximum `event_ts` over earlier `arrival_seq`, plus the prior maximum stored in the existing `fct_edit` and `late_events` tables.
- Build `late_events` (incremental): rows where `W_before > window_end + 600`. Keep the same columns as the edit fact, plus `W_before`.
- Build `fct_edit` (incremental): rows that are not late. Grain: one change event. Keep `event_id` as the unique key. Add the `is_bot` and `net_bytes` columns.
- Build `mart_edit_windows_5min` (incremental): grain is one 5-minute window, wiki, namespace and actor type. Columns: `window_start`, `window_end`, `wiki`, `namespace`, `actor_type`, `edit_count`, `net_bytes_added`. Only rows from `fct_edit`.
- Publish the window mart under `out/marts/`. If the dbt-duckdb external materialization does not support the incremental model, use a post-hook `COPY` to Parquet and record it in `DECISIONS.md` (see Risk R2).
- Add `unique` and `not_null` tests. Apply them to `event_id` on `fct_edit` and `late_events`. Apply them to the composite key on the window mart.

Exit criteria:

- `dbt build --select stream` passes on the replayed events.
- A test shows no event id is in both `fct_edit` and `late_events`.
- A test shows `mart_edit_windows_5min` equals a direct `GROUP BY` over `fct_edit`.
- Running the stream models twice on the same lake leaves the tables unchanged.

TDD notes: Write the late-rule test first, with a 4-event fixture. It covers an event exactly at the 10-minute boundary (not late) and one just past it (late).

### Phase 8: Stream checks and resume verification

Work:

- Add oracle views for checks 5 to 7:
  - Check 5: `v_stream_by_wiki_actor` over the union of `fct_edit` and `late_events`. Counts and net bytes per wiki, split human and bot.
  - Check 6: `v_top_windows_en_wikipedia` over `fct_edit` only, filtered on `wiki = 'en.wikipedia.org'`.
  - Check 7: `v_late_event_count`, the count of rows in `late_events`.
- Add a singular test that check 5 totals equal the total of consumed first arrivals (count of distinct `event_id` in the lake).
- Run the full stream path twice with a stop in between on the replay. Compare the check 5 totals with a single uninterrupted run.

Exit criteria:

- Checks 5, 6 and 7 return rows.
- The total for check 5 after the interrupted run equals the uninterrupted run.

TDD notes: The interrupted-versus-uninterrupted test is the acceptance test for the stream. Write it before Phase 8 work begins.

### Phase 9: Documentation and handoff files

Work:

- Write `oracle_map.yml`. For each of the seven checks: the check name, the table or view, and the column that answers it.
- Write `DECISIONS.md`. Each entry: the choice, the reason, and the alternative. Include Decisions 1 to 13, the source findings from Phase 1, the population fallback list, and the notes on Risks R1 and R2.
- Save `summary.md` (what was done and the result of each stage) and `PR.md` (PR title and body) in the outputs folder named in the ticket.
- Run the STE lint on `DECISIONS.md` and `PR.md`.

Exit criteria:

- `oracle_map.yml` lists all seven checks and each answer column or view.
- `DECISIONS.md` lists every choice the ticket left open.
- `ste-lint.py` reports 0 hard violations on `DECISIONS.md` and `PR.md`.

## Reuse and extension

Reuse:

- The existing `Makefile` targets (`build`, `stream`), the `pyproject.toml` dependency pins, and `transform/profiles.yml`. Do not add a second profile or a second Makefile.
- One batch reader (Phase 2) for the contract and assistance files. Pass the type as a parameter.
- One macro file in `transform/macros/` for amount casts and FIPS padding (Rule of Three: shared by at least three callers).
- One macro for the late rule (Phase 7). Both `late_events` and `fct_edit` call it.
- The existing `data/raw/` layout. No file is moved.

Extension points:

- A source list in `pipeline/` (one entry per source). Adding a source adds one entry and one staging model. It does not change the loader.
- The late threshold (600 seconds) and the window length (300 seconds) are dbt variables in `transform/dbt_project.yml`. A second threshold reads a variable, not a new branch.
- Edit types are a dbt variable (`edit_types`). A new edit type changes one variable.

## Risks and challenges to the ticket

- **R1. dbt contracts with external materialization.** dbt-duckdb 1.11.0 may not enforce a contract on the `external` materialization. Phase 1 checks this. If it does not enforce, Phase 5 adds a singular test that compares the column names and types in `information_schema` with the contract. Record the result in `DECISIONS.md`.
- **R2. Incremental models with external publish.** The external materialization may not apply to incremental models. Phase 7 has a fallback: a post-hook `COPY` to Parquet.
- **R3. Replay format.** The ticket does not give the SSE field layout. Phase 1 reads one live capture. If the replay is not reachable, the local test server follows the Wikimedia EventStreams format. Record this in `DECISIONS.md` as an unverified assumption.
- **R4. Census county key gap.** The 2024 file may lack some counties (for example, Connecticut planning regions). Phase 1 lists them. Phase 5 applies the fallback.
- **R5. Watermark across restarts.** `W_before` depends on every earlier arrival, including events from before a restart. The design stores `arrival_seq` in the lake and takes the prior maximum from the existing tables. Phase 8 tests this.
- **R6. Test tooling.** The repo has no pytest. `uv run --with pytest` runs it without a dependency change. If the grader needs a fixed test command, record the command in `DECISIONS.md`.
- **Challenge C1.** The ticket says "where did the money go" without a place rule. This plan uses place of performance (Decision 3). Recipient location would answer a different question.
- **Challenge C2.** The ticket says `make build` must not change any output on a second run. The lake changes its load metadata each run. The plan compares marts only, not the lake.

## Footer

Next step: `/plan-review .context/plans/gh-1-pipeline.plan.md`.
Do not run `/plan-update` until a review file exists.

---

## Update 1 (2026-10-19): plan-review cycle 1

RUN_BY_COMMAND: plan-update

**Task:** gh-1
**Review applied:** `.context/reviews/plan_gh-1-pipeline.md` (Verdict: READY WITH CHANGES, cycle 1 of 5)

This update keeps the text above. Where this section conflicts with the text above, this section governs. Each item below names the review finding it closes.

### MF-1. dbt singular test location

- All dbt singular tests live in `transform/tests/`. dbt reads `test-paths: ["tests"]` relative to the project folder `transform/`.
- The pytest tests stay in the repo-root `tests/`.
- This applies to every singular test in Phases 3, 4, 5, 7 and 8.
- Blast radius: both locations are named there (see the Blast radius addendum below).

### MF-2. One dedupe rule (Option B chosen)

Dedupe runs in dbt only. The lake does not drop arrivals.

- **Decision 12 (replaces the text above):** The lake keeps every arrival, with its `arrival_seq`. This is source data plus load metadata. `first_arrivals` keeps one row per `meta.id`, the row with the smallest `arrival_seq`. Replays add rows to the lake. They do not add rows to `first_arrivals`.
- **Crash rule (Phase 6):** On start, the consumer deletes each lake batch file whose `arrival_seq` range is above the committed cursor. Such a file was written but never committed. After the delete, the replay writes that range once. A crash between the write and the commit adds no duplicate.
- **Phase 5 exit (replaces the text above):** Not a dedupe check. The check is the reconciliation test. The oracle views count awards and totals from `first_arrivals` only, for the stream side.
- **Phase 7 `first_arrivals`:** A filter, as the original text says. Its distinct `meta.id` count equals the distinct count in the lake.

### MF-3. Event type rules for lateness

1. **Which types raise `W_before`:** All event types. `W_before(e)` is the maximum `timestamp` over all earlier first arrivals, of any `type`. This includes `log` and `categorize`.
2. **Where the edit filter applies:** After the lateness test.
   - `late_events` = first arrivals where `W_before > window_end + 600` and `type` is in `edit_types`.
   - `fct_edit` = first arrivals where `W_before <= window_end + 600` and `type` is in `edit_types`.
   - A first arrival with a type outside `edit_types` is in neither table.
- `window_end(e) = floor(ts / 300) * 300 + 300`. The late rule in Decision 10 is unchanged.

### MF-4. Common column set (Phase 3)

Source headers were checked in the FY2024 zips for agencies 417 and 418.

| Common column | Contracts source column | Assistance source column |
|---|---|---|
| `transaction_key` | `contract_transaction_unique_key` | `assistance_transaction_unique_key` |
| `award_key` | `contract_award_unique_key` | `assistance_award_unique_key` |
| `award_id` (display only) | `award_id_piid` | `award_id_fain` |
| `action_date` | `action_date` | `action_date` |
| `action_date_fiscal_year` | `action_date_fiscal_year` | `action_date_fiscal_year` |
| `obligation` | `federal_action_obligation` | `federal_action_obligation` |
| `agency_code` | `awarding_agency_code` | `awarding_agency_code` |
| `agency_name` | `awarding_agency_name` | `awarding_agency_name` |
| `state_fips` | `prime_award_transaction_place_of_performance_state_fips_code` | same |
| `county_fips` | `prime_award_transaction_place_of_performance_county_fips_code` | same |

- `transaction_id` = `transaction_key`. This is the fact key.
- `award_id` for check 3 = `award_key`. The unique award key is used. `award_id_piid` and `award_id_fain` are not unique across agencies.
- `primary_place_of_performance_state_code` (letters, contracts only) is not used. The FIPS columns are the join keys.
- `county_fips` is the 5-digit code (state FIPS plus county FIPS).
- Census join: `dim_place` and `dim_population_county_2024` join on the 5-digit code. The census side is built from `STATE` (2 digits) and `COUNTY` (3 digits), both padded by the FIPS macro.
- **Fiscal year:** `stg_usaspending_transactions` keeps all rows, so its row count equals the lake row count (Phase 3 exit). The filter `action_date_fiscal_year = 2024` is applied in `fct_award_transaction` (Phase 4) and in each oracle view for checks 1 to 4.
- Phase 4 "no row lost" test: the sum of `fct_award_transaction` amounts (FY2024) equals the sum of `stg_usaspending_transactions` amounts filtered to `action_date_fiscal_year = 2024`.

### MF-5. Stream model location

- Stream models live in `transform/models/stream/`. This matches `staging/`. `dbt build --select stream` selects them by folder.
- Makefile `stream` target: before running `dbt build --select stream`, run `dbt ls --project-dir transform --profiles-dir transform --select stream --resource-type model`. Fail the target when the output has no model lines. dbt exits 0 when nothing is selected, so this guard is needed.

### MF-6. Exact counts for the stream tests (Phase 6)

**Cursor rule (added by this update, not in the review):** Resume with `Last-Event-ID` set to the last committed id. Do not use the last seen id. A disconnect drops the unflushed buffer. Using the last seen id would lose those events. The counter is committed with the cursor, so it also restarts from the committed value.

**Disconnect rule:** On a disconnect, discard the unflushed buffer and reconnect from the committed cursor. A batch flush on stop (`DURATION` reached) is unchanged.

**Test A, stop and restart:**
- The test server sends 60 distinct ids (1 to 60).
- Run 1 stops after 30 events (ids 1 to 30 are committed).
- On reconnect, the test server repeats ids 26 to 60. Ids 26 to 30 are the overlap (5 ids).
- Expected: lake rows = 65 (30 + 35). Distinct `meta.id` = 60. `first_arrivals` rows = 60.

**Test B, forced disconnect mid-batch:**
- The test server sends 60 distinct ids. The batch size is 10. The server closes the connection after id 17.
- The buffer holds ids 11 to 17, which are not committed. The buffer is discarded.
- The consumer reconnects from the committed cursor (id 10) and receives ids 11 to 60 again.
- Expected: lake rows = 60 exactly. Distinct `meta.id` = 60. `first_arrivals` rows = 60.

### Phase 7 and Phase 8 test rules (MF-1, MF-2, MF-3 applied)

- Singular tests are in `transform/tests/`.
- Late-rule test (4 events, TDD note in Phase 7): one event exactly at `window_end + 600` (not late) and one event one second past it (late). Both are edit types. Add one non-edit event, which is in neither table.
- Check 5 totals equal the distinct `meta.id` count of `first_arrivals`, filtered to edit types, plus the late part. The interrupted and uninterrupted runs must match.

### Notes (N-1 to N-8)

- **N-1:** Phase 2 replaces the existing `build` stub in the Makefile. It does not add a target.
- **N-2:** `stg_recentchange` is a view over the lake. `first_arrivals`, `late_events`, `fct_edit` and `mart_edit_windows_5min` are incremental.
- **N-3:** Phase 1 creates `DECISIONS.md` with the source-findings section. Phase 9 completes it.
- **N-4:** The implement stage (E1) makes one commit per phase, after that phase's exit criteria pass.
- **N-5:** Rollback: the branch `feature/gh-1-pipeline` is new. Rollback is deleting that branch. This is added to Blast radius.
- **N-6:** Phase 5 fallback for a county with no `POPESTIMATE2024`: use `POPESTIMATE2021` and set `population_year = 2021`. `CENSUS2020POP` is not used (Amendment A).
- **N-7:** Risk R1. If dbt-duckdb does not enforce contracts on the external materialization, the singular test in Phase 5 replaces enforcement. The ticket says contracts are enforced, so this changes the ticket. Record it in `DECISIONS.md` and flag it for the author. The author must accept or reject it.
- **N-8:** Unknown-county rows have null population and null `obligations_per_person`. Check 2 excludes them on purpose.

### Blast radius addendum

- Singular tests: `transform/tests/`. Pytest tests: `tests/` (repo root).
- Rollback: delete branch `feature/gh-1-pipeline`.

## Footer (Update 1)

Next step: `/plan-review .context/plans/gh-1-pipeline.plan.md`.

---

## Update 2 (2026-10-19): plan-review cycle 2

RUN_BY_COMMAND: plan-update

**Task:** gh-1
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
**Review applied:** `.context/reviews/plan_gh-1-pipeline.md` (Verdict: READY WITH CHANGES, cycle 2 of 5)

This update keeps the text above and Update 1. Where this section conflicts with them, this section governs.

### MF-1. W_before reads the lake

This replaces the Phase 7 text "plus the prior maximum stored in the existing `fct_edit` and `late_events` tables", and the Decision 10 meaning of `W_before`.

- `W_before(e)` = the maximum `timestamp` over all lake rows (every `type`) whose `arrival_seq` is less than the `arrival_seq` of the first arrival of `e`.
- The lake keeps every arrival (Update 1 MF-2). No other table supplies a prior maximum. A restart adds no state to this calculation.
- A duplicate arrival of an earlier event has the same timestamp as that event's first arrival. That first arrival has a smaller `arrival_seq`. So "all earlier arrivals" and "all earlier first arrivals" give the same maximum.
- A stored `arrival_seq` never changes. So `W_before(e)` is fixed once `e` is first seen. An incremental run never changes an earlier classification.
- The macro reads `stg_recentchange`, the view over all lake rows.

### MF-2. Stream landing, state store, crash rule and filter

**The stream path does not use dlt.** This replaces the Phase 6 words "with dlt (Parquet, append disposition)". The consumer writes micro-batches with pyarrow. dlt keeps its own load state. A file delete would leave that state out of step with the lake. The batch path (Phase 2) still uses dlt.

**Files and names:**

- Batch file: `lake/stream_recentchange/batch_<first_seq>_<last_seq>.parquet`. Each seq is zero-padded to 12 digits. The file holds the rows whose `arrival_seq` is in that range.
- Temp file: `lake/stream_recentchange/*.tmp`.
- State file: `lake/_state/stream_state.json`, with keys `last_event_id` and `committed_arrival_seq`. This file is the source of the cursor and the counter. It replaces "the pipeline state" in Phase 6.

**Write order for each batch (the state write is the commit):**

1. Write the batch to a `.tmp` file.
2. Rename it to the batch file name with `os.replace`.
3. Write the state file to a `.tmp` file with the new `last_event_id` and `committed_arrival_seq`. Rename it with `os.replace`.

The next batch starts at `committed_arrival_seq + 1`.

**Start rule:**

1. Delete every `*.tmp` file under `lake/stream_recentchange/`.
2. Delete every batch file whose last seq is greater than `committed_arrival_seq`. These were written but not committed.
3. Read `last_event_id` and send it as `Last-Event-ID`. With no state file, start at id empty and seq 0.

**Batch path boundary:** `make build` replaces only the batch source folders (USAspending, census, site matrix). It never deletes `lake/stream_recentchange/` or `lake/_state/`.

**Incremental filter for `first_arrivals`:** A lake row enters `first_arrivals` when all three hold:

- `arrival_seq` is greater than the maximum `arrival_seq` already in `first_arrivals` (0 when the table is empty).
- Its `meta.id` is not already in `first_arrivals`.
- It has the smallest `arrival_seq` for its `meta.id` among the new rows (`row_number() over (partition by meta.id order by arrival_seq) = 1`).

The key is `event_id = meta.id`.

**Crash test (new, Phase 6):** A test stops the process after the batch rename and before the state write. The restart deletes the batch file. The replay then writes that range once. Expected: the lake rows match the uninterrupted run on `meta.id` and `arrival_seq`, and `first_arrivals` matches too.

### MF-3. Population fallback by county code

This replaces Update 1 N-6, the Phase 5 population bullet and R4.

**Repo facts, checked in this update:**

- `co-est2024-alldata.csv` has 9 Connecticut rows, state 09 and county 110 to 190 (planning regions). It has no old Connecticut county codes.
- `co-est2021-alldata.csv` has 8 Connecticut rows, state 09 and county 001 to 015 (old counties). It has no planning-region codes.
- Every other county appears in the 2024 file.

**Rule for `dim_population_county_2024`** (one row per 5-digit county code):

1. Code present in the 2024 file: `POPESTIMATE2024`, `population_year = 2024`.
2. Code absent from the 2024 file and present in the 2021 file (old Connecticut counties 09001, 09003, 09005, 09007, 09009, 09011, 09013, 09015): `POPESTIMATE2021`, `population_year = 2021`.
3. Code absent from both files: no population row. Population and `obligations_per_person` are null.

**Connecticut outcome:**

- Planning-region codes 09110, 09170 and 09180 appear in the FY2024 transactions. They join to the 2024 file under rule 1. No fallback applies to them. R4 is corrected: the 2024 file is complete for these codes. The gap is the 2021 file.
- Old codes 09001, 09003, 09005, 09009, 09011 and 09013 appear in the FY2024 transactions. They take rule 2. Their population is a 2021 value. Their per-person figure is not comparable with the planning-region figures for the same state. Record this in `DECISIONS.md` as a choice the author can reject. The alternative is null for these codes.

**Checks:**

- Phase 1 counts FY2024 transaction rows by county code for every code absent from the 2024 file. It records the list and the counts in `DECISIONS.md`.
- Phase 5 adds a singular test in `transform/tests/`. Every non-blank county code in `stg_usaspending_transactions` joins to `dim_population_county_2024`, or is on the recorded list from Phase 1.

### Phase 6 exit and tests (N-1, N-2)

- Phase 6 exit replaces "the lake then holds 60 rows with no duplicate `meta.id`". The lake keeps every arrival, so duplicates stay in the lake. The exit is: the lake holds 65 rows, 60 distinct `meta.id`, and `first_arrivals` holds 60 rows.
- Test A (Update 1 MF-6) makes the server ignore `Last-Event-ID`. It tests the dbt dedupe under replay. Expected: lake 65 rows, distinct `meta.id` 60, `first_arrivals` 60 rows.
- Test A2 (new) makes the server honor `Last-Event-ID` and send ids 31 to 60 only. Expected: lake 60 rows, distinct `meta.id` 60, `first_arrivals` 60 rows.

### Build and stream targets (new gap)

- `make build` runs `dbt build` with `--exclude stream`. The stream models read the stream lake, which the batch path does not create. Without the exclude, `make build` fails on a fresh checkout.
- `make stream DURATION=<seconds>` runs the guard from Update 1 MF-5, then `dbt build --select stream`, then the publish step for `mart_edit_windows_5min`.
- The Phase 5 idempotence check covers the batch marts only.

### Notes (N-3 to N-5)

- N-3: Phase 1 reads the header of all eight zips. It records the check for each zip, not only agencies 417 and 418.
- N-4: Phase 1 records, for each file, the count of rows with a blank place-of-performance county. These rows go to the unknown-county row (Decision 4).
- N-5: The source total for check 4 is `stg_usaspending_transactions` filtered on `action_date_fiscal_year = 2024`, summed by month. `v_month_reconciliation` compares the county totals and the state totals with this total.

### Decisions to record in DECISIONS.md

- Decision 14: The stream landing uses pyarrow, not dlt (MF-2).
- Decision 15: The population rule for old Connecticut codes (MF-3, rule 2).

## Footer (Update 2)

Next step: `/plan-review .context/plans/gh-1-pipeline.plan.md`.

---

## Update 3 (2026-10-19): plan-review cycle 3

RUN_BY_COMMAND: plan-update

**Task:** gh-1
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
**Review applied:** `.context/reviews/plan_gh-1-pipeline.md` (Verdict: READY WITH CHANGES, cycle 3 of 5)

This update keeps the text above, Update 1 and Update 2. Where this section conflicts with them, this section governs. Each item names the review finding it closes.

### MF-1. Check 5 has one expected value

This replaces the Phase 8 singular-test text and the Update 2 sentence "Check 5 totals equal the distinct `meta.id` count ... plus the late part".

- The expected count for check 5 is the count of distinct `event_id` in `first_arrivals` where `type` is in `edit_types`.
- This count equals the check 5 total over `fct_edit` union `late_events`. Update 1 MF-3 puts each edit-type first arrival in exactly one of those tables.
- Do not add a late count. Do not use a lake-wide count.
- The expected net bytes is the sum of `net_bytes` over the same rows. Decision 8 applies to null lengths.
- Use the same expected values in the Phase 8 singular test and in `oracle_map.yml`.

### MF-2. Checks 3, 5 and 7 have published outputs

Three outputs are added under `out/marts/`. The ticket allows downstream reads only from there.

- **`mart_award_net_fy2024`** (Phase 5). Grain: one award, by `award_key`, for FY2024 rows. Columns: `award_key`, `award_id`, `agency_code`, `net_obligation` (decimal sum of `obligation`). Check 3 is the count of rows where `net_obligation < 0`. The view `v_fy2024_award_net` is its build source.
- **`mart_stream_wiki_actor`** (Phase 7). Grain: one `wiki` and one `actor_type`. Columns: `wiki`, `actor_type`, `edit_count` (rows in `fct_edit` union `late_events`), `late_event_count` (rows in `late_events`), `net_bytes_added` (sum over the same union). Check 5 reads `edit_count` and `net_bytes_added`. Check 7 is the sum of `late_event_count`. This mart is a full rebuild, not incremental.
- `mart_edit_windows_5min` already covers check 6. No change.
- Add the publish step for `mart_award_net_fy2024` to Phase 5 exit criteria. Add the publish steps for `mart_stream_wiki_actor` and `mart_edit_windows_5min` to Phase 7 exit criteria. The `make stream` target runs both stream publish steps.
- Record the three outputs and their grain in `DECISIONS.md` as Decision 17.

### MF-3. The stream landing uses dlt

This replaces the Update 2 MF-2 text "The stream path does not use dlt". It also replaces the Update 2 state file rules and the Phase 6 pyarrow work item. Decision 14 (pyarrow) is withdrawn. Decision 16 replaces it.

The ticket requires dlt for the stream. The author cannot answer questions, so the plan keeps the ticket stack.

**Design:**

- `pipeline/stream.py` runs one dlt pipeline named `stream_recentchange`. It uses the dlt filesystem destination, Parquet files, and `write_disposition="append"`. The files go under `lake/stream_recentchange/`.
- The cursor is `last_event_id` and `committed_arrival_seq`. It lives in dlt pipeline state. dlt commits this state with each load. The design does not use the file `lake/_state/stream_state.json`.
- Each micro-batch is one dlt load. The consumer adds `arrival_seq` to each row before it yields the row.
- Start rule:
  1. Run dlt pending-load recovery before reading the cursor.
  2. Delete each stream batch file whose last `arrival_seq` is greater than `committed_arrival_seq`. These files were written but not committed.
  3. Read `last_event_id` and send it as `Last-Event-ID`. With no committed state, start at id empty and seq 0.
- Phase 6 keeps the Update 2 crash test. The test forces an exit after the batch file write and before the state commit. The restart deletes the orphan file. The replay writes that range once.
- Phase 6 also states this rule. The consumer restarts before any manual `dbt build --select stream`. The start rule runs first. Update 1 N-5 applies.

**Phase 1 gate for this design.** Phase 1 checks three facts on the pinned dlt version, and records the version in `DECISIONS.md`:

- Resource or pipeline state commits with the load.
- Each load file can be found and matched to its `arrival_seq` range, for the delete rule in step 2.
- Pending loads recover on the next run.

If one fact fails, Option 2 applies. The stream uses pyarrow with the Update 2 MF-2 rules. Add a risk entry in the form of N-7. Name the ticket text it departs from. Say the author must accept or reject it.

### MF-4. The "no row lost" test checks counts and sums

This extends Phase 4 and Update 1 MF-4. The singular test is in `transform/tests/`. For FY2024, it checks two things:

1. The row count of `stg_usaspending_transactions` (filtered on `action_date_fiscal_year = 2024`) equals the row count of `fct_award_transaction`.
2. The sum of `obligation` on both sides is equal.

TDD: write the test first on a fixture that drops one row from the fact side. The test must fail on that fixture. It must also fail on a join that drops the unknown rows.

### Notes (N-1, N-2, N-3, N-5, N-7)

- **N-1.** `stg_recentchange` is a view. Phase 7 text does not call it incremental. Update 1 N-2 gives the incremental list. It is `first_arrivals`, `late_events`, `fct_edit` and `mart_edit_windows_5min`.
- **N-2.** Body text is not edited, because this file is append-only. These rules govern the body text:
  - Phase 5, population: Update 2 MF-3 governs. It replaces the "latest earlier estimate" text.
  - Phase 6, stream landing: this update, MF-3, governs. It replaces the pyarrow and state file text.
  - Phase 6, exit counts: Update 2 MF-2 governs. It replaces the "60 rows" exit.
  - Phase 7, lateness and dedupe: Update 1 MF-2 and Update 2 MF-1 govern. They replace the "existing tables" prior maximum and the body dedupe text.
  - Phase 8, check 5: MF-1 of this update governs.
- **N-3.** Risk R1 and N-7 stay in force. `DECISIONS.md` in Phase 9 states the contract gap as a choice the author must accept or reject.
- **N-5.** The consumer restart rule is in MF-3 above.
- **N-7.** Phase 1 lists every county code absent from both Census files. It records the FY2024 transaction count for each code. Update 2 MF-3 rule 3 applies to these codes. They take null population.

### Decisions to record in DECISIONS.md

- Decision 14 (pyarrow for the stream): withdrawn. MF-3 of this update applies.
- Decision 15 (population rule for old Connecticut codes): unchanged.
- Decision 16 (stream landing with dlt and dlt state): new. Record the Phase 1 gate result.
- Decision 17 (outputs for checks 3, 5 and 7): new. MF-2 of this update applies.

## Footer (Update 3)

Next step: `/plan-review .context/plans/gh-1-pipeline.plan.md`.

---

## Update 4 (2026-10-19): plan-review cycle 4

RUN_BY_COMMAND: plan-update

**Task:** gh-1
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
**Review applied:** `.context/reviews/plan_gh-1-pipeline.md` (Verdict: READY WITH CHANGES, cycle 4 of 5)

This update keeps the text above and Updates 1 to 3. Where this section conflicts with them, this section governs. Each item names the review finding it closes.

### MF-1. Checks 1, 2 and 4 have published outputs

This replaces the Phase 5 oracle-view bullets and the Phase 5 exit text for checks 1, 2 and 4.
Check 1 has the same gap as checks 2 and 4. The review did not name it, but the same fix applies.
The ticket allows reads only from `out/marts/`. A warehouse view is not an answer path.

Add these three marts to Phase 5. Each is an external model under `out/marts/<mart_name>/`.

- **`mart_agency_fy2024`** (check 1). Grain: one `agency_code`. Columns: `agency_code`, `agency_name`, `net_obligations` (decimal sum of `obligation` for FY2024). Check 1 reads this mart. `v_fy2024_obligations_by_agency` is not an answer path.
- **`mart_county_fy2024_per_person`** (check 2). Grain: one 5-digit `county_fips`. Built from `fct_award_transaction` for FY2024, joined to `dim_population_county_2024` and `dim_place`. Columns: `county_fips`, `state_code`, `population`, `population_year`, `net_obligations` (decimal sum over FY2024), `obligations_per_person` (decimal division, scale 2). The county grain counts each county population once. The unknown-county row is not in this mart. Check 2 is the top 10 counties by `obligations_per_person`, with null population excluded. `v_fy2024_top10_counties_per_person` is not an answer path.
- **`mart_month_reconciliation`** (check 4). Grain: one calendar month of FY2024 action dates. Columns: `month`, `source_total`, `county_total`, `state_total`, `county_diff`, `state_diff`.
  - `source_total`: sum of `obligation` in `stg_usaspending_transactions` for FY2024, by month.
  - `county_total`: sum of `obligation` over all county rows in `fct_award_transaction`, by month. Include the unknown county.
  - `state_total`: the same sum over state rows. Include the unknown state.
  - `county_diff` and `state_diff`: each total minus `source_total`.
- `v_month_reconciliation` is not an answer path.

Notes for this section:

- `obligations_per_person` in `mart_obligations_monthly` is a monthly figure. Do not sum it over months. Check 2 reads `mart_county_fy2024_per_person`.
- Check 4 passes when the singular test in `transform/tests/` returns zero rows where `county_diff` or `state_diff` is not zero.
- Phase 5 exit criteria: each of `mart_agency_fy2024`, `mart_county_fy2024_per_person`, `mart_month_reconciliation` and `mart_award_net_fy2024` has a publish step in `make build` and a folder under `out/marts/`.
- The Phase 5 idempotence check covers all Phase 5 marts.
- Record the four outputs and their grain in `DECISIONS.md` as Decision 18.

### MF-2. The dlt stream start rule

This replaces the Update 3 MF-3 start rule for the dlt path. It also replaces the Update 2 MF-2 file-name rules and the `*.tmp` rule for the dlt path.
The Update 2 file names, the `*.tmp` rule and the Update 2 write order apply only when Option 2 (pyarrow) applies. Option 2 applies only if the Phase 1 gate fails.

**File mapping.** dlt names each stream file. The plan does not set those names. The consumer never parses a file name. Each Parquet file in `lake/stream_recentchange/` holds one dlt load:

1. Read the `arrival_seq` column of the file with pyarrow.
2. Take the minimum and the maximum of that column. The file covers the range from minimum to maximum.
3. Each load covers one contiguous range of `arrival_seq`.
4. A file that spans the committed cursor (minimum at or below `committed_arrival_seq`, maximum above it) breaks this rule. The consumer exits non-zero, names the file and both ranges, and deletes no file.

**Start rule (dlt path):**

1. Let dlt run pending-load recovery for the pipeline `stream_recentchange`. dlt does this before the cursor is read.
2. Read `last_event_id` and `committed_arrival_seq` from the dlt pipeline state in `lake/_dlt/`.
3. If no state exists and `lake/stream_recentchange/` holds a Parquet file, stop. See MF-3 for the rule.
4. Delete each Parquet file whose minimum `arrival_seq` is greater than `committed_arrival_seq`. A load in that range was written but not committed. This is the only delete step in the stream path.
5. Send `last_event_id` as `Last-Event-ID`. With no state and an empty stream folder, start with no id and seq 0.

**Crash test (kept from Update 3, file named).** The test forces an exit after dlt writes the Parquet file for a batch. The exit comes before dlt commits the state. The test checks the Parquet file whose minimum `arrival_seq` is the first uncommitted seq.
The test records which path ran: dlt recovery committed the load, or step 4 deleted the file. Either path must end with lake rows and `first_arrivals` that match the uninterrupted run on `meta.id` and `arrival_seq`.

### MF-3. dlt pipeline state has a fixed location

- Both dlt pipelines, the batch pipeline and `stream_recentchange`, set their pipelines directory to `lake/_dlt/`. Each pipeline keeps its state in a subfolder named after the pipeline. Phase 1 checks the argument name on the pinned version.
- Add the `lake/_dlt/` setting to the Phase 6 work list. Add `lake/_dlt/` to Blast radius as generated state under `lake/`.
- `lake/` is already in `.gitignore`, so `lake/_dlt/` needs no new line. Phase 6 exit checks it with `git check-ignore`.
- Batch boundary (replaces Update 2 text): `make build` deletes only the batch source folders (USAspending, census, site matrix). It never deletes `lake/stream_recentchange/` or `lake/_dlt/`.
- Missing-state rule: when `lake/stream_recentchange/` holds a Parquet file and the state is missing, the consumer exits non-zero with `STOPPED: stream state missing for non-empty lake`. It writes nothing and deletes nothing. To start again from zero, the operator deletes `lake/stream_recentchange/` by hand.
- Phase 6 test C: run a full stream, then delete `lake/_dlt/`, then run `make stream`. Expected: non-zero exit, the message above, and an unchanged file list in `lake/stream_recentchange/`.

Phase 6 work also adds: `pipeline/stream.py` reads the environment variable `STREAM_STOP_AFTER_EVENTS` (an integer). When it is set, the consumer stops after that many events and flushes. Test A and Test A2 use this variable. `make stream DURATION=` does not read it.

### Phase 1 gate (the one code exception in Phase 1)

Phase 1 has no code, except the gate test below. The gate test checks three facts on the pinned version `dlt[parquet]==1.31.0`.

- File: `tests/test_dlt_stream_gate.py`. Run: `uv run --with pytest pytest tests/test_dlt_stream_gate.py`.
- Test `test_state_commits_with_load`: the state commits with each load.
- Test `test_load_file_maps_to_seq_range`: each load file has an `arrival_seq` range that MF-2 reads.
- Test `test_pending_load_recovers_on_next_run`: pending loads recover on the next run.
- Test `test_pipelines_dir_argument`: the pipelines directory setting puts state under `lake/_dlt/`.
- Record the pinned version and the result of each test in Decision 16.
- If one test fails, Option 2 applies. Option 2 is pyarrow with the Update 2 MF-2 file rules. Risk R7 records it. The ticket requires dlt, so Option 2 departs from the ticket. The author must accept or reject it.

### Notes (N-1, N-2, N-3, N-5)

- **N-1 (duplicate ids).** Update 1 N-7 is Risk R1, and it stays. Update 3 N-7 is the county-code note, and it stays. The dlt fallback risk from Update 3 MF-3 is Risk R7.
- **N-2 (author choices).** E1 records each choice in `DECISIONS.md` and keeps the ticket rule. E1 does not wait for an answer.
- **N-3 (Phase 1 gate commands).** The command and the test names are in the Phase 1 gate section above. E1 records the result in Decision 16.
- **N-5 (stop hook).** `STREAM_STOP_AFTER_EVENTS` is the hook. See MF-3.

### Decisions to record in DECISIONS.md

- Decision 16 (stream landing with dlt): updated. It has the state location, the start rule in MF-2, and the Phase 1 gate result.
- Decision 18 (outputs for checks 1, 2 and 4): new. MF-1 applies.
- Decision 19 (refuse start when stream state is missing): new. MF-3 applies.

## Footer (Update 4)

This update closes review cycle 4. The next review is cycle 5 of 5.
Next step: `/plan-review .context/plans/gh-1-pipeline.plan.md`.

---

## Update 5 (2026-10-19): plan-review cycle 5 of 5 (last update)

RUN_BY_COMMAND: plan-update

**Task:** gh-1
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
**Review applied:** `.context/reviews/plan_gh-1-pipeline.md` (Verdict: READY WITH CHANGES, cycle 5 of 5)

This is the last update in the loop. No further review is requested.
This update keeps the text above and Updates 1 to 4. Where this section conflicts with them, this section governs.
The open items are listed under "Carried review findings" at the end of this section.

### MF-1. Checks 5, 6 and 7 have one answer path each

This replaces the Phase 8 oracle-view bullets. It also replaces the Update 3 MF-2 check 6 text.

- **Check 5:** answered by `mart_stream_wiki_actor`. Read the columns `edit_count` and `net_bytes_added`, summed over all rows. This is the same as Update 3 MF-2.
- **Check 6:** answered by a query over `out/marts/mart_edit_windows_5min`. Filter on `wiki = 'en.wikipedia.org'`. Order by `edit_count` descending, then `window_start` ascending. Keep the first N rows, where **N = 10**.
  - N = 10 is a choice. The ticket gives no N. The author can reject it.
  - Record N and the tie-break in `DECISIONS.md` as an extension of Decision 18.
- **Check 7:** answered by `mart_stream_wiki_actor`. The answer is the sum of `late_event_count`. This is the same as Update 3 MF-2.
- **Not answer paths:** `v_stream_by_wiki_actor`, `v_top_windows_en_wikipedia` and `v_late_event_count`. Remove them from the Phase 8 work list. Do not build them.
- **Phase 8 exit (replaces the Phase 8 exit text for checks 5 to 7):** Checks 5, 6 and 7 each return rows from a file under `out/marts/`.

### MF-2. The Phase 1 gate has an exit criterion

This replaces the Phase 1 TDD note (line 90). It adds to the Phase 1 exit criteria. Update 4 "Phase 1 gate" text governs the test names.

- **Phase 1 exit (added):** `uv run --with pytest pytest tests/test_dlt_stream_gate.py` runs. Each of the four tests has a recorded result, pass or fail.
- **Decision 16 (added):** Record the pinned version `dlt[parquet]==1.31.0` and the result of each of the four tests.
- **Phase 6 entry check (added):** The dlt stream path (Option 1) starts only when all four gate tests pass. If any test fails, Option 2 applies. Option 2 is pyarrow with the Update 2 MF-2 file rules. Risk R7 records it.
- **Phase 1 TDD note (replaces line 90):** The gate test file `tests/test_dlt_stream_gate.py` is the only code in Phase 1. Every other Phase 1 item is a stated fact with its source (file and line, or the command output).

### MF-3. Test server behavior per connection

This replaces the Update 1 MF-6 Test A and Test B text. It keeps the exit counts from Update 1 MF-6 and Update 2 MF-2. The test server and the test file have fixed names:

- **Test server:** `tests/stream_test_server.py`. It sends a fixed list of events. Its mode sets whether it reads `Last-Event-ID`.
- **Test file:** `tests/test_stream_restart.py`.

Counting rules that all three tests use:

- `STREAM_STOP_AFTER_EVENTS` counts arrivals that the run writes and commits. Duplicate arrivals count. Rows that a disconnect discards do not count.
- `arrival_seq` is assigned when a row enters a batch. On a disconnect, the counter rolls back to `committed_arrival_seq` (Update 1 MF-6). Discarded rows use no sequence numbers.
- The server closes a connection only where a test says so. A server that closes every connection never ends a run.

**Test A (server ignores `Last-Event-ID`):**

- Run 1, connection 1: no header. The server sends ids 1 to 60 in order. The consumer runs with `STREAM_STOP_AFTER_EVENTS=30`. It commits ids 1 to 30, then closes. The server does not close.
- Run 2, connection 1: the consumer sends `Last-Event-ID: 30`. The server ignores the header. It sends ids 26 to 60 (35 events). The server does not close. The consumer runs with `STREAM_STOP_AFTER_EVENTS=35`.
- Expected: lake rows 65 (30 + 35). Distinct `meta.id` 60. `first_arrivals` 60 rows.

**Test A2 (server honors `Last-Event-ID`):**

- Run 1, connection 1: no header. The server sends ids 1 to 60 in order. The consumer runs with `STREAM_STOP_AFTER_EVENTS=30`. It commits ids 1 to 30, then closes. The server does not close.
- Run 2, connection 1: the consumer sends `Last-Event-ID: 30`. The server sends only ids greater than 30, that is ids 31 to 60 (30 events). The consumer runs with `STREAM_STOP_AFTER_EVENTS=30`.
- Expected: lake rows 60. Distinct `meta.id` 60. `first_arrivals` 60 rows.

**Test B (forced disconnect mid-batch, batch size 10):**

- One run, connection 1: no header. The server sends ids 1 to 17, then closes the connection after id 17. This is the only close in Test B. Ids 1 to 10 flush as one batch and commit (cursor id 10). Ids 11 to 17 stay in the buffer. The disconnect discards them. The counter rolls back to 10.
- Same run, connection 2: the consumer sends `Last-Event-ID: 10`. The server honors the header and sends ids 11 to 60 (50 events). The server does not close. The run uses `STREAM_STOP_AFTER_EVENTS=60`. That count is 10 from connection 1 plus 50 from connection 2.
- Expected: lake rows 60. Distinct `meta.id` 60. `first_arrivals` 60 rows.

### MF-4. Phase 8 stop mechanism and replay checks

This replaces the Phase 8 interrupted-run text. It adds to the Phase 1 work list.

- **Acceptance input:** The Phase 8 acceptance test uses the Phase 6 test server in honor mode (the Test A2 server). It does not use the live replay.
- **Interrupted run:** Run 1 is `STREAM_STOP_AFTER_EVENTS=30` with the test server URL. Run 2 sends `Last-Event-ID: 30`, and the server honors it. Run 2 uses `STREAM_STOP_AFTER_EVENTS=30`. After each run, the test runs `dbt build --select stream`, the same steps as `make stream`.
- **Uninterrupted run:** One run against the test server, with `STREAM_STOP_AFTER_EVENTS=60`, and no restart.
- **Stop mechanism:** `pipeline/stream.py` reads `STREAM_STOP_AFTER_EVENTS`. The acceptance test calls `uv run python -m pipeline.stream` with that variable set. The `make stream DURATION=` target does not read it (Update 4 MF-3).
- **Replay end condition:** The test server sends its fixed list. It then keeps the connection open and sends nothing. Each run ends by its arrival count, not by time.
- **Live replay:** The live replay is not used for the acceptance test. A live run uses `DURATION`, and its totals are not compared with the test server totals.
- **Phase 1 work (added):** If `localhost:8099` answers, the check sends one request with the header `Last-Event-ID: 5`. Read at most 20 lines or 10 seconds. Record whether the first `id:` received is 6. Record `honors` or `does not honor` in `DECISIONS.md`. If the replay does not answer, record `not reachable`.
- **Phase 8 exit (added):** The total for check 5 after the interrupted run equals the total after the uninterrupted run. This is already in Phase 8. The test uses the test server only.

### Notes (N-1 to N-5)

- **N-1 (Risk R7, added to the Risks section):** R7. The dlt stream path can fail the Phase 1 gate. If it fails, the stream uses pyarrow with the Update 2 MF-2 file rules. This departs from the ticket requirement to use dlt for the stream. The author must accept or reject it. Record it in `DECISIONS.md` under Decision 16.
- **N-2 (body text):** Phase 2 text "Each `make build` replaces the lake folder" is governed by Update 4 MF-3. `make build` deletes only the batch source folders.
- **N-3 (R1 and N-7):** These stay as written in Updates 1 and 3. Record the contract gap in `DECISIONS.md`.
- **N-4 (incremental strategy for `mart_edit_windows_5min`):** The chosen option is delete and insert. Find the set of windows touched by rows added in this run. Delete those windows from the mart. Insert the `GROUP BY` result over `fct_edit` for those windows only. The Phase 7 test "equals a direct `GROUP BY` over `fct_edit`" checks it. Record this as Decision 20.
- **N-5 (missing-state message):** The first word changes. The message is `ERROR: stream state missing for non-empty lake`. This replaces the `STOPPED:` text in Update 4 MF-3 and in Test C. Test C still checks for a non-zero exit, the message, and an unchanged file list.
- **N-6 to N-8:** No change. The ids stay as they are.

### Decisions to record in DECISIONS.md

- Decision 16 (stream landing with dlt): add the four gate results and the pinned version (MF-2). Add the replay `Last-Event-ID` result (MF-4).
- Decision 18 (outputs for checks 1, 2 and 4): extended for checks 5 to 7 (MF-1). Record N = 10 and the tie-break for check 6.
- Decision 19 (refuse start when stream state is missing): message text per N-5.
- Decision 20 (incremental strategy for `mart_edit_windows_5min`): delete and insert of affected windows (N-4).

## Carried review findings

This update applies every must-fix from cycle 5. Each open item is listed here with the phase test that settles it. The gate checks these ids. No review is requested for them.

- **MF-1 (cycle 5):** Settled by the Phase 8 exit check. Checks 5, 6 and 7 each read from `out/marts/`. The Phase 9 `oracle_map.yml` names the answer path for each check.
- **MF-2 (cycle 5):** Settled by the Phase 1 gate test `tests/test_dlt_stream_gate.py`. The four results are recorded in Decision 16.
- **MF-3 (cycle 5):** Settled by the Phase 6 tests A, A2 and B in `tests/test_stream_restart.py`, with the test server in `tests/stream_test_server.py`.
- **MF-4 (cycle 5):** Settled by the Phase 1 replay `Last-Event-ID` check and the Phase 8 interrupted-run acceptance test.
- **MF-6 (cycle 1, cited by cycle 5 review):** Settled by the Phase 6 Test A and Test B in `tests/test_stream_restart.py`. The cycle 5 review cites Update 1 MF-6 for the test server behavior. Those tests cover it.

Status: open until the named test runs and passes.

## Footer (Update 5)

This update closes the review loop at cycle 5 of 5. No further `/plan-review` is requested by this update.
The gate checks the carried ids above against the phase tests. Do not start E1 from this update.
