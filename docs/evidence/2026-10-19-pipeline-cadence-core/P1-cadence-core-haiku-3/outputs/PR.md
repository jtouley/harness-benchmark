# gh-1: build the federal awards and Wikipedia edit pipeline

Draft PR. Branch `feature/gh-1-pipeline`. Base `main`. Task gh-1.

## What this change does

It adds a pipeline that answers two questions for analysts.

- Question A (batch). Federal FY2024 award money, in total and per resident, by state, county, agency and month.
- Question B (stream). Wikipedia edits per wiki, namespace and 5-minute window, split by human and bot, with net bytes.

The pipeline has three parts.

- The lake. `pipeline/batch.py` lands the three batch sources with dlt. `pipeline/stream_consumer.py` lands the edit stream in micro-batches. Both write Parquet under `lake/open_data/<table>/`.
- The models. dbt-duckdb builds the staging models, the star schema, the monthly mart, the stream models, and the check views in `transform/`.
- The publish step. The published marts are Parquet under `out/marts/`.

## How to run

- `make build` runs the batch part from the raw files. Two runs give the same mart hash.
- `make stream DURATION=<seconds>` consumes the stream for that time, then builds the stream models. A killed consumer resumes from its last committed event.

## Stages and results

- Phase 1, batch lake: 9,820 USAspending rows, 6,287 census county rows, 1,073 wiki sites.
- Phase 2 to 4, batch models: 56 dbt tests pass in `make build`. The mart has 2,672 rows. The mart hash is the same in two clean builds.
- Phase 5 to 7, stream: the consumer passes 16 unit tests, including odd event shapes. A clean run of `make stream DURATION=60` consumed 14,571 arrivals. A killed and restarted run reached 15,399 arrivals. Neither run has a duplicate `meta_id` or a gap in `arrival_seq`.
- Phase 9, restart check: the three asserts of the restart check pass over the common prefix (m = 14,571).

## Checks (analyst questions)

1. FY2024 net obligations per agency. The four agencies sum to $1,442,017,216.67, the source total. View: `chk_fy2024_obligations_by_agency`.
2. The ten counties with the highest FY2024 obligations per person. View: `chk_top10_counties_per_person`.
3. Awards with a net negative obligation in FY2024: 1,122. View: `chk_negative_award_count`.
4. For June 2024, the 52 state rows match the county totals, and the states sum to the source total. View: `chk_month_reconciliation`.
5. Stream edits and net bytes per wiki, human and bot, late events included. View: `chk_stream_edits_by_wiki`.
6. Top 5-minute windows on en.wikipedia.org, on-time edits only. View: `chk_top_windows_enwiki`.
7. Late events: 0. View: `chk_late_event_count`.

Check 7 is 0 because the replayed hour never moves the watermark more than 10 minutes past a window end. A second scan in arrival order gives the same result. The late rule has a fixture test that finds one late event.

## Decisions

`DECISIONS.md` lists each choice. Some choices differ from the plan's first draft.

- Connecticut counties from the 2021 census file use their 2021 population (Amendment A). They carry `population_source_year = 2021`.
- The state per-person value uses 2024 counties only, so Connecticut's people are counted once.
- The stream checkpoint is a DuckDB file, not JSON. The checkpoint and the set of recorded ids change in one transaction.
- The resume rule drops an event whose id is already recorded. The ids are JSON arrays with no order, so "at or before" does not apply.
- A malformed event is skipped and recorded. A good copy of the same id is still accepted.

## Review

- R1 (local review, five rounds): round 1 found three must-fix items. Round 2 found two. Round 3 found three, round 4 found one. Round 5 found no must-fix item. Each must-fix item is fixed, with a test. Open non-blocking nits are listed in the summary.

## Known limits

- The replay sent one truncated event on an early resume. The acceptance run did not show it again. The consumer records any such event in the `skipped` table, and `skipped_malformed` shows the count that no good copy replaced.
- The consumer checks its deadline on each line. A run with `--duration` ends within the socket timeout of its deadline (10 seconds).
- `lake/`, `out/`, and `transform/target/` are generated and not committed.

## Tests

- `uv run --python 3.12 python -m unittest discover -s pipeline/tests -p "test_*.py"`: 30 tests pass.
- `uv run dbt build --project-dir transform --profiles-dir transform`: 84 of 84 pass.
- `uv run dbt parse --project-dir transform --profiles-dir transform`: passes.

🤖 Generated with [Claude Code](https://claude.com/code)
