---
decision_id: cd-1-engine-interface
status: proposed
question: How do sources, transforms and sinks plug into the engine?
choice: Three registries keyed by kind: sources, transforms, sinks. Each step takes and returns Arrow tables or record batch readers. A transform names its engine (polars or datafusion) in the YAML. A step is added by a registry entry and a schema entry, not by editing the run loop.
rationale: The spec requires that a new source or mart of an existing kind needs YAML only, and that data moves as Arrow. The rejected option was a plugin loader with dynamic import from YAML, which runs arbitrary code named in data. The rejected option was pandas as the common format, which the spec does not name.
---
Ticket: cd-1
