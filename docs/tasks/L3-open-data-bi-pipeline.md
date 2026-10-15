# Proposed task L3: an open-data BI pipeline (DuckDB, dlt, dbt)

> **Superseded (2026-10-14)** by the [pipeline family](pipeline-family.md): one [shared spec](pipeline-spec.md) on three stacks ([P1](P1-duckdb-dlt-dbt.md), [P2](P2-config-arrow-polars-datafusion.md), [P3](P3-scala-spark.md)). Its traps are B1–B7 in the [trap catalog](pipeline-traps.md). This page is kept for history.

Status: **proposed** (2026-10-12). It is not a golden task yet. It enters a run set only after it is
committed under `golden/tasks/` with a reference solution and a hidden oracle, and after the untouched
repository fails that oracle ([criteria §3](../criteria.md#3-task-classes)).

## Why this task

On T04–T06 (about 300 lines of Python, every output format given), Opus 5.5 alone finished in about
2 minutes with the top scores ([findings](../findings.md)). Those tasks are too small to show what a
harness is for. Real data work is the opposite: many tools, a design the spec does not fix, and data
quirks where a plausible answer is wrong. That is class L (repository scale, open design) and class O
(a wrong number that looks right) at the same time.

## The request (the task text every arm gets, draft)

> Build a local analytics stack that answers: where did federal contract and grant money go in fiscal
> year 2024, in total and per person, by state, county, agency and month?
>
> The raw files are in `data/raw/` (USAspending.gov prime award transactions for FY2024 for the agencies
> listed in `data/raw/README.md`, and the Census Bureau county population estimates). Load them with
> dlt into DuckDB, and model them with dbt (dbt-duckdb) into a star schema that a BI tool can use
> directly. Document the grain of each model and test the keys. `make build` must run the whole thing
> from the raw files, and running it twice must not change the results.

## What makes it hard (and what a shallow solution gets wrong)

These are properties of the public data. Each one must be checked against the snapshot when the task is
built, before it is admitted.

| Trap | What a shallow solution does | What the oracle checks |
|---|---|---|
| A transaction file has one row per action, and an award's total amount repeats on each of its rows | Sums the award total over transactions, and counts a modified award many times | Net obligations per agency equal the sum of the per-action obligation amounts |
| De-obligations are negative actions | Drops negative rows, or treats them as errors | Awards with a net negative obligation are counted, not dropped |
| County codes are state code plus county code, with leading zeros | Reads codes as integers, so `01001` becomes `1001` and joins fail | Every county in the population file joins; none is lost to a missing zero |
| Connecticut's counties became planning regions in Census data from 2022 | Joins silently drop Connecticut, or double count it | Connecticut's money and population are both present, with the mapping documented |
| Some transactions have no place-of-performance county | Drops them silently, so state totals do not reconcile | They go to an explicit "unknown county" member, and state totals reconcile with the source |
| Re-running the load | Appends a second copy of every row | A second `make build` leaves every mart unchanged |

## The oracle (hidden from the agent)

After `make build`, a hidden test suite runs read-only SQL against the delivered DuckDB file:

1. FY2024 net obligations per agency (the double-count trap).
2. The ten counties with the highest obligations per person (zero padding, Connecticut, population join).
3. The count of awards with a net negative obligation.
4. Reconciliation: monthly county totals sum to state totals, and state totals sum to the source total,
   including the unknown-county member.
5. Idempotence: the row counts and totals are unchanged after a second `make build`.

The expected answers come from the reference solution and are stored hashed in the hidden suite. Each
money answer is rounded to whole cents and each count is exact before it is hashed, so a correct solution
that sums in a different order still matches. Names of
tables and columns are not prescribed. The suite reads a small `oracle_map.yml` that the agent must write
(the spec asks for it), which says which model and column answer each question. A missing or wrong map
is a failed question, not a crash.

## How it is graded

- **M1 acceptance**: all five oracle questions pass.
- **M2 defects** and **M3 false success**: a run that reports success while an oracle answer is wrong is a
  false success, the most expensive failure ([criteria §4](../criteria.md#4-measures)).
- **The [quality model](../quality-model.md)**: the design checklist, including "dbt tests on every key"
  and "the grain of each model is documented", and the tool gate. `scripts/quality_metrics.py` measures
  Python only; this task's dbt SQL needs its own measures (sqlfluff, and dbt test coverage of each model's
  keys), added to the script before the task is admitted.

## Work to admit it

1. Snapshot script: download the FY2024 files for a fixed agency list and the population file, record
   each file's sha256 and source URL and date, and commit the script and the hashes. The run itself is
   offline.
2. Skeleton repository: `data/raw/` with the snapshot, an empty dbt project, a `Makefile` with a `build`
   target that fails, the pinned tool versions, no models.
3. Reference solution: dlt pipeline, dbt models and tests, `oracle_map.yml`.
4. Hidden suite and answer key, generated from the reference solution.
5. Checks: the untouched skeleton fails all five questions, and the reference passes all five, twice.
   And the task is hard enough: a Haiku 5.5 one-shot fails the oracle in at least half of 5 pilot runs.
   A task that a cheap model alone passes cannot show what a harness adds. These admission runs are not
   part of the results.
6. Caps: this task needs a higher time cap than criteria v1's 1800 s, recorded in the next criteria
   version before the run set.

Two more class L or O tasks are needed before a class claim is possible (criteria §6). The criteria
already name L1 (headless runtime), L2 (PR sweep) and O1 (golden questions).
