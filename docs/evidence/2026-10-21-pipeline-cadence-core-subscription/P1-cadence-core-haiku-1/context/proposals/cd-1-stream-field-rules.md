---
decision_id: cd-1-stream-field-rules
status: proposed
question: What is counted when length, bot, wiki key or the replayed hour is missing or unnamed?
choice: A missing length gives bytes_delta 0 with has_length false; a missing bot flag gives actor_type human; wiki is the sitematrix dbname (enwiki) joined from the stream wiki value, with server_name for en.wikipedia.org; the replayed hour is every landed event, and its first and last event time go to DECISIONS.md.
rationale: Each event still counts as an edit, so check 5 counts every consumed edit; the flags keep the defaults visible. Rejected: dropping events with missing fields (breaks the count) and a clock-based hour (the spec forbids a clock reading for lateness, and the hour is defined by the capture).
---
Ticket: cd-1
