# Time bucketing of Cadence transcripts

`bucket.py` splits a Cadence run's stream-json transcript into time buckets by what each tool call was doing,
and prints per run: wall time, a sum per bucket, minutes per peer, reverted edits, the top tool calls,
redundant calls, stops, segments and sinks. Usage: `python3 bucket.py <transcript.jsonl>...`.

Buckets, from the code: `a` product code written, `b` tests and oracles written, `c` long-running commands
(pytest, dbt, make, uv, sleeps and waits), `d` Cadence process work (`.context/`, `DECISIONS`, plans, ledgers,
Cadence scripts, skills), `h` other tool calls; `e` to `g` are assigned in `run()`.

- **Produced by:** an analysis subagent of the coordinator session (the file names no author).
- **Date:** 2026-10-24 (file time 22:12 UTC). Committed by the evidence agent on 2026-10-25.

## Verified versus inferred

The script measures time from transcript timestamps. Which bucket a call falls in is a heuristic (regular
expressions over paths and commands), so a bucket total is an estimate. Its outputs (`ana/out*.txt`) were not
requested and are not committed; re-run it on the runs-store transcripts to reproduce them.
