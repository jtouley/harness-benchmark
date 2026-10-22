---
decision_id: cd-1-marts-external-parquet
status: proposed
question: How are the marts published to out/marts/?
choice: dbt-duckdb external materialization writes each mart as Parquet under out/marts/.
rationale: The request requires the marts at out/marts/. External Parquet gives a published file that any consumer can read. The option rejected is a warehouse table only, which the request does not name as a deliverable.
---
Ticket: cd-1
