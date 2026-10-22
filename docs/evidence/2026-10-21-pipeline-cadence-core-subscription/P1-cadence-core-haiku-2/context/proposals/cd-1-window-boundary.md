---
decision_id: cd-1-window-boundary
status: proposed
question: Is a 5-minute window open or closed at its end, and how is an event assigned to a window?
choice: Windows are half-open [start, end) in UTC. window_start = floor(timestamp / 300) * 300 on epoch seconds. An event at exactly start + 300 belongs to the next window.
rationale: Each event falls in exactly one window, so the window totals add up to the event count (check 6). Rejected option: closed windows on both ends, which would count a boundary event twice.
---
Ticket: cd-1

Applies to Phase 7 (window assignment) and check 6 in Phase 8. Gap N-4 is settled by this record.
