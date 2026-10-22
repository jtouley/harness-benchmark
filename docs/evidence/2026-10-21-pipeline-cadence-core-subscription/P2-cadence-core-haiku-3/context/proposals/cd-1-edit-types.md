---
decision_id: cd-1-edit-types
status: proposed
question: Which change types count as edits, and how are null lengths treated? (G-6)
choice: edit and new are edits. log and categorize stay in the fact with their change_type. Null length gives a 0 byte delta and has_length false.
rationale: Matches the meaning of an edit. Rejects counting every change event as an edit.
---
Ticket: cd-1
