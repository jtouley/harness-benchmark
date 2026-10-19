# gh-1: federal spending and Wikipedia edit pipeline

RUN_BY_COMMAND: plan-create

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Session ticket: cd-1 (local ticket: `.context/issues/cd-1.md`, task id gh-1)

Branch: `feature/gh-1-pipeline`
Spec: `.context/issues/cd-1.md`

## Step 0: problem restatement

The change builds two pipelines for analysts.

- Question A (batch): where did FY2024 federal contract and grant money go?
- Question B (stream): how is Wikipedia edited now, per wiki, namespace and 5-minute window?

The flow runs in three layers. Ingestion lands sources in a Parquet lake under `lake/`. dbt-duckdb models build staging, the star schema and the marts. The models publish Parquet files under `out/marts/`. Only `out/marts/` is read downstream.

The repo has a skeleton only. `Makefile` targets `build` and `stream` print "not implemented" and exit 1. No ingestion code, no dbt models and no tests exist yet.

### Facts checked in the repo

- USAspending: 8 zip files (4 agencies, Assistance and Contracts). The FY417 sample has 3913 Assistance rows and 48 Contracts rows. Every row has a FY2024 action date.
- USAspending amounts are text. The FY417 Assistance sample has 247 negative amounts.
- Place of performance county is blank for 3856 of 3913 Assistance rows. Recipient county is blank for 10 of 3913. Place of performance state is never blank.
- Census: `co-est2024-alldata.csv` has `POPESTIMATE2024`. `co-est2021-alldata.csv` has `POPESTIMATE2021` as its latest year.
- Sitematrix: one JSON object per language. Each site has `dbname` (for example `enwiki`) and `url`.
- Stream: the replay endpoint at `http://localhost:8099/v2/stream/recentchange` responds now. In a 300-event sample, `meta.id` is unique and `wiki` is set on every event. Event types are `edit`, `new`, `categorize` and `log`. `length` appears only on `edit` and `new` events (144 of 300).
- Stream order: 97 of 299 consecutive events have a lower `timestamp` than the event before. Arrival order and event time differ, so the lateness rule matters.
- Event time: `timestamp` is epoch seconds. It matches `meta.dt` to within seconds.

### Design decisions

Each decision also goes into `DECISIONS.md` (the spec's deliverable 5).

- **D1, county basis.** Place of performance county is blank for almost all Assistance rows. Recipient county is almost always set. Proposed rule:
  1. State comes from place of performance state. It is always set.
  2. County comes from place of performance county when set.
  3. Otherwise, county comes from recipient county, only when the recipient county is in the same state as the place of performance.
  4. Otherwise, the row goes to the state's `UNASSIGNED` county.
  The column `county_source` records which rule applied.
  Challenge: rule 3 mixes two sources. Without it, checks 2 and 4 say little. Review must accept or reject this rule.
- **D2, award identity for check 3.** An award is one prime award key within one awarding agency. Assistance uses `award_id_fain`, or `award_id_uri` when FAIN is blank. Contracts use `award_id_piid`. The phase 4 test counts blank keys and sets the fallback order from the result.
- **D3, population.** Use `POPESTIMATE2024` from the county rows (`SUMLEV` 050). Counties missing from the 2024 file use the latest earlier estimate, `POPESTIMATE2021`, from the 2021 file. Record the count of fallback counties in `DECISIONS.md`. State totals come from the state rows (`SUMLEV` 040). Unassigned county rows have no population and no per-person value.
- **D4, what an edit is.** The edit fact holds every consumed change event, of every type, once. An edit is a change event with type `edit` or `new`. Net bytes are `length.new` minus `length.old`. For `new`, `length.old` is missing and counts as 0. Events without `length` add 0 net bytes.
- **D5, keys and fields.** Dedupe key: `meta.id`. Event time: `timestamp`. Wiki: `wiki`, joined to sitematrix `dbname`. Actor type: `bot` is true gives `bot`, otherwise `human`.
- **D6, late events.** `fct_recentchange_edits` keeps every event with an `is_late` flag. `late_events` is a table of the late rows. The 5-minute window mart counts only on-time events. Check 5 counts all events. Check 6 uses the window mart. Check 7 counts `late_events`.
- **D7, lateness rule.** Order events by `arrival_seq`, the order of first arrival. For each event, let `prior_max` be the highest `timestamp` among earlier arrivals. The event is late when `prior_max` is greater than `window_start + 900`. Window start is `floor(timestamp / 300) * 300`. Late events count in `prior_max` for later events.
- **D8, money.** Parse amounts as `DECIMAL(20,2)`. Sums use decimal arithmetic. Per-person values use `DECIMAL(20,4)`.

### Blast radius

- Created: `pipeline/` (ingestion, stream consumer, unit tests), `transform/models/` (staging, star, marts, stream, oracle), model YAML files, `oracle_map.yml`, `DECISIONS.md`.
- Changed: `Makefile` (both targets become real), `transform/dbt_project.yml` (tags and materialization only).
- Not changed: `pyproject.toml`, `uv.lock` (pins stay), `data/raw/**`, `transform/profiles.yml`.
- Generated and ignored: `lake/`, `out/`.
- Outside the repo: `outputs/summary.md` and `outputs/PR.md`.
- Gated: `pipeline/`, `transform/` and `Makefile` match `gated_prefixes_extra` in `.cadence.json`. The implementation phases run under the TDD gate.

### Quality gates

These commands exist now or come from this plan. Do not invent other targets.

- `uv sync` (Python 3.12 from `.python-version`). The system Python is 3.13.
- `uv run python -m unittest discover -s pipeline -p "test_*.py"`
- `uv run dbt build --project-dir transform --profiles-dir transform --select tag:batch`
- `uv run dbt build --project-dir transform --profiles-dir transform --select tag:stream`
- `uv run dbt test --project-dir transform --profiles-dir transform`
- `make build` and `make stream DURATION=<seconds>`
- `python3 "$CADENCE_HOME/skills/asd-ste100/scripts/ste-lint.py" <file>` for `DECISIONS.md`, `outputs/summary.md` and `outputs/PR.md`

Run one dbt build at a time. DuckDB allows one writer on `out/warehouse.duckdb`.

## Phases

### Phase 1: Environment and make targets

Goal: a working environment, and two make targets that do real work.

1. Run `uv sync`. Check the pins: dlt 1.31.0, dbt-core 1.11.6, dbt-duckdb 1.11.0, duckdb 1.5.6.
2. Create the `pipeline/` package.
3. Replace the Makefile recipes.
   - `build` runs the batch ingestion, then the batch dbt build.
   - `stream` runs the consumer for `DURATION` seconds, then the stream dbt build.
   - `DURATION` is required for `stream`. The recipe exits with an error when it is empty.

TDD note: a unit test runs `make -n build` and `make -n stream`. It checks that each target names its steps.

Exit criteria:
- `uv sync` passes.
- `uv run dbt debug --project-dir transform --profiles-dir transform` connects to `out/warehouse.duckdb`.
- Neither target prints "not implemented".

### Phase 2: Batch landing to the lake

Goal: land every raw source in `lake/`, unchanged, with load metadata.

1. Read each of the 8 USAspending zips with `zipfile`. Stream the CSV inside. Do not extract to the repo.
2. Write two lake tables with dlt and the filesystem destination (Parquet):
   - `lake/usaspending_assistance/` and `lake/usaspending_contracts/`, partitioned by `awarding_agency_code`.
   - Keep every source column as text.
3. Write `lake/census_county_2024/` and `lake/census_county_2021/` from the two census CSV files.
4. Write `lake/sitematrix/`, one row per site, with `dbname`, `url`, `code`, `sitename` and the language code.
5. Use `write_disposition="replace"` for each batch resource. Keep dlt pipeline state under `lake/`, not in the home directory.

TDD note: unit tests compare row counts with the source data rows. Sitematrix `dbname` must be unique.

Exit criteria:
- Row counts match the sources exactly.
- `make build` run twice gives the same file list and the same row counts.

### Phase 3: Stream consumer and stream landing

Goal: consume the SSE stream for a set time. Restart without a duplicate or a gap.

1. Write `pipeline/stream_consumer.py` with the standard library only. Do not add a dependency.
2. Read the SSE `data:` lines. Skip keep-alive lines and lines that are not JSON.
3. Send the last `id:` value as `Last-Event-ID` on reconnect. Use backoff.
4. Assign `arrival_seq` in arrival order. Continue from the largest `arrival_seq` in the lake.
5. Before landing, drop events whose `meta.id` is already in the lake.
6. Land micro-batches as Parquet in `lake/recentchange/`. Flatten `meta.id`, `meta.dt`, `length.old`, `length.new`, `revision.old` and `revision.new`.
7. Write the cursor file `lake/_state/stream_cursor.json` after each landed batch. Write it atomically.
8. Stop after `DURATION` seconds. Flush the last batch before exit.
9. Read `STREAM_URL` from the environment. The default is the replay URL.

Challenge: the replay may not honour `Last-Event-ID`. Test this first. Step 5 must run in all cases. It is the guarantee against a double count.

TDD note:
- A unit test parses an SSE fixture that holds keep-alives, a non-JSON line and a repeated event.
- An integration test runs 20 seconds, stops, restarts for 20 seconds, and checks that `meta.id` is unique and `arrival_seq` has no gap.
- A second integration test kills the process with `SIGKILL` during a batch, restarts, and runs the same checks.

Exit criteria: the integration tests pass.

### Phase 4: Staging models

Goal: typed, deduplicated views of each lake table.

1. `stg_usaspending_transactions`: union of both lake tables. Cast the amount to `DECIMAL(20,2)`. Keep rows with `action_date_fiscal_year = 2024`. Set `source_type` to `assistance` or `contract`. Set `award_key` by D2.
2. `stg_census_county`: rows with `SUMLEV` 050. `county_fips` is the 2-digit state code and the 3-digit county code, zero-padded to 5 characters. Include `population_2024` and `population_2021`.
3. `stg_census_state`: rows with `SUMLEV` 040, with `POPESTIMATE2024`.
4. `stg_sitematrix_wikis`: one row per `dbname`, with the site URL.
5. `stg_recentchange_events`: one row per `meta.id`, keeping the smallest `arrival_seq`. Set `event_time` from `timestamp`. Set `window_start` by D5 and the window rule.

Tag every model `batch` or `stream`. Document the grain of each model in its YAML. Test the key of each model with `unique` and `not_null`.

TDD note: a dbt singular test checks that the staging row count equals the lake row count, minus the FY2023 and FY2025 rows, if any.

Exit criteria:
- `uv run dbt build --select tag:batch` passes for the staging models.
- The phase 4 check of blank award keys is recorded. Its result sets the D2 fallback order.

### Phase 5: Star schema for Question A

Goal: one fact table and three dimensions, following the spec's grain rules.

1. `fct_award_transactions`: grain is one source transaction row. Key: the source's unique key (`assistance_transaction_unique_key` or `contract_transaction_unique_key`). Columns: `source_type`, `award_key`, `agency_key`, `place_key`, `date_key`, `federal_action_obligation` (`DECIMAL(20,2)`).
2. `dim_agency`: grain is one awarding agency (toptier code, name).
3. `dim_place`: grain is one county, or one `UNASSIGNED` county for a state. Columns: state FIPS and code, county FIPS and name, `county_source`. Implement D1 here.
4. `dim_date`: grain is one day, with `month_start`.

Test the keys with `unique` and `not_null`. Test the relationships from the fact to each dimension.

Exit criteria: `uv run dbt build --select tag:batch` passes. The fact row count equals the staging row count.

### Phase 6: Marts for Question A

Goal: the monthly mart that answers the spec's Question A.

1. `mart_obligations_monthly`: grain is one month, one state, one county or `UNASSIGNED`, and one awarding agency.
   - Columns: `mart_key` (hash of the grain), `month_start`, state FIPS and code, county FIPS and name, `agency_code`.
   - Columns: `net_obligations` (`DECIMAL(20,2)`), `award_transaction_count`, `population_2024`, `obligations_per_person` (`DECIMAL(20,4)`).
   - `population_2024` is null for `UNASSIGNED`. `obligations_per_person` is null when the population is null.
2. Apply D3 for population.
3. Enforce the contract in the YAML: column names and types.
4. Test the `mart_key` with `unique` and `not_null`.
5. A singular test checks the reconciliation for every month: county totals add up to state totals, and state totals add up to the source total.

Exit criteria: the contract and the tests pass. The reconciliation test returns no rows.

### Phase 7: Models for Question B

Goal: the edit fact, the late events table and the 5-minute window mart.

1. `fct_recentchange_edits`: incremental, `unique_key = meta_id`. Grain is one change event. Columns: `meta_id`, `event_id`, `event_time`, `arrival_seq`, `wiki`, `namespace`, `event_type`, `actor_type`, `is_edit`, `net_bytes`, `window_start`, `window_end`, `prior_max_event_time`, `is_late`.
   - In a full run, `prior_max_event_time` is the running maximum of `event_time` over earlier `arrival_seq` values.
   - In an incremental run, seed the maximum with the maximum `event_time` of the rows already in the fact. This works because the fact holds every event, late ones included, in arrival order.
2. `late_events`: table, rows where `is_late` is true.
3. `mart_edit_windows_5min`: incremental merge. Grain is one window, one wiki, one namespace, and one actor type. Columns: `edit_count`, `net_bytes_added`. Count on-time events only (D6). Rebuild the windows that the new batch touches.
4. Publish `fct_recentchange_edits`, `late_events` and `mart_edit_windows_5min` as external Parquet under `out/marts/`.

TDD note:
- Unit test: a hand-made event sequence gives the expected `is_late` values. Include a late event, an event at exactly the boundary, and a late event that raises `prior_max`.
- dbt test: a full refresh gives the same tables as an incremental run over the same arrivals. Compare row hashes.
- dbt test: every `wiki` joins to `stg_sitematrix_wikis`.

Exit criteria: the unit test and the dbt tests pass.

### Phase 8: Publish and determinism

Goal: every analyst model under `out/marts/`, and repeat runs with no change.

1. Configure the external materialization in `transform/dbt_project.yml`. Each published model writes to `out/marts/<model>/`.
2. `make build` runs the batch ingestion, then `dbt build --select tag:batch`.
3. `make stream` runs the consumer, then `dbt build --select tag:stream`.
4. Run `make build` twice. Compare each file under `out/marts/`. Compare file bytes first. If the bytes differ, compare the table contents instead, and record the reason in `DECISIONS.md`.

Exit criteria: two runs of `make build` give the same outputs.

### Phase 9: Analyst checks and oracle map

Goal: one SQL view or table for each of the seven checks in the spec.

1. Write one dbt model per check under `transform/models/oracle/`. Each reads only `out/marts/`.
2. Write `oracle_map.yml`. For each check, list the model, the table and the columns.
3. Check 3 counts awards by D2 with a negative sum over FY2024.
4. Check 5 groups `fct_recentchange_edits` by wiki and actor type, with the hour of `event_time`.
5. Check 6 reads the window mart for `enwiki`, which is `en.wikipedia.org`, sorted by `edit_count`.
6. Check 7 counts `late_events`.

TDD note: a dbt test per oracle model checks that the model returns rows on the replay data.

Exit criteria: each check returns rows. `oracle_map.yml` names each check.

### Phase 10: Decisions, summary and PR text

Goal: the written record.

1. Write `DECISIONS.md`. It holds D1 to D8, the fallback counts from D2 and D3, and any choice made during the build.
2. Write `outputs/summary.md`.
3. Write `outputs/PR.md`, with the PR title and the body. Run `ste-lint.py` on it.
4. Run a clean verification:
   - `rm -rf lake out`
   - `make build`, then `make build` again, then compare
   - `make stream DURATION=<seconds>` against the replay
   - all dbt tests and the seven checks

Exit criteria: the clean verification passes. The three files exist under `outputs/` and `DECISIONS.md`.

## Acceptance

From the spec, the plan adds these measurable checks.

- `make build` runs without error from raw files. Two runs give the same output.
- `make stream DURATION=<seconds>` runs without error. A restart counts no event twice and loses no event.
- Every model has a documented grain. Every model key has `unique` and `not_null` tests.
- The mart contract is enforced.
- Money sums use `DECIMAL`, not floating point.
- County totals add up to state totals. State totals add up to the source total, for every month.
- The lateness rule uses stream time (D7). No wall clock is used.
- The seven checks return rows. Each check maps to a model in `oracle_map.yml`.
- `pyproject.toml` and `uv.lock` do not change.

## Non-goals

- No BI dashboard.
- No change to the raw files or to the version pins.
- No fiscal years other than FY2024 in the marts.
- No live-endpoint run required for grading. The live URL is a configuration change only, and it is not tested in this plan.
- No commit or PR creation in this phase. The E4 step handles them.

## Reuse and extension

- Reused: the dlt filesystem destination (Parquet), the dbt-duckdb `external` materialization, dbt's built-in `unique`, `not_null` and `relationships` tests, and the existing `Makefile` targets.
- Extension point used: dbt-duckdb `external` materialization for publishing. The plan adds no framework and no new dependency.
- Helper added: the stream consumer uses only the standard library.

## Open decisions for review

1. D1: accept or reject the recipient-county fallback.
2. D6: accept or reject that the edit fact includes late events, with `late_events` as a separate table.
3. D2: accept or reject the award key and its fallback order, after the phase 4 check.

## Next step

`/plan-review .context/plans/gh-1-pipeline_cd-1.plan.md`

---

RUN_BY_COMMAND: plan-update

## Update 2026-10-19 (plan-update, cycle 1)

Source: `.context/reviews/plan_gh-1-pipeline_cd-1.md` (verdict READY WITH CHANGES; MF-1 to MF-5 blocking).
This section amends the phases above. Where an amendment and the original step differ, the amendment wins. The original text is kept above.

### Phase 3 amendments

- **MF-1, stream landing through dlt.** Step 6 is replaced: the consumer hands each micro-batch to a dlt pipeline with the filesystem destination (Parquet). The resource is `recentchange`, the table is `lake/recentchange/`, and `write_disposition="append"`. Dedupe is step 5. The SSE client stays standard library only. Only the landing step uses dlt.
- **MF-2, fields.** Step 6 flattens these fields, and no others are dropped: `meta.id` (as `meta_id`), `meta.dt`, `id` (event id), `timestamp`, `wiki`, `namespace`, `type`, `bot`, `length.old` (as `length_old`), `length.new` (as `length_new`), `revision.old`, `revision.new`, and `arrival_seq`. Staging and the fact read only these columns.
- **N-7, dedupe cost.** Step 5 uses an in-memory set of `meta_id` values. The set is loaded once at startup from the `meta_id` column of `lake/recentchange/`. It is not reloaded per batch.

### Phase 4 amendments

- **N-3.** Step 5: `window_start` follows D7 and Phase 7 (`floor(timestamp / 300) * 300`). Replace "by D5 and the window rule" with "by D7".
- **N-6.** The singular test computes the expected count from the lake with an explicit filter: the number of `lake/usaspending_*` rows whose `action_date_fiscal_year` cast to integer equals 2024. It then compares that number with the row count of the union in `stg_usaspending_transactions`. A pass needs equal counts. No "if any" wording.
- **N-5.** Step 4 parse rule: each top-level key whose name is an integer string is a language object. Other keys (for example `count`, `specials`) are skipped. The language code is the object's `code` field. Each entry in its `site` list gives one row with `dbname` and `url`.

### Phase 6 amendments

- **N-4.** The mart grain stays county. A state per-person value is derived in the check view (Phase 9, check 2 and check 4 support): state net obligations divided by the `POPESTIMATE2024` of the state row (`SUMLEV` 040). It is not a mart column. `DECISIONS.md` records this choice.

### Phase 7 amendments

- No change to steps. The `window_start` rule is D7.

### Phase 8 amendments

- **MF-3, byte-identical determinism.** Step 4 is replaced: compare file bytes under `out/marts/` after two `make build` runs. The files must be byte-identical. There is no content-comparison fallback. If bytes differ, remove the cause: fix the parquet writer settings for the external materialization, and add an explicit `ORDER BY` with a unique tie-break in every published model.
- **N-9.** The Makefile runs `mkdir -p lake out` before the first step of `build` and `stream`.
- **N-2, rollback.** Rollback is `git revert` of the phase commit, plus `rm -rf lake out` to drop generated data.
- **N-1, commit checkpoints.** After each phase exit criteria pass, commit the phase. One commit per phase.

### Phase 9 amendments

- **MF-4, checks 1, 2 and 4 get models.** Each model reads only `out/marts/`. Each has a key test (`unique`, `not_null`) (N-10).
  - `oracle_check1_agency_obligations`: grain is one awarding agency. Net obligations are the sum of `net_obligations` over all months and counties for that `agency_code`. Name comes from `dim_agency`. Key: `agency_code`.
  - `oracle_check2_top_counties_per_person`: grain is one county (not `UNASSIGNED`, population not null). The value is the sum of `net_obligations` over all agencies and months, divided by `population_2024`, as `DECIMAL(20,4)`. Order by value descending, then `county_fips` ascending. Limit 10. Key: `county_fips`.
  - `oracle_check4_reconciliation`: a named view. The month is fixed to `2024-01-01` and is recorded in `DECISIONS.md`. It returns three figures: the source total from `stg_usaspending_transactions` for that month, the sum of county rows, and the sum of state rows. The county and state sums come from `mart_obligations_monthly`. Key: `month_start`. It maps to the Phase 6 step 5 test.
- **MF-5, check 5 scope.** `oracle_check5_stream_hour` filters `fct_recentchange_edits` with `is_edit = true` (D4). The replayed hour is the hour that contains the minimum `event_time` in the lake: `hour_start = floor(min(event_time) / 3600) * 3600`, and the window is `[hour_start, hour_start + 3600)`. Late events are included (the spec says so). The model groups by `wiki` and `actor_type` and returns `edit_count` and `net_bytes`.
- **Check 3.** Groups `stg_usaspending_transactions` for FY2024 by `award_key` (D2), sums the amount as `DECIMAL(20,2)`, and counts the keys where the sum is negative. Key: a single-row model with `award_count`, or a test on the grain key.
- **Check 6.** Reads `mart_edit_windows_5min` for `enwiki` (`en.wikipedia.org`), on-time edits only. Order by `edit_count` descending, then `window_start` ascending, then `namespace` and `actor_type` ascending. Limit 10. The limit and the tie-break go into `DECISIONS.md`.
- **Check 7.** Counts rows of `late_events`. Key: a single-row model with `late_count`.
- **N-10.** Each oracle model has a key test on its grain key.
- The `oracle_map.yml` entry names all seven checks, each with its model and columns.

### Carried findings

None. This is cycle 1. The review's notes N-1 to N-10 are applied above, except where listed as recorded in `DECISIONS.md`.

## Next step after this update

`/plan-review .context/plans/gh-1-pipeline_cd-1.plan.md`

---

RUN_BY_COMMAND: plan-update

## Update 2026-10-19 (plan-update, cycle 2)

Source: `.context/reviews/plan_gh-1-pipeline_cd-1.md` (cycle 2 of 5, verdict READY WITH CHANGES). MF-6 to MF-10 are blocking.
This section amends the phases above. Where an amendment and the original step differ, the amendment wins. The earlier text stays.

### Published set (MF-6)

Downstream reads only `out/marts/`. A model is published when it appears in this list. Phase 8 writes each listed model to `out/marts/<model>/`.

- Batch: `fct_award_transactions`, `dim_agency`, `dim_place`, `dim_date`, `dim_state`, `mart_obligations_monthly`.
- Stream: `fct_recentchange_edits`, `late_events`, `mart_edit_windows_5min`.
- Oracle: each `oracle_*` model in Phase 9.

Staging models (`stg_*`) are not published. Each oracle model reads only models in this list.

### Phase 2 amendments

- **N-12.** Step 4 applies the N-5 parse rule. Step 4 parses the language objects and writes one row per `dbname`.
- **N-16.** One helper, `pipeline/landing.py`, writes Parquet through dlt. The five batch resources and the stream landing call it. The helper takes the resource name and the `write_disposition` as arguments. E1 writes the helper once.

### Phase 3 amendments

- **MF-10, reference set for the no-loss test.** A relay helper, `pipeline/replay_relay.py`, is a test helper. It uses the standard library only. It sits between the consumer and the replay URL, forwards each SSE line, and logs the `meta.id` of each `data:` line it forwards. The log covers all connections in one run.
- The reference set is the set of unique `meta.id` values in that log.
- A pass needs three results. The landed `meta_id` set equals the reference set (no loss). No `meta_id` appears twice in the lake (no double count). `arrival_seq` has no gap.
- The relay runs in the 20-second restart test and in the SIGKILL test.
- The first Phase 3 test checks whether the replay honours `Last-Event-ID`. If the replay does not resend lost events, the SIGKILL test fails. E1 records this in `DECISIONS.md` and does not mark Phase 3 complete. E1 does not weaken the reference set.

### Phase 4 amendments

- **N-15, null keys.** Rows with a null `award_key` are excluded from every grouping by `award_key`. They do not form a group. The Phase 4 blank-key count records the number of these rows in `DECISIONS.md`.

### Phase 5 amendments

- **MF-6, MF-9, state fields.** `fct_award_transactions` adds the column `state_fips`. It takes the place of performance state (D1 rule 1).
- **MF-9, new dimension.** `dim_state` is a new published dimension. Its grain is one state, from the state rows (`SUMLEV` 040). Columns: `state_fips`, `state_code`, `population_2024`. D3 applies to the state rows, with the same 2021 fallback.

### Phase 6 amendments

- **MF-9, state totals source.** Step 5 reconciliation reads three sources. County sums come from `mart_obligations_monthly`. State sums come from `fct_award_transactions`, grouped by `state_fips` and month. The source total comes from `fct_award_transactions` for each month.
- The state sums do not add county rows. The county-to-state comparison can fail.

### Phase 7 amendments

- **MF-7, incremental publish.** `fct_recentchange_edits` and `mart_edit_windows_5min` keep incremental materialization. Neither uses the `external` materialization.
- Each incremental model has a `post_hook` that writes its Parquet file. The hook runs `COPY (SELECT * FROM {{ this }} ORDER BY <key>) TO 'out/marts/<model>/<model>.parquet' (FORMAT PARQUET)`. The key is `meta_id` for the fact. The key is `window_start, wiki, namespace, actor_type` for the window mart.
- The Makefile creates each `out/marts/<model>/` directory before dbt runs. See Phase 8.
- If the `post_hook` does not work, E1 runs the same `COPY` from one Python step in `pipeline/` after `dbt build`. E1 records the choice in `DECISIONS.md`.
- The result that must hold has three parts. After each incremental run, the Parquet file has the same rows as the model table (compare sorted row hashes). A full refresh (`dbt run --full-refresh`) gives the same rows as an incremental run over the same arrivals. The Parquet bytes are the same across two runs of the same input.
- **MF-8, edit counts.** Step 3 counts only rows with `is_edit = true` and `is_late = false`. `edit_count` counts these rows. `net_bytes_added` sums `net_bytes` over these rows. Rows of type `log` and `categorize` add to neither value. Late rows add to neither value.
- Step 1 and step 2 do not change. Step 4 is replaced by the `post_hook` above.

### Phase 8 amendments

- **MF-6, publish list.** Step 1 is replaced. The `external` materialization writes each model in the Published set to `out/marts/<model>/`, except the two incremental models in Phase 7. Those two use their `post_hook`.
- The Makefile runs `mkdir -p lake out out/marts` and creates each `out/marts/<model>/` directory before the first dbt step.
- **N-17.** The byte check covers batch files only. Stream files come from `make stream`, which this check does not repeat. `DECISIONS.md` records this.
- The rest of Phase 8 is unchanged, including MF-3 and N-1 and N-2.

### Phase 9 amendments

- **MF-6.** Each oracle model reads only models in the Published set.
- **Check 1.** Unchanged. The name comes from `dim_agency`, which is published.
- **Check 2 and state view (N-4, MF-9).** `oracle_state_per_person` is a new model. Its grain is one state. Net obligations are the sum of `federal_action_obligation` over FY2024, grouped by `state_fips`. The population is `dim_state.population_2024`. The value is net obligations divided by population, as `DECIMAL(20,4)`. The value is null when the population is null. Key: `state_fips`. Check 2 reports these state values next to its county rows.
- **Check 3.** Reads `fct_award_transactions`. Groups the FY2024 rows by `award_key` (D2) and excludes null keys (N-15). Counts the keys whose sum is negative. The model returns one row named `award_count`. The key test is `not_null` on `award_count` (N-14).
- **Check 4.** Reads three sources as listed in Phase 6. The model is a named view, with month `2024-01-01`. Columns: `source_total`, `county_total`, `state_total`. Key: `month_start`.
- **Check 5 (N-13).** Reads `fct_recentchange_edits` with `is_edit = true`. The check reads one hour only, as stated in MF-5. `DECISIONS.md` records the hour, the number of events outside the hour, and this rule.
- **Check 6.** Unchanged. Reads `mart_edit_windows_5min` for `enwiki`, on-time edits only.
- **Check 7 (N-14).** Single row, `late_count`. The key test is `not_null` on `late_count`.
- **N-10.** Each oracle model has a key test on its grain key, or `not_null` on the count column when the model has one row.
- `oracle_map.yml` names each check and each model, including `oracle_state_per_person` under check 2.

### Reuse and extension (N-16 and MF-10)

- Helper added: `pipeline/landing.py`, one Parquet landing helper for the batch resources and the stream. It uses dlt.
- Helper added: `pipeline/replay_relay.py`, a test relay. It uses the standard library only. It is not part of the production run.

### DECISIONS.md additions

`DECISIONS.md` records these items in addition to D1 to D8:

- The number of null award keys (N-15).
- The state totals source and the state view (MF-9).
- The incremental publish mechanism and any fallback (MF-7).
- The no-loss reference and the replay result for `Last-Event-ID` (MF-10).
- The check 5 hour rule (N-13).
- The stream byte-check scope (N-17).

### Carried findings

None. This is cycle 2 of 5. The orchestrator runs `/plan-review` next.

### Next step after this update

`/plan-review .context/plans/gh-1-pipeline_cd-1.plan.md`

---

RUN_BY_COMMAND: plan-update

## Update 2026-10-19 (plan-update, cycle 3)

Source: `.context/reviews/plan_gh-1-pipeline_cd-1.md` (cycle 3 of 5, verdict READY WITH CHANGES). MF-11 to MF-14 are blocking.
This section amends the phases above. Where an amendment and the original step differ, the amendment wins. The earlier text stays.

### Phase 2 amendments (MF-11, comparison rule)

- The Phase 2 exit criterion "same file list" is replaced. The dlt default layout `{table_name}/{load_id}.{file_id}.{ext}` puts a new `load_id` in each file name on each run. File names therefore differ between runs.
- New rule: two runs of `make build` give the same set of lake table names and the same row content for each lake table. Compare the sorted row hashes of each table under `lake/`. File names and file bytes under `lake/` are not compared.
- The Phase 8 byte check covers `out/marts/` only. It does not use this rule.

### Award identity (MF-12)

- D2 is replaced. An award is the pair (`awarding_agency_code`, `award_key`). `award_key` is the prime award key within that agency. Assistance uses `award_id_fain`, or `award_id_uri` when FAIN is blank. Contracts use `award_id_piid`. The fallback order stays deferred to the phase 4 check.
- Phase 4 step 1: `stg_usaspending_transactions` keeps `awarding_agency_code`. Every grouping by award uses the pair, not `award_key` alone.
- Phase 5 step 1: `fct_award_transactions` adds the columns `awarding_agency_code` and `award_key`.
- A row is excluded from every award grouping when `award_key` or `awarding_agency_code` is null. This applies N-15 to the pair. The phase 4 blank-key count reports the rows excluded for each null column.
- Phase 9 check 3 is replaced. The check reads `fct_award_transactions`, groups the FY2024 rows by (`awarding_agency_code`, `award_key`), excludes null pairs, and counts the pairs whose sum is negative. It returns one row named `award_count`. The key test is `not_null` on `award_count` (N-14).

### Check 6 ranks windows (MF-13)

- Phase 9 check 6 is replaced. The check ranks 5-minute windows, as the spec asks. It does not rank mart slices.
- The check reads `mart_edit_windows_5min` for `enwiki` (`en.wikipedia.org`). The mart holds on-time edits only (D6).
- The check sums `edit_count` and `net_bytes_added` over namespace and actor type for each `window_start`. It then orders the windows by the summed `edit_count` descending, then `window_start` ascending. Limit 10.
- Output columns: `window_start`, `edit_count`, `net_bytes_added`. Key: `window_start`, with `unique` and `not_null` tests (N-10).
- The summing rule and the tie-break go into `DECISIONS.md`.

### Phase 3 outcome when the replay does not honour `Last-Event-ID` (MF-14)

- This applies when the first Phase 3 test shows that the replay does not resend lost events. It extends the MF-10 text. The rule "E1 does not mark Phase 3 complete" stays.
- The run stops at Phase 3. It does not start Phase 4. Phase 10 is not run on this path, so `outputs/PR.md` is not written.
- The SIGKILL test fails. The test writes the lost `meta_id` values: the reference set minus the landed `meta_id` set, with the count.
- E1 writes the gap to `DECISIONS.md`, under the no-loss entry. The entry holds the replay result for `Last-Event-ID`, the size of the reference set, the size of the landed set, and the count of lost `meta_id` values.
- E1 writes `outputs/summary.md` at the halt. The file names the gap as an open decision. It names two choices for the user: a replay that honours `Last-Event-ID`, or a spec change that accepts a loss. E1 makes neither choice.
- E1 does not change the reference set. E1 does not change the no-loss rule. E1 does not count the SIGKILL test as passed.

### Carried findings

None. This is cycle 3 of 5. The orchestrator runs `/plan-review` next.

### Next step after this update

`/plan-review .context/plans/gh-1-pipeline_cd-1.plan.md`

---

RUN_BY_COMMAND: plan-update

## Update 2026-10-19 (plan-update, cycle 4)

Source: `.context/reviews/plan_gh-1-pipeline_cd-1.md` (review 4 of 5, verdict READY WITH CHANGES). MF-15 and MF-16 are blocking. Notes N-18 to N-28 are applied below.
This section amends the phases above. Where an amendment and the original step differ, the amendment wins. The earlier text stays.

### Phase 2 amendments

- **MF-15, comparison scope.** The cycle 3 comparison rule covers five batch resources only: `usaspending_assistance`, `usaspending_contracts`, `census_county_2024`, `census_county_2021` and `sitematrix`. The stream table `lake/recentchange/` is not compared.
- **MF-15, row hash.** The row hash covers the source columns only. It excludes every `_dlt_*` column.
- **MF-15, metadata tables.** The comparison does not read any `_dlt_*` table, including `_dlt_loads`.
- **N-27, partitioning.** E1 sets the dlt filesystem destination to partition each USAspending table by `awarding_agency_code`. The partition column is an argument of `pipeline/landing.py` (N-16). E1 names the dlt setting in `DECISIONS.md`. After the first `make build`, E1 checks that one folder exists for each partition value. If the destination cannot partition by this column, E1 removes the partition claim from Phase 2 and records the removal in `DECISIONS.md`.

### Phase 3 amendments

- **MF-16, halt output.** This amends the MF-14 halt path. The sentence "Phase 10 is not run on this path, so `outputs/PR.md` is not written" is replaced. Phase 10 still does not run.
- E1 writes `outputs/PR.md`. The title and body name the halt at Phase 3, name the gap (the lost `meta_id` count and the `Last-Event-ID` result), and state that the PR is not ready.
- E1 runs `ste-lint.py` on `outputs/PR.md`.
- E1 creates `DECISIONS.md` with the no-loss entry. Phase 10 does not run on this path, so the file does not exist otherwise.
- The rest of MF-14 stays as written.

### Phase 6 amendments

- **N-28, population description.** The mart YAML description of `population_2024` and the `dim_state` YAML description of `population_2024` both state the fallback. The value is the 2024 estimate. Where no 2024 estimate exists, the value is the 2021 estimate (D3).

### Phase 7 amendments

- **N-20, step 4 replaced.** Step 4 is replaced. `fct_recentchange_edits`, `late_events` and `mart_edit_windows_5min` are published under `out/marts/` by the MF-7 `post_hook`. The words "as external Parquet" are void. Neither model uses the external materialization.
- **N-23, fact filter.** `fct_recentchange_edits` keeps `unique_key = meta_id`. Its incremental filter is `where arrival_seq > (select coalesce(max(arrival_seq), 0) from {{ this }})`.
- **N-23, window mart key and filter.** `mart_edit_windows_5min` uses the composite `unique_key` of `window_start, wiki, namespace, actor_type`. Its incremental run rebuilds every window that holds a fact row with `arrival_seq` above the watermark. The watermark is the largest `arrival_seq` that the last window-mart run read. E1 stores the watermark in a one-row table, `window_watermark`, under `transform/models/`. The table is tagged `stream` and is not published. Each rebuilt window is recomputed from the full fact table with the MF-8 filters. A late flag does not change when later events arrive, because a late flag depends only on earlier arrivals. So a rebuilt window stays correct.

### Phase 8 amendments

- No change in this update.

### Phase 9 amendments

- **N-18, tags.** Each oracle model carries one tag. Checks 1 to 4 carry `batch`. Checks 5 to 7 carry `stream`. No `batch` model reads a stream model.
- **N-21, check 4 output.** Check 4 adds two boolean columns: `county_matches_source` (true when the county total equals the source total) and `state_matches_source` (true when the state total equals the source total). The analyst reads these columns as the pass or fail result of each comparison. Key: `month_start`.
- **N-22.** Closed. The hour rule is recorded in `DECISIONS.md` under N-13.

### Quality gates amendments

- **N-19, replay.** The operator starts the replay on `localhost:8099` before any Phase 3 integration test. E1 does not start it. The integration tests live in `pipeline/integration_stream_test.py`. When the replay is down, the integration test fails with a connection error. It does not skip.
- **N-19, gate.** Add this command to the quality gates list: `uv run python -m unittest discover -s pipeline -p "integration_stream_test.py"`, with the replay running. The unit gate pattern `test_*.py` does not match this file, so the unit gate runs without the replay.

### Non-goals amendment (N-24)

- The non-goal "No commit or PR creation in this phase" applies to the PR only. E1 commits each phase after its exit criteria pass (N-1). E1 does not open a PR. E4 opens the PR.

### Reuse and extension (N-25)

- The `COPY` post-hook appears in two models: the fact and the window mart. The Rule of Three is not met. Each model keeps its own `post_hook`. If a third model needs the publish, E1 moves the `COPY` into a dbt macro at `transform/macros/publish_parquet.sql`, and adds that file to the blast radius.

### Blast radius (N-26)

- Created, added: `transform/tests/` (the singular tests of Phase 4, Phase 6 and Phase 7), `transform/models/` file for `window_watermark` (Phase 7), and `pipeline/integration_stream_test.py` (Phase 3).
- Created, conditional: `transform/macros/publish_parquet.sql`, only if N-25 is triggered.

### Carried findings

- MF-15: applied (Phase 2 amendments).
- MF-16: applied (Phase 3 amendments).
- N-18 to N-22: applied or closed above.
- N-23 to N-28: applied above.
- No must-fix item is open. This is cycle 4 of 5. The next review is review 5 of 5.

### Next step after this update

`/plan-review .context/plans/gh-1-pipeline_cd-1.plan.md`

---

RUN_BY_COMMAND: plan-update

## Update 2026-10-19 (plan-update, cycle 5, last update)

Source: `.context/reviews/plan_gh-1-pipeline_cd-1.md` (review 5 of 5, verdict READY WITH CHANGES). MF-17, MF-18 and MF-19 are blocking. Notes N-29 to N-33 are applied below.
This is the last plan-update in the loop. This update requests no further review. The gate checks the carried ids in `## Carried review findings`.
This section amends the phases above. Where an amendment and the original step differ, the amendment wins. The earlier text stays.

### Phase 4 amendments (N-29)

- Step 3, `stg_census_state`, also carries `population_2021`. It comes from the state rows (`SUMLEV` 040) of `lake/census_county_2021/`. Phase 5 `dim_state` takes its D3 fallback from this column.

### Phase 7 amendments (MF-17, window mart contract)

- `mart_edit_windows_5min` has a dbt model contract in its YAML (`contract: enforced: true`). The contract names these columns and types:
  - `window_start` TIMESTAMP
  - `wiki` VARCHAR
  - `namespace` INTEGER
  - `actor_type` VARCHAR
  - `edit_count` BIGINT
  - `net_bytes_added` BIGINT
- The Phase 7 exit criteria include `uv run dbt build --project-dir transform --profiles-dir transform --select mart_edit_windows_5min` with the contract enforced.

### Phase 7 amendments (MF-18, watermark write path)

This replaces the watermark storage text in N-23. The rest of N-23 stands.

- The write path is a `post_hook` on `mart_edit_windows_5min`. No dbt model file exists for the watermark.
- The watermark is a one-row table, `window_watermark`, in the same schema as the window mart. Its column is `watermark_arrival_seq`.
- The window mart's incremental filter reads the prior value from `window_watermark` at the start of the run. The filter runs only when `is_incremental()` is true. On the first run and on a full refresh, every window is built.
- The `post_hook` writes the value that the run read from the fact:
  `CREATE OR REPLACE TABLE {{ this.schema }}.window_watermark AS SELECT coalesce(max(arrival_seq), 0) AS watermark_arrival_seq FROM {{ ref('fct_recentchange_edits') }}`.
  The fact builds earlier in the same `dbt build`. No writer runs between the two models. So the value equals the largest `arrival_seq` that the window run read.
- After a full refresh, the watermark is the largest `arrival_seq` of the fact. For an empty fact, the watermark is 0.
- The rebuild set is the set of windows that hold a fact row with `arrival_seq` above the prior watermark. Each window in the set is recomputed from the full fact with the MF-8 filters. The rows then merge on `window_start, wiki, namespace, actor_type`.
- Blast radius: drop the `transform/models/` file for `window_watermark`. The table is not published and has no dbt tag.

### Phase 7 amendments (MF-19, publish mechanism)

- The `post_hook` `COPY` path stays for `fct_recentchange_edits`, `late_events` and `mart_edit_windows_5min`. This is the second option in MF-19. The `external` materialization is not used for these three models.
- Reason, for the `DECISIONS.md` entry: the spec asks for the `external` materialization. The two stream marts keep state between runs in their DuckDB tables: the fact watermark and the window merge. The `post_hook` `COPY` writes the Parquet file from that table after each run. The entry names this reason and the test below.

### Phase 7 amendments (exit test, MF-18 and MF-19)

This replaces the general full-refresh statement in the Phase 7 TDD note.

1. Land arrival batch 1 in `lake/recentchange/`. Run `dbt build --select tag:stream`.
2. Land arrival batch 2. Run `dbt build --select tag:stream`.
3. On the same lake, run `dbt run --full-refresh --select fct_recentchange_edits late_events mart_edit_windows_5min`.
4. Compare the sorted row hashes of the two incremental outputs with the full-refresh outputs. The Parquet bytes under `out/marts/` must match too.
5. Check that `window_watermark` equals the largest `arrival_seq` of the fact after step 2.

Phase 7 exit criteria: the unit test, the dbt tests, the contract build in MF-17, and steps 1 to 5 above all pass.

### Phase 6 amendments (contract scope)

- The Phase 6 contract stays for `mart_obligations_monthly`. The acceptance line now covers both marts (see Acceptance amendments).

### Phase 9 amendments (N-31, check 5 hour source)

- The minimum `event_time` for the replayed hour is read from `fct_recentchange_edits`, not from `lake/recentchange`. The `DECISIONS.md` hour entry (N-13) names this source.

### Quality gates amendments (N-30, import path)

- `pipeline/` is a package. E1 creates `pipeline/__init__.py`.
- Both test gates run with `-t .`, so that `pipeline.landing` and `pipeline.replay_relay` import:
  - `uv run python -m unittest discover -s pipeline -t . -p "test_*.py"`
  - `uv run python -m unittest discover -s pipeline -t . -p "integration_stream_test.py"`

### Acceptance amendments

- Replace "The mart contract is enforced." with: "The mart contracts are enforced for `mart_obligations_monthly` and `mart_edit_windows_5min`."
- Add: "The two stream marts and `late_events` equal a full refresh over the same two arrival batches, and the published Parquet bytes match."

### DECISIONS.md additions

These entries join the list above:

- MF-18: the watermark write path, the first-run and full-refresh values, and the first-run rule.
- MF-19: the publish mechanism for the stream marts, the reason for the departure from `external`, and the Phase 7 exit test that shows the outputs match.
- N-32 (halt path, Phase 3): reconnect with `meta.id` dedupe prevents a double count. It does not recover events that the replay does not resend. So the halt stays. E1 writes this reason when the halt runs.
- N-33: D4 is a spec reading. The spec's "fact table of edits" holds every change event type, as D4 states.

### Reuse and extension and blast radius (cycle 5)

- The `transform/models/` file for `window_watermark` is removed (MF-18).
- `transform/macros/publish_parquet.sql` stays conditional (N-25).

### Carried review findings

- **MF-17 (window mart contract).** Open. Text applied in this update (Phase 7 amendments, MF-17). Settled by the Phase 7 contract build for `mart_edit_windows_5min`.
- **MF-18 (watermark write path).** Open. Text applied in this update (Phase 7 amendments, MF-18). Settled by the Phase 7 exit test, steps 1 to 5. Step 5 checks the watermark value.
- **MF-19 (publish mechanism).** Open. Text applied in this update (Phase 7 amendments, MF-19, and the DECISIONS.md entry). Settled by the Phase 7 exit test, step 4, which compares the Parquet bytes.
- N-29 to N-33: applied in this update. Not blocking.

### Next step after this update

No further review is requested. The gate checks the carried ids against `## Carried review findings`. Phase 3 is the first implementation phase, under the TDD gate.

---

RUN_BY_COMMAND: plan-update

## Update 2026-10-19 (plan-update, cycle 5, carried findings heading)

Source: `.context/reviews/plan_gh-1-pipeline_cd-1.md` (review 5 of 5, verdict READY WITH CHANGES).
The cycle 5 update above applies MF-17, MF-18 and MF-19. This section changes only the heading level of the carried findings. The plan gate reads the heading `## Carried review findings` with two hash marks. The cycle 5 heading had three hash marks, so the gate did not find it.
This update requests no further review.

## Carried review findings

Each open must-fix maps to the Phase 7 test that settles it.

- **MF-17 (window mart contract). Open.** Phase: 7. Settled by the Phase 7 contract build: `uv run dbt build --project-dir transform --profiles-dir transform --select mart_edit_windows_5min`, with `contract: enforced: true` in the YAML.
- **MF-18 (watermark write path). Open.** Phase: 7. Settled by the Phase 7 exit test, steps 1 to 5. Step 5 checks that `window_watermark` equals the largest `arrival_seq` of the fact.
- **MF-19 (publish mechanism). Open.** Phase: 7. Settled by the Phase 7 exit test, step 4 (Parquet bytes match a full refresh), and by the `DECISIONS.md` entry for the `post_hook` path.
- N-29 to N-33: applied in the cycle 5 update. Not blocking.

---

RUN_BY_COMMAND: plan-update

## Update 2026-10-19 (plan-update, carry-only, after review 5 of 5)

Source: `.context/reviews/plan_gh-1-pipeline_cd-1.md` (review 5 of 5, verdict READY WITH CHANGES). This is a carry-only update. P3 is at its limit, so no review is requested.
MF-17, MF-18 and MF-19 text was applied in the cycle 5 updates above. This update maps them to the phase that settles them. It also fixes one gap in the MF-19 test.

### Phase 7 amendments (MF-19, comparison inputs)

- Step 4 of the Phase 7 exit test compares two sets of outputs. Step 3 overwrites `out/marts/` through the `post_hook` `COPY`. Before step 3 runs, copy the step 2 outputs of `fct_recentchange_edits`, `late_events` and `mart_edit_windows_5min` to `out/check/incremental/<model>.parquet`. Then run step 3. Step 4 compares those copies with the full-refresh files in `out/marts/`.
- The copies are the incremental outputs. Without them, step 4 compares the full refresh with itself.

## Carried review findings

Each open must-fix maps to the Phase 7 test that settles it.

- **MF-17 (window mart contract). Open.** Phase: 7. Settled by the Phase 7 contract build: `uv run dbt build --project-dir transform --profiles-dir transform --select mart_edit_windows_5min`, with `contract: enforced: true` in the YAML.
- **MF-18 (watermark write path). Open.** Phase: 7. Settled by the Phase 7 exit test, steps 1 to 5. Step 5 checks that `window_watermark` equals the largest `arrival_seq` of the fact.
- **MF-19 (publish mechanism). Open.** Phase: 7. Settled by the Phase 7 exit test, step 4 (Parquet bytes match a full refresh, using the copies from the amendment above), and by the `DECISIONS.md` entry for the `post_hook` path.
- N-29 to N-33: applied in the cycle 5 updates. Not blocking.

### Next step after this update

No further review is requested. The gate checks the carried ids against `## Carried review findings`.
