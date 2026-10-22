---
decision_id: cd-1-make-targets
status: proposed
question: Which make targets run the batch and the stream, and what does each run? (G-9)
choice: Only make build and make stream. build runs the batch engine, then dbt build --exclude tag:stream. stream requires DURATION, runs the engine with --duration, then dbt build --select tag:stream.
rationale: The request names two targets, and the stream dbt step must run after the engine commits. Rejects new targets per step, which the request does not name.
---
Ticket: cd-1
