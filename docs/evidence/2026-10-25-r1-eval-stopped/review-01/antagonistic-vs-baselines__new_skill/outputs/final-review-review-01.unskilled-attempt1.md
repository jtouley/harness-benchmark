# Final review: branch `review` against `base` (review-01)

**Change:** branch `review` (commit c176f99 "Change under review") against `base` (d176e80). 45 files, +2085 / -2.
**Working copy:** `/var/tmp/revieweval/antagonistic-vs-baselines/review-01/new_skill/run-1/repo`
**Inputs:** findings A, B and C; reviewer B's probe script; `build.log`; my own checks in the copy (listed under "What I checked myself").
**Build:** not run again. The build log was read. `dbt ls` (selection only, no build) and the probe script were run. The repo is clean at the end; one temporary edit to a test was reverted.

**Consolidation standard:** the "standard of the consolidation" and "final review" sections of `antagonistic-review/SKILL.md` were not applied. That file sits outside the paths this run may read, so this review uses the structure the three findings files share. If that standard is needed, the consolidation should be re-run with it.

---

## Verdict: CHANGES REQUESTED

All three reviewers reach the same verdict.

- **Batch half (USAspending, Census, sitematrix; marts 1 to 4 and 8):** sound. Recomputed numbers agree with the raw data. The issues are about what the published columns claim, not about the arithmetic.
- **Stream half:** not ready to merge. A malformed event can crash the run. The late-events check never executes. The stream results depend on run history, not on a defined run. Several documented guarantees (flush cadence, stop at DURATION) do not hold.

---

## Blocking

### R1. The stream consumer crashes on malformed input
*Merges A-B3, A-M1, B-2, C-F1, C-F2.*

**Where:** `pipeline/stream_consumer.py`. Line 66 (`raw.decode("utf-8")`). Lines 200 and 206 (`meta.id` and `type` used as set and dict keys). Lines 157-160 (`_read_until` catches only `OSError` around `_connect`). Lines 253-267 (`_field_problem` checks only meta type, length and timestamp).

**Verified by me** with reviewer B's probe script, run against the copy with a local server:

| Input | Result | Rows landed |
|---|---|---|
| Invalid UTF-8 byte in a data line | `UnicodeDecodeError` | none |
| `meta.id = ["x"]` | `TypeError: unhashable type: 'list'` | none |
| `type = ["edit"]` | `TypeError: unhashable type: 'list'` | none |
| Status line `HTTP/1.1 garbage` | `BadStatusLine` | none |
| `namespace = 10**30` | `PipelineStepFailed` at extract | none (the good event in the same batch is lost too) |

Not a crash, but silent: `namespace = "Talk"` lands with namespace NULL and no skip message. `wiki = 123` lands as `"123"`.

This contradicts the `_skip` docstring ("so one bad event does not stop the stream") and DECISIONS.

*Inferred from code, not probed:* `_flush` does not advance the checkpoint when `pipeline.run` raises (lines 241-242). A restart therefore replays from before the bad event, so one poison event can stop the stream on every restart.

**Ask:** validate every field the consumer uses. `meta.id` and `type` must be strings. `namespace` must be an integer in bigint range or null. `wiki` and `server_name` must be strings or null. `bot` must be a boolean. Decode per line and skip on `UnicodeDecodeError`. Catch `(OSError, http.client.HTTPException)` around `_connect`. Add one test per case. Log every skip.

### R2. The late-events check (check 7) never runs
*A-B1 and B-1. C does not mention it.*

**Where:** `transform/tests/test_late_events_count.sql` reads `read_parquet('out/marts/late_events/*.parquet')` with no `ref()`. dbt has no edge to `late_events`, so the `+late_events` selector never reaches the test.

**Verified:**
- The stream build log lists 15 nodes. The singular tests that ran are `test_stream_totals_per_wiki`, `test_top_windows_en_wikipedia` and `test_event_time_utc_is_utc`. `test_late_events_count` does not appear.
- `dbt ls` with the stream selector does not list it.
- **Fix tested:** I changed the `read_parquet` call to `{{ ref('late_events') }}` on a temporary edit. `dbt ls` then lists `open_data_pipeline.test_late_events_count` under the stream selector. I restored the file with `git checkout`, and the repo is clean.

**Not verified:** that the test passes on a real lake. That needs one `make stream` run.

**Ask:** apply the `ref()` change, run `make stream` once, and confirm the test's PASS line in the log. DECISIONS lines 117-120 say three stream tests cover checks 5, 6 and 7. Only two do so far.

### R3. Checks 5 to 7 answer for all landed data, not for a defined run
*A-B2, B-5, C-F5.*

**Where:** `_connect` resumes from the checkpoint and sends `Last-Event-ID` (lines 182-183). `stream_raw` and `stream_events` are appended (lines 224, 233-238). The stream macro `stream_raw_arrivals` reads all of `lake/stream_raw/*.parquet`. No run id is recorded.

**Facts:**
- The build log's stream run is `make stream DURATION=90`, on whatever lake exists.
- DECISIONS cites a 3600 s run on a fresh lake (21,502 events, 3,603 s span). Its log is not in the build log.
- Each `make stream` continues the replay where the last one stopped, so the marts hold the union.
- The spec defining "the replayed hour" (A-18) is absent (see M8), so I cannot check which scope it requires.

**Decision needed from the author.** I recommend resetting the `stream_*` tables at the start of `make stream`. That makes the output reproducible and matches "the replayed hour" for one run. The alternative is a run id on each row, with the marts and oracles filtered to it. Either way, the grader's run must be stated.

---

## High

### H1. Flush and deadline are checked only after an accepted event
*A-M4, B-4, C-F3, C-F4.*

**Where:** `_batch_full()` is called only after an accepted event (lines 169-170). `_lines` checks the deadline only between lines, and `readline` can block for `SOCKET_TIMEOUT` (5 s, line 25).

**Verified:**
- Heartbeats only: the flush happened at the deadline, not at the batch age. Reviewer C measured 1.56 s with a 0.2 s batch; reviewer A measured 4.0 s with a 0.5 s batch. Time-based flushing does not work during quiet stretches. I confirmed the code path (lines 169-170), not the timings.
- Silent stream, `DURATION = 0.5`, socket timeout 5.0 s: `run()` returned after **5.52 s** (my probe). Reviewer C measured 5.00 s and reviewer A measured 3.24 s with a 3 s timeout. All are consistent with "overrun by up to one socket timeout".

**Consequence:** DECISIONS line 73 ("flushed every 5 seconds") is false. Events sit in memory until the next event or the deadline. A kill in that window loses them until a replay resends them.

**Ask:** check batch age on every line, including heartbeats and timeouts. Bound each read by `min(socket_timeout, deadline - now)`. Add a flush-latency test and a silent-stream test.

---

## Medium

### M1. Malformed fields are coerced or nulled without a skip
*A-M7 related, B-3, C-F10, A-L3.*

**Verified:** `namespace = "Talk"` lands as NULL with no log. `wiki = 123` lands as `"123"`. Code: `bot` uses `bool(event.get("bot"))` (line 91) for the `bot` column and `event.get("bot") is True` (line 94) for `actor_type`. So `bot = "false"` gives `bot = True` and `actor_type = "human"`. Two columns disagree.

**Impact:** NULL `namespace` is part of the `window_5min` unique key (`window_5min.sql` line 3). NULL keys do not match in an incremental merge, so duplicates are possible. Not reproduced.

**Ask:** apply the R1 validation and log each skip. Derive `bot` and `actor_type` from one value.

### M2. `mart_award_fy2024` publishes an arbitrary place for some awards
*A-M2, B-7, C-F8.*

**Verified:** two awards have transactions in more than one place:
- `ASST_NON_FEL29493424_418`: `09009` and `09170`.
- `ASST_NON_21FXDWY001_485`: state `35` and state `56`.

`mart_award_fy2024.sql` uses `any_value` for `agency_code`, `state_fips` and `county_fips`, and `any_value` has no defined order. `tests/check_rerun.py` line 15 compares only `mart_monthly_obligations`, so a change here is not caught. DECISIONS lines 134-135 ("compares the mart rows and data columns") overstate the check.

**Ask:** choose a deterministic rule (for example, the place of the latest action date, with a tie-break on the transaction key) or drop the place columns from this mart. Extend `check_rerun` to all three batch marts.

### M3. Published population columns hold 2021 values under 2024 names
*A-M3, C-F6.*

**Verified:** `stg_census_counties.sql` line 22 writes the 2021 estimate into `population_2024`, with `population_year = 2021`. `dim_place` keeps `population_year`. `mart_monthly_obligations` exposes `county_population_2024` and `state_population_2024` without a year column. For six Connecticut counties, the value is 2021 under a 2024 name.

**Effect:** check 2 is not affected. Two reviewers recomputed the top ten and no Connecticut county is in it.

**Ask:** add `county_population_year` (and a state equivalent) to the mart and to its `schema.yml` contract. Keep the existing column names, because `oracle_map.yml` check 2 names them.

### M4. DECISIONS undercounts the 2021 fallback
*A-L2, C-F6 (partly), B-12.*

**Verified:** the 2021 file has eight Connecticut county rows with no 2024 row: `09001, 09003, 09005, 09007, 09009, 09011, 09013, 09015`. DECISIONS (lines 46-47, 137) names six. Awards use only the six. `09007` and `09015` still land in `dim_place` with 2021 values. `test_census_fallback_uses_earlier_estimate` checks only `09001`.

**Ask:** correct the DECISIONS wording. Extend the test to all six award codes, and check that the two extra rows carry `population_year = 2021`.

### M5. Oracles share code with the models
*B-6, C-F11, A-M7.*

**Where:**
- The oracles for checks 1 to 4 use `usaspending_raw()`, which staging also uses. A wrong column mapping passes every test.
- `test_top_ten_counties_per_person` takes populations from `dim_place`, a model under test.
- The late rule is written twice (`lateness.py` and `stream_raw_arrivals.sql`). The tests check that the two agree, not that the reading of the spec is right.

**Mitigation:** reviewers B and C each recomputed the top ten from the raw CSVs with no repo SQL, and both got the same ten values. Rank 10 has no tie (11th is 32510 at 37.9291). Reviewer C also fuzzed the macro against a Decimal reference: 23,606 cases, 0 mismatches.

**Ask:** check in the independent recomputed values as fixtures. Or say in DECISIONS which answers are consistency checks only.

### M6. Test suite hygiene
*A-M5, B-11, C-F14.*

- There is no `make test` target.
- `tests/test_rerun.py` runs `make build` twice. Any `unittest` discovery therefore builds the whole pipeline.
- `test_consumer_replayAtLocalUrl` skips silently when the replay is down ("local replay is not running"). The live-replay path is never exercised in a grader without the replay.
- Reviewers ran the unit suite without the rerun test: 48 OK, 1 skipped. I did not rerun it.

**Ask:** add a `make test` target that runs the unit suite without `make build`. Make the rerun check a separate target. Report skips in the log.

### M7. DECISIONS counts and spec references cannot be checked from the tree
*A-M6, B-10, C-"not verified".*

- `spec/` is absent. `oracle_map.yml` and DECISIONS cite `spec/spec.md` and ids such as A-2, A-18, G-22 and N-3. Spec conformance cannot be checked. The code was checked against DECISIONS' paraphrase only.
- The stream figures (21,502 events, 12,876 edits, 3,603 s, about 370 events/s, about 3,200 backward steps) have no run log and no lake in the copy.

**Ask:** include the spec, or a link and version. Attach the log for the 3600 s run, or drop the figures.

### M8. DECISIONS states transaction counts as award counts
*A-M6, C-F13. B reported these as matching.*

**Verified** by recomputing from the eight FY2024 zips, 9,820 transaction rows, 7,918 awards:
- 7,724 and 57 are **transaction** counts (state and no county; neither).
- At award level: **6,007** awards have a transaction with a state and no county. **47** awards have no place in any transaction.

**Ask:** fix the wording. Exact replacement is in the section below.

---

## Low

- **L1. Territories get `state_name = 'UNKNOWN'`.** `dim_place.sql` line 21 coalesces the missing name. The Census files have no rows for states 60, 66, 69, 72 or 78. Those states have 138 FY2024 transactions (72: 75, 66: 25, 78: 15, 69: 12, 60: 11, all verified). `county_name` is NULL for them, while a missing county elsewhere shows `UNKNOWN`. Use a fixed name table, or a distinct label, and make the two columns consistent.
- **L2. Checkpoint can be reset to null.** Line 212 assigns `_pending_last_id = sse_id` even when the event has no `id:` line. The next connection then sends no `Last-Event-ID`. Reproduced by reviewer B. Assign only when the id is not null.
- **L3. `dim_agency` uses `first(agency_name)` with no order.** One name per code in the current data, so no effect now. Use `max()` or order the aggregate.
- **L4. Deprecated test arguments.** `schema.yml` lines 83-84, 107-108 and 155-156 put test arguments at the top level. The build log warns `MissingArgumentsPropertyInGenericTestDeprecation` (3 occurrences). Nest them under `arguments:`.
- **L5. `.gitignore` and `.env` wording.** Line 1 of `.gitignore` says the files are "never committed (the grader removes them first)". A grading reference does not belong in committed code. `read_stream_url` reads the environment, then `.env.example` (lines 50-54). No code loads a `.env` file, so copying the example to `.env` does nothing. Reword, and either document the export or load `.env`.
- **L6. `dim_date` is unused.** Built, but no model or test references it. Verified by grep: only the `schema.yml` description mentions it.
- **L7. `pyarrow` is not declared.** `batch_load.py` and `stream_consumer.py` import it directly. `pyproject.toml` does not list it; it arrives only through `dlt[parquet]`. Declare it.
- **L8. `closed` in sitematrix.** `bool(site.get("closed", False))` would read `""` as open. The current data is boolean (173 true, 900 absent), so this is latent only.
- **L9. Relative paths.** `lake/` and `out/` are relative. `make` runs from the root, so it works, but running dbt from `transform/` breaks.
- **L10. Connecticut mixed geography.** Old county codes use 2021 populations and planning-region codes use 2024 populations side by side. No effect on the top ten. Worth one sentence in the spec answer.
- **L11. Unverified latent risks** (not reproduced by anyone): a partial `stream_raw` load after a flush failure could duplicate rows (A-L8, because `_flush` does not clear pending lists when `pipeline.run` raises). NULL unique-key parts in `window_5min` (see M1).

---

## Reviewer disagreements, resolved

- **Award counts (7,724 / 57):** A and C say these are transactions, and B reported them as matching. Recomputed: transactions. Award-level figures are 6,007 and 47 (M8).
- **Check 7:** A and B flag it as never run. C does not mention it. Confirmed with `dbt ls` (R2).
- **Overrun size:** 3.24 s, 5.00 s and 5.52 s were measured with different socket timeouts. All are consistent with "up to one socket timeout" (H1).
- **Connecticut fallback count:** DECISIONS says six. The 2021 file has eight, and the staging model includes all eight (M4).
- **`closed` (sitematrix):** A calls it a latent risk. C checked the data, which is boolean. Latent only (L8).

---

## What I checked myself

- Read `build.log`: `make build` PASS=26 ERROR=0; `make stream` PASS=15 ERROR=0; no WARN/ERROR lines. Deprecation warning count (3) confirmed.
- Ran reviewer B's probe script against the copy with the repo's `.venv`, `-I`, no build. Results in R1 and H1.
- Ran `dbt ls` for both targets' selectors. Confirmed R2 and that the late-events test is absent from both (`dbt ls` only, no build).
- Tested the R2 `ref()` fix by temporary edit, then `git checkout`. Repo clean afterwards.
- Probed the `namespace = 10**30` crash claim from C. Confirmed (R1).
- Recomputed from the raw zips (no SQL): transaction and award counts, multi-place awards, the eight Connecticut 2021 codes against the nine 2024 planning regions, and the territory transaction counts (M4, M8, L1, R1).
- Confirmed by reading the code: `_batch_full` placement (H1), `bot` coercion (M1), `check_rerun` scope (M2), `population_year` in staging and the mart (M3), `dim_agency`, `dim_date`, `pyproject.toml`, `.gitignore`, `.env` handling.

**Not verified:** mart values (no `out/` or `lake/`), spec conformance (no spec), the stream figures in DECISIONS (no run log, no lake), the rerun check (it runs `make build`), the live-replay test (skipped here), L8 and L11 (not reproduced).

---

## Author actions, in order

1. **R1 and M1.** Validate the fields the consumer uses. Catch `HTTPException` on connect. Decode per line. Add one test per case.
2. **R2.** Apply the `ref()` change to `test_late_events_count.sql`. Run `make stream` once. Confirm the PASS line.
3. **R3.** Decide the stream scope (reset at start of `make stream`, or a run id), and state the graded run.
4. **H1.** Check flush age and the deadline on every line. Bound reads by the remaining time. Add latency and overrun tests.
5. **M2, M3, M4.** Deterministic place rule (or drop the columns). Add `population_year` to the mart and its contract. Extend the census test to six codes.
6. **M5, M6.** Checked-in independent fixtures. A `make test` target. Report skips.
7. **M7, M8, L1 to L11.** Documentation fixes and the low items above.

### Suggested DECISIONS.md replacements (for the author to paste)

- **Lines 41-42:** replace "In the data, 7,724 awards have a state and no county, and 57 have neither." with "In the data, 7,724 FY2024 transactions have a state and no county, and 57 have neither. At award level (7,918 awards), 6,007 have a transaction with a state and no county, and 47 have no place in any transaction."
- **Lines 46-47 and 137:** replace "The six Connecticut codes take their 2021 estimate" with "Eight Connecticut county codes (09001 to 09015, odd numbers) have a 2021 estimate and no 2024 row. Six of them appear in awards; 09007 and 09015 do not."
- **Lines 70-71:** replace "every unique event received, before any filter" with the post-R1 wording, "every unique event that passes field validation".
- **Line 73:** replace "every 5 seconds" with the post-H1 behaviour. Until H1 is fixed, say that a quiet stream is flushed only on the next event or at the deadline.
- **Lines 134-135:** replace "compares the mart rows and data columns" with "compares `mart_monthly_obligations` only; `mart_award_fy2024` is not compared" (until M2 is fixed).
- **Lines 117-120:** keep as is once R2 is fixed and the test runs.
