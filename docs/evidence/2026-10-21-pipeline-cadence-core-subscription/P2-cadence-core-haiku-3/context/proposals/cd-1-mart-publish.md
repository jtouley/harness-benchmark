---
decision_id: cd-1-mart-publish
status: proposed
question: How are marts materialized and published as Parquet with an enforced contract?
choice: Marts are models with an enforced contract: table models, and the incremental window mart mart_edit_windows_5min (plan update MF-3). A post-hook copies each to out/marts/<mart>/<mart>.parquet after each build.
rationale: dbt-duckdb external materialization does not enforce the contract. Rejects external materialization.
---
Ticket: cd-1
