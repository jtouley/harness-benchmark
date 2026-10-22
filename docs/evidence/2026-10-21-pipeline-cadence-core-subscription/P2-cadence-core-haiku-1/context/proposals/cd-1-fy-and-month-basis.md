---
decision_id: cd-1-fy-and-month-basis
status: proposed
question: Which date defines FY2024 and the month of an award transaction, and which amount is net obligations?
choice: The date is action_date. FY2024 is action_date from 2023-10-01 to 2024-09-30 inclusive. Month is the calendar month of action_date. Net obligations is the sum of federal_action_obligation.
rationale: action_date is the date the USAspending archive uses to assign a transaction to a fiscal year, and the README says these files hold rows with action date in FY2024. The option rejected is action_date-free grouping by the period of performance start, which is not the federal fiscal year definition.
---
Ticket: cd-1
