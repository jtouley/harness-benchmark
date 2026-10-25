---
type: llm
focus: trace
weight: 1
---

[recall:live-endpoint-no-user-agent-silent-exit] The final review reports as must-fix, shown from the code or a local stub (an outside request is not required): The consumer sends no User-Agent header (the live endpoint that the spec names requires one), and every connect failure is swallowed: on an unreachable or refusing endpoint the consumer prints nothing and exits 0.
