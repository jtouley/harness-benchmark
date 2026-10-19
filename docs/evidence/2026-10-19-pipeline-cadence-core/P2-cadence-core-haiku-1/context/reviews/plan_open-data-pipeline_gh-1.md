RUN_BY_COMMAND: plan-review

# Plan review: open-data-pipeline (gh-1), cycle 5

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
**Local ticket:** gh-1, file `.context/issues/gh-1.md`
**Plan:** `.cursor/plans/open-data-pipeline_gh-1.plan.md` (reviewed after `## Plan update 4`)
**Prior review:** `.context/reviews/plan_open-data-pipeline_gh-1.md` (cycle 4, READY WITH CHANGES, MF-1 to MF-3), replaced by this file
**Cycle:** 5 of 5

**Verdict:** READY WITH CHANGES

## Summary

Plan update 4 applies the three cycle 4 must-fix items. The capture and lake dedup order is set (MF-1 of cycle 4). The loss limit is recorded as D11 (MF-2 of cycle 4). The replay start probe is set (MF-3 of cycle 4). The `## Reuse and extension` section still matches the repo.

This review found four new must-fix items. Each one has a fix inside the plan. None needs a new phase. Items MF-1 and MF-2 are a data loss path and an acceptance gap. They block E1.

This is the fifth and last review of the loop. The orchestrator maps each open `MF-n` to a phase under `## Carried review findings`. It does not start another review.

## Must-fix items

### MF-1: an uncommitted event is dropped and never reaches the lake

Update 4 MF-1 writes the capture line before the lake check. Step 1 drops an event whose `meta.id` is already in this run's capture. Two paths put an event in the capture without a lake write:

- Path A, reconnect inside a run. Phase 7 item 2 sends `Last-Event-ID` set to the last committed id. Events received after that commit, and before the disconnect, sit in the open micro-batch. They already have capture lines. The server sends them again after the reconnect. Step 1 drops them as resends. The micro-batch never gets them. The plan does not say that the open micro-batch commits before a reconnect.
- Path B, crash inside a run. Update 3 MF-2 writes each segment before the checkpoint. The checkpoint does not name the segments. Startup cleanup (update 2 MF-2) covers only the lake folders and temporary names there. An uncommitted segment file stays under `.context/replay/<RUN_ID>/`. After the restart, the server resends its events. Step 1 finds them in the capture and drops them. The lake never gets them.

Both paths end with `fct_edit` missing events. The capture then counts them. The Phase 10 check compares distinct `meta_id` in `fct_edit` with the capture line count. That check fails on the first run, so the plan's own check finds the bug. The plan still has no rule that prevents it.

Fix: choose one. (a) Commit the open micro-batch before any reconnect. Then the reconnect point equals the last commit, and the capture holds only committed lines. (b) Make step 1 check only the capture segments that the checkpoint names. Delete the uncommitted segments on startup. Name both cases in Phase 7 item 4. Add failing tests before the sink: a fake SSE server drops the connection with events in the open micro-batch, and the final `fct_edit` count equals the sent count. A crash after the capture write and before the checkpoint leaves no event missing from the lake after restart.

### MF-2: the acceptance weakens the issue, and E1 needs a user decision

The issue says the consumer must not count any event twice or lose one (`.context/issues/gh-1.md`, Rules). Step 0 acceptance now says the plan "does not detect loss of an event that the consumer never received. See D11." Update 4 MF-2 option (b) keeps this. D11 says "The user must accept this limit ... E1 does not start until D11 is recorded in `DECISIONS.md`."

The issue also says "Work autonomously. Nobody answers questions." The implementer cannot get the user decision that D11 needs. So E1 cannot start, and Phase 10 cannot pass. The plan also has no autonomous path for the probe case BLOCKED (update 4 MF-3). It says "The implementer does not choose." A BLOCKED result then ends the run with no deliverable.

This is a weakened acceptance. The plan changes a stated requirement and makes its own proof depend on a person who the issue says does not answer.

Fix: restate the requirement as the plan sees it. Name a default that the implementer records in `DECISIONS.md` and then follows. For example, the plan records "loss before consumer receipt is not checked" as the accepted limit. Name the user review as a later step, not a gate for E1. For BLOCKED, name the next step that the implementer takes, or name the stop state and the artifact that it writes. Either way, the plan must say what the autonomous run does, and it must not say that Phase 10 passes when the check did not run.

### MF-3: the two-run acceptance fails a normal second run

The two-run acceptance comes from plan update 2 MF-5 and Step 0. The issue does not ask for it. The issue asks for one `make stream DURATION=<seconds>` run, with a resume after a drop, that counts no event twice and loses none.

Update 3 MF-3 fails run 2 when its replay window intersects run 1 or when a `meta.id` appears in both captures. The probe in update 4 MF-3 expects the server to restart at the same position on each connect. If that holds, run 2 fails by design. The plan treats a normal second `make stream` as an error, and the issue does not say so.

Fix: restate the two-run rule in Step 0, Phase 7 and Phase 10. Either drop it, or keep it as a check that records a warning in `DECISIONS.md` and does not fail the run. Name which rule the acceptance uses. Update the Phase 7 TDD tests that name the overlap message to match the chosen rule.

### MF-4: check 5 covers a window that the issue does not name

The issue names check 5 as "the replayed hour" (`.context/issues/gh-1.md`, Checks, item 5). Update 4 note N-r says "The grader does not need `DURATION=3600`." The plan gives no source for that claim. The check 5 view covers the first to last `meta.dt` of the run. A run with `DURATION` below 3600 covers less than an hour. So the answer to check 5 can differ from the question that the analysts ask.

Fix: name the acceptance run with `DURATION=3600`, so check 5 covers the hour that the issue names. Or record in `DECISIONS.md` that check 5 covers the replay window, and why. Either fix must say which one the implementer uses. Do not state an assumption about the grader.

## Notes (not blocking)

- N-a. Phase 3 item 3 names `_loaded_at`. The value is the source file modification time (update 1 MF-3). A load time and a file time differ. Consider a name such as `_source_mtime`. This is a word choice.
- N-b. `tests/test_late_count.py` (update 2 MF-3) applies the late rule a second time. An independent oracle is useful. Record in `DECISIONS.md` that this copy is an oracle, not a reuse of the engine code.
- N-c. The fake SSE server, the zip fixture builder and the capture writer appear in several test files. No `tests/` folder exists yet, so no helper duplicates an existing one. Put shared test helpers in `tests/conftest.py` when the Rule of Three applies.
- N-d. The probe script in Phase 7 item 2a uses one connection pair. A probe connect may move the server position. Name whether the probe runs before or after the acceptance runs, so the run start stays known.
- N-e. The `ste-lint.py` path is not named in the plan (cycle 2 note N-12, still open). The writing contract names it as `skills/asd-ste100/scripts/ste-lint.py` under `$CADENCE_HOME`.
- N-f. Check 1 has no query step. Phase 6 item 2 names checks 2 to 4 and check 3. The `oracle_map.yml` row for check 1 is still needed.

## Checks run

- Stages: `stages.json` (`$CADENCE_HOME/stages.json`) lists the core blocks A1 to R7. The plan covers the plan blocks (P1, P3, P4), the implement block (E1) and the draft PR block (E4). The review and close blocks follow the plan's execution order. No block is missing.
- Reuse and extension: the section exists at `## Reuse and extension`. The repo has no `tests/`, `scripts/`, `shared/` or `engine/` folder yet. So the plan writes no helper that already exists. Helper counts for R1 style: `helpers_reimplemented` none, `helpers_reused` none, `thin_files` none. The engine registries (Phase 2 item 4) are the extension point.
- Standalone package: the plan names no `~/.cursor` path. It runs no host command or skill. The probe and the engine use `$CADENCE_HOME` only where the plan names it.
- TDD and checkpoints: Phases 2 to 9 each start with a failing test. Phases 1 and 10 are configuration and run phases. Each phase ends with a local commit (plan preamble). The Phase 7 TDD list lacks the tests for MF-1 and the open micro-batch.
- Weak tests: the Phase 10 count check cannot detect loss (MF-2). The Phase 7 fake-server test does not name the micro-batch size or the commit trigger, so it may pass or fail by chance (MF-1).
- Rollback and blast radius: the blast radius lists new and changed files. `.gitignore` already ignores `lake/`, `out/` and `.context/`. The plan does not name a rollback for a failed phase. This is a note only, since each phase keeps its own commit.
- Gates: `make build`, `make stream DURATION=<seconds>`, `uv run pytest` and `uv run dbt test --project-dir transform --profiles-dir transform`. The Makefile is a stub. Phase 1 exit checks each target.
- Repo state: `Makefile` (stub), `pyproject.toml` (pins present), `transform/dbt_project.yml` and `transform/profiles.yml` (present), `data/raw/` (present), `.context/issues/gh-1.md` (present).

## Evidence

- Plan Phase 7 item 2 (reconnect with the last committed id), Phase 7 item 4 (startup cleanup of lake folders only).
- Plan update 2 MF-2 (cleanup rules a to d, lake folders only), update 3 MF-2 (segments under `.context/replay/<RUN_ID>/`, checkpoint holds the next `seq` and segment number), update 4 MF-1 (step 1 drops a run-capture resend, step 2 writes the capture line first).
- Plan update 4 MF-2 (D11, E1 waits for the user), update 4 MF-3 (BLOCKED path, "The implementer does not choose").
- Issue: `.context/issues/gh-1.md`, Rules (stop and resume: no event counted twice or lost), Checks item 5 ("the replayed hour"), Environment ("Work autonomously. Nobody answers questions.").
- Plan Step 0 acceptance (second bullet) and update 4 note N-r.

## Next step

The orchestrator maps MF-1 to MF-4 to phases under `## Carried review findings`. The orchestrator runs `/plan-update` on the same plan. The loop ends after this cycle. No further `/plan-review` run starts from this review.
