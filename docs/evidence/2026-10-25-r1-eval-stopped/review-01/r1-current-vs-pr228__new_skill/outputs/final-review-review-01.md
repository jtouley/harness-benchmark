RUN_BY_COMMAND: pr-review-local
Last reviewed commit: c176f99dc309b01a2e353856ebc599a32840f8e4

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
**Branch:** review (head c176f99) against base (d176e80), merge base d176e80
**Repo copy:** /var/tmp/revieweval/r1-current-vs-pr228/review-01/new_skill/run-1/repo
**Verdict:** NO MERGE

No Cadence run is active. The ledger append and the gates were skipped, as the orchestrator asked. The PR text file (`PR: local:<path>`) was not given, and the tree has no `spec/spec.md`. Contracts were checked against `DECISIONS.md` and `oracle_map.yml`.

## Must-fix items

MF-1. `pipeline/stream_consumer.py`, `StreamConsumer._accept` (line 196 and line 200). Crash on a non-string `meta.id`. A list id raises `TypeError: unhashable type: 'list'` at `event_id in self.seen`. `_read_until` catches only `OSError` and `HTTPException`, so the process stops and the pending batch is not flushed. The module docstring and `_skip` say one bad event must not stop the stream. Fix: in `_field_problem`, reject a `meta.id` that is not a string, and skip the event with a counted skip. Check: `tests/test_stream_parsing.py::FieldProblemTest::test_fieldProblem_metaIdNotString_isRejected` and `tests/test_stream_consumer.py::StreamConsumerTest::test_consumer_metaIdNotString_skipsEventAndStreamContinues` (a list id, then one good event, then one good event; the stream lands both good events).

MF-2. `pipeline/stream_consumer.py`, `_field_problem` and `flatten` (lines 253-267 and 78-96). Fields `bot`, `namespace`, `wiki` and `type` are not type-checked. Two silent wrong results:
- `bot: "false"` lands with `bot = True` in `stream_raw` and `stream_events.bot = True`, but `actor_type = "human"`. The two columns disagree on the same row. The check 5 oracle (`case when bot then 'bot'`, `transform/tests/test_stream_totals_per_wiki.sql`) would count this row as bot, and the mart would count it as human. The test would fail on such input.
- `namespace: "zero"` lands as NULL with no skip and no log line.
Fix: extend `_field_problem`: `bot` must be a bool or null; `namespace` must be an int or null; `wiki`, `type` and `server_name` must be strings or null. Each failure is a counted skip. Check: one parametrized row per field in `tests/test_stream_parsing.py::FieldProblemTest` (for example `bot="false"` returns `"bot is not a boolean"`), and `tests/test_stream_consumer.py::StreamConsumerTest::test_consumer_wrongTypedBot_isSkippedNotMislabelled` (asserts `actor_type` and `bot` agree for every landed row).

MF-3. `pipeline/stream_consumer.py`, `StreamConsumer.run` (line 147). The step prints no accounting counts. The build log for `make stream DURATION=90` shows one skip line and the dbt output. It shows no count of events read, committed, duplicates, skipped and dead-lettered, and no end-of-input value. The walk cannot be completed from the output. Fix: print one summary line at the end of `run`, with read, committed, duplicates, skipped (by reason), dead-lettered (0) and deadline reached. Check: `tests/test_stream_consumer.py::StreamConsumerTest::test_consumer_run_printsAccountingSummary`, which asserts that the counts add up to `read`.

MF-4. `pipeline/batch_load.py`, `load_batch` (line 99). The batch step reads about 4 zip files and 3 other sources. It prints nothing about rows read per table, so the walk row for `make build` cannot state the input accounting. The build log shows `uv run python -m pipeline.batch_load` followed directly by the dbt output. Fix: print the dlt load info per resource (rows read and rows loaded) after `pipeline.run`. Check: `tests/test_batch_load.py` asserts that the printed row count per table equals the count of CSV data rows read from the fixture.

MF-5. `tests/test_stream_consumer.py::_replay_ids` (lines 127-151) copies the connect and read loop of `StreamConsumer._connect` and `_lines` (`pipeline/stream_consumer.py` lines 176-189 and 275-281). It is a new test helper that duplicates existing module helpers, which `core:dry-extension` item 1 forbids. Fix: import `_lines` and `StreamConsumer._connect` (or a small public `open_stream(url)`), and delete the copy. Check: `tests/test_stream_consumer.py::StreamConsumerTest::test_consumer_replayAtLocalUrl_landsUniqueEdits` still reaches the same assertions, and `test_stream_parsing` still passes.

MF-6. `transform/tests/test_late_events_count.sql` (check 7) never runs. The file has no `ref()`. It reads `out/marts/late_events` with `read_parquet` and calls the `stream_raw_arrivals()` macro, and neither adds a graph edge. Both Makefile selections therefore leave it out. Evidence: `dbt ls --select +mart_window_5min +late_events +edits_by_wiki_actor --resource-type test` does not list it, while `dbt ls --select test_late_events_count --resource-type test` lists it. The build log has no PASS line for it. Fix: add `{{ ref('late_events') }}` to the test (for example in a CTE that selects from the mart), and rebuild the selection. Check: `dbt ls --select +late_events --resource-type test` lists `test_late_events_count`, and the `make stream` output contains `test_late_events_count ... PASS`.

## Reproductions

Each command ran in the repo copy with `.venv` created by `uv sync --frozen`. `make build` and `make stream` were not run again. The one build log was read, not re-run.

MF-1 and MF-2. Script: `outputs/repro/repro_consumer.py` (run as `.venv/bin/python -I outputs/repro/repro_consumer.py`). Output:
```
[meta.id is a list (unhashable), then good events in same batch] CRASH TypeError: unhashable type: 'list'
    raw landed: []
[meta.id is an int] ok
    raw landed: ['ev-1', '2', 'ev-3']
[namespace is a string, then good events in same batch] ok
    raw landed: ['ev-1', 'ev-2', 'ev-3']
[bot is the string 'false' (actor_type vs bot column)] ok
    raw landed: ['ev-1']
    stream_events actor_type: ['human']
```
Script `outputs/repro/probe_values.py` shows the stored values:
```
bot='false' -> raw bot: True | raw namespace: 0 | events actor_type: human | events bot: True
namespace='zero' -> raw bot: False | raw namespace: None | events actor_type: human | events bot: False
```

MF-3. `/var/tmp/revieweval/r1-current-vs-pr228/review-01/build.log`, the `$ make stream DURATION=90` block. The only lines from the consumer are the skip line `stream consumer skipped an event (data is not JSON), sse id '[{"topic":...}]'`. No count line follows.

MF-4. The same build log, the `$ make build` block. Nothing is printed between `uv run python -m pipeline.batch_load` and the first dbt line.

MF-6. `.venv/bin/dbt ls --project-dir transform --profiles-dir transform --select +mart_window_5min +late_events +edits_by_wiki_actor --resource-type test` lists 10 tests, none of them `test_late_events_count`. The same command with `--select test_late_events_count` lists it. `make build` selection (`+mart_monthly_obligations +mart_award_fy2024`) lists 19 tests, also without it.

Checked and not a finding: `window_5min`, `fact_edit` and checkpoint replacement. Script `outputs/repro/probe_resume.py`: after three flushes, `stream_checkpoint` holds one file with `sse-3` and `high_water` 1792021603. A restart restores `last_landed_id = sse-3`, `high_water` and the 3 seen ids.

Unit tests: `.venv/bin/python -m unittest tests.test_stream_parsing tests.test_lateness tests.test_stream_consumer tests.test_batch_parsing -v`: `Ran 50 tests ... OK (skipped=1)`. The skip is `test_consumer_replayAtLocalUrl_landsUniqueEdits` ("local replay is not running").

Not run: `make build`, `make stream`, `tests/test_rerun.py` (it runs `make build`), `test_shape.py`, `cognitive_complexity_gate.py`, ruff and mypy.

## End-to-end walk

| Step | Spec rule | Observed output | Input accounting | Verdict |
|---|---|---|---|---|
| `make build`, batch load | DECISIONS.md "Make targets" and "Lake layout" | `pipeline.batch_load` prints nothing | not reported: no rows read per table, no end-of-input line | MF-4 |
| `make build`, dbt batch tests | oracle_map.yml checks 1-4 | `PASS=26 WARN=0 ERROR=0 SKIP=0 TOTAL=26`; PASS for `test_fy2024_net_obligations_per_agency`, `test_top_ten_counties_per_person`, `test_negative_net_award_count`, `test_county_state_source_reconcile`, `test_census_fallback_uses_earlier_estimate` | n/a: dbt test; the counts are in each test's query, which returned no rows | cleared (checks 1, 2, 3, 4) |
| `make stream DURATION=90`, consumer | DECISIONS.md "Stop rule" and "Dedup" | one skip line: `data is not JSON`; the run stopped at the deadline (exit 0, 99.4 s total) | read: not reported; committed: not reported; duplicates: not reported; skipped: 1 (log line only); dead-lettered: 0 (not reported); end of input: n/a, live stream, deadline reached | MF-3 |
| `make stream`, dbt stream tests | oracle_map.yml checks 5 and 6 | PASS for `test_stream_totals_per_wiki`, `test_top_windows_en_wikipedia`, `test_event_time_utc_is_utc` | n/a: dbt test; the counts are in each test's query | cleared (checks 5, 6) |
| `make stream`, check 7 | oracle_map.yml check 7 | no output: test not selected | n/a: not run | MF-6 |
| Consumer, malformed `meta.id` | DECISIONS.md "Stream consumer" (a bad event is a counted skip, not a crash) | `TypeError`, process stops | read: 2 of 3 (run stopped); committed 0; end of input: no | MF-1 |
| Consumer, `bot: "false"` | oracle_map.yml check 5 (split human and bot) | row lands with `bot=True`, `actor_type=human` | read 1; committed 1; the two columns disagree | MF-2 |

Check 3 and check 1 are cleared by the PASS lines above. The stream counts (21,502 unique events in an hour) come from DECISIONS.md. They are not in the build log, so they are not cleared here (see Follow-ups N1).

## Adversarial inputs

Stream consumer (`pipeline/stream_consumer.py`):

| Input | Result | Note |
|---|---|---|
| missing `meta.id` | counted skip (`event has no meta.id`) | code path only, no test |
| `meta.id` is a list | crash | MF-1 |
| `meta.id` is an int | lands as text `"2"` | a string id `"2"` would be deduplicated against it (N6); MF-1 fix covers it |
| `namespace` is a string | lands as NULL, no skip | MF-2 |
| `bot` is `"false"`, `0` or `"true"` | lands with `bot` = bool(value), `actor_type` = human | MF-2 |
| `wiki` is an int | lands as text `"7"`, no skip | MF-2 fix covers it |
| corrupt JSON in `data` | counted skip | tested |
| `timestamp` or `length` wrong type | counted skip | tested |
| resume with `Last-Event-ID` | sent from the checkpoint | tested |
| heartbeat only | stops at DURATION | tested |
| offline host | retries once per second until DURATION, no other limit | bounded; not tested |
| workspace that never ran Cadence | not applicable: this is a data pipeline, not a Cadence workspace | n/a |
| an event with no `id:` line | checkpoint becomes None, next connect replays from the start (N7) | dedup keeps counts right |

Batch (`pipeline/batch_load.py`):

| Input | Result | Note |
|---|---|---|
| a zip listed in the README is missing | `FileNotFoundError` before any load | fails loud; not tested |
| a corrupt zip | `BadZipFile` | fails loud; not tested |
| zip whose first member is not the CSV | wrong member read silently | N8 |

## Contracts

The spec file is not in the tree. Contracts were checked against `DECISIONS.md` and `oracle_map.yml`.

- Decision for the author, not a must-fix. `DECISIONS.md` "Per person" says the per-person value divides by "the county's July 1, 2024 population". "Census fallback (Amendment A)" says six Connecticut codes use the 2021 estimate. The mart column `county_population_2024` holds 2021 values for those six rows. The mart does not publish `population_year`, so a reader cannot tell. The author should rename the column or publish `population_year`.
- Accepted with the author's reasoning. `DECISIONS.md` "Dedup" dedups on `lake/stream_raw/`, not `lake/stream_events/` as A-2 names. The reasoning is in the file and holds.
- R3 `bugs` (ruff) and `types` (mypy) records: not produced. No verdict is given for them.
- R2 `test_shape` and R3 `cognitive_complexity` records: not produced.

## Design choices

MF-1 and MF-2 each have two reasonable fixes: extend `_field_problem` (one rule per field, a counted skip), or wrap `_accept` in a `try` and count a failure as a skip. I did not build the matrix in this run. I recommend extending `_field_problem`. It matches the existing timestamp and length rules, and a `try` around `_accept` would also hide bugs in `flatten` and `_flush`. The matrix is a follow-up for the author if they prefer the second option.

## Scope

Diff: `git diff --stat base...review` gives 45 files, +2085 and -2. The change mixes docs (`DECISIONS.md`, `oracle_map.yml`, `.env.example`), a batch pipeline (`pipeline/batch_load.py`, `transform/` batch models), and a stream pipeline (`pipeline/stream_consumer.py`, `pipeline/lateness.py`, stream models and tests). The batch and stream paths share only the Makefile and `.gitignore`. The PR title type is not known because no PR text was given. Recommend a split into a batch change and a stream change, each with its own review.

## Lookback

- MF-1 and MF-2 share one failure class: external input reaches a typed sink with no per-field rule. The existing tests cover four of the seven fields, so the test list was built from a short list of faults. Fix all typed fields in one change.
- MF-3 and MF-4 share one failure class: a step that reads records prints no count. Fix both in one change.
- MF-5 is a test helper that copies module code.
- MF-6 is a singular dbt test with no `ref()`, so graph selection cannot pick it. I checked the other singular tests in `transform/tests/`. Each one has at least one `ref()` except `test_late_events_count`. No other test is affected.
- After fixes: the suite and the matrices were not re-run, because this run has no fix commit. The combined diff was not re-read after fixes.

## Reuse and extension

1. Reused helpers: `read_table` and `read_column` (`pipeline/stream_consumer.py`); `pipeline.lateness` (`is_late`, `window_start`); macros `usaspending_raw()`, `obligations_per_person()` and `stream_raw_arrivals()`; generic test `unique_combination_of_columns`; `tests/stream_harness.py` (`FakeReplay`, `make_event`, `read_rows`).
2. Duplication added: `_replay_ids` (MF-5) copies the stream loop. Oracle copies in SQL: the `sites` CTE in `transform/tests/test_top_windows_en_wikipedia.sql` repeats `transform/models/star/fact_edit.sql`; the UNKNOWN place rule repeats `stg_usaspending_awards.sql` in `transform/tests/test_top_ten_counties_per_person.sql`; the 300-second window arithmetic repeats in `pipeline/lateness.py` and `stream_raw_arrivals.sql`. Oracles restate rules on purpose, so these are follow-ups (N4), not must-fixes.
3. Extension point: `_field_problem` is the field-rule extension point for the consumer (MF-2 adds rules there). No `stages.json` change.
4. Net test lines: +699 under `tests/*.py`, all added (`tests/check_rerun.py` included). Test SQL under `transform/tests/` adds 7 files.
5. R2 and R3 measure records: not produced (see Contracts).

## Follow-ups

- N1. `DECISIONS.md` "Data step" states 21,502 unique events, 12,876 edits, a 3,600 second run, 7,724 awards with a state and no county, 57 with neither, and replay rates of about 370 and about 6 events per second. The build log holds only the 90 second stream run. Attach the 3,600 second run log or the lake counts.
- N2. The real-replay test is skipped in this run. `DECISIONS.md` says it runs "when reachable". No result for it exists.
- N3. `dim_place.missing_places` sets `county_name` to NULL for the 13 codes that are not in the Census file (only UNKNOWN gets a name). Give them a name, or document the NULL.
- N4. Oracle copies of model logic (see Reuse, item 2). Keep for independence, or move the shared CTE into a macro.
- N5. `dim_date` is not used by any mart or test.
- N6. An int `meta.id` lands as text. MF-1 fix covers it.
- N7. A flushed batch whose last accepted event has no `id:` line writes `last_event_id = None`. The next connect then replays from the start. Dedup keeps the counts right, but the replay is slow. Keep the last non-null id.
- N8. `_extract_usaspending` takes `archive.namelist()[0]` as the CSV without a check.
- N9. The tests use paths relative to the repo root (`out/marts/...`, `lake`). They pass only when run from the root.

ARTIFACT: /var/tmp/revieweval/r1-current-vs-pr228/review-01/new_skill/run-1/outputs/final-review-review-01.md VERDICT: NO MERGE
