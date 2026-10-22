RUN_BY_SKILL: de-adversarial-reviewer
Mode: plan-gate
Pipeline-Run: a4a4146f-ee60-4507-90b6-b015e00c812a

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Ticket token: cd-1

# Adversarial review: gh-1 pipeline plan (cd-1), round 3

Plan: `.cursor/plans/gh-1-pipeline_cd-1.plan.md` (sha256 e2c50302757bc8c9423e974983f7cbb45b20aa1a6962aaa3ee1f5c56d529f1a1, matches the input line of the P6 call).
Packet sha256: 3d2c65170c3a779f066ff45ea7c04a47e97cdbee781dfc6642d7e523aabbc767.
Prior rounds: `.context/adversarial/adversarial_gh-1-pipeline_cd-1.md` (REQUEST CHANGES) and `_r2.md` (REQUEST CHANGES). Both reviewed the same plan text (e2c5). The plan has not changed since round 2, so round 2's findings are still open unless the plan text says otherwise.

## Verification notes

Inspected:
- The full plan (sections 1 to 9, all cycle update blocks, revision ledgers).
- Round 2 report, to confirm its B-1 and C-1 to C-5 against the plan text.
- Skeleton files: `Makefile` (both targets are stubs that exit 1), `.gitignore` (`lake/` and `out/` ignored; comment says the grader removes them first), `pyproject.toml` (pins as stated), `transform/dbt_project.yml`, `transform/profiles.yml` (path is hard-coded `out/warehouse.duckdb`, no `warehouse_path` var yet), `transform/models/` (only `.gitkeep`), no `transform/tests/`, no `engine/`.
- Request `.context/proposals/cd-1.md`: check 2 asks for "the ten counties"; check 5 asks for "every edit consumed, on time or late"; check 7 asks for "the count of late events".
- Decision records `.context/proposals/cd-1-*.md` (13 files): each has the five frontmatter keys and `status: proposed`. `core:decision-coverage` is met.
- Deferral register `.context/deferrals/cd-1_deferral-register.md`: G-1 to G-9 rows match the plan text.

Grep results for the plan text:
- `tag` appears at lines 90, 145, 146, 181, 208, 209, 278, and in the MF-3, MF-6 and MF-8 ledgers and commands. The only node given a tag is `mart_edit_windows_5min` (line 278).
- `top 10`, `limit 10` and `ten` do not appear in the Phase 4 or N-7 text. The count of ten is only in the request.
- `DURATION` reaches the engine in no phase text. Cycle-five notes (lines 503-504) defer it to E1.

Not run: DuckDB and dbt are not installed in this environment, so no dbt selection or DuckDB type claim is run. Claims that depend on them are reasoned from the plan and marked unverified.

Round 2 items, status in this plan:

| Round 2 item | Status | Where |
|---|---|---|
| B-1 untagged stream-dependent nodes | Open. No text tags any node except `mart_edit_windows_5min` | Plan lines 44, 90, 145-146, 203-209, 278 |
| C-1 check 7 predicate | Open. Line 216 still says "count of late events"; line 476 changed only check 5 | Lines 216, 476 |
| C-2 explicit casts for money and timestamp | Open | Phase 3 (line 179), MF-3 (lines 265-274) |
| C-3 DURATION path and stream end condition | Open | Lines 208, 503-504 |
| C-4 check 2 cut-off and tie-break test | Partly closed. Tie-break is in N-7 (line 283). `limit 10` is not in Phase 4 (line 186) or in the request-to-view mapping | Lines 186, 283 |
| C-5 Connecticut fallback test | Partly closed. The rule is in N-1 (line 294). No Phase 4 test asserts it | Line 294 |

## Blocking issues

### B-1. A fresh `make build` fails, and `make stream` never refreshes the fact that the window mart reads

Evidence (round 2 B-1, re-checked against the text and the skeleton):
- `make build` runs `dbt build --exclude tag:stream` (G-9, line 90; Phase 6, line 208). Phase 3 exit (line 181) uses the same command.
- Only `mart_edit_windows_5min` carries the tag `stream` (line 278). The stream source, its staging models, `fct_edit` (line 203), `late_events` (line 204), `window_build_state` (MF-6, line 338), and the check 5 to 7 views (lines 216-218) carry no tag.
- Those untagged nodes read `lake/stream_events/`. That folder exists only after `make stream`. `lake/` is gitignored (`.gitignore`), and the grader removes it before grading. `dbt build --exclude tag:stream` does not remove untagged nodes, so they run and fail on the missing Parquet path. Success signal 1 (line 39) fails on a fresh checkout.
- dbt `--select tag:stream` does not add upstream nodes. `make stream` therefore does not rebuild the untagged `fct_edit`. The window mart and `window_build_state` (computed from `fct_edit`, MF-6 line 339) read a stale fact. The end-to-end check at Phase 6 exit (line 212) can pass its file checks and still show stale window output.
- The MF-5 double-build test runs `make build` on a lake with no stream data (line 289). It fails for the same reason.

Required fix:
- Tag every node that reads the stream lake with `stream`: the stream sources, their staging models, `fct_edit`, `late_events`, `window_build_state` (the state post-hook writes it), and the check 5 to 7 views. Name the full tag list in G-9 and in Phase 6.
- Add a test: on an empty `lake/` (no `stream_events/`), `make build` passes. Name it in Phase 3 or Phase 6.
- Add a test: after `make stream`, `fct_edit` is rebuilt in the same run. For example, the `dbt build --select tag:stream` run results list `fct_edit`.

Core rule: none of `core:*` covers this. It is a plan defect against section 1 success signal 1 and against G-9.

## Conditions

### C-1. Name the check 7 predicate

Check 7 (line 216) says "count of late events". `late_events` (line 204) holds the late rows of `fct_edit`, which holds all change types. G-6 counts only `edit` and `new` as edits, and cycle five changed check 5 to match G-6 (line 476), but check 7 was not changed.
Condition: state in Phase 7 and DECISIONS.md whether check 7 counts all late change types or only `edit` and `new`. Add a fixture test with a late `log` event that fixes the answer.

### C-2. Mart contract types need explicit casts (unverified)

Phase 3 (line 179) and MF-3 (lines 265-274) enforce `DECIMAL(18,2)` for money (G-5) and `TIMESTAMP` UTC for `window_start`. The plan does not say the model SQL casts to those types. DuckDB `sum` over `DECIMAL(18,2)` can widen the scale (section 8, line 232, names the division case). A `to_timestamp` result can be timezone-aware.
Condition: each contracted money and timestamp column gets an explicit `cast(... as DECIMAL(18,2))` or `cast(... as TIMESTAMP)` in the model SQL. The Phase 3 contract test reads the column types.

### C-3. The DURATION path and the stream end condition are not named

`make stream` requires `DURATION` (line 208). Cycle five defers the path to E1 (lines 503-504). The plan does not name the CLI argument or YAML key that carries it to the engine. The end condition of `transform/tests/fixtures/pipelines/stream_test.yml` (the fake SSE server closes the stream, or a duration key) is not named either.
Condition: name the key or argument, and the end condition the test relies on, in Phase 5 or Phase 6.

### C-4. Check 2 top-ten cut and its tie-break are not in the view text

The request asks for "the ten counties" (check 2). N-7 (line 283) gives the inclusion rule and the tie-break by county FIPS ascending. Phase 4 (line 186) says the view "ranks" counties with no cut-off.
Condition: state `limit 10` in Phase 4 and in `oracle_map.yml`, and add a fixture test for the tie-break.

### C-5. Connecticut fallback needs a test that matches the logged rule

The 2024 census file has nine Connecticut planning-region rows under SUMLEV 050. The 2021 file has eight county rows (09001 to 09015). Under N-1 (line 294) all eight Connecticut counties take `POPESTIMATE2021`. No Phase 4 test asserts this, so check 2 mixes vintages inside one state without a test.
Condition: add a Phase 4 fixture test that asserts the Connecticut counties take the 2021 value. Name the eight counties in DECISIONS.md.

### C-6. `make stream` must create the stream lake folders on a fresh checkout

`lake/` is removed before grading (`.gitignore` comment). The plan does not say that the engine creates `lake/stream_events/_tmp/` and `lake/stream_events/` on first run. The `parquet_stream` sink (Phase 5, line 196) writes into `_tmp/` first, so a missing folder fails the first commit.
Condition: state in Phase 5 that the sink creates both folders, and add a test that runs the sink against a missing `lake/`.

## Adversarial scenarios

| Scenario | Handled? | Evidence |
|---|---|---|
| S1. Fresh clone, `make build` before any `make stream` | No | B-1. Untagged stream nodes read a lake that does not exist yet (`.gitignore`, plan lines 203-218, 278). |
| S2. `make stream` after a fact change, with `fct_edit` untagged | No | B-1. `--select tag:stream` does not select upstream nodes, so the window mart reads a fact that `make stream` did not rebuild. |
| S3. Crash between the micro-batch tmp write and the `os.replace` | Yes | Footer is the commit (line 124). Restart reads the highest committed batch id and deletes `_tmp/` (line 297). Phase 5 crash test (line 197). |
| S4. Redelivered event after reconnect, replay ignores `Last-Event-ID` | Yes | Dedupe on `meta.id` against all committed ids (line 300). Risks section (line 230) names the fallback. The cost is a full scan, accepted at trial volume. |
| S5. Late event at the boundary, with an earlier same-batch arrival | Yes | MF-1 (lines 246-254), including `test_late_uses_max_including_same_batch` and the boundary case. |
| S6. Window mart after a restart, with on-time events in the same batch | Yes | MF-6 algebra (lines 334-336) holds: an on-time event has `window_start >= max_before - 15 min`, so every unbuilt batch starts at or after L. Tests at lines 352-355. Failure injection at lines 473-475. |
| S7. First build with no state row, or mart present and state absent | Yes | MF-8 (lines 398-405) and `test_window_first_build_full_refresh` cases (a) and (b). |
| S8. Phase 6 tests write to the real stream lake | Yes | MF-10 (lines 452-461) and `test_phase6_run_leaves_real_stream_lake_unchanged`. |
| S9. Second run of the same Phase 6 fixture dedupes against the first | Yes, in a note | Cycle-five notes, line 505. The reset is not a named test step. |
| S10. Mart contract on money and timestamp columns | Unverified | C-2. DuckDB not installed. |
| S11. Check 7 counts late `log` and `categorize` events | Not stated | C-1. |
| S12. `make stream DURATION=<s>` where the replay ends early | Partly | G-9 (line 90): engine exits 0 and dbt still runs. The DURATION path is not named (C-3). |
| S13. Check 2 ties and the county cut | Partly | N-7 gives the tie-break. No `limit 10` in the view text (C-4). |
| S14. Fresh checkout, `make stream` with no `lake/` folder | No | C-6. The sink's first write goes to a folder the plan never creates. |

## Trade-offs

- The window refresh reads the whole fact from L on each run (MF-6). This is simpler and correct, and it is not a pure delta. The cost grows with the lake. Accepted for trial volume.
- Dedupe scans all committed `meta.id` values on each batch (line 300). It does not scale. Accepted by the plan.
- The stream position lives in the Parquet footer. Its atomicity depends on `os.replace` on the same filesystem. `_tmp/` lives under `lake/`, so this holds.
- Section 1 success signal 1 is the only success signal that a fresh checkout tests end to end. B-1 blocks it. Tagging every stream node (B-1) is the smallest fix.

Verdict: REQUEST CHANGES
