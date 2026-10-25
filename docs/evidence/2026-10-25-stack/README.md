# The 2026-10-25 Cadence stack: verification evidence

Evidence for the combined Cadence branch `stack/2026-10-25` (cadence #228, #229, #231 and #232 merged, plus the
seven 2026-10-25 skill reviews and their gate follow-ups). Cadence #230 (the candidate review skill) is not in it.

- **Produced by:** the stack agent (a subagent of the coordinator), 2026-10-25.
- **Cadence commit verified:** `b463d95` (`cadence-head.txt`), merged to cadence main as `9fafe09` (jtouley/cadence#233).
- **Owner consent:** the postmortem update log, Oct 25 05:00 ("Do the suggestions, but wait for the other
  subagents and do their updates as well"; consent to merge the stack once it is combined and re-verified).

| File | What it is |
|---|---|
| `table.md` | The 11 shapes-r2 trees: recorded `stream_ok` against the gate's stream verdict, the fresh-clone check and the output check. |
| `verify/<run>.json` | `clean_checkout.clean_build` record of each tree (entries with `"fresh": true` ran first in their own fresh clone). |
| `verify/replay-dev.log` | The dev replay (seed 0, localhost:8099) during the checks. |
| `budget_replay.jsonl` | The context budget (`guard_context_budget.py` rules, shipped config) replayed on the 11 transcripts. |
| `supervisor_replay.json`, `supervisor_replay.log` | The supervisor rules replayed on the 11 transcripts (`replay2.py` of 2026-10-25-speed-replay, against this stack). |
| `m2_placeholder.log`, `verify/m2-*.log` | P1 core-6 after `make build` and a 3 s `make stream` (0 late events): the output check on `out/marts`. |
| `install_defaults.log` | The defaults read from a clean clone of the stack commit, the way the harness installs the plugin. |
| `ci_local.log` | `scripts/ci_local.sh` of the stack, with its own TMPDIR. |
| `bin/` | The scripts that produced the files above. |
| `skill-review-stopguard.md` | The stop-guard skill review (dispatch item 6), not pushed before. |

## Method

- Each tree is the `cadence/spec` head of the run's stored bundle (runs-store, via `runs/<run>/record.json`).
- The entry is the spec's stream command, `make stream DURATION=400`, input
  `sse http://localhost:8099/v2/stream/recentchange`, output `out/marts`. 400 s is under the 600 s Command cost
  limit and the supervisor's `command_max_seconds`; at 150 s, P2 full-6 does not drain (enforcement-gate log).
- The build step is the spec's `make build` only; the trees' `make test` and `make check` are not part of
  `stream_ok`, so they were not run.
- `uv` ran offline from its cache; dbt and dlt telemetry were off. No request left the machine.

## Verified versus inferred

- **Verified (tool output):** every verdict in `table.md`, the budget and supervisor replays, the install
  defaults, and ci_local.
- **Projected, not measured:** the supervisor replay's "after" minutes and the budget's denies are a replay of
  stored transcripts, not runs under the rules. How Haiku reacts to a deny still needs a real run.
- **Verified:** P2 core-6 and P2 core-5 fail the fresh-clone check for the same reason as P1 core-6: on a fresh
  tree, `make stream`'s dbt step finds no parquet that only `make build` writes (`lake/sitematrix`,
  `lake/usaspending_transactions`). See the `output` tails in `verify/<run>.json`.

## Results

- The gate's stream verdict (after the build) matches the recorded `stream_ok` on 11 of 11 trees.
- The fresh-clone check fails P1 core-6 (M1), P2 core-5 and P2 core-6, and every tree whose stream fails anyway.
  It passes P1 full-6, P2 full-5 and P2 full-6.
- The output check passes all 11 after a 400 s stream. It fails P1 core-6's placeholder row after a 3 s stream (M2).
- ci_local: 4600 passed, 2 skipped on Python 3.11 and 3.13; `ci_local: all CI steps passed at b463d95`.
