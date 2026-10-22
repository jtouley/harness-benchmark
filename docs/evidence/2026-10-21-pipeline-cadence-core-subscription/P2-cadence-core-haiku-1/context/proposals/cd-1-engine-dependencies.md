---
decision_id: cd-1-engine-dependencies
status: proposed
question: Which packages does the engine add beyond the pinned set, to read YAML, validate it, and run tests?
choice: Add pyyaml and jsonschema as runtime dependencies, and pytest as a dev dependency, all through uv add with exact versions in uv.lock.
rationale: The engine must read YAML with line numbers and validate it against a schema with file and line errors, and neither is in the pinned set. The option rejected is a hand-written YAML parser, which would be a large untested surface.
---
Ticket: cd-1
