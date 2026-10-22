# PR: gh-1 pipeline: federal awards (FY2024) and Wikipedia edit stream

Status: DRAFT (no GitHub in this environment; text recorded here instead of opening a PR)
Branch: feature/gh-1-pipeline (base: main)
Head: edc56ea
Run: c11abad2-208f-4d85-bb55-2a95c021b556 (task cd-1)

## Summary

Adds the two-question pipeline: a config-driven Python engine (pyarrow, Polars, DataFusion) that
lands raw sources into a Parquet lake, a dbt project (dbt-duckdb) that builds staging, the star
schema and marts, and published marts under out/marts/.

- Question A (batch): FY2024 federal award obligations by agency, state, county and month, with
  population (July 1, 2024 estimate, latest earlier estimate where missing) and obligations per person.
- Question B (stream): Wikimedia recentchange edits, consumed as micro-batches. Edit fact at the grain
  of one change event; 5-minute window mart by wiki, namespace and actor type (human/bot).
  Late events (stream-time rule, >10 min past window end at first arrival) go to late_events.

## Commits

- phase 0: dependencies and package skeleton
- phase 1: pipeline YAML loading and schema validation
- phase 2: engine core and parquet lake sink
- phase 3: file sources and clean source tables
- phase 4: polars and datafusion transforms
- phase 5: stream source and micro-batch stream sink
- phase 6: event identity, edit rule and late events
- phase 7: pipeline YAML files and make targets
- phase 8: dbt batch models: staging, star schema, Question A mart
- phase 9: dbt stream models: edit fact and 5-minute window mart
- phase 10: oracle map, decisions file, checks, and acceptance run
- refactor: meet the R3 limits for the cadence run

## Review

Local review (R1 through R7) runs on this branch; results are recorded in the session summary.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
