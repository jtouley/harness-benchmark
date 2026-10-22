# PR not opened: gh-1 run stopped at P7 (retries)

No draft PR was opened. The cadence run stopped at a hard stop before E1 (implementation), so there
is no code to put in a PR. The text below is the draft PR that would be opened once the run passes
P7 and P9. Do not open it as-is; it describes work that does not exist yet.

## Title

gh-1: federal awards and Wikipedia edit pipeline (batch + stream) with YAML-configured engine

## Body

Closes gh-1 (not yet implemented).

### Planned scope

- `pipelines/*.yml`: declarative sources (file, HTTP SSE), transforms (Polars, DataFusion), sinks (Parquet lake under `lake/`).
- Python 3.12 engine that validates each YAML file against a schema and reports file, line and problem on error.
- Stream sink writes micro-batches and commits the consumer position in the same step as the data.
- dbt project in `transform/` (dbt-duckdb reading the lake): staging, star schema, marts with contracts.
- Published marts under `out/marts/`.
- `make build` (batch, idempotent) and `make stream DURATION=<seconds>`.
- `oracle_map.yml` for the seven analyst checks, and `DECISIONS.md`.

### Status

- Cadence run stopped at P7 (test-benchmark plan): FAIL on three runs, retries exhausted.
- Plan: `.context/plans/cd-1-pipeline.plan.md` (READY WITH CHANGES, never READY TO EXECUTE).
- A5 vibe-test: NOT READY FOR PLANNING.
- No implementation, no tests, no checks run.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
