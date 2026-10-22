RUN_BY_SKILL: de-adversarial-reviewer
Mode: plan-gate
Pipeline-Run: 0f84b2cc-3cf4-4553-b890-6f79e87e0cd2

Ticket: cd-1
Input: .context/plans/cd-1-pipeline.plan.md (sha256 d86dc30b133bd822269a0dec17f650c8d1a2b2201d2e380662635f4d426e3979, matches the input hash)
Packet sha256: eebec79323c0956dac8ff91afd5c9bec12dd02643dd4ef091e94d65469a55588 (not recomputed by this reviewer; the packet file was not in the files read)
Round: 3 (`adversarial_cd-1-pipeline.md` and `adversarial_cd-1-pipeline_r2.md` existed; this is the last P6 round)
Prior round: `adversarial_cd-1-pipeline_r2.md` (round 2, REQUEST CHANGES, plan sha256 029d83d41d80...)

## Verification notes

- Plan read in full (754 lines), including the round 2 update (lines 685 to 754). The round 2 items B-1, B-2, B-3, C-1 and C-2 are each stated as applied. Checked by reading the text.
- Session: `pipeline_run_id` 0f84b2cc-3cf4-4553-b890-6f79e87e0cd2 in `.context/sessions/by-worktree/dd962f6cc1983ba4.json`. Matches the plan header.
- Limits: `python3 -I scripts/cadence_config.py resolve` in the repo gives `adversarial_cycles` = 3 and `plan_review_cycles` = 5, both `[default]`, no project or user layer. The round 2 condition C-2 is verified. Round 3 is the last P6 round.
- `core:decision-coverage`: `.context/proposals/cd-1-stream-dedup-resume.md` and the other proposals are present. Not re-audited in this round. Not a blocker here.
- Live probe, one run each, 6 s per connection, `GET http://localhost:8099/v2/stream/recentchange` with `Accept: text/event-stream`:
  - Two fresh connections return the same first 2000 distinct `meta.id` values in the same order (B-3 check (a) holds for this replay, on this run).
  - The SSE block order is `event:`, `id:`, `data:`. The `id:` value is a JSON array of `{topic, partition, timestamp|offset}` objects, as the round 2 report said.
  - A reconnect with `Last-Event-ID` set to the `id:` line of the 500th distinct event returns, as its first event, the 500th event again (the same `meta.id`), not the 501st. This contradicts B-3 check (b) as written. See B-1.
  - Only one reconnect was tested, over 6 s. The probe does not show the behaviour over longer runs or at other positions.
- Not run: no `dbt build`, no `pytest`, no stream run of the engine (none exists yet). No live run of the full replay window or the `DURATION=600` cap (C-4 is not yet measured).

## Blocking issues

### B-1. B-3 check (b) expects the 501st event after `Last-Event-ID`; the replay re-sends the 500th

Round 2 B-3 (b) says a reconnect with `Last-Event-ID` set to the 500th id "returns the 501st event first", and that "G-1 holds with this reading". The probe above shows the server re-sends the event named by `Last-Event-ID`. The resume is inclusive.

Effect on the plan:
- Check (b) as written will fail on the real server. Recorded as a result, it would be a false negative, and the plan would then pick the wrong path under C-3.
- The Phase 5 red test (`tests/test_stream_resume.py`, "expects `Last-Event-ID` = id of event 500 ... no duplicates and no gaps") does not say which event the reconnect must start with. A test that expects the 501st would be red for the wrong reason (core:implement).
- Exactness still holds on the inclusive reading, because the landed-id index (MF-2) drops the re-sent 500th `meta.id` in the resumed process. The B-1 union count also still gives `max_events - K` new ids, since the re-sent id is in M.

Fix: change B-3 (b) and C-3 to: "a reconnect with `Last-Event-ID` set to the 500th id returns the 500th event first (inclusive), and the engine drops it by `meta.id` (MF-2)". Make the Phase 5 red test assert that the re-sent event lands once and no event is lost, not that the first received event is the 501st. Record the observed inclusive behaviour in `.context/proposals/cd-1-stream-dedup-resume.md` before Phase 5. Also state in G-1 that the resume position is inclusive.

Rules: `core:implement` (the red test must fail for the right reason; an assertion about the 501st cannot be decided against this server).

## Conditions

### C-1. `N` is needed before Phase 5 but is set after it

The B-3 fallback says that when check (a) fails, the harness captures "the first N events once" into `tests/fixtures/replay_window.jsonl` at the Phase 5 entry step. C-4 sets N "before Phase 7" from a live run. So the fallback has no value of N at the time it runs. The B-2 (round 2) assertion `K >= 500` and the Acceptance 3 `max_events` also use N.

Fix: fix the window size as a constant, for example `WINDOW = 2000`, and state that `max_events` = min(WINDOW, recorded distinct count from C-4). Name this in the proposal. The probe above gives about 2000 distinct events in under 6 s, so the cap is not expected to bind. C-4 still has to record the real count and rate.

### C-2. The C-3 result must be recorded from the full check, not from this probe

This review ran one 6 s probe on each check. It is evidence for the reviewer, not for the plan's proposal record. The plan's C-3 says the check result goes to `.context/proposals/cd-1-stream-dedup-resume.md` and `DECISIONS.md` before Phase 5. The author must run checks (a) and (b) as the plan defines them, with the corrected expectation from B-1, and write the observed result there.

## Adversarial scenarios

1. Dedup-only resume (C-3 path 2) double-counts landed ids against `max_events`. Handled? Yes. Evidence: B-1 (round 2) union count `|M ∪ Y|`; test `tests/test_stream_resume.py::test_restart_from_beginning_counts_union` (K = 500, `max_events` = 2000 gives 1500 new ids).
2. SIGTERM after the 500th id commits more than 500 ids. Handled? Yes. Evidence: B-2 (round 2): K is read from the manifest after the interrupted process exits, and the resumed run lands `N - K`.
3. dbt reads an orphan batch file after a crash. Handled? Yes. Evidence: round 1 B-2; `transform/tests/test_orphan_batch_excluded.sql`.
4. Population summed across agency and month rows. Handled? Yes. Evidence: C-2 (round 1); `transform/tests/test_population_not_additive.sql`.
5. Connecticut counted twice (2024 planning regions and 2021 counties). Handled? Yes. Evidence: MF-9 and MF-10; `test_population_no_double_count.sql` and `test_connecticut_planning_region.sql`.
6. Territory places with no population rows. Handled? Yes. Evidence: MF-11; `transform/tests/test_territory_places.sql`.
7. Publish crash in any swap state. Handled? Yes. Evidence: MF-6 (P1 to P3, S1 to S3); `tests/test_publish_states.py`.
8. Replay too short for N events before the 600 s cap. Handled? Yes on this probe, not yet on the plan's record. Evidence: the probe gave 2000 distinct ids in under 6 s. C-4 still has to record the live count and rate in `DECISIONS.md`.
9. Replay does not honor `Last-Event-ID`. Handled? Yes for the engine, No for the plan's text. Evidence: the probe shows the server honours it, but inclusively. Plan check (b) expects the 501st, so the plan's expectation is wrong (B-1).
10. Two connections to the replay see different events. Handled? Yes on this probe. Evidence: two connections gave the same first 2000 distinct `meta.id` values. The plan still has to record check (a) (B-3).
11. Stream state in `lake/` against the MF-4 "four tables" rule. Handled? Yes. Evidence: C-1 (round 2): the stream scope is `lake/stream_recentchange/` and `lake/_state/`; `tests/test_lake_tables.py` subset test.
12. The inclusive resume re-sends the 500th event and the engine lands it twice. Handled? Yes, by dedup. Evidence: MF-2 (landed-id index covers every committed batch file). Not yet tested against the inclusive reading (see B-1).
13. The fallback capture needs N before N is set. Handled? No. Evidence: C-1 above.

## Trade-offs

- Keeping dedup and publish rules in the engine keeps lake and position consistent. The cost is that dbt reads the manifest (round 1 B-2), which couples the stages.
- Dropping the Connecticut planning regions and territory counties into `UNKNOWN` keeps totals exact, but county rankings are incomplete for those places. `DECISIONS.md` must say so (MF-10, MF-11).
- The 2021 vintage for the eight Connecticut counties (MF-9) is the only county data available. `population_2024` then holds a 2021 figure for them, and `population_as_of` shows it.
- Relying on a dedup key instead of exact resume keeps Acceptance 3 exact even if the server's resume is inclusive. The cost is one dropped re-delivery per resume.

Verdict: REQUEST CHANGES
