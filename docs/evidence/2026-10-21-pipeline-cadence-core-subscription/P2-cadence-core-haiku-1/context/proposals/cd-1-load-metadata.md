---
decision_id: cd-1-load-metadata
status: proposed
question: What load metadata does the lake keep, and may it reach an output?
choice: Load metadata is deterministic only: source file name, source SHA-256, row number within the file, and batch sequence number. No wall-clock time is written to lake/ or out/. Marts do not include load metadata columns.
rationale: Idempotence (a second make build changes nothing) needs every stored value to be a function of the input. The option rejected is a load timestamp per row, which changes on every run.
---
Ticket: cd-1
