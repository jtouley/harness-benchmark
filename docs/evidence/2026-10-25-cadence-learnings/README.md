# Cadence run-learnings documents

One learnings document per Cadence run, from Oct 19 to Oct 24 (P1 and P2 pipeline runs, the shapes-r2 batch,
and the earlier arm, `c`/`k`/`q`/`r`/`s`/`t`/`u`/`v`/`w`/`x`/`y`/`z` and `d` series runs).

- **Produced by:** Cadence's `run-learnings` command (each file starts `RUN_BY_COMMAND: run-learnings`), run
  after each Cadence run. Each header names the run, the Cadence commit (or `unrecorded`) and the sha256 of the
  packet it read.
- **Date:** the date prefix of each file name is the run's date. All 86 documents and `ROLLUP.md` were
  regenerated in the coordinator's scratchpad `learnings/` at 03:22 to 03:24 UTC on 2026-10-25 (new packet
  hashes); this folder is that version, committed by the evidence agent the same day.
- **`ROLLUP.md`:** ranks the candidate proposals across the 86 runs by how many runs' own records support each.

## Verified versus inferred

Every proposal is a candidate, as each file says: "A proposal changes a skill only after the
revision-against-current eval on stored diffs shows no regression." Every eval line reads `Eval: pending`, so
none of the proposals is verified. The evidence lines quote the run's own records and transcript.

## Redactions

Commit-trailer email addresses (`noreply@anthropic.com`, 36 occurrences in 8 of the `20261024-*` files) were
replaced with `[redacted-email]`. Nothing else was changed.
