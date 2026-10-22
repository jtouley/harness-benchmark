---
decision_id: cd-1-money-decimal
status: proposed
question: What numeric type stores USAspending amounts and per-person results so that sums stay exact?
choice: DECIMAL(18,2) for federal_action_obligation in the lake and in facts; DECIMAL(38,6) for per-person ratios, rounded half-up once at that step. No float or double in the money path.
rationale: Inferred types from dlt and DuckDB can produce float columns, which break exact sums (vibe-test C-1, R-1). Rejected option: inferred float types with a tolerance in checks. A tolerance hides rounding drift; the exact check needs no tolerance.
---
Ticket: cd-1

Applies to Phase 2 (dlt column hint), Phase 4 (fact and per-person marts) and check 2 in Phase 8.
