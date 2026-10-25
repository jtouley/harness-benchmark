# Explanation: branch `review` vs `base`

Scope: `git diff base...review` in the repo copy. 45 files, +2085 / -2. The single commit is "Change under review" (no message body). The spec the code cites (A-, G-, N- ids) is not in my copy, so the spec itself was not checked; the checks below are against the code and `DECISIONS.md`.

## What it does

The base has `make build` and `make stream` as stubs that exit 1. This change implements both as a two-part data pipeline.

1. **Batch path (`make build`)**
   - `pipeline/batch_load.py` (dlt) extracts the USAspending FY2024 contract and assistance zips, the Census 2024 and 2021 county estimate files (Latin-1), and the Wikimedia sitematrix JSON into `lake/<table>/` as Parquet, replacing each table per run.
   - dbt builds a star schema (`fact_award_transaction`, `dim_agency`, `dim_place`, `dim_date`) and publishes `mart_monthly_obligations` (per county, agency and month, with exact `obligations_per_person`) and `mart_award_fy2024` to `out/marts/`.
   - Thirteen place codes missing from the 2024 Census file are handled explicitly: six Connecticut codes fall back to the 2021 estimate, seven territory codes get a null population.

2. **Stream path (`make stream DURATION=60`)**
   - `pipeline/stream_consumer.py` reads the Wikimedia recentchange SSE stream (`STREAM_URL`, default in `.env.example`). It lands every unique event in `lake/stream_raw/`, edits and new pages in `lake/stream_events/`, and a checkpoint in `lake/stream_checkpoint/`.
   - Dedup is on `meta.id` against `stream_raw`. Reconnects send `Last-Event-ID`. A high-water mark is kept across runs.
   - `pipeline/lateness.py` assigns 5-minute windows (UTC) and marks an event late when the highest earlier event time is more than 600 s past its window end (strict).
   - dbt models `fact_edit`, `window_5min` (incremental, on-time edits only), `late_events`, `edits_by_wiki_actor`, and the published `mart_window_5min`, `late_events`, `edits_by_wiki_actor` in `out/marts/`.
   - `DECISIONS.md` notes that the dbt-duckdb `external` materialization cannot be incremental, which is why the stream models use an in-warehouse fallback.

3. **Tests**: 9 singular dbt tests in `transform/tests/` (checks 1 to 7 plus census fallback and coverage), 4 Python test modules in `tests/`, and `tests/check_rerun.py` (runs `make build` twice and compares marts; not run by me).

## Verification

- **Build log** (`/var/tmp/revieweval/antagonistic-vs-baselines/review-01/build.log`): two dbt runs, both exit 0. The batch run reports `PASS=26 WARN=0 ERROR=0`; the stream run reports `PASS=15 WARN=0 ERROR=0`. I did not rebuild.
- **Lateness and dedup code** matches `DECISIONS.md`: the late comparison is strict (`> 600`), the high-water mark is taken before the current event updates it, and duplicates are skipped before they can update the mark or the flag.
- **Per-person macro**: I evaluated `obligations_per_person(1000000, 10000)` with DuckDB. It returns `100.0000`, which equals 1,000,000 / 10,000. The arithmetic is correct for that case.

## Caveats

- The per-person check (`test_top_ten_counties_per_person.sql`) uses the same macro as the model. It confirms the mart and the raw-lake recomputation agree, but it cannot catch an error in the macro's formula. The independent check is the Python `Decimal` comparison that `DECISIONS.md` mentions; I did not run it.
- The 1-hour stream run and the rerun check were not repeated. The data counts (21,502 unique events, 12,876 edits) come from `DECISIONS.md`, not from my own run.
- The spec (A-, G-, N- items) was not available, so requirement coverage is not verified.
