---
decision_id: cd-1-geography-basis
status: proposed
question: Which location of an award gives its state and county, and what happens when it is missing?
choice: The recipient location (prime_award_transaction_recipient_state_fips_code and recipient county FIPS), because the question asks where money went. Obligations with a missing or unmatched county go to a sentinel place (state UNK, county 00000) in dim_place, so every dollar stays in the mart and Check 4 reconciles.
rationale: The place of performance is a second geography and is kept in the fact for later use. The rejected option was dropping unmatched rows, which breaks the reconciliation to the source total. Unmatched counties are measured in Phase 3 and reported.
---
Ticket: cd-1
