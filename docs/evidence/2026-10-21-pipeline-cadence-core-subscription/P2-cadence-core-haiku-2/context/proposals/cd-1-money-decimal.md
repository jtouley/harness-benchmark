---
decision_id: cd-1-money-decimal
status: proposed
question: What type holds money in the lake and the marts?
choice: decimal128(18,2) for every dollar amount from the source, with sums in decimal arithmetic. A source value with more than 2 decimal places fails the build. obligations_per_person is decimal128(18,4), computed as net obligations divided by population, rounded half-even at that last step only.
rationale: The spec requires exact sums in US dollars. Float64 sums drift and make the reconciliation in Check 4 fail. The rejected option was float64 with rounding at output, which hides drift. Per-person values cannot be exact, so they are rounded once, at the end.
---
Ticket: cd-1
