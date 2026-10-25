# Enforcement gate: verification logs

Logs from verifying the Cadence enforcement-gate branch (`fix/enforcement-gate`, head `4c437ca`): the entry-point
check run on the stored shapes-r2 trees, the budget simulation over their transcripts, the test suites and
ci_local.

- **Produced by:** the enforcement-gate agent (a working session of the coordinator).
- **Date:** 2026-10-25 (log times 00:11 to 03:15 UTC). Committed by the evidence agent the same day.

| File | What it is |
|---|---|
| `verify.log`, `verify400.log`, `verify_final.log` | The entry-point check in a clean checkout of each run's tree, at `DURATION=150` and `400`: `OK`, or `FAIL` with the reason (for example a consumer that reconnects with one `Last-Event-ID` and never gets past it). |
| `sim_budget.jsonl` | Per run: where the supervisor budget would first deny a call, and how many work calls it would deny. |
| `replay0.log` | The local replay server's log during the checks. |
| `gates.log`, `tgc.log` | Gate test suites: 1970 passed, 1 skipped; 46 passed. |
| `full.log` | The full suite in one attempt; it ends in `OSError: could not create numbered dir ... /tmp/pytest-of-root` (a shared-`/tmp` problem on that machine, not a test result). |
| `ci_local.log` | `ci_local: all CI steps passed at 4c437ca`, exit 0. |
| `push.log` | The push of `fix/enforcement-gate` to jtouley/cadence. |

## Verified versus inferred

Everything here is tool output, so it records what ran. Which runs pass or fail the entry-point check is
measured on the stored trees. What the budget would have saved (`sim_budget.jsonl`) is a simulation over stored
transcripts, not a run under the gate.
