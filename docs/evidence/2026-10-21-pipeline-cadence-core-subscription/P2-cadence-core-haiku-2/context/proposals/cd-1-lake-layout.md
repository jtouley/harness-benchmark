---
decision_id: cd-1-lake-layout
status: proposed
question: How is the Parquet lake laid out, and how is each table written?
choice: One folder per table under lake/<table>/, with partition folders where partition_by is set. Each write goes to a temp folder and is renamed over the table folder. Load metadata is _source_file (relative path) and _source_row (integer) only. No wall-clock column.
rationale: Running make build twice must not change any output, so no run timestamp goes into the lake. An atomic rename keeps the last good table readable after a crash. The rejected option was a single DuckDB file as the lake, because dbt-duckdb reads Parquet folders directly and the spec puts the lake in Parquet. The rejected option was adding _loaded_at timestamps, which breaks rerun equality.
---
Ticket: cd-1
