---
decision_id: cd-1-award-key-and-sign
status: proposed
question: What is the award key for check 3, and is the sign test applied to each transaction or to the sum per award?
choice: Award key is generated_unique_award_id; net obligation is summed per award over FY2024 transactions, then the sign test is applied to that sum.
rationale: The check counts awards, and an award can have a positive and a negative transaction that net to a positive value. Rejected: the transaction-level sign test (counts transactions, not awards) and the award_id_piid key (not unique across agencies).
---
Ticket: cd-1
