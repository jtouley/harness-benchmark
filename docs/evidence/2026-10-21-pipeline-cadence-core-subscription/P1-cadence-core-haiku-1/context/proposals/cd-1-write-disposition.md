---
decision_id: cd-1-write-disposition
status: proposed
question: Which dlt write disposition does each source use so that running make build twice changes no output?
choice: Batch raw sources use replace; the stream table uses append with the consumer's meta.id dedupe in front; marts are overwritten by dbt external materialization.
rationale: Replace makes the batch idempotent; append is needed for the stream, and the dedupe prevents double counts. Rejected: dlt's default append for the batch sources (second run doubles rows).
---
Ticket: cd-1
