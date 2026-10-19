# Evidence

Every experiment round so far, oldest first. None of them is a pre-registered result: each ran outside
the live tier, and most ran once per setup with one grader. Check the sample size before citing a number.
The [claims register](../claims.md) rates each claim, [how results are graded](../method/grading.md) says
what produced each number, and the [whitepaper](../whitepaper.md) draws them together.

*Disclosure: the owner of this benchmark wrote Cadence.*

## Iteration 3 (9–10 October): superseded

- Question: do two harnesses on Opus beat Sonnet and Haiku working alone, on three feature tasks?
- Sample: one run per setup, one blind grader.
- Result: the harnesses scored higher, but there was no Opus-alone run, so this shows that Opus beats
  Sonnet and Haiku, not that a harness helps. Iteration 4 replaced it.
- Read: [iteration 3 write-up](2026-10-10-harness-vs-oneshot.md), [iteration 3 data](2026-10-10-harness-vs-oneshot.json)

## Iteration 4 (11–12 October): exploratory

- Question: the same, with the missing Opus-alone run.
- Sample: three tasks, one run per setup, one blind grader. Not a clean room.
- Result: Opus alone scored 8.00, Cadence 7.33, so no quality gain was shown. The harnesses shipped no
  crashes; each model working alone shipped two.
- Read: [iteration 4 write-up](2026-10-12-iteration-4.md), [iteration 4 data](2026-10-12-iteration-4/)

## Pilot (13 October): exploratory

- Question: can Cadence run by the cheap Haiku 5.5 model deliver a feature?
- Sample: one task, one run per setup, clean room.
- Result: no. Both Cadence runs stopped in their own checks. Opus alone delivered in 111 seconds for $0.40.
- Read: [pilot write-up](2026-10-13-pilot.md), [pilot data](2026-10-13-pilot/)

## Multi-cause bug B01 (13–14 October): operator-reported

- Question: can an independent review lift cheap models on a real bug with two causes?
- Sample: 5 to 10 runs per model working alone; 1 to 2 runs per review setup. Regraded in isolation.
- Result: both causes fixed by Opus alone in 10 of 10, Sonnet 1 of 5, Haiku 0 of 5, and with an Opus
  review in 3 of 3. The task belongs to a third party, so only scores are published.
- Read: [whitepaper section 3.3](../whitepaper.md#33-a-real-multi-cause-bug-b01-a-lift-task)

## SWE-bench Pro sample (14 October): calibration

- Question: on a published benchmark, where is Opus working alone unreliable?
- Sample: 20 tasks, one try per model.
- Result: Opus 18, Sonnet 18, Haiku 17 of 20, with Haiku at about a tenth of the cost (a lower bound).
- Read: [calibration notes](../../calibration/README.md), [results per task](../../calibration/swebench-pro/round2.md)

## Pipeline tasks P1 to P3 (15 October): exploratory

- Question: how do models working alone do on long data-pipeline tasks?
- Sample: three tasks, one run per model, seven scripted checks each. Some checks have open readings.
- Result: best per task was Opus 6 of 7 on P1, Opus 5 of 7 on P2 and Sonnet 5 of 7 on P3. Haiku scored 0
  of 7 on all three. No harness has run on these tasks yet.
- Read: [pipeline trials write-up](2026-10-15-pipeline-trials.md), [pipeline trials data](2026-10-15-pipeline-trials.json)

## Cadence building Cadence (10–17 October): operator-reported

- Question: what did Cadence's reviews catch while it was used to build Cadence?
- Sample: 10 merged runs. Severity is the reviewer's own word.
- Result: 85 must-fix findings closed before merge, 73% of them at the planning stage. The records are
  private; only the cited public pull requests can be checked.
- Read: [self-evidence write-up](2026-10-17-cadence-self-evidence.md), and how review rounds are counted:
  [review value](review-value.md)

## Pipeline family, first harness arm (19 October): exploratory

- Question: does a harness let Haiku 5.5 deliver P1, which it did not deliver alone?
- Sample: one run per cell, on a host without the isolated runner (no clean room). The ten-block core
  of Cadence, Haiku 5.5 as orchestrator and every peer.
- Result: on P1, 5 of 7 checks at $0.67 list price, against 0 of 7 for Haiku alone and 6 of 7 for
  Opus alone ($5.82). The run stopped before its review stages because the environment has no PR. On
  P2, 1 of 7 at $0.65: the guard cap killed the run during a one-hour acceptance step, before the
  export step the grader reads. An Opus run died on a host defect (a peer started in the background),
  now fixed in the runner.
- Read: [write-up](2026-10-19-pipeline-cadence-core.md), [data](2026-10-19-pipeline-cadence-core/)

## Smoke check on Harbor (18 October): no model

- Question: does SlopCodeBench's and FeatureBench's grading run end to end, before money is spent?
- Sample: each benchmark's reference solution, one task each; no model.
- Result: SlopCodeBench grades with tests and a static analyzer, no model; its reference passes every
  core test, and scores worse on erosion and verbosity than the paper's average agent. FeatureBench
  needs more disk than the test machine had.
- Read: [smoke check](2026-10-18-smoke-check.md), with its grader and analyzer outputs

## Scripts kept with the data

The scripts beside each round's data (`grade.py`, `run_arm.sh` and others) are the exact ones used for that
round, kept unchanged except for file paths, so it can be regraded. Current tooling lives in [`cbench/`](../../cbench/),
[`scripts/`](../../scripts/) and [`runner/`](../../runner/).
