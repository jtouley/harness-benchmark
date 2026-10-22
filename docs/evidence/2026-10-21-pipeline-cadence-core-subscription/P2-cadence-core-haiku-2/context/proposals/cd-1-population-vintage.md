---
decision_id: cd-1-population-vintage
status: proposed
question: Which population is the per-person denominator, and what is the fallback?
choice: The July 1, 2024 estimate (POPESTIMATE2024 in co-est2024-alldata.csv). A county with a blank 2024 value uses the latest earlier value in the same file (2023, then 2022, then 2021). A county absent from the 2024 file uses the 2021 file, under the same rule. Each fallback use is counted and listed in DECISIONS.md.
rationale: Amendment A says per person means the July 1, 2024 estimate and not the 2020 census count. The 2021 file has only 2020 and 2021, so it is a last resort. The rejected option was the 2020 census base, which Amendment A excludes.
---
Ticket: cd-1
