---
decision_id: cd-1-stream-tooling
status: proposed
question: Which libraries and test runner does the stream consumer and its tests use, given that the pins in pyproject.toml must not change?
choice: Stdlib urllib for SSE, stdlib unittest for Python tests, and dbt unit tests in yml for the SQL rules; no new dependency.
rationale: The pins are fixed by the spec, and pytest or an HTTP client would be a new dependency. Rejected: adding httpx or pytest to pyproject.toml.
---
Ticket: cd-1
