# Task P1: the open-data pipeline on dlt, DuckDB and dbt

Status: **proposed** (2026-10-14). Successor to [L3](L3-open-data-bi-pipeline.md). Part of the
[pipeline family](pipeline-family.md).

## Stack section (appended to the [shared spec](pipeline-spec.md))

> Use Python 3.12, dlt to load the raw files and the stream, DuckDB as the warehouse
> (`out/warehouse.duckdb`), and dbt-duckdb for every model. The skeleton pins the versions in
> `pyproject.toml`; do not change them. dbt tests cover the keys of every model. The stream consumer
> may be a dlt pipeline or a plain Python consumer that writes to DuckDB; the stream marts are dbt
> models. Write the Parquet outputs with DuckDB `COPY ... TO ... (FORMAT parquet)`.

## Skeleton

`data/raw/` (snapshot), an empty dbt project (`dbt_project.yml`, `profiles.yml` pointing at
`out/warehouse.duckdb`), a `Makefile` with `build` and `stream` targets that fail, `pyproject.toml` and
`uv.lock` with the pinned versions, and no models.

## Stack-specific traps (in addition to the [catalog](pipeline-traps.md))

Each of these is a claim about the pinned tool versions. It is verified when the reference solution is built (the trap is reproduced, then fixed); a trap that does not reproduce is removed.

| Id | Trap | Shallow behavior | Detected by |
|---|---|---|---|
| D1 | DuckDB reads `county_fips` as an integer when every value in its sample looks numeric | Loses leading zeros at load, before any model can fix them | Check 2 |
| D2 | dlt's default write disposition appends | A second `make build` doubles every row | Idempotence |
| D3 | dlt flattens nested objects (`length`, `revision`, `meta`) into columns such as `length__new`, and a column exists only after an event that has it arrives | A model that assumes `length__new` exists fails on a batch of only `log` events, or treats the missing value as 0 bytes | Check 5 |

## Oracle

The shared checks, read from `out/` Parquet and `out/warehouse.duckdb` through `oracle_map.yml`.
