# Plan review: gh-1-pipeline_cd-1

RUN_BY_COMMAND: plan-review

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Session ticket: cd-1 (local ticket: `.context/issues/cd-1.md`, task id gh-1)

Plan: `.context/plans/gh-1-pipeline_cd-1.plan.md`
Spec: `.context/issues/cd-1.md`
Review cycle: 5 of 5. This is the last review in the loop. Plan-update cycle 4 applied MF-15 and MF-16.

Verdict: READY WITH CHANGES

## Cycle 4 items: status

- **MF-15 (Phase 2 comparison, dlt metadata).** Applied. The row hash covers source columns only. No `_dlt_*` column or table is read.
- **MF-16 (halt path outputs).** Applied. E1 writes `outputs/PR.md`, runs `ste-lint.py` on it, and creates `DECISIONS.md` on the halt path.
- **N-18 to N-28.** Applied or closed. Checked against the amended phases. No open item from them.

## Must-fix items

**MF-17. The spec requires a dbt model contract on each mart. The plan enforces it on one mart. (Spec gap.)**
The spec, Architecture section, says: "Each mart has a dbt model contract (column names and types enforced)." The marts are `mart_obligations_monthly` and `mart_edit_windows_5min`. Phase 6 step 3 enforces the contract only for `mart_obligations_monthly`. Phase 7 names no contract for `mart_edit_windows_5min`. The acceptance line "The mart contract is enforced" is also written for one mart.
Fix: the plan must state the following.
- `mart_edit_windows_5min` has a dbt model contract in its YAML. The contract names each column and type in the Phase 7 step 3 column list.
- The Phase 7 exit criteria include the contract check.
- The acceptance line covers both marts.

**MF-18. The `window_watermark` write path is not named. The incremental window mart can miss events. (Spec gap.)**
Phase 7 (N-23) stores the watermark in `window_watermark`, a one-row table under `transform/models/`, tagged `stream`. The plan does not say how the value is written. A dbt model with table materialization is rebuilt from its SQL on each run. It cannot keep the value from the last run unless the plan names a write path. A watermark computed from the fact (for example, `max(arrival_seq)` over `fct_recentchange_edits`) equals the newest arrival on every run. The rebuild set would then be empty, and new events would not reach the window mart.
Fix: the plan must name the write path for the watermark. Two options are acceptable: an incremental model that appends the value, or a `post_hook` on the window mart that writes the value it read. The plan must also name the watermark value after a full refresh. Phase 7 exit criteria must include a test that runs two incremental batches, and the window mart matches a full refresh over the same arrivals. The current Phase 7 test covers this only as a general statement.

**MF-19. The plan changes the publish mechanism that the spec requires, and does not record the change. (Spec gap.)**
Spec Amendment A says: "materialize the marts as Parquet with dbt-duckdb's `external` materialization." Phase 8 uses `external` for the batch models. Phase 7 (N-20 and MF-7) publishes `fct_recentchange_edits` and `mart_edit_windows_5min` with an incremental model and a `post_hook` `COPY`. The plan names no reason for the departure. It does not list it under `DECISIONS.md` additions.
Fix: the plan must do one of the following.
- Keep the `external` materialization for both stream marts, and name the incremental strategy that works with it. Phase 7 must prove it with the incremental-equals-full-refresh test.
- Or keep the `post_hook` path and add a `DECISIONS.md` entry. The entry names the spec requirement, the reason the external materialization does not fit the incremental models, and the test that shows the outputs match.
The `DECISIONS.md` additions list (end of cycle 2 update) must include this entry.

## Notes (not blocking)

- **N-29. State population fallback.** D3 applies the 2021 fallback to the state rows too. Phase 4 step 3 (`stg_census_state`) carries only `POPESTIMATE2024`. Add `population_2021` to that model, so `dim_state` (Phase 5) has the fallback input.
- **N-30. Integration test import path.** The quality gate `uv run python -m unittest discover -s pipeline -p "integration_stream_test.py"` runs with `-s pipeline`. The test file imports `pipeline.landing` and `pipeline.replay_relay`. The plan does not say whether `pipeline/` is a package (`__init__.py`) or how the import path is set. E1 can choose. The plan should name one.
- **N-31. Check 5 hour source.** The Phase 9 update (MF-5) sets the replayed hour from "the minimum `event_time` in the lake". The check reads `fct_recentchange_edits`. Name the source of the minimum: the fact, or `lake/recentchange`. Both give the same value only when the fact is current.
- **N-32. Halt path against "work to the end".** The spec says "Nobody answers questions: work to the end." The MF-14 halt stops at Phase 3 when the replay does not honour `Last-Event-ID`. The spec also says the consumer resumes where it stopped, and `meta.id` dedupe (Phase 3 step 5) already prevents a double count. The plan does not say why reconnect with `meta.id` dedupe is not enough to resume. Record that reasoning in `DECISIONS.md` on the halt path, or keep the halt. This does not block.
- **N-33. Edit fact scope.** D4 puts every change event (`edit`, `new`, `categorize`, `log`) in `fct_recentchange_edits`. The spec calls this table "a fact table of edits". D4 is a sound choice. Name it in `DECISIONS.md` as a spec reading, so the analyst sees it.

## Checked and found sound

- The plan has a `## Reuse and extension` section. It names `pipeline/landing.py`, `pipeline/replay_relay.py`, the dbt-duckdb `external` materialization and dbt's built-in tests.
- No shared helper exists in this repo. `tests/`, `scripts/`, `shared/` and `pipeline/` do not exist. `transform/` holds only the skeleton (`dbt_project.yml`, `models/`, `profiles.yml`). The plan writes no helper that already exists.
- The pins match `pyproject.toml`: dlt 1.31.0, dbt-core 1.11.6, dbt-duckdb 1.11.0 and duckdb 1.5.6. `.python-version` is 3.12. The plan does not change either file.
- The plan has no host path. Its gate and peer references use `$CADENCE_HOME`. `ste-lint.py` exists at `$CADENCE_HOME/skills/asd-ste100/scripts/ste-lint.py`.
- The input files exist: `data/raw/usaspending/`, `data/raw/census/` and `data/raw/sitematrix.json`.
- `.cadence.json` lists `pipeline/`, `transform/` and `Makefile` as gated prefixes. The TDD gate applies to each implementation phase.
- D7 matches the spec. Late means `prior_max > window_start + 900`. The spec's "more than 10 minutes after the end of its window" gives `window_start + 300 + 600`.
- Check 1 to check 7 match the spec. Check 3 and check 6 match after MF-12 and MF-13. Check 5 includes late events, as the spec requires.
- Phase order matches `stages.json`: planning, then E1 (implement), then E4 (draft PR). No stage is missing.

## Open decisions (review result)

1. **D1, recipient-county fallback.** Accepted in cycle 2. No change.
2. **D6, late events in the fact.** Accepted in cycle 2. No change.
3. **D2, award identity.** The pair (`awarding_agency_code`, `award_key`) is accepted in cycle 3. The fallback order stays deferred to the Phase 4 check.

## Verdict basis

Three must-fix items block E1: MF-17, MF-18 and MF-19.
- MF-17: the spec requires a contract on each mart. The plan enforces one.
- MF-18: the watermark write path is missing. The incremental window mart can miss events.
- MF-19: the plan departs from the spec's `external` materialization without a recorded reason.

Each fix changes one rule in the phase named. The plan keeps its structure.
This is review 5 of 5. The loop ends after this review. The `/plan-update` that follows maps MF-17 to MF-19 to phases under `## Carried review findings`, as the cycle limit requires.
