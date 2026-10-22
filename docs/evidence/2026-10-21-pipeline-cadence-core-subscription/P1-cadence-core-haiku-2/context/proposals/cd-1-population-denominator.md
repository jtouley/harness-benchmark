---
decision_id: cd-1-population-denominator
status: proposed
question: Which population is the per-person denominator, for each cut, and what happens when a geography has no July 1 2024 estimate?
choice: Use POPESTIMATE2024 from co-est2024-alldata.csv (July 1 2024) for state and county cuts. Use the national population (sum of the 3,144 county POPESTIMATE2024 values) for awarding agency and month cuts. Fallback when a county has no 2024 value: the latest earlier estimate, in order POPESTIMATE2023, 2022, 2021, 2020 from co-est2024, then from co-est2021. Each mart row carries population_source, and build_report.json counts fallback rows. DECISIONS.md states the rule.
rationale: The amendment in the request asks for the July 1 2024 estimate with a latest-earlier fallback and a DECISIONS note. The census file has no state-free population, so the national denominator is the sum of counties. Rejected options: the 2021 file as primary (wrong vintage) and an unlabeled fallback (fallbacks would be invisible).
---
Ticket: cd-1

Applies to Phase 3 (census sources), Phase 4 (per-person marts), Phase 5 (build report) and check 4 in Phase 8. Gaps G-4 and N-1 are settled by this record.
