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
| [P1](P1-duckdb-dlt-dbt.md) | Python: dlt, DuckDB, dbt-duckdb | The SQL-first stack. Successor to L3 |
| [P2](P2-config-arrow-polars-datafusion.md) | Python: a config-driven engine on Apache Arrow, Polars and DataFusion | The pipeline is data (YAML), not code; the engine must be general |
| [P3](P3-scala-spark.md) | Scala 2.13, Apache Spark 3.5 (local mode), Structured Streaming | The JVM batch and streaming stack; a heavier build and run |

All three get the same [request](pipeline-spec.md), inputs and checks. The [trap catalog](pipeline-traps.md)
is shared.

## Conformance

The three stacks answer the same seven checks from the same inputs, so they must agree:

1. **Against the answer key.** Each check's answer, rounded (money to whole cents, counts exact), is
   compared to the hashed key from the reference solution.
2. **Against each other.** For each pair of delivered solutions, the fact tables are compared on the
   shared grain: row count, sum of net obligations, and the set of keys (county FIPS, wiki, window
   start). Differential testing finds disagreements that a single key cannot, and a disagreement names
   the table where two interpretations split.
3. **Against itself.** `make build` twice and `make stream` stopped and started give the same outputs
   (traps B7, F6).

## Audit protocol {#audit-protocol}

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
   - Diagnosis accuracy: the cause matches the grader's trap id (questions 1 and 3).
   - Origin accuracy: question 2 matches the human adjudication.
   - Audit cost: the auditor's wall time and tokens.
   - Repair cost: an arm-matched repair agent fixes the run from the auditor's answer; its time, tokens and
     whether the checks then pass.
5. **Hypothesis.** With a one-shot record, the auditor finds the cause but not the origin, and repair
   often means redoing the work. With a harness record, the auditor finds both, and repair touches one
   phase.

## Arms

The arms of [next steps](../next-steps.md#arms), on each task:

- the Opus 5.5 one-shot (the bar), and one-shots on each cheap model;
- the review loop (a cheap model works; an independent reviewer checks the running result; the cheap
  model fixes);
- the verification harness (a cheap model, plus a contract and automated checks written before the code,
  that the model must run and pass; no model reviewer);
- full Cadence with `peer_models`.

The verification-harness arm follows from B01: Haiku saw its second defect in all 5 runs, diagnosed it
once, then left it out ("I'll leave that out of this change and report it") and never reported it. A
check the model must pass removes that judgment call. It costs far less than a reviewer that re-verifies
by hand.

## Runner

P3 runs Spark and a JVM build, and P1 and P2 run a replay server and a consumer. The test host (a 16 GB
Apple Silicon laptop with Docker Desktop) failed three times under emulated containers in the
calibration runs. These tasks run on a remote Linux host (x86-64, at least 8 cores and 32 GB RAM), one
trial per host at a time, with the replay server and grader in the same container network. Harbor
supports this through a custom environment; the task images are built once and pinned by digest.

## Work to admit the family

1. Snapshot and capture:
   - the USAspending and Census files of L3, with their sha256 values;
   - one hour of `recentchange` captured from the live service, with each frame's `id`, and the site
     matrix;
   - each catalog fact checked against them.
2. The replay server: serves the capture as SSE, honours `Last-Event-ID`, and injects faults F1 to F6 from
   a seed. Tests prove each fault occurs at its scheduled point.
3. One reference solution per stack, each passing every check twice and agreeing with the other two.
4. The answer key, and the single-trap wrong answers for the diagnosis step.
5. Calibration ([rule](../next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13)):
   the untouched skeleton fails every check; the Opus one-shot runs 5 times per stack, and the cheap
   one-shots 5 times each, to classify each stack as a lift task or a beyond task.
