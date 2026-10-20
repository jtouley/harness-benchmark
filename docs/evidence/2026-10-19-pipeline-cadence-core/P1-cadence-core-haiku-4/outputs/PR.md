Build the federal spend and Wikipedia edit pipeline (gh-1)

## Summary

This change adds a pipeline with two questions:

- **Question A (batch):** FY2024 federal contract and grant obligations by state, county, agency and month, with obligations per resident (July 1, 2024 estimate).
- **Question B (stream):** Wikipedia edits per wiki, namespace and 5-minute window, split human and bot, with net bytes added. Arrival order sets lateness.

Layers: a Parquet lake (`lake/`, written by dlt), dbt-duckdb models (`transform/`, with contracts and tests), and Parquet marts under `out/marts/`. `make build` runs the batch. `make stream DURATION=<seconds>` runs the consumer.

## Evidence for each success signal

1. **`make build` runs from raw files and exits 0.** Yes, from a clean state, with and without stream data. dbt: 67 tests PASS.
2. **A second `make build` gives the same rows.** Yes. The sorted-row hashes of all six check objects match across two builds.
3. **`make stream DURATION=<seconds>` consumes the replay.** Yes. `make stream DURATION=60` exits 0 and lands 15,839 events.
4. **A stop and a restart keep the unique count.** Yes. A second 60-second run after a stop left the count at 15,839 unique `meta.id`. A scratch test killed a consumer during a flush after a partial write. The restart counted each event once.
5. **`dbt build` passes, including key tests.** Yes. 67 PASS.
6. **`oracle_map.yml` maps checks 1 to 7.** Yes.
7. **`DECISIONS.md` records each open choice.** Yes. D1 to D32.
8. **Checks 1 to 7 match an independent oracle.** Checks 1 to 4 and 7 match `pipeline/oracle.py`. Check 5 matches the edit count. Check 6 is a window query and has no oracle value.

## Decisions (short list, full text in DECISIONS.md)

- An edit is any `recentchange` event. The `type` field stays for filtering.
- Money uses place of performance, not recipient location.
- Eight Connecticut counties have no 2024 estimate. They use the 2021 estimate, and `population_year` records it.
- Stream models are DuckDB tables with a Parquet copy. The `external` writer adds a NULL row to an empty result.
- The window mart is incremental from a checkpoint table. Incremental and full builds give the same hashes.
- The consumer resumes the replay after each drop. Each event key is `meta.id`.

## Open risk

- The replay cuts each connection at event 15,839. Resumes do not pass that point. The lake holds the 15,839 reachable events. Raise this with the replay owner before a grade run.

## Test plan

- `uv run python -m unittest discover -s pipeline/tests -t .`: 13 tests, OK.
- `make build` twice, then compare `uv run python -m pipeline.check_marts`.
- `make stream DURATION=60`, then `make build`.

Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
