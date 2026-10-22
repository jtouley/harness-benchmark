RUN_BY_SKILL: de-adversarial-reviewer
Mode: plan-gate
Pipeline-Run: 0f84b2cc-3cf4-4553-b890-6f79e87e0cd2

Ticket: cd-1
Input: .context/plans/cd-1-pipeline.plan.md (sha256 d19f6f11705f3866baa7889bb04eac6ee8e768dae3765afe8166253e5e811b5b, matches the input hash)
Round: 1 (no file in .context/adversarial/ existed before this run)

## Verification notes

- Plan read in full (577 lines, five stacked update sections: cycles 1 to 5, each with "Replaces" overrides). The body still holds text that the update sections override; see C-1.
- Session: `pipeline_run_id` 0f84b2cc-3cf4-4553-b890-6f79e87e0cd2 from `.context/sessions/by-worktree/dd962f6cc1983ba4.json`.
- `.context/architecture-review-notice.json`: P5 skipped `core:dependency-direction` and `core:boundary-integrity` because `layer_map` is empty. This review does not rely on those two rules.
- `core:decision-coverage`: 10 proposal files read (cd-1-engine-dependencies, -fy-and-month-basis, -late-event-placement, -load-metadata, -money-scale, -negative-award-key, -place-basis, -population-fallback, -publish-format, -stage-ownership). Each has `decision_id`, `status: proposed`, `question`, `choice`, `rationale`. Not read: `cd-1-stream-commit-manifest.md`, `cd-1-stream-dedup-resume.md`, `cd-1.md`. Coverage passes for the ten read.
- Census (`data/raw/census/`), compared county keys (SUMLEV 050) across both files:
  - 2021 file: 3,143 county rows. 2024 file: 3,144 county rows.
  - In 2024 only: 09110, 09120, 09130, 09140, 09150, 09160, 09170, 09180, 09190 (the nine Connecticut planning regions).
  - In 2021 only: 09001, 09003, 09005, 09007, 09009, 09011, 09013, 09015 (the eight Connecticut counties).
  - Both files have the same 51 state codes. States 60, 66, 69, 72, 78 appear in neither file.
  - Alaska 02063 and 02066 appear in both files, so no Alaska key change.
  - Leading zeros present in the text (`01|000` in the first row). The plan's text-typed FIPS rule (MF-8) is needed.
- USAspending (`data/raw/usaspending/`, 8 zips): place county FIPS (`prime_award_transaction_place_of_performance_county_fips_code`) is either empty or 5 characters in every file read. Example: the first zip has 3,913 rows, 3,856 empty. Agency codes 417, 418, 474, 485 have no leading zero.
- Not checked: the replay server at localhost:8099 (no live check; R-1 in the plan says Last-Event-ID support is unknown). No dbt or pytest run.

## Blocking issues

### B-1. Acceptance 3 cannot be decided for a resumed run

Plan line 271 replaces Acceptance 3 with: a forced disconnect and a resume, plus an uninterrupted run, "both with the same `max_events`", produce the same `fact_edit` `meta_id` set, and both runs end with stop reason `max_events`. Line 273 sets `max_events: 2000` for the two runs.

Phase 5 (line 164) forces the drop after event 500. With `max_events` counted "in the run" (line 267), the resumed process counts 2000 new distinct ids. The landed set is then 500 + 2000 = 2500 ids, not 2000. The uninterrupted run lands 2000. The sets cannot be equal under this rule. The plan does not say whether the resumed run's budget is 2000 or 1500, or whether `max_events` counts across processes that share one lake.

Without a fixed counting rule, the test in Phase 7 (`tests/test_stream_e2e.py`) cannot be written to pass or fail for the right reason. Fix: define the budget over the whole logical run (the committed `meta_id` count in the lake), state the stop reason of the interrupted process, and name the assertion.

Rules: `core:implement` (test names and seam contracts are set by the plan; an undefined assertion breaks the red-first step).

### B-2. dbt reads uncommitted batch files, which breaks the commit invariant

Plan line 160 defines a batch file "not in the manifest" as an orphan, and says the sink deletes orphans only on start. Line 172 defines `stg_recentchange` as reading `lake/stream_recentchange/*.parquet`, a glob that also matches orphans. Phase 6 never filters by the manifest.

The MF-1 argument (plan line 246) says the derived running max matches the committed state "because orphan batch files are deleted on start". That holds only when the engine restarts before dbt runs. The `make stream` recipe (MF-6, line 364) runs dbt only after the engine exits 0, so the make path is safe. A direct `dbt build --select stream` after a crash is not covered. In that case, orphan events land in `fact_edit`. On the next engine start the same events are re-read with a new `arrival_seq`. The merge key keeps one row per `meta_id`, but `arrival_seq` and the late flag are then computed from a state that never committed, and the MF-1 "exact, no drift" claim is false for that path.

Fix: `stg_recentchange` reads only the batch files listed in `lake/_state/stream_manifest.json`. Add a test: an orphan file present in the lake does not reach `fact_edit`. This test is absent from Phase 6 and from the MF-1 test list (line 255).

Rules: `core:implement` (a red test must exist for each claimed invariant).

## Conditions

### C-1. The plan body still states superseded rules

The five update sections use "Replaces" lines, and the body keeps the old text. Examples a builder would read first:
- Phase 3 (lines 118 to 131): the `to_decimal` step, its test and its exit. MF-7 moved them to Phase 2, and MF-4 retired Phase 3's DataFusion steps. Phase 3 still exists as a heading with a bullet list.
- Phase 4 (line 144): the publish macro that renames folders. MF-6 moved the renames to the engine.
- Reuse (line 207): `datafusion.SessionContext` for SQL steps. The plan has no DataFusion step after MF-4.
- Phase 2 (line 109) and line 137: the old sitematrix and staging text.

Before any execution, write one consolidated plan or a table of every superseded line with its replacement. The loop is at cycle 5 of 5 (plan line 531), so the consolidation goes to the gate, not to another plan-review round.

### C-2. `population_2024` is not additive in `mart_obligations_monthly`

Line 139 sets the mart grain to month, state, county and agency, with `population_2024` and `obligations_per_person`. One county population repeats on every agency and month row of that county. A sum of the population column over the mart counts each county once per agency and month. Check 2 (top ten counties by obligations per person) and check 4 (county sums equal state sums) both read this mart. Fix: state in the contract that `population_2024` is not additive, and make check 2 and check 4 aggregate the obligations from the mart and take population from `int_county_population_2024` once per county.

### C-3. The Last-Event-ID fallback is not decided before Phase 5

Risk R-1 (line 229) says the replay's `Last-Event-ID` support is unknown, and that a mismatch goes to `DECISIONS.md`. A decision recorded after the fact does not give Phase 5 a path. Phase 5's exit (line 168) does not require the live check to pass. Fix: name the live check as a Phase 5 entry gate, and name the fallback (dedup-only resume with a replay from the start, or a stop) before Phase 5 starts.

### C-4. The replay must supply at least 2000 distinct events

Line 273 runs both stream tests with `max_events: 2000` and a 600 s cap. If the replay has fewer than 2000 distinct events in the window, the stop reason is `replay_end` and the test fails for a reason outside the code. Fix: state the replay's event rate or count, and record it in `DECISIONS.md` before Phase 7.

## Adversarial scenarios

1. Connecticut counted twice (2024 planning regions plus 2021 counties). Handled? Yes (MF-9, MF-10). Evidence: the census key diff above. The nine planning regions are dropped from the county grain and map to the state's `UNKNOWN` county, so the eight 2021 counties carry the state total with no double count.
2. Alaska key change (Valdez-Cordova split). Handled? Not needed for this data. Evidence: 02063 and 02066 appear in both census files, and 2021-only keys are the Connecticut eight only.
3. Territory places with no population rows (states 60, 66, 69, 72, 78). Handled? Yes (MF-11). Evidence: none of the five states appears in either census file, and the rule maps them to `UNKNOWN` with NULL population.
4. USAspending place county code in the wrong shape (2-digit or 3-digit). Handled? Yes (MF-10). Evidence: non-empty county codes in all eight zips are 5 characters; empty codes map to `UNKNOWN`.
5. Crash between batch rename and manifest commit, then a direct dbt run. Handled? No. See B-2. Evidence: plan lines 160, 172.
6. Restart with a forced drop, then a resume, compared to an uninterrupted run. Handled? No. See B-1. Evidence: plan lines 267, 271, 273.
7. Publish crash in any of the swap states (P1, P2, P3, S1 to S3). Handled? Yes (MF-6, `tests/test_publish_states.py`). Evidence: plan lines 351 to 372 cover each state with an action and a test.
8. Replay does not support Last-Event-ID. Handled? Partly. See C-3. Evidence: plan line 229.
9. Population summed across agency rows. Handled? No. See C-2. Evidence: plan line 139.
10. Replay too short for `max_events: 2000`. Handled? No. See C-4. Evidence: plan line 273.
11. Hive partition values with leading zeros (dbt-duckdb `read_parquet(... hive_partitioning=true)`). Handled? Not triggered. Evidence: agency partition values 417, 418, 474, 485 have no leading zero. The plan does not test this path if a future agency code starts with 0.

## Trade-offs

- Keeping the publish and dedup rules in the engine keeps the position and the lake consistent (MF-1, MF-6). The cost is that dbt must read the manifest (B-2), which couples the two stages more tightly.
- Dropping the Connecticut planning regions from the county grain and mapping them to `UNKNOWN` keeps totals exact, but makes Connecticut county rankings incomplete. Analysts reading check 2 should be told this in `DECISIONS.md` (the rule is in MF-10).
- Using the 2021 vintage for fallback counties (MF-9, Amendment A) is the only data the request allows. The fallback counts are 8 Connecticut counties, and the mart column `population_2024` then holds a 2021 figure for them (N-4 in cycle 4).

Verdict: REQUEST CHANGES
