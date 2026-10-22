---
decision_id: cd-1-lake-parquet-dlt
status: proposed
question: What storage format and writer hold the raw lake under lake/?
choice: Parquet files written by dlt with the filesystem destination.
rationale: Parquet keeps the raw layer open to any engine and matches the request. The option rejected is loading raw rows straight into the DuckDB file, which would couple the raw layer to one engine.
---
Ticket: cd-1
