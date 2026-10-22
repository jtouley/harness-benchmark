RUN_BY_COMMAND: spec-driven

# Implementation: cd-1 (gh-1 open-data pipeline)

Plan: `.context/plans/cd-1-gh-1-pipeline.plan.md` (sha256 0a523071571a9afb24f55163028a8cafdd1776d4ce2dbb7df93abad50f13f3e2).
Branch: feature/gh-1-pipeline. Commits: `92eee78` (phase 0) to `b6ba463` (phase 10), and `edc56ea` (R3 fix round).

## Step 0

- Problem: the repo held the P2 skeleton. `make build` and `make stream` were stubs. There was no engine, no tests, no dbt models.
- Done means: phases 0 to 10 are committed, one commit per phase with subject `phase N: ...`. Each phase has a test that failed before its code. Acceptance items A1 to A8 are checked in the Implementation Summary.
- Design decisions: the nine proposal records in `.context/proposals/cd-1-*.md`, and the plan amendments MF-1 to MF-8. The replay at `localhost:8099` was reachable throughout, so the blocked path did not apply.
- Blast radius: `pyproject.toml`, `uv.lock`, `Makefile`, `engine/`, `pipelines/`, `tests/`, `transform/`, `oracle_map.yml`, `DECISIONS.md`, `.gitignore`. `data/raw/` is unchanged. `lake/` and `out/` are generated and not committed.
- Plan is wrong? No blocking defect. Findings that changed the work are listed under Deviations below.

## Implementation Summary

Phases, in order (one commit each):

| Phase | Commit | Result |
|---|---|---|
| 0 | 92eee78 | Dependencies, `engine` package, smoke test. |
| 1 | 7c9272e | JSON Schema validation, `file:line:col` problems. |
| 2 | 3dc531e | Run loop, registries, Parquet lake sink with the MF-1 swap and recovery. |
| 3 | cd24c00 | USAspending, Census and sitematrix sources. Measurements in `DECISIONS.md`. |
| 4 | 911a543 | polars ops (`normalize_fips`, `parse_date`) and datafusion SQL. |
| 5 | 775dbdb | SSE source with reconnect and batching; `stream_lake` sink with manifests and the seen set. Replay fixture captured. |
| 6 | 4a1945f | `arrival_seq`, windows, edit rule, late rule, `late_events`, watermark in the manifest. |
| 7 | f966319 | `pipelines/build.yml`, `pipelines/stream.yml`, `engine run --duration`, make targets. |
| 8 | 659274d | dbt staging, dims, fact, and the Question A mart published to `out/marts`. |
| 9 | aef8769 | `stream_edit_fact`, `mart_wiki_window_5min` (MF-4, MF-6), `late_events` view. |
| 10 | b6ba463 | `oracle_map.yml`, seven check queries, acceptance run, blocked-path test, DECISIONS. |
| fix | edc56ea | R3 limits: complexity, duplication, bugs. |

Options tried (per the option rule):

- Phase 3, USAspending multi-line cells: the first read failed with "parser out of sync". Option 2, `newlines_in_values`, was kept.
- Phase 8, per-person division: DuckDB divides decimals as DOUBLE. Option 1, a decimal divide, was not exact. Option 2, integer half-even arithmetic on cents, was kept.
- Phase 8, mart publication: the external materialization cannot be incremental. Option 1, external for the stream mart, was dropped. Option 2, an incremental table with a post-hook `COPY` to `out/marts`, was kept.
- Phase 5, reader: a blocking line iterator could not wake for batch time limits. Option 2, a reader thread and a queue, was kept.
- Phase 5 and 6, duplicate delivery: the replay is inclusive on resume. Option 2, a seen set on `meta.id`, was kept.

Deviations from the plan (also in `DECISIONS.md`):

- Transforms have no `kind`. Their key is `engine`; `op` or `sql` names the step.
- Source kind `census_county_population` was added. The `csv` kind is implemented but no pipeline uses it.
- The Census source also outputs county and state names, for `dim_place`.
- Stream tables carry `sse_id` and no `_source_*` columns. `late_events` is written for every commit.
- Canary events are skipped. Malformed events are skipped with a message. The replay sends raw control characters inside JSON strings, and one event is truncated upstream.
- `make build` excludes stream models (`--exclude tag:stream`), so a batch build does not need stream data.
- Status values in `out/run_status.json` add `failed` to the three values in MF-8.

Findings from the replay:

- `Last-Event-ID` resume is inclusive: the event that carries the given id is sent again. SSE ids are not unique per event.
- Canary events (no wiki, no timestamp) are in the stream.

Findings from the data:

- Connecticut: the 2024 Census file lists nine planning regions, and the 2021 file lists eight counties. Seven county codes take the 2021 population (68 rows, 7,212,018.08).
- 15 territory county codes are in neither Census file (138 rows, 21,008,281.50). They go to the sentinel place.

## Verification

Commands and results (run in this worktree, 2026-10-21 to 2026-10-22):

- `uv run pytest -q`: 84 passed.
- `make build` twice: exit 0 both times, dbt `PASS=24`. Batch lake tables and `out/marts` are equal on sorted rows and equal schemas (A1).
- `make stream DURATION=20`, then `make stream DURATION=15`: exit 0, dbt `PASS=9` for the stream models. Raw rows are distinct by `meta.id`. 60 late events, flagged in raw and in `late_events` (check 7).
- Incremental stream mart equals a `--full-refresh` build on the live lake: 674 rows, equal schema and content.
- `uv run python -m tests.checks.acceptance --summary outputs/summary.md`: exit 0. A1 to A8 passed. Checks 1 to 7 passed. `out/run_status.json` has replay reachable, stream tables built.
- A2: an uninterrupted run of 25 s and a run with three restarts (4 segments of 8 s). Up to arrival 9208 both have the same meta.id sequence, no repeats, and equal per-wiki edit totals.
- Check 1 agency totals equal the lake. Check 4 counties roll up to states, and states total the lake total for June 2024 (264,837,644.85).
- Check 3: 1122 awards with negative FY2024 net obligation.
- `.context/gates/cognitive-complexity.json` written; `cognitive_complexity_gate.py --check`: exit 0.
- `uv tool run ruff==0.17.0 check --select F engine tests pipelines`: all checks passed.
- `python3 $CADENCE_HOME/scripts/entry_invariant.py --phase execution`: OK at the start of E1.

Outputs: `outputs/summary.md` (acceptance and check results). Repository files: `oracle_map.yml`, `DECISIONS.md`, `tests/checks/`.

ARTIFACT: .context/implementation/cd-1_stage4.md
