---
decision_id: cd-1-no-new-dependencies
status: proposed
question: Which test runner and dbt packages does the project use?
choice: Stdlib unittest for Python tests and dbt built-in tests. No new dependency and no dbt packages.
rationale: The request forbids changing the pinned versions in pyproject.toml. Adding pytest or dbt_utils changes the dependency set. The option rejected is adding pytest as a dev dependency.
---
Ticket: cd-1
