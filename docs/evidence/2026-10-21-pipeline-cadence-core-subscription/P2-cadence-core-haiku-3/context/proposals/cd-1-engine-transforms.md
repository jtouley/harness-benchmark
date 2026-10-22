---
decision_id: cd-1-engine-transforms
status: proposed
question: Which engine runs each transform in the YAML?
choice: The transform names engine polars or datafusion. Polars does row-wise steps; DataFusion does SQL steps.
rationale: The request names both engines for the ingestion side. Rejects a single engine, which would drop one named dependency.
---
Ticket: cd-1
