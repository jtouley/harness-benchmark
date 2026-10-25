---
type: llm
focus: trace
weight: 1
---

[recall:stream-consumer-does-not-survive-invalid-frame] The final review reports as must-fix: The stream consumer does not consume the whole replayed stream: on a frame whose data is not valid JSON (the replay sends it on every reconnect) it reconnects without end, so `make stream` never reaches the end of its input and the stream marts are incomplete.
