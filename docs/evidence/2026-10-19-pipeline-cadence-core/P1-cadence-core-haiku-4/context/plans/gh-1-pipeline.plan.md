RUN_BY_COMMAND: plan-create

# gh-1: Federal spend and Wikipedia edit pipeline

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)

Task: gh-1. Branch: `feature/gh-1-pipeline`. Source: `.context/issues/gh-1.md`.
Status: plan only. Nothing is implemented.

## Step 0: Problem, decisions, blast radius, acceptance

### Problem

The analysts need two answers.

- Question A (batch): where federal contract and grant money went in FY2024. Totals, per person, by state, county, awarding agency and month.
- Question B (stream): how Wikipedia is edited now. Edits per wiki, namespace and 5-minute window, split human and bot, with net bytes added.

Outputs are Parquet marts under `out/marts/`. Downstream readers use only that folder.

### Success signals

1. `make build` runs from the raw files and exits 0.
2. A second `make build` leaves every batch mart with the same rows.
3. `make stream DURATION=<seconds>` consumes the replay and updates the stream tables.
4. A stop and a restart of the consumer keep the unique event count unchanged.
5. `uv run dbt build --project-dir transform --profiles-dir transform` passes, including all key tests.
6. `oracle_map.yml` maps checks 1 to 7 to a table or view.
7. `DECISIONS.md` records each choice that the spec left open.
8. Checks 1 to 7 match an independent oracle.

### Constraints

- Python 3.12, dlt 1.31.0 (filesystem Parquet destination), dbt-core 1.11.6, dbt-duckdb 1.11.0, duckdb 1.5.6. Source: `pyproject.toml`.
- Do not change `pyproject.toml` or `uv.lock`.
- Add no dependency. `pytest` is not pinned, so tests use stdlib `unittest`. The stream client uses stdlib `urllib`.
- The `build` and `stream` targets in `Makefile` are stubs. Implement both.
- No GitHub and no Linear. The PR is a local file.
- Nobody answers questions during the run. Choose, record the choice in `DECISIONS.md`, and continue.

### Non-goals

- No BI tool and no dashboard.
- The replay server at `http://localhost:8099/v2/stream/recentchange` is the test source. A live run against `stream.wikimedia.org` is an optional demo.
- Do not edit `data/raw/`.
- Do not add other sources. The inputs are the eight zips listed in `data/raw/usaspending/README.md`, the census county file and `sitematrix.json`.

### Scope challenges

The spec leaves these points open or unclear. The plan decides each one. Phase 1 records each decision in `DECISIONS.md`.

1. "Edit" is not defined. Decision: count every `recentchange` event as an edit. Keep the `type` field so analysts can filter. Check 5 says "every edit consumed", which supports this reading.
2. "Where the money went" has two readings: place of performance or recipient location. Decision: use place of performance. Record recipient location as the rejected option.
3. "Awards with a net negative obligation" is not defined at the award level. Decision: sum `federal_action_obligation` per award key over the FY2024 rows. Count awards whose sum is below zero.
4. The Assistance zips may use different columns than the Contracts zips. Phase 1 reads all eight headers before any union.
5. Late classification depends on arrival order. Decision: store an arrival sequence number at ingest. Classify late events as a pure function of that sequence. A full rebuild then gives the same flags.
6. Incremental models with the `external` materialization are unverified in dbt-duckdb 1.11.0. Phase 1 tests this. Phase 6 has a fallback.
7. The census file mixes state rows (SUMLEV 040) and county rows (SUMLEV 050). Decision: use SUMLEV 050 for counties.
8. `.gitignore` lists `transform/dbt_project.yml` and `transform/profiles.yml`, but git tracks both. Do not edit them.
9. The raw money fields are decimal strings. A type guess in dlt could turn them into floats. Decision: load every money field as text. Cast to `DECIMAL(18,2)` in dbt. A cast error fails the build.

### Blast radius

Files this plan adds or changes:

- `pipeline/` (new Python package: batch ingest, stream consumer, oracle, tests). Cadence gates this prefix through `.cadence.json`.
- `Makefile` (implement `build` and `stream`).
- `transform/models/` (staging, dimensions, facts, marts, schema YAML with tests and contracts).
- `transform/seeds/` (test fixtures and oracle values, only where a test needs them).
- `transform/tests/` (singular dbt tests for Phase 3 and Phase 6). Added by Update 1.
- `oracle_map.yml` and `DECISIONS.md` at the repo root.
- `lake/` and `out/`. Both are generated and gitignored. Never commit them.

Files this plan does not change: `pyproject.toml`, `uv.lock`, `.gitignore`, `data/raw/**`, `transform/dbt_project.yml`, `transform/profiles.yml`.

Rollback: delete `lake/` and `out/`, then revert the commit. Both folders are gitignored and rebuild from `data/raw/`. Added by Update 1.

### Acceptance

The work is accepted when every success signal in this section holds, and when the E4 PR text in `outputs/PR.md` cites the evidence for each signal.

## Reuse and extension

Existing helpers and modules that the plan reuses:

- `transform/dbt_project.yml`: profile `open_data_pipeline`, model path `models`. Reused as is.
- `transform/profiles.yml`: DuckDB at `out/warehouse.duckdb`, 4 threads. Reused as is.
- `Makefile` targets `build` and `stream`. Filled in, not renamed.
- `pyproject.toml` pins: dlt, dbt-core, dbt-duckdb and duckdb. Reused as is.

The repo has no existing Python code and no dbt models. No other helper exists to reuse.

Extension points that the plan uses:

- The dbt layer order: staging, then dimensions and facts, then marts.
- One dlt resource for each source table.
- The two Makefile targets.

The plan adds no new extension mechanism.

## Quality gates (real commands)

- `uv run dbt parse --project-dir transform --profiles-dir transform`
- `uv run dbt build --project-dir transform --profiles-dir transform`
- `uv run python -m unittest discover -s pipeline/tests -t .` (Phase 2 creates the test package and checks this command.)
- `make build`
- `make stream DURATION=<seconds>`

## Phases

Phases run in order. Each phase ends with its exit gate. Do not start a phase before the previous exit gate passes.

### Phase 1: Discovery and contract checks

Work:

1. Read the headers of all eight zips in `data/raw/usaspending/`. Unzip each into a new empty directory outside the repo. Record the column sets of the Contracts and Assistance files.
2. Check that the `action_date_fiscal_year` values are 2024 only. Check the format of `federal_action_obligation`. Count duplicate transaction keys. Update 2: name the transaction key column from the header read. Duplicate rule: keep one row for each transaction key. When a key appears in both the Contracts and the Assistance files, keep the Contracts row. Within one file, keep the first row in file order. Record the key column and the rule in `DECISIONS.md`.
3. Read `data/raw/census/co-est2024-alldata.csv`. Check the SUMLEV 050 rows, the `STATE` and `COUNTY` columns, and the `POPESTIMATE2024` column. List the counties with no 2024 value.
4. Read `data/raw/sitematrix.json`. Map each `dbname` to its `url`.
5. Sample the replay at `http://localhost:8099/v2/stream/recentchange`. Record the fields, the event id field, the event time field, and the `bot`, `namespace`, `length` and `type` fields. Test a reconnect with `Last-Event-ID`. Record whether the replay restarts from the start on each connect.
6. Check that dlt 1.31.0 writes Parquet to a local path. Check that a column hint keeps money fields as text.
7. Check that dbt-duckdb 1.11.0 accepts `incremental` with the `external` materialization. Record the result.
8. Write `pipeline/oracle.py`. It reads the raw files with `decimal` only. It does not use dbt or dlt. It prints the FY2024 totals. It prints the per-agency totals, the count of negative-net awards and the per-county totals. It also prints the census population for each county and the unique replay event count.

Exit gate: `uv run python pipeline/oracle.py` exits 0. `DECISIONS.md` has one entry for each scope challenge and each new finding.

TDD note: discovery only. No test is required in this phase.

### Phase 2: Batch lake

Work:

1. Write `pipeline/batch.py`, a dlt pipeline with one resource for each source: the Contracts files, the Assistance files, the census county file and `sitematrix.json`.
2. Extract the zips into a fresh temporary directory for each run. Do not extract them into the repo.
3. Load every money field as text. Keep all source columns. dlt adds only its load metadata.
4. Write each table to `lake/<source_table>/` with the `replace` write disposition, so a second run does not duplicate rows.
5. Do not touch the stream folders when the batch runs.
6. Update `make build` to run `uv run python -m pipeline.batch`.
7. Create `pipeline/tests/` and check the unittest command from the quality gates. Write the red tests in the TDD list before steps 1 to 6 run. Added by Update 1.

TDD:

- Red: a test that the value `-187158.88` lands as the exact text `-187158.88`.
- Red: a test that the census `SUMLEV` column keeps its original values.
- Red: a test that two runs give the same row count for each table.

Exit gate: `make build` exits 0. The row count of each lake table equals the oracle row count. A second `make build` gives the same row counts. `uv run python --version` reports 3.12, so `.python-version` is honored.

### Phase 3: Batch star schema

Work:

1. `transform/models/staging/stg_usaspending_transactions`: union the Contracts and Assistance tables on a shared set of columns. Add `source_file_type`. Cast `federal_action_obligation` to `DECIMAL(18,2)`. Keep one row for each transaction key.
2. `stg_census_county`: keep SUMLEV 050 rows. Build `county_fips` from `STATE` and `COUNTY` as a five-character text value. Keep the population columns.
3. `stg_sitematrix`: keep `dbname` and `url`.
4. `dim_agency`: awarding agency code and name.
5. `dim_place`: state and county. Add an `UNKNOWN` member for rows with no state or no county. Those rows keep the totals equal to the source total.
6. `dim_date`: day, fiscal year and month start.
7. `fct_award_transaction`: grain is one award transaction. Key is the transaction key, unique and not null. Money is `DECIMAL(18,2)`.
8. Add YAML descriptions that state each model grain. Add `unique`, `not_null` and `relationships` tests on the keys.
9. Update `make build` to run `dbt build` after the batch step.
10. `mart_fy2024_award_net` (added by Update 1, MF-3): grain is one award key, FY2024 rows only. Columns: `award_key`, `net_obligations` (the sum of `federal_action_obligation` per `award_key` over the FY2024 rows), `is_net_negative` (`net_obligations < 0`). The award key is the source award identifier column, which the Phase 1 header read names. Build it as a dbt table. Add `unique` and `not_null` tests on `award_key`. This model answers check 3. Superseded by Update 2 (MF-5, MF-6): build it with the `external` materialization to `out/marts/mart_fy2024_award_net/`. Add the model contract: `award_key` TEXT, `net_obligations` DECIMAL(18,2), `is_net_negative` BOOLEAN.

TDD:

- Red: a singular dbt test. The FY2024 sum of `federal_action_obligation` equals the oracle total.
- Red: a test that FY2024 by `action_date_fiscal_year` equals FY2024 by action date between 2023-10-01 and 2024-09-30.
- Red: a test that a cast error fails the build.
- Red (Update 2, MF-6): a contract test. A model whose column type differs from its contract fails the build.

Tests from review (Update 1):
- Phase 3, input: two transactions with the same transaction key in one Contracts zip and one Assistance zip. Expected: `stg_usaspending_transactions` keeps the rows that the Phase 1 duplicate rule keeps, and the FY2024 sum equals the oracle sum computed with that same rule. Phase 1 must record the duplicate rule in `DECISIONS.md`.

Tests from review (Update 2):
- Phase 3, input: two transactions with the same transaction key, one in a Contracts zip and one in an Assistance zip. Expected: `stg_usaspending_transactions` keeps the rows that the Phase 1 duplicate rule keeps, and the FY2024 sum equals the oracle sum with that same rule.

Exit gate: `uv run dbt build --project-dir transform --profiles-dir transform` passes. `make build` exits 0.

### Phase 4: Batch marts and publish (Question A)

Work:

1. `mart_fy2024_monthly_county_agency`: grain is one month, one county and one awarding agency. Columns: `month_start`, `state_code`, `state_name`, `county_fips`, `county_name`, `awarding_agency_code`, `awarding_agency_name`, `net_obligations`, `population_year`, `population`, `obligations_per_person`.
2. Enforce the model contract with the column names and types. Use the `external` materialization to `out/marts/mart_fy2024_monthly_county_agency/`. Key test (Update 2, MF-7, for step 1): a singular dbt test that `month_start`, `county_fips` and `awarding_agency_code` together are unique and not null.
3. Population rule: use `POPESTIMATE2024`. If a county has no 2024 value, use the latest earlier value from the same file. Record the year in `population_year`. Record each fallback in `DECISIONS.md`.
4. `obligations_per_person` = summed `net_obligations` divided by `population`. Round to two decimals. Do not average ratios. Set it to null when the population is null or zero.
5. Write `oracle_map.yml` for checks 1 to 4.
6. Write `pipeline/check_marts.py`. It prints the results of checks 1 to 4. It also prints a sorted-row hash for each mart.
7. `view_fy2024_county_per_person_top10` (added by Update 1, MF-4): a dbt view. Sum `net_obligations` over the FY2024 months and agencies for each `county_fips`. Divide that county total by `population`, using the ratio of sums rule from step 4. Rank the counties by that ratio, descending, with `county_fips` as the tie breaker. Keep ranks 1 to 10. Map it to check 2 in `oracle_map.yml`. Superseded by Update 2 (MF-5): also write the view as Parquet with the `external` materialization to `out/marts/view_fy2024_county_per_person_top10/`.
8. Map check 3 in `oracle_map.yml` to `mart_fy2024_award_net` (Phase 3 step 10) (added by Update 1, MF-3). Check 3 counts the rows where `is_net_negative` is true.

TDD:

- Red: a singular test for check 4. For one month, the county totals equal the state totals. The state totals equal the source total.
- Red: a fixture test. A county with no 2024 value uses the 2023 value.
- Red: a fixture test. Two transactions in one county give the ratio of their sum, not the average of two ratios.

Exit gate: `make build` exits 0 twice in a row. The sorted-row hash of each mart is the same after both runs. The results of checks 1 to 4 match the oracle.

### Phase 5: Stream consumer

Work:

1. Write `pipeline/stream.py`. It reads the SSE stream with `urllib.request`. It parses the `id:` and `data:` lines.
2. Reconnect after a disconnect with a bounded backoff. Send `Last-Event-ID` with the last stored id. The Phase 1 finding sets the exact resume method.
3. Deduplicate on the event `meta.id`. Skip an event whose id is already in the lake. Assign each new event the next `arrival_seq`. Update 2: `arrival_seq` is ingest metadata. Record that in `DECISIONS.md`.
4. Flush a micro-batch every N events or every T seconds. Write it to `lake/wiki_recentchange/` with dlt. Keep the checkpoint in the same load, so the events and the checkpoint commit together.
5. Stop after `DURATION` seconds. Flush the last batch. Exit 0.
6. Exit with a non-zero code and a clear message when `DURATION` is missing.
7. Update `make stream` to run `uv run python -m pipeline.stream --duration $(DURATION)`.

TDD:

- Red: a test with a local `http.server`. The fake SSE server drops the connection after three events. The client must resume with `Last-Event-ID`. The unique count must equal the total, with no duplicates.
- Red: a test that a duplicate `meta.id` is stored once.
- Red: a test that a stop and a restart keep the unique count equal to one uninterrupted run.

Tests from review (Update 1):
- Phase 5, input: the fake SSE server stops after three events, and the consumer is killed during a micro-batch flush before the checkpoint is written. Restart the consumer. Expected: unique count equals the replay total, with no `meta.id` stored twice. Phase 5 step 4 says the events and the checkpoint commit together. The dlt filesystem destination does not give that guarantee for two files, so this test decides the design.

Tests from review (Update 2):
- Phase 5, input: the fake SSE server stops after three events. The consumer stops during a micro-batch flush, before the checkpoint write. Restart the consumer. Expected: the unique count equals the replay total, and the `meta.id` values are unique.

Exit gate: `make stream DURATION=60` exits 0 against the replay. Two runs, with a stop between them, give a unique event count equal to the replay total from Phase 1. No `meta.id` appears twice in the lake.

### Phase 6: Stream models (Question B)

Work:

1. `stg_recentchange`: parse the fields. Use the event time from the `timestamp` field, as chosen in Phase 1. Set `wiki` to the `dbname` field. Set `actor_type` to `bot` when `bot` is true, else `human`. Set `bytes_added` to `new_length` minus `old_length`. Treat a missing length as zero and count those events in `DECISIONS.md`. (Superseded by Update 2: this sentence is void. Follow the NULL rule in this step.) Superseded by Update 1: a missing length gives `bytes_added` NULL, not zero. The event still counts in `edit_count`, and `net_bytes_added` sums only the non-null values. Record the choice in `DECISIONS.md`.
2. `window_start` = the event time floored to a multiple of 300 seconds, in UTC. The window end is `window_start + 300`.
3. `watermark_before` for arrival `n` = the maximum event time over all arrivals before `n`. Compute it with a window function over `arrival_seq`.
4. `is_late` = `watermark_before > window_start + 900`. An event exactly 600 seconds after the window end is not late.
5. `fct_edit`: grain is one change event, key `meta_id`. Contains every consumed event with `is_late`, `window_start`, `actor_type`, `bytes_added`, and the `server_name` from the sitematrix join. Build it incrementally on new `arrival_seq` values. Once set, `is_late` does not change. Update 2 (MF-5): also write `fct_edit` as Parquet with the `external` materialization to `out/marts/fct_edit/`. Use the fallback below if incremental `external` builds fail.
6. `late_events`: the rows of `fct_edit` where `is_late` is true. Build it as a dbt view. The view-or-table choice is recorded in `DECISIONS.md` (Update 1, review note). Superseded by Update 2 (MF-5): `late_events` is a table. Materialize it with the `external` materialization to `out/marts/late_events/`. Record the change in `DECISIONS.md`.
7. `mart_edit_window_5min`: grain is one `window_start`, `wiki`, `namespace` and `actor_type`. Counts on-time events only. Columns: `edit_count`, `net_bytes_added`. Use the `external` materialization to `out/marts/mart_edit_window_5min/`. Added by Update 1 (MF-1, MF-2): model contract with `wiki` TEXT, `namespace` INTEGER, `actor_type` TEXT, `window_start` TIMESTAMP, `edit_count` BIGINT, `net_bytes_added` BIGINT. The mart builds incrementally on new `arrival_seq` values. Each run reads the `fct_edit` rows with a new `arrival_seq`, then recomputes the windows those rows touch (delete and insert on the grain key). A full refresh gives the same `edit_count` and `net_bytes_added`. Key test (Update 2, MF-7): a singular dbt test that `window_start`, `wiki`, `namespace` and `actor_type` together are unique and not null.
8. `oracle_map.yml`: check 5 uses `fct_edit`. Check 6 uses the mart filtered to `en.wikipedia.org`. Check 7 counts `late_events`. Superseded by Update 2 (test from review): check 6 filters on `wiki = 'enwiki'`. The window mart has no `server_name` column, so a filter on `en.wikipedia.org` returns no rows.
9. Add an independent late-count function to `pipeline/oracle.py`. It applies the lateness rule to the raw arrival order.

TDD:

- Red: a dbt seed of crafted events covers these cases. An event exactly 600 seconds after its window end is not late. An event 601 seconds after is late. Arrival order differs from event order. A duplicate `meta_id` is not counted. Window starts are multiples of 300.
- Red: `fct_edit.meta_id` is unique and not null.
- Red: a full refresh gives the same `is_late` flags as the incremental build.
- Red (added by Update 1, MF-2): a full refresh gives the same `edit_count` and `net_bytes_added` in `mart_edit_window_5min` as the incremental build.
- Red (Update 2, MF-5): a test lists `out/marts/` after `make build` and finds one Parquet folder for each check object: `mart_fy2024_monthly_county_agency`, `view_fy2024_county_per_person_top10`, `mart_fy2024_award_net`, `fct_edit`, `mart_edit_window_5min` and `late_events`.

Tests from review (Update 1):
- Phase 6, input: one event with `length.new` absent and `length.old` 500. Expected: the event counts in `edit_count`, and `bytes_added` is not a negative value made from the missing side. The plan's rule "treat a missing length as zero" gives -500 here. Test the result the ticket asks for ("net bytes added"), and record the chosen rule in `DECISIONS.md`.
- Phase 6, input: a seed with an event whose window starts at 0 and whose `watermark_before` is 1500 (exactly 900 seconds after the window start). Expected: `is_late` is false. Input: the same event with 1501. Expected: `is_late` is true. The plan has the 600 and 601 second cases in the window-end form. Add the boundary in the window-start form as well, so the rule `watermark_before > window_start + 900` is tested as written.

Clarification (Update 1): the review's `window_start` of 0 does not match its 900-second offset. With `window_start` 0, the values 1500 and 1501 are 1500 seconds after the window start, and the rule marks both as late. The boundary test uses `window_start` 600, so `watermark_before` 1500 is exactly 900 seconds after the window start (not late), and 1501 is late.

Tests from review (Update 2):
- Phase 6, input: one event with `length.new` absent and `length.old` 500. Expected: the event counts in `edit_count`, `bytes_added` is NULL, and `net_bytes_added` does not include the event.
- Phase 6, input: one event with `window_start` 600 and `watermark_before` 1500. Expected: `is_late` is false. The same event with `watermark_before` 1501. Expected: `is_late` is true.
- Phase 6, input: events with `dbname` `enwiki` and server `en.wikipedia.org`. Expected: check 6 selects the `enwiki` rows. The window mart has no `server_name` column, so a filter on `en.wikipedia.org` returns no rows.

Exit gate: `make build` exits 0 with an empty stream folder. `make build` exits 0 after a stream run. The result of check 7 matches the oracle late count. Checks 5 and 6 return values.

Fallback: if Phase 1 shows that the `external` materialization does not support incremental builds, keep `fct_edit` and `mart_edit_window_5min` as DuckDB tables. Export them to `out/marts/` with a dbt post-hook. Record the change in `DECISIONS.md`.

### Phase 7: Evidence and hand-off

Work:

1. Remove `lake/` and `out/`. Run `make build`. The stream models must build with no stream data.
2. Run `make stream DURATION=<seconds>`. Then run `make build` twice. Compare the mart hashes.
3. Run the checks 1 to 7 queries and record the results in `summary.md`.
4. Write `outputs/summary.md`. It lists each stage and its result.
5. Write `outputs/PR.md`. It has a title and a body. The body lists the decisions and the evidence for each success signal.
6. Run `python3 $CADENCE_HOME/skills/asd-ste100/scripts/ste-lint.py` on `outputs/PR.md`. Fix each hard violation.
7. Finish `DECISIONS.md`.

Output paths (absolute):

- `/tmp/claude-0/-home-user/a08112b2-70f8-5c85-83c0-3c1d7290b3c5/scratchpad/pipe/P1-cadence-core-haiku-4/outputs/summary.md`
- `/tmp/claude-0/-home-user/a08112b2-70f8-5c85-83c0-3c1d7290b3c5/scratchpad/pipe/P1-cadence-core-haiku-4/outputs/PR.md`

Exit gate: every success signal holds. Both output files exist.

## Risks

- The replay behavior is unknown until Phase 1. A replay that restarts on each connect changes the Phase 5 design.
- dlt type inference could turn money into floats. The Phase 2 red test checks this.
- `.python-version` pins 3.12. The shell Python is 3.13. `uv` must fetch 3.12. The Phase 2 exit gate checks it.
- Incremental `external` models are unverified. The Phase 6 fallback covers this.
- The late rule needs the arrival order. The lake must keep `arrival_seq` for every event.

## Open decisions

None block the plan. Phase 1 records each decision in `DECISIONS.md`.

## Footer

Next step: `/plan-review .context/plans/gh-1-pipeline.plan.md`.
Do not run `/plan-update` before a review file exists.

---

## Update 1: plan-review cycle 1 applied (2026-10-19)

RUN_BY_COMMAND: plan-update

Source: `.context/reviews/plan_gh-1-pipeline.md` (RUN_BY_COMMAND: plan-review, Verdict: READY WITH CHANGES, review cycle 1).
Ticket: gh-1. **Tracker:** none. **Ticket:** TICKET_SKIPPED (none: no tracker declared).

Must-fix items:
- MF-1 applied: Phase 6 step 7 adds the model contract for `mart_edit_window_5min`.
- MF-2 applied: Phase 6 step 7 states the incremental build. Phase 6 TDD adds a full-refresh check on the mart.
- MF-3 applied: Phase 3 step 10 adds `mart_fy2024_award_net`. Phase 4 step 8 maps check 3 to it.
- MF-4 applied: Phase 4 step 7 adds `view_fy2024_county_per_person_top10`, mapped to check 2.

Tests from review: each line is copied under `Tests from review (Update 1)` in Phase 3, Phase 5 and Phase 6.

Other changes:
- Phase 6 step 1: the missing-length rule is superseded (`bytes_added` NULL, not zero). The review test requires it.
- Phase 6 TDD: the boundary numbers are clarified. The review's 1500 and 1501 values use `window_start` 0, which does not match the 900-second offset. The test uses `window_start` 600.
- Notes applied: `transform/tests/` and the rollback line are in Blast radius. Phase 2 step 7 says red tests come first. Phase 6 step 6 makes `late_events` a view.
- Notes not applied: the class check, reuse, replay probe, ste-lint path and census fallback. The review marks each one as checked with no change needed.

Open for the next review:
- The award key column name is set by the Phase 1 header read (Phase 3 step 10).
- Phase 5 step 4 still assumes one commit for events and checkpoint. The Phase 5 review test decides this.

---

## Update 2: plan-review cycle 2 applied (2026-10-19)

RUN_BY_COMMAND: plan-update

Source: `.context/reviews/plan_gh-1-pipeline.md` (RUN_BY_COMMAND: plan-review, Verdict: READY WITH CHANGES, review cycle 2).
Ticket: gh-1. **Tracker:** none. **Ticket:** TICKET_SKIPPED (none: no tracker declared).

This is the last plan update. The review is the second blocking review. No further review is requested. The open must-fix items are carried below.

Must-fix items:
- MF-5 applied: Phase 3 step 10, Phase 4 step 7 and Phase 6 steps 5, 6, 7 and 8 write each check object to `out/marts/` with the `external` materialization. `late_events` is a table. The test is in Phase 6 TDD.
- MF-6 applied: Phase 3 step 10 adds the model contract. The test is in Phase 3 TDD.
- MF-7 applied: Phase 4 step 2 (monthly mart) and Phase 6 step 7 (window mart) add singular key tests.

Tests from review: each line is copied under `Tests from review (Update 2)` in Phase 3, Phase 5 and Phase 6.

Other changes:
- Phase 1 step 2: the transaction key column and the duplicate rule are named. Rule: one row for each key. The Contracts row is kept when the key is in both files. Otherwise the first row in file order is kept. Recorded in `DECISIONS.md`.
- Phase 5 step 3: `arrival_seq` is ingest metadata. Recorded in `DECISIONS.md`.
- Phase 6 step 1: the "treat as zero" sentence is void. The NULL rule applies.
- Phase 6 step 8: check 6 filters on `wiki = 'enwiki'`.
- Notes not applied: Phase 5 step 4 (the review says no more text on this point). Reuse, class check, replay probe, ste-lint path and census fallback. The review marks each one as checked with no change needed.

New `DECISIONS.md` entries: the duplicate rule, `arrival_seq` as ingest metadata, the `late_events` table, the `external` output of each check object, and check 6 on `wiki = 'enwiki'`.

## Carried review findings

- MF-5 -> Phase 6 (TDD red: `out/marts/` holds one Parquet folder for each check object).
- MF-6 -> Phase 3 (TDD red: contract type mismatch fails the build).
- MF-7 -> Phase 4 (monthly mart key test) and Phase 6 (window mart key test).
