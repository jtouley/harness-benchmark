# gh-1: federal spend and Wikipedia edit pipeline, summary

Branch: `feature/gh-1-pipeline`. Repo: `/tmp/claude-0/-home-user/a08112b2-70f8-5c85-83c0-3c1d7290b3c5/scratchpad/pipe/P1-cadence-core-haiku-4/repo`.
Cadence run: `c86befd2-6ec7-4c02-aa2e-d1de6bf2d165`. The branch derived the task id `cd-1`. The issue is `gh-1`.

## Stages

| Block | Result |
|---|---|
| A1 activate | Fresh run started at A1. |
| P1 plan-create | Plan written as `.context/plans/gh-1-pipeline.plan.md` with 7 phases. |
| P3 plan-review, cycle 1 | `READY WITH CHANGES`. 4 must-fix items (MF-1 to MF-4). |
| P4 plan-update, cycle 1 | Applied MF-1 to MF-4 and the test lines. |
| P3 plan-review, cycle 2 | `READY WITH CHANGES`. 3 must-fix items (MF-5 to MF-7). Two cycles reached. |
| P4 plan-update, final | Carried MF-5 to MF-7 to phases. No more review, per the cycle limit. |
| P9 entry invariant | First run failed on the heading format. The heading was fixed, then `OK`. |
| E1 phases 1 to 7 | Seven commits, `phase 1` to `phase 7`. Each phase passed its gate. |
| E4 draft PR | Local file: `outputs/PR.md`. No GitHub. |
| R1 to R7 | See the end of this file. |

The plan review never returned `READY TO EXECUTE`. Cadence allows two cycles. The three carried findings were built in: MF-5 is the folder test (`pipeline/tests/test_marts_published.py`), MF-6 is the contract guard (`pipeline/tests/test_dbt_guards.py`), and MF-7 is the key tests.

## Phase results

1. **Discovery.** Read the eight zips, the census files, the site matrix and the replay. Wrote `pipeline/oracle.py` (decimal sums). Recorded 18 decisions in `DECISIONS.md`. Found that the replay cuts each connection at event 15,839 (see D32).
2. **Batch lake.** `pipeline/batch.py` lands the Contracts, Assistance, the 2024 and 2021 census files, and the site matrix as Parquet under `lake/batch/`. Money stays text. Tests: money text, census SUMLEV, two runs with the same row counts. Row counts: 416 contract rows, 9,404 assistance rows, 949 sites.
3. **Star schema.** Staging, dimensions (agency, place, date), `fct_award_transaction`, and `mart_fy2024_award_net`. Tests: keys, FY2024 total against the oracle, fiscal year against action dates, a population fallback unit test, a dedup unit test, and build guards for cast errors and contract mismatches. Dbt: 43 PASS.
4. **Batch marts.** `mart_fy2024_monthly_county_agency` (ratio of sums), `view_fy2024_county_per_person_top10`, and the check 4 reconciliation test. `pipeline/check_marts.py` and `oracle_map.yml`. Two builds gave the same mart hashes.
5. **Stream consumer.** `pipeline/stream.py` resumes after each drop, dedups on `meta.id`, and lands each micro-batch as one Parquet file. A file that cannot be read goes to `_quarantine/`. Tests: drop and resume, duplicate `meta.id`, stop and restart, kill during a flush. All 5 PASS.
6. **Stream models.** `stg_recentchange`, `fct_edit` (incremental), `mart_edit_window_5min` (incremental), `late_events`. Tests: lateness at 1500 and 1501, NULL bytes, dedup, window alignment, keys, and oracle counts. Total dbt: 67 PASS.
7. **Evidence.** Commands and results are below.

## Phase 7 evidence

Commands, in order, from a clean state (`rm -rf lake out`):

1. `make build` with no stream data: exit 0. dbt: 67 PASS.
2. `make stream DURATION=60`: exit 0. Lake: 15,839 rows, 15,839 unique `meta.id`.
3. `make stream DURATION=60` again, after a stop: exit 0. The count stayed at 15,839.
4. `make build`: exit 0, then `make build` again: exit 0. The sorted-row hashes of all six check objects were identical across the two builds (`outputs` log: `MART HASHES IDENTICAL`).

Python tests: `uv run python -m unittest discover -s pipeline/tests -t .` gives 13 tests, OK.

Hashes (sorted rows, sha256) after step 4:

| Mart | Rows | Hash (first 16 hex) |
|---|---:|---|
| `mart_fy2024_monthly_county_agency` | 2,724 | 11ee47a5279c751f |
| `view_fy2024_county_per_person_top10` | 10 | ec31e9fcd702d08a |
| `mart_fy2024_award_net` | 7,918 | 1bd951c795a6d1e2 |
| `fct_edit` | 15,837 | 08f0527b73f7cb07 |
| `mart_edit_window_5min` | 614 | b74a1055597cba79 |
| `late_events` | 60 | a75dcc4a7488ac2d |

## Check results

1. **FY2024 net obligations per awarding agency** (`oracle_map.yml`, check 1):

   | Agency | Net obligations (USD) |
   |---|---:|
   | 417 National Endowment for the Arts | 164,522,022.53 |
   | 418 National Endowment for the Humanities | 166,315,027.20 |
   | 474 Institute of Museum and Library Services | 279,998,069.91 |
   | 485 Corporation for National and Community Service | 831,182,097.03 |

   Total: 1,442,017,216.67. Matches the oracle.

2. **Ten counties with the highest FY2024 obligations per person.** Rank 1 is District of Columbia, 129.07 per person. Rank 10 is Lake and Peninsula Borough, Alaska, 38.02. Matches the oracle.
3. **Awards with a net negative obligation in FY2024:** 1,122 of 7,918 awards. Matches the oracle.
4. **For one month, county totals, state totals and the source total.** The dbt test `check4_county_state_source_reconcile` checks every month and state. The source total is 1,442,017,216.67. PASS.
5. **Stream edits and net bytes per wiki, human and bot, late included.** 15,837 edits in total. `enwiki` has 7,861 human and 3,682 bot edits. The full list is in `p7_checks_b.txt`.
6. **Top 5-minute windows on enwiki (on-time only).** Top window: 2026-10-15 00:25 UTC, 550 edits.
7. **Late events:** 60. Matches the oracle count, which applies the lateness rule to the replay arrival order.

## Decisions

Each choice is in `DECISIONS.md` (D1 to D32). The main ones:

- An edit is any `recentchange` event (D1). Money uses place of performance (D2).
- Eight Connecticut counties have no 2024 estimate. They use the 2021 estimate, and `population_year` says so (D10, D17).
- Stream models are DuckDB tables with a Parquet copy, not `external`. The `external` writer adds a NULL row when a result is empty (D24).
- The window mart is incremental from a checkpoint table (D25). Incremental and full builds agree on hashes. A scratch test removed five stream files and restored them to show this.

## Open risks

- **The replay stops at event 15,839.** Every connection cuts at the same event, and resumes do not pass it. The lake holds the reachable 15,839 events. The full capture may hold more. See D32.
- **The "replayed hour" is about 26 minutes of event time.** The reachable replay spans 1,725 seconds of event time.
- **Two stream tests run only with data.** `fct_edit_counts_match_oracle` and `late_events_match_oracle` skip the comparison when the stream is empty (D26).
- **Makefile uses `--no-partial-parse`.** A stale parse cache hid four stream tests during development (D27).
- **Generated file.** dbt writes `transform/.user.yml` on each run. It is not committed.

## Cadence stages after E1

- **E4:** draft PR text written to `outputs/PR.md`. No GitHub.
- **R1, R5, R7:** see the final message of the run.
