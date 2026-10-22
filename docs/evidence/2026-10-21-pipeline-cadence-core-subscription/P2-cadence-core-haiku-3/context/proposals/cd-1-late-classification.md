---
decision_id: cd-1-late-classification
status: proposed
question: Where and how is an event classed as late, and what is the dedupe key?
choice: The engine classes each first arrival at ingest. Late when the running maximum event time over all first arrivals in arrival order is more than window_end + 10 minutes. The running maximum starts from the max_event_time in the footer of the last committed batch, and a late first arrival still advances it. Dedupe on meta.id. Window mart reads on-time rows only.
rationale: The rule needs stream history across batches, which the engine keeps in the footer (max_event_time) of the last committed batch. The footer stores the running maximum after the batch (plan update MF-1). Rejects dbt-side classification, which has no history across batches.
---
Ticket: cd-1
