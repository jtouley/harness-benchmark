---
decision_id: cd-1-event-time
status: proposed
question: Which field is the event time used for windows and lateness? (N-7)
choice: The timestamp field, an integer count of epoch seconds.
rationale: Integer arithmetic for window_start, no parsing per row, and exact comparison with the 10-minute lateness bound. Rejects meta.dt, an ISO string that would add a second time source.
---
Ticket: cd-1
