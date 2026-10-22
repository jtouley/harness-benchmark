RUN_BY_COMMAND: plan-review

Ticket: cd-1
Input: .context/plans/cd-1-gh-1-pipeline.plan.md (sha256 b01ace9a150c74af6aca13adb55096a1713a933e52c8994963f8bdc00df45d47)
Input: .context/reviews/plan_cd-1-gh-1-pipeline.md (sha256 751fc55a25abda9993ec5d2076b39a29a13f03f2837e51f1e3548594c3b6d5d6, previous review)

Verdict: READY TO EXECUTE

Last reviewed plan sha256: b01ace9a150c74af6aca13adb55096a1713a933e52c8994963f8bdc00df45d47

## Status of earlier items

| Id | Status | Evidence |
|---|---|---|
| MF-1 | closed | Revision ledger (review b0f4e3dbf2a2) row MF-1. Mode R or N is set by the Phase 3 probe. Mode N fails S2 and acceptance. |
| MF-2 | closed | Revision ledger (review b0f4e3dbf2a2) row MF-2. Store of record, append write, uniqueness and commit order are named. |
| MF-3 | closed | Revision ledger (review b0f4e3dbf2a2) row MF-3. `LATE_AFTER` and `is_late()` are defined once in `pipeline/stream.py`. |
| MF-4 | closed | Revision ledger (review b0f4e3dbf2a2) row MF-4. `source_file`, `source_row` and `award_row_key` are added in Phase 2 and keyed in Phase 4. |
| MF-5 | closed | Revision ledger (review ef75c715e884) row MF-5. `max_event_time_seen` is `max(meta.dt)` over `lake/raw/stream_events`. |
| MF-6 | closed | Revision ledger (review 62d0005f60b7) row MF-6. The consumer writes one store. `late_events` is a dbt model over the stored `is_late = true` rows. |
| MF-7 | closed | Plan update MF-7 section (plan lines 397-405) and Revision ledger (review 751fc55a25ab) row MF-7. Check 6 has one run point: `make stream`, then `make build`, then check 6. No `make stream` runs after the build. |

## Must-fix items

None.

## Notes (not blocking)

- N-1. Carried. The Phase 3 bullets that name `max_event_time_seen` in the state file and the `meta.dt` cursor are superseded by MF-5 (plan lines 334-336). They are still in place. Mark them superseded in place so E1 does not read two rules.
- N-2. Carried. MF-4 text (plan line 312) still says "The row counts compared from Phase 1 to Phase 6". Phase 1 records no counts. Read it as Phase 2 to Phase 6, or fix the text.
- N-3. Carried. Oracle check 1 (plan line 198) expects FY2024 rows to equal "the row counts recorded per zip in Phase 2". Phase 2 records two counts per member. Name the post-filter count.
- N-4. Carried, still open. `make build` (Phase 1) runs the raw load and `dbt build`. `lake/raw/stream_events/**` is written only by `make stream`. On a clean checkout, `stg_wiki__recentchange` reads an empty Parquet source, so S1 ("`make build` exits 0 on a clean checkout") is not met as written. The plan update says a decision is needed before E1 runs Phase 4. The plan does not record that decision. This is a note because the text was in the plan when the previous review passed it. It must be decided before E1 reaches Phase 4.
- N-5. Carried. Phase 6 line 208 still says "Checks 6 and 7 run as scripts under `make stream` in the verification step". MF-7 governs over that sentence, and the rule matches the convention of the MF-1 to MF-6 updates. Mark the sentence superseded in place, so that E1 reads one run point for check 6.
- N-6. Carried. The ledgers name tests that the phase test lists do not contain: `test_no_replay_records_gap`, `test_kill_between_write_and_cursor_no_duplicate`, `test_award_row_key_unique_per_member`, `test_kill_between_write_and_cursor_same_is_late`, and the `test_late_rule.py` boundary cases. Name them in the Phase 2 and Phase 3 test lists.
- N-7. Carried. The plan does not say where the mode R or N result of check 7 is recorded, where the S5 result is recorded, or how the replay is held constant across the kill-and-resume run and the uninterrupted run.
- N-8. Carried. Whether the state rollup `mart_obligations_by_state_month` (a view in Phase 5) is published to `out/marts/` is not stated. Phase 7 and the exit criteria do not say.
- N-9. Carried. The type of `meta.dt`, `window_start` and `window_end` (timestamp or string) is not named. MF-5 depends on `max(meta.dt)` being comparable.
- N-10. Carried. The plan says "Wikipedia edits", but Phase 4 does not filter the recentchange `type`. Name whether `fct_wiki_edit_5min` counts only `type = 'edit'`. Check 6 depends on it.
- N-11. Carried. MF-6 relies on one dlt `append` write per batch being all-or-nothing. State how a partial Parquet file from a kill during that write is handled at restart.
- N-12. New, wording only. Check 6 (plan line 203) compares against "distinct stored events in the replay window". MF-2 removed the "current replay window" bound. State whether check 6 counts all stored rows or only the rows of the run. MF-7 does not change this expected value.
- N-13. New, wording only. MF-7 (plan line 408) says the Phase 6 "Tests" bullet does not list check 6 under `make stream`. Line 208 still does. Fix the line, as N-5 asks.

## Checks with no finding

- Input hashes: the plan on disk matches `b01ace9a...`. The previous review file matches `751fc55a...`, the value in the packet.
- Single run point for check 6: MF-7 (steps 1 to 3) runs `make stream`, then `make build`, then check 6. The new text adds no `make stream` after the build. Check 7 stays under `make stream`.
- Late rule: `is_late` still uses `> LATE_AFTER`. The MF-7 text does not change it.
- Single writer: the plan writes `lake/raw/stream_events` only. `grep -rn "lake/raw/late_events" pipeline transform` should return nothing, and no plan text writes that path.
- Reuse and extension: the `## Reuse and extension` section is present. The repo has no `tests/`, `scripts/`, `shared/` or `pipeline/` directory, so no existing helper is written again. The plan adds no shared helper module.
- Pins: MF-7 adds no dependency and changes no pin.
- Previous must-fix ids: MF-1 to MF-7 are all closed. No id is carried. This review adds no new must-fix item.
- Cycle count: this is the fifth review in the loop. It is not a blocking verdict, so the loop ends here.

## Open decisions

None recorded in this review. N-4 needs a decision before E1 reaches Phase 4, as the plan update states.

RUN_BY_COMMAND: plan-review
