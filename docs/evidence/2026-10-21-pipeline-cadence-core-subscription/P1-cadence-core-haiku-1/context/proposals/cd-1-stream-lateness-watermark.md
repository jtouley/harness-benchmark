---
decision_id: cd-1-stream-lateness-watermark
status: proposed
question: What is the lateness watermark, does it persist across make stream runs and reconnects, and do late events raise it?
choice: The watermark is the running max of event time over all first arrivals, computed in dbt over arrival_seq and kept in fct_edit; it persists because the fact persists; late events are included in the max.
rationale: The spec defines the rule over earlier arrivals, so persistence and inclusion follow from it. A late event has event time at most its window end, and it is late only when the max already exceeds window end plus 10 minutes, so it can never raise the max; the question has no effect on results. Rejected: a per-run reset (makes the result depend on how the run was split) and wall-clock time (the spec forbids it).
---
Ticket: cd-1
