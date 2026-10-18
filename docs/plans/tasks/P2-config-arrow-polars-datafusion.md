# Task P2: a config-driven pipeline engine on Arrow, Polars and DataFusion

Status: **proposed** (2026-10-14). Part of the [pipeline family](pipeline-family.md).

## Stack section (appended to the [shared spec](pipeline-spec.md))

> Build a small pipeline engine in Python 3.12 and express this pipeline as configuration for it.
>
> - `pipelines/*.yml` declares sources (file, HTTP SSE stream), transforms and sinks. The engine reads the
>   YAML and runs it. Adding a new source or mart of the same kinds needs YAML only, no Python.
> - Data moves between steps as Apache Arrow tables or record batches (`pyarrow`). Use Polars for
>   row-wise and dataframe transforms and Apache DataFusion (`datafusion` Python package) for SQL
>   transforms. A transform in the YAML names its engine.
> - Sinks write the Parquet lake under `lake/`. The stream sink writes in micro-batches and commits the
>   consumer's position in the same step as the data, so a crash between them cannot lose or repeat an
>   event.
> - The engine does ingestion and the transforms needed to land clean source tables. Everything after the
>   lake is the dbt project (dbt-duckdb reading the lake), as the shared spec says. DataFusion has no
>   mature dbt adapter, so DataFusion and Polars work on the ingestion side.
> - The engine validates each YAML file against a schema before it runs, and reports the file, line and
>   problem on an error.
> - `make build` and `make stream` call the engine with the matching YAML.
>
> The skeleton pins `pyarrow`, `polars` and `datafusion` in `pyproject.toml`.

## Why this stack

The pipeline is data, so the engine must be general. A one-shot that hard-codes this one pipeline in
Python and hides it behind a thin YAML fails the generality check below. Moving from rows to Arrow
columns also brings type traps that a pandas-style solution does not see.

## Stack-specific traps

Each of these is a claim about the pinned tool versions. It is verified when the reference solution is built (the trap is reproduced, then fixed); a trap that does not reproduce is removed. **Same as** names the catalog trap it repeats at this layer; the two are one [equivalence set](pipeline-traps.md#equivalent-traps) for diagnosis.

| Id | Trap | Shallow behavior | Detected by | Cause class | Same as |
|---|---|---|---|---|---|
| A1 | Polars and Arrow infer `county_fips` as an integer from a CSV | Loses leading zeros (same effect as B3, at a different layer) | Check 2 | data-semantics | B3 |
| A2 | Arrow `decimal128` survives Parquet, but a Polars cast to `Float64` in one transform silently ends exact money | Totals drift by cents | Checks 1, 4 | numeric | B8 |
| A3 | Equality joins never match `NULL` keys (DataFusion SQL always, Polars by default) | Facts with no county drop out of the inner join to the place dimension, so the unknown-county member is lost | Check 4 | data-semantics | B5 |
| A4 | Committing the stream position before writing the batch | Loses events on a crash (F6) | Check 5 | idempotence | F6 |
| A5 | The YAML is not general: the engine branches on the pipeline name | Fails the generality check | Generality check | spec-reading | — |

## Extra check: generality

The grader adds a third YAML pipeline that the arm never saw: a new source (the same Census file under a
new name) landed in the lake with one Polars transform and one DataFusion SQL transform. It must run with
no engine code change and land the right rows.

## Oracle

The shared checks, read from `out/marts/` through `oracle_map.yml`, plus the generality check.
