---
decision_id: cd-1-population-fallback
status: proposed
question: How is the county population joined and what is used where a county has no 2024 estimate?
choice: Join on the 5-digit FIPS (state plus county, from the 2024 file); use POPESTIMATE2024 (July 1 2024); where a key is absent from the 2024 file, use the 2021 vintage estimate and record population_year and population_source; never read the 2020 base column.
rationale: Matches Amendment A (July 1 2024, latest earlier estimate, said in DECISIONS). Rejected: the 2020 census base (Amendment A excludes it) and dropping absent counties (leaves a per-person gap).
---
Ticket: cd-1
