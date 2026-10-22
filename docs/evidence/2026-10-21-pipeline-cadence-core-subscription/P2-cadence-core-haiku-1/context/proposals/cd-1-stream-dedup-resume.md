---
decision_id: cd-1-stream-dedup-resume
status: proposed
question: What identifies an edit for dedup, and where does the stream consumer resume after a disconnect?
choice: Dedup key is meta.id, checked against every committed batch file in the manifest, not only the current run (plan update 2026-10-21, MF-2). Resume position is the SSE id of the last committed event, sent back as Last-Event-ID on reconnect.
rationale: meta.id is unique per recentchange event and is present in every replayed event, so a re-delivered event is detected by key. Last-Event-ID lets the server skip what was committed. The option rejected is resuming from a wall-clock timestamp, which replays by arrival time and cannot prove no gap.
---
Ticket: cd-1
