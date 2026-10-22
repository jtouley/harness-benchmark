RUN_BY_COMMAND: plan-update
Pipeline-Run: 1a240cbc-2484-4175-b2ce-b76ba5272a21

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Ticket token: cd-1 (GitHub issue gh-1, branch feature/gh-1-pipeline)

# Plan: open-data pipeline (gh-1, cd-1)

Inputs: `.context/proposals/cd-1.md` (sha256 1b0078a7...), `.context/vibetest/cd-1_2026-10-21.md`
(sha256 87234335..., verdict NOT READY FOR PLANNING, blocking gaps G-1 to G-6). Each G-n has an
assumption row in `.context/deferrals/cd-1_deferral-register.md`. This plan builds those assumptions.
Plan review (P3) must confirm them before E1.

Plan history: this file is a fresh plan-create run (see `.context/issues/cd-1.md`). Its content is the
cycle-1 plan (sha256 117b4404...) with review items MF-1 to MF-6 of `.context/reviews/plan_cd-1-pipeline.plan.md`
applied in the phase text. Each MF-n is named where it is applied, so the next review can check it.

## Goal

Build one pipeline that answers two questions:

- (A, batch) Where federal contract and grant money went in FY2024: total and per person, by state,
  county, awarding agency and month.
- (B, stream) How Wikipedia is being edited now: edits per wiki, namespace and 5-minute UTC window,
  split human and bot, with net bytes added.

## Constraints

- Python 3.12. `pyproject.toml` pins stay as they are: dlt[parquet] 1.31.0, dbt-core 1.11.6,
  dbt-duckdb 1.11.0, duckdb 1.5.6. No new runtime dependency. Stream client uses stdlib `urllib`.
- Lake under `lake/` (dlt, Parquet). dbt-duckdb in `transform/`. Published marts in `out/marts/`
  through external materialization.
- `make build` idempotent. `make stream DURATION=<s>` resumable with no double count and no loss.
- Windows are 5 minutes, UTC. Late = stream time more than 10 minutes past window end at first arrival.
  Late events go to `late_events`.
- Money sums are exact (no float anywhere in the money path).
- `lake/` and `out/` are generated and gitignored. `data/raw/` is read only.

## Non-goals

- No dashboard, no scheduler, no cloud deployment.
- No restatement of published 5-minute windows after a late event.
- No change to `data/raw/` or to `pyproject.toml` / `uv.lock` pins.
- No test against the live stream. Tests use a local fake SSE server.

## Success signals

- `make build` exits 0 on a clean checkout. `make stream DURATION=60` exits 0 while the endpoint is up, and
  exits 3 when it is down (Phase 6, MF-11).
- A second `make build` gives byte-identical files in `out/marts/`.
- Each check 1 to 7 (see Phase 8 and assumption G-1) passes.
- Every decision record in `.context/proposals/cd-1-*.md` has a row in the P9 coverage check.

## Step 0: problem, design, blast radius, acceptance

### Problem restatement

Two pipelines in one repo. Batch: 8 USAspending zip files (4 agencies x contracts/assistance), two
Census county vintages, and the sitematrix wiki list. Stream: SSE events from a local endpoint. Both
feed one star schema in dbt-duckdb.

### Weak scope, challenged in the plan text

- The issue text is not on disk. Checks 1 to 7 are unknown (G-1). This plan writes its own checks 1 to 7
  from the rules the spec does state (Phase 8). The plan review must replace them with the issue text
  if the issue differs.
- "Idempotent", "stream time", "dedupe key" and "geography" are undefined in the spec (G-2 to G-6). Each is
  settled by a decision record (D1 to D6) and a test. None is left as a silent guess.
- Census gives population by state and county only. Per-person by agency or by month needs a national
  denominator (D5). This is a choice, not a fact in the source.

### Design decisions (one decision record each)

| ID | Decision | Record |
|---|---|---|
| D1 | Money types: DECIMAL(18,2) for amounts, DECIMAL(38,6) for per-person ratios | `cd-1-money-decimal` |
| D2 | Stream dedupe key is `meta.id`; checkpoint is the last committed event id | `cd-1-stream-dedupe-checkpoint` |
| D3 | Stream time is a watermark over arrival order; late rule and no restatement | `cd-1-late-event-watermark` |
| D4 | Windows are half-open `[start, end)` UTC, 300-second floor on epoch seconds | `cd-1-window-boundary` |
| D5 | Population: July 1 2024 estimate; national denominator for agency and month; fallback rule | `cd-1-population-denominator` |
| D6 | Storage: dlt Parquet in `lake/`; dbt-duckdb reads it; marts published as external Parquet | `cd-1-lake-storage` |

### Blast radius

- New: `pipeline/` (Python package: sources, build and stream entry points), `tests/`, `transform/models/`
  (staging, marts, `schema.yml`), `transform/tests/` (dbt singular tests, MF-3 and Phase 4), `oracle_map.yml`,
  `DECISIONS.md`.
- Changed: `Makefile` (`build` and `stream` targets are stubs now).
- Generated, not committed: `lake/`, `out/`, `transform/target/`.
- Rollback: `git revert` of the phase commits, then remove the gitignored `lake/`, `out/` and `transform/target/`.
- Unchanged: `pyproject.toml`, `uv.lock`, `data/raw/`, `transform/profiles.yml` (target path stays
  `out/warehouse.duckdb` as the dev database; published marts do not depend on it).

### Acceptance

The build passes Phases 1 to 9 and the checks in Phase 8. Each phase lists its own exit criteria.

## Assumptions (one per vibe-test gap; rows in the register)

- G-1: Checks 1 to 7 are the rules of Phase 8, not the issue text. Settled by Phase 8 tests and the P3 review.
- G-2: Money is `federal_action_obligation`. Sign is kept as recorded (de-obligations stay negative, no
  `abs()`). Scale is 2 decimals; a value must match `-?[0-9]+(\.[0-9]{1,2})?` or it fails ingest. Settled by Phase 2.
- G-3: Geography is place of performance: state FIPS `prime_award_transaction_place_of_performance_state_fips_code`
  and county FIPS `prime_award_transaction_place_of_performance_county_fips_code`, in all eight zips. The
  bucket rules of Phase 4 `dim_geography` apply. Blank county, or a county FIPS not in the 2024 county rows,
  goes to `<state_fips>-UNKNOWN-COUNTY`: in state totals, not in county totals. Territory rows go to
  `OUTSIDE-50-STATES-DC` and blank-state rows to `UNKNOWN-STATE`; both are in money totals and in no per-person row.
  Settled by Phase 4.
- G-4: Per-person for agency and month uses the national population (sum of the 3,144 county rows,
  July 1 2024). The numerator and denominator cover the 51 state geographies only. Settled by Phase 4 and D5.
- G-5: Dedupe key is `meta.id`. Checkpoint is the last committed `Last-Event-ID` and `arrival_seq`. If the
  endpoint does not honor `Last-Event-ID` (R-2), resume reconnects and dedupe keeps counts exact for replayed
  events. This build does not detect events that the endpoint skips during a disconnect, and writes no gap
  report (MF-8). Settled by Phase 6.
- G-6: Stream time is the watermark defined in D3. Late events are not restated. Settled by Phase 7.
- N-1 to N-8 (non-blocking, from the vibe-test): settled in Phases 2 to 7, each recorded in DECISIONS.md.

## Reuse and extension

- Reuses existing: `dlt` (`dlt.resource`, `dlt.pipeline`, column hints for `decimal`), `dbt-duckdb`
  external materialization, stdlib `zipfile`, `csv`, `urllib`, `json`, `unittest`. No helper exists in
  this repo yet (`pipeline/` and `tests/` are new). Shared test helpers (zip fixture builder, fake SSE server,
  census readers) go in `tests/support.py`, not `tests/conftest.py`: the suite runs under `unittest discover`,
  which does not load `conftest.py`.
- Extension point added: one dlt resource per source in `pipeline/sources/`, and one dbt layer per
  concern (`staging`, `marts`). A new source adds one resource and one staging model.

## Quality gates (real commands in this repo)

- `uv sync --frozen`
- `uv run python -m unittest discover -s tests -t .`
- `uv run dbt parse --project-dir transform --profiles-dir transform`
- `uv run dbt build --project-dir transform --profiles-dir transform`
- `make build`
- `make stream DURATION=60`
- `git diff --exit-code -- pyproject.toml uv.lock`

No make target other than `build` and `stream` is added or assumed.

Commit checkpoints: one commit per phase on `feature/gh-1-pipeline`, message `P<n>: <phase name>`.

### Phase 1: Skeleton, environment and gates

Scope: create `pipeline/__init__.py`, `pipeline/build.py`, `pipeline/stream.py` (stubs that raise
`NotImplementedError`), `tests/__init__.py`. Set the Makefile: `build` runs
`uv run python -m pipeline.build`; `stream` requires `DURATION` (fail with a usage line when missing) and
runs `uv run python -m pipeline.stream --duration $(DURATION)`.
Create `DECISIONS.md`. This phase is the only one that creates it. It has one heading for each of D1 to D6
and N-1 to N-8, each with the rule and the rejected option. Phases 2 to 8 fill their sections (MF-6).

TDD: first write `tests/test_makefile.py` that asserts `make stream` without `DURATION` exits non-zero and
prints `DURATION`. Then the Makefile.

Exit criteria:
- `uv sync --frozen` exits 0.
- `uv run python -m unittest discover -s tests -t .` exits 0.
- `uv run dbt parse --project-dir transform --profiles-dir transform` exits 0.
- `git diff --exit-code -- pyproject.toml uv.lock` exits 0.
- `DECISIONS.md` has 14 headings (D1 to D6, N-1 to N-8).

### Phase 2: Batch ingest, USAspending

Scope: dlt resource `usaspending_transactions` in `pipeline/sources/usaspending.py`. Read each zip with
`zipfile` and `csv` in streaming mode. Never extract into `data/raw/`. Keep these columns. Each name was
checked against the headers of all eight zips:
- Both award types: `federal_action_obligation`, `action_date`, `awarding_agency_code`, `awarding_agency_name`,
  `prime_award_transaction_place_of_performance_state_fips_code` (2-digit state FIPS) and
  `prime_award_transaction_place_of_performance_county_fips_code` (5-digit county FIPS).
- Derived fields, not header columns (MF-7): `source_file` (the zip member name) and `award_type`
  (`contracts` or `assistance`, from the zip file name). The reader sets them. No zip has them as a header.
- Unique key: `contract_transaction_unique_key` for Contracts zips; `assistance_transaction_unique_key` for
  Assistance zips. Stored as one column `transaction_unique_key`, with `award_type`.
- Not used: `primary_place_of_performance_state_code` and `primary_place_of_performance_state_name`. The
  2-letter state code exists only in the Contracts zips. The state FIPS column is the one state column that all
  eight zips share (MF-2).
- `toptier_code` is not a column of any zip. The agency columns are the `awarding_agency_*` pair above.
- Source is FY2024 only. A row whose `action_date` is outside 2023-10-01 to 2024-09-30 fails ingest, so a
  later zip cannot change Goal (A) without notice.

TDD (header test first): for each zip type (`contracts`, `assistance`), a test reads only the header and asserts
the header columns above. The derived fields are not asserted. A missing column fails the test before any row is read. Test names:
`tests/test_usaspending_headers.py::test_contracts_headers` and `::test_assistance_headers`.

Typing: `federal_action_obligation` as dlt column hint `{"data_type": "decimal", "precision": 18, "scale": 2}`
(D1). Before `decimal.Decimal` parses a value, the value must match the regex `-?[0-9]+(\.[0-9]{1,2})?` (MF-4; ASCII digits only, so `re.ASCII` is not needed). A value
that does not match fails ingest. This includes an empty value, `1e3`, `+1`, `1,000` and a value with more than
2 decimals. All eight zips match the pattern and have no empty amounts.
Write disposition `replace` per build (full rebuild from raw; N-7).

TDD: tests build small zip fixtures in a temp dir at test time (no binary fixtures committed). The fixture
builder lives in `tests/support.py` (see Reuse and extension). Tests:
- `test_amount_pattern` (in `tests/test_usaspending_ingest.py`): accept `1234567.89`, `-0.01`, `0`, `12.5`; reject
  `1e3`, `1.005`, `+1`, `1,000` and an empty value. The check is the regex, then `Decimal`.
- row count of the lake equals the CSV data row count for each fixture zip.

Exit criteria:
- Over all 8 real zips, the lake row count equals the sum of CSV data rows (checked by a script that
  counts with `csv`, not `wc`, because of quoted newlines).
- `SUM(federal_action_obligation)` in DuckDB equals the `Decimal` sum computed from the source CSVs (exact
  equality, no tolerance).

### Phase 3: Reference ingest, Census and sitematrix

Scope:
- `pipeline/sources/census.py`: read `co-est2024-alldata.csv` (primary) and `co-est2021-alldata.csv`
  (fallback only, D5). Keep SUMLEV 040 (state) and 050 (county). County FIPS = `STATE` (2) + `COUNTY` (3).
  Keep `POPESTIMATE2020` to `POPESTIMATE2024` from the 2024 file and `POPESTIMATE2020`, `POPESTIMATE2021`
  from the 2021 file, as typed integers.
- `pipeline/sources/sitematrix.py`: flatten numeric language keys and the `specials` list. One row per
  site entry, with `dbname`, `url`, `code`, `sitename`, `closed` (null when absent). The stream `wiki`
  field joins to `dbname` (N-3).

TDD: tests on the real `sitematrix.json` and on the census file headers (no full scan needed in unit tests).
Assert: 3,144 county rows and 51 state rows in the 2024 file; `dbname` is unique across the flattened list.

Exit criteria:
- Lake contains 51 state rows and 3,144 county rows for the 2024 vintage.
- `dbname` unique count equals the flattened row count (no duplicate join keys).

### Phase 4: Star schema and batch marts

Scope, in `transform/models/`:
- `staging/stg_usaspending_transactions.sql`, `stg_census_population.sql`, `stg_sitematrix_wikis.sql`.
- Dimensions:
  - `dim_agency` (awarding_agency_code, awarding_agency_name).
  - `dim_month` (month_key from `action_date`, UTC date, month start).
  - `dim_wiki` (MF-1): one row per sitematrix `dbname` from `stg_sitematrix_wikis` (`wiki_key`, `url`, `code`,
    `sitename`, `closed`), plus one `unknown` row for stream wikis that match no `dbname` (N-3).
  - `dim_geography` (G-3, MF-3). Each fact row gets one `geography_key` from its state FIPS and county FIPS. The
    rules apply in this order:
    1. Blank state FIPS: `UNKNOWN-STATE` (57 rows in the eight zips).
    2. State FIPS 60, 66, 69, 72 or 78 (US territories): `OUTSIDE-50-STATES-DC`.
    3. Any other state FIPS that is not one of the 51 state rows of the 2024 census file: the build fails.
    4. Blank county FIPS, or a county FIPS that is not one of the 3,144 county rows of the 2024 census file:
       `<state_fips>-UNKNOWN-COUNTY`.
    5. Otherwise the county FIPS.
    Rule 4 covers the 16 Connecticut rows with 2021 county codes (09001 to 09015). No 1:1 crosswalk from those
    codes to the 2022 planning regions (09110 to 09190) is in the packet, so they are not mapped to a region.
    They go to `09-UNKNOWN-COUNTY`. The dimension holds the 3,144 county rows, the 51 state rows, one
    `<state_fips>-UNKNOWN-COUNTY` per state, `UNKNOWN-STATE` and `OUTSIDE-50-STATES-DC`. Each fact row also
    carries `state_fips`, and state totals group by it.
- Fact: `fct_award_transaction`, grain one row per prime award transaction (the unique key from Phase 2),
  keys to `dim_agency`, `dim_geography` and `dim_month`, measure `federal_action_obligation` as `DECIMAL(18,2)`.
- Marts (external Parquet to `out/marts/`, see D6):
  - `mart_money_monthly`: money by month, state, county, agency.
  - `mart_money_per_person`: money per person by state, county, agency and month. Denominator per D5:
    state and county use July 1 2024 population of that geography; agency and month use the national
    population. Ratio is `DECIMAL(38,6)`, rounded half-up at this step only (D1). Each row carries
    `population_source` with one of these values: `co-est2024` (POPESTIMATE2024 of the 2024 file),
    `co-est2024-<year>` (the fallback column POPESTIMATE<year> of the 2024 file), `co-est2021-<year>` (a column
    of the 2021 file), or `none` (no county population, see below). Fallbacks are visible by these values.
    The per-person numerator and denominator cover the 51 state geographies only, that is 50 states and DC,
    including their `<state_fips>-UNKNOWN-COUNTY` rows. Money in `OUTSIDE-50-STATES-DC` and `UNKNOWN-STATE`
    is in `mart_money_monthly` but in no per-person row (MF-3 b). The national population for agency and month
    is the sum of the 3,144 county rows of the 2024 census file. A `<state_fips>-UNKNOWN-COUNTY` row has no county
    population, so its per-person value is NULL and its `population_source` is `none`.

Schema tests in `transform/models/schema.yml`: `unique` and `not_null` on keys (`dim_wiki.wiki_key` included),
`relationships` from the fact to each batch dimension.

TDD: dbt singular tests in `transform/tests/` for:
- the sum of all `mart_money_monthly` rows equals the Phase 2 source sum (buckets included);
- the 51 state geographies plus `OUTSIDE-50-STATES-DC` plus `UNKNOWN-STATE` equal the national total (G-3, G-4);
- within each state, the county rows plus `<state_fips>-UNKNOWN-COUNTY` equal the state total;
- a row with county code 09001 lands in `09-UNKNOWN-COUNTY`, and a row with state 72 lands in `OUTSIDE-50-STATES-DC`
  (file `transform/tests/geography_buckets.sql`);
- the national per-person denominator equals the sum of the 3,144 county rows.

Exit criteria:
- `uv run dbt build --project-dir transform --profiles-dir transform` exits 0.
- Sum of `federal_action_obligation` in `fct_award_transaction` equals the Phase 2 source sum.

### Phase 5: Idempotent build

Scope: `pipeline/build.py` runs, in order: batch ingest (Phases 2 and 3, replace), `dbt build`, publish
marts to `out/marts/*.parquet`, write `out/build_report.json` (row counts per table, fallback counts from D5, and
the share of fact rows in `<state_fips>-UNKNOWN-COUNTY` and in the two buckets of Phase 4). The build reports
these shares and does not gate on them. The sample read showed 79% of rows with a blank county. The
report field `stream_available` is added in Phase 7 and `oracle_map.yml` is written in Phase 8 (MF-6).
`DECISIONS.md` is created in Phase 1. This phase adds the N-7 entry (the idempotence method).

Idempotence (N-7): build from empty `lake/` and `out/`; hash `out/marts/*`; build again without cleaning;
hash again. The hashes must match. Parquet writes use a fixed `ORDER BY` on the key and a fixed row group
size. If DuckDB Parquet output is not byte-stable, the check falls back to a sorted row hash and DECISIONS.md
records that choice.

TDD: test in `tests/test_build_idempotent.py` runs the build twice on a fixture subset (`PIPELINE_FIXTURE=1`
reads two small zips, not the full set).

Exit criteria:
- `make build` exits 0 twice in a row; `sha256sum out/marts/*` is identical after both runs.
- `out/build_report.json` has the row counts, the fallback counts and the UNKNOWN-COUNTY and bucket shares.

### Phase 6: Stream ingest, resumable

Scope: `pipeline/sources/stream.py` and `pipeline/stream.py`. SSE client on `urllib` to
`http://localhost:8099/v2/stream/recentchange`. Parse `id:` and `data:` lines. Keep the event `meta.id`,
`meta.dt`, `wiki`, `namespace`, `type`, `bot`, `timestamp`, `length` (`old`, `new`), `user`, `title`.

Dedupe (D2): the stream table in the lake is merged on `meta.id`. A replay of an event that is already
committed changes nothing.

Arrival sequence (MF-9): `arrival_seq` is set on the first insert of a `meta.id` only. In one commit, each new
`meta.id` gets `arrival_seq` = (max `arrival_seq` already in the lake) + its 1-based position among the new ids
of that batch, in batch order. The merge does not change `arrival_seq` of an existing `meta.id`, so a replay keeps
its first value. The merge and the checkpoint of a batch are one commit, in that order.

Endpoint down (MF-11): when the connection is refused or the response status is not 200, `pipeline/stream.py`
writes nothing to `lake/`, leaves the checkpoint unchanged, prints one line that names the URL and the reason,
and exits 3.

Checkpoint (D2): `lake/stream/_checkpoint.json` holds the last committed `Last-Event-ID` and the last
committed `arrival_seq`. Written after the batch is committed to the lake, through a temp file and
`os.replace`. On start, send `Last-Event-ID` when the checkpoint has one.

`DURATION` is wall-clock seconds. The run commits in batches of `batch_size` events (default 100, a parameter
so that tests can use 5) or at exit, whichever is first, then exits 0. A commit merges the batch into the lake on
`meta.id`, then writes the checkpoint with the id of the last event of that batch.

Probe (R-2): one manual `curl` with a 5 s timeout checks whether the endpoint honors `Last-Event-ID`. Its
result goes into DECISIONS.md. The code does not depend on the answer for dedupe. The answer changes no output
of this build, because the build writes no gap report (MF-8).

TDD: `tests/test_stream_resume.py` runs a fake SSE server (stdlib `http.server`, on a random port). It sends
10 events with ids `1` to `10` and records the `Last-Event-ID` header of each request. The helpers live in
`tests/support.py`.
- `test_resume_sends_last_event_id_of_batch` (the server honors `Last-Event-ID`): the client runs with
  `batch_size=5` and a test hook that raises `SimulatedKill` right after the first batch commit. Events 1 to 5 are
  then committed and the checkpoint names event 5. The second run must send `Last-Event-ID: 5`, and it must end with
  exactly 10 rows and no duplicate `meta.id` (MF-5).
- `test_server_ignores_last_event_id`: the same kill, but the server replays events 1 to 10 on reconnect. The
  result must still be 10 rows with no duplicate `meta.id`.
- `test_replayed_event_keeps_first_arrival_seq` (MF-9): the same scenario as the previous case. After the second run,
  events 1 to 5 keep `arrival_seq` 1 to 5 from the first run, and events 6 to 10 get `arrival_seq` 6 to 10.
- `test_endpoint_down_exits_3_writes_nothing` (MF-11): `pipeline/stream.py` runs against a local port with no
  listener, then against a fake server that answers 500. Each run exits 3, creates no `lake/stream/`, and writes
  no checkpoint.

Exit criteria:
- The four fake-server and endpoint cases above pass.
- `make stream DURATION=60` followed by `make stream DURATION=60` gives no duplicate `meta.id` in the lake.

### Phase 7: Edit fact and 5-minute window mart

Scope:
- `stg_stream_events` joins `wiki` to `dim_wiki` (Phase 4, from sitematrix `dbname`). Unmatched wikis get
  `wiki_key = 'unknown'` (N-3). `schema.yml` adds a `relationships` test from `fct_edit.wiki_key` to
  `dim_wiki.wiki_key` (MF-1).
- `build_report.json` gets the field `stream_available` (MF-6, the stream field moved here from Phase 5).
- `fct_edit` grain: one row per stream event `meta.id`. `is_bot` from `bot`. `namespace` from `namespace`.
  `net_bytes_added = length.new - length.old` for type `edit` and `new` only when both lengths are present.
  A null length is excluded from net bytes and still counted in edit totals by type (N-2).
- Windows (D4): `window_start = floor(timestamp / 300) * 300` (epoch seconds, UTC), window is
  `[window_start, window_start + 300)`. An event at exactly `window_start + 300` belongs to the next window.
- Late rule (D3): events are ordered by `arrival_seq` (the position of first arrival in the lake). The
  watermark before event `k` is the max event `timestamp` among events with `arrival_seq < k`. Event `k` is
  late when `watermark > window_start + 300 + 600` at its first arrival. Late events go to `late_events`
  with `late_reason = 'watermark'` and the watermark value. They do not enter `mart_edit_window_5min`, and no
  published window is restated (G-6).
- `mart_edit_window_5min` grain `(window_start, wiki_key, namespace, is_bot)`. Measures: `edits_total`,
  `edits_by_type`, `net_bytes_added`. A window with no events has no row (N-8). A missing stream (no lake
  stream table) makes the build record `stream_available = false` in `out/build_report.json` and still exit 0.
  Then `pipeline/build.py` runs `dbt build` without the stream models (`stg_stream_events`, `fct_edit`, `late_events`,
  `mart_edit_window_5min` and their tests), and publishes only the batch marts (MF-10). With a stream table present,
  all marts are built and published.

TDD: tests on fixture events in `tests/test_windows.py`:
- event at `12:04:59.999` goes to the 12:00 window; event at `12:05:00` goes to the 12:05 window (D4);
- event whose watermark is 11 minutes past its window end goes to `late_events`; the same event at 9 minutes
  past stays in the window mart (boundary of D3);
- a duplicate `meta.id` does not re-evaluate lateness (first arrival only).

Exit criteria:
- The three test cases above pass.
- `SUM(edits_total)` in the window mart plus `COUNT(*)` in `late_events` equals `COUNT(*)` in `fct_edit`
  (every event is in exactly one place).

### Phase 8: Oracle map, DECISIONS and checks 1 to 7

Scope:
- `oracle_map.yml`: one entry per published mart (name, path, grain, keys, measures, source models, checks).
  Format is this plan's choice (N-5). PyYAML is not a pinned dependency, so the build writes JSON text,
  which is valid YAML, and the test reads it back with `json`. `pipeline/build.py` writes it as its last step,
  after publish (MF-6).
- `DECISIONS.md` (created in Phase 1): complete D1 to D6 with the rule and the rejected option; N-1 to N-8 decisions;
  the R-2 probe result (Phase 6). N-1 records the D5 fallback order: `POPESTIMATE2023`, 2022, 2021, 2020 from
  co-est2024, then co-est2021. This differs from the vibe-test N-1 wording on purpose.
- `tests/test_checks.py` implements checks 1 to 7. These are the plan's checks (G-1), not the issue text. It reads
  the built output in `out/marts`, so `make build` runs first (Phase 9 step 7 does this). Checks 1, 2, 3, 4, 6
  and 7 read the built `out/`. Check 5 runs its own fake server and does not read `out/`:
  1. Build idempotent: two builds give identical `out/marts/*` hashes (Phase 5).
  2. Exact money: fact sum equals the Decimal sum of the source CSVs.
  3. Geography totals: the 51 state geographies plus `OUTSIDE-50-STATES-DC` and `UNKNOWN-STATE` sum to the national
     total. Within each state, the county rows plus `<state_fips>-UNKNOWN-COUNTY` sum to the state total.
  4. Per person: `mart_money_per_person` ratio equals sum / population for the row's `population_source`. A
     `<state_fips>-UNKNOWN-COUNTY` row has NULL and `none`. No bucket appears in a per-person row. Fallback rows
     are counted in `build_report.json`.
  5. Stream resume: no duplicate `meta.id`, no loss against the fake server (Phase 6).
  6. Windows: each event falls in exactly one half-open UTC 5-minute window (Phase 7).
  7. Late routing: every late event is in `late_events` and in no window row (Phase 7).

Exit criteria:
- `uv run python -m unittest discover -s tests -t .` exits 0 including `test_checks.py`, run after `make build`.
- `DECISIONS.md` has one section per D-n and per N-n.
- `grep -n "oracle_map" pipeline/build.py` shows the write only as the last step of the build (MF-6).

### Phase 9: Final verification on a clean tree

Scope: no code changes unless a gate fails.

Precondition: the endpoint at `http://localhost:8099` is up (Phase 6). Steps, in order:
1. `rm -rf lake out transform/target`.
2. `make build`. No stream table exists yet, so the build publishes batch marts only. Its hashes are not compared.
3. `make stream DURATION=60`.
4. `make build`; keep the output of `sha256sum out/marts/*` as H1.
5. `make build` again; keep the output of `sha256sum out/marts/*` as H2. H1 must equal H2. Both builds run after step 3.
6. `make stream DURATION=60`; check for duplicate `meta.id` (query in `tests/test_checks.py`).
7. `make build`, so that `out/` matches the lake after step 6.
8. Run every quality gate listed above.
9. `git status --short` shows only the files in Blast radius, and `lake/`, `out/` are ignored.

Exit criteria: every step exits 0; H1 equals H2; `pyproject.toml` and `uv.lock` are unchanged.

## Revision ledger

None. This is the first plan version of this run's plan-create.

## Plan update 2026-10-21

Answers `.context/reviews/plan_cd-1-pipeline.plan.md` (cycle 2, READY WITH CHANGES, sha256 9c180b13b589...).
The review's MF-7 to MF-11 are applied. Each change is named in the phase it touches.

- MF-7: `source_file` and `award_type` are derived fields, not header columns. The header test asserts only the header names.
- MF-8: the gap-report claim is removed. G-5, the R-2 probe text and the register row no longer claim a gap report.
  The build writes none. The issue text is not on disk, so the P3 review must confirm this removal against it.
- MF-9: `arrival_seq` has an assignment rule (first insert, batch order, merge keeps it) and a test.
- MF-10: Phase 9 compares two builds that both run after the stream run. With no stream table, the build publishes batch marts only.
- MF-11: `make stream` exits 3 when the endpoint is down or answers non-200, with no lake write and no checkpoint change. Test added.

Notes from the review applied: the blast radius lists `transform/tests/`; the amount regex uses `[0-9]`; `population_source`
values are named; the Connecticut code range is 09001 to 09015; the Phase 8 check ordering is stated; commit checkpoints per phase.

Notes not applied (open for the next review): the dlt write disposition that merges into Parquet under `lake/`, and its support at
dlt 1.31.0. This update did not run dlt.

## Revision ledger (review 9c180b13b589)

| Id | Change | Where (phase or section) | Verification (the test or check that proves it) |
|---|---|---|---|
| MF-7 | `source_file` and `award_type` are derived fields; the header test asserts only header names | Phase 2 scope and TDD | `tests/test_usaspending_headers.py::test_contracts_headers`, `::test_assistance_headers` |
| MF-8 | Gap-report claim removed from G-5, R-2 probe text and the register row | Assumptions G-5; Phase 6 probe; `.context/deferrals/cd-1_deferral-register.md` | `grep -c "logged as \`gap\`" .context/plans/cd-1-pipeline.plan.md` returns 0 |
| MF-9 | `arrival_seq` assigned on first insert in batch order; merge keeps it | Phase 6 "Arrival sequence" and TDD | `tests/test_stream_resume.py::test_replayed_event_keeps_first_arrival_seq` |
| MF-10 | Phase 9 compares H1 and H2, both built after the stream run; batch-only publish without a stream table | Phase 9 steps 2 to 5; Phase 7 publication | Phase 9 exit criterion H1 equals H2 (`sha256sum out/marts/*`) |
| MF-11 | `make stream` exits 3 when the endpoint is down or answers non-200; no lake write, no checkpoint change | Phase 6 "Endpoint down"; Success signals; Phase 9 precondition | `tests/test_stream_resume.py::test_endpoint_down_exits_3_writes_nothing` |
