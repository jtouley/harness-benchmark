RUN_BY_COMMAND: plan-review

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Task: gh-1

# Plan review: open data pipeline (gh-1)

Plan reviewed: `.cursor/plans/open-data-pipeline_gh-1.plan.md` (full plan, with Updates 1 to 4)
Review cycle: 5 (after `Update 4 (2026-10-19)`). This is the cycle limit. Do not review again after this run.

Verdict: READY WITH CHANGES

## Summary

Update 4 applied the two cycle-4 must-fix items, MF-12 and MF-13. Both are closed. The Phase 5 proof now reads lake batch files, not `fct_edit`. The resume and drop rule is stated.

Two new must-fix items remain. Both are in the Phase 5 test design. The Phase 5 consumer has no stop rule that the fake server can trigger. The duplicate test has no disconnect point. Without these, the Run A and Run B proofs cannot run as written.

Each item has a short fix. No new phase is needed. The verdict blocks E1. At the cycle limit, the plan update maps each open id to a phase under `## Carried review findings`.

## Must-fix items

- MF-14 (Phase 5 work list, Phase 5 TDD, MF-10, MF-12 proof). The Phase 5 work list says that the consumer reconnects on disconnect with backoff, and stops only after `DURATION` seconds. MF-10 says a partial batch closes "when the stream closes". The MF-12 proof says Run A consumes all 30 events, and the fake server "closes the stream after the last event". Run A has no `DURATION`. The plan does not say whether a closed stream ends the run or starts a reconnect. If it reconnects, Run A and Run B never end. Fix: state one rule. For example, a stream close with no `DURATION` ends the run after the partial batch closes, and a stream close during a `DURATION` run reconnects until `DURATION` ends. Then state the arguments that the unit test passes to the consumer for each run.

- MF-15 (Phase 5 TDD, duplicate test, MF-13). The duplicate test says the fake server "also resends events 1 to 5 on reconnect, after the resume". A resend needs a reconnect, and a reconnect needs a disconnect. The plan does not say where the fake server disconnects in duplicate mode. The earlier fake-server spec says it "must disconnect after N events", but Update 4 does not give N for this mode. Without a disconnect point, the duplicate path never runs and the test passes without testing MF-13. Fix: state the event number after which the fake disconnects in duplicate mode, and state that the test asserts the disconnect happened (for example, the fake records its reconnect count, and the test checks that it is 1).

## Resolved from cycle 4

- Cycle 4 MF-12 (the Phase 5 proof reads lake files, not `fct_edit`): closed. Update 4 builds the lists from `lake/stream_recentchange/` in `_batch_id` order. It keeps the first arrival of each `meta_id` (D11). The `fct_edit` comparison moves to Phase 9 (Update 2, steps 2 and 4). Phase 5 no longer depends on Phase 6.
- Cycle 4 MF-13 (resume and drop rule): closed for the Run B arithmetic. Update 4 states the drop rule (`id` at or before the checkpoint `id` is dropped before any `arrival_seq` or batch count). It also states that the checkpoint stores the last `id` only. It names the Phase 0 gate for the replay `id` order. The Run B batches 12 to 15 and their event ranges follow from this rule and from `batch_size=2`. The arithmetic is correct.
- Cycle 3 MF-9, MF-10 and MF-11 remain closed. Update 3 does not conflict with Update 4.
- Cycle 1 and cycle 2 items remain closed. Update 4 does not reopen them.

## Notes (not blocking)

- Check-view grains: the MF-7 scope names check views under `transform/models/checks/`. No grain line is given for any of the eight `chk_*` views. E1 can derive each grain from the view SQL. A one-line list in the plan update removes the doubt. Cycle 3 and 4 note, still open.
- Mart contract fallback: Phase 0 records whether the `external` materialization enforces a model contract. The plan does not say what to do if it does not. The ticket requires enforced contracts. E1 can pick a fallback, such as a singular check on the Parquet shape, and record the choice in `DECISIONS.md`. This is an option, not a block.
- Rollback: Step 0 has a blast radius but no rollback line. Cycle 1 to 4 note, still open.
- Commit checkpoints: no phase has a commit step. Cycle 1 to 4 note, still open.
- Phase 6 fixture route: the 12-event fixture has no stated route into the models (dbt seed, lake files in a test folder, or a direct insert). Cycle 1 to 4 note, still open.
- Stream selection: name the dbt selector for `dbt build --select stream`, and confirm that `late_events` is in it. Cycle 2 to 4 note, still open.
- Phase 7 checks: the repeatability check and the resume check have no file location. Name a script or a test file. Cycle 2 to 4 note, still open.
- Replay rate: Phase 0 should record the replay event rate. Check 5 says "the replayed hour", and Phase 9 runs `DURATION=60`. The plan should say whether 60 seconds covers the hour. Cycle 1 to 4 note, still open.
- Duplicate after reconnect: Phase 5 should say whether a duplicate delivered after a reconnect gets a new `arrival_seq`. The MF-13 drop rule makes this moot for the plan's own test, but the plan should still say it. Cycle 1 to 4 note, still open.
- Older text under the updates: Phase 5 says `make stream` runs the stream dbt step, Phase 6 says `late_events` is a view, and Phase 6 says `mart_edit_windows_5min` is incremental. The updates override these lines. A plan update can edit them. Cycle 2 to 4 note, still open.
- Check 4: state that the source total equals the sum of state totals plus the `UNKNOWN` amount. Cycle 2 to 4 note, still open.
- Phase 9 output paths: use the absolute outputs path from the ticket. The ticket says `outputs/` under the task directory. Cycle 1 to 4 note, still open.
- Phase 4 month: the reconciliation view uses "the chosen month". Name the month, or name the rule for choosing it. Option only.

## Checks with no finding

- `core:standalone-package`: the plan names no host path. It uses only `.cursor/plans/`, `.context/` and repo-relative paths. The ticket path is a task directory, which the plan does not use as a procedure input.
- `core:dry-extension`: the repository has no `tests/`, `scripts/` or `shared/` directory. No helper in the plan already exists in a shared module. The plan writes a new `pipeline/` package, `pipeline/tests/` with `unittest`, and stdlib-only fakes. The `## Reuse and extension` section is present and correct.
- Phase order: Phases 0 to 9 are in dependency order. The Phase 5 proof no longer depends on Phase 6 (MF-12 closed).
- Real quality gates: the plan lists the quality-gate commands in repository form, and each phase has an exit criterion that uses them.
- Ticket rules: the lateness rule (D8, strict `>`), the window rule (5-minute UTC windows), the exact money rule (`DECIMAL`) and the two-object window design match the ticket text, as checked in cycle 4.

## Evidence checked

- Plan: `.cursor/plans/open-data-pipeline_gh-1.plan.md`, full text including Updates 1 to 4.
- Cycle 4 review: `.context/reviews/plan_open-data-pipeline_gh-1.md` (prior version of this file), used to confirm MF-12 and MF-13 and the notes still open.
- Cadence config: `.cadence.json` (gated prefixes include `pipeline/`, `transform/` and `Makefile`).
- Repository: no `pipeline/`, `tests/`, `scripts/` or `shared/` directory exists.
- Cadence references: `peer-contract.md`, `architecture-core-rules.md`.
