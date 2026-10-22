---
decision_id: cd-1-stream-commit-manifest
status: proposed
question: How do the stream data, the consumer position and the running max event time commit together?
choice: A JSON manifest at lake/_state/stream_manifest.json lists the committed batch files, the last SSE id and last_arrival_seq. The running max event time is not stored; dbt derives it from fact_edit and the earlier rows of the batch (plan update 2026-10-21, MF-1). Batch files are written to a temp name and renamed; the manifest is replaced by rename last. Files not in the manifest are orphans and are deleted on start.
rationale: A crash before the manifest rename leaves an orphan file that is never counted, and the events are re-read once. A crash after it leaves a consistent state. The option rejected is a separate offset file written after the data, which can leave data committed with no position, or a position with no data.
---
Ticket: cd-1
