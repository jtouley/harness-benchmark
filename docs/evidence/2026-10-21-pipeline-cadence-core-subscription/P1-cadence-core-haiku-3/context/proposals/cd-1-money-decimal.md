---
decision_id: cd-1-money-decimal
status: proposed
question: What numeric type holds money totals and per-person values?
choice: DECIMAL(18,2) for obligation totals and DECIMAL(18,4) for per-person values, with half-up rounding for the per-person value.
rationale: The request requires exact money. Decimal arithmetic gives exact cent totals. The option rejected is DOUBLE, which introduces binary rounding error in sums.
---
Ticket: cd-1
