RUN_BY_SKILL: de-adversarial-reviewer
Mode: plan-gate
Pipeline-Run: 5c0a2846-be0c-4861-b63f-0189a220b806
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Ticket token: cd-1 (task gh-1)

Plan: `.cursor/plans/gh-1-pipeline_cd-1.plan.md`, sha256 af7ec7aa9206bb3fa0d9ab00581aebd8a5dbf7896fb9e23638450676ac476c94 (matches the input line).
Request: `.context/proposals/cd-1.md` (sha256 9ce8ff61312f1bd49b72db2eebcdd3f8ce263bbbd4b7821a852d6dcfea588758).
Round 1. No earlier plan-gate report exists in `.context/adversarial/`.

## Verification notes

Checked against the real files in `data/raw/` on 2026-10-22 (stdlib csv, zipfile, json only):

- USAspending: all eight zips hold the columns that the plan names (both file types: `awarding_agency_code`, `action_date`, `action_date_fiscal_year`, `federal_action_obligation`, `primary_place_of_performance_country_code`, state FIPS, county FIPS; Contracts: `contract_award_unique_key`, `contract_transaction_unique_key`, `award_id_piid`, `primary_place_of_performance_state_code`; Assistance: `assistance_award_unique_key`, `assistance_transaction_unique_key`, `award_id_fain`, `primary_place_of_performance_state_name`). Neither file type has `generated_unique_award_id`. Confirmed.
- FY2024 rows: 9,820. Bucket rules of MF-2 (as revised by MF-11) give 28 / 8 / 21 / 7,724 / 2,039 for rules 1 to 5. Confirmed.
- Award key prefixes: `ASST_NON_` 9,336, `ASST_AGG_` 68, `CONT_AWD_` 388, `CONT_IDV_` 28. The two file families are disjoint. Confirmed.
- Census 2024 and 2021: 51 SUMLEV 040 rows each. In 2024, every state's county `POPESTIMATE2024` sum equals its state row. Connecticut 2024 has nine planning-region rows (09110 to 09190). Connecticut 2021 has the eight old counties (09001 to 09015), with `POPESTIMATE2021`. Confirmed.
- No Census file has rows for states 60, 66, 69, 72 or 78 (American Samoa, Guam, Northern Mariana Islands, Puerto Rico, Virgin Islands). The plan does not mention them.
- sitematrix: 949 `dbname` values, all unique. `enwiki` present. Confirmed.
- Makefile: `build` and `stream` are stubs. pyproject pins match the plan. Confirmed.
- PyYAML is not declared in `pyproject.toml`. It is in `uv.lock` as a dependency of dbt-core (lock lines 219, 292).

## Blocking issues

### B-1. Amendment A is rewritten against the analysts' instruction, and the decision record is not updated

The request (`.context/proposals/cd-1.md`, Amendment A) says: "Where a county has no 2024 estimate, use the latest earlier estimate and say so in DECISIONS.md." The plan's MF-10 and MF-13 change this to a state-level rule: a county fallback is "never applied county by county", and the plan says "the fallback adds no row" for the 2024 file. Result for Connecticut:

- The six old-county keys (09001, 09003, 09005, 09009, 09011, 09013) have no 2024 row. The 2021 file does have a `POPESTIMATE2021` for each one. Under Amendment A they take that value. Under the plan they get NULL population, are excluded from check 2 (MF-7), and are only reported by a dbt test.
- These keys carry 16 FY2024 rows and $2,601,171.10 of obligations (recounted from the zips).
- `.context/proposals/cd-1-per-person.md` (status `proposed`) still says "Missing 2024 county uses POPESTIMATE2021". The plan's rule contradicts that record, and the record was not rewritten. `core:decision-coverage` needs the record and the plan to agree.
- The plan itself lists this as "Open for the user" (plan line 417) and as "awaiting the user". The plan still goes to execution with the rule in place. A user decision that the plan has not received should not be built in as the default.

Required before execution, one of:
(a) implement Amendment A as the analysts wrote it (county-level fallback to `POPESTIMATE2021` for the six keys, named per county in DECISIONS.md), and keep MF-13's no-mixed-geography test as a guard on the fallback source; or
(b) stop the plan at this point and ask the user to confirm the state-level rule before E1. Rewrite `cd-1-per-person.md` in either case.

### B-2. Five territories have no population row and no stated rule

FY2024 `primary_place_of_performance_state_fips_code` values 60, 66, 69, 72 and 78 (American Samoa, Guam, Northern Mariana Islands, Puerto Rico, Virgin Islands) occur in the USAspending data: 138 FY2024 rows, $21,008,281.50. Neither Census file has a SUMLEV 040 or 050 row for these states (the 2024 and 2021 files each have 51 state rows). The county keys 66010, 72021, 72113, 72127, 78030, 69110 and 60050 are in the data, and none is in Census 2024.

The plan says "51 states" in `test_census_state_sum` and in MF-10. It does not say what happens to these rows in:
- `stg_census__state` (no SUMLEV 040 row, so no state population);
- `mart_obligations_state_monthly` (`state_population` joins `stg_census__state`; an inner join drops these rows and fails check 4, a left join gives NULL per-person);
- MF-13's state-level fallback (no 2021 rows either, so it adds nothing);
- the DECISIONS list in Phase 7.

Check 4 requires state totals to add to the source total, so the territory rows must be either carried with a stated NULL population or excluded by a named rule. The plan must state which, and add the test that proves it.

## Conditions

### C-1. G-12 changes the request's "YAML only" rule (decision record needed)

The request says "Adding a new source or mart of the same kinds needs YAML only, no Python." The plan's G-12 and `cd-1-mart-definition` make a mart a dbt SQL model plus a schema YAML entry. A dbt model is SQL by nature, so the conflict is in the request text as well. DECISIONS must quote the request sentence, state the deviation, and say that the user should confirm it. The plan notes the quote as open (MF-note, cycle 2 and 3) and it is still open.

### C-2. Stale Phase 3 text

Plan line 168 still says "the 2021 fallback per county (N-1)". MF-13 overrides it. The E1 agent reads the phase text first. Correct line 168 in the plan, or add a strikethrough, before execution.

### C-3. PyYAML is an undeclared direct import

`cd-1-engine-schema` uses `yaml.compose` (PyYAML). PyYAML is not in `pyproject.toml`. The plan forbids new pins. Either the engine uses it through a declared route, or Phase 1 records the transitive import in DECISIONS and adds a test that fails if PyYAML is missing from `uv.lock`.

### C-4. Replay tests for `Last-Event-ID` and `meta.id`

Both are open notes since cycle 1. Phase 5 should carry them as tests, not notes: a fake SSE server that resumes with `Last-Event-ID` after a disconnect, and a redelivered `meta.id` after restart (dropped, not counted in the maximum).

### C-5. Failure action of `test_award_key_one_agency`

The test runs on all eight zips (MF-9). The plan does not say whether a failure stops the build or only fails the test. Name it: a failure stops `make build` with the file and key.

### C-6. Composite keys without a safe separator

`obligation_key` and `state_obligation_key` are concatenations with a single separator (MF-8). With variable-width place keys (`UNKNOWN`, `FOREIGN`, 2-digit states), a collision is possible in principle. Use a separator that cannot occur in the values, or assert uniqueness on the three columns, not the concatenation.

### C-7. Per-person in the monthly mart is not additive across agencies

`mart_obligations_monthly.obligations_per_person_monthly` repeats the county population on every agency row (G-4). A reader who sums this column across agencies gets a wrong value. The column description must say so (plan says it will), and a test should check that the per-person value equals obligations divided by the county population on each row.

### C-8. Check 7 scope

"The count of late events" is ambiguous. G-6 makes `log` and `categorize` first arrivals late too, so `late_events` includes them. DECISIONS must say whether check 7 counts all change types or only edits.

### C-9. Replayed hour

G-10 takes the minimum `timestamp` over all of `fct_edit`, which includes `log` events. This is an open note (cycle 2). Record the rule and the value found in DECISIONS.md, and say that it includes non-edit events.

## Adversarial scenarios

| # | Scenario | Handled? | Evidence |
|---|---|---|---|
| S1 | Connecticut old counties after the 2024 planning-region change: do the six keys get population and per-person values? | No | MF-10, MF-13. 2021 file has `POPESTIMATE2021` for 09001 to 09013. 16 FY2024 rows, $2,601,171.10 with NULL per-person. See B-1. |
| S2 | Territories (states 60, 66, 69, 72, 78): where do their rows go, and do check 4's state totals still add up? | No | 138 FY2024 rows, $21,008,281.50. No Census rows for these states. Plan says "51 states". See B-2. |
| S3 | Blank country, blank state, blank county rows: each lands in one bucket and the five counts add to the staging count. | Yes | Recount: rule 1 = 28, rule 2 = 8, rule 3 = 21, rule 4 = 7,724, rule 5 = 2,039, total 9,820. MF-11 asserts these. |
| S4 | Award key collision across the contract and assistance files, or a prefix outside the four. | Yes | Four prefixes, disjoint families. MF-9 test `test_award_key_disjoint_files`. |
| S5 | One award key with two agencies. | Yes for the 417 zips only | Plan says no such key in 417. The test runs on all eight zips (C-5). |
| S6 | Census state row differs from its county sum for any state. | Yes | Checked: all 51 states match in 2024. `test_census_state_sum`. |
| S7 | Duplicate `dbname` in sitematrix, or `enwiki` missing. | Yes | 949 `dbname` values, all unique, `enwiki` present. |
| S8 | Late event exactly 10 minutes after window end. | Yes | Late is `max_prev > window_end + 600`, strictly. Matches the request. Test in Phase 5. |
| S9 | Crash between `_tmp` write and `os.replace`, and after the replace. | Yes | Phase 5 crash tests. Leftover `_tmp/` on start is an open note (C-4). |
| S10 | Make target count and pins. | Yes | Only `build` and `stream` added as used. pyproject pins unchanged. |

## Trade-offs

- Blocking B-1 and B-2 can be fixed inside the plan, or by asking the user first. The plan is not ready for E1 until one of them is chosen.
- The plan adds a dbt model for each mart instead of YAML only (C-1). That is the right engineering choice, but it needs the user's confirmation.
- Stream design (footer commit, `os.replace`, stream-time lateness) matches the request closely. I found no gap there.

Verdict: REQUEST CHANGES
