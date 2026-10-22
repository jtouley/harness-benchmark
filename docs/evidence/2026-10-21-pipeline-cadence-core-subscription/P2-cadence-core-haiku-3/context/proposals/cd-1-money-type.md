---
decision_id: cd-1-money-type
status: proposed
question: What type holds money, and how is per-person rounded? (G-5)
choice: DECIMAL(18,2) in the lake and marts. Per-person rounded half away from zero (DuckDB round).
rationale: Exact sums are required. Rejects DOUBLE, which is not exact.
---
Ticket: cd-1
