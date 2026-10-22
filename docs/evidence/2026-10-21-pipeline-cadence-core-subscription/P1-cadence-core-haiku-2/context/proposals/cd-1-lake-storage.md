---
decision_id: cd-1-lake-storage
status: proposed
question: Where do raw loads and published marts live, and which tool moves data between them?
choice: dlt writes Parquet under lake/<source>/. dbt-duckdb reads the lake with read_parquet and builds the star schema. Published marts use external materialization to out/marts/<name>.parquet. out/warehouse.duckdb (the profiles.yml dev target) is a working database only; no published output depends on its tables.
rationale: The request names dlt for the lake and external materialization for the marts. Parquet files can be hashed directly, which makes check 1 (idempotent build) a file comparison. Rejected option: publishing tables from the DuckDB file, because a database file is not byte-stable across runs and cannot be read without DuckDB.
---
Ticket: cd-1

Applies to Phases 2, 3, 4 and 5. Dependencies are the existing pins (dlt 1.31.0, dbt-duckdb 1.11.0, duckdb 1.5.6); none is added.
