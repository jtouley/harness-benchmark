---
decision_id: cd-1-month-and-award
status: proposed
question: What is a month and what is an award? (G-2, G-3)
choice: Month is the calendar month of action_date (YYYY-MM). Award is one value of the award-level key of each file, as the file holds it, with its prefix: contract_award_unique_key (prefixes CONT_AWD_ and CONT_IDV_) or assistance_award_unique_key (prefixes ASST_NON_ and ASST_AGG_). Check 3 counts every such key, including CONT_IDV_ and ASST_AGG_, and returns a count per prefix family (plan update 2026-10-22, MF-1 and MF-9).
rationale: Calendar months are unambiguous labels for FY2024 rows. generated_unique_award_id is not in either file (checked on the CSV headers of all eight zips). The award-level keys span the contract and assistance files and identify one award each. The file values already carry their prefix, so the prefix is kept. The contract and assistance prefix families are disjoint, so no key is in both files. CONT_IDV_ (indefinite delivery vehicles) and ASST_AGG_ (aggregate assistance records) are award-level keys in their files and the plan has no rule that drops them; the per-prefix count lets a reader take them out. Rejects fiscal month numbering, per-transaction counts, generated_unique_award_id and stripping the prefix.
---
Ticket: cd-1
