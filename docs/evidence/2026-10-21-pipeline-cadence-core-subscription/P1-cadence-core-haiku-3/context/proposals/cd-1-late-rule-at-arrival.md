---
decision_id: cd-1-late-rule-at-arrival
status: proposed
question: Where is the late-event flag computed for Question B?
choice: In the consumer at first arrival, from the max event time seen before that event. The flag and max_event_time_before are stored per event.
rationale: The request defines lateness by arrival order. Arrival order exists only in the consumer, so the rule is decided there once. The option rejected is recomputing lateness in dbt from event time, which cannot recover the arrival order.
---
Ticket: cd-1
