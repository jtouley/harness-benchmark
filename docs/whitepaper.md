# Harnesses against one-shotting: what a harness is for when the model is this good

*Whitepaper, version 1, 14 October 2026. Benchmark: jtouley/harness-benchmark.*

> **Disclosure.** The author of this benchmark wrote Cadence, one of the harnesses measured. The
> results below that do not favor Cadence are stated first, and every number links to its data.

## Abstract

We asked when a plan-to-PR harness is worth running instead of handing a task to one strong model.
Over four rounds of measurement, the answer moved twice.

1. **On small, fully specified tasks, a harness does not write better code.** Opus 5.5 alone scored
   8.00 of 10 against 7.33 for Cadence on Opus, in about 1/30 of the time (iteration 4, one run per
   cell). The harness did ship no crashes (each one-shot shipped two) and left an audit trail.
2. **A full harness does not make a cheap model work.** Cadence orchestrated by Haiku 5.5 delivered
   nothing on a task that the Opus one-shot finished in 111 seconds for $0.40 (pilot, one run per arm).
   The run stopped in its own planning loop, or failed its own gates.
3. **On a real multi-cause bug, the cheap models do most of the work and miss the rest, and an
   independent review recovers it.** Opus alone fixed both defects of a brownfield bug in 10 runs of 10.
   Haiku alone fixed the main path in 5 of 5 and the second defect in 0 of 5. Sonnet fixed it in 1 of 5.
   A minimal review loop (the cheap model works, an independent reviewer checks the running system) fixed
   both in all 3 valid runs, but at about the Opus one-shot's cost.
4. **Why the cheap models miss is specific and fixable.** Haiku saw the second defect in every run,
   diagnosed it correctly once, then decided to "leave that out of this change and report it" and never
   reported it. Sonnet mostly never exercised that path. The gap is scope judgment and coverage, not
   reasoning depth. Haiku took more turns than Opus.

Our current position: **a harness earns its cost by verification and by holding scope, not by
ceremony.** A planning pipeline on a weak model mostly adds places to stop. An independent check of the
running result, and a rule that no part of the request may be dropped silently, recover the cheap
model's misses. The open question is whether that check can itself be cheap. The next measures are
cost per defect-free run, traceability when a long task goes wrong, and design quality under a follow-up
change.

## 1. The question and why it matters

Models write code faster than people can check it. A one-shot from a strong model is often correct, and
when it is, it is fast and cheap. The case for a harness (a plan, independent reviews, gates, a record)
must rest on something a one-shot cannot give:

- **Evidence.** A record of what was planned, checked and decided, by agents that did not write the code.
- **Reliability over repeats.** A one-shot that passes once says nothing about the next run.
- **Cost.** Opus 5.5 costs 40 times Haiku 5.5 per token (for prompts up to 100K tokens). If a harness
  lets a cheap model reach the strong model's result, the extra tokens are cheap.

## 2. Method

- **Pre-registered criteria** ([criteria v1](criteria.md)): measures, sample size and a decision rule
  written before the runs.
- **A neutral one-shot baseline:** the same request, with the harness parts removed and nothing added.
- **A clean room** ([process](process.md#clean-room)): each run has an empty `HOME`, so user-level skills,
  rules and memory cannot prime or replace anything. A checker reads each transcript and must return
  `clean` before grading ([`clean_room_check.py`](../scripts/clean_room_check.py)).
- **A published quality model** ([quality model](quality-model.md)): ISO/IEC 25010 characteristics,
  measured by published tools and thresholds (coverage, cognitive and cyclomatic complexity, bug and
  type findings), blind defect review, and from now on duplication, coupling and a follow-up change.
- **Costs from token counts** at list prices ([`pricing.json`](../pricing.json)), because the host
  misprices models it does not know.
- **Task selection by calibration** ([next steps](next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13)).
  A task is chosen by what the bar does on it, not by how hard it looks:
  - a **lift task**: the Opus one-shot is reliable and the cheap one-shots are not. Can a harness lift a
    cheap model to the bar for less?
  - a **beyond task**: the Opus one-shot is unreliable. Can a harness raise reliability at all?

## 3. Results

### 3.1 Small, fully specified tasks (iteration 4)

Three feature tasks on a 300-line Python ledger (T04–T06), one run per cell, one blind grader
([iteration 4](experiments/2026-10-12-iteration-4.md), [findings](findings.md)).

| Arm | Delivered | Blind quality | Crashes shipped | Time per task |
|---|---|---|---|---|
| Opus 5.5 one-shot | 3 of 3 | 8.00 | 2 | 2 min |
| Cadence (Opus) | 3 of 3 | 7.33 | 0 | 63 min |
| Sonnet 5.5 one-shot | 3 of 3 | 7.08 | 2 | 2 min |
| Haiku 4.5 one-shot | 1 of 3 | 3.50 | 2 | 4 min |

No quality gain from the harness. What it did give: no crash in delivered code, an audit trail with
hash-attested reviews by separate agents, completion or a recorded stop, and hooks the model cannot skip.

### 3.2 Cadence on a cheap model (pilot)

T05 (budgets), clean room, Cadence loaded with `--plugin-dir`, one run per arm
([pilot](experiments/2026-10-13-pilot.md)).

| Arm | Result | Time | Cost |
|---|---|---|---|
| Opus 5.5 one-shot | Delivered; 7/7 hidden tests; quality gate passed | 111 s | $0.40 |
| Cadence, all Haiku 5.5 | Hard stop at P6 after four plan updates | 75 min | $1.13 |
| Cadence, Haiku 5.5 + Opus reviews | Hard stop at P9: no delegation records | 27 min | $3.19 |

The harness gave the cheap model more places to stop: a review loop with no cycle limit, and gates that
depend on the orchestrator recording its own delegations. Four Cadence defects were filed from this run
(cadence#63–#66).

### 3.3 A real multi-cause bug (B01, a lift task)

A private brownfield bug in a multi-service application. Several faults stack across services, and the
existing mocked tests hide some of them. The prompt is the original product request. The grader runs the real
stack and checks the product outcome: the main path, and a second entry point that the original
human-assisted fix also missed. The task's code is not published (it belongs to a third party); its
scores are.

| Arm | Main path fixed | Both defects fixed | Mean cost | Mean time |
|---|---|---|---|---|
| Opus 5.5 one-shot | 10/10 | 10/10 | $1.29 | 7.3 min |
| Sonnet 5.5 one-shot | 4/5 | 1/5 | $0.39 | 3.5 min |
| Haiku 5.5 one-shot | 5/5 | 0/5 | $0.11 | 8.6 min |
| Haiku 5.5 + Opus review loop | 2/2 | 2/2 | $1.15 | |
| Sonnet 5.5 + Opus review loop | 1/1 | 1/1 | $1.24 | |

All runs were regraded with an isolated grader after a contamination incident (§5); no grade changed.

**Reading.** The independent review closes the reliability gap, in 3 of 3 valid runs. It does not save
money. The reviewer must run and exercise the stack to check the work, and that costs about as much as
Opus doing the task.

### 3.4 Why the cheap models miss

From the transcripts of all 20 B01 one-shots:

| | Opus | Sonnet | Haiku |
|---|---|---|---|
| Turns per run (mean) | 90 | 42 | 166 |
| Tool calls per run (mean) | 41 | 22 | 64 |
| Runs that hit the second defect's error | 10 of 10 | 1 of 5 | 5 of 5 |
| Runs that fixed it | 10 of 10 | 1 of 5 | 0 of 5 |

- **Haiku did more work, not less.** It hit the error every time. In one run it named the cause correctly,
  then wrote that it would "leave that out of this change and report it". The final summary did not
  mention it. The failure is **scope narrowing plus a dropped commitment**.
- **Sonnet mostly never exercised the second entry point.** When it did, it fixed it. The failure is
  **coverage**.
- **Opus treated every broken entry point as part of the request.**

This points to two harness mechanisms that need no strong model:

1. **No silent deferral.** Every decision to leave work out goes to an independent reviewer at once, which
   judges it against the request; a rejected deferral is implemented before the run may finish
   (cadence#68).
2. **Contracts before code.** Write executable checks for every entry point the request covers before the
   implementation starts, and do not let the session end while one fails. This is the "harness-first"
   argument of Datadog's engineering team: verification, not review, is the bottleneck, and *"a weak
   harness cannot be compensated for by better models or more human review"*
   ([Datadog, harness-first agents](https://www.datadoghq.com/blog/ai/harness-first-agents/)).

### 3.5 A published benchmark: where the bar is unreliable

SWE-bench Pro (Harbor, Claude Code in each task's container), 20 Python tasks drawn at random
([calibration](../calibration/README.md)): the Opus 5.5 one-shot passed 17. Two tasks passed only 2 of 5
tries. Those are beyond candidates: a harness that raises their pass rate does something the strong model
alone cannot do reliably.

## 4. What this means for building a harness

| Holds up | Does not |
|---|---|
| Independent verification of the running result (it recovered every cheap-model miss in B01) | A long planning pipeline on a weak orchestrator (more places to stop) |
| An audit trail with attested authorship (it makes failures diagnosable in minutes) | Review by a strong model as the verification step, if the goal is cost |
| Enforcement the model cannot skip (gates, stop hooks) | Review as a stand-in for executable checks |
| Holding scope: a dropped part of the request is a defect | Deferral checks that look only at form (a ticket, a label) |

Cadence changes that follow: P6 gets a cycle limit (cadence#63); the delegation record is written by a
hook, not by the orchestrator (cadence#64); a no-tracker mode (cadence#65); a verdict counts only from the
peer of its stage (cadence#66); deferrals are judged in real time (cadence#68).

## 5. Threats to validity

- **Small samples.** Iteration 4 and the pilot are one run per cell. B01 has 5–10 runs per one-shot arm
  and 1–2 per review-loop arm. Only the largest gaps are outside noise.
- **Contamination incident.** The B01 runs ran agents on the host. Workers they started outlived their
  runs and shared a message broker with later runs and the grader. All runs were regraded with an isolated
  grader (a private broker database, stray processes killed); no grade changed. From now on each trial runs
  in its own container ([harness-benchmark#10](https://github.com/jtouley/harness-benchmark/issues/10)).
- **Infrastructure losses.** Emulated x86 containers crashed the test laptop's Docker three times; the
  affected trials are recorded as infrastructure errors, not failures, and were rerun.
- **One task per class so far.** B01 is one bug; SWE-bench Pro is one benchmark's sample of 20.
- **Author bias.** Mitigated by pre-registration, blind grading, and stating the unfavorable results first.

## 6. What comes next

1. **The pipeline family** ([tasks](tasks/pipeline-family.md)): one spec on three stacks (dlt and
   dbt-duckdb; a config-driven Arrow, Polars and DataFusion engine with dbt-duckdb; Scala Spark with
   dbt-spark), each on a Parquet lake, each with a follow-up change (a new mart and a dashboard). Work that
   does not fit one session.
2. **Traceability as a measure.** Seeded traps give each failure a known cause. A blind auditor gets only
   the run's record and must find the cause, where it first went wrong, and the cheapest fix point. A
   one-shot leaves a transcript; a harness leaves a spec, a plan, phases, reviews and decisions. The
   question is what each is worth when something breaks.
3. **Cheap verification.** Haiku-only arms: a verification harness (contracts before code, a stop gate),
   a review loop with a Haiku reviewer, and Cadence with all peers on Haiku after its defects are fixed.
4. **Success criteria** ([quality model](quality-model.md#owner-criteria-2026-10-14-dry-solid-extensible-traceable-cheap)):
   the arm closest to a DRY, SOLID and extensible system, whose path we can understand, and the
   cheapest arm in that top tier.
