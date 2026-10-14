# Task P3: the open-data pipeline on Scala and Spark

Status: **proposed** (2026-10-14). Part of the [pipeline family](pipeline-family.md).

## Stack section (appended to the [shared spec](pipeline-spec.md))

> Use Scala 2.13, sbt and Apache Spark 3.5 in local mode (`local[*]`). The skeleton pins every version in
> `build.sbt`. The batch part is a Spark job that reads the raw files and writes the star schema and
> marts as Parquet under `out/`. The stream part uses Spark Structured Streaming with a custom source or
> a small reader that feeds it, event-time windows with a watermark, and a checkpoint directory under
> `out/_checkpoints/`. Test the transforms with ScalaTest on small in-memory DataFrames.
> `make build` and `make stream` call sbt.

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
| K3 | A watermark drops late rows silently; the spec wants them in `late_events` | Late events vanish (S3, F4) | Checks 6, 7 |
| K4 | `DecimalType` is capped at precision 38: dividing money by population can lose scale, or give `null` when ANSI mode is off | Casts to `double` (drifts by cents) or gets `null` per-person values | Check 2 |
| K5 | An outer join on place produces two `null` county keys that do not join each other | The unknown-county member splits or vanishes | Check 4 |
| K6 | Writing Parquet with the default `SaveMode` | The second `make build` fails or appends | Idempotence |

## Oracle

The shared checks, read from `out/` Parquet through `oracle_map.yml`. The grader reads the Parquet with
DuckDB, so no JVM is needed to grade.
