---
decision_id: cd-1-event-identity
status: proposed
question: What identifies one change event, and which events count as edits?
choice: The event key is meta.id from the recentchange event. The first arrival is kept; later copies are dropped and counted in the manifest. An edit has type edit or new. net_bytes is length.new minus coalesce(length.old, 0), with a null length.new counted as 0. Other types stay in the raw table only.
rationale: Reconnects redeliver events, so the key must be stable across restarts. meta.id is the stream's own event id. The rejected option was a hash of the whole payload, which breaks when a field is absent on replay. The rejected option was counting log and categorize events as edits, which inflates the counts in Questions B.5 and B.6. The field names are confirmed against the replay in Phase 5.
---
Ticket: cd-1
