---
decision_id: cd-1-late-events
status: proposed
question: How is an event marked late, and where is the watermark kept?
choice: At its first arrival, an event is late when the highest timestamp among the earlier first arrivals is strictly greater than window_end + 600 seconds, where window_end = window_start + 300 and window_start = floor(timestamp / 300) * 300. The engine computes is_late at ingest, in arrival order. A late event is flagged in the raw table, written to late_events, and kept out of the window mart. The watermark (highest timestamp seen) is saved in each manifest.
rationale: The spec defines lateness in stream time and forbids a wall-clock reading. Arrival order exists only at ingest, so the engine must decide there and store the result. The watermark goes in the manifest so that a restart does not reset it. The rejected option was a dbt-side rule over the lake, which cannot recover arrival order after a restart.
---
Ticket: cd-1
