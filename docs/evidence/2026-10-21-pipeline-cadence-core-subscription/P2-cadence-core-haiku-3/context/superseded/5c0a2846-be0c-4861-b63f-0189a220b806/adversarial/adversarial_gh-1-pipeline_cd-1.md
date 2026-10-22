RUN_BY_SKILL: de-adversarial-reviewer
Mode: plan-gate
Pipeline-Run: a4a4146f-ee60-4507-90b6-b015e00c812a

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Ticket token: cd-1

# Adversarial review: gh-1 pipeline plan (cd-1), round 1

Plan: `.cursor/plans/gh-1-pipeline_cd-1.plan.md` (sha256 9c87f15e5ea0401bc9c41d63d1cee7344105e1592f36293e6fa834b8fda5ae54, verified).
Request: `.context/proposals/cd-1.md`. Vibe test: `.context/vibetest/cd-1_2026-10-22.md`. Deferral register: `.context/deferrals/cd-1_deferral-register.md`.

## Verification notes

Inspected:
- `Makefile`: both targets are stubs (`build`, `stream`). No other targets.
- `pyproject.toml`: pins match the plan (pyarrow 26.0.0, polars 2.0.0, datafusion 55.0.0, dbt-core 1.11.6, dbt-duckdb 1.11.0, duckdb 1.5.6).
- `transform/profiles.yml`: `path` is hard-coded to `out/warehouse.duckdb`. The plan's `warehouse_path` var is not yet in the skeleton. Expected, because Phase 4 edits it.
- `.gitignore`: `lake/` and `out/` are ignored, and the comment says the grader removes them first.
- `data/raw/usaspending/`: 8 zips for agencies 417, 418, 474, 485 (assistance and contracts), as the README and the plan say.
- `data/raw/census/co-est2024-alldata.csv`: Connecticut SUMLEV 050 rows are the nine planning regions (STATE 09, COUNTY 110 to 190). The 2024 file has no county rows for Connecticut. `co-est2021-alldata.csv` has eight Connecticut county rows (09001 to 09015). This confirms N-1 in the plan.
- Plan text: section 1 success signals, section 3 (G-1 to G-9), Phase 3 to Phase 7, MF-1 to MF-10, and the cycle-five notes.
- Window arithmetic (MF-6 and MF-8). An event is late when `max > window_end + 10 min`, which is `max > window_start + 900 s`. So an on-time event has `window_start >= max_before - 900 s`. With `L = built_max_event_time - 900 s`, every window that an unbuilt batch can touch starts at or after L. The rule holds.

Not run: DuckDB and dbt are not installed in this environment, so no build, contract or profile rendering was reproduced. Claims that depend on them are marked as unverified in the conditions.

Prior rounds:

| Round | Artifact | Verdict | Note |
|---|---|---|---|
| plan-review, cycle five | `.context/reviews/plan_gh-1-pipeline_cd-1.md` | READY TO EXECUTE | Did not check which models carry `tag:stream`, so B-1 is not covered there. |

## Blocking issues

### B-1. A fresh `make build` fails because the stream-dependent models are not tagged

Evidence:
- `make build` runs `dbt build --exclude tag:stream` (G-9, line 90; Phase 6, line 208).
- The plan tags one node `stream`: `mart_edit_windows_5min` (line 278). It names no tag for `fct_edit`, `late_events` (Phase 6, lines 203-204), the stream source and staging models (Phase 3 does not mention them), or the check 5 to 7 views (Phase 7, lines 215-218).
- The untagged nodes read `lake/stream_events/`, which is created only by `make stream`. `lake/` is gitignored and removed before grading (`.gitignore`).
- `dbt build --exclude tag:stream` removes only the tagged nodes. The untagged nodes still run and fail on a missing relation or a missing Parquet glob.
- Section 1 success signal 1 requires `make build` to pass, and the Phase 3 exit requires `dbt build --exclude tag:stream` to pass. Neither holds on a fresh checkout.
- The plan has no test that runs `make build` before `make stream`. Phase 7 runs `make build` only after the stream has run.

Required fix: tag every node that reads the stream lake with `stream` (the stream sources, their staging models, `fct_edit`, `late_events`, `mart_edit_windows_5min`, the `window_build_state` state, and the check 5 to 7 views). Add a Phase 3 or Phase 6 TDD case: on an empty `lake/` (no `stream_events/`), `make build` passes. Name this in the G-9 row.

Core rule: none of `core:*` covers this. It is a plan defect against section 1 success signal 1.

## Conditions

### C-1. Name the `warehouse_path` default in the profile form that dbt renders

The plan says `transform/profiles.yml` takes `path` from `warehouse_path`, "default `out/warehouse.duckdb`" (MF-9, line 412). It does not give the Jinja form. The cycle-five review (Notes, line 30) reported that a default set only in `dbt_project.yml` is not in the profile render context. dbt is not installed here, so this is not reproduced.

Condition: write `path: "{{ var('warehouse_path', 'out/warehouse.duckdb') }}"` and the same for `publish_dir`, with the default as the second argument. Add a check that `make build` (which sets no vars) loads the profile.

### C-2. Mart contract types need explicit casts (unverified)

Phase 3 (line 179) and MF-3 (line 265-274) require enforced types, `DECIMAL(18,2)` for money (G-5) and `TIMESTAMP` UTC for `window_start`. The plan does not say the mart SQL casts to these types. Two likely mismatches:
- A DuckDB `sum` over `DECIMAL(18,2)` may widen to a wider decimal type. The contract then fails.
- A `to_timestamp` or epoch conversion may return a timezone-aware type, not `TIMESTAMP`.

Not verified here (DuckDB not installed). Condition: each contracted money and timestamp column gets an explicit `cast(... as DECIMAL(18,2))` or `cast(... as TIMESTAMP)` in the model SQL. Phase 3 and Phase 6 TDD adds a test that reads the contract types.

### C-3. Check 7 scope is not stated

G-6 (line 87) says lateness applies to every consumed event, and that `log` and `categorize` stay in the fact but are not edits. The plan does not say whether check 7 ("the count of late events") counts all late change types or only `edit` and `new`. `late_events` is "late rows of `fct_edit`" (line 204), which includes all types. Condition: state the check 7 predicate in Phase 7 and in DECISIONS.md, and add a fixture test with a late `log` event.

### C-4. The Phase 6 test fixture lake accumulates state between runs

The cycle-five review (Notes, line 29) asked for a reset of `transform/tests/fixtures/lake/stream_events/` before each test run. The plan (MF-10, lines 452-454) does not add it. Without it, the second test run dedupes against the first run. Condition: name the reset step in the Phase 6 test harness, before each `stream_test.yml` run.

### C-5. The end condition and the DURATION handoff are not named

`make stream` requires `DURATION` (line 208), and `pipelines/stream.yml` has no duration key in the plan. The cycle-five review (Notes, line 28) asked for the end condition of `transform/tests/fixtures/pipelines/stream_test.yml` (the fake SSE server closes the stream, or a duration key). The plan does not name either. Condition: name the CLI argument or YAML key that carries DURATION to the engine, and the end condition the test relies on.

### C-6. Check 2 cut-off is not written in the view text

The request asks for "the ten counties" (check 2). Phase 4 (line 186) says the view "ranks" counties, with the MF-4 inclusion rule. The top-10 cut and its tie-break are not stated in the view definition. Condition: state `limit 10` and the tie-break in Phase 4 and in `oracle_map.yml`.

### C-7. The Connecticut fallback needs a test that matches the logged rule

I confirmed N-1 in the census CSV. For all eight Connecticut counties, check 2 uses the 2021 population (`POPESTIMATE2021`), and the nine 2024 planning-region rows are not joined. The plan says the "population NULL" test does not fire for Connecticut (line 294). That is the right logging, but it leaves check 2 mixing vintages inside one state. Condition: add a Phase 4 fixture test that asserts Connecticut counties take the 2021 value, and name the eight counties in DECISIONS.md.

## Adversarial scenarios

| Scenario | Handled? | Evidence |
|---|---|---|
| S1. Fresh clone, `make build` before any `make stream` | No | B-1. Untagged stream-dependent nodes read a lake that does not exist yet (Makefile, `.gitignore`, plan lines 203-218, 278). |
| S2. Crash between the micro-batch tmp write and the `os.replace` | Yes | The footer is the commit (cd-1-stream-commit, line 124). The restart reads the highest committed batch id and deletes `_tmp/` (line 297). Phase 5 crash test (line 197). |
| S3. Redelivered event after reconnect, and the replay ignores `Last-Event-ID` | Yes | Dedupe on `meta.id` against all committed ids (line 300). The cost is a full scan, accepted at trial volume. |
| S4. Late event at the boundary, with a same-batch earlier arrival | Yes | MF-1 (lines 246-254) and its boundary test. The rule is `max > window_start + 900 s`, matching "more than 10 minutes after the window end". |
| S5. Window mart after a restart, with on-time events in the same batch | Yes | MF-6 proof (lines 334-336) checked by algebra above. Tests `test_window_refresh_covers_same_batch_on_time` and `test_window_refresh_after_failed_dbt_run` (lines 352-355). |
| S6. Connecticut county with no 2024 estimate | Partly | Logged in N-1 and checked in the census CSV (see C-7). No test asserts the fallback. |
| S7. Profile loads with no `--vars` (`make build`) | Unverified | C-1. The plan's wording does not give the default's form. dbt not run here. |
| S8. Mart contract on money and timestamp columns | Unverified | C-2. DuckDB not installed. |
| S9. Check 7 counts late log and categorize events | Not stated | C-3. G-6 and the plan do not give the predicate. |
| S10. Second Phase 6 test run dedupes against the first | Not handled | C-4. The cycle-five note asked for a reset. The plan does not add it. |
| S11. `make stream DURATION=<s>` where the replay ends early | Handled | G-9 (line 90): the engine exits 0 and the dbt step still runs. The DURATION handoff is not named (C-5). |

## Trade-offs

- The window refresh reads the whole fact from L on each run (MF-6). This is simpler and correct, and it is not a pure delta. The cost grows with the lake. Accepted for trial volume.
- Dedupe scans all committed `meta.id` values on each batch (line 300). This keeps the no-loss and no-duplicate rule without a separate position store. It does not scale. Accepted by the plan.
- The stream position lives in the Parquet footer (cd-1-stream-commit). Its atomicity depends on `os.replace` on the same filesystem. The plan's `_tmp/` lives under `lake/`, so this holds.
- The fixture stream lake is isolated by path (MF-10). That isolation depends on C-4 being fixed.

Verdict: REQUEST CHANGES
