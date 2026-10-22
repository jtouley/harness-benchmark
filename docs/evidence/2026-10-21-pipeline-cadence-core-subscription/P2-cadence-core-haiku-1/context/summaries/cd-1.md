# Session summary: cd-1

RUN_BY_COMMAND: session-summary
Pipeline-Run: 0f84b2cc-3cf4-4553-b890-6f79e87e0cd2

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)

Source manifest: `.context/manifests/cd-1.md` (sha256 ddfc3c33...). All document hashes in the manifest match the files on disk.
Branch: feature/gh-1-pipeline. Base: main. Commit on the branch: dfb7685 "cadence config for the trial" (before this run).

Hard stop (from the manifest): P7 test-benchmark-plan returned FAIL three times (initial run and two plan-update rounds). Retries are exhausted before P8, P9 and E1. The run ended at the plan stage.

## Request

- Source: `.context/proposals/cd-1.md` (the request as written).
- Build a pipeline from raw public data to Parquet tables for analysts, in two parts:
  - Question A (batch): FY2024 federal award money by state, county, agency and month, in total and per person (population from the July 1, 2024 estimate, Amendment A).
  - Question B (stream): Wikipedia edits per wiki, namespace and 5-minute window, split human and bot, with net bytes, from an SSE stream with resume after disconnect.
- Required parts: a Python 3.12 pipeline engine driven by `pipelines/*.yml`, a dbt project in `transform/`, a lake under `lake/`, marts under `out/marts/`, `oracle_map.yml`, and `DECISIONS.md`.

## What changed

- No phase was executed. No plan phase has a commit in the run. The manifest lists no implementation artifact, no PR review, no PR comment and no findings ledger, so none of these exist.
- Documents written by the run (all under `.context/`):
  - Vibe test: `vibetest/cd-1_2026-10-21.md`.
  - Proposals (decision records): `proposals/cd-1-*.md`, ten files named in the Decisions section.
  - Plan: `plans/cd-1-pipeline.plan.md`, with five plan-review update sections and two P6 update sections (the file is still the baseline plan plus stacked updates).
  - Reviews: `reviews/plan_cd-1-pipeline.md` (cycle 5 file), `adversarial/adversarial_cd-1-pipeline.md`, `_r2.md`, `_r3.md`.
  - Benchmark: `benchmarks/cd-1_plan.json`.
  - Deferral register: `deferrals/cd-1_deferral-register.md`.
  - Failure record: `issues/cd-1-p7-fail.md`.

## Decisions

Decision records are in `.context/proposals/`. All are `status: proposed` in the files. The plan answers the gaps G-1 to G-8 from the vibe test (see the deferral register, "Assumptions").

| Decision | Choice (from the proposal file) | Gap |
|---|---|---|
| cd-1-fy-and-month-basis | `action_date`; FY2024 is 2023-10-01 to 2024-09-30; month is calendar month; net obligations is the sum of `federal_action_obligation` | G-4 |
| cd-1-place-basis | Place of performance; missing state or county maps to `UNKNOWN`; Connecticut planning regions (09110 to 09190) map to the state `UNKNOWN` county (MF-10); territory states 60, 66, 69, 72, 78 keep their state and map to `UNKNOWN` county with no population join (MF-11) | G-5 |
| cd-1-negative-award-key | Award is the prime award unique key; negative when the FY2024 net sum is below zero | G-6 |
| cd-1-late-event-placement | `fact_edit` holds every consumed edit with `is_late`; the window mart counts on-time edits only; `late_events` is the `is_late` subset | G-3 |
| cd-1-load-metadata | Deterministic load metadata only (file name, SHA-256, row number, batch sequence); no wall-clock time in `lake/` or `out/` | G-7 |
| cd-1-stage-ownership | Engine lands and dedups events and assigns `arrival_seq`; dbt computes event-time windows, lateness, the late split, the wiki join, the FY2024 filter and the population fallback; event time is `meta.dt` | G-8 |
| cd-1-stream-dedup-resume | Dedup key is `meta.id`, checked against every committed batch file; resume with `Last-Event-ID` set to the last committed SSE id | G-1 |
| cd-1-stream-commit-manifest | JSON manifest `lake/_state/stream_manifest.json` lists committed batch files, last SSE id and `last_arrival_seq`; running max event time is not stored (dbt derives it) | G-2 |
| cd-1-money-scale | `DECIMAL(18,2)`; a value with more decimals fails in `to_decimal` | N-6 |
| cd-1-population-fallback | `POPESTIMATE2024`, falling back to `POPESTIMATE2021` with `population_as_of = 2021`; Connecticut's nine 2024 planning regions dropped (MF-9) | Amendment A |
| cd-1-publish-format | On-run-end COPY to `out/.marts-staging/`, then the engine swaps to `out/marts` | publish |
| cd-1-engine-dependencies | Add pyyaml and jsonschema (runtime) and pytest (dev), exact versions in `uv.lock` | engine |

Plan decisions with later revisions: the running max event time rule (MF-1), the dedup scope (MF-2), derived data leaving the lake (MF-4), the publish states (MF-6), and the join keys typing (MF-8) are set in the plan update sections.

## Reviews

- Vibe test (`vibetest/cd-1_2026-10-21.md`): NOT READY FOR PLANNING. Blocking gaps G-1 to G-8. Non-blocking N-1 to N-8.
- Plan review, five cycles (`reviews/plan_cd-1-pipeline.md` is the cycle 5 file; earlier verdicts are recorded in the plan update sections):
  - Cycles 1 to 4: READY WITH CHANGES, with must-fix items MF-1 to MF-10.
  - Cycle 5: READY WITH CHANGES, blocking. MF-11 (territory places) is open. The plan-review limit (`plan_review_cycles` = 5) is reached.
- Adversarial review of the plan (de-adversarial-reviewer, plan-gate):
  - Round 1 (`adversarial_cd-1-pipeline.md`): REQUEST CHANGES.
  - Round 2 (`_r2.md`): REQUEST CHANGES.
  - Round 3 (`_r3.md`): REQUEST CHANGES. Blocking B-1 (the `Last-Event-ID` resume is inclusive: the server re-sends the 500th event, so the check as written expects the wrong event). Conditions C-1 (value of N undefined before Phase 5) and C-2 (C-3 result must come from the full check).
  - The adversarial limit (`adversarial_cycles` = 3) is reached. No plan section after round 3 applies B-1, C-1 or C-2. The last plan section is "Plan update 2026-10-21 (P6 round 2)".
- Test benchmark plan (`benchmarks/cd-1_plan.json`): FAIL, mean 6.33, floor 7. Scores: coverage 7, assertion strength 6, DRY 6, layer 6, failure paths 8, mutation resilience 5. Mutants were not run (plan mode). Three mutants survive on the rows as written (F18, F19, F20).

## Findings

Must-fix findings from the P7 benchmark (all open at the time of the last update in the file, none closed by a fix commit):

- F12: `## Reuse and extension` does not name the helpers that the plan update says it names.
- F13: carry sections and ledger rows still name two test files that F02 removes.
- F14: fixture rows for the dbt singular tests have no path into the warehouse the test reads.
- F15: kill and restart setup is written in three files with no shared helper.
- F16: the territory row count and the stream N-event margin have no values in the assertion.
- F17: no row checks that a late edit is absent from `mart_edit_window_5min` and present in `late_events`, or checks `check_late_count`.
- F18: no row fixes the value of `length_new - length_old`; sign-flipped and dropped-subtraction mutants survive.
- F19: no sum row where float addition drifts.
- F20: no row differs under a local time zone (UTC rule).
- F21: the name S3 is used for two different test cases.

Must-fix from the plan review: MF-11 (territory places; the 23 USAspending rows in states 60, 66, 69, 72, 78 fail `test_place_population_join.sql` under the current text). Open at cycle 5.

Blocking from the P6 round 3 report: B-1 (inclusive `Last-Event-ID`). Not applied in the plan file.

Notes (not blocking): F23 (oracle queries have no test), F24 (COPY ORDER BY has no row), F25 (dedup test names no file), F26 (state 09 equality moved out of tests), F27 (rounding of `obligations_per_person`).

Closure: none of the items above has a fix commit or a deferral ticket. The deferral register lists "No approved deferrals."

## Deferrals and open items

- Deferrals: none approved (`deferrals/cd-1_deferral-register.md`).
- Hard stop: P7 FAIL three times; retries exhausted before P8, P9 and E1.
- Plan review limit reached (cycle 5 of 5, blocking). MF-11 open.
- Adversarial limit reached (3 of 3). B-1, C-1 and C-2 from round 3 not applied in the plan.
- Open must-fix: P7 items F12 to F21.
- Notes: F23 to F27; vibe-test N-1 to N-8 (logged as assumptions in the deferral register only where the plan answered them).
- Missing by design of the stop: implementation (E1), architecture conformance, draft PR, PR review, findings ledger.

## Next action

A person decides how the run continues. The run cannot reach E1 under its current limits (plan review at 5 of 5, adversarial at 3 of 3, P7 retries exhausted). The options the documents support:

1. Review the plan and the P7 scorecard (`benchmarks/cd-1_plan.json`), and the failure record (`issues/cd-1-p7-fail.md`). Decide whether to write a new plan revision outside the loop limits, or to raise the limits.
2. Answer whether MF-11 (territory places) takes the `UNKNOWN`-county rule or the stated-exclusion rule. The plan leaves this open.
3. Decide how B-1 (inclusive `Last-Event-ID`) changes the Phase 5 test and the C-3 check.

No PR is open for this run. No merge is possible from this state.
