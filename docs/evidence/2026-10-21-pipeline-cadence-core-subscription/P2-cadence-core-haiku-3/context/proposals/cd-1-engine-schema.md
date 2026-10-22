---
decision_id: cd-1-engine-schema
status: proposed
question: How is each pipeline YAML validated, and how are errors tied to a file and line?
choice: JSON Schema draft 2020-12 checked with jsonschema (added as a direct dependency); line numbers from the PyYAML node tree (yaml.compose).
rationale: Schema is data, so new fields need no Python. Rejects pydantic and hand-written checks, which would duplicate the schema in code.
---
Ticket: cd-1
