# Pipeline family: Haiku 5.5 with a harness (2026-10-17)

The question: does a harness lift the cheapest model on the hardest public tasks? On the pipeline
family (P1 to P3), the Haiku 5.5 one-shot scored 0 of 7 checks on all three tasks
([pipeline trials](2026-10-15-pipeline-trials.md)). Sonnet 5.5 scored 3, 3 and 5; Opus 5.5 scored
6 (provisional), 5 and 3. No harness arm had run on these tasks.

## Run set (recorded before the first run)

| Order | Arm | Implementer | Other agents | Plugin |
|---|---|---|---|---|
| 1 | Review loop, Opus reviewer | Haiku 5.5 | reviewer: Opus | [`harnesses/reviewloop`](../../harnesses/reviewloop) |
| 2 | Review loop, Sonnet reviewer | Haiku 5.5 | reviewer: Sonnet | [`harnesses/reviewloop-sonnet-reviewer`](../../harnesses/reviewloop-sonnet-reviewer) |
| 3 | Verification loop | Haiku 5.5 | contract writer: Opus | [`harnesses/verifyloop`](../../harnesses/verifyloop) |

- Tasks: P1, P2, P3, k = 1 per cell (9 trials). Same runner, images, prompts, grader and caps as the
  one-shot trials, so the cells compare directly.
- Grading: the rule of the one-shot trials holds. The grader is not changed after it sees an arm's
  output, and the open readings of TASK-81 apply to every arm alike.
- Time: harness arms have no per-trial cap (owner decision, 2026-10-12). The runner gets
  `--agent-timeout 86400` (24 h) as a backstop only; each trial records the value it ran with.
- Budget for the run set: **$60** at `pricing.json` list prices. The run set stops scheduling new
  trials when the spend reaches the budget, and never stops a trial in progress.
- Haiku 5.5 costs use the base price tier, so they are lower bounds for requests above 100 K tokens
  (see [next steps](../next-steps.md#cost-accounting-price-each-request-at-its-own-tier-planned-2026-10-16)).
- Host: at most two `py`-image trials (P1, P2) at once, and P3 (the Spark image) alone, because the
  16 GB host lost earlier runs to Docker failures.

## Incident: Docker crash under parallel load (2026-10-17)

The run set started as planned (two `py` trials at 08:44 local). At the owner's request to run as much in
parallel as possible, three more trials started at 08:59: P3 and the two Sonnet-reviewer trials, five at
once. At 09:00:50 local (13:00:50Z) the Docker Desktop VM went from `running` to `stopping`
(`com.docker.backend.engines`, with a crash-detector entry) and did not come back; `docker desktop restart`
then failed. All five trials were lost in their agent phase. Their folders hold only `runner.log`, and
they are set aside under `results/runs/pipeline/void-2026-10-17-docker-crash/`. They are not results and
do not count as model failures.

Lesson for this host (16 GB, Docker VM 15.6 GB, other stacks running): five pipeline trials at once,
one of them Spark, crashed the VM. The plan's limit (two `py` trials, P3 alone) stays the limit.

## Run set, revised before the next trial (owner, 2026-10-17)

The owner's priority is Cadence itself on Haiku. Two Cadence arms go first, in the pilot's form
(`docs/experiments/2026-10-13-pilot/run_arm.sh`): a copy of Cadence main loaded with `--plugin-dir`,
`peer_models` set in its `cadence.config.json`, and the task prompt started with `/cadence:cadence`
plus the pilot's note that there is no GitHub and nobody answers questions.

| Order | Arm | peer_models | Cadence |
|---|---|---|---|
| 1 | Cadence, all Haiku | `{"default": "haiku"}` | jtouley/cadence main at the trial start (sha in `trial.json`) |
| 2 | Cadence, Haiku with Opus reviews | Haiku default; plan-review, adversarial-review, test-benchmark-plan, pr-review-local, test-benchmark-pr on Opus | same |
| 3 to 5 | the three arms above | | |

The two review-loop trials that had restarted at 11:44 were stopped at the owner's request to run
Cadence first; they are set aside under `void-2026-10-17-preempted/` and are not results. The budget
rises to **$90** for the 15 trials, recorded here before the first Cadence trial.

## Cadence config v2: a fake offline ticket (owner, 2026-10-17, before the v2 trials)

Config v1 (the pilot's form above) loaded Cadence and activated it in both first trials, but the A4 ticket
gate cannot pass in the container: the adapter is `github-issues`, which needs a `#N` on the branch or task
id, and the trial has no tracker. The pilot had no ticket either and recorded A4 as `TICKET_SKIPPED`
(cadence#65). Under v1, `P2-haiku-cadence-haiku-1` stopped at A4 with a `credentials` hard stop after 916 s
(no code, reward 0), and `P1-haiku-cadence-haiku-1` left the gated flow after A4 and wrote the pipeline
without spec, plan or reviews. Both are harness-configuration effects, not model results:

- `P2-haiku-cadence-haiku-1` is void, and `P1-haiku-cadence-haiku-opus-1` (stopped one minute into its agent
  phase so that it would not run under v1) is void too. Both are under
  `results/runs/pipeline/void-2026-10-17-cadence-config-v1/`.
- `P1-haiku-cadence-haiku-1` ran to the end under v1. It is reported apart, labeled config v1, and never
  mixed with v2 rows.

**Config v2: fake offline ticket #1.** The adapter stays `github-issues` as in the pilot. Each Cadence trial
starts on the branch `feat/gh-1-pipeline` (same commit as `main`), which A4 reads (`gh-1` gives task `cd-1`
and ticket `#1`). The prompt also says `Ticket: #1 (offline test ticket; the tracker is not reachable, so do
not look it up)`. `trial.json` records `cadence_config: v2`, the ticket and the branch. Check before the v2
trials: in the `py` image with `--network none`, A1 (activation, task `cd-1`), A2, A3 and A4 passed, and
`headless.py next` named A5. No Cadence step looks the ticket up; only the PR steps (E4) call `gh`, and the
environment note says to skip them. This differs from the pilot, which had no ticket.

The v2 trials (out dirs `*-v2`) run cadence-haiku and then cadence-haiku-opus on P1 to P3, under the same
parallel limits, before the three other arms.

## Cadence config v3: gate the task's code paths (2026-10-17, before the v3 trials)

A postmortem of the void v1 P1 run found that Cadence holds code writes until the execution entry invariant
(P9) only under its gated prefixes (`src/ lib/ app/ packages/`). The pipeline tasks keep their code in
`pipeline/`, `transform/`, `Makefile` and `oracle_map.yml`, so the write gate let every code write through
(52 writes in that run, 0 denials). v2 fixes A4 but not this.

**Config v3 = v2 plus a `.cadence.json`** in the trial repo root, committed on `feat/gh-1-pipeline` as one
commit: `{"gated_prefixes_extra": ["pipeline/", "transform/", "Makefile", "oracle_map.yml"]}`. Check before
the v3 trials, in the `py` image with `--network none` at Cadence 0786330: after A1 to A4 passed, a PreToolUse
`Write` to `pipeline/batch.py`, `transform/models/x.sql`, `Makefile` and `oracle_map.yml` was denied
(`gated path ... requires entry invariant`), and `README.md` was allowed. The same replay is a test
(`tests/test_pipeline_trials.py`). `trial.json` records `cadence_config: v3` and the prefixes.

Which trials ran under which config: P1 and P2 cadence-haiku ran under v2 (started before v3), and their out
dirs end in `-v2`. P3 cadence-haiku and all three cadence-haiku-opus trials run under v3 (`-v3`).

**Counting rule for v2 and v3 (owner, 2026-10-17).** A Cadence trial counts as a Cadence result only if the
entry-invariant marker (`.context/gates/entry-invariant-<run_id>.ok`) existed before the first code write
outside `.context/` (the marker's time against the transcript's first Write, Edit or shell write). Otherwise
it is labeled "Cadence loaded, gates bypassed (prefix gap)" and reported apart.

## Results

**Stopped at 13:13 local: the API account ran out of credit.** At 17:13:16Z to 17:13:17Z the two running
trials ended with `Credit balance is too low` (Claude Code `api_error`). The next trial (P3 cadence-haiku) then
failed on its first request, and scheduling stopped. Only one trial is a counted result. This section lists only
finished, counted trials. Every row is in
`2026-10-17-haiku-harness-pipeline.json`, and the void trials are there with `counted: false`. Cost is computed
from token counts at `pricing.json` list prices. Haiku 5.5 is priced at its base tier, so above 100 K tokens per
request the cost is a lower bound.

### Cadence, all Haiku (cadence-haiku)

| Task | Config | Checks | Reward | Cost | Agent s | Turns | Last stage reached | Stop reason |
|---|---|---|---|---|---|---|---|---|
| P1 | v2 (Cadence 13342c8) | 0/7 | 0.0 | $0.457 | 1,893.0 | 62 | P9 entry invariant not passed. A1 to A5, P1, P3, P4 and P6 passed; P7 (test benchmark of the plan) failed | Hard stop (`retries`) before any code; see below |
| P2 | v2 | lost (API credit) | | | | | E1 (implementation) | Set aside |
| P3 | v3 | lost (API credit) | | | | | none | Set aside |

**P1 (v2).** Cadence ran in the paceline: a spec, a vibe-test, a plan, plan reviews and an adversarial review.
It stopped at the entry invariant (P9) and wrote no code, so the grader found no pipeline (no stream
consumed, not idempotent, 0 of 7). Marker check: the run wrote no code outside `.context/`, so no write came
before the entry invariant. This counts as a Cadence result. Two things held P9 shut:

1. **The plan-review count disagreed.** The cycle-1 plan-update peer ran the plan-review skill itself four
   times in its own context (cycles 2 to 5), and the review file ended at "cycle 5 of 5". The gate counted 2 attested
   cycles, so it asked for another review, and the next review peer refused because the file said the limit
   was reached. Filed as jtouley/cadence#144.
2. **P7 failed.** The test benchmark of the plan returned FAIL with 7 must-fix findings (known-answer checks,
   exact decimal money, the Connecticut and unknown-geography rules, late rows, stream exit rules,
   malformed events, crash injection points). The plan-update peer applied none of them.

The orchestrator then recorded a `retries` hard stop with these two reasons. It did not edit the count to force
a pass.

### Cadence, Haiku with Opus reviews (cadence-haiku-opus)

| Task | Config | Checks | Reward | Cost | Agent s | Last stage reached | Stop reason |
|---|---|---|---|---|---|---|---|
| P1 | v3 | lost (API credit) | | | | P3/P4 plan-review loop | Set aside |
| P2 | v3 | not run | | | | | |
| P3 | v3 | not run | | | | | |

The review loop, Sonnet-reviewer and verification-loop arms did not run.

### Set aside (not results)

| Run | Config | Why |
|---|---|---|
| P2-haiku-cadence-haiku-1 | v1 | Hard stop at A4 (`credentials`, no ticket) after 916 s, no code |
| P1-haiku-cadence-haiku-1 | v1 | A4 failed; it wrote the pipeline outside the paceline (no spec, plan or review), then hit the stop guard 3 times at A4, and the guard let the stop through at its refusal cap. Graded 2/7, reward 0. Kept for the postmortem, not a result |
| P1-haiku-cadence-haiku-opus-1 | v1 | Stopped 1 min into its agent phase so that it would not run under v1 |
| P2-haiku-cadence-haiku-1-v2 | v2 | API credit ran out at 17:13:17Z, after 3,432 s, in E1. It was a valid Cadence run up to then: the entry-invariant marker was written at 16:56:10Z, and its first code write (`pyproject.toml`) came at 16:57:00Z. 26 tests passed and a stream smoke run was done, but no `oracle_map.yml` existed yet. $0.744 |
| P1-haiku-cadence-haiku-opus-1-v3 | v3 | API credit ran out at 17:13:16Z, after 1,963 s, still in the plan-review loop (A1 to A5 passed). No code written. $2.943 (Opus reviews) |
| P3-haiku-cadence-haiku-1-v3 | v3 | API credit ran out before its first request (3 s), $0 |

The three credit-loss trials are under `results/runs/pipeline/void-2026-10-17-credit-exhausted/`. The runner now
classifies `Credit balance is too low` as an API stall (`api_stall`, not a model failure), so a future run
cannot count such a session as graded.

Spend from token counts: $0.457 counted, plus $4.244 on the trials set aside ($0.557 under v1, $3.687 lost to
the credit stop). Total $4.70 of the $90 budget. The budget did not stop the run set; the API account did.

### Comparison with the one-shot trials

The one-shot rows of [pipeline trials](2026-10-15-pipeline-trials.md) are: Haiku 0/7 on P1, P2 and P3; Sonnet 3, 3
and 5; Opus 6 (provisional), 5 and 3. The one counted cell, P1 cadence-haiku, matches the Haiku one-shot (0/7), for a different reason. The one-shot delivered a pipeline that answered against the spec. Cadence delivered no
pipeline, because its own gates held implementation.

No other cell can be compared yet. The lost P2 run was the closest to a delivered Cadence pipeline: it passed the
entry invariant and was implementing with passing tests when the credit ran out.

### Limits

Only 1 of 15 planned cells has a result. k = 1 per cell. Haiku costs are lower bounds above 100 K tokens per request. Cadence configs v1, v2 and v3 differ
(see above), and each row names its config.

