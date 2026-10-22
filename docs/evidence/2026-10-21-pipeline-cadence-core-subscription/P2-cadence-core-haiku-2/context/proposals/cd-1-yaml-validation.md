---
decision_id: cd-1-yaml-validation
status: proposed
question: How does the engine validate a pipeline YAML file and report where a problem is?
choice: PyYAML for parsing, with yaml.compose to keep node marks. jsonschema (Draft 2020-12) validates the schema in engine/schema/pipeline.schema.json. Each error maps its JSON path to the node's line and column and prints file:line:col: problem.
rationale: The spec requires file, line and problem on every error. Node marks give the line. The rejected option was pydantic, which reports field paths but not lines without extra work. The rejected option was hand-written checks, which drift from the documented schema.
---
Ticket: cd-1
