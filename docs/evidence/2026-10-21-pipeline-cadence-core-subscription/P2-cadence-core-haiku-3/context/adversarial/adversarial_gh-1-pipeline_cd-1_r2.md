RUN_BY_SKILL: de-adversarial-reviewer
Mode: plan-gate
Pipeline-Run: 5c0a2846-be0c-4861-b63f-0189a220b806
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Ticket token: cd-1 (task gh-1)

Plan: `.cursor/plans/gh-1-pipeline_cd-1.plan.md`, sha256 bc627afef4e446e7f38eafba64764162bdb823fa65820a1c655d194d7438ad31 (matches the input line). The file has 538 lines and includes the fourth plan update of 2026-10-22.
Round 2. Round 1 is `.context/adversarial/adversarial_gh-1-pipeline_cd-1.md` (plan sha256 af7ec7aa..., verdict REQUEST CHANGES, blocking B-1 and B-2).

## Verification notes

Checked on 2026-10-22 against the real files in `data/raw/` (stdlib csv, zipfile only). Nothing was written to `data/raw/`.

- Round 1 blocking B-2 (territories) reproduced: FY2024 rows (`action_date_fiscal_year = 2024`, 9,820 rows) with `prime_award_transaction_place_of_performance_state_fips_code` in 60, 66, 69, 72, 78: 138 rows, $21,008,281.50 (72: 75 rows, $12,372,178.72; 66: 25, $5,685,941.95; 69: 12, $1,382,703.51; 78: 15, $740,219.32; 60: 11, $827,238.00).
- `data/raw/census/co-est2024-alldata.csv` has 51 SUMLEV 040 rows (states 01 to 56, no 60, 66, 69, 72 or 78). The territories have no state population row in the 2024 file.
- Round 1 blocking B-1 reproduced: FY2024 rows with county key in 09001, 09003, 09005, 09009, 09011, 09013: 16 rows, $2,601,171.10.
- Amendment A in `.context/proposals/cd-1.md` (line 50 onward) reads: "Where a county has no 2024 estimate, use the latest earlier estimate and say so in DECISIONS.md." The plan's MF-13 replaces this with a state-level rule and keeps the county fallback out. The plan's own text says the Amendment A question is "awaiting the user" (plan lines 417, 483, 525).
- `.context/proposals/cd-1-per-person.md` still carries the Amendment A rationale (line 6: "Matches Amendment A"). The plan's fourth update says no decision record changes, so that record and the plan now disagree.
- Plan lines 168 and 215 still say "the 2021 fallback per county" (round 1 C-2). The plan's own fourth update lists line 168 as stale and open.
- The fourth update of 2026-10-22 (plan review cycle 4) changes no plan text. It says "Open items: none". Its verdict is not re-checked here. This review does not rely on it. The plan review did not address B-1 or B-2, and the plan text has no territory rule (searched for "territor", "Puerto", "51 states" context: only "51 states" in `test_census_state_sum` and MF-10).

## Blocking issues

### B-1. Amendment A is still replaced by a state-level rule that the request does not give, and the user has not confirmed it

Same as round 1 B-1, still open. MF-13 makes the fallback state-level and states that it "adds no row" in the 2024 file. The request says per-county fallback. The six old Connecticut county keys (16 FY2024 rows, $2,601,171.10) get NULL population, so they are not ranked in check 2 (MF-7) and only a dbt test reports them.

The plan asks the user to confirm this (plan line 417). It still goes to execution with the rule in place. A rule that the user has not confirmed should not be the default. Required before E1, one of:
(a) implement Amendment A as written (a county fallback to `POPESTIMATE2021` for the six keys, named per county in DECISIONS.md), and keep the no-mixed-geography test as a guard on that fallback; or
(b) stop before E1 and ask the user to confirm the state-level rule. Rewrite `.context/proposals/cd-1-per-person.md` in either case so it matches the plan.

### B-2. Five territories (138 FY2024 rows, $21,008,281.50) have no population row and no stated rule

Same as round 1 B-2, still open. The plan has no rule for states 60, 66, 69, 72 and 78. The Census 2024 file has no state or county row for them. Effects:
- `stg_census__state` has no row for them.
- `mart_obligations_state_monthly` takes `state_population` from `stg_census__state` (MF-10). An inner join drops these rows. Check 4 then fails (state totals no longer add to the source total). A left join gives NULL per-person.
- MF-13's state-level fallback adds nothing for them, because the 2021 file has no rows for them either.
- Their county-level keys (for example 66010, 72021, 72113, 72127, 78030, 69110, 60050) are in the data, and none is in Census 2024.

The plan must state the rule (for example: keep them in state and source totals with NULL population and a named dbt test, or exclude them from the state grain by a named rule that is also in check 4). It must add the test that proves the rule and the DECISIONS entry. The phrase "all 51 states" in the plan does not cover them.

## Conditions

### C-1. G-12 changes the request's "YAML only" rule (decision record needed)

Still open (round 1 C-1). `cd-1-mart-definition` makes a mart a dbt SQL model with a schema YAML entry. The request says "needs YAML only, no Python". DECISIONS must quote the request sentence, state the deviation, and mark it for the user to confirm. The plan leaves the quote as an open note.

### C-2. Stale Phase 3 text

Still open (round 1 C-2). Plan line 168 says "the 2021 fallback per county (N-1)". MF-13 replaces it. Correct line 168 in the plan itself before execution. The E1 agent reads the phase text first.

### C-3. PyYAML is an undeclared direct import

Still open (round 1 C-3). `cd-1-engine-schema` uses `yaml.compose`. PyYAML is not in `pyproject.toml`. The cycle 2 note says it is transitive through dbt-core and "to be stated in Phase 1". Phase 1 text does not yet say so. Add it to Phase 1 and to DECISIONS, with a test or check that PyYAML is in `uv.lock`.

### C-4. Replay tests for `Last-Event-ID` and `meta.id` are notes, not tests

Still open (round 1 C-4). Phase 5 must carry a fake SSE server test that resumes with `Last-Event-ID` after a disconnect, and a redelivered `meta.id` after restart (dropped, not counted in the running maximum).

### C-5. Failure action of `test_award_key_one_agency`

Still open (round 1 C-5; third update note). The plan does not say whether a failure stops `make build` or only fails the test. State it: a failure stops the build and names the file and key.

### C-6. Composite keys with a single separator

Still open (round 1 C-6; cycle 2 note). `obligation_key` and `state_obligation_key` concatenate with `|`. A value containing `|` is not excluded. Use a separator that cannot occur in the values, or test uniqueness on the three columns.

### C-7. Per-person in the monthly mart is not additive across agencies

Still open (round 1 C-7). `obligations_per_person_monthly` repeats the county population on every agency row. The column description must say so, and a test must check that each row equals obligations divided by its county population.

### C-8. Check 7 scope

Still open (round 1 C-8). Check 7 is "the row count of `late_events`". `late_events` holds every late first arrival (G-6: lateness applies to every first arrival), so it counts `log` and `categorize` events too. DECISIONS must say so, or the check must filter to edits.

### C-9. Replayed hour rule

Still open (round 1 C-9; cycle 2 note). G-10 takes the minimum `timestamp` over all of `fct_edit`, including `log` events. Record the rule and the value found in DECISIONS.md, and say that it includes non-edit events.

## Adversarial scenarios

| # | Scenario | Handled? | Evidence |
|---|---|---|---|
| S1 | Connecticut old counties (09001 to 09013): do the six keys get population and per-person values? | No | 16 FY2024 rows, $2,601,171.10. MF-13 and plan line 417 leave them NULL and "awaiting the user". See B-1. |
| S2 | Territories (states 60, 66, 69, 72, 78): where do their rows go, and do check 4's state totals still add up? | No | 138 FY2024 rows, $21,008,281.50. No Census 2024 rows for them. Plan has no rule. See B-2. |
| S3 | Blank country, blank state, blank county rows: each in one bucket, five counts add to staging. | Yes | Round 1 recount: 28 / 8 / 21 / 7,724 / 2,039 (total 9,820). Matches MF-11. Re-counted in round 2 only for the territory rows, not all five buckets. |
| S4 | Award key collision across the contract and assistance files, or a prefix outside the four. | Yes | Prefix families disjoint (round 1 recount). MF-9 test `test_award_key_disjoint_files`. |
| S5 | One award key with two agencies. | Partly | Plan says none in the 417 zips. Failure action not stated (C-5). |
| S6 | Census state row differs from its county sum for any state. | Yes | Round 1 check: all 51 states match in 2024. `test_census_state_sum` (MF-10). |
| S7 | Duplicate `dbname` in sitematrix, or `enwiki` missing. | Yes | Round 1: 949 `dbname` values, all unique, `enwiki` present. |
| S8 | Late event exactly 10 minutes after window end. | Yes | Late is `max_prev > window_end + 600`, strictly. Phase 5 test. |
| S9 | Crash between `_tmp` write and `os.replace`, and after it. | Yes | Phase 5 crash tests. Leftover `_tmp/` on start is an open note (round 1 C-4). |
| S10 | Make target count and pins. | Yes | Only `build` and `stream` used. Pins unchanged in the plan. |

## Trade-offs

- B-1 and B-2 are the same as round 1. The fourth plan update (cycle 4) did not change them, so the plan is not ready for E1. Either fix them in the plan, or stop and ask the user first (B-1 needs the user's answer either way).
- The plan's cycle 4 "READY TO EXECUTE" verdict does not count as evidence here. This review reads the plan text and the data directly.
- The stream design (footer commit, `os.replace`, stream-time lateness) still matches the request. No gap found there.

Verdict: REQUEST CHANGES
