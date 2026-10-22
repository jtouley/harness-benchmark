---
decision_id: cd-1-make-target-split
status: proposed
question: Which make target builds which part, so that make build does not depend on the stream and make stream does not rebuild batch models?
choice: make build runs the batch ingestion and dbt build with exclude tag stream; make stream runs the consumer and dbt build with select tag stream.
rationale: Keeps each target's inputs separate, so the batch build stays idempotent without the stream lake. Rejected: one target that builds everything (the stream lake would be needed for make build).
---
Ticket: cd-1
