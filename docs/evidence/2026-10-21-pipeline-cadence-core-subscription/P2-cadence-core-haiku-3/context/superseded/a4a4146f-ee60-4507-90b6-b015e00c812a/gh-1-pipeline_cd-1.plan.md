RUN_BY_COMMAND: plan-create
Pipeline-Run: a4a4146f-ee60-4507-90b6-b015e00c812a
Ticket: cd-1 (task gh-1)
Tracker: none

# Plan: gh-1 open-data pipeline (cd-1)

Inputs:
- Request: `.context/proposals/cd-1.md` (sha256 9ce8ff61312f1bd49b72db2eebcdd3f8ce263bbbd4b7821a852d6dcfea588758)
- Vibe test: `.context/vibetest/cd-1_2026-10-22.md` (sha256 692e057cf367b99e7b909ebcc0d4b4a61a896163090274891a98f14b59f5690a), verdict NOT READY FOR PLANNING, gaps G-1 to G-9.

The gaps G-1 to G-9 are settled by assumptions in this plan. Each assumption is a row in
`.context/deferrals/cd-1_deferral-register.md` and is built by the phase named there.

## 1. Goal, constraints, non-goals, success signals

Goal: a Python 3.12 pipeline engine, configured by `pipelines/*.yml`, that lands the USAspending,
Census and Wikimedia sources into a Parquet lake under `lake/`. A dbt project in `transform/`
builds staging, star schema and marts on the lake. Marts are published as Parquet under
`out/marts/<mart>/`. Two questions are answered: batch (FY2024 federal obligations) and stream
(Wikipedia edits per 5-minute window).

Constraints:
- Only the make targets that exist may be used: `build` and `stream` (both are stubs in `Makefile`
  and are implemented here). Do not add other make targets.
- Engine YAML is the only way to add a source or a mart of an existing kind (no Python needed).
- Money is exact (decimal). No floating-point sums.
- Running `make build` twice does not change any output.
- `make stream DURATION=<s>` neither loses nor double-counts an event across stop and start.
- Pinned deps in `pyproject.toml` (pyarrow 26.0.0, polars 2.0.0, datafusion 55.0.0, dbt-core 1.11.6,
  dbt-duckdb 1.11.0, duckdb 1.5.6). Versions are not changed.

Non-goals:
- No live Wikimedia calls in tests or grading. The live URL is used only in the demo, by config.
- No BI layer, no dashboards.
- No change to the request's check definitions.

Success signals (all must hold at the end of Phase 7):
- `make build` then `make build` again: same row content in every lake table and every mart.
- `make stream DURATION=60` against the replay at `http://localhost:8099/v2/stream/recentchange`,
  stopped and restarted, gives the same edit count as one uninterrupted run.
- Checks 1 to 7 in `oracle_map.yml` each resolve to a table or SQL view that returns the answer.
- `dbt build` passes, including key tests and the reconciliation test for check 4.
- `DECISIONS.md` lists every choice, including the 9 gap assumptions and the 6 non-blocking gaps.

## 2. Step 0: problem restatement, challenges, blast radius

Problem: the request is a full pipeline with two sources of different kinds (files and an SSE
stream), two engines (Polars/DataFusion for ingestion, DuckDB via dbt after the lake), and exact
money and stream-time rules. The vibe test found that the spec does not define county choice,
month, award, per-person measure, money types, the stream commit, the dedupe key and the make
target for the stream models.

Challenges to the spec text (carried into DECISIONS.md, not silently fixed):
- "Build a small pipeline engine" plus "DataFusion and Polars work on the ingestion side" means the
  engine has two transform engines. The plan keeps both, because the spec says the YAML names the
  engine. Polars does row-wise steps, DataFusion does SQL steps (see decision cd-1-engine-transforms).
- "The lake keeps the source's data and adds only load metadata." Load timestamps break
  `make build` idempotence (G-8). The lake keeps a content hash of the source file and no wall-clock
  time (see cd-1-lake-layout).
- "Late" is a stream-time rule over the running maximum. A process restart loses that maximum
  unless it is stored with the position (G-7). It is stored with the position (see cd-1-stream-commit).
- The request says marts are Parquet under `out/marts/`, and that dbt model contracts are
  enforced. dbt-duckdb external materialization does not enforce contracts, so marts are built as
  tables and copied to Parquet by a post-hook (see cd-1-mart-publish).

Blast radius:
- New: `engine/`, `pipelines/`, `transform/models/`, `transform/macros/` (if needed), `oracle_map.yml`,
  `DECISIONS.md`, `Makefile` (two targets filled in), `pyproject.toml` (adds jsonschema, pytest; see
  cd-1-engine-schema and Phase 1).
- Generated and gitignored: `lake/`, `out/`, `transform/target/`.
- Not touched: `data/raw/` (read only), `uv.lock` except for the dev dependency added in Phase 1.

Acceptance: the success signals in section 1, and each phase exit criterion below.

## 3. Assumptions for the blocking gaps

Each row is logged in `.context/deferrals/cd-1_deferral-register.md` under `## Assumptions`.

| Gap | Assumption | Settled by |
|---|---|---|
| G-1 | "Where the money went" uses the place of performance (`primary_place_of_performance_*` state and county FIPS), not the recipient. Rows with a foreign place of performance go to state `FOREIGN` and county `FOREIGN`. Rows with a US place but no county FIPS go to county `UNKNOWN` inside the state. Every source row lands in exactly one bucket, so county, state and source totals reconcile exactly. | Phase 2 (place bucketing in the ingestion transform), Phase 3 (dbt reconciliation test for check 4) |
| G-2 | "Month" is the calendar month of `action_date`, labelled `YYYY-MM`. FY2024 rows are those with `action_date_fiscal_year = 2024`; the engine fails if an FY2024 row has an action date outside 2023-10-01 to 2024-09-30. | Phase 2 (filter and check), Phase 3 (monthly mart grain) |
| G-3 | An award is one value of `generated_unique_award_id` (one key across the contract and assistance files). Check 3 counts awards whose summed FY2024 `federal_action_obligation` is below zero. A per-transaction count is not used. | Phase 3 (`dim_award` key), Phase 4 (check 3 view) |
| G-4 | Per-person is FY2024 (or monthly) obligations divided by the county population for July 1, 2024 (`POPESTIMATE2024`). The monthly mart holds the monthly obligations divided by that population, and this is documented as a monthly rate. Population is a county attribute: it is never summed across agency rows, and state population is the sum of its county populations. | Phase 3 (mart columns and uniqueness test on county population), Phase 4 (check 2) |
| G-5 | Obligations are `DECIMAL(18,2)` in the lake and the marts. Per-person values are `DECIMAL(18,2)`, rounded half away from zero (DuckDB `round`). Sums are on decimals only; no float cast anywhere. | Phase 2 (decimal parse in engine), Phase 3 (column types enforced by dbt contract) |
| G-6 | Change types `edit` and `new` count as edits. `log` and `categorize` events are kept in the fact with their `change_type`, and are not counted as edits. Lateness applies to every consumed event. Null `length.old` or `length.new` gives a 0 byte delta and sets `has_length = false`. Lateness is computed at ingest in the engine, because it needs the stream history (see cd-1-late-classification). | Phase 5 (classification and types), Phase 6 (edit fact and window mart filters) |
| G-7 | The event identity for dedupe is `meta.id`. The consumer position (last SSE `id`) and the running maximum event time are stored in the same Parquet file as the micro-batch, in its footer, and that file appears by one atomic rename. | Phase 5 (sink and commit), Phase 5 crash tests |
| G-8 | `make build` idempotence is checked by row content, sorted by the table key, with all columns compared. The lake and marts carry no load timestamp; the lake keeps `_source_sha256` and `_source_file` only. A byte comparison is reported but not required. | Phase 2 (deterministic writes), Phase 7 (double-build check script in the test suite) |
| G-9 | `make build` runs `dbt build --exclude tag:stream`. `make stream DURATION=<s>` runs the engine on `pipelines/stream.yml`, then `dbt build --select tag:stream`. If the replay ends before DURATION, the engine exits 0 and the dbt step still runs. | Phase 6 (Makefile), Phase 7 (end-to-end run) |

Non-blocking gaps, chosen and logged in `DECISIONS.md` (Phase 7):
- N-1: The census file is filtered to `SUMLEV = 050` rows. The join key is the 5-digit FIPS `STATE || COUNTY`. Amendment A fallback: a county missing from the 2024 file uses `POPESTIMATE2021` from the 2021 file, and the case is named in DECISIONS.md. If the county is missing from both, population is NULL and the row is reported by a test; the fallback is not extended further.
- N-2: The stream `wiki` field is the dbname. It joins to `data/raw/sitematrix.json` by dbname, which gives language and project. Check 6 filters on `server_name` = `en.wikipedia.org`. The bot field is `bot`.
- N-3: The YAML format and the `oracle_map.yml` format are chosen in Phase 1 and Phase 4.
- N-4: The resume uses the `Last-Event-ID` request header with the position stored in the footer.
- N-5: Ties in check 6 are broken by `window_start` ascending.
- N-6: "Contract and grant money" is the union of the Contracts and Assistance files. The fact key is `transaction_key`, which is the source's own unique transaction key per file type, prefixed with the file type.

## 4. Reuse and extension

Existing helpers and modules in this repo: none beyond the skeleton. The skeleton has `pyproject.toml`
(pins), `Makefile` (two stub targets), `transform/dbt_project.yml` and `transform/profiles.yml` (dbt
project and DuckDB profile at `out/warehouse.duckdb`), and the raw data under `data/raw/`. The plan reuses
them as they are. The `Makefile`, `dbt_project.yml` and `profiles.yml` are edited only where a phase says so.

Extension points added by this plan:
- The engine source registry (`file` and `sse` kinds), the transform registry (`polars` and
  `datafusion` engines) and the sink registry (`parquet_lake` and `parquet_stream`). A new source or
  mart of an existing kind is a new YAML entry.
- The YAML schema file `engine/schema/pipeline.schema.json`. Adding a field is a schema change and a test.
- dbt `source()` entries with `external_location` metadata, so a new lake table needs a source entry
  and a staging model, and no engine code.

## 5. Design decisions

Each decision has a record in `.context/proposals/cd-1-<slug>.md` (see section 6).

| Decision | Choice | Rejects |
|---|---|---|
| cd-1-lake-layout | One folder per lake table, Parquet, rows sorted by key, file names deterministic, `_source_sha256` and `_source_file` as the only load metadata | Load timestamp, run id, random file names |
| cd-1-engine-transforms | `engine:` in each transform names `polars` or `datafusion`. Polars does row-wise steps (cast, filter, parse), DataFusion does SQL (union, joins used for landing) | One engine only |
| cd-1-engine-schema | JSON Schema (draft 2020-12) checked with `jsonschema`, which is added as a direct dependency. Error line numbers come from the PyYAML node tree (`yaml.compose`), so each error names file, line and problem | Pydantic, hand-written checks |
| cd-1-stream-commit | The micro-batch is one Parquet file, written to `lake/stream_events/_tmp/`, then moved into `lake/stream_events/` by one `os.replace`. The footer holds `last_sse_id`, `max_event_time` and the batch id. The file is the commit | A separate position file (two writes, not atomic) |
| cd-1-late-classification | The engine marks each first arrival as on time or late, using the running maximum event time from the last committed footer. Late is `max_prev > window_end + 10 min`. Dedupe on `meta.id`. The window mart reads only on-time rows | dbt-side classification (needs history across batches) |
| cd-1-county-place | Place of performance, with buckets `FOREIGN` and `UNKNOWN` (see G-1) | Recipient county, dropping rows |
| cd-1-month-and-award | Calendar month of `action_date`; award key `generated_unique_award_id` | Fiscal month numbering; per-transaction counts |
| cd-1-money-type | `DECIMAL(18,2)` everywhere; half-away-from-zero rounding on per-person | `DOUBLE` sums |
| cd-1-per-person | July 1, 2024 population (`POPESTIMATE2024`), 2021 fallback per Amendment A; population not additive across agency rows | Census 2020 base (`CENSUS2020BASE`); summing population per agency |
| cd-1-edit-types | Edits are `edit` and `new`; other types kept in the fact with their type | Counting every change event as an edit |
| cd-1-window-incremental | Window mart is incremental with `delete+insert` on `window_start >= max_event_time - 15 min` (on-time events can still change a window until the running max passes `window_end + 10 min`) | Full rebuild each run (correct, but not incremental as the request asks) |
| cd-1-mart-publish | Marts are `table` models with an enforced contract; a post-hook copies each to `out/marts/<mart>/<mart>.parquet` | dbt external materialization (no contract enforcement) |
| cd-1-stream-replay-ids | Stream resume uses `Last-Event-ID`; the SSE reader is stdlib `urllib`, so no HTTP dependency is added | `requests` or `httpx` added as dependencies |

## 6. Decision records

One file per row of section 5, at `.context/proposals/cd-1-<slug>.md`, with the frontmatter from the
P1 contract (`decision_id`, `status: proposed`, `question`, `choice`, `rationale`) and a `Ticket: cd-1` line.

## 7. Phases

Quality gate commands, all real in this repo:
- `uv run pytest engine/tests` (pytest is added in Phase 1 as a dev dependency)
- `uv run python -m engine validate pipelines/*.yml`
- `uv run dbt build --project-dir transform --profiles-dir transform --exclude tag:stream`
- `uv run dbt build --project-dir transform --profiles-dir transform --select tag:stream`
- `make build`, `make stream DURATION=<s>`

TDD: each phase starts with failing tests in `engine/tests/` or dbt tests in `transform/tests/`
(dbt singular tests as SQL), then the code. Engine tests use small fixtures and a local fake SSE
server, not the replay service. The real replay is used only in Phase 6 and Phase 7.

### Phase 1: Engine skeleton, YAML schema and validation
Scope: `engine/` package with `__main__` (`validate` and `run` subcommands). Pipeline schema
`engine/schema/pipeline.schema.json` with sources, transforms and sinks. Validator maps each error
to file, line and problem (cd-1-engine-schema). Add `jsonschema` and `pytest` (`uv add jsonschema`,
`uv add --dev pytest`), with the lock updated.
TDD: tests for a valid file, a file with an unknown engine, a missing sink, a bad type, a YAML syntax
error. Each error test checks the file, the line and the problem text.
Exit: `uv run pytest engine/tests` passes; `uv run python -m engine validate` on a bad file prints
`file:line: problem` and exits non-zero.

### Phase 2: Batch sources to the lake
Scope: `file` source kinds (zip member CSV for USAspending, CSV for Census, JSON for sitematrix).
Transforms: polars for casts and parsing (decimal, date, FIPS as 2 and 3 character strings), filter
of FY2024 with the G-2 check, place bucketing (G-1), union of Contracts and Assistance (N-6) in
DataFusion SQL. Census: `SUMLEV = 050`, 5-digit FIPS (N-1). Sitematrix flattened to one row per wiki
(dbname, language, project, url host). Sink `parquet_lake`: deterministic file names and sorted
rows, `_source_sha256` and `_source_file` columns only (cd-1-lake-layout, G-8).
TDD: tests with small CSV and zip fixtures: decimal sums exact, bucket rules, G-2 failure, sort order.
Exit: `uv run python -m engine run pipelines/batch.yml` writes `lake/` twice with the same rows.

### Phase 3: dbt staging, star schema and marts
Scope: `transform/models/` sources (with `external_location` into `lake/`), staging models,
`dim_agency`, `dim_place` (state, county, buckets), `dim_date` (date and calendar month), `dim_award`,
`fct_award_transaction` (grain: one source transaction row). `mart_obligations_monthly` (grain: month,
state, county, agency; net obligations, county population, obligations per person) with contract
enforced (G-4, G-5, cd-1-mart-publish). Documentation of each model's grain. dbt tests on keys
(`unique`, `not_null`) and a singular test for population uniqueness per county.
TDD: singular tests written first (reconciliation, population uniqueness, decimal type).
Exit: `uv run dbt build --project-dir transform --profiles-dir transform --exclude tag:stream` passes.

### Phase 4: Batch oracle views for checks 1 to 4
Scope: SQL views under `transform/models/checks/` for checks 1 to 4 (the view names are the
answers). `oracle_map.yml` lists, for each check, the table or view and the column.
Check 2 ranks counties by FY2024 obligations per person; ties broken by county FIPS.
TDD: tests on a small hand-made lake fixture (in `transform/tests/fixtures`) with known answers.
Exit: `oracle_map.yml` has rows for checks 1 to 4, and each view returns the expected fixture answer.

### Phase 5: Stream consumer and micro-batch sink
Scope: `sse` source kind (stdlib `urllib`, reconnect with backoff, `Last-Event-ID` from the footer,
N-4). Engine transforms in polars: parse `timestamp` (epoch seconds, event time), window start
`floor(ts / 300) * 300` UTC, change type, bot flag, net bytes. Late classification (cd-1-late-classification,
G-6). Dedupe on `meta.id` against the committed lake before a commit. Sink `parquet_stream`: write
the batch to `lake/stream_events/_tmp/`, then `os.replace` into `lake/stream_events/`; footer holds
`last_sse_id`, `max_event_time` (cd-1-stream-commit, G-7). On start, delete leftover `_tmp/` files.
TDD: fake SSE server in tests. Crash tests: kill after the tmp write and before the rename, then
restart: no event lost or doubled. Disconnect test: server drops the connection mid-batch, consumer
resumes from the last footer. Late rule tests at the boundary (exactly 10 minutes is on time).
Exit: `uv run pytest engine/tests` passes, including the crash and disconnect tests.

### Phase 6: Stream models and make targets
Scope: `fct_edit` (grain: one change event; incremental, unique key `event_id`; holds on-time and
late events, with `is_late`, and all change types). `late_events` (table: late rows of `fct_edit`).
`mart_edit_windows_5min` (grain: 5-minute window, wiki, namespace, actor type; edit count and net bytes
for `edit` and `new` on-time events; incremental with the cd-1-window-incremental rule). Actor type
is `bot` or `human`. Dedupe test on `event_id`. Makefile: `build` runs the batch YAML then
`dbt build --exclude tag:stream`; `stream` requires `DURATION` (`$(error ...)` when unset), runs
`pipelines/stream.yml` then `dbt build --select tag:stream` (G-9). `pipelines/batch.yml` and
`pipelines/stream.yml` are written.
TDD: dbt singular tests (window boundary, late excluded from window, late included in fact).
Exit: `make stream DURATION=60` against the replay completes; the same window output is produced
when the consumer is stopped at 30 seconds and restarted.

### Phase 7: Stream oracle checks, end-to-end, deliverables
Scope: checks 5 to 7 views (check 5: edits and net bytes per wiki, human and bot, all consumed events;
check 6: top 5-minute windows on `en.wikipedia.org`, on-time edits, ties by `window_start`; check 7:
count of late events). `oracle_map.yml` complete for checks 1 to 7. Publish marts to `out/marts/`.
Double-build check: run `make build` twice and compare rows (G-8). DECISIONS.md covers every choice in
sections 3 and 5 and the non-blocking gaps. Write `outputs/summary.md` and `outputs/PR.md` as the task
requires.
TDD: a test that runs the batch twice and compares row content for every mart.
Exit: all success signals in section 1 hold; the end-to-end run of `make build` and
`make stream DURATION=<s>` is recorded in `outputs/summary.md`.

## 8. Risks

- USAspending column names are taken from the data dictionary; Phase 2 verifies them against the CSV
  headers before any mapping. A mismatch stops Phase 2.
- The replay server may not support `Last-Event-ID` (N-4). Phase 5 falls back to the footer position
  and meta.id dedupe, which keeps the no-loss and no-duplicate rule.
- DuckDB decimal division can widen the scale. Phase 3 casts before dividing and tests the result.

## 9. Next step

`/plan-review .cursor/plans/gh-1-pipeline_cd-1.plan.md`

## Plan update 2026-10-22

RUN_BY_COMMAND: plan-update

Source: `.context/reviews/plan_gh-1-pipeline_cd-1.md` (sha256 90f663e022710aa63cae65d145b11a1690d46c9951528c1c53df5b7609455f15,
verdict READY WITH CHANGES, reviewed plan sha256 1755f17bba8584a6e0cdbb24dbad24fb9543b7f7bb906a2fc6ad039427fe74b1).
The text above is kept. Where this section and an earlier section differ, this section governs.

### MF-1: late rule uses the running maximum over all first arrivals

Replaces the footer-only rule in section 5 (cd-1-late-classification) and Phase 5.
- `max_seen` starts at the `max_event_time` in the footer of the last committed batch (no value on the first batch).
- Events of a micro-batch are processed in arrival order. Each first arrival (a `meta.id` not in the committed lake and not already seen in this run) is classed first, then `max_seen = max(max_seen, event_time)`. A first arrival that is late still advances `max_seen`.
- Late: `max_seen > window_end + 10 min`, where `window_end = window_start + 300 s`. Exactly 10 minutes is on time.
- A duplicate arrival is dropped and does not change `max_seen`.
- The footer stores `max_seen` after the batch, as `max_event_time`.
- Phase 5 TDD adds this case: one micro-batch with event A (event time 12:31:00, window 12:30) arriving first and event B (event time 12:05:00, window 12:05, window end plus 10 min = 12:20:00) arriving second. B is late, although B is in the same batch as A. Test name: `test_late_uses_max_including_same_batch`. Boundary case: event A at 12:20:00 arrives first, then event B at 12:05:00 (window end plus 10 min = 12:20:00). The maximum is 12:20:00, which is not more than 12:20:00, so B is on time.

### MF-2: "YAML only" applies to the engine half

Replaces the constraint in section 1 ("Engine YAML is the only way to add a source or a mart of an existing kind").
- Constraint, narrowed: adding a source or a mart of an existing kind needs no Python. On the engine side it is YAML only. On the dbt side a new lake table needs a `source()` entry and a staging model, and a new mart needs a dbt model with its contract and post-hook. These are SQL and YAML, not Python.
- Challenge added to section 2, to be carried into DECISIONS.md: the request says "YAML only, no Python". The engine half meets that. The dbt half needs SQL per new lake table or mart. Logged as a challenge to the spec text, not silently accepted.

### MF-3: contract and publish for `mart_edit_windows_5min`

Adds to Phase 6.
- Contract, enforced (column names and types):

| Column | Type | Null |
|---|---|---|
| window_start | TIMESTAMP (UTC, multiple of 300 s) | not null |
| wiki | VARCHAR (dbname) | not null |
| namespace | INTEGER | not null |
| actor_type | VARCHAR (`bot` or `human`) | not null |
| edit_count | BIGINT | not null |
| net_bytes | BIGINT | not null |

- Grain: one row per `window_start`, `wiki`, `namespace`, `actor_type`. dbt `unique` test on that four-column key.
- The mart is incremental (cd-1-window-incremental). Its contract is enforced on each incremental build. The decision record cd-1-mart-publish is amended to say "table, or incremental for the window mart" (see the record).
- Publish: the post-hook copies the whole mart to `out/marts/mart_edit_windows_5min/mart_edit_windows_5min.parquet` after each build. The mart has tag `stream`, so the hook runs in `make stream`, not in `make build`.

### MF-4: inclusion rules for check 2 and the month rule for check 4

Adds to Phase 4. The two rules are non-blocking gaps N-7 (check 2) and N-8 (check 4). They are logged in DECISIONS.md with the text below.
- Check 2 (`check_2_county_per_person`): ranks only counties with a 5-digit county FIPS, not in state `FOREIGN` or county `UNKNOWN`, and with a population (2024, or the 2021 fallback under N-1). A county with NULL population is excluded. Rows excluded from check 2 still count in checks 1 and 4. Ties are broken by county FIPS ascending.
- Check 4 (`check_4_reconciliation`): the request names no month, so the view returns one row per calendar month of FY2024 (`YYYY-MM`, 12 rows), with `county_sum`, `state_sum`, `source_total` and the two differences. The analyst reads the row for the month asked. Counties include the `FOREIGN` and `UNKNOWN` buckets (G-1), so no row is excluded. A dbt singular test asserts that both differences are zero for every month.

### MF-5: double-build test runs `make build`

Replaces the Phase 7 TDD line ("runs the batch twice and compares row content for every mart").
- TDD: a test runs `make build` twice (engine and dbt). After each run it reads every lake table that `make build` writes and every mart in `out/marts/`, sorts each by its key, and compares all columns. Run 1 and run 2 must be equal. Byte equality is not required (G-8).
- The stream tables are produced by `make stream`. Their restart behaviour is tested in Phase 5 and Phase 6, not here.

### Notes applied (not must-fix)

- N-1 (Connecticut): the 2024 file has planning-region rows under SUMLEV 050 (codes 09110 to 09190). The 2021 file has county rows 09001 to 09015. No 2024 row matches a 2021 code, so all eight Connecticut counties take the 2021 fallback, and the nine planning-region rows are not joined. The "population NULL" test does not fire for Connecticut. Named in N-1 and in DECISIONS.md.
- Commit checkpoint: each phase ends with a commit on `feature/gh-1-pipeline`, after its exit criterion holds.
- Rollback: revert the feature branch. `lake/`, `out/` and `transform/target/` are generated and gitignored.
- Restart position: on start, the consumer reads the highest batch id among the committed files in `lake/stream_events/` (ignoring `_tmp/`). That file's footer gives `last_sse_id` and `max_event_time`. Leftover `_tmp/` files are then deleted.
- Key naming: `fct_edit.event_id` is the event `meta.id`.
- Window predicate: the `delete+insert` predicate in cd-1-window-incremental uses `max_event_time` from the footer (the engine running maximum over all first arrivals, late ones included), not `max(event_time)` of on-time rows.
- Dedupe scope: on each batch, `meta.id` is checked against all committed ids in `lake/stream_events/`. This is acceptable at trial volume. Phase 5 tests use this scope.
- Fixture wiring: the dbt sources read the lake root from the dbt variable `lake_root` (default `lake`). Phase 4 tests pass `--vars '{lake_root: transform/tests/fixtures/lake}'`.

## Revision ledger (review 90f663e02271)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-1 | Late rule uses the running max over all first arrivals in arrival order, from the footer, and the footer stores the max after the batch | Section 5 (cd-1-late-classification), Phase 5 | `test_late_uses_max_including_same_batch` and the boundary case in `engine/tests` |
| MF-2 | Constraint narrowed to the engine half; dbt half (SQL and YAML) logged as a challenge | This update, MF-2 (replaces section 1 constraint); section 2 challenge carried into DECISIONS.md | Phase 7 DECISIONS.md has the challenge row; `engine/tests` covers the YAML-only source and sink path (`test_new_source_needs_no_python`) |
| MF-3 | Contract (six columns and types) and publish post-hook for `mart_edit_windows_5min` | Phase 6, record cd-1-mart-publish | `dbt build --select tag:stream` runs the contract test; `out/marts/mart_edit_windows_5min/` exists after `make stream` |
| MF-4 | Check 2 exclusion rule; check 4 returns one row per month, test on every month | Phase 4, section 3 (N-7, N-8) | `dbt build` singular test `check_4_all_months_reconcile`; fixture test for check 2 excluding FOREIGN, UNKNOWN and NULL population |
| MF-5 | Double-build test runs `make build` (engine and dbt) and compares all lake and mart tables by sorted content | Phase 7 | `test_make_build_twice_same_rows` in the test suite |

### Assumption rows changed in the deferral register

G-6 and G-7 rows in `.context/deferrals/cd-1_deferral-register.md` now name the running maximum rule of MF-1.

### Not changed

- The review's Notes section lists the items above. No other item is open.

## Plan update 2026-10-22 (cycle two)

RUN_BY_COMMAND: plan-update

Source: `.context/reviews/plan_gh-1-pipeline_cd-1.md` (sha256 78692b2fa1b07831487c86f548464953276146251780aeb02778011433f3ebdb,
verdict READY WITH CHANGES, reviewed plan sha256 96dd0fe962008dc5c6c38aa1fca09edb458e7cc133bb545e940cffcfb24ff079).
Open must-fixes: MF-6 and MF-7. MF-1 to MF-5 are closed in that review and stay as written.
The text above is kept. Where this section and an earlier section differ, this section governs.

### MF-6: window refresh covers on-time events of the same micro-batch

Replaces the predicate in section 5 (cd-1-window-incremental), the cycle-one note "Window predicate", and the Phase 6 window rule.

Why the bound holds: an on-time event has `max_before <= window_end + 10 min`, where `max_before` is the running maximum before that event.
So its `window_start >= max_before - 15 min`. Every batch that is not yet built starts from a running maximum at or above the running
maximum after the last built batch. So every window that an unbuilt batch can touch starts at or after that maximum minus 15 min.

State: the window mart knows the last batch it built through the table `window_build_state` (one row, column `built_max_event_time`).
- After each successful build, a post-hook of `mart_edit_windows_5min` writes `built_max_event_time = max(event_time)` over `fct_edit`.
  `fct_edit` holds every first arrival (on time and late), so this maximum is the running maximum after the last committed batch.
- A failed dbt run skips that post-hook. The state then stays at the last successful build, and the next `make stream` covers the uncovered batch.

Predicate:
- Lower bound `L = built_max_event_time - 15 min`. A first build (no `window_build_state` table, so `is_incremental()` is false) rebuilds all windows.
- The incremental select reads the on-time edit rows of `fct_edit` (`is_late = false`, change type `edit` or `new`) with `window_start >= L`.
  It reads the fact, not the rows of the batch. So each window at or after `L` is recomputed whole, and delete+insert replaces it whole.
- Model config: `materialized='incremental'`, `incremental_strategy='delete+insert'`, `unique_key=['window_start', 'wiki', 'namespace', 'actor_type']`
  (the MF-3 key).
- The footer `max_event_time` keeps the running maximum after each batch, as in the cycle-one update.

Phase 6 TDD adds these dbt tests in `transform/tests/` (the names are notes):
- `test_window_refresh_covers_same_batch_on_time`: the running maximum before a batch is 12:00. The batch holds E1 (event time 12:12,
  window 12:10, on time) and then E2 (event time 12:40). After the build, window 12:10 counts E1. The incremental result equals a `--full-refresh` build.
- `test_window_refresh_after_failed_dbt_run`: build once. Commit a batch. Make the mart step fail after `fct_edit` runs. Run again. The windows
  equal a `--full-refresh` build, and the state did not move on the failed run.
- `test_window_first_build_full_refresh`: no state table, so the mart equals a full rebuild.

### MF-7: DECISIONS.md scope and the non-blocking gap count

Phase 7 scope, replacing "DECISIONS.md covers every choice in sections 3 and 5 and the non-blocking gaps":
`DECISIONS.md` covers every choice in sections 3 and 5, the section 2 challenges (including the MF-2 challenge: the YAML-only constraint
holds for the engine half, and the dbt half needs SQL and YAML per new lake table or mart), and the non-blocking gaps N-1 to N-8
(N-7 is the check 2 inclusion rule and N-8 is the check 4 month rule, both from MF-4 of cycle one).

Success signal in section 1 (line 44) now reads: `DECISIONS.md` lists every choice, including the 9 gap assumptions and the 8 non-blocking gaps (N-1 to N-8).

### Notes applied (not must-fix)

- Phase 2 TDD adds `test_new_source_needs_no_python`: a new `file` source is added by a YAML entry only, and the batch run writes its lake table.
- Publish post-hooks that write `out/marts/` are guarded by `{% if var('publish', true) %}`. Phase 4 test runs pass
  `--vars '{lake_root: transform/tests/fixtures/lake, publish: false}'`, so fixture marts are not copied to `out/marts/`.
  `make build` and `make stream` do not set `publish`, so it stays true there. The `window_build_state` post-hook is not guarded.

### Decision records

- `.context/proposals/cd-1-window-incremental.md` is amended: the choice names `unique_key`, the lower bound `L` and the state table (MF-6).

## Revision ledger (review 78692b2fa1b0)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-6 | Window lower bound from `built_max_event_time` in `window_build_state` (minus 15 min), `unique_key` of four columns, recompute of the fact rows from L, state written only by a successful build | This update, MF-6; section 5 (cd-1-window-incremental, record amended); Phase 6 | `test_window_refresh_covers_same_batch_on_time`, `test_window_refresh_after_failed_dbt_run` and `test_window_first_build_full_refresh` in `transform/tests/`, run by `uv run dbt build --project-dir transform --profiles-dir transform --select tag:stream` |
| MF-7 | Phase 7 scope names the section 2 challenges and N-7, N-8; the success signal count is 8 | This update, MF-7; section 1 success signal (line 44, governed by this update); Phase 7 scope | `grep -cE "^- N-[1-8]:" DECISIONS.md` prints `8`, and `grep -n "MF-2 challenge\|YAML-only" DECISIONS.md` finds the section 2 challenge row |

## Plan update 2026-10-22 (cycle three)

RUN_BY_COMMAND: plan-update

Source: `.context/reviews/plan_gh-1-pipeline_cd-1.md` (sha256 74dd4ee9d6525c33f3f1b28996be79b527c5cb80a2f050b91b54dca82901cc89,
verdict READY WITH CHANGES, reviewed plan sha256 f2cfebb1caea5f132342e80f09bb93e32a7d047fa68cd9e17098f508f3f09ba).
Open must-fixes: MF-8 and MF-9. MF-6 and MF-7 are closed in that review and stay as written.
The text above is kept. Where this section and an earlier section differ, this section governs.

### MF-8: the first build is "no state row", not "no state table"

Replaces the first-build sentence in MF-6 ("A first build (no `window_build_state` table, so `is_incremental()` is false) rebuilds all windows.")
and the cycle-two Phase 6 first-build test line.
- `is_incremental()` is true when the mart table exists, the model is incremental and the run is not `--full-refresh`. It does not read `window_build_state`.
- L is read through a guard that runs before the select. L is null when `window_build_state` is missing or has no row.
- The filter `window_start >= L` applies only when `is_incremental()` is true and L is not null. Otherwise the select reads every on-time
  edit row of `fct_edit` (`is_late = false`, change type `edit` or `new`), so every window is rebuilt whole.
- The state post-hook creates `window_build_state` if it does not exist, then writes one row. A first build whose post-hook fails leaves the
  mart table and no state. The next run takes the full select, so it does not fail on the missing table.
- Phase 6 TDD: `test_window_first_build_full_refresh` has two cases: (a) no state table, mart built fresh; (b) mart table exists, state table
  absent (the failed first post-hook). Each case equals a `--full-refresh` build.
- The decision record `.context/proposals/cd-1-window-incremental.md` is amended to match (choice and rationale).

### MF-9: fixture runs write their own DuckDB file

Replaces the cycle-two note that fixture runs pass `publish: false` only, and the cycle-two statement that the `window_build_state` post-hook is not guarded.
Replaces the Phase 4 fixture arguments of the cycle-two note on fixture wiring.
- `transform/profiles.yml` takes its `path` from the dbt variable `warehouse_path`, default `out/warehouse.duckdb`. This edits the skeleton file in Phase 4,
  the first phase that needs it.
- A second variable, `publish_dir`, defaults to `out/marts`. It is the target directory of the Parquet copy hooks.
- The Parquet copy hooks and the `window_build_state` post-hook are both under `{% if var('publish', true) %}`. The state post-hook is therefore guarded
  by the same guard as the copy hooks.
- Phase 4 fixture runs pass `--vars '{lake_root: transform/tests/fixtures/lake, warehouse_path: transform/tests/fixtures/warehouse_fixture.duckdb, publish: false}'`.
  The fixture DuckDB file is generated and gitignored, like `out/`.
- Phase 6 window-refresh tests need state. They run with `publish: true`, `warehouse_path: transform/tests/fixtures/warehouse_window.duckdb` and
  `publish_dir: transform/tests/fixtures/marts`, so no test run writes to `out/`.
- Phase 4 TDD adds `test_fixture_run_leaves_real_warehouse_unchanged` (pytest in `engine/tests/`, which runs the Phase 4 fixture build in a subprocess).
  It records the SHA-256 of `out/warehouse.duckdb` (or that the file is absent) before and after the run, and asserts that the two are equal.
- `make build` and `make stream` set neither `warehouse_path`, `publish_dir` nor `publish`, so they use `out/` as before.

### Sections touched by this update

- Section 2 blast radius and section 4 (reuse and extension): `transform/profiles.yml` is edited in Phase 4 for `warehouse_path` (MF-9). The fixture
  DuckDB files and `transform/tests/fixtures/marts/` are generated and gitignored; Phase 4 adds them to `.gitignore`.

## Revision ledger (review 74dd4ee9d652)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-8 | First build is "no state row": L null gives a full select of on-time edits; the filter applies only when `is_incremental()` and L is not null; state post-hook creates the state table; record amended | This update, MF-8; Phase 6; `.context/proposals/cd-1-window-incremental.md` | `test_window_first_build_full_refresh` (cases: no state table; mart exists and state table absent) in `transform/tests/`, run by `uv run dbt build --project-dir transform --profiles-dir transform --select tag:stream` |
| MF-9 | Fixture runs use `warehouse_path` and `publish: false`; state post-hook under the publish guard; Phase 6 tests use a test warehouse and `publish_dir` | This update, MF-9; Phase 4; Phase 6 | `test_fixture_run_leaves_real_warehouse_unchanged` in `engine/tests/` (Phase 4) |

## Plan update 2026-10-22 (cycle four)

RUN_BY_COMMAND: plan-update

Source: `.context/reviews/plan_gh-1-pipeline_cd-1.md` (sha256 d969387ad40c587b913850e02f6463094af02b4de4ae3c11aa46d3fb10391e41,
verdict READY WITH CHANGES, reviewed plan sha256 8b11ce2c220e1602ac8297b0fe0eb11507b6d78f7e526426472afb12ee165c0f).
Open must-fixes: MF-10. MF-8 and MF-9 are closed in that review and stay as written.
The text above is kept. Where this section and an earlier section differ, this section governs.

### MF-10: Phase 6 tests isolate the stream lake

Replaces the Phase 6 test isolation of cycle three (MF-9 names only the warehouse and `publish_dir`). The stream lake
`lake/stream_events/` is also state of the real consumer (restart position and dedupe scope, see the restart and dedupe notes of cycle one).
Phase 6 tests must not write to it.

- Phase 6 dbt test runs (the window-refresh tests and the other stream singular tests) pass
  `--vars '{lake_root: transform/tests/fixtures/lake, warehouse_path: transform/tests/fixtures/warehouse_window.duckdb, publish: true, publish_dir: transform/tests/fixtures/marts}'`.
  So the dbt sources read `transform/tests/fixtures/lake/stream_events/`. That folder is generated and gitignored, with the other fixture outputs (Phase 4 adds it to `.gitignore`).
- Stream sink root for tests: the `parquet_stream` sink takes its root from its `path` field (cd-1-engine-schema). No engine option is added.
  The tests do not run `pipelines/stream.yml`. They run the checked-in file `transform/tests/fixtures/pipelines/stream_test.yml`, which is the same pipeline
  with the sink `path` set to `transform/tests/fixtures/lake/stream_events` and the source set to the Phase 5 fake SSE server.
  The test batches are committed with `uv run python -m engine run transform/tests/fixtures/pipelines/stream_test.yml`.
- Isolation test: `test_phase6_run_leaves_real_stream_lake_unchanged` in `engine/tests/` (pytest, Phase 6, mirrors `test_fixture_run_leaves_real_warehouse_unchanged`).
  Before and after the Phase 6 test runs (the stream_test engine runs and the dbt test runs above), it records the file list of `lake/stream_events/` and
  `lake/stream_events/_tmp/` with the SHA-256 of each file, or that the folder is absent. It asserts that the two records are equal.

### Decision record

- `.context/proposals/cd-1-late-classification.md` is amended to the cycle-one rule of MF-1: the running maximum is over all first arrivals in arrival order,
  starting from the `max_event_time` in the footer of the last committed batch. The footer stores the maximum after the batch.

### Notes applied (not must-fix)

- `window_build_state` post-hook (MF-8, cycle three): it replaces the row, so the table keeps one row across builds. It is one statement:
  `create or replace table window_build_state as select max(event_time) as built_max_event_time from {{ ref('fct_edit') }}`.
  It stays last in the post-hook list of `mart_edit_windows_5min`, under the publish guard (MF-9).
- Failure injection (Phase 6 `test_window_refresh_after_failed_dbt_run`): dbt var `inject_mart_failure` (default `false`). When `true`, the first post-hook of
  `mart_edit_windows_5min` runs `select cast('injected failure' as integer)`, which fails in DuckDB. The state post-hook is last, so it does not run after that failure.
  The test runs the failing build with `inject_mart_failure: true` added to its Phase 6 vars, then reruns without it.
- Check 5 (Phase 7): counts events with change type `edit` or `new`, on-time and late, per G-6, per wiki and actor type, with edit count and net bytes.
  Replaces "all consumed events".
- Check 6 (Phase 7, N-2): the view reads `fct_edit`, which holds `server_name`. It keeps rows with `server_name = 'en.wikipedia.org'`, change type `edit` or `new`,
  and `is_late = false`. It groups by `window_start`, counts the rows as the window total (namespace and actor type are summed by the grouping), and ranks by count descending
  then `window_start` ascending (N-5). It returns the top 5.
- Phase 7 deliverables: `outputs/summary.md` and `outputs/PR.md` are written under the run's `outputs/` directory (the additional working directory of the run). The plan names no host path (standalone-package rule).
- Phase 6 `make stream DURATION=60` end-to-end run is unchanged: it uses the real `lake/stream_events/`, and only the test runs above are isolated.

## Revision ledger (review d969387ad40c)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-10 | Phase 6 dbt test runs set `lake_root` to `transform/tests/fixtures/lake`; the test commits use `transform/tests/fixtures/pipelines/stream_test.yml` with the sink path in the fixture lake; a Phase 6 test run leaves `lake/stream_events/` unchanged | This update, MF-10; Phase 6; `.context/proposals/cd-1-late-classification.md` | `test_phase6_run_leaves_real_stream_lake_unchanged` in `engine/tests/` (Phase 6) |

## Plan update 2026-10-22 (cycle five)

RUN_BY_COMMAND: plan-update

Source: `.context/reviews/plan_gh-1-pipeline_cd-1.md` (sha256 64db5863199805044b4ab271178c8ce48131d1e7a0a4aa5ee86c59ae43f0266f,
verdict READY TO EXECUTE, reviewed plan sha256 9c87f15ea0401bc9c41d63d1cee7344105e1592f36293e6fa834b8fda5ae54).
Open must-fixes: none. MF-8, MF-9 and MF-10 are closed in that review and stay as written.
The text above is kept. No phase text changes in this update.

### Notes carried to E1 (not must-fix)

These are the review notes. E1 settles each one in the phase named. None of them changes a phase test.

- Phase 6 stream runs: `uv run python -m engine run transform/tests/fixtures/pipelines/stream_test.yml` ends when the fake SSE server closes its stream.
  The Phase 6 harness starts the Phase 5 fake SSE server before that command. The plan does not yet say how `DURATION` reaches the engine for `make stream`. E1 names that path.
- Phase 6 stream runs: before each Phase 6 test run, `transform/tests/fixtures/lake/stream_events/` is removed. Otherwise the second run dedupes against the first.
- Phase 4 profile variable: dbt renders `transform/profiles.yml` from CLI `--vars` only. The default goes in the call, not only in `dbt_project.yml`:
  `{{ var('warehouse_path', 'out/warehouse.duckdb') }}`. Without it, `make build` (no `warehouse_path` set) fails at profile load.
- Phase 7 scope line: name the `outputs/` path (`outputs/summary.md`, `outputs/PR.md`) in the Phase 7 scope line, not only in the cycle-four note.
- Phase 6 failure injection: the injected post-hook is one of the guarded copy hooks, so the Phase 6 build still fails under the publish guard (checked by E1).

## Revision ledger (review 64db58631998)

No `MF-n` is open in this review, so the ledger has no rows.

## Plan update 2026-10-22 (test benchmark)

RUN_BY_COMMAND: plan-update

Source: `.context/benchmarks/gh-1-pipeline_cd-1_plan.json` (sha256 6acb5c150ea6ca4e9eb6d660df3c3506bd369b292f58f927885ebc17066ecd86,
verdict FAIL, mean 6.5, findings cd-1-F01 to cd-1-F06; must-fix: cd-1-F01 to cd-1-F04; minor: cd-1-F05 and cd-1-F06).
The review `.context/reviews/plan_gh-1-pipeline_cd-1.md` (sha256 64db5863199805044b4ab271178c8ce48131d1e7a0a4aa5ee86c59ae43f0266f,
READY TO EXECUTE) has no open `MF-n`. This update answers the scorecard only. The text above is kept. Where this section and an earlier section differ, this section governs.
These rules replace the named test lines of the phases below. They add no new phase and change no phase scope, except Phase 7 (outputs and integration marker) and section 4.

### cd-1-F01: shared test helpers (section 4)

Adds to section 4 (test layer only; production extension points are unchanged):
- `engine/tests/support.py`, created in Phase 4 (the first phase that runs a subprocess and hashes files). Two functions:
  - `run_cli(args, env_vars)`: runs a command from the repo root with `subprocess.run` and the given environment, and returns the completed process (no exception on non-zero exit).
  - `hash_snapshot(paths)`: returns a map from path to SHA-256 for each file. A folder is walked recursively, `_tmp/` included. A missing path maps to `None`.
- `engine/tests/conftest.py`, created in Phase 5. It defines the fixture `fake_sse_server`, which runs the Phase 5 fake SSE server on a free local port and yields its URL. Phase 5 owns it. Phase 6 imports it and starts no second server.
- Users: `test_fixture_run_leaves_real_warehouse_unchanged` (Phase 4) and `test_phase6_run_leaves_real_stream_lake_unchanged` (Phase 6) use `run_cli` and `hash_snapshot`. `test_make_build_twice_same_rows` (Phase 7) uses `run_cli`.

### cd-1-F02: expected values of each named test

Each named test compares the output with an expected file under its fixture folder. The expected file is written before the code, and the comparison is exact: same rows, same values, same count. A run that returns no rows fails the test.
- Phase 2 (fixtures in `engine/tests/fixtures/batch/`):
  - Decimal sum: one county and month with obligations `0.10`, `0.20`, `-0.05` gives `0.25` as `DECIMAL(18,2)`. Ten rows of `0.10` give `1.00`.
  - Bucket rules: three rows give three buckets. A non-US place of performance gives state `FOREIGN` and county `FOREIGN`. A US place with blank county FIPS gives county `UNKNOWN` and its own state. A US place with county `01001` gives county `01001`.
  - G-2 failure: one FY2024 row with `action_date` `2024-10-01` makes `engine run` exit non-zero. The message names the file and the row.
  - Sort order: lake rows are sorted by `transaction_key` ascending.
- Phase 3 (dbt singular tests on `transform/tests/fixtures/lake`, created in Phase 3):
  - Reconciliation: source total `1000.00`, county sum `1000.00`, state sum `1000.00`, both differences `0.00`.
  - Population uniqueness: two population rows for county `01001` make the test fail (count `2`).
  - Decimal type: the obligations column must be `DECIMAL(18,2)`. A `DOUBLE` column fails.
- Phase 4 (check views): each check has `transform/tests/fixtures/expected/check_<n>.csv` for checks 1 to 4. The singular test compares the view with it row for row. Check 2 includes a tie: two counties with equal per-person values are ordered by county FIPS ascending.
- Phase 5 (fake SSE server, in `engine/tests/`):
  - Crash: the fixture stream is ids `e1` to `e10`. After the kill between the tmp write and the rename, and the restart, the set of `meta.id` in the lake is exactly `e1` to `e10`, each once.
  - Disconnect: the same ten ids, each once, and the footer `last_sse_id` is `e10`.
- Phase 6 and Phase 7: the expected window rows and the check 5, 6 and 7 rows are in `expected` files, named in cd-1-F03.

### cd-1-F03: checks 5 to 7 tests (Phase 7)

Phase 7 TDD adds three tests, on the Phase 6 fixture stream (`transform/tests/fixtures/pipelines/stream_test.yml`):
- `test_check_5_edit_and_bytes`: one row per wiki and actor type, with `edit_count` and `net_bytes`, from `expected/check_5.csv`. A `log` or `categorize` event in the input is not counted (G-6). A late `edit` is counted (check 5 counts all `edit` and `new` events).
- `test_check_6_top_windows_tie`: `en.wikipedia.org` windows at 12:00, 12:05 and 12:10 UTC with on-time counts 2, 2 and 3. A late edit in another window is excluded. The expected top list is 12:10 (3), then 12:00 (2), then 12:05 (2), by N-5 ascending `window_start` on the tie.
- `test_check_7_late_count`: the count of late first arrivals, from `expected/check_7.csv`. A duplicate `meta.id` is not counted again.

### cd-1-F04: cases a mutant would pass

Each case is one row of a parametrized table. One table per module.
- Rounding (Phase 3, singular test `test_per_person_rounds_half_away_from_zero`): obligations `0.25` over population `2` gives per-person `0.13`. Obligations `-0.25` over `2` gives `-0.13`. Banker's rounding and float rounding both give `0.12`, so they fail.
- Edit types (Phase 5, `engine/tests/test_stream_transforms.py`, table `test_change_type_counts`): `edit` and `new` are edits; `log` and `categorize` are kept in the fact and are not edits. Phase 6 adds the singular test `test_window_counts_only_edit_and_new`, where a `log` and a `categorize` event in an on-time window do not change `edit_count`.
- Null length (same table, `test_length_delta_and_has_length`): old null and new `100` gives delta `0` and `has_length` false. Old `100` and new null gives delta `0` and `has_length` false. Old `100` and new `150` gives delta `50` and `has_length` true.
- Window start (same table, `test_window_start_utc`): epoch seconds at 12:04:59 UTC give 12:00:00, at 12:05:00 give 12:05:00, and at 12:09:59 give 12:05:00. The test runs with `TZ=America/New_York` and gives the same result.
- SUMLEV filter (Phase 2 batch transform test module, `test_census_keeps_sumlevel_050`): a census fixture with SUMLEV `040`, `050` and `060` rows keeps only the `050` rows.

### cd-1-F05: restart equals one run (Phase 6, minor)

Phase 6 adds `test_restart_matches_single_run_window` (marked `integration`, see cd-1-F06). The fake SSE server stops in the middle of a batch, the engine restarts on `stream_test.yml`, and the window mart is built. The sorted window rows equal those of one uninterrupted run over the same fixture stream.

### cd-1-F06: integration placement (Phase 7, minor)

`test_make_build_twice_same_rows` moves to `engine/tests/integration/test_make_build_twice.py` and carries `@pytest.mark.integration`. The marker is registered in `pyproject.toml` in Phase 1. Unit gate: `uv run pytest engine/tests -m "not integration"`. Integration gate: `uv run pytest engine/tests -m integration`. Phase 7 names the `outputs/` path (`outputs/summary.md`, `outputs/PR.md`) in its scope line.

## Revision ledger (review 64db58631998)

No `MF-n` is open in review 64db58631998, so the ledger has no rows.

## Revision ledger (scorecard 6acb5c150ea6)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| cd-1-F01 | Named test helpers: `run_cli` and `hash_snapshot` in `engine/tests/support.py` (Phase 4); `fake_sse_server` fixture in `engine/tests/conftest.py` (Phase 5, imported by Phase 6) | This update, section 4 (cd-1-F01); Phases 4, 5, 6, 7 | `test_fixture_run_leaves_real_warehouse_unchanged`, `test_phase6_run_leaves_real_stream_lake_unchanged` and `test_make_build_twice_same_rows` import `support.py`; `grep -rn "def fake_sse_server" engine/tests` finds one definition |
| cd-1-F02 | Expected values for each named test: exact expected rows in fixture expected files; empty output fails | This update, cd-1-F02; Phases 2, 3, 4, 5, 6, 7 | Each named test compares exact rows with its expected file; a run with no rows fails |
| cd-1-F03 | Phase 7 tests for checks 5, 6 and 7, with the tie case for check 6 | This update, cd-1-F03; Phase 7 | `test_check_5_edit_and_bytes`, `test_check_6_top_windows_tie`, `test_check_7_late_count` in `transform/tests/` |
| cd-1-F04 | Boundary and mutant cases as parametrized rows: half-away rounding, edit types, null length, UTC window start, SUMLEV 050 | This update, cd-1-F04; Phases 2, 3, 5, 6 | `test_per_person_rounds_half_away_from_zero`, `test_change_type_counts`, `test_length_delta_and_has_length`, `test_window_start_utc`, `test_census_keeps_sumlevel_050`, `test_window_counts_only_edit_and_new` |
| cd-1-F05 | Restart run equals one run for the window mart (minor, applied) | This update, cd-1-F05; Phase 6 | `test_restart_matches_single_run_window` (integration marker) |
| cd-1-F06 | Double-build test moves to the integration directory and marker (minor, applied) | This update, cd-1-F06; Phase 1 (marker), Phase 7 | `uv run pytest engine/tests -m "not integration"` excludes it; `uv run pytest engine/tests -m integration` runs it |
