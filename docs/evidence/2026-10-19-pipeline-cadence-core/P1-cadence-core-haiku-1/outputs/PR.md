# PR: gh-1 pipeline. Question A (batch) and Question B (stream)

Branch: `feature/gh-1-pipeline` (9 commits on `origin/main`). Status: draft. No GitHub in this environment, so this file holds the PR text. No PR URL exists.

## Summary

- Batch path: `make build` loads the raw files into a Parquet lake under `lake/`, runs dbt, and publishes five marts under `out/marts/`.
- Stream path: `make stream DURATION=<seconds>` consumes the Wikimedia recentchange stream into the lake, then builds the stream models and publishes two stream marts.
- Question A answers checks 1 to 4 from the marts. Question B answers checks 5 to 7 from the marts.
- `oracle_map.yml` names the answer table and query for each check. `DECISIONS.md` lists each choice the ticket left open.

## Stack

- Python 3.12. dlt 1.31.0 lands the batch files and the stream in Parquet.
- dbt-duckdb 1.11.0 builds the models. The marts use the `external` materialization.
- The pinned versions in `pyproject.toml` did not change.

## Results

- `make build` runs twice on a clean lake. The sorted content of each batch mart is the same on each run.
- Check 1: four agencies. Net obligations total 1,442,017,216.67 USD.
- Check 4: all 12 months reconcile to zero difference.
- Stream: the consumer stops and restarts without double counts. The check 5 totals of an interrupted run equal an uninterrupted run.

## Gates and tests

- Tests: 13 pytest tests. `make build` runs 81 dbt nodes (models and tests), and all pass.
- dlt gate: four tests on dlt 1.31.0. All four pass, so the stream uses dlt.
- Replay: the replay does not honor `Last-Event-ID`. The dedupe on `meta.id` covers the overlap.

## Choices for review

1. Decision 15: old Connecticut county codes use the 2021 population.
2. Decision 18: check 6 lists the top 10 windows. The ticket gives no N.
3. Decision 17: the stream mart has no time filter. Check 5 "for the replayed hour" holds only while the lake holds one replay hour.

## Test plan

- [ ] `uv run --with pytest pytest tests -q`
- [ ] `make build` twice. Compare the sorted content of `out/marts/*`.
- [ ] `make stream DURATION=60` against the replay.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
