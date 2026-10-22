# gh-1: federal spend and Wikipedia edit pipeline (draft, stopped before implementation)

**Draft, not ready.** This PR text describes a cadence run that stopped at the plan stage (P7, retries hard stop). No code has been written and no commits exist on `feature/gh-1-pipeline`.

## What is blocked

- The plan's USAspending column names do not match the raw zips in `data/raw/usaspending/`:
  - Contracts CSVs have no `generated_unique_award_id`.
  - Assistance CSVs have no `primary_place_of_performance_state_code`.
- The P7 test-benchmark audit failed three times on the test plan (score floor 7). The retries are used up.

## Next steps

1. Re-plan with the column names read from the zips.
2. Fix the test plan items that the P7 score file names (`.context/benchmarks/`).
3. Rerun the cadence pipeline from P1 on a fresh run.

## Scope when it lands

Batch (Question A) and stream (Question B) as described in issue gh-1: the Python engine driven by `pipelines/*.yml`, the lake under `lake/`, the dbt project under `transform/`, the marts under `out/marts/`, `oracle_map.yml`, and `DECISIONS.md`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
