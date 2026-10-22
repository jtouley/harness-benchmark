RUN_BY_SKILL: de-adversarial-reviewer
Mode: plan-gate
Pipeline-Run: 0f84b2cc-3cf4-4553-b890-6f79e87e0cd2

Ticket: cd-1
Input: .context/plans/cd-1-pipeline.plan.md (sha256 029d83d41d80f686a2a64ac15f2ec36ffe663bf7f133e07bd9982b18067519ae, matches the input hash)
Packet sha256: 452fdefd83975acf0aeeffd52e7778eeda43db752edf70905fed5104e2dd8f3a (not recomputed by this reviewer; the packet was not in the files read)
Round: 2 (`adversarial_cd-1-pipeline.md` existed; no `_r*` file existed)
Prior round: `adversarial_cd-1-pipeline.md` (round 1, REQUEST CHANGES, plan sha256 d19f6f11705f)

## Verification notes

- Plan read in full (about 684 lines). The body is still followed by six stacked update sections (cycles 1 to 5, and "Plan update 2026-10-21 (P6 round 1)"). Later "Replaces" lines win over earlier text.
- Round 1 items: B-1 and B-2 and C-1 to C-4 are each applied in the P6 round 1 update section (lines 582 to 672). Checked by reading the text, not by running anything.
- Session: `pipeline_run_id` 0f84b2cc-3cf4-4553-b890-6f79e87e0cd2 from `.context/sessions/by-worktree/dd962f6cc1983ba4.json`. Matches the plan header.
- `.context/architecture-review-notice.json`: P5 skipped `core:dependency-direction` and `core:boundary-integrity` (`layer_map` empty). This review does not rely on them.
- `core:decision-coverage`: the proposal `cd-1-stream-dedup-resume.md` is `status: proposed` with the five keys. The other proposals were checked in round 1 and were not changed in a way that matters here. `core:decision-coverage` passes.
- Replay probe: `GET http://localhost:8099/v2/stream/recentchange` with `Accept: text/event-stream` returns SSE events. The `id:` line is a JSON array of objects (`topic`, `partition`, `offset`/`timestamp`), not a single integer. `GET /` returns 404. I did not test `Last-Event-ID`, and I did not test whether two connections see the same events.
- Config: `references/cadence.config.schema.json` defines `adversarial_cycles` (minimum 1, lower is stricter). The plan says the P6 limit is three cycles. I did not resolve the active config, so the limit is unverified.
- Not run: no dbt build, no pytest, no stream run of the engine (none exists yet).

## Blocking issues

### B-1. The `max_events` count adds two sets that can overlap

The B-1 choice in the P6 round 1 update says the count is "the `meta_id` values in the batch files that the manifest lists, plus the distinct ids this process has yielded". The two terms overlap. Under the dedup-only resume path of C-3 (no `Last-Event-ID`), the replay starts from the beginning. The resumed process then yields the 500 ids that are already in the manifest. Those are distinct inside the process, so they are counted again. The run stops early, with fewer than N new ids landed, and the test still reads as "stop reason `max_events`".

The sentence "A re-delivered id does not count" does not fix this, because a re-delivered id is not the same as a manifest id that is yielded again by a new process.

Fix: define the count as the cardinality of a set: `|manifest meta_id set ∪ ids yielded by this process|`. Then state the expected new-id count for the resumed run as N minus the committed count at interruption (see B-2). Add a red test for the path-2 case: a replay that restarts from the beginning, with 500 landed ids, must land N - 500 new ids and stop with `max_events`.

Rules: `core:implement` (a test whose assertion is not decidable cannot be red for the right reason).

### B-2. The resumed-run assertion assumes the interrupt lands exactly at 500

The B-1 Acceptance 3 text says: "The harness sends SIGTERM to the first process after its manifest commit of the 500th distinct id." Then: "the resumed process ... lands N - 500 new ids."

Phase 5 (sink) buffers events and writes a micro-batch at 500 events or 5 seconds. The source reads ahead into that buffer. The B-1 SIGTERM rule says "On SIGTERM the sink flushes its buffer, commits the manifest, logs `interrupted` and exits 0." So events read after the 500th id, but before the signal, are committed by the interrupted process. The committed count at interruption is then 500 plus some number that depends on timing, not exactly 500. The resumed run then lands N minus that number, and the assertion fails for a reason outside the code.

Fix: the harness reads the committed count from `lake/_state/stream_manifest.json` after the interrupted process exits, and asserts the resumed run lands N minus that count. Or the harness pauses the source before it sends SIGTERM, so the count is exact. Name the choice in the plan.

Rules: `core:implement` (the red test must fail for the right reason).

### B-3. "The same replay window" is not defined for the live replay

Acceptance 3 and the B-1 text require the interrupted-and-resumed run and the uninterrupted run to produce the same `meta_id` set, "over the same replay window". The plan does not say what defines the window. The probe shows a live SSE feed whose events carry their own `dt` and `timestamp`, and whose `id` is a composite JSON array. The plan does not say that the feed:

- returns the same events to two connections over the same time range (no clock-based window), and
- honors `Last-Event-ID` with the composite id as an opaque string.

C-3 (the live check) would test the second point. It does not test the first. C-4 records a count and a rate, which does not fix the window either. Without a fixed window, the set-equality assertion in Acceptance 3 and `tests/test_stream_e2e.py` cannot be decided.

Fix: name the window (a recorded fixture of the replay, or a replay start parameter the server accepts). Add the check to C-3: two connections over the same window return the same first 2000 `meta_id` values, and a reconnect with the 500th composite id returns the 501st event. The result goes to `.context/proposals/cd-1-stream-dedup-resume.md` before Phase 5 starts.

Rules: `core:implement`, and the plan's own rule that Acceptance 3 is a set equality.

## Conditions

### C-1. The lake scope in MF-4 does not cover the stream tables

MF-4 and the cycle 2 MF-4 test say the lake holds only the four source tables, and `tests/test_lake_tables.py` checks that the folder names under `lake/` equal the four batch tables. Phase 5 writes `lake/stream_recentchange/` and `lake/_state/stream_manifest.json` under the same `lake/` root. The test runs on a batch fixture pipeline, so it passes, but the stated rule ("lake holds only the four source tables") is false once the stream runs. Fix: state in MF-4 that the rule covers the batch landing, and name the stream tables and `_state/` as the stream's lake scope. Or move the stream state to a separate path.

### C-2. The P6 cycle limit is not verified

The plan says "P6 is below its limit (three cycles)". The schema defines `adversarial_cycles` (default and value are in the active config, not read here). Before the orchestrator runs round 3, it should resolve the config (`cadence_config.py resolve`) and record `adversarial_cycles` in the plan update. If the limit is one, this round is the last and the verdict must be carried, not applied.

## Adversarial scenarios

1. Dedup-only resume (C-3, path 2) double-counts the landed ids against `max_events`. Handled? No. Evidence: B-1 choice sentence ("plus the distinct ids this process has yielded"); C-3 path 2 ("the replay starts again from the beginning").
2. SIGTERM after the 500th id commits more than 500 ids. Handled? No. Evidence: B-2; Phase 5 sink buffer (500 events or 5 seconds); B-1 SIGTERM rule (flush, then commit).
3. dbt reads an orphan batch file after a crash. Handled? Yes. Evidence: B-2 rule (`stg_recentchange` reads only manifest-listed files) and red test `transform/tests/test_orphan_batch_excluded.sql`.
4. Population summed across agency and month rows. Handled? Yes. Evidence: C-2 (`population_2024` not additive); test `transform/tests/test_population_not_additive.sql`.
5. Connecticut counted twice (2024 planning regions plus 2021 counties). Handled? Yes. Evidence: MF-9 and MF-10 rules, tests `test_population_no_double_count.sql` and `test_connecticut_planning_region.sql`.
6. Territory places with no population rows (states 60, 66, 69, 72, 78). Handled? Yes. Evidence: MF-11 rule and `transform/tests/test_territory_places.sql`.
7. Publish crash in any swap state. Handled? Yes. Evidence: MF-6 states P1 to P3 and S1 to S3, plus N-5 and `tests/test_publish_states.py`.
8. Replay too short for N events before the 600 s cap. Handled? Partly. Evidence: C-4 requires a recorded count and rate in `DECISIONS.md`. The live run has not happened.
9. Replay does not honor `Last-Event-ID`. Handled? Partly. Evidence: C-3 path 2 covers it, but the path-2 count is wrong (scenario 1).
10. Two connections to the replay see different events (live window). Handled? No. Evidence: B-3; the probe shows a live feed with its own timestamps.
11. Stream state in `lake/` against the MF-4 "four tables" rule. Handled? No. Evidence: C-1.

## Trade-offs

- Keeping the dedup and the publish rules in the engine keeps the lake and the position consistent. The cost is that dbt must read the manifest (B-2), which couples the stages.
- Dropping the Connecticut planning regions and the territory counties into `UNKNOWN` keeps the totals exact, but makes county rankings incomplete for those places. `DECISIONS.md` must say so (MF-10, MF-11).
- The 2021 vintage for the eight Connecticut counties (MF-9) is the only county data available. The `population_2024` column then holds a 2021 figure for them, and `population_as_of` shows it.

Verdict: REQUEST CHANGES
