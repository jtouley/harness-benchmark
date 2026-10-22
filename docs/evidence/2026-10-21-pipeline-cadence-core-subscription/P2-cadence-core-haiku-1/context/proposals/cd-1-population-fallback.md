---
decision_id: cd-1-population-fallback
status: proposed
question: Which population figure is used per county under Amendment A, and what does a county without a 2024 estimate get?
choice: POPESTIMATE2024 from co-est2024-alldata.csv, keyed by state and county FIPS. A county missing from that file takes POPESTIMATE2021 from co-est2021-alldata.csv, with population_as_of = 2021 recorded on the row. The fallback is computed in the dbt model int_county_population_2024, not in the engine (plan update 2026-10-21, MF-4). Connecticut's 2024 file has nine planning regions (state 09, county 110 to 190) in place of its eight counties, with no crosswalk. The nine planning-region rows are dropped, and the eight 2021 Connecticut counties take population_as_of = 2021 (plan update 2026-10-21 (cycle 3), MF-9).
rationale: Amendment A asks for the latest earlier estimate, and the 2021 vintage is the latest earlier one in the data. The 2020 census count is excluded as the analysts asked. The option rejected is dropping the county, which would break the county sum check.
---
Ticket: cd-1
