# gh-1 summary: pipeline for federal awards (Question A) and Wikipedia edits (Question B)

Branch `feature/gh-1-pipeline` in `repo`, nine phase commits on top of `origin/main`, pushed to the local origin. The PR text is in `outputs/PR.md`. No PR exists, because this environment has no GitHub.

## Pipeline stages

| Stage | Result |
|---|---|
| A1 activate | Run started on `feature/gh-1-pipeline`. |
| P1 plan-create | Plan written with 9 phases. |
| P3 / P4 plan review loop | Five review cycles. The fifth review said READY WITH CHANGES. I applied its carried findings. The review limit is reached, so I did not run another review. One carried id (MF-6) was mapped by hand to the Phase 6 tests. That was a small edit I made to the plan, not a peer update. |
| P9 entry invariant | OK. |
| E1 implement | 9 of 9 phases committed. dlt gate passes, so the stream uses dlt. |
| E4 draft PR | Branch pushed. PR text in `outputs/PR.md` (STE lint: 0 violations). No PR URL. |
| R1 pr-review-local | Not run. The peer needs a PR number and a GitHub remote. |
| R5 closure | Not run. It depends on R1. |
| R7 session close | Not run. A hard stop is recorded (`credentials`), so the session stays open. |

## Batch (Question A)

- `make build` runs on a clean lake and out folder. It finishes with 81 dbt nodes passing.
- Lake row counts equal the sources: USAspending contracts 416, assistance 9404; Census 2024 3144 and 2021 3143 county rows; site matrix 1073.
- Five marts under `out/marts/`: agency, award net, county per person, month reconciliation, and monthly obligations.
- A second build gives the same sorted content hash for each mart.

Answers from the marts:

1. Net obligations per agency total 1,442,017,216.67 USD. Largest: NCSA (485) at 831,182,097.03.
2. Top counties by obligations per person (July 1, 2024 population): 11001 (DC) 129.07, 46065 at 76.85, 31181 at 75.17, and so on.
3. Awards with a net negative obligation: 1122.
4. All 12 months reconcile to zero difference between county, state and source totals.

## Stream (Question B)

- `make stream DURATION=60` against the replay. Committed 21493 arrivals. Arrival sequence is 1 to 21493 with no gap and no duplicate.
- Independent Python check: 60 late edits, 12807 on-time edits. dbt gives the same counts.
- Check 5 totals of an interrupted run equal an uninterrupted run (acceptance test).
- Check 6: the top window on en.wikipedia.org is 2026-10-15 00:25 with 553 on-time edits. Ties sort by window start.
- Check 7: 60 late events.
- The stream mart has no time filter. Check 5 says "the replayed hour". This holds only while the lake holds one replay hour.

## Findings that changed the plan

- The replay ignores `Last-Event-ID`. Dedupe on `meta.id` covers the overlap.
- The replay ids are JSON arrays, not counters.
- dlt `run()` does not load an extracted package on 1.31.0. The start rule calls `normalize()` and `load()` first.
- The Connecticut gap is in the 2021 file (old county codes). The 2024 file has the new planning regions. Puerto Rico, Guam and the other territories are in neither file.
- dbt-duckdb enforces contracts on external models, so the R1 fallback is not needed. dbt-duckdb external does not run incremental models, so the window mart is published with a post hook (R2).

## Choices for the author

See `DECISIONS.md`. The open ones are:

1. The six old Connecticut codes use the 2021 population (Decision 15).
2. Check 6 lists the top 10 windows (Decision 18).
3. The stream mart has no time filter (Decision 17).

## Not done

- No PR number, so no R1 review, no R5 closure, and no R7 session close.
- The live replay runs faster than real time and sends repeated events. Totals depend on how long the consumer runs.

## Files

- `DECISIONS.md`, `oracle_map.yml`, `Makefile`, `pipeline/`, `tests/`, `transform/`, `.context/plans/gh-1-pipeline.plan.md`, `.context/reviews/plan_gh-1-pipeline.md`.
- `outputs/PR.md` (PR title and body).
