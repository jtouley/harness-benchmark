---
decision_id: cd-1-lake-layout
status: proposed
question: How is the Parquet lake laid out, and what load metadata does it keep?
choice: One folder per lake table, Parquet, rows sorted by key, deterministic file names; load metadata is _source_sha256 and _source_file only.
rationale: Keeps make build idempotent (G-8) with no wall-clock values. Rejects a load timestamp or run id, which change every build.
---
Ticket: cd-1
