RUN_BY_COMMAND: plan-review
Ticket: cd-1
Spec: gh-1
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Plan: .context/plans/cd-1-gh-1-pipeline.plan.md
Verdict: READY TO EXECUTE
Last reviewed plan sha256: 0a523071571a9afb24f55163028a8cafdd1776d4ce2dbb7df93abad50f13f3e2

# Plan review: cd-1 gh-1 open-data pipeline (cycle 4, delta review)

## Status of earlier items

| Id | Status | Evidence |
|---|---|---|
| MF-6 | closed | Closed in the cycle 3 review. Revision ledger (review aea71577045f) row MF-6 and the Phase 9 amendment (MF-6) are unchanged in the cycle 3 update. |
| MF-7 | closed | Closed in the cycle 3 review. Revision ledger (review aea71577045f) row MF-7 and the Phase 7, 9 and 10 amendments (MF-7) are unchanged in the cycle 3 update. |
| MF-8 | closed | Revision ledger (review 6135ad33f49e) row MF-8. Phase 10 amendment (MF-8) moves the blocked-path check inside the repo. The test `tests/checks/test_blocked_path.py::test_blocked_path_status` is a named Phase 10 exit line and a TDD addition (written before the acceptance run). It reads `out/run_status.json`, which the acceptance run writes. `out/` is in `.gitignore`. The test asserts `blocked` for Checks 5, 6, 7 and A2, A3, asserts `stream_tables` is `skipped`, and queries `information_schema.tables` in `out/warehouse.duckdb` for `stream_edit_fact`, `mart_wiki_window_5min` and `late_events`. No check reads `outputs/`. |

## Checks run

- Plan sha256 `0a523071571a9afb24f55163028a8cafdd1776d4ce2dbb7df93abad50f13f3e2` matches the packet `Input:` line.
- Previous review sha256 `6135ad33f49ed22e1aaf0b544c74295b83140cc9e2c7ab07bd05fb6b24b8aaa9` matches the packet `Input:` line. It was read first. Its only open item was MF-8.
- Newest update section (cycle 3, MF-8) read in full. It adds one Phase 10 test and a status file. No new must-fix item cites it.
- Proposals `cd-1-*.md`: all nine decision records exist in `.context/proposals/`.
- Shared modules (`tests/`, `scripts/`, `shared/`) and the `engine/` and `pipelines/` packages do not exist in this repo. No helper in the plan duplicates an existing one.
- `## Reuse and extension` section is present and unchanged by the cycle 3 update.
- `stages.json` is not in the repo. The phase list was not compared against it.

## Must-fix items

None.

## Notes (not blocking)

- Carried from cycle 3, not applied. These sentences were in the plan when the earlier reviews passed them, so they are notes:
  - Phase 2 exit "A crash mid-write leaves the previous table readable" does not match the MF-1 amendment. The table path is empty between steps 1 and 2. E1 should read the MF-1 amendment as the rule.
  - Phase 5 exit "The first 5 events of the replay are saved as a fixture" does not match the conditional capture in the MF-5 amendment. E1 should read the MF-5 amendment as the rule.
  - The Phase 9 column list does not include `last_arrival_seq`, but `contract: enforced: true` (A5) needs every column in the schema. Add it to the mart's column list when the Phase 9 models are written.
  - The Phase 9 incremental model needs an `is_incremental()` guard, or a full build on the first run, so that `{{ this }}` is not read before the table exists.
  - Phase 5 start check: record its result (replay reachable or not, fixture present or not) in `DECISIONS.md`, so that Phase 10 knows which blocked-path status applies.
  - Phase 6 and Phase 9 window-mart tests can run on synthetic fixtures without the replay. The blocking is a choice, not a requirement.
- Volume and growth: `mart_wiki_window_5min` recomputes keys from all on-time rows of `stream_edit_fact`, and the Phase 5 seen-set rebuild scans every committed batch file on start. Both costs grow with the stream. The plan states no expected volume.
- `duplicates_dropped` is a running total. After a restart it can differ from an uninterrupted run, because duplicates in an uncommitted batch are counted again. A2 compares totals, not this counter.
- Test and phase names in the revision ledgers are names, not must-fix items.
