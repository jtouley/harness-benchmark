---
decision_id: cd-1-money-type
status: proposed
question: What type holds dollar amounts so that sums are exact?
choice: Obligations and net amounts are DECIMAL(18,2); the per-person ratio is DECIMAL(18,4); net bytes are BIGINT; no FLOAT or DOUBLE in any model.
rationale: Exact decimal sums meet the spec rule and the source precision (cents). Rejected: DOUBLE (rounding error in sums) and integer cents (more casting code for the same result).
---
Ticket: cd-1
