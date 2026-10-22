---
decision_id: cd-1-county-place
status: proposed
question: Which county and state is a USAspending row placed in? (G-1)
choice: Place of performance. Foreign places go to state FOREIGN and county FOREIGN; US rows without county FIPS go to county UNKNOWN in their state.
rationale: Every row lands in one bucket, so check 4 reconciles exactly. Rejects recipient county (a company's address is not where the money went) and dropping rows.
---
Ticket: cd-1
