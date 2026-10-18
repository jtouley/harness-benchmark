# Task family: one pipeline spec, three stacks (P1, P2, P3)

Status: **proposed** (2026-10-14, owner direction). Supersedes the single-stack [L3](L3-open-data-bi-pipeline.md).

## Why this family

The calibration so far showed that a strong one-shot can do a lot alone: Opus 5.5 fixed a multi-service
brownfield bug 10 times in 10 ([next steps](../next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13)).
The open question is no longer only "can the model do it". It is:

> When a long, many-part piece of work goes wrong, can you tell **where** it went wrong and **why**, and
> fix it there instead of starting again?

A one-shot leaves a transcript and a self-written summary. A harness leaves a spec, a plan, phases,
reviews and decisions. This family measures what each of those records is worth when something fails,
on work that does not fit one session.

| Task | Stack | What it adds |
|---|---|---|
| [P1](P1-duckdb-dlt-dbt.md) | Ingestion: dlt (Python). Models: dbt-duckdb | The reference stack. Successor to L3 |
| [P2](P2-config-arrow-polars-datafusion.md) | Ingestion: a config-driven engine on Apache Arrow, Polars and DataFusion. Models: dbt-duckdb | The ingestion pipeline is data (YAML), not code; the engine must be general |
| [P3](P3-scala-spark.md) | Ingestion: Scala 2.13, Apache Spark 3.5 batch and Structured Streaming. Models: dbt-spark on the same local Spark | The JVM stack; a heavier build and run |

All three share one architecture (owner direction, 2026-10-14): ingestion lands a **Parquet lake**, a
**dbt project** builds every model after it, and the marts are **published as Parquet**. So the modeling
layer, its tests and the follow-up mart are comparable across stacks, and the stacks differ where they
really differ: ingestion, streaming and exactly-once delivery.

All three get the same [request](pipeline-spec.md), inputs and checks. The [trap catalog](pipeline-traps.md)
is shared.

## Conformance

The three stacks answer the same seven checks from the same inputs, so they must agree:

1. **Against the answer key.** Each check's answer, rounded (money to whole cents, counts exact), is
   compared to the hashed key from the reference solution.
2. **Against each other.** For each pair of delivered solutions, the same tables are compared, each on
   its own grain:
   - the spending fact (one award transaction): row count, sum of net obligations, and the set of
     county FIPS codes;
   - the edit fact (one change event): row count, net bytes, and the set of event ids (`meta.id`);
   - the window mart: the set of keys (wiki, namespace, actor type, window start) and the edit count
     per key;
   - `late_events`: the set of event ids.

   Differential testing finds disagreements that a single key cannot, and a disagreement names the
   table where two interpretations split.
3. **Against itself.** `make build` twice and `make stream` stopped and started give the same outputs
   (traps B7, F6).

## Audit protocol

This is the measure the family exists for.

1. **Seeded ground truth.** Each failed check is first explained by the grader: the answer key stores the
   wrong answer each single trap produces ([catalog](pipeline-traps.md#mapping-for-the-audit)). So most
   failures have a known trap id and cause class before anyone audits.
2. **Blind auditor.** For each failed run, an auditor gets only the run's record and the symptom ("check 2
   is wrong: expected X, got Y"). It does not get the trap id. The auditor is a fixed agent (the same
   model and prompt for every arm), plus a human spot check on a sample. The record is:
   - one-shot arms: the repository, the transcript, and the arm's own summary;
   - harness arms: the same, plus the harness artifacts (spec notes, plan, phase commits, reviews,
     `DECISIONS.md`).
3. **The auditor answers four questions:**
   1. Which trap or cause (a cause class from the catalog, and the specific fact)?
   2. Where did it first go wrong: the reading of the spec, the plan, a phase, a review that missed it, or
      never considered?
   3. What is the cheapest fix point (the file or artifact to change)?
   4. How much of the delivered work must be redone (a list of tables or phases)?
4. **Scores.**
   - Diagnosis accuracy: the cause matches the grader's trap id, or any id in its
     [equivalence set](pipeline-traps.md#equivalent-traps) (questions 1 and 3).
   - Origin accuracy: question 2 matches the human adjudication.
   - Audit cost: the auditor's wall time and tokens.
   - Repair cost: an arm-matched repair agent fixes the run from the auditor's answer; its time, tokens and
     whether the checks then pass.
5. **Hypothesis.** With a one-shot record, the auditor finds the cause but not the origin, and repair
   often means redoing the work. With a harness record, the auditor finds both, and repair touches one
   phase.

## Success criteria (owner, 2026-10-14)

Which arm comes closest to a **DRY, SOLID and extensible** system, **whose path we can understand**,
and **at what cost**. The measures are in the [quality model](../../method/quality-model.md#owner-criteria-2026-10-14-dry-solid-extensible-traceable-cheap).
Each base task has a [follow-up task](pipeline-followup.md) (a new data mart and a Streamlit dashboard)
that the same arm builds on its own code; its success, cost and edit radius measure extensibility.

## Arms

Cost is the point: a harness may spend many tokens if each one is cheap. So every harness arm runs on
Haiku 5.5, reviews included, unless the arm says otherwise.

- The Opus 5.5 one-shot: the bar for checks and design, not a harness arm.
- One-shots on Haiku 5.5 and Sonnet 5.5: each model's own baseline.
- The review loop, Haiku 5.5 working and Haiku 5.5 reviewing (and, for comparison on B01 only, a Sonnet or
  Opus reviewer).
- The verification harness: an executable contract written before the code (by Haiku 5.5), and a stop
  gate that runs it; no model reviewer.
- Full Cadence with `peer_models: {"default": "haiku"}`, after jtouley/cadence#63–#66 are fixed.

**Deferrals are reviewed in real time.** In every harness arm, each deferral (work the harness decides
not to do now) goes to an independent Haiku 5.5 reviewer at the moment it is proposed. The reviewer
judges it against the request: *accept* (it is outside the request, or blocked, with a reason) or
*reject* (it is part of the request). A rejected deferral is implemented before the run may finish.
The log of proposals and verdicts is part of the run record and of the audit. Cadence does not do this
yet: its P8 gate checks a deferral's form (ticket, ripeness), not whether it was the right call
(jtouley/cadence#68). This rule comes from B01, where Haiku correctly diagnosed a second defect, decided
to "leave that out of this change and report it", and then reported nothing.

## Prompt hygiene

The prompts must not poison any run:

1. Every arm gets the same request text, word for word. No arm's prompt adds hints, quality adjectives
   ("staff level", "production quality") or knowledge of the traps, checks or follow-up.
2. A harness arm differs only by its installed harness (plugin, hooks, skill) and one line naming it
   ("Use the review-loop skill."). The harness's own instructions are generic: none names this task, its
   data or its traps.
3. The follow-up request is not visible to any arm until its base task is frozen.
4. The trap catalog, the answer key and this page are not in any arm's environment.
5. The staff-level bar is applied by the grading (checks, quality model, audit), not by the prompt.

The verification-harness arm follows from B01: Haiku saw its second defect in all 5 runs, diagnosed it
once, then left it out ("I'll leave that out of this change and report it") and never reported it. A
check the model must pass removes that judgment call. It costs far less than a reviewer that re-verifies
by hand.

## Runner and isolation

Every trial runs fully isolated from the owner's machine: the agent process, its tools, every virtual
environment and package cache, the database and broker containers, and anything the agent starts live in
one disposable environment that is deleted after grading. Nothing runs on the host but the orchestration
that starts and collects trials.

- Each trial gets its own container with its own Docker daemon inside (Docker-in-Docker, or a sysbox
  runtime), so a task that starts Postgres or Spark cannot reach another trial or the host. A worker an
  agent leaves running dies with the container. (The B01 calibration found that workers left by earlier
  runs consumed later runs' events through a shared Redis port; isolation per trial removes that class.)
- Python dependencies install into the trial's own virtual environment inside the container; the JVM
  build uses its own cache inside the container.
- The host is a remote Linux machine (x86-64, at least 8 cores and 32 GB RAM), one trial per machine at a
  time. The test laptop (16 GB Apple Silicon, Docker Desktop) failed three times under emulated x86
  containers in the calibration runs.
- Harbor runs the trials (its agent runs inside the trial container). The task images are built once and
  pinned by digest.

## Work to admit the family

1. Snapshot and capture:
   - the USAspending and Census files of L3, with their sha256 values;
   - one hour of `recentchange` captured from the live service, with each frame's `id`, and the site
     matrix;
   - each catalog fact checked against them.
2. The replay server: serves the capture as SSE, honours `Last-Event-ID`, and injects faults F1 to F6 from
   a seed. Tests prove each fault occurs at its scheduled point, and also that:
   - every event of F4's batch is late under the spec's rule (at its first arrival, the highest event
     time before it is more than 10 minutes past its window's end), and no other event is;
   - after an F2 reconnect, the re-sent events have the same timestamp as the `Last-Event-ID`;
   - the capture contains canary events (W1).
3. One reference solution per stack, each passing every check twice and agreeing with the other two.
4. The answer key, and the single-trap wrong answers for the diagnosis step.
5. Calibration ([rule](../next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13)):
   the untouched skeleton fails every check; the Opus one-shot runs 5 times per stack, and the cheap
   one-shots 5 times each, to classify each stack as a lift task or a beyond task.
