RUN_BY_COMMAND: plan-review

# Plan review: gh-1-pipeline

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)

Ticket: gh-1. Source: `.context/issues/gh-1.md`.
Plan: `.context/plans/gh-1-pipeline.plan.md`.
Review cycle: 2. This review checks the delta from Update 1.

Verdict: READY WITH CHANGES

Three must-fix items block E1. Each one is a ticket requirement with no phase that meets it.
Fix them in `/plan-update`. The tests and notes below do not block.

## Cycle 1 status

- MF-1 (model contract on `mart_edit_window_5min`): applied in full. Phase 6 step 7.
- MF-2 (incremental window mart, full refresh check): applied in full. Phase 6 step 7 and Phase 6 TDD.
- MF-3 (award-level net negative count): applied in full. Phase 3 step 10 and Phase 4 step 8. The publish and contract gaps for this model are in MF-5 and MF-6.
- MF-4 (top ten counties per person): applied in full. Phase 4 step 7. The publish gap for this view is in MF-5.

## Must-fix items

### MF-5 [requirement without a phase]

Ticket sentence: "The marts are materialized as Parquet under `out/marts/` (one folder per mart). Anything downstream reads only `out/marts/`."

Phase 3 step 10 builds `mart_fy2024_award_net` as a dbt table in the DuckDB warehouse. Phase 4 step 7 builds `view_fy2024_county_per_person_top10` as a dbt view. Check 5 reads `fct_edit`. Check 7 reads `late_events`. No phase writes any of these to `out/marts/`.

Fix: add a step that writes each object that answers a check to `out/marts/` as Parquet, with the `external` materialization. Make `late_events` a table, as the ticket names it. Record the change in `DECISIONS.md`.

### MF-6 [requirement without a phase]

Ticket sentence: "Each mart has a dbt model contract (column names and types enforced)."

Phase 3 step 10 defines `mart_fy2024_award_net` with no model contract.

Fix: add the contract to Phase 3 step 10. List `award_key`, `net_obligations` and `is_net_negative` with their types.

### MF-7 [requirement without a phase]

Ticket sentence: "Test the keys of each model with dbt tests."

Phase 4 step 1 (`mart_fy2024_monthly_county_agency`) and Phase 6 step 7 (`mart_edit_window_5min`) have no key tests.

Fix: add a key test to each mart. The grain key of the monthly mart is `month_start`, `county_fips` and `awarding_agency_code`. The grain key of the window mart is `window_start`, `wiki`, `namespace` and `actor_type`. Use a singular dbt test for each composite key. Do not add `dbt_utils`, because the plan adds no dependency.

## Tests to write

- Phase 3, input: two transactions with the same transaction key, one in a Contracts zip and one in an Assistance zip. Expected: `stg_usaspending_transactions` keeps the rows that the Phase 1 duplicate rule keeps, and the FY2024 sum equals the oracle sum with that same rule.
- Phase 5, input: the fake SSE server stops after three events. The consumer stops during a micro-batch flush, before the checkpoint write. Restart the consumer. Expected: the unique count equals the replay total, and the `meta.id` values are unique.
- Phase 6, input: one event with `length.new` absent and `length.old` 500. Expected: the event counts in `edit_count`, `bytes_added` is NULL, and `net_bytes_added` does not include the event.
- Phase 6, input: one event with `window_start` 600 and `watermark_before` 1500. Expected: `is_late` is false. The same event with `watermark_before` 1501. Expected: `is_late` is true.
- Phase 6, input: events with `dbname` `enwiki` and server `en.wikipedia.org`. Expected: check 6 selects the `enwiki` rows. The window mart has no `server_name` column, so a filter on `en.wikipedia.org` returns no rows.

## Notes (not blocking)

- Phase 6 step 1 gives two rules for a missing length. The first sentence says to treat it as zero. The "Superseded" sentence says NULL. Delete the first sentence. The Phase 6 test above sets the result.
- The Phase 6 "Tests from review" boundary line still says the window starts at 0. The clarification below it says 600. The test line above uses 600. Delete the stale line.
- Phase 3 step 1 says to keep one row for each transaction key. The Phase 3 test says to keep the rows that the Phase 1 rule keeps. Phase 1 step 2 counts duplicate keys, but no step names the transaction key column or the duplicate rule. Add both to Phase 1 and record them in `DECISIONS.md`.
- Phase 5 step 3 writes `arrival_seq` into the lake. The ticket says the lake adds only load metadata. Record in `DECISIONS.md` that `arrival_seq` is ingest metadata.
- Phase 5 step 4 still says the events and the checkpoint commit together. The Phase 5 test decides the design. Do not add more text on this point.
- Reuse and extension: checked again. The plan writes no helper that exists. This repo has no `tests/conftest.py`, `scripts/` or `shared/` module to reuse.
- `core:dry-extension`: the plan adds no gate shape. The oracle repeats the population and lateness rules on purpose, to stay independent of the marts. This is not a DRY finding.
- `core:standalone-package`: Phase 7 step 6 runs `ste-lint.py` from `$CADENCE_HOME`. The file exists. No host path is read.
- The replay was not probed again in this run. Cycle 1 recorded HTTP 200.

## Checks run

- Cycle 1 must-fix items: four checked. All four are applied in full.
- Ticket sentences: checked against the Architecture, Outputs, Rules, Checks and Amendment A sections. Three sentences have no phase that meets them for every model (MF-5, MF-6, MF-7). The rest have a phase.
- Phase order: each exit gate uses only outputs of an earlier phase.
- Helpers: the plan writes no helper that exists.
- The plan file was not edited.
