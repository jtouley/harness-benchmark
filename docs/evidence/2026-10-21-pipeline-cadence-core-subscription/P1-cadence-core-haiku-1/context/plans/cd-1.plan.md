RUN_BY_COMMAND: plan-create

# Plan: cd-1 open data pipeline (batch federal money, Wikipedia edit stream)

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
**Task token:** cd-1 (the packet argument; file names and the register use it)
**Branch:** feature/gh-1-pipeline (the `gh-1` in the request is the GitHub issue reference for the PR, not the Cadence token)
**Pipeline-Run:** 81d6f968-0843-449a-b3ac-e0fffa47a255

Inputs (pinned by the packet):
- `.context/proposals/cd-1.md` sha256 d9d6fd011b66b3ab66fbc072fe01d5be685da0267321151131d0abf4c48a2883
- `.context/vibetest/cd-1_2026-10-21.md` sha256 3febdc71ca850fa5ea5f9ef4992acf32d6013de8d79511c8b28611524f6bac87

The vibe-test verdict is **NOT READY FOR PLANNING** with blocking gaps G-1 to G-5. This plan does not
wait for answers. Each blocking gap is turned into an assumption in
`.context/deferrals/cd-1_deferral-register.md`. Each assumption is built in a named phase and recorded in
`.context/proposals/cd-1-*.md`. A reviewer or the owner can overturn an assumption; the cost is the phase
named in the register.

## Step 0: problem, design, blast radius, acceptance

### Problem

Build one repository that answers two analyst questions from raw public data:

- A (batch): FY2024 federal contract and grant money, in total and per resident, by state, county,
  awarding agency and month. Source: USAspending FY2024 prime transactions for agencies 417, 418, 474, 485
  (assistance and contracts files), Census county estimates, Wikimedia site matrix.
- B (stream): Wikipedia edits per wiki, namespace and 5-minute window, split human and bot, with net
  bytes. Source: Wikimedia EventStreams `recentchange` over SSE (replay at `http://localhost:8099`).

Flow: raw files and stream -> Parquet lake (`lake/`, dlt) -> dbt-duckdb models (`transform/`) ->
published Parquet marts (`out/marts/`, dbt external materialization).

### Challenges to the spec (written into the plan, not silently accepted)

1. The spec has no answer for G-1 to G-5. The plan picks answers (see the register). Each pick is a
   decision record, so P3 and the adversarial review can attack it.
2. The stream dedupe depends on the replay server. The replay may or may not honor `Last-Event-ID`. The
   plan does not depend on it: dedupe by `meta.id` against the lake makes replays harmless either way.
   The live URL (`stream.wikimedia.org`) is not tested here. That is the residual risk of G-1.
3. "Per person" in the monthly mart repeats the population on each month row. Per-person values are
   additive only in the FY sums, so the FY check (check 2) computes per person from FY sums, not from
   summed monthly ratios.
4. The packet says the task id is `gh-1`, the request file says `cd-1`. The plan uses `cd-1` for every
   Cadence artifact. The PR and branch keep `gh-1`.
5. The spec asks for dlt. The stdlib `urllib` is used for SSE, so no new dependency is added. The pins
   in `pyproject.toml` stay as they are (spec rule).

### Design decisions (each has a decision record in `.context/proposals/`)

| Decision | Record | Settles |
|---|---|---|
| Stream dedupe key is `meta.id`; the lake is the state; `Last-Event-ID` is a hint | `cd-1-stream-dedupe-resume` | G-1 |
| Watermark is the running max of event time over all first arrivals, kept in `fct_edit`; `arrival_seq` set at first landing | `cd-1-stream-lateness-watermark` | G-2 |
| Award key `generated_unique_award_id`; net obligation summed per award over FY2024, then the sign test | `cd-1-award-key-and-sign` | G-3 |
| Place means place of performance; rows without a state or county go to explicit unplaced members | `cd-1-place-and-unplaced` | G-4 |
| Publish every table analysts query (facts, dimensions, late_events) under `out/marts/`; oracle map points only there | `cd-1-publication-scope` | G-5, C-1 |
| Money is DECIMAL(18,2); per-person ratio is DECIMAL(18,4); no DOUBLE anywhere | `cd-1-money-type` | G-7 |
| Population: join on 5-digit FIPS, 2024 estimate July 1 2024, fallback to 2021 vintage estimate for absent keys | `cd-1-population-fallback` | G-12 |
| Batch raw sources use `replace`; stream uses append with dedupe; marts overwrite | `cd-1-write-disposition` | G-13 |
| Stream field rules: missing length gives 0 bytes and `has_length=false`; missing bot flag gives `human`; wiki key is `dbname` joined from the site matrix | `cd-1-stream-field-rules` | G-8, G-9, G-10, G-11 |
| Stream code uses stdlib only; tests are `unittest` and dbt unit tests | `cd-1-stream-tooling` | dependency choice |
| `make build` = batch only; `make stream` = consumer + stream models | `cd-1-make-target-split` | blast radius of rebuilds |

### Blast radius

- New: `pipeline/` (Python, dlt and SSE), `transform/models/**`, `transform/seeds/` (state codes),
  `transform/tests` or yml unit tests, `tests/` (unittest), `oracle_map.yml`, `DECISIONS.md`.
- Changed: `Makefile` (targets `build` and `stream` are stubs now), `transform/dbt_project.yml`
  (materialization and tags).
- Not changed: `pyproject.toml` pins, `uv.lock`, the raw data, the `.gitignore` lines for `lake/` and `out/`.
- Gated paths (`.cadence.json`): `pipeline/`, `transform/`, `Makefile` will trigger the E1 gates. That is intended.

### Acceptance (the run is done when all hold)

1. `make build` runs twice from a clean `lake/` and `out/`. Row content of every mart and every lake
   table is identical after the second run (compare by content hash, not file bytes).
2. `make stream DURATION=<s>` runs twice in two halves, and once unbroken on the same replay. The edit
   counts and net bytes per wiki, namespace, actor type are identical in both cases. No `meta.id` appears
   twice in `fct_edit`.
3. All seven checks in `oracle_map.yml` resolve to objects in `out/marts/` only, and each check returns
   a result that matches the independent Python computation in `tests/`.
4. `uv run dbt test` passes, including the key tests on every model and the unit tests for the late rule
   (S4 and S5 from the vibe test).
5. `DECISIONS.md` lists each choice, each assumption outcome, and each non-blocking gap with its answer.

## Quality gates (real commands from this repo)

- Environment: `uv sync --frozen` (uses `uv.lock`, Python 3.12 from `.python-version`).
- Batch: `make build` (after Phase 2 it runs `uv run python -m pipeline.batch_ingest` and then
  `uv run dbt build --project-dir transform --profiles-dir transform --exclude tag:stream`).
- Stream: `make stream DURATION=<seconds>` (runs `uv run python -m pipeline.stream_consume --duration $(DURATION)`
  and then `uv run dbt build --project-dir transform --profiles-dir transform --select tag:stream`).
- Models and tests: `uv run dbt test --project-dir transform --profiles-dir transform`.
- Python tests: `uv run python -m unittest discover -s tests -v`. No pytest (not pinned).
- Contract check: `uv run dbt parse --project-dir transform --profiles-dir transform` must succeed after
  every phase that changes a yml contract.

The `Makefile` targets are stubs now (`exit 1`). Phase 1 replaces them. Do not add make targets that the
Makefile does not call.

## Reuse and extension

- Reused existing pieces: `pyproject.toml` (dlt 1.31.0, dbt-core 1.11.6, dbt-duckdb 1.11.0, duckdb 1.5.6);
  `transform/profiles.yml` (profile `open_data_pipeline`, DuckDB at `out/warehouse.duckdb`);
  `transform/dbt_project.yml` (model paths); the `Makefile` targets `build` and `stream`;
  `.gitignore` entries for `lake/` and `out/`.
- Extension point added: the dbt layers `staging` -> `core` (star and stream facts) -> `marts`
  (published externally), selected by tags `batch` and `stream`. Each new model joins one layer.
- Extension point added: `pipeline/` is one Python package with one module per source (`batch_ingest`,
  `stream_consume`). A new source adds a module, not a new entry point.
- No helper is copied from elsewhere. The SSE reader and the Census fallback are new code in `pipeline/`.

## Layout after the run

```
lake/
  usaspending_assistance/   (dlt parquet, replace)
  usaspending_contracts/    (dlt parquet, replace)
  census_county_2024/       (dlt parquet, replace)
  census_county_2021/       (dlt parquet, replace)
  sitematrix/               (dlt parquet, replace)
  recentchange/             (dlt parquet, append; one file per consumer flush; carries meta.id and arrival_seq)
  _stream_cursor.json       (last SSE id; a hint only)
out/
  warehouse.duckdb          (dbt dev target; holds incremental state)
  marts/<mart>/<mart>.parquet  (one folder per published table)
transform/models/
  staging/  core/  marts/  stream/
transform/seeds/state_codes.csv  (USPS abbreviation, state FIPS, state name)
pipeline/batch_ingest.py  pipeline/stream_consume.py  pipeline/sse.py
tests/  oracle_map.yml  DECISIONS.md
```

## Phases

Registry order. Each phase ends with a commit. Each phase has a `Phase N` commit subject
(`phase N: <title>`).

### Phase 1: Wiring, state codes and the Makefile

Goal: the repo builds and parses with no data logic yet.

- Replace the `Makefile` stubs with the commands in the quality gates section. Keep `build` and `stream`
  names.
- Add `transform/seeds/state_codes.csv` with the 50 states, DC and the inhabited territories: USPS code,
  2-digit state FIPS, name. Source of the FIPS values: the state rows of the 2024 Census file
  (`COUNTY = 000`), checked against the names.
- Update `transform/dbt_project.yml`: `staging` as views, `core` as tables, `marts` as external
  (dbt-duckdb `external` materialization, `external_location: out/marts/{{ this.name }}/{{ this.name }}.parquet`),
  tags `batch` and `stream` per folder.
- Add `DECISIONS.md` with a heading per record in `.context/proposals/cd-1-*.md`.

TDD note: write `tests/test_wiring.py` first. It asserts that `make -n build` and `make -n stream` no
longer print "not implemented", that `state_codes.csv` has one row per state FIPS value in the 2024 Census
file's state rows, and that no dependency pin in `pyproject.toml` changed (compare with `git show main:pyproject.toml`).
Run it red on the stubs, then make it green.

Exit criteria:
- `uv run dbt debug --project-dir transform --profiles-dir transform` reports the connection ok.
- `make build` exits 0 with no models and no data.
- `uv run python -m unittest tests.test_wiring -v` passes.
- The seed row count equals the number of state rows in `co-est2024-alldata.csv` (`COUNTY = 000`), read from the file.
- `make stream` against an unreachable URL is not a Phase 1 check; it is covered in Phase 5.

### Phase 2: Batch ingestion with dlt (raw to lake)

Goal: every raw input lands in `lake/` with its source columns and load metadata only.

- `pipeline/batch_ingest.py`: dlt resources, filesystem destination with Parquet, `write_disposition="replace"`
  (record `cd-1-write-disposition`).
- USAspending: for each of the 8 assistance and 8 contracts zips under `data/raw/usaspending/`, read the
  single CSV inside the zip with the stdlib `zipfile` and `csv` module. Land one dlt table per family:
  `usaspending_assistance`, `usaspending_contracts`. Add a column `source_file` (zip name) for traceability.
  Column names come from the CSV header; confirm the names of: award key `generated_unique_award_id`,
  transaction id, action date, federal action obligation, place-of-performance state code, county code,
  country code, toptier agency code and name. Record the confirmed names in `DECISIONS.md`.
- Census: `co-est2024-alldata.csv` into `census_county_2024`, `co-est2021-alldata.csv` into
  `census_county_2021`. Keep all columns. Drop nothing here.
- Site matrix: flatten `data/raw/sitematrix.json` `sitematrix` entries into one row per site (`dbname`,
  `url`, `code` (project), language code, `closed`). Table `sitematrix`.
- Stream is not touched in this phase.

TDD note: write `tests/test_batch_ingest.py` first. Test: row count of each lake table equals the row
count of its source (CSV rows, census rows, flattened sites); a second run gives the same content hash of
every lake table. Run it red before writing `batch_ingest.py`.

Exit criteria:
- `make build` runs the ingestion step and exits 0.
- `uv run python -m unittest tests.test_batch_ingest -v` passes.
- Content hash of each lake table is identical after two runs.

### Phase 3: Batch staging and star schema (dbt core)

Goal: typed staging, dimensions and the transaction fact, with keys tested.

- Staging (views): `stg_usaspending_transactions` (union of both families, cast amounts with
  `CAST(... AS DECIMAL(18,2))` and no FLOAT, action date to DATE, FY2024 filter on action date),
  `stg_census_population` (join key `state_fips || county_fips` as 5-digit text; drop the `COUNTY = 000`
  state rows; POPESTIMATE2024 for July 1 2024; fallback from 2021 for keys absent in 2024),
  `stg_sitematrix`.
- Core (tables): `dim_agency` (toptier code, agency name), `dim_place` (state FIPS, county FIPS 5-digit,
  state name, county name, `is_unplaced`), `dim_date` (date, month start, fiscal year), and
  `fct_award_transaction` at the grain of one transaction (transaction key from Phase 2 confirmation).
- Unplaced members (record `cd-1-place-and-unplaced`): a transaction with no valid US state code goes to
  `state_fips = '99'`, `county_fips = '99999'`, named "Unplaced". A transaction with a state but no county goes to
  `county_fips = <state fips>000`, named "Unknown county". Both are rows in `dim_place`. No row is dropped.
- Population: `stg_census_population` keeps `population_year` (2024 or 2021) and `population_source`.
- Money: every amount in DECIMAL(18,2). The per-person ratio is DECIMAL(18,4) in Phase 4.

TDD note: write the dbt tests first: `unique` and `not_null` on each key, `relationships` from the fact to
`dim_agency`, `dim_place`, `dim_date`, a singular test that the fact total for FY2024 equals the sum of the
staging amounts (no loss), and a singular test that every transaction has one place key. Run `dbt test`
red first.

Exit criteria:
- `uv run dbt build --project-dir transform --profiles-dir transform --select tag:batch --exclude marts`
  passes.
- Fact row count equals the number of FY2024 source rows (from Phase 2 counts, not typed).

### Phase 4: Batch marts, oracle checks 1 to 4, publish

Goal: the monthly mart with a contract, published to `out/marts/`, and checks 1 to 4 answered.

- `mart_obligations_monthly`, grain: month start, state FIPS, county FIPS, agency code. Columns:
  `month_start DATE`, `state_fips VARCHAR`, `county_fips VARCHAR`, `agency_code VARCHAR`,
  `net_obligations DECIMAL(18,2)`, `transaction_count BIGINT`, `population BIGINT`,
  `population_year INTEGER`, `population_source VARCHAR`, `obligations_per_person DECIMAL(18,4)`.
  Enforced contract (dbt `contract: enforced: true`) with these types. Marts carry no `_dlt_*` columns.
- Population on each monthly row is the FY2024 population for that county (not divided by 12).
- Publish the star tables under `out/marts/` too (record `cd-1-publication-scope`): `dim_agency`,
  `dim_place`, `dim_date`, `fct_award_transaction`, `mart_obligations_monthly`. Each is an external
  model in the `marts` layer with a thin select (`select * from ...`) so the write path is the same.
- Oracle checks: `oracle_map.yml` entries 1 to 4. Check 1: `mart_obligations_monthly` or the fact,
  by agency, FY2024 sum. Check 2: FY obligations per person computed from FY sums of the monthly mart,
  ties broken by county FIPS ascending (record in DECISIONS, G-14). Check 3: the award-level view
  (`award_net` = sum per `award_key` over FY2024, then count where below zero), published as
  `mart_award_net_fy2024` (record `cd-1-award-key-and-sign`). Check 4: a singular dbt test for one chosen
  month: county totals per state equal the state total, state totals sum to the source total.

TDD note: write the singular tests for check 4 and the expected counts for check 3 before the marts.
Write the independent Python computation in `tests/test_oracle_batch.py` for checks 1 to 3 from the raw CSV
(stdlib `zipfile`, `csv`, and integer cents for money), then compare to the dbt results.

Exit criteria:
- `make build` run twice: content hash of every table under `out/marts/` is identical.
- Each dbt contract passes `dbt build`.
- The independent Python results match the dbt results for checks 1, 2 and 3.
- Check 4 passes for every month in the FY (stronger than one month).

### Phase 5: Stream consumer (SSE to lake, no dbt yet)

Goal: `make stream DURATION=<s>` lands each unique edit once, with a stable arrival sequence, across
disconnects and restarts.

- `pipeline/sse.py`: stdlib `urllib.request` SSE reader. Parses `event:`, `data:`, `id:` lines and `retry:`.
  On a dropped connection: reconnect with backoff, send `Last-Event-ID` from `lake/_stream_cursor.json`
  when present.
- `pipeline/stream_consume.py`: for each `message` event, parse JSON. Dedupe key is `meta.id` (record
  `cd-1-stream-dedupe-resume`). Before landing a flush, read existing `meta.id` values from
  `lake/recentchange/*.parquet` with DuckDB and drop any already landed. `arrival_seq` is the next integer
  after `max(arrival_seq)` in the lake (the lake is the state; `_stream_cursor.json` is only a hint).
  Land each flush through dlt with `write_disposition="append"` (record `cd-1-write-disposition`).
  Write `_stream_cursor.json` after the land succeeds, via a temp file and `os.replace`.
- The stream row keeps: `meta_id`, `timestamp` (event time, seconds), `meta_dt`, `wiki`, `server_name`,
  `namespace`, `bot`, `length_old`, `length_new`, `arrival_seq`, `arrival_ts`.
- `--duration` is wall-clock seconds. At the deadline: stop reading, flush, land, write the cursor, exit 0.
- Stop and restart: a second run reads the lake state, so no event is counted twice and no landed event
  is lost. An event read but not landed is not acknowledged, so the next run receives it again (if the
  server replays) or the replay is restarted from the top and deduped. Either way no loss.

TDD note: write `tests/test_stream_consume.py` first with a local HTTP server that serves SSE and can
drop the connection after N events. Tests: (a) a drop after 5 events, then reconnect, gives each `meta.id`
once; (b) stop after 10 events, restart: the union equals one unbroken run; (c) a replayed block with
repeated `meta.id` values lands once; (d) `arrival_seq` is strictly increasing with no gaps.

Exit criteria:
- Tests (a) to (d) pass.
- `make stream DURATION=20` against `http://localhost:8099/v2/stream/recentchange` lands rows (the replay
  must be up; if it is not, the Phase fails with `STOPPED`, not a fake pass).
- Second run against the same replay adds no rows with an existing `meta.id`.

### Phase 6: Stream models (incremental fact, late events, 5-minute windows)

Goal: the edit fact, the late_events table and the window mart, built by incremental dbt models from the
landed micro-batches.

- `stg_recentchange` (view on the lake): `event_id = meta_id`, `event_time = to_timestamp(timestamp)` (UTC),
  `window_start = time_bucket(INTERVAL 5 MINUTE, event_time)` (check the bucket origin is epoch, so
  windows start on multiples of 5 minutes UTC; write a unit test), `actor_type = case when bot then 'bot'
  else 'human' end` (missing bot = human; record `cd-1-stream-field-rules`), `bytes_delta` = `length_new -
  length_old` or 0 when either is missing, `has_length` flag.
- `fct_edit` (incremental, `unique_key = event_id`, grain: one change event): adds `is_late`. Late rule
  (record `cd-1-stream-lateness-watermark`): `prior_max` = the greatest `event_time` of earlier arrivals,
  from `fct_edit` itself for old rows and from `ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING` over
  `arrival_seq` for new rows. `is_late = prior_max is not null and prior_max > window_start + 15 minutes`.
  (The window end is `window_start + 5 minutes`; 10 minutes after it is `window_start + 15 minutes`.)
  Because a late event's own time is at most its window end, it never raises `prior_max`, so the
  watermark answers G-2 without a special case.
- `late_events` (table, the late rows of `fct_edit`), published.
- `mart_edit_windows_5min` (incremental, unique key of window, wiki, namespace, actor type): only rows with
  `is_late = false`. Columns: `window_start TIMESTAMP`, `window_end TIMESTAMP`, `wiki VARCHAR`,
  `server_name VARCHAR`, `namespace INTEGER`, `actor_type VARCHAR`, `edit_count BIGINT`,
  `net_bytes_added BIGINT`. Enforced contract. Recomputed for affected windows only (a late event does
  not touch a window).
- `dim_wiki` (from `stg_sitematrix`): `wiki` = `dbname`, `server_name` = host of `url`, `project`, `language`.
  Check 6 uses `server_name = 'en.wikipedia.org'`, which maps to `dbname = 'enwiki'` (answers G-10).
- Publish `fct_edit`, `late_events`, `mart_edit_windows_5min`, `dim_wiki` under `out/marts/`.
- Stream models carry the tag `stream`. `make stream` builds them after the consumer.

TDD note: dbt unit tests in yml (dbt-core 1.11 supports `unit_tests:`) first. Cases:
- S4: event 12:21, window 12:15 start, prior max 12:31 gives `is_late = true`.
- S5: event 12:30, window 12:25 start, prior max 12:30 gives `is_late = false`.
- Boundary: prior max exactly window start + 15 minutes gives false.
- Window start for 12:04:59 is 12:00, for 12:05:00 is 12:05.
- Missing length gives `bytes_delta = 0`, `has_length = false`.
- Missing bot gives `actor_type = 'human'`.
Plus key tests: `event_id` unique and not null on `fct_edit`; the window mart key test.
Plus an incremental test: build on two batches, then a full rebuild: same content hash.

Exit criteria:
- All unit tests in yml pass.
- After `make stream` on the replay: `count(*) from fct_edit` equals the count of unique `meta.id` in the lake.
- A full rebuild of the stream models (`dbt run --full-refresh --select tag:stream`) gives the same content
  hash of `fct_edit` and the window mart as the incremental path.

### Phase 7: Stream checks 5 to 7 and the replay tests

Goal: checks 5, 6 and 7 answered and tested; the stop and restart rule is tested on the real replay.

- Check 5: edits and net bytes per wiki, actor type, over every row of `fct_edit` (late included). The
  replayed hour is all consumed events (record `cd-1-stream-field-rules`, G-11); the first and last event
  time are written to `DECISIONS.md` from the data.
- Check 6: the window with the most edits on `server_name = 'en.wikipedia.org'`, on-time only, from
  `mart_edit_windows_5min`. Ties: the earliest window_start wins; record in DECISIONS.
- Check 7: `count(*)` of `late_events`.
- `oracle_map.yml`: entries 1 to 7, each naming the table and column (or view) under `out/marts/` only.
- Independent Python check for checks 5 to 7 from the raw lake files (stdlib + DuckDB) in
  `tests/test_oracle_stream.py`.
- Stop and restart test on the real replay: run one unbroken `make stream`, record the counts; reset the
  stream lake; run two halves with a stop between; compare counts. Both must match exactly.

Exit criteria:
- The oracle test for checks 5 to 7 passes against the dbt results.
- The stop and restart comparison matches exactly (no difference in count or net bytes per group).

### Phase 8: Close-out and the repeat-run proof

Goal: the final build and documentation match the acceptance list.

- Fill `DECISIONS.md` with the choices and their outcomes; each entry links to its decision record.
- Each model has a description of its grain in its yml (`description:` with "one row per ..."). Fix any
  model without it.
- Run from a clean tree (remove `lake/` and `out/`): `make build` twice, `make stream` twice on the replay
  (with the stop-restart comparison already done in Phase 7), `uv run dbt test`, `uv run python -m unittest
  discover -s tests -v`.
- Write `summary.md` and `PR.md` outputs as the packet asks (the packet path under the outputs directory).

Exit criteria: every item in the Acceptance list is true, and the content hashes from both builds match.

## Assumptions that the plan builds

Each row is in `.context/deferrals/cd-1_deferral-register.md`. Phase is where it is built.

| Gap | Assumption | Built in |
|---|---|---|
| G-1 | Dedupe key `meta.id`; the lake is the state; `Last-Event-ID` is a hint; replay restarts are deduped | Phase 5 |
| G-2 | Watermark = running max of event time over all first arrivals, persisted in `fct_edit` | Phase 6 |
| G-3 | Award key `generated_unique_award_id`; sum per award over FY2024, then sign | Phase 3, 4 |
| G-4 | Place of performance; unplaced members for no state, and "Unknown county" for no county | Phase 3 |
| G-5 | Star tables and stream facts are published under `out/marts/`; oracle points only there | Phase 4, 6 |

## Risks for the reviewer

- The replay behavior for `Last-Event-ID` is not known. The plan works either way; the live URL is untested.
- The dlt filesystem destination in append mode with one file per flush must be verified in Phase 5 (a
  spike at the start of the phase). If it cannot append Parquet files, the consumer writes Parquet with
  DuckDB directly, and the plan's `DECISIONS.md` says so.
- The incremental state lives in `out/warehouse.duckdb`. The grader removes `out/` and `lake/` before a
  run, so a fresh build must regenerate all state from `lake/`. Phase 8 tests that.

## Footer

Next step: `/plan-review .context/plans/cd-1.plan.md`.
