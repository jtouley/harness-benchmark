RUN_BY_COMMAND: plan-review
Pipeline-Run: 5c0a2846-be0c-4861-b63f-0189a220b806
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Ticket token: cd-1 (task gh-1)

Verdict: READY TO EXECUTE

Last reviewed plan sha256: bc627afef4e446e7f38eafba64764162bdb823fa65820a1c655d194d7438ad31

# Plan review: gh-1 open-data pipeline (cd-1, rev2), cycle 5

Plan: `.cursor/plans/gh-1-pipeline_cd-1.plan.md` (sha256 bc627afe...). Previous review: `.context/reviews/plan_gh-1-pipeline_cd-1.md` (cycle 4, sha256 575a6b7c..., verdict READY TO EXECUTE, last reviewed plan sha256 af7ec7aa..., no open must-fix items). Vibe test: `.context/vibetest/cd-1_2026-10-22-rev2.md` (sha256 4d54f757..., verdict NOT READY FOR PLANNING, gaps G-1 to G-12 and N-1 to N-8). The newest update section is the fourth `## Plan update 2026-10-22` (plan line 507). Its ledger is `## Revision ledger (review 575a6b7c9f40)`, which has no row.

Result: no new must-fix item. The plan changed after the cycle 4 review only by the fourth update section, and that section changes no plan text ("Required changes: None", "Phase changes: None"). A new must-fix item may cite only text the newest update section added or changed, so none can be raised. The plan is ready to execute.

## Status of earlier items

| Id | Status | Evidence |
|---|---|---|
| MF-11 | closed | Third update MF-11 (plan lines 456-465) adds `bucket_rule` (1 to 5) to `stg_usaspending__transactions`, keeps the bucket keys and gives the three checks of `test_place_buckets_exhaustive`. Ledger row MF-11 (review df05e6b4a027). |
| MF-12 | closed | Third update MF-12 (plan lines 467-475) keys `chk_03` by prefix (four prefix rows and `TOTAL`). Test `test_chk03_prefix_counts_sum_to_total`. Ledger row MF-12. |
| MF-13 | closed | Third update MF-13 (plan lines 477-483) makes Amendment A a state-level rule. Test `test_census_no_mixed_geographies` (Phase 3). Ledger row MF-13. |

## Evidence checked

- Plan body: the Phase 1 to 7 text, section 3 (G-1 to G-12 and N-1 to N-8), the Reuse section, the MF-1 to MF-10 updates and the third and fourth updates were read in full. The fourth update adds no requirement.
- Vibe test coverage: each G-n has a section 3 row naming a settling phase (Phases 2 to 7). Each N-n has a choice in section 3 or in Phases 2, 3 or 6.
- Register: `.context/deferrals/cd-1_deferral-register.md` `## Assumptions` rows G-1 to G-12 match the plan's section 3 and the MF-2, MF-9 and MF-10 rules (G-1 bucket rules, G-3 four prefixes with `CONT_IDV_` and `ASST_AGG_` counted, G-4 state population from the SUMLEV 040 row).
- Reuse: searched `/home/user/cadence-core` (`scripts/`, `tests/conftest.py`, `shared/`) for FIPS padding, SSE reading, decimal summing and `os.replace` commits. No helper matches what the plan writes. The `## Reuse and extension` section names engine files that exist in this repo (`engine/config.py`, `engine/__main__.py`, `engine/tests/test_validate.py`, `engine/schema/`). The reuse check passes.
- Phase order: `/home/user/cadence-core/stages.json` is the Cadence pipeline-stage registry (A1 to the review stages). It does not list the build phases of this plan, so the plan's Phase 1 to 7 order is not checked against it. Phase order was last checked in cycle 1 and the titles have not changed since.
- Byte identity with the cycle 4 plan (af7ec7aa) was not checked, because no copy of that version is in the snapshot. The check relies on the fourth update's own statement that it changes no text.
- Data facts: the bucket counts (28, 8, 21, 7,724, 2,039) and the Census state sums were checked by the cycle 4 review on the 2026-10-22 data in `data/raw/`. They are not re-checked here.

## Must-fix items

None.

## Notes (not blocking)

- Phase 3 text at plan line 168 still says "the 2021 fallback per county (N-1)". The third update's MF-13 (state-level rule, plan line 487) governs. Build and DECISIONS must follow MF-13. This sentence was in the plan when cycle 3 passed it, so it is a note.
- Rules 1 and 3 both write `UNKNOWN|UNKNOWN` to `dim_place` and the marts (MF-11). `bucket_rule` is only in staging, so the marts do not show the split. DECISIONS must say so.
- Cycle 4 notes stay open, not re-checked: the Phase 2 first-two-characters assertion for rows with a blank state; the name `census_county_2024`, which holds SUMLEV 040 rows (Phase 2, line 159); the name and severity of the dbt test that reports the six old Connecticut keys (line 412); the failure action of `test_award_key_one_agency` on all eight zips; the Connecticut Amendment A change, which stays logged as awaiting the user (line 417; DECISIONS must not mark it settled); and the missing commit checkpoint per phase and rollback step.
- Cycle 2 notes listed in the second update (line 436) also stay open.

## Verdict

READY TO EXECUTE. Open must-fix items: none. The orchestrator may run E1 on this plan. The Amendment A question for Connecticut is still open for the user.
