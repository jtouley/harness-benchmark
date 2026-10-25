# What the PR does (commit 736d6fe, "change under review")

It fills in the empty project skeleton with the whole pipeline from PR-description.md: 45 files, about 2,100 lines.

## In one paragraph

`make build` uses dlt to land the raw files as Parquet under `lake/`: two USAspending tables (contracts and
assistance), the Census 2024 county file, the Census 2021 county file (used as a fallback) and the Wikimedia
site matrix. dbt-duckdb then builds a star schema from the lake (`fact_award_transaction`, `dim_agency`,
`dim_place`, `dim_date`) and publishes two marts to `out/marts/`: `mart_monthly_obligations` (month x county
x agency) and `mart_award_fy2024` (one row per award, for check 3). `make stream` runs a Python SSE
consumer. It lands micro-batches in `lake/stream_raw` (every event), `lake/stream_events` (edits and new
pages, already flagged `is_late`) and `lake/stream_checkpoint` (the last SSE id and the high-water event
time). It skips any `meta.id` it has already landed, so restarts and reconnects add no duplicates. dbt then
builds the incremental `fact_edit` and `window_5min` tables and publishes `window_5min`, `late_events` and
`edits_by_wiki_actor`. `oracle_map.yml` maps checks 1 to 7 to these marts, and `DECISIONS.md` records the
choices.

## Key mechanisms

- **Exact money.** Amounts are cast to `decimal(18,2)` and summed as decimals. Per-person values come from
  integer (hugeint) arithmetic in `transform/macros/obligations_per_person.sql`, because DuckDB decimal
  division returns a DOUBLE.
- **Amendment A.** Population is `POPESTIMATE2024`. A county missing from the 2024 file falls back to
  `POPESTIMATE2021`, and `population_year = 2021` records that. In practice this covers Connecticut's six
  old county codes. Seven territory codes have no estimate in either file and keep a null population.
- **Lateness** (`pipeline/lateness.py`). An event is late if
  `high_water - (window_start + 300) > 600`, where `high_water` is the highest event time seen before the
  event. It counts every event type, is kept in memory and saved in the checkpoint, so it uses stream time
  and survives restarts. Late edits are excluded from `window_5min` and listed in `late_events`.
- **Resume.** On reconnect the consumer sends `Last-Event-ID` with the checkpoint id. It reloads the dedup
  set from `stream_raw` at startup.
- **Incremental models.** Both stream models select loads by dlt `_dlt_load_id`. `window_5min` recomputes
  every window that a newer load touched.

## What I verified (in a scratch copy; the tree was not modified)

| Check | Result |
|---|---|
| Batch build plus `dbt build` | 26/26 models and tests pass |
| PR's own test suite (`python -m unittest`, 49 tests, including rerun idempotence) | all pass |
| Checks 1 to 3 recomputed from the raw zips/CSVs with Python `Decimal` (not reading the lake) | Agency totals match to the cent (417: 164,522,022.53; 418: 166,315,027.20; 474: 279,998,069.91; 485: 831,182,097.03; total 1,442,017,216.67). Negative-net awards: 1,122 of 7,918, matches. The top-10 per-person counties match in order and value (DC 11001 is first at $129.07). |
| Stream: one continuous run vs. a run that was stopped, then killed with `kill -9` partway through, then restarted | The resumed run is an exact prefix of the continuous run: no duplicates, no gaps, identical late flags |
| Full replay (21,502 events, 12,876 edits, 3,602 s of event time) | `fact_edit` has 12,876 unique rows. My own recomputation of the late rule from arrival order finds the same 60 late events as the pipeline. |
| Incremental vs. full | After an extra append and an incremental `dbt build`, `window_5min` equals a full recompute from `fact_edit` (674 rows). Stream dbt build: 15/15 pass. |

## Things to know (not blocking unless the analysts disagree)

1. **72.7% of the dollars land in county `UNKNOWN`.** The PR uses place of performance, and its
   county FIPS is empty for 7,753 of 9,404 assistance rows. Recipient county FIPS is filled for about 99% of
   rows. So check 2 (top counties per person) ranks only about 27% of the money. The totals stay correct
   because the UNKNOWN rows are kept. This is a documented choice, but `DECISIONS.md` does not mention its
   size.
2. The stream tests (checks 5 to 7) compute their expected values with the same late rule, from the same
   lake. They catch plumbing errors but not a misreading of the spec. My independent recomputation agreed.
3. Live demo (not tested, no network allowed): the consumer sends no `User-Agent` header. The public
   Wikimedia stream may reject requests without one.
4. Minor issues: `tests/check_rerun.py` compares only `mart_monthly_obligations`, not `mart_award_fy2024`.
   Clearing `lake/stream_*` without clearing `out/warehouse.duckdb` needs `--full-refresh`, as
   `DECISIONS.md` notes. `make build` and `make stream` call `uv run`, which creates a `.venv` in the project
   on first use.

**Verdict:** the PR does what the description asks. Every number I could check independently matched,
and the stream is exactly-once across stop, kill and restart. The main open question is analytic: whether
counties should come from place of performance (as now) or from the recipient, given how sparse the
place-of-performance county is.
