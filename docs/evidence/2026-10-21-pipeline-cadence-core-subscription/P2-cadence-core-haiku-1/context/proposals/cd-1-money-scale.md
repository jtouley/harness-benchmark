---
decision_id: cd-1-money-scale
status: proposed
question: How are dollar amounts stored and summed so the sums are exact?
choice: DECIMAL(18,2) in Arrow and in DuckDB. A value with more than 2 decimal places fails the run in the engine's to_decimal step.
rationale: The source amounts are whole cents, so a scale of 2 is exact and a larger scale adds no information. Failing on extra decimals surfaces a source change instead of silently rounding. The option rejected is float64, which the request forbids for sums.
---
Ticket: cd-1
