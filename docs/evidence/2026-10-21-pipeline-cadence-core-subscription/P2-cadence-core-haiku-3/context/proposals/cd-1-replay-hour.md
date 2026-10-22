---
decision_id: cd-1-replay-hour
status: proposed
question: Which hour does "the replayed hour" in check 5 mean? (G-10)
choice: The first UTC event-time hour in fct_edit: from date_trunc('hour', min(event_time)) to that plus one hour, end exclusive. Event time is the timestamp field.
rationale: The replay speed is wall-clock dependent, so a consumer-run hour is not testable. The event-time hour is fixed by the capture. Rejects the wall-clock hour of the consumer run and the whole lake.
---
Ticket: cd-1
