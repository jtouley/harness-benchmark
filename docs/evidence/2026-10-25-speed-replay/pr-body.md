## Summary

Speed SLO work for Cadence-on-Haiku runs. The branch is off #228 (`9314a61`). Each change is its own commit. Nothing here touches cadence-core. No gate passes more easily than before: a block that is still failing after its fix round now ends the run with a `retries` hard stop. It is not skipped.

The rules come from the owner (postmortem front matter and the Oct 24–25 log). ADR-0030 has the details.

1. **`perf(checks)` `998a8d3`**: `ledger_verify.py` and `acceptance_checks.py pass` run the same check one time on the same tree (`scripts/check_cache.py`). The key is the command, HEAD, the tracked diff and the untracked files. `.context/` and git-ignored files are not in the key. `ledger_verify` also gets the 600 s limit that `acceptance_checks` has.
2. **`feat(supervisor)` `98c306c`**: `hooks/guard_supervisor.py` (rules in `scripts/supervisor.py`) runs on every tool call:
   - The orchestrator runs no project runner (make, dbt, pytest, uv, npm, bash -c, project Python). A free-form subagent prompt and ScheduleWakeup/CronCreate are denied too. The hook acts only on Claude Code runs (session host `claude`), because Pi runs every block in one session.
   - Commands are bounded in every thread. The hook denies a polling loop, a sleep over 30 s, and a duration or timeout over 600 s.
   - A block that has written its document can only read or edit that document, or run Cadence scripts.
   - Each stages.json peer row has a budget: minutes, tokens and dispatches, plus trees for R2 and R3. A subagent is stopped when it goes over minutes or tokens, sits idle for 15 min, or gets the same result from the same call twice. It is then dispatched one more time.
   - Going past dispatches (2) or trees (2), or a block's second stop, records a hard stop. A closed run denies waits and new work.
   - SKILL.md: a `/spec-driven` peer runs E1 and the fix round.
3. **`feat(review)` `3419ec7`**: R2 and R3 are one `code-review` round that runs after R1, from the reviewed diff. One fix round covers R1, R2 and R3.
4. **Fixes found by ci_local and the replay** (`4c471f3`, `9e9e40d`, `a012132`): SKILL.md's `${CADENCE_HOME:-...}` form, quoted assignments, the runner list, Claude Code only, Pi fixtures, and refreshed pinned hashes with their reasons.

## Proof: stored transcripts replayed (no new runs)

The replay script feeds the 11 shapes-r2 transcripts (harness-benchmark `runs-store`, cadence 2100c6e) through this branch's `scripts/supervisor.py` rules and `stages.json` budgets. Minutes are agent wall time.

- SLO = 1.25 × the Oct 15 Haiku one-shot (`baselines.json`): P1 39.2 min, P2 33.3 min.
- "After" = before minus the union of the intervals the rules remove.

| Run | Before | After | SLO | P phase before→after | R phase before→after | R2 dispatches | R3 gate runs | E1 ran in | Orchestrator runner cmds (min) |
|---|---|---|---|---|---|---|---|---|---|
| P1-core-4 | 71.3 | 70.0 | 39.2 | 8.8→8.8 | 28.5→27.3 | 2 | 13 | orchestrator | 21.0 |
| P1-core-5 | 119.9 | 73.5 | 39.2 | 4.8→4.7 | 23.8→23.8 | 0 | 12 | orchestrator | 21.4 |
| P1-core-6 | 261.8 | 105.4 | 39.2 | 5.0→4.9 | 28.6→28.5 | 2 | 14 | subagent | 7.6 |
| P1-full-4 | 141.0 | 116.2 | 39.2 | 7.4→5.3 | 61.0→59.9 | 4 | 12 | orchestrator | 50.4 |
| P1-full-6 | 221.1 | 78.5 | 39.2 | 5.9→5.3 | 148.0→25.4 | 8 | 21 | subagent | 37.4 |
| P2-core-4 | 81.9 | 81.7 | 33.3 | 6.7→6.7 | 25.3→25.2 | 1 | 20 | subagent | 0.6 |
| P2-core-5 | 63.3 | 58.4 | 33.3 | 4.8→4.8 | 20.0→15.4 | 3 | 13 | subagent | 1.7 |
| P2-core-6 | 99.4 | 97.3 | 33.3 | 4.5→4.5 | 28.8→26.7 | 2 | 13 | orchestrator | 29.5 |
| P2-full-4 | 98.3 | 75.3 | 33.3 | 13.0→8.1 | 48.5→30.6 | 4 | 16 | orchestrator | 37.5 |
| P2-full-5 | 123.5 | 89.3 | 33.3 | 6.4→5.9 | 43.0→18.4 | 3 | 19 | subagent | 0.7 |
| P2-full-6 | 128.2 | 111.6 | 33.3 | 6.2→5.9 | 68.4→52.4 | 1 | 22 | subagent | 4.7 |

The rules step in at these points:

- **Bounded commands:** P1 core-5 E1 polled a one-hour stream for 57 min (−46). P1 core-6 E1 polled two `--duration 3600` streams (−95).
- **Waits:** P1 core-6 sat in ScheduleWakeup for 61 min after its hard stop (−61).
- **Dispatch budget, hard stop at the 3rd dispatch:**
  - P1 full-6: R2 ×8 (−136)
  - P1 full-4: R2 ×4 (−22)
  - P2 full-4: R2 ×4 (−16)
  - P2 core-5: R2 ×3 (−4)
  - P2 full-5: a third fix agent (−33)
  - P2 full-6: a third fix agent (−16)
- **Parallel P round:** P2 full-4 ran P4 before P6 and P7 and then a second P4 (−4.9). P1 full-4 saved −2.1.
- **Document lock:** blocks did ≤1.1 min of work after their document. It is not in the totals.

Total: 1410 → 957 min across the 11 runs. The mean goes from 128 to 87 min, the median from 120 to 82.

**The SLO is not met.** After the changes, the shortest run is 58 min against an SLO of 33 to 39. What is left is E1 (34–49 min once its waits are out, more than the whole one-shot), plus R1 (~8), two R2 runs (~4 each), one fix round and A5+P (~7). The owner's run shape puts these blocks one after another. That is a decision for the owner, not something this PR can change.

## Run-shape violations in the stored runs

- R2 ran up to 8 times in one run (shape: one code review).
- Five runs dispatched fix rounds as free-form prompts (P2 full-5 had 3), which no hook counted.
- The R3 gate ran 12–22 times per run.
- Five runs ran E1 on the orchestrator (21–50 min of build and test runs on the orchestrator).
- P2 full-4 ran two P4 updates, and its review round ran in sequence instead of in parallel.

## Coordination

The enforcement-gate branch (`r1-deterministic`/`fix/enforcement-gate`) works in `clean_checkout.py`, `gate_common.py` and `scripts/entry_observer/`. This branch does not change those files. The supervisor allows a gate's own project commands: they run inside the gate script.

## Test plan
- [x] `tests/gates/test_check_cache.py`: same tree reused, every change runs again, timeout not stored, no repo, ledger_verify runs a shared check once
- [x] `tests/hooks/test_supervisor.py`: command classes; bounded commands; orchestrator rules; R2 dispatch budget and hard stop; denied calls not counted; R3 tree budget; closed run; shadow and off; config; dispatch order; document lock; minutes, repeat, idle and tokens; budgets in stages.json
- [x] `tests/session/test_code_review_round.py`
- [x] `scripts/ci_local.sh` at `a012132`: Python 3.11 4466 passed, 2 skipped; Python 3.13 4466 passed, 2 skipped; complexity job OK; `ci_local: all CI steps passed at a012132`

## Update 2 (coordinator redirects)

**Moves on.** At a budget, the hook now writes `block_stops[<block>]` (`"gate": "FAIL"`) and tells the orchestrator to continue. It no longer ends the run. `headless.walk` skips a stopped block whose gate fails, and lists it under `stopped`. `closure.py` prints a `STOPPED` line, and `--deactivate` lists the stops. The gate verdict is still FAIL.

**R phase.** R2, R3 and R5 form the `code-review` round after R1. R5 checks the tree again after the fix round.

**Why E1 takes 34–49 min when the one-shot takes 27–31.** Comparison: the six E1 subagents against the Oct 23 Haiku P1 one-shot transcript (39 min, 80 calls, 10.4 min of model time, no tests run).

| Source of time in E1 | Cost |
|---|---|
| TDD test runs (11–42 per E1) | 3–13 min (the one-shot ran 0) |
| Stream runs (13–27 calls) | 4–17 min (one-shot: 2.9) |
| Nested deslop/simplify subagents | 1.5–5.5 min |
| More model turns (110–144 against 80) | 14–20 min of model time against 10.4 |

**Fixes in this push:**
- Deslop runs only when E2 is on. E2 is off in both shapes, so this saves 1.5–3.3 min in 5 runs.
- E1 writes its document last and then stops.
- A runner command on an unchanged tree is denied with its stored result. This saves ≈0 min on the stored runs, because they never repeated a runner on an unchanged tree.

**Projection** (replay; "move on" adds the stored median closure segment of 4.5 min where a block stops):

| Run | Before | v1 | v2 (this push) | SLO | v2 ÷ one-shot |
|---|---|---|---|---|---|
| P1-core-4 | 71.3 | 70.0 | 70.0 | 39.2 | 2.23× |
| P1-core-5 | 119.9 | 73.5 | 73.5 | 39.2 | 2.34× |
| P1-core-6 | 261.8 | 105.4 | 102.6 | 39.2 | 3.27× |
| P1-full-4 | 141.0 | 116.2 | 120.7 | 39.2 | 3.85× |
| P1-full-6 | 221.1 | 78.5 | 81.5 | 39.2 | 2.6× |
| P2-core-4 | 81.9 | 81.7 | 79.1 | 33.3 | 2.97× |
| P2-core-5 | 63.3 | 58.4 | 59.6 | 33.3 | 2.24× |
| P2-core-6 | 99.4 | 97.3 | 97.3 | 33.3 | 3.65× |
| P2-full-4 | 98.3 | 75.3 | 79.8 | 33.3 | 3.0× |
| P2-full-5 | 123.5 | 89.3 | 91.7 | 33.3 | 3.44× |
| P2-full-6 | 128.2 | 111.6 | 116.1 | 33.3 | 4.36× |

Mean 88.4 min, median 81.5 min.

**What blocks the SLO.** The blockers are owner-set constraints, measured at stored p50 block times.
- The one-code-review shape is sequential: R1 7.9 → R2 4.4 (R3 and R5 run beside it) → fix round 6.5 → R2 recheck 4.4. That is 23.2 min.
- The plan round P1 → P3 → P4 takes 5.5 min.
- A5 is in core: 1.9 min.
- E4, R5 and R7 together take 3.0 min.

The non-E1 blocks total 33.6 min, and orchestrator turns between blocks add ≈5 min. That is ≈39 min before E1 starts, the same as the P1 SLO (39.2 min) and more than the P2 SLO (33.3 min). E1 under the owner's TDD code standard runs at or above the one-shot's whole time (27–31 min). So 1.25× cannot be reached without changing the shape or the TDD standard (for example, R1 in parallel with R2/R3, or no recheck after the fix round). The floor within the shape is about 2× the one-shot.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01QAzPEbn3jrqAw3J58oC4VA
