---
decision_id: cd-1-stream-commit
status: proposed
question: How does the stream sink commit data and the consumer position so that a crash cannot lose or repeat an event?
choice: One manifest file per micro-batch, lake/_commits/stream_recentchange/<seq>.json, holds the SSE position, the watermark, the arrival sequence and the list of batch files. Batch files are written first. The manifest is written to a temp name and renamed; the rename is the commit. On start, the newest manifest sets the resume point, and batch files that no manifest lists are deleted.
rationale: The spec requires the position and the data to commit in one step. A single rename is the only step that is atomic on a POSIX file system here. The rejected option was a separate position file written after the data, which repeats a batch if the crash falls between the two writes. The rejected option was a DuckDB transaction, which would make the lake depend on DuckDB for ingestion.
---
Ticket: cd-1
