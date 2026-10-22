# Deferral register: cd-1

Ticket: cd-1
Pipeline-Run: 0f84b2cc-3cf4-4553-b890-6f79e87e0cd2
RUN_BY_COMMAND: plan-create

## Approved deferrals

No approved deferrals.

## Assumptions

| Gap | Assumption | Settled by |
|---|---|---|
| G-1 | Dedup key is meta.id, checked against every committed batch file in the manifest. Resume position is the SSE id of the last committed event, sent as Last-Event-ID. | Phase 5 tests (tests/test_stream_resume.py, row restart_redelivers_committed_id); decision cd-1-stream-dedup-resume |
| G-2 | The running max event time is not stored. dbt derives it from fact_edit and the earlier rows of the batch. | Phase 5 test_stream_commit (no max_event_time key); Phase 6 transform/tests/test_late_after_restart.sql; decision cd-1-stream-commit-manifest |
| G-3 | fact_edit holds all consumed edits with is_late. The window mart counts on-time edits only. late_events is the is_late subset. | Phase 6 late-event singular test; check 5 and check 7 views; decision cd-1-late-event-placement |
| G-4 | FY2024 is action_date from 2023-10-01 to 2024-09-30 inclusive. Month is the calendar month of action_date. | Phase 4 dbt test transform/tests/test_fy2024_bounds.sql; decision cd-1-fy-and-month-basis |
| G-5 | Place is place of performance. Missing state or county maps to an UNKNOWN member, so check 4 reconciles. | Phase 4 singular test check_county_state_source; transform/tests/test_place_county_unknown.sql; decision cd-1-place-basis |
| G-6 | An award is the prime award unique key. It is negative when its FY2024 net obligation sum is below zero. | Phase 4 check_negative_awards view; decision cd-1-negative-award-key |
| G-7 | Load metadata is deterministic (file name, SHA-256, row number, batch sequence). No wall-clock time in lake/ or out/. | Phase 2 test_lake_sink (identical bytes on rerun); Phase 7 hash check; decision cd-1-load-metadata |
| G-8 | The engine lands and dedups events and assigns arrival_seq. dbt computes lateness, windows and the late split. | Phase 5 (engine side), Phase 6 (dbt side); decision cd-1-stage-ownership |
