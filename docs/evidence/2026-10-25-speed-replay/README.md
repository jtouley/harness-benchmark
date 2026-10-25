# Speed SLO: the shapes-r2 transcripts replayed through the supervisor rules

The scripts and output that measured where Cadence-on-Haiku time goes, and how much the supervisor rules on the
Cadence branch `fix/speed-slo` would remove, without any new run.

- **Produced by:** the speed agent (a working session of the coordinator) for the Cadence speed PR, whose body
  is `pr-body.md` (branch off #228 at `9314a61`; commits `998a8d3`, `98c306c`, `3419ec7`, `4c471f3`,
  `9e9e40d`, `a012132`).
- **Date:** 2026-10-24 to 2026-10-25 (file times 23:33 to 01:09 UTC). Committed by the evidence agent on
  2026-10-25.

| Path | What it is |
|---|---|
| `bin/tl.py` | Timeline of a stream-json transcript: main-thread tool calls with start and end. |
| `bin/replay.py` | Measures phases, gate loops and removable time per run (basis: the Oct 15 Haiku one-shot `agent_wall_seconds`). |
| `bin/replay2.py` | Replays the transcripts through `scripts/supervisor.py` of `fix/speed-slo`. Usage: `replay2.py <tx dir> <cadence worktree> <out.json>`. |
| `bin/e1.py`, `bin/e1deep.py`, `bin/afterdoc.py` | E1 decomposition, and work a block did after writing its document. |
| `replay2.json` | `replay2.py`'s output, one entry per run. |
| `pr-body.md` | The PR body with the before and after table. |

## Verified versus inferred

- **Measured:** "Before" minutes are agent wall time from the stored transcripts (runs-store, Cadence `2100c6e`).
  The PR's checklist records `scripts/ci_local.sh` passing at `a012132`.
- **Projected, not measured:** "After" is before minus the union of the intervals the rules would remove; no
  run has been made with the rules. The PR itself says **the SLO is not met** (shortest projected run 58 min
  against 33 to 39).

## Left out

The transcripts (`slo/tx/`, `slo/oneshot-*.jsonl`; already in runs-store), push logs and the other drafts in
`slo/`.
