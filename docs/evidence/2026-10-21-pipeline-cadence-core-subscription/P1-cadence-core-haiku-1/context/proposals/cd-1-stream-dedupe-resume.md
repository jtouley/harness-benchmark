---
decision_id: cd-1-stream-dedupe-resume
status: proposed
question: How does the stream consumer avoid double counting and losing events across disconnects and restarts, when the replay server may not honor Last-Event-ID?
choice: Dedupe key is meta.id checked against the landed lake; the lake is the state; Last-Event-ID from a cursor file is only a hint; the cursor advances only after a successful land.
rationale: Works whether or not the server resumes; a replay that restarts from the top is deduped, so nothing is counted twice or lost. Rejected: Last-Event-ID alone (the replay may not honor it) and a composite key of wiki, timestamp and title (not unique).
---
Ticket: cd-1
