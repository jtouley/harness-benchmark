---
decision_id: cd-1-stream-dedupe-checkpoint
status: proposed
question: What key dedupes stream events, and what checkpoint lets make stream resume without double count or loss?
choice: Dedupe key is the event meta.id; the lake stream table is merged on meta.id. Checkpoint file lake/stream/_checkpoint.json holds the last committed Last-Event-ID and arrival_seq, written after commit through a temp file and os.replace. A resumed run sends Last-Event-ID when the checkpoint has one.
rationale: The SSE stream has no offset, so Last-Event-ID is the only resume position. A merge on meta.id makes a replay harmless even when the endpoint ignores Last-Event-ID (vibe-test R-2). Rejected options: an offset checkpoint (no offset exists in the stream) and an in-memory seen-set (lost on restart, so it cannot guarantee no double count across runs).
---
Ticket: cd-1

Applies to Phase 6 (stream client and merge) and checks 5 in Phase 8. Gap G-5 is settled by this record.
