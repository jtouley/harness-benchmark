---
decision_id: cd-1-late-event-placement
status: proposed
question: Does the edit fact hold late events, given that a late event is not added to its window but check 5 counts every edit consumed?
choice: fact_edit holds every consumed edit with an is_late flag. mart_edit_window_5min counts only is_late = false. late_events is the view of fact_edit where is_late = true.
rationale: Check 5 needs all consumed edits, and check 7 needs the late count, so one fact with a flag answers both without a second copy. The window mart keeps the rule that late events are not added to windows. The option rejected is a separate late fact with no rows in fact_edit, which would make check 5 a union of two tables and split one grain across two models.
---
Ticket: cd-1
