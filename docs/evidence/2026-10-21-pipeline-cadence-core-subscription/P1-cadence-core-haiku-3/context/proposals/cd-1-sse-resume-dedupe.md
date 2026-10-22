---
decision_id: cd-1-sse-resume-dedupe
status: proposed
question: How does the SSE consumer resume after a disconnect without loss or double counting?
choice: A persisted cursor (last event id and time) plus deduplication on meta.id against the stored id set, with Last-Event-ID sent on reconnect when the server supports it.
rationale: The cursor gives no loss. The id dedupe gives no double count even when the server replays. The options rejected are offset-only resume, which trusts the server to never replay, and at-most-once delivery, which loses events on a disconnect.
---
Ticket: cd-1
