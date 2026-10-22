---
decision_id: cd-1-stream-commit
status: proposed
question: How is the consumer position committed in the same step as the micro-batch data?
choice: One Parquet file per micro-batch, written to _tmp/ then moved by a single os.replace. The footer holds last_sse_id, max_event_time and the batch id.
rationale: One atomic rename commits data and position together (G-7). Rejects a separate position file, which is a second write and can split.
---
Ticket: cd-1
