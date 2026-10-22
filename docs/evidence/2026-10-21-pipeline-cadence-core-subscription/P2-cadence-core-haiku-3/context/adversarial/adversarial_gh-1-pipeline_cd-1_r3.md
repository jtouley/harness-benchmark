RUN_BY_SKILL: de-adversarial-reviewer
Mode: plan-gate
Pipeline-Run: 5c0a2846-be0c-4861-b63f-0189a220b806
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Ticket token: cd-1 (task gh-1)

Plan: `.cursor/plans/gh-1-pipeline_cd-1.plan.md`, sha256 f0da065845db18f59bea84057a1d4f8d22e92ab9e08e8e4956f80089559d4a19 (matches the input line). The file has 572 lines and ends with the fifth `## Plan update 2026-10-22`.
Request: `.context/proposals/cd-1.md`. Round 3. Round 1 is `adversarial_gh-1-pipeline_cd-1.md` (plan af7ec7aa..., REQUEST CHANGES, B-1, B-2). Round 2 is `adversarial_gh-1-pipeline_cd-1_r2.md` (plan bc627afe..., REQUEST CHANGES, B-1, B-2).

## Verification notes

Checked on 2026-10-22 against the real files in `data/raw/` (stdlib csv, zipfile, and a read of the Census CSV headers and SUMLEV counts only). Nothing was written to `data/raw/`.

- Territories, reproduced: FY2024 rows (`action_date_fiscal_year = 2024`) with `prime_award_transaction_place_of_performance_state_fips_code` in 60, 66, 69, 72, 78: 138 rows, $21,008,281.50. By state: 72 = 75 rows, $12,372,178.72; 66 = 25, $5,685,941.95; 69 = 12, $1,382,703.51; 78 = 15, $740,219.32; 60 = 11, $827,238.00.
- Census 2024 (`co-est2024-alldata.csv`) has 51 SUMLEV 040 rows and 3,144 SUMLEV 050 rows. Census 2021 has 51 SUMLEV 040 rows and 3,143 SUMLEV 050 rows. Neither file has a state row for 60, 66, 69, 72 or 78 in the 2024 file.
- Connecticut old counties, reproduced: FY2024 rows with county key in 09001, 09003, 09005, 09009, 09011, 09013: 16 rows, $2,601,171.10.
- `.context/proposals/cd-1-per-person.md` still says "Missing 2024 county uses POPESTIMATE2021" (choice line) and "Matches Amendment A" (rationale). The deferral register G-4 row says "NULL where N-1 leaves no population". The record and the register disagree with each other, and the plan (MF-13) gives a third rule.
- The request (`.context/proposals/cd-1.md` line 51) reads: "Where a county has no 2024 estimate, use the latest earlier estimate and say so in DECISIONS.md."
- The plan review `.context/reviews/plan_gh-1-pipeline_cd-1.md` (verdict READY TO EXECUTE, cycle 5) says the Amendment A question "is still open for the user". Its verdict does not discharge B-1 or B-2. Its own note lists the open Amendment A change as a note, not a must-fix. This review does not rely on that verdict.
- Searched the plan (all 572 lines) for "territor", "Puerto", "Guam", "Samoa", "Virgin", "Marian", and state codes 60, 66, 69, 72, 78. No territory rule exists. The only "51 states" phrases are in `test_census_state_sum` and MF-10.
- Round 2 blocking items are unchanged in the fifth update. The fifth update says "Required changes: None" and "Phase changes: None" and changes no plan text. The plan therefore has the same B-1 and B-2 as round 2.

## Blocking issues

### B-1. Amendment A is still replaced by a state-level rule, and the user has not confirmed it (open since round 1)

The request's Amendment A requires a per-county fallback to the latest earlier estimate, with each case named in DECISIONS.md. The plan (MF-10, MF-13, plan line 417) instead makes the fallback state-level and states that it "adds no row" in the 2024 file. Result for Connecticut: the six old-county keys (09001, 09003, 09005, 09009, 09011, 09013) have NULL population, 16 FY2024 rows and $2,601,171.10 of obligations. They are not ranked in check 2 (MF-7) and only a dbt test reports them.

The plan itself marks this as "awaiting the user" in four places (plan lines 417, 483, 525, 558). The plan still goes to E1 with that rule in place. The rule is a default the user has not chosen. The fifth update did not change it. The per-person record still states the request's rule, so the decision record and the plan disagree (`core:decision-coverage`).

Required before E1, one of:
(a) Implement Amendment A as written: a county fallback to `POPESTIMATE2021` for the six keys, each named in DECISIONS.md. Keep `test_census_no_mixed_geographies` as a guard on that fallback. Rewrite `cd-1-per-person.md` to match.
(b) Stop before E1 and ask the user to confirm the state-level rule. Rewrite `cd-1-per-person.md` to match the answer.

### B-2. Five territories (138 FY2024 rows, $21,008,281.50) have no population row and no stated rule (open since round 1)

States 60, 66, 69, 72 and 78 occur in the FY2024 USAspending data. Neither Census file has a state row for them (see verification notes). The plan has no rule for them. Effects, as in round 1 and round 2:
- `stg_census__state` has no row for them (MF-8 grain is one state from the SUMLEV 040 row).
- `mart_obligations_state_monthly` takes `state_population` from `stg_census__state` (MF-10). An inner join drops these rows, and check 4 then fails because state totals no longer add to the source total. A left join gives NULL per-person values with no stated meaning.
- MF-13's state-level fallback adds nothing for them, because the 2021 file has no rows for them either.
- The county keys (for example 66010, 72021, 72113, 72127, 78030, 69110, 60050) do not appear in Census 2024.

Required: state the rule for these five states (for example, keep them in state and source totals with NULL population and a named dbt test, or exclude them from the state grain by a named rule that check 4 also applies). Add the test that proves it, and the DECISIONS entry. The phrase "all 51 states" does not cover these rows.

## Conditions

### C-1. G-12 changes the request's "YAML only" rule (open since round 1; decision record needed)

The request says "Adding a new source or mart of the same kinds needs YAML only, no Python." `cd-1-mart-definition` makes a mart a dbt SQL model with a schema YAML entry. DECISIONS must quote the request sentence, state the deviation, and mark it for the user to confirm. The plan still leaves the quote as an open note (plan line 531-ish, "the G-12 quote in DECISIONS.md").

### C-2. Stale Phase 3 text (open since round 1)

Plan line 168 still reads "the 2021 fallback per county (N-1)". MF-13 replaces it. The E1 agent reads phase text first. Correct line 168 in the plan itself before E1. The plan's own notes list this as stale and open; it is not corrected.

### C-3. PyYAML is an undeclared direct import (open since round 1)

`cd-1-engine-schema` uses `yaml.compose`. PyYAML is not in `pyproject.toml`. The cycle 2 note says it is transitive through dbt-core and "to be stated in Phase 1", but Phase 1 text does not say so. Add it to Phase 1 and to DECISIONS, with a check that PyYAML is in `uv.lock`.

### C-4. Replay tests for `Last-Event-ID` and `meta.id` are notes, not tests (open since round 1)

Phase 5 must carry a fake SSE server test that resumes with `Last-Event-ID` after a disconnect, and a redelivered `meta.id` after restart (dropped, not counted in the running maximum). The plan lists these as "notes" in the fifth update.

### C-5. Failure action of `test_award_key_one_agency` (open since round 1)

The plan does not say whether a failure stops `make build` or only fails the test. State it: a failure stops the build and names the file and key.

### C-6. Composite keys with a single separator (open since round 1)

`obligation_key` and `state_obligation_key` concatenate with `|`. A value containing `|` is not excluded. Use a separator that cannot occur in the values, or test uniqueness on the component columns.

### C-7. Per-person in the monthly mart is not additive across agencies (open since round 1)

`obligations_per_person_monthly` repeats the county population on every agency row. The column description must say so, and a test must check that each row equals its obligations divided by its county population.

### C-8. Check 7 scope (open since round 1)

Check 7 is "the row count of `late_events`". `late_events` holds every late first arrival (G-6), so it counts `log` and `categorize` events. DECISIONS must say so, or the check must filter to edits.

### C-9. Replayed hour rule (open since round 1)

G-10 takes the minimum `timestamp` over all of `fct_edit`, including `log` events. Record the rule and the value found in DECISIONS.md, and say that it includes non-edit events.

## Adversarial scenarios

| # | Scenario | Handled? | Evidence |
|---|---|---|---|
| S1 | Connecticut old counties (09001 to 09013): do the six keys get population and per-person values? | No | 16 FY2024 rows, $2,601,171.10, NULL population. MF-13 and plan line 417 leave them "awaiting the user". See B-1. |
| S2 | Territories (states 60, 66, 69, 72, 78): where do their rows go, and do check 4's state totals still add up? | No | 138 FY2024 rows, $21,008,281.50. No Census 2024 state or county rows. No rule in the plan. See B-2. |
| S3 | Blank country, blank state, blank county rows: each in one bucket, five counts add to the staging count. | Yes | Round 1 recount: 28 / 8 / 21 / 7,724 / 2,039 (total 9,820). MF-11 asserts these. Not re-counted here. |
| S4 | Award key collision across contract and assistance, or a prefix outside the four. | Yes | Prefix families disjoint (round 1 recount). MF-9 test `test_award_key_disjoint_files`. |
| S5 | One award key with two agencies. | Partly | Plan says none in the 417 zips. The test runs on all eight zips, and the failure action is not stated (C-5). |
| S6 | Census state row differs from its county sum for any state. | Yes | Round 1 check: all 51 states match in 2024. `test_census_state_sum` (MF-10). Holds only for the 51 states (B-2). |
| S7 | Duplicate `dbname` in sitematrix, or `enwiki` missing. | Yes | Round 1: 949 `dbname` values, all unique, `enwiki` present. |
| S8 | Late event exactly 10 minutes after window end. | Yes | Late is `max_prev > window_end + 600`, strictly. Phase 5 test. |
| S9 | Crash between `_tmp` write and `os.replace`, and after it. | Yes | Phase 5 crash tests. Leftover `_tmp/` on start is an open note. |
| S10 | Make target count and pins. | Yes | Only `build` and `stream` used. Pins unchanged in the plan. |
| S11 | The fifth plan update and the plan review cycle 5 declare READY TO EXECUTE. Does that clear B-1 and B-2? | No | The fifth update changes no text and says "Open items: none". The plan review does not mention territories and treats Amendment A as an open note. Both blockers are still in the plan. |

## Trade-offs

- B-1 and B-2 have been open in three rounds. The plan's readiness verdicts (cycle 4 and cycle 5) do not address them. The fix is either a plan change (B-2 needs a rule, and B-1 needs a choice) or a stop to ask the user (B-1 needs the user's answer either way).
- The "YAML only" deviation (C-1) is the right engineering choice, but it needs the user's confirmation, as in round 1.
- The stream design (footer commit, `os.replace`, stream-time lateness) still matches the request. No gap found there.

Verdict: REQUEST CHANGES
