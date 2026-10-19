RUN_BY_COMMAND: plan-review

**Task:** gh-1
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
**Plan:** `.context/plans/gh-1-pipeline.plan.md` (read in full: base plan, Updates 1 to 4)
**Review cycle:** 5 of 5

Verdict: READY WITH CHANGES

Update 4 closes the cycle-4 items. Checks 1, 2 and 4 have published marts. The dlt start rule names the files it deletes. The dlt state lives in `lake/_dlt/`.

This review found four must-fix items (MF-1 to MF-4). They block E1. This is the fifth review. Do not review again after the plan update. The plan is not edited in this run.

## Must-fix items

### MF-1. Checks 5, 6 and 7 still name warehouse views as answer paths

Plan: Phase 8 names `v_stream_by_wiki_actor` (check 5), `v_top_windows_en_wikipedia` (check 6) and `v_late_event_count` (check 7) as the oracle views. Update 4 MF-1 says a warehouse view is not an answer path. Update 3 MF-2 says check 5 and check 7 read `mart_stream_wiki_actor`.

Ticket: "Anything downstream reads only `out/marts/`."

Problem:
- Check 6 reads `fct_edit`. `fct_edit` is a warehouse table. It is not published under `out/marts/`.
- Update 3 says `mart_edit_windows_5min` covers check 6 with no change. Phase 8 still names the view. Two answer paths are named for check 6, and only one is allowed.
- Checks 5 and 7 name a view in Phase 8 and a mart in Update 3 MF-2. The plan does not say which one applies.
- The ticket does not give the count N for check 6 ("the 5-minute windows with the most edits"). The plan does not set N.

Effect: `oracle_map.yml` (Phase 9) cannot name one answer path for checks 5, 6 and 7. The analyst rule in the ticket fails for check 6.

Fix:
- Check 5: answered by `mart_stream_wiki_actor`, columns `edit_count` and `net_bytes_added`.
- Check 7: answered by `mart_stream_wiki_actor`, the sum of `late_event_count`.
- Check 6: answered by a query over `mart_edit_windows_5min`, filtered on `wiki = 'en.wikipedia.org'`, ordered by `edit_count` descending. Name N in the plan and in `DECISIONS.md`.
- State that `v_stream_by_wiki_actor`, `v_top_windows_en_wikipedia` and `v_late_event_count` are not answer paths. Remove them from the Phase 8 work list.
- Record the choice in `DECISIONS.md` as an extension of Decision 18.

### MF-2. Phase 1 gate has no exit criterion

Plan: Update 4 says the gate test file `tests/test_dlt_stream_gate.py` runs in Phase 1. It decides Option 1 (dlt) or Option 2 (pyarrow) for Phase 6. The Phase 1 exit criteria (lines 84 to 88) do not require the gate test to run. They do not require a result.

Problem:
- The Phase 1 TDD note (line 90) says "No code in this phase." Update 4 says Phase 1 has one code exception, the gate test. The two statements conflict.
- Phase 6 has no entry check on the gate result. The phase can start before the gate runs.

Effect: E1 can start Phase 6 on the dlt path without a passed gate. The stream design depends on facts that the gate has not checked.

Fix:
- Add to the Phase 1 exit criteria: `uv run --with pytest pytest tests/test_dlt_stream_gate.py` runs, and each of the four tests has a recorded result.
- Record the pinned version `dlt[parquet]==1.31.0` and each result in `DECISIONS.md` Decision 16.
- Add to the Phase 6 entry: the stream path follows Option 1 only when all four tests pass. Otherwise it follows Option 2 and Risk R7 is recorded.
- Replace the Phase 1 TDD note (line 90) with a note that names the gate test as the only code in Phase 1.

### MF-3. Test A and Test B do not state the test server behavior per connection

Plan: Test A (Update 2 MF-1 and Update 1 MF-6) says the server ignores `Last-Event-ID`. It also says the server repeats ids 26 to 60 on reconnect. Test B (Update 1 MF-6) says the server closes after id 17, and the consumer reconnects from id 10 and receives ids 11 to 60.

Problem:
- Test A. "Ignores `Last-Event-ID`" and "repeats ids 26 to 60" do not say what the server sends on the second connection. The expected count of 65 rows assumes the server starts at id 26 on the second connection, whatever the header says. The plan does not state that.
- Test B. The expected result needs a server that honors `Last-Event-ID` and starts at id 11. The plan does not say that Test B honors the header. The plan does not say that the server closes after id 17 on the first connection only. If the server closes every connection after id 17, the test never ends.
- Test A2 names "honors `Last-Event-ID`". Test A and Test B do not name a header rule.

Effect: Three test servers have no defined per-connection behavior. An implementer can write a server that passes the count and fails the intent, or the reverse. The Phase 6 exit counts (65, 60, 60) depend on these rules.

Fix: For each of Test A, Test A2 and Test B, state for each connection:
- The event ids sent.
- Whether the server reads `Last-Event-ID`, and the id it starts from.
- When the server closes the connection.

Keep the exit counts. Name the test file that holds the server.

### MF-4. Phase 8 interrupted run has no stop mechanism

Plan: Phase 8 says "Run the full stream path twice with a stop in between on the replay. Compare the check 5 totals with a single uninterrupted run." This is the acceptance test for the stream (Phase 8 TDD note).

Problem:
- `make stream DURATION=<seconds>` stops on time (Update 4 MF-3). Two timed runs on a live replay can consume different event sets. The totals then differ for a reason that is not a bug.
- `STREAM_STOP_AFTER_EVENTS` is for Test A and Test A2 only. Update 4 MF-3 says `make stream DURATION=` does not read it.
- The plan does not state whether the replay at `localhost:8099` honors `Last-Event-ID`. R3 covers the SSE format only. If the replay ignores the header, the interrupted run double counts. The test then fails, and the plan does not say why.
- The plan does not say when the replay ends. An uninterrupted run needs a finite replay to compare with.

Effect: The acceptance test for the stream has no defined input. It can fail or pass for reasons the plan does not name.

Fix:
- Name the stop mechanism for the Phase 8 interrupted run. One option: use the Phase 6 local test server with `STREAM_STOP_AFTER_EVENTS`. Name a second option only if the live replay is used.
- Add a Phase 1 check that records whether the replay honors `Last-Event-ID`. Record the result in `DECISIONS.md`.
- Name the end condition of the replay used for the Phase 8 comparison.

## Notes (not blocking)

- N-1. Risk R7 is named in Update 4 (MF-2 and the Phase 1 gate text) and in the Decisions list. The Risks section has no R7 entry. Add a row to the Risks section with the Option 2 text. Keep the Update 2 MF-2 file rules for Option 2.
- N-2. Phase 2 (line 101) says "Each `make build` replaces the lake folder." Update 2 MF-2 limits the replace to the batch source folders. Update 4 MF-3 governs. Change the base text, or state that Update 4 governs it.
- N-3. The ticket says each mart has a dbt model contract. R1 allows a singular test in place of enforcement. The plan records this as a departure (N-7 of Update 1). The ticket gives no way for E1 to ask. E1 records the choice in `DECISIONS.md` and keeps the ticket rule where dbt-duckdb enforces it.
- N-4. The incremental strategy for `mart_edit_windows_5min` is still not named (cycle 4 N-4). A new event can change an existing window. Name one option before E1: merge on the window key, delete and insert the affected windows, or a full rebuild. The test "equals a direct `GROUP BY` over `fct_edit`" catches a wrong choice.
- N-5. The missing-state message in Update 4 MF-3 starts with `STOPPED:`. The peer contract uses the same word for the one-line return. The message is for the operator. Consider a different first word to avoid confusion.
- N-6. Update 3 N-7 and Update 1 N-7 are different items. Update 4 N-1 keeps both ids. Keep the ids. Do not renumber them.
- N-7. Phase 2 (line 97) says "Pass the file type as a parameter. Do not write two loaders." Update 4 does not change this. No change needed.
- N-8. The Phase 1 gate test checks the pinned `dlt[parquet]==1.31.0` version from `pyproject.toml`. The pin matches. `dbt-core==1.11.6`, `dbt-duckdb==1.11.0` and `duckdb==1.5.6` also match the pins. No change needed.

## Reuse and extension

Checked against `core:dry-extension`. The plan has a `## Reuse and extension` section.

- The repo has no `tests/`, `scripts/`, `shared/` or `pipeline/` folder. The plan's new helpers have no existing copy to reuse. No helper is written twice.
- The single batch reader (Phase 2) and the single late-rule macro (Phase 7) meet the Rule of Three.
- The extension points (source list, dbt variables for the thresholds, `edit_types`) are config or data, not new branches.
- No must-fix item comes from this check.

## Standalone package

- The plan's `ste-lint.py` path uses `$CADENCE_HOME`. It is a peer path. No host path appears in the plan.
- No `core:standalone-package` finding.

## Evidence checked

- Plan read in full: base plan, Update 1, Update 2, Update 3 and Update 4 (694 lines).
- `.context/reviews/plan_gh-1-pipeline.md` (cycle 4) read. Its three must-fix items were checked against Update 4. MF-1 (checks 1, 2, 4) is closed. MF-2 (dlt file rules) is closed. MF-3 (dlt state location) is closed.
- `.context/issues/gh-1.md` read. Checked the checks list, the `out/marts/` rule, the lateness rule, the stack rule and the replay rules against the plan. The check 6 gap (MF-1) came from this check.
- `pyproject.toml` pins `dlt[parquet]==1.31.0`, `dbt-core==1.11.6`, `dbt-duckdb==1.11.0`, `duckdb==1.5.6`. `uv.lock` agrees on `dlt` 1.31.0 and `dbt-duckdb` 1.11.0.
- `Makefile` has only the two stubs. `.gitignore` lists `lake/` and `out/`. `transform/dbt_project.yml` has `test-paths: ["tests"]`.
- The replay at `localhost:8099` was not probed in this run. MF-4 requires Phase 1 to record it.
- dlt's file naming and state location were not run in this environment. Phase 1 gate tests confirm them on the pinned version.

## Decision needed

None for the author. The four must-fix items are plan choices that E1 can record in `DECISIONS.md`.

## Footer

Next step: the orchestrator runs `/plan-update .context/plans/gh-1-pipeline.plan.md` with this review. This is cycle 5 of 5. Do not run another review after that update, per the loop limit.
