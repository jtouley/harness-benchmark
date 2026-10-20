RUN_BY_COMMAND: pr-review-local
Last reviewed commit: aefc53ecf28e2390c1f876b8a5388e7c87dbbcd5

# PR review: local (gh-1-pipeline)

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)

Branch: `feature/gh-1-pipeline`. Base: `9c4e037` (merge-base with `origin/main`).
Head: `aefc53e`. Diff: 49 files, +2185, -2. PR text: `outputs/PR.md` (no E4 record names a `PR: local:` path).
Spec: `.context/issues/gh-1.md`. Plan: `.context/plans/gh-1-pipeline.plan.md`.

Verification ran in a copy of the head (`git archive`), not in the user's tree.
Scratch files: `scratchpad/review/` (build logs, probes, `late_check.py`).

Verdict: CHANGES REQUESTED. Five must-fix items. Two nits.

## Summary

- `make build` passes and is idempotent. Full refresh of the stream marts gives the same output.
- The batch half is sound on the checks I ran. Reconciliation and oracle tests pass.
- The stream consumer stops at event 15,839. The replay sends a malformed data line there. The consumer treats it as a disconnect. Every resume hits it again. The PR records this as an open risk. It is a consumer defect that the fix can remove (MF-1).
- Five must-fix items: MF-1 to MF-5. The fix for MF-1 is an author decision (see Design choices).

## Must-fix

### MF-1 Stream consumer stalls at event 15,839

The consumer stops after 15,839 events. The replay has more.

- Cause: `pipeline/sse.py` raises `Disconnected` on a data line that does not parse. `pipeline/stream.py` then resumes from the last good id. The resume starts about 19 events earlier. It passes the same malformed line again. The loop repeats.
- The replay does not close the connection at that line. The bytes after it continue on the same connection. Skipping the one bad line reaches the rest of the replay (see Reproductions R7 and R8).
- The PR text and `DECISIONS.md` D12 and D32 say each connection closes at event 15,839. The raw curl capture contradicts this (MF-2).
- Test gap: `pipeline/tests/fake_replay.py` drops only connection 1 (`connection_number == 1`). No test covers a cut that repeats on every resume. `test_drop_then_resume_counts_each_event_once` passes with the defect present.
- Impact: checks 5, 6 and 7 use 15,837 of the events the replay sends (about 21,500 or more). Check 5 and check 7 values are wrong for the full capture.
- Required: pick a handling rule for a malformed data line (see Design choices). Add a test where the cut repeats on each resume. Re-run `make stream` and report the new count.

### MF-2 Documentation states a replay behavior that the capture contradicts

- `DECISIONS.md` D12: "The replay cuts each connection in the same place." D32: "Each connection stops at the same point."
- Evidence against: R6 (a raw curl read). Event 15,840 arrives after the malformed line on the same connection. The connection stays open to at least 21,503 data lines.
- `PR.md` evidence item 3 says `make stream DURATION=60` "consumes the replay." It lands 15,839 events. Correct the claim after MF-1 is decided.

### MF-3 `late_events` has no enforced model contract

- Spec (`gh-1.md`, Architecture, Models): "Each mart has a dbt model contract (column names and types enforced)."
- `transform/models/marts/_marts.yml` has `contract: enforced: true` on four models: `mart_fy2024_award_net`, `mart_fy2024_monthly_county_agency`, `view_fy2024_county_per_person_top10`, `mart_edit_window_5min`.
- `late_events` (a check object, read by check 7) has columns and tests but no contract. No entry in `DECISIONS.md` explains the gap.
- Required: add `contract: enforced: true` and the column types for `late_events`.

### MF-4 Top-10 view drops ranked counties that have no name row

- `transform/models/marts/view_fy2024_county_per_person_top10.sql` ranks counties, then inner-joins `stg_census_county` for names. The rank is computed before the join.
- `stg_census_county` reads the 2024 file. That file has no row for the eight Connecticut counties that use the 2021 fallback (`int_county_population`). Those counties have a population and FY2024 spend, but no name.
- Current data: no fallback county ranks in the top ten. The best one ranks 119 (`09003`). The view shows ranks 1 to 10 with no gap (R9). This is latent.
- Impact if a fallback county ranks in the top ten: the view returns fewer than ten rows with a gap in `county_rank`. Nothing fails.
- Required: take names from a source that covers the fallback counties, or join names before ranking. Add a dbt test that `county_rank` is 1 to 10 with no gaps and that every row has a name.

### MF-5 Dlt destination setup repeats at three call sites

- `pipeline/batch.py` (line 92) and `pipeline/stream.py` (lines 69 and 108) each build `dlt.destinations.filesystem(bucket_url=..., warn_unsafe_layout_separators=False)`. Stream repeats the `dlt.pipeline(...)` call too.
- `core:dry-extension` (Rule of Three): three callers need the same logic. Add one shared helper, for example `lake_destination(lake_root)` in a shared module.
- Required: extract the helper. Re-run `make build` and the unit tests.

## Nits

### N-1 Silent success when the endpoint is unreachable

- Reproduction R10: `uv run python -m pipeline.stream --duration 3 --url http://127.0.0.1:9/v2/stream` exits 0 with no output. It lands zero events and says nothing.
- Recommend one log line per failed connect, and a non-zero exit when no event lands in the duration.

### N-2 `consume` has more than one job

- `pipeline/stream.py` `consume` reads the stream, deduplicates, batches, lands files, and reconnects. The function is long and hard to test piece by piece. Split reading from landing if MF-1 touches this code.

## Reproductions

Each command ran in `scratchpad/review/head`, a copy of head `aefc53e`.

- R1. `make build` from raw files. Exit 0. `dbt build`: PASS=67, WARN=0, ERROR=0. Build log: `scratchpad/review/build1.log`.
- R2. `make build` twice more, with stream data present. `python -m pipeline.check_marts` output after build 2 and build 3 is identical (`diff` empty). Sorted-row hashes match. Files: `scratchpad/review/check_after_build2.txt`, `check_after_build3.txt`.
- R3. `dbt run --full-refresh --select fct_edit mart_edit_window_5min late_events`. Exit 0. Check output identical to the incremental build (`check_after_full.txt`). Incremental and full builds agree.
- R4. Independent lateness and window oracle, from the lake only (`scratchpad/review/late_check.py`). Raw events 15,839. Canary dropped 2. Counted 15,837. Late 60. Flag mismatches against `fct_edit` 0. On-time windows 614, on-time total 15,777. These match `mart_edit_window_5min` (614 rows, 15,777) and `late_events` (60 rows).
- R5. `python -m unittest discover -s pipeline/tests -t .`. Ran 13 tests, OK.
- R6. Raw SSE capture, no client logic: `curl -sN http://localhost:8099/v2/stream/recentchange` ran 180 s. 21,503 data lines. One line is not valid JSON: line 15,840 (0-based 15,839), "Unterminated string". Lines after it parse. Capture: `scratchpad/review/s2.txt`.
- R7. Consumer path (`scratchpad/review/probe.py`, `probe2.py`). First connection: 15,839 events, then "truncated data line". Resume from the last good id: 19 events (ids 15,820 to 15,838, all seen), then the same error. Six attempts: unique events stay at 15,839.
- R8. Same stream, skip the malformed line only (`scratchpad/review/skipprobe.py`). 120 s. Parsed 21,502 events, all unique. One unparseable line. Stream not ended at the limit.
- R9. Top-10 rank check (SQL on `out/warehouse.duckdb`). Ranks 1 to 12 are all named. Fallback counties `09003` (rank 119) and `09013` (rank 144) have `has_name = false`.
- R10. Offline endpoint: `pipeline.stream --duration 3 --url http://127.0.0.1:9/v2/stream`. Exit 0. No output. Zero events landed.
- R11. Stream restart. Run 1: `pipeline.stream --duration 60` lands 15,839. Run 2: `--duration 3` against an unreachable endpoint (R10) leaves 15,839 rows and 15,839 distinct ids. A full second 60-second run was not made. The restart claim holds only for the stall point, not a full restart.
- R12. Model contracts. Enforced on four models (MF-3). Build log: no contract errors.

## End-to-end walk

- Step 1, `make build` from raw files. Cleared. Exit 0, 67 PASS.
- Step 2, `make build` a second time. Cleared. Same hashes.
- Step 3, `make stream DURATION=60`. Cleared, with the scope limit in MF-1. Lands 15,839.
- Step 4, stop and restart the stream. Partly cleared. No double count at the stall point (R11). A full restart mid-replay was not run.
- Step 5, `make build` after the stream. Cleared. Stream marts match the independent oracle (R4).
- Step 6, `python -m pipeline.check_marts`. Cleared. Prints checks 1 to 7 and hashes.
- Step 7, full refresh of the stream models. Cleared (R3).
- Not run: the `oracle_map.yml` walk against each check. The oracle SQL tests pass in step 1.
- Not run: the batch CLI with a missing raw file. Not verified.

## Adversarial inputs

Stream CLI (`pipeline/stream.py`):

- Missing lake folder. `--init` writes the empty table. `make build` passes from scratch (R1). Cleared.
- Corrupt committed file. `quarantine_unreadable` moves it. The kill test passes (`test_kill_during_flush_loses_and_duplicates_nothing`). Cleared.
- Malformed data line from the replay. Stalls the stream (MF-1). Not cleared.
- Duplicate `meta.id` on resume. Stored once (`test_duplicate_meta_id_is_stored_once`, R11). Cleared.
- Restart after a stop. No double count at the stall point (R11). Partly cleared. Mid-replay restart not run.
- Canary event. Stored in the lake, dropped in staging (D23). Cleared.
- Offline host. Exit 0, no output (N-1). Not cleared (nit).
- Missing `--duration`. Exits non-zero (`test_missing_duration_exits_nonzero`). Cleared.
- Another ticket's leftovers. Not applicable: the lake keys on `meta.id` (UUID), not a ticket token.
- Adjacent id (`cd-1` and `cd-12`). Not applicable: no ticket ids in the data path.
- Workspace that never ran Cadence. Not applicable to this change.

Batch CLI (`pipeline/batch.py`):

- Re-run on existing lake. `replace` write disposition. Cleared by R2.
- Missing raw file. Not run. Not verified.

## Contracts

Each item below contradicts written design. Each is a decision for the author. None is a must-fix here.

- C-1. Stream marts are not `external`. The spec says "Marts are materialized as Parquet with dbt-duckdb's external materialization" (`gh-1.md`, Stack). `fct_edit` and `mart_edit_window_5min` use `incremental` plus a post-hook `copy`. `DECISIONS.md` D24 and D25 give the reason: the external writer adds a NULL row to an empty result. Accept or change.
- C-2. Canary events are dropped from `fct_edit`. The spec says check 5 "counts every edit consumed." Canary events are not edits. `DECISIONS.md` D23 records the choice. Accept.
- C-3. Money uses place of performance, not recipient location. The spec is silent. `DECISIONS.md` D2 records the choice. Accept.
- C-4. The 2021 population fallback for eight Connecticut counties. This matches Amendment A, which allows the latest earlier estimate. `DECISIONS.md` D10 and D17 record it. Accept.
- C-5. The check 6 window uses `wiki = 'enwiki'`. The spec says `en.wikipedia.org`. `DECISIONS.md` D29 records the mapping. Accept.

## Design choices

MF-1 has more than one reasonable fix.

Scenario matrix (expected results from the spec):

- S1. Connection drops once mid-line, then resumes. Expected: every event once. Existing test covers it.
- S2. Malformed line on a connection that keeps going. Expected: the rest of the replay arrives. Currently fails (R7). Skip-line fix passes (R8).
- S3. Cut that repeats on every resume at the same event. Expected: no infinite loop; the consumer makes progress or stops with an error. Currently loops with no progress.
- S4. Unreachable endpoint. Expected: non-zero exit or a log line (N-1).

Options. Not built or scored in worktrees for this review. Scored by probe only.

- Option A (simple): on a malformed data line, log it, store the raw text and sse_id in a rejects file, and keep reading the same connection. Covers S1, S2, S3 (no reconnect loop). Diff: about 15 lines in `sse.py` and `stream.py`. Cost: one event (the malformed one) is recorded as rejected, not counted. Matches the replay evidence in R6 and R8.
- Option B (medium): keep `Disconnected` on a malformed line. Track the resume point. After two resumes that stop at the same sse_id, skip that event and reconnect. Covers S1, S2, S3. Diff: about 30 lines. More state to test.
- Option C (over-engineered): quarantine the malformed event and fetch a fresh copy from the replay with a wider lookback. Fails on this replay (R7): the replay sends the same malformed line on every connection. Not recommended.

Recommendation: Option A for this replay, with the rejects file counted in the report. Add a test with the repeating cut (S3). The author picks the option in the fix phase.

## Scope

- Title: "Build the federal spend and Wikipedia edit pipeline (gh-1)". It has no type prefix. The spec does not require one.
- Size: 49 files, +2185 lines, -2 lines. Breakdown: `pipeline/` 1,000 lines of Python plus tests, `transform/` models and tests, `DECISIONS.md` (140 lines), `oracle_map.yml`.
- Docs and code in one change: `DECISIONS.md` and `oracle_map.yml` are spec outputs. They do not need a split.
- Recommend no split. Recommend fixing MF-2 text before the PR opens.

## Lookback

Failure classes behind the must-fix items:

- Class 1, protocol-level fault treated as a transport fault. A malformed line is handled as a disconnect. A resume that repeats the same fault has no progress check. (MF-1)
- Class 2, test fakes that model only one fault. The fake drops only connection 1. The suite passes with the defect present. (MF-1, test gap)
- Class 3, a join after a rank that silently drops rows. (MF-4)
- Class 4, a stated spec requirement missed on one model. (MF-3)
- Class 5, duplicated setup code added at each call site. (MF-5)
- Class 6, a success exit on no data. (N-1)
- Class 7, a claim in the docs that the evidence contradicts. The author did not re-run the raw capture. (MF-2)

After fixes: not applicable. This review did not change the tree. Re-run the suite and every matrix after the author applies MF-1 to MF-5.

## Reuse and extension

Checked against `core:dry-extension` (`references/architecture-core-rules.md`).

- Shared helpers in use: none exist in the repo. There is no `tests/conftest.py`. The shared module for pipeline tests is `pipeline/tests/fake_replay.py`.
- Helpers that duplicate an existing one: none in the test files.
- Extension point added or used: none. The consumer reads no config key and adds no `stages.json` field.

Measurement lists (changed test files: `pipeline/tests/test_batch.py`, `test_dbt_guards.py`, `test_marts_published.py`, `test_stream.py`, `fake_replay.py`, `stream_kill.py`; plus `transform/tests/*.sql`):

- `helpers_reimplemented`: none
- `helpers_reused`:
  - `pipeline/tests/test_stream.py`: `FakeReplay`, `make_events` from `pipeline/tests/fake_replay.py`
  - `pipeline/tests/test_stream.py`: `consume` from `pipeline/stream.py`
  - `pipeline/tests/stream_kill.py`: `TABLE`, `DATASET`, `consume`, `land_batch` from `pipeline/stream.py`
- `thin_files`: none. `pipeline/tests/test_marts_published.py` has one test. No other test file checks the published `out/marts/` folders, so it is not a duplicate.

Net change in test lines: about 499 lines added and none removed. `pipeline/tests/` 363 lines. `transform/tests/` 136 lines. Dbt unit tests in the `_*.yml` files are not counted.

Duplication added by this change: the dlt destination setup in MF-5.
