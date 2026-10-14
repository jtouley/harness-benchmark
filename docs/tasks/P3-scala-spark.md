# Task P3: the open-data pipeline on Scala and Spark

Status: **proposed** (2026-10-14). Part of the [pipeline family](pipeline-family.md).

## Stack section (appended to the [shared spec](pipeline-spec.md))

> Use Scala 2.13, sbt and Apache Spark 3.5 in local mode (`local[*]`) to land the raw files and the
> stream in the Parquet lake: a Spark batch job for the files, and Spark Structured Streaming for the
> stream (a custom source or a small reader that feeds it, with a checkpoint directory under
> `lake/_checkpoints/`). Model with dbt-spark using its `session` method, so the dbt models run on the
> same local Spark. Test the Scala ingestion with ScalaTest on small in-memory DataFrames. The skeleton
> pins every version in `build.sbt` and `requirements.txt`. `make build` and `make stream` call sbt and
> dbt.

## Why this stack

Spark has its own semantics for each trap: schema inference, `null` in joins, watermarks and checkpoints.
The JVM build is slow, so each loop costs more, and a plan that saves loops is worth more. This is the
heaviest task in the family. It runs on the remote runner only ([family](pipeline-family.md#runner)).

## Stack-specific traps

Each of these is a claim about the pinned tool versions. It is verified when the reference solution is built (the trap is reproduced, then fixed); a trap that does not reproduce is removed.

| Id | Trap | Shallow behavior | Detected by |
|---|---|---|---|
| K1 | `inferSchema` reads `county_fips` as an integer | Loses leading zeros (as B3) | Check 2 |
| K2 | Spark has no built-in SSE source; the stream must reach Structured Streaming somehow | Reads the stream in a driver loop with `foreachBatch` and no checkpoint of the SSE position, so a restart double counts (F6) | Check 5 |
| K3 | Late events: if the window logic sits in Structured Streaming with a watermark, Spark drops late rows silently; the spec wants them in `late_events` | Late events vanish (S3, F4) | Checks 6, 7 |
| K4 | `DecimalType` is capped at precision 38: dividing money by population can lose scale, or give `null` when ANSI mode is off | Casts to `double` (drifts by cents) or gets `null` per-person values | Check 2 |
| K5 | An outer join on place produces two `null` county keys that do not join each other | The unknown-county member splits or vanishes | Check 4 |
| K6 | Writing Parquet with the default `SaveMode` | The second `make build` fails or appends | Idempotence |

## Oracle

The shared checks, read from `out/marts/` through `oracle_map.yml`. The grader reads the Parquet with
DuckDB, so no JVM is needed to grade.
