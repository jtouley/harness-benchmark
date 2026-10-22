# PR title

Open data pipeline: batch sources, SSE consumer, dbt star schema and marts (gh-1)

# PR body

## Status

Draft, not opened. No GitHub host is configured (origin is a local bare repo) and `gh` auth is invalid, so this text is the PR. Branch `feature/gh-1-pipeline` is pushed at `66143c6`.

## Summary

- Batch sources (sitematrix, Census 2024 county population, USAspending FY2024 prime awards, agencies 417, 418, 474, 485) land as Parquet under `lake/raw/`. `make build` runs them, then `dbt build`.
- `make stream DURATION=<s>` consumes the Wikimedia recentchange SSE stream. It resumes from a persisted cursor and dedupes on `meta.id`. Late events go to `late_events`, not to windows.
- dbt-duckdb staging and star schema, with model contracts and key tests. Four marts are published to `out/marts/`.
- `oracle_map.yml` and `python -m pipeline.oracle run` check conservation and reconciliation.

## Verified

- `make build`: exit 0, PASS=74 ERROR=0.
- Second `make build`: row content of all four marts identical (per-file fingerprint). Raw Parquet bytes and the dlt state files change between runs; the marts do not.
- `make stream DURATION=60`: exit 0.
- Unit tests: 46 tests, OK.
- Oracle: 6 checks PASS (raw row conservation, obligation total exact, state equals county, per-person recompute, stream no duplicate ids, window conservation).

## Known gaps

- `oracle_map.yml` maps internal checks, not the seven analyst questions one-to-one. The mapping for analyst questions 1 to 7 needs to be completed.
- About 79% of award rows have no county. Their obligations sit in state-unallocated rows, so county-level per-person rankings (analyst check 2) cover only the rows that report a county.
- Question A covers four agencies only.

## Decisions

See `DECISIONS.md`, including the replay-server behaviour (replays from `Last-Event-ID`) and the population vintage (July 1, 2024).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
