---
decision_id: cd-1-place-and-unplaced
status: proposed
question: Does place mean place of performance or recipient location, and how are rows without a state or county handled so that county totals equal state totals?
choice: Place means place of performance; a row with no valid US state goes to an Unplaced member (state 99, county 99999); a row with a state but no county goes to an Unknown county member (state FIPS plus 000); both are rows of dim_place, so no row is dropped.
rationale: Where the money went is the place of performance. The explicit members keep the reconciliation exact. Rejected: recipient location (answers where the recipient is, not where the money went) and dropping unplaced rows (breaks check 4).
---
Ticket: cd-1
