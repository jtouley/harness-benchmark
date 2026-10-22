RUN_BY_COMMAND: spec-driven

# cd-1 E1 (spec-driven): implementation of all seven phases

Input: `.context/plans/cd-1-gh-1-pipeline.plan.md` (sha256 b01ace9a150c74af6aca13adb55096a1713a933e52c8994963f8bdc00df45d47).
Contract: `$CADENCE_HOME/commands/spec-driven.md`. Ticket: cd-1.

This replaces the earlier stage-4 record that stopped before implementation. Its three blockers are resolved:

1. N-4 (does `make build` run the stream, and how an empty stream source behaves): decided. `make build` does not run the stream. It first writes an empty, schema-correct stream part when none exists. Recorded in `DECISIONS.md`. The plan text was not edited.
2. The Phase 3 probe: the replay server is reachable now. It replays from `Last-Event-ID`, so mode R. Recorded in `pipeline/README.md`.
3. Stacked plan updates (MF-2 to MF-7): applied in order; MF-5, MF-6 and MF-7 superseded the earlier text as they say.

## Step 0

- Problem: raw sources to Parquet, a dbt-duckdb star schema, two published marts (Question A: FY2024 obligations by county, agency and month, per person; Question B: Wikipedia edits per 5-minute event-time window with late events), and a resumable SSE consumer with no loss and no double count.
- Done means: each phase exit met; S1 to S6 met; `DECISIONS.md`, `outputs/summary.md`, `outputs/PR.md` present. Met, see Verification.
- Design decisions: as in the plan (Parquet lake, persisted cursor plus dedupe on `meta.id` against the stored rows, `is_late` computed at arrival, `DECIMAL(18,2)` and `DECIMAL(18,4)`, `external` marts, stdlib `unittest`, no dependency change). One deviation, below.
- Blast radius: `pipeline/`, `tests/`, `transform/`, `Makefile`, `oracle_map.yml`, `DECISIONS.md`, `outputs/`. `pyproject.toml`, `uv.lock` and `.gitignore` unchanged.
- Plan problems found: (a) a DuckDB `CAST` to `DECIMAL(18,2)` rounds, so the "parse fails above two decimals" rule needs a singular test, not the cast; (b) the plan's `toptier_agency_code` has no source column, so it is taken from the zip name; (c) the Phase 3 "dlt append" cannot give the seen-id check control over every write, so the consumer writes Parquet parts itself; (d) `unittest discover -s tests -t .` needs `tests/__init__.py`.

## Implementation Summary

Commits (one per phase, in order): `c55f2ec` phase 1, `9a11cbc` phase 2, `51a4618` phase 3, `89a2b73` phase 4, `2baeceb` phase 5, `196cb84` phase 6, `ff8a241` phase 7, `66143c6` refactor(stream) phase 3 (R3 fix round).

- Phase 1: `Makefile` targets; `stream` rejects a missing or non-positive `DURATION`. `tests/test_makefile.py`. Red run failed for the right reason (no DURATION in the message), then green.
- Phase 2: `pipeline/batch.py` (dlt resources `sitematrix`, `census_county`, `usaspending_awards`; pure row functions; `source_file`, `source_row`, `award_row_key` per MF-4; per-zip counts in `lake/logs/batch_counts.json`). `tests/test_batch.py`.
- Phase 3: `pipeline/stream.py` (SSE parser, `LATE_AFTER` and `is_late()` only here, `classify_batch`, `Store`, `consume`). Commit order per MF-2 (rows, then cursor). Startup reload per MF-2 and MF-5. Gaps in `lake/state/gaps.json`. `tests/test_stream.py` with an in-process fake server (no network mocks). Live check: `make stream DURATION=60` exit 0, 21,500 rows stored. Kill-and-restart check: see Verification.
- Phase 4: `transform/models/sources.yml`; staging `stg_usaspending__awards`, `stg_census__county_population`, `stg_wiki__sites`, `stg_wiki__recentchange`; intermediate `dim_geography`, `dim_agency`, `dim_date_month`, `dim_wiki`, `fct_obligation_monthly`; contracts enforced; key tests; `relationships`. Singular tests `assert_stg_usaspending_total_matches_raw_csv` (independent read of the zip CSVs through `zipfs`) and `assert_obligation_has_two_decimals`. County key: five-digit county FIPS, else `{state}000`, else `UNKNOWN` (79% of FY2024 rows have no county).
- Phase 5: marts in `transform/models/marts/`: `mart_obligations_by_geo_agency_month`, `mart_obligations_by_state_month`, `fct_wiki_edit_5min` (moved here, external), `late_events` (external; one writer per MF-6). External form checked in dbt-duckdb 1.11.0: `materialized='external'`, `location='out/marts/<name>.parquet'`, `format='parquet'`. Contracts on all four. Singular test `assert_state_total_equals_county_sum`. `tests/test_late_rule.py` (arrival rule on the Phase 3 fixture; threshold defined only in `pipeline/stream.py`).
- Phase 6: `oracle_map.yml` (seven checks), `pipeline/oracle.py` (checks, `marts-hash`), `tests/test_oracle.py` (checks 1 to 5 on fixtures and csv-module totals). Check 7 runs the consumer as a subprocess, kills it after two stored parts, restarts it, and compares arrival-ordered rows against an uninterrupted run over the same 2,000 stored events (`max_events` added to `consume` for this).
- Phase 7: `DECISIONS.md`, `outputs/summary.md`, `outputs/PR.md`.
- R3 fix round (`.context/gates/cognitive-complexity.json`): offenders were `consume` (complexity 40, 65 statements), one test function (complexity 16), ruff S608 (SQL built by f-string in `oracle.py`), ruff S310 (`urlopen`), mypy var-annotated (two). Fixed: `consume` split into a `Consumer` class; the test uses a helper; oracle SQL binds paths as parameters; the URL scheme is checked before `urlopen`, with a line-level `noqa: S310` (the URL is operator-configured); two annotations. Each option tried: one (no alternative needed). R3 `--check` now reports OK.

Options tried per phase: one option per phase; none failed its gates.

## Verification

- `uv sync --locked`: exit 0, `uv.lock` unchanged.
- `uv run python -m unittest discover -s tests -t .`: 46 tests, OK.
- `uv run dbt parse` and `uv run dbt build --project-dir transform --profiles-dir transform`: 74 of 74 PASS (clean build, and after a 60-second stream).
- `make build` on a clean checkout (`lake/`, `out/`, `transform/target` removed): exit 0.
- `make stream DURATION=60`: exit 0, `stored=21500 dropped=0 reconnects=0 canary=2 malformed=1`.
- `make build` a second and third time: marts identical (`python -m pipeline.oracle marts-hash`, row counts and sorted-row sha256 for all four files). S1 met.
- `python -m pipeline.oracle run` (checks 1 to 6): PASS for all six. Check 1: 9,820 = 9,820. Check 2: 1,442,017,216.67 = 1,442,017,216.67 (csv module, Decimal). Check 3: 0 keys differ. Check 4: 2,724 rows, 0 mismatches. Check 5: 21,500 rows = 21,500 distinct. Check 6: 21,441 edits + 59 late = 21,500 stored.
- `python -m pipeline.oracle run --check resume_equivalence` (check 7): PASS, 2,000 rows equal in arrival order (killed consumer restarted; the replay server was not restarted). Mode R.
- `cognitive_complexity_gate.py --check`: OK.
- `entry_invariant.py --phase execution`: OK.
- `phase_ledger.py --json`: completed [1..7], next none.
- `pyproject.toml`, `uv.lock`, `.gitignore`: unchanged from `35c22fd`.

## Open items and limits

- Canary events (2) and one truncated replay frame (`a0f69b5d-0c87-48d0-bbe5-c07b7c8c0262`) are not stored (`DECISIONS.md`, `pipeline/README.md`). S4 is measured on stored events.
- Question A covers agencies 417, 418, 474 and 485 only (C2). 73% of the obligation total sits in state-unallocated keys because 79% of rows have no county reported.
- 32 county keys (39 awards) are not in the 2024 Census county file (territories, Connecticut 09xxx); their population is null.
- The kill-and-restart checks (Phase 3 and check 7) kill the consumer, not the replay server.
- The stream store in `lake/` is a dev artifact; it is regenerated by `make stream` and is not committed.

ARTIFACT: .context/implementation/cd-1_stage4.md
