# Pipeline family: cadence-core on Haiku 5.5, run on a subscription (21–22 October 2026)

Status: exploratory. Six counted runs (P1 and P2, three each) and two infrastructure losses, run on a
host, not in the isolated runner. Data: [`2026-10-21-pipeline-cadence-core-subscription/`](2026-10-21-pipeline-cadence-core-subscription/).
The one-shot rows it is compared with are from [the 15 October trials](2026-10-15-pipeline-trials.md); the
earlier cadence-core round is on branch `ccr-3d2e0c73-lr6bdt`
([write-up](https://github.com/jtouley/harness-benchmark/blob/d4f9b00/docs/evidence/2026-10-19-pipeline-cadence-core.md),
[postmortem](2026-10-19-cadence-core-postmortem.md)).

*Disclosure: the owner of this benchmark wrote Cadence.*

## Question

The 19 October round's next step: rerun P1 and P2 at n = 3 with no time cap on the harness arm, on a
current Cadence. Here that is the public `jtouley/cadence-core` at `29315c4` (the commit measured in
[tiers 1 and 2](2026-10-21-cadence-core-tiers-1-2.md)), with Haiku 5.5 as orchestrator and every peer.
On 15 October, Haiku 5.5 alone scored 0 of 7 on P1 and P2; Opus 5.5 alone 6 of 7 (provisional) and 5 of 7.

## Setup

- **Host, not the isolated runner.** The machine is a cloud container (4 CPUs, 15 GB, x86-64 Linux)
  with no Docker daemon, so P3 could not run. The method is the 19 October host method, in a script kept
  with the data ([`host_trial.sh`](2026-10-21-pipeline-cadence-core-subscription/host_trial.sh),
  [`queue.sh`](2026-10-21-pipeline-cadence-core-subscription/queue.sh)): the starting repository from
  `pipetask.assemble` on branch `feature/gh-1-pipeline` with a local bare origin; a clean, empty `HOME`;
  the dev replay (seed 0) on `localhost:8099` during the session; then the grader (`pipetask.trial
  --snapshot-worktree --deadline 600`, seed 1). The host graded the P1 reference at 7 of 7 in 164 s.
- **Auth: the operator's Claude subscription, not an API key.** The runner takes only
  `ANTHROPIC_API_KEY`, which is why these runs are on the host.
- **Arm.** cadence-core `29315c4` loaded with `--plugin-dir`. Config: `adapter: none`,
  `peer_models: {"default": "haiku"}`, and a committed `.cadence.json` that adds `pipeline/`, `engine/`,
  `pipelines/`, `transform/` and the `Makefile` to the gated prefixes. Headless variables from Cadence's
  quickstart (`CLAUDE_AUTO_BACKGROUND_TASKS=false`, `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`).
  Claude Code 2.1.306, `claude -p`, permission mode `auto`.
- **Prompt.** The 19 October prompt, word for word in form: the lockfile's `cadence-core` drive prompt
  around the task prompt, plus the same environment note (no GitHub, PR text to `outputs/PR.md`, nobody
  answers, task id gh-1). It carries the same prompt-hygiene limits that round lists (#56).
- **No time cap.** Only the harness backstop, the `runner/pipeline/caps.json` default of 86,400 s and
  no dollar cap (criteria v2 §5.3). No run came near it.

## Results

| Run | Task | Ended at | How it ended | Phase commits | Reward | Agent min | Cost (list) | Claude Code's cost |
|---|---|---|---|---|---|---|---|---|
| P1-cadence-core-haiku-1 | P1 | P4 | stopped to ask: P4 refused four times | 0 | 0.0 (0/7) | 9.6 | $0.11 | $0.12 |
| P1-cadence-core-haiku-2 | P1 | P4 | `retries` hard stop: P4 drops the plan's provenance marker | 0 | 0.0 (0/7) | 20.6 | $0.24 | $0.25 |
| P1-cadence-core-haiku-3 | P1 | E4 | `credentials` hard stop: no GitHub PR URL | 7 | 0.0 (0/7) | 51.6 | $0.55 | $1.71 |
| P2-cadence-core-haiku-1 | P2 | P7 | `retries` hard stop: P7 failed three times | 0 | 0.0 (0/7) | 42.7 | $0.57 | $0.59 |
| P2-cadence-core-haiku-2 | P2 | E4 | `credentials` hard stop: no GitHub PR URL | 11 | 0.0 (0/7) | 64.4 | $0.68 | $2.48 |
| P2-cadence-core-haiku-3 | P2 | P7 (replan) | `retries` hard stop: P7 failed three times after a replan from E1 | 1 | 0.0 (0/7) | 81.3 | $1.09 | $1.54 |
| P1-cadence-core-haiku-0-killed | P1 | E1 | infrastructure loss: container reclaimed | 4 | not scored | ~103 | not recorded | — |
| P2-cadence-core-haiku-2a-killed | P2 | E1 | infrastructure loss: worker restarted | 8 | not scored | ~43 | not recorded | — |

Rows from `scripts/pipeline_trial.py summary` ([rows.md](2026-10-21-pipeline-cadence-core-subscription/rows.md),
[rows.json](2026-10-21-pipeline-cadence-core-subscription/rows.json)). "Cost (list)" is from token
counts at `pricing.json` prices, as in the other rounds, and is a lower bound for Haiku (#51). Claude
Code's own figure is kept for the record; it is 1.0 to 3.6 times the list figure. Every session ended on
its own, with exit 0; no run hit the backstop.

For comparison, the 15 October one-shots (isolated runner, k = 1):

| Task | Haiku 5.5 | Sonnet 5.5 | Opus 5.5 |
|---|---|---|---|
| P1 | 0/7, $0.30 | 3/7, $2.06 | 6/7 (provisional), $5.82 |
| P2 | 0/7, $0.28 | 3/7, $4.56 | 5/7, $7.84 |

**No counted run delivered an answer.** Four of six stopped in planning and never wrote code. The two
that built a working pipeline (both `make build` runs and both `make stream` runs exit 0, nothing
changed by the second build, the grading replay read to the end) stopped at E4 and scored 0 of 7 on
their answer maps. The 19 October round's best Haiku run (P1, 5 of 7, on Cadence `b1bbdcd`) is not
reproduced here.

### Why each run ended

1. **P1-1: a plan review that the gates could not count.** The P3 peer wrote its review to
   `.context/plans/cd-1.plan-review.md`, not `.context/reviews/plan_cd-1.plan.md`. The orchestrator had
   the same peer rewrite it at the right path, then add the run id; the P4 handoff hook still refused
   ("no plan review of the run with a verdict"), four times. Then the P9 entry invariant **passed**,
   with the plan's only review blocking and never counted. The orchestrator would not build on an
   unreviewed plan, the stop guard kept sending it to E1, and it ended by asking a question nobody
   would answer. Not checked here: why the rewritten review did not count (the P3 accept rule requires
   the file to be written by a plan-review peer on a `verdict_join` run; a resumed peer's write may not
   be attested as such).
2. **P1-2: P4 drops a marker that every handoff needs.** Each P4 plan update rewrote the plan without
   `RUN_BY_COMMAND: plan-create`. From then on every peer handoff was refused ("no plan of the run …
   with RUN_BY_COMMAND: plan-create"). A fresh P1 restored it, the next P4 dropped it again, and the
   orchestrator recorded a `retries` hard stop.
3. **P2-1 and P2-3: P7 failed on its score average three times.** P2-1's last scorecard: mean 6.33
   against a floor of 7, verdict FAIL, with must-fix findings about the plan's own text (a revision
   ledger naming test files a later update renamed; a section not listing helpers an update said it
   would). The orchestrator could not read the scorecard (the orchestrator-scope guard, ADR-0017), so
   it could not tell the plan update what to fix. P2-3 passed planning once, committed E1 phase 1, found
   the plan's USAspending column names wrong, planned again from scratch (five P3 cycles, three P6
   rounds) and then failed P7 three times. Its final summary says nothing was committed; phase 1 was.
4. **P1-3 and P2-2: E4 cannot pass without GitHub.** At `29315c4`, `draft_pr_gate.py` requires a
   record with a `https://github.com/<owner>/<repo>/pull/<n>` URL; there is no local PR mode under
   `adapter: none` (the 19 October round added one to the old `jtouley/cadence` in `f734888`; it is
   not in cadence-core). So R1 to R7 cannot run in this benchmark's environment, and no delivered
   code was reviewed.

### Why the two built pipelines scored 0

- **P1-3** wrote an `oracle_map.yml` of seven self-invented invariants in prose
  (`raw_row_conservation`, `window_conservation`, …), not the seven checks the ticket lists. Every
  check fails to parse (`syntax error at or near "count"`).
- **P2-2** mapped each check to `query: tests/checks/check_0N.sql`, a file path the grader runs as SQL
  (`syntax error at or near "tests"`). The grader's contract reads `query` as SQL text, so this is an
  open reading and the grade stands (the 15 October rule); three of its entries also read `lake/`,
  which the spec rules out. Haiku's 15 October P3 one-shot failed the same way.
- **Both** published single-file marts (`out/marts/*.parquet`). The grader's run-twice check hashes
  only mart folders (`mart_digests`), so it found no marts, set `idempotent: false` and would have
  zeroed the reward on its own. This is #49, found in the postmortem and still on main.

The first two are the 19 October lesson again: nothing in the core traces the ticket's own requirement
list (here, the seven checks) to a delivered proof.

## Findings for this benchmark

1. **The runner cannot use a subscription.** `run_trial.sh` passes only `ANTHROPIC_API_KEY`. A
   subscription run has to use the host method, with no clean room. The driver used here is kept with
   the data.
2. **A nested `claude -p` inherits the operator's session.** Launched from inside a Claude Code
   session, the trial reported under the operator's session id until the driver dropped every `CLAUDE*`
   and `CCR_*` variable. Auth still works without them (through the environment's proxy).
3. **A cloud session is not a place for multi-hour trials.** The container was reclaimed once while
   idle (14:47 UTC, 103 minutes into P1-0) and its worker was restarted once while busy (23:40 UTC,
   43 minutes into P2-2a). Both killed every process; both runs are infrastructure losses under §5.3
   and were run again. Two of eight sessions lost.
4. **#49 decides grades now.** It zeroed both runs that built a pipeline. Until it is fixed, a
   delivered pipeline with single-file marts cannot score.
5. **No clean room, and it showed.** A peer's file search found a second copy of the arm at
   `/home/user/cadence-core` (the same commit, `29315c4`), and peers read its skill files from there.
   No session read anything under the benchmark's repository: no key, grader, reference or replay code
   (checked by path in every transcript).
6. **Cost columns.** `pipeline_trial.py summary` reads `modelUsage` from the last `result` line. In a
   headless session with background peers there is one `result` line per wake-up; their `usage` is
   per wake-up, but `modelUsage` is session-wide and matches the per-message sums in the transcript, so
   the rows above are right.

## Limits

- n = 3 per task on one arm, one model, on a host. Rates, not rankings.
- No clean room, no network isolation (the agent had the host's network during its session).
- The prompt has the 19 October hygiene problems (#56).
- Haiku costs are lower bounds (#51).
- Tool measures (`quality_metrics.py`, `commit_replay.py`) were not run on the two built pipelines.
- Transcripts are not committed (5 to 9 MB each, with host paths); the run records, Cadence's
  `.context/` of each run, the outputs and the grades are.

## Next

- In cadence-core: a local PR record under `adapter: none`, so E4 and R1 to R7 can run without GitHub
  (two of two built pipelines stopped there).
- In cadence-core: P4 must keep the plan's provenance marker; the P9 entry invariant must not pass
  while the plan's review is blocking or uncounted; and an orchestrator that cannot read a P7 scorecard
  needs the gate to print the failing rows.
- In this benchmark: fix #49 before the next pipeline round; give the runner a subscription path or
  run on a Docker host with an API key.
