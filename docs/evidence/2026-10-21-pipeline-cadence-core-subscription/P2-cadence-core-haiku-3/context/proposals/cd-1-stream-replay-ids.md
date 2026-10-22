---
decision_id: cd-1-stream-replay-ids
status: proposed
question: How does the SSE consumer resume, and how is the wiki joined? (N-2, N-4)
choice: Resume with Last-Event-ID from the footer, using stdlib urllib. Wiki joins sitematrix by dbname; check 6 uses server_name.
rationale: No HTTP dependency added. Rejects requests and httpx as new dependencies.
---
Ticket: cd-1
