# Claims register

Every claim this repository makes, how strong its evidence is, and when it should be checked again.
If a sentence anywhere else in the repository goes further than its row here, the row wins.

*Disclosure: the owner of this benchmark wrote Cadence.*

## Evidence levels

- **Reproducible.** Anyone can recompute it from this repository and get the same bytes.
- **Exploratory.** It was measured, and the data is here, but the sample is small (often one run per
  cell) or the method was not pre-registered. Treat it as a direction, not a result.
- **Operator-reported.** The owner measured it on inputs that are not public. You can read the method
  and the counts, but you cannot check them.
- **Not run.** It was designed and not yet measured.

How each number is produced, and which ones rest on a model's judgment: [how results are graded](method/grading.md).

Last reviewed: 18 October 2026.

## Reproducible

| Claim | How it was checked | Evidence | Check again when |
|---|---|---|---|
| Only Cadence's hooks block a forged approval, a self-certified verdict, an edit before plan approval and a stop mid-run (7 of 9 probes; GSD Core next, 4 of 9). | Replayed agent actions through each harness's real hooks. Cadence is private, so only people with access can reproduce its row. | [Probe results](../results/probes.json), [report](../results/REPORT.md) | Any harness pin changes in the lockfile |
| GSD Core blocks reading `.env` and overwriting the plan; Cadence does not. | Same probes. | [Probe results](../results/probes.json) | Any harness pin changes |
| Loading any harness's whole workflow costs cents per session. | Token counts of the installed files, with a pinned proxy tokenizer, at list prices. | [Footprint results](../results/footprint.json), [pricing](../pricing.json) | A pin or a price changes |
| Every harness installs identically twice from its pinned commit. | Install twice, compare normalized tree hashes. CI checks this on every push for the public harnesses. | [Install results](../results/install.json), [CI workflow](../.github/workflows/verify.yml) | Every push (automatic) |

## Exploratory

| Claim | Sample and date | Evidence | Check again when |
|---|---|---|---|
| On small, fully specified tasks, a harness did not write better code than Opus 5.5 alone (8.00 against 7.33 for Cadence, out of 10). | 3 tasks, 1 run per cell, 1 blind grader; 12 October. Not a clean room. | [Iteration 4](evidence/2026-10-12-iteration-4.md) | A rerun with 5 runs per cell and 2 graders |
| Neither harness shipped a crash in the code it delivered (ship-feature delivered 2 of 3 tasks); each one-shot shipped two, all on one task. | Same round. | [Defect records](evidence/2026-10-12-iteration-4/defects.json) | Same |
| The harness took about 30 times the wall time of a one-shot. | Same round. | [Iteration 4 results](evidence/2026-10-12-iteration-4/results.json) | Same |
| Full Cadence orchestrated by Haiku 5.5 delivered nothing on a task the Opus one-shot finished in 111 seconds. | 1 task, 1 run per arm; 13 October. Clean room. | [Pilot](evidence/2026-10-13-pilot.md) | After the Cadence defects it surfaced are fixed |
| On 20 SWE-bench Pro tasks, Haiku 5.5 passed 17 and Opus 5.5 passed 18, at about a tenth of the cost. | 20 tasks, 1 try per model; 14 October. Cost is a lower bound. | [Results per task](../calibration/swebench-pro/round2.md) | A repeat with several tries per task |
| Harbor runs SlopCodeBench's grading end to end with no model: its reference solution passes every core test at all 6 checkpoints of `cfgpipe`, and its own erosion (0.782) and verbosity (0.556) are worse than the paper's average agent. | 1 task, reference solution only; 18 October. | [Smoke check](evidence/2026-10-18-smoke-check.md) | When a model runs on it |
| On the long pipeline tasks, the best one-shot scored 6 of 7 checks (Opus on P1); Haiku scored 0 of 7 on all three. | 3 tasks, 1 run per model; 15 October. Some checks have open readings. | [Pipeline trials](evidence/2026-10-15-pipeline-trials.md) | When the open readings are settled, or a harness runs on them |
| With the ten-block core of Cadence, Haiku 5.5 delivered P1 with 5 of 7 checks at $0.67 (a lower bound), where Haiku alone delivered 0 of 7. The run reached no review stage. A P1 rerun stopped at the entry gate on a Cadence gate defect, 0 of 7. A third P1 run went through every block, with five review rounds, and scored 0 of 7: its answers stayed unpublished in the warehouse. The P2 run was cut off by a host guard and is not scored. | 2 tasks, 4 runs, 3 scored; 19 October. On a host, not in the isolated runner. | [Pipeline, first harness arm](evidence/2026-10-19-pipeline-cadence-core.md) | A rerun in the isolated runner with n = 3 |

## Operator-reported

| Claim | Sample and date | Why you cannot check it | Check again when |
|---|---|---|---|
| On a real two-cause bug, a review loop with Opus 5.5 as reviewer fixed both causes in 3 of 3 cheap-model runs, against 1 of 10 cheap runs without it (Fisher exact, p ≈ 0.014). Opus alone fixed both in 10 of 10, at about the same cost. | 20 runs alone, 3 with review; 13–14 October. | Third-party task: code, grader and transcripts are private ([whitepaper 3.3](whitepaper.md#33-a-real-multi-cause-bug-b01-a-lift-task)). | A public task with the same shape |
| Cheap models miss by narrowing scope and skipping coverage, not by shallow reasoning. | Transcripts of the same 20 one-shots. | Same private task ([whitepaper §3.4](whitepaper.md#34-why-the-cheap-models-miss)). | Same |
| In PR reviews, the first review round found most confirmed defects (40 of 51). | Cadence's own review records. | Records are private; the counting script is public ([review value](evidence/review-value.md)). | If the records are published |
| Cadence's reviews caught 85 must-fix findings before merge while building Cadence, 73% at plan time. | 10 merged runs, 10–17 October. | Records are private; the cited pull requests are public ([self-evidence](evidence/2026-10-17-cadence-self-evidence.md)). | If the records are published |

## Not run

| Claim it would test | Design | Status |
|---|---|---|
| Which setup gives the lowest cost per solved task, across all seven. | 240 trials under pre-registered criteria ([live tier](method/live-tier.md)) | Built and checked in CI; never run |
| A cheap verification harness (contracts before code, a stop gate) lets a cheap model match Opus. | [Next steps](plans/next-steps.md), [verification harness](../harnesses/verifyloop/) | Built; not run |
| Harnesses do better on accepted benchmarks graded only by code: correctness, quality under change, a tool gate. | [Grade with accepted benchmarks](plans/accepted-benchmarks.md) | Proposed |
| A harness makes a failed long task easier to trace to its cause. | [Pipeline family](plans/tasks/pipeline-family.md), seeded traps and a blind auditor | Tasks built; no harness has run on them |
