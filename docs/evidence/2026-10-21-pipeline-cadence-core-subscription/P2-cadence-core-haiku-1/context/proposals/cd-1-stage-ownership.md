---
decision_id: cd-1-stage-ownership
status: proposed
question: Which stage owns event dedup, arrival order, lateness and the event time field, the engine or dbt?
choice: The engine lands events, dedups on meta.id, and assigns arrival_seq. dbt computes event time windows, lateness, the late split, the wiki join, the FY2024 row filter and the population fallback. The engine's to_decimal step changes the type only and keeps every row and value, and the sitematrix_flatten step reshapes sites without a derived column (plan update 2026-10-21, MF-4, and cycle 2, MF-5). Event time is meta.dt. dbt derives server_name from the sitematrix url host, which joins to get dbname and code.
rationale: Dedup and arrival order are facts about the stream connection, which only the consumer sees, so they belong in the landing step that owns the position. Lateness and windows are derived from landed facts, so they belong in dbt, as the spec requires for everything after the lake. The option rejected is dedup in dbt, which needs every raw duplicate in the lake and cannot guarantee no double count across a restart.
---
Ticket: cd-1
