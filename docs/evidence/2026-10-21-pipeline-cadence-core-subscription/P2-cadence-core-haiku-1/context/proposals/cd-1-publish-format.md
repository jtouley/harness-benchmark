---
decision_id: cd-1-publish-format
status: proposed
question: How are the marts written to out/marts/, given that dbt-duckdb builds them as DuckDB tables?
choice: An on-run-end dbt macro runs COPY to out/.marts-staging/<mart>/part-0.parquet for every mart in the publish list. The engine's publish prepare and swap steps move staging to out/marts (plan update 2026-10-21 cycle 2, MF-6). Parquet with the declared column types, no compression choice beyond the default.
rationale: The spec asks for Parquet under out/marts/, and a COPY after the contract-checked build publishes exactly the enforced columns. The option rejected is dbt external materialization, which does not support the incremental stream mart.
---
Ticket: cd-1
