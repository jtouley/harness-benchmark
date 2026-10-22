RUN_BY_SKILL: de-adversarial-reviewer
Mode: plan-gate
Pipeline-Run: a4a4146f-ee60-4507-90b6-b015e00c812a

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Ticket token: cd-1

# Adversarial review: gh-1 pipeline plan (cd-1), round 2

Plan: `.cursor/plans/gh-1-pipeline_cd-1.plan.md` (sha256 e2c50302757bc8c9423e974983f7cbb45b20aa1a6962aaa3ee1f5c56d529f1a1, matches the input line).
This is the plan of cycle five: the cycle-five plan review reviewed sha 9c87f15e (the round 1 input), and the cycle-five plan-update text was then applied to it, giving e2c5.
Round 1: `.context/adversarial/adversarial_gh-1-pipeline_cd-1.md` (REQUEST CHANGES, sha 9c87). Round 2 checks which round 1 items the plan now closes.

## Verification notes

Inspected:
- The full plan, sections 1 to 9 and all update blocks (MF-1 to MF-10, cycle-five notes, revision ledgers).
- `Makefile` and `transform/` (skeleton only: `dbt_project.yml`, `profiles.yml`, `models/`). No stream model or `tests/` tree exists yet.
- `.context/proposals/` (13 records, all `cd-1-*`), `.context/reviews/plan_gh-1-pipeline_cd-1.md`.
- Tag mentions in the plan (`grep -n tag`): `tag:stream` appears only on the `mart_edit_windows_5min` model (line 278) and in the `make` and dbt command lines (lines 145, 146, 208, 209, 181, 382, 434). No other node is tagged.

Not run: DuckDB and dbt are not installed in this environment. Claims about dbt selection and DuckDB types are reasoned from the plan text and marked unverified where they depend on a run.

Round 1 items, status in this plan:

| Round 1 item | Status | Where |
|---|---|---|
| B-1 untagged stream-dependent nodes | Open. No new text tags any node except the window mart (see B-1 below) | Plan lines 90, 145-146, 208-209, 278 |
| C-1 `warehouse_path` default in the Jinja form | Closed in a note, not in a phase test | Cycle-five notes, line 507 (`{{ var('warehouse_path', 'out/warehouse.duckdb') }}`). The make-build profile-load check is not named as a test |
| C-2 explicit casts for money and timestamp | Open | Phase 3 and MF-3 name types only |
| C-3 check 7 predicate | Partly closed. Check 5 is now `edit` or `new` (line 476). Check 7 still says "count of late events" (line 216) | Lines 216, 476 |
| C-4 reset of the Phase 6 fixture lake | Closed in a note | Cycle-five notes, line 505 |
| C-5 DURATION handoff and stream end condition | Open. The plan defers the path to E1 | Cycle-five notes, lines 503-504 |
| C-6 check 2 `limit 10` and tie-break | Partly closed. Tie-break by county FIPS is in N-7 (line 283). `top 10` is not written | Lines 283, 186 |
| C-7 Connecticut fallback test | Partly closed. The fallback is named in N-1, no Phase 4 test asserts it | Line 294 |

## Blocking issues

### B-1. A fresh `make build` fails, and `make stream` never refreshes the fact that the window mart reads

Evidence:
- `make build` runs `dbt build --exclude tag:stream` (G-9, line 90; Phase 6, line 208).
- Only `mart_edit_windows_5min` carries tag `stream` (line 278). The stream source, its staging models, `fct_edit` (line 203), `late_events` (line 204), `window_build_state`, and the check 5 to 7 views (lines 216-218) carry no tag.
- Those untagged nodes read `lake/stream_events/`. That folder exists only after `make stream`. `lake/` is gitignored and removed before grading.
- `dbt build --exclude tag:stream` removes only tagged nodes. The untagged stream nodes still run and fail on a missing Parquet glob. Section 1 success signal 1 (`make build` passes) therefore fails on a fresh checkout. Phase 3 exit (line 181) fails the same way.
- Second effect: `make stream` runs `dbt build --select tag:stream` (line 209). dbt `--select tag:` does not add upstream nodes. The untagged `fct_edit` is not rebuilt by `make stream`. The window mart then reads a stale fact, and MF-6's state (`built_max_event_time` from `fct_edit`) is computed on the stale fact too. The `make stream DURATION=60` end-to-end check (Phase 6 exit, line 212) can pass its file checks while the window output is stale.
- The MF-5 double-build test runs `make build` on a lake with no stream data (line 289). It fails for the same reason as the first effect.
- The plan has no test that runs `make build` on an empty lake before `make stream`.

Required fix:
- Tag every node that reads the stream lake with `stream`: the stream sources, their staging models, `fct_edit`, `late_events`, `window_build_state`, and the check 5 to 7 views. Name the tag list in G-9 and in Phase 6.
- Add a test: on an empty `lake/` (no `stream_events/`), `make build` passes. Name it in Phase 6 or Phase 3.
- Add a test: after `make stream`, `fct_edit` is rebuilt in the same run (for example, `dbt build --select tag:stream` lists `fct_edit` in its run results).

Core rule: none of `core:*` covers this. It is a plan defect against section 1 success signal 1 and against G-9.

## Conditions

### C-1. Name the `stream` tag list and the check 7 predicate

Check 7 (line 216) says "count of late events". `late_events` (line 204) is the late rows of `fct_edit`, which holds all change types. G-6 counts only `edit` and `new` as edits, and cycle five changed check 5 to match G-6 (line 476), but check 7 is not changed.
Condition: state in Phase 7 and DECISIONS.md whether check 7 counts all late change types or only `edit` and `new`. Add a fixture test with a late `log` event that fixes the answer.

### C-2. Mart contract types need explicit casts (unverified)

Phase 3 (line 179) and MF-3 (lines 265-274) enforce `DECIMAL(18,2)` for money (G-5) and `TIMESTAMP` UTC for `window_start`. The plan does not say the SQL casts to those types. DuckDB `sum` over `DECIMAL(18,2)` can widen the scale (section 8, line 232, names the division case). A `to_timestamp` result can be timezone-aware.
Condition: each contracted money and timestamp column gets an explicit `cast(... as DECIMAL(18,2))` or `cast(... as TIMESTAMP)` in the model SQL. The Phase 3 contract test reads the column types.

### C-3. The DURATION path and the stream end condition are not named

`make stream` requires `DURATION` (line 208). Cycle five defers the path to E1 (lines 503-504), and the plan does not name the CLI argument or YAML key that carries it to the engine. The end condition of `transform/tests/fixtures/pipelines/stream_test.yml` (the fake SSE server closes the stream, or a duration key) is also not named.
Condition: name the key or argument, and the end condition the test relies on, in Phase 5 or Phase 6.

### C-4. Check 2 top-10 cut and its tie-break are not in the view text

The request asks for "the ten counties" (check 2). N-7 (line 283) gives the inclusion rule and the tie-break by county FIPS ascending, but Phase 4 (line 186) says the view "ranks" counties without a cut-off.
Condition: state `limit 10` in Phase 4 and in `oracle_map.yml`, and add a fixture test for the tie-break.

### C-5. Connecticut fallback needs a test that matches the logged rule

The 2024 census file has nine Connecticut planning-region rows under SUMLEV 050, and the 2021 file has eight county rows (09001 to 09015). Under N-1 (line 294) all eight Connecticut counties take `POPESTIMATE2021`. No Phase 4 test asserts this, so check 2 mixes vintages inside one state without a test.
Condition: add a Phase 4 fixture test that asserts the Connecticut counties take the 2021 value, and name the eight counties in DECISIONS.md.

## Adversarial scenarios

| Scenario | Handled? | Evidence |
|---|---|---|
| S1. Fresh clone, `make build` before any `make stream` | No | B-1. Untagged stream nodes read a lake that does not exist yet (Makefile, `.gitignore`, plan lines 203-218, 278). |
| S2. `make stream` after a fact change, with `fct_edit` untagged | No | B-1. `--select tag:stream` does not select upstream nodes, so the window mart reads a fact that `make stream` did not rebuild. |
| S3. Crash between the micro-batch tmp write and the `os.replace` | Yes | Footer is the commit (line 124). Restart reads the highest committed batch id and deletes `_tmp/` (line 297). Phase 5 crash test (line 197). |
| S4. Redelivered event after reconnect, replay ignores `Last-Event-ID` | Yes | Dedupe on `meta.id` against all committed ids (line 300). Risks section (line 230) names the fallback. Cost is a full scan, accepted at trial volume. |
| S5. Late event at the boundary, with an earlier same-batch arrival | Yes | MF-1 (lines 246-254), including `test_late_uses_max_including_same_batch` and the boundary case. |
| S6. Window mart after a restart, with on-time events in the same batch | Yes | MF-6 algebra (lines 334-336) holds. Tests `test_window_refresh_covers_same_batch_on_time` and `test_window_refresh_after_failed_dbt_run` (lines 352-355). Failure injection is in the cycle-five notes (lines 473-475). |
| S7. First build with no state row, or mart present and state absent | Yes | MF-8 (lines 398-405) and `test_window_first_build_full_refresh` cases (a) and (b). |
| S8. Phase 6 tests write to the real stream lake | Yes | MF-10 (lines 452-461) and `test_phase6_run_leaves_real_stream_lake_unchanged`. Fixture lake reset in cycle-five notes (line 505). |
| S9. Second run of the same Phase 6 fixture dedupes against the first | Yes, in a note | Cycle-five notes, line 505. The reset step is not a named test step. |
| S10. Mart contract on money and timestamp columns | Unverified | C-2. DuckDB not installed. |
| S11. Check 7 counts late `log` and `categorize` events | Not stated | C-1. |
| S12. `make stream DURATION=<s>` where the replay ends early | Partly | G-9 (line 90): engine exits 0 and dbt still runs. The DURATION path is not named (C-3). |
| S13. Check 2 ties and the county cut | Partly | N-7 gives the tie-break. No `limit 10` in the view text (C-4). |

## Trade-offs

- The window refresh reads the whole fact from L on each run (MF-6). This is simpler and correct, and it is not a pure delta. The cost grows with the lake. Accepted for trial volume.
- Dedupe scans all committed `meta.id` values on each batch (line 300). This keeps the no-loss and no-duplicate rule without a separate position store. It does not scale. Accepted by the plan.
- The stream position lives in the Parquet footer. Its atomicity depends on `os.replace` on the same filesystem. `_tmp/` lives under `lake/`, so this holds.
- Section 1 success signal 1 is the only success signal that a fresh checkout tests end to end. B-1 blocks it. Fixing B-1 by tagging every stream node is the smallest change.

Verdict: REQUEST CHANGES
