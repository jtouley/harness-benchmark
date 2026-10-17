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

## Results

Pending.
