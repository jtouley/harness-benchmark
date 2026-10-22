---
decision_id: cd-1-late-event-watermark
status: proposed
question: What is stream time, and when is an event late, so that the 5-minute window mart is reproducible from the lake?
choice: Stream time is a watermark over arrival order: the max event timestamp among events with a smaller arrival_seq. Event k is late when watermark > window_start + 900 seconds (window end plus 10 minutes) at its first arrival. Late events go to late_events with the watermark value and are excluded from mart_edit_window_5min. Published windows are not restated.
rationale: Arrival order is stored in the lake, so a rebuild gives the same late set. Wall-clock stream time would change on each rebuild and break idempotence. Rejected option: restating a window when a late event arrives, because a published number would change after it was published.
---
Ticket: cd-1

Applies to Phase 7 (late routing) and check 7 in Phase 8. Gap G-6 is settled by this record.
