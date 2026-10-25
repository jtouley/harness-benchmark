---
type: llm
focus: trace
weight: 1
---

[recall:stop-mid-flush-drops-events] The final review reports as must-fix: A stop or crash between dlt normalize and load leaves a pending package; the next run builds its seen-set and checkpoint without it and drops events it read, against the spec's stop/start rule.
