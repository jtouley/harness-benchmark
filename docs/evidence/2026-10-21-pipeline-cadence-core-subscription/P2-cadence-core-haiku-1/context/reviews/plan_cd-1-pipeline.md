RUN_BY_COMMAND: plan-review

Verdict: READY WITH CHANGES

Last reviewed plan sha256: 71c1bad953a6e02e6c8febcd12c007b98c81a5223d7f53f93460167824beb407

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Ticket: cd-1
Pipeline-Run: 0f84b2cc-3cf4-4553-b890-6f79e87e0cd2

Plan: `.context/plans/cd-1-pipeline.plan.md` (cycle 5, delta review of the Plan update 2026-10-21 (cycle 4), lines 478-526).
Input vibe test: `.context/vibetest/cd-1_2026-10-21.md` (sha256 f5ed4852...).
Previous review: `.context/reviews/plan_cd-1-pipeline.md` (sha256 e21870f1..., cycle 4, READY WITH CHANGES, MF-10). This file overwrites it, as the loop requires.
Packet sha256: 91ab486387392192ded648826375fa3f6e2e4ef96d68598d5ec5a153867d54fe.
Cycle count: this is the fifth review of the loop (`plan_review_cycles` default 5). The verdict is blocking, so the loop ends here without another review.

## Status of earlier items

| Id | Status | Evidence |
|---|---|---|
| MF-10 | closed | Plan update (cycle 4), MF-10 (lines 484-503). Lines 488-491 map a Connecticut place with county `09110` to `09190` to the state's `UNKNOWN` county, with no crosswalk. Lines 501-503 name the red fixtures and the real-build checks. Checked against `data/raw/usaspending/`: the Connecticut county codes in FY2024 are `09001` (6), `09003` (4), `09005` (1), `09009` (1), `09011` (2), `09013` (2), `09110` (2), `09170` (4), `09180` (2). The six 2021 codes are in the 2021 county file, so they join. The three planning-region codes map to `UNKNOWN`. Ledger row MF-10 (line 525). The same rule leaves a gap for other states, see MF-11. |

## Must-fix items

- MF-11: Places in the territories have no population row, and the plan has no rule for them. The rule at lines 488-491 sets `UNKNOWN` only for a missing county or a Connecticut planning region. The join test at lines 501-502 fails on "a place's `county_fips5` is not `UNKNOWN` and has no row in `int_county_population_2024`".
  Checked: the census files hold no `SUMLEV = 050` rows for states `60`, `66`, `69`, `72` or `78`. Their `STATE` values run `01` to `56` only. The FY2024 USAspending files hold 23 rows with a county code in those states: Puerto Rico (`72`) 11 rows (`72127` 9, `72021` 1, `72113` 1), Guam (`66`) 5 rows (`66010`), U.S. Virgin Islands (`78`) 4 rows (`78030`), Northern Mariana Islands (`69`) 2 rows (`69110`), American Samoa (`60`) 1 row (`60050`).
  Consequences under the current text:
  (a) Each of the 23 rows fails `transform/tests/test_place_population_join.sql`. So `dbt build` fails, and Acceptance 5 (plan line 80) cannot pass.
  (b) Their dollars have no county population basis. Check 4 for those states cannot be stated as written.
  The plan must choose one rule and name the test that checks it. Options: (1) map a place in a state with no census county file to the county member `UNKNOWN`, keep its state, and keep the code in `source_county_fips5`. Or (2) add a stated exclusion for those states to the join test, with the rule written in the plan. Either way: a red fixture (a state `72` place with county `72127` fails before the rule and passes after it), the count by state written to `DECISIONS.md` from the real build (23 rows, as above), and the population columns NULL for these places, as MF-10 already sets for `UNKNOWN`.

## Notes (not blocking)

- N-5: `transform/tests/test_connecticut_planning_region.sql` (plan line 503) says "any row of `dim_place` ... has a county in `09110` to `09190`". Line 491 keeps the code as read in `source_county_fips5`, so a test that scans any county column of `dim_place` fails on the real build. Name the column `county_fips5` in the test text.
- N-6: The 57 FY2024 rows with an empty state also have an empty county. MF-10 (lines 488-491) gives a rule for the county only. G-5 (plan line 60) says a missing state maps to `UNKNOWN`. Add the state rule to the list at lines 488-491, so the state key of `dim_place` is never null. Check 4 depends on it.
- N-7: Checked and holding: no FY2024 `federal_action_obligation` or `total_dollars_obligated` value has more than 2 decimal places (9,820 rows), so `to_decimal` (MF-7) does not fail on the current data. All `action_date` values fall within 2023-10-01 to 2024-09-30. Every non-empty county code begins with its row's state code, and every county code is 5 characters (N-2 holds).
- N-8: The plan settles G-1 to G-8 and N-1 to N-8 in its assumption table (plan lines 52-70). The register rows are unchanged by cycle 4 and are not reviewed here.

## Verdict basis

One must-fix item is open: MF-11, the territory places. MF-10 is closed. The rule for Connecticut planning regions holds on the real data. The verdict is READY WITH CHANGES, which blocks E1. This is cycle 5 of 5.
