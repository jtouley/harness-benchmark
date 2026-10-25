RUN_BY_COMMAND: pr-review-local
Last reviewed commit: c176f99dc309b01a2e353856ebc599a32840f8e4
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)

# PR review: branch `review` against `base` (local)

Verdict: **NO MERGE**. Five must-fix items. The review ran without the Cadence gates and without the ledger append, as the run instructions asked. Nothing was written to the findings ledger.

Scope of the review: branch `review` at c176f99 against `base` at d176e80. The merge base is d176e80. The diff is 45 files, +2085 / -2 lines, in one commit ("Change under review"). The PR text is `DECISIONS.md` and `oracle_map.yml`. No `spec/spec.md` is in the repo copy (see Contracts).

## Must-fix items

### MF-1. Stop and restart tests pass when the consumer lands nothing

- Location: `tests/test_stream_consumer.py`, `test_consumer_stopAtDuration_landsContiguousPrefixWithoutDuplicates` and `test_consumer_restartAfterStop_neverCountsAnEventTwice`. Also `test_consumer_replayAtLocalUrl_landsUniqueEdits` (same assertion shape).
- Evidence: each test compares `raw` with `sent_unique[: len(raw)]`. When `raw` is empty, the slice is empty, so the comparison holds. The only guard is `assertTrue(replay.sent)`, which checks the fake server, not the consumer.
- Reproduction (mutant: `StreamConsumer._flush` replaced by a no-op, so nothing is ever landed):
  ```
  python -m unittest (the two tests above, with the mutant patched in)
  Ran 2 tests in 2.686s
  OK
  ```
  Both tests pass against a consumer that lands zero events.
- Fix: assert that `len(raw) > 0` and that `len(raw)` equals the number of events the consumer accepted before the deadline. Do not accept a prefix of any length.
- Test that proves the fix: the mutant above must fail both tests.

### MF-2. The consumer exits 0 and lands nothing when the stream endpoint is down

- Location: `pipeline/stream_consumer.py`. `_connect` raises `OSError`, `_read_until` catches it with `except OSError: return`, and `run()` returns normally.
- Reproduction (no listener on the port):
  ```
  StreamConsumer(lake_dir=..., url="http://127.0.0.1:<closed port>/v2/stream/recentchange", duration=1.0, reconnect_seconds=0.1).run()
  run() returned normally; lake exists: False
  exit=0
  ```
  `make stream` with a wrong `STREAM_URL` therefore reports success. Nothing is logged for the failed connections.
- Impact: the failure shows up only later, when dbt reads a stream folder that does not exist.
- Fix: log each failed connection to stderr. When the deadline passes with no successful connection, raise or exit non-zero. Give `main()` the same exit code.
- Test that proves the fix: a run against a closed port must raise (or `main` must exit non-zero). A run against FakeReplay must still return 0.

### MF-3. Batches are not flushed by time when the stream is quiet

- Location: `pipeline/stream_consumer.py`. `_batch_full` (the time check) runs only after `_accept`. `_read_until` calls `_accept` only for parsed events. Heartbeat and comment lines never reach `_batch_full`.
- Contract: `DECISIONS.md`, "Landing": "A batch is flushed every 2,000 events, every 5 seconds, on every disconnect and at the deadline."
- Reproduction (one event, then heartbeats only; `batch_seconds=0.2`):
  ```
  t=1.5s, batch_seconds=0.2, one event then heartbeats only: landed rows = 0
  after deadline: landed rows = 1 elapsed 3.17
  ```
  The event waits until the deadline. The 5-second rule is not met.
- Effect: landing latency. On a crash during a quiet period, the events read are re-read on restart, because the checkpoint did not move. Data is not lost, but the written contract is false.
- Fix: run the time check on every line read, including heartbeats. Two reasonable fixes exist (a time check per line, or a socket timeout that triggers a flush). The scenario matrix was not built in this run.
- Test that proves the fix: extend `test_consumer_heartbeatsOnly_stopsAtDuration` with a `batch_seconds` value and assert that the event lands before the deadline.

### MF-4. The check-2 oracle shares the macro under test and reads a model

- Location: `transform/tests/test_top_ten_counties_per_person.sql`. The `expected` CTE calls `{{ obligations_per_person(...) }}`, the same macro that the mart uses. It takes the county population from `{{ ref('dim_place') }}`, a model.
- Contract: `DECISIONS.md` says the oracles are "read from the raw lake, not from the models". The same paragraph cites "The Python `Decimal` check agrees with the mart for the top counties" (line 57). No such check exists in the repo (grep for `Decimal` finds only that line).
- Evidence on the macro: I emulated the integer formula in `obligations_per_person.sql` and compared it with Python `Decimal` ROUND_HALF_UP over 200,000 random cases (cents from -1e12 to 1e12, population from 1 to 1e8). Result: 0 mismatches. The macro arithmetic is correct today.
- Why this is still must-fix: the expected and actual sides call the same macro, so any change to the macro gives the same output on both sides. The test cannot fail on a rounding regression. A population error in `dim_place` also passes.
- Fix: compute the expected per-person value without the macro, for example with Python `Decimal` in the test or with a separate SQL formula. Take the population from the raw Census file, not `dim_place`. Remove the claim about a Python check, or add that check to the repo.
- Test that proves the fix: a mutant macro that rounds half to even must fail `test_top_ten_counties_per_person`.
- The dbt tests were not run in this review (see Reproductions). This finding rests on reading the SQL, the macro emulation and the grep.

### MF-5. A test helper copies two stream helpers

- Location: `tests/test_stream_consumer.py`, `_replay_ids`. Its inner `lines()` generator repeats `pipeline/stream_consumer.py::_lines`. Its HTTP connect and request repeat `StreamConsumer._connect`.
- Evidence: `grep -rn "def lines\|_lines" pipeline tests` finds `_lines` in `pipeline/stream_consumer.py` (line 275) and `def lines()` in `tests/test_stream_consumer.py` (line 136).
- Rule: `core:dry-extension` item 1 (reuse a shared helper). `review-rigor.md`: "A new helper that duplicates an existing one is a must-fix. Merge it into the existing one."
- Fix: call `_lines(resp, time.monotonic, deadline)` from the pipeline module. Reuse `StreamConsumer._connect` if it is made usable from the test, or move the connect code into a shared function that both call.
- Test that proves the fix: `tests.test_stream_consumer` passes unchanged. `grep -n "def lines" tests` returns nothing.

## Nits

- N-1. `flatten` uses `bool(event.get("bot"))`, and `actor_type` uses `event.get("bot") is True`. A non-boolean `bot` value gives `bot=True` with `actor_type=human` (reproduced: `"bot": "false"` gives bot True, actor human). `_field_problem` does not reject a non-boolean `bot`. The test oracle uses the `bot` column and the model uses `actor_type`, so they disagree on this input. Fix: reject a non-boolean `bot` in `_field_problem`, with a test in `tests/test_stream_parsing.py`.
- N-2. `pipeline/batch_load.py::_extract_usaspending` reads `archive.namelist()[0]` and drops any other member. All eight raw zips hold one CSV, so no fault shows today. `_csv_row_count` in `tests/test_batch_load.py` makes the same assumption, so the test cannot catch it. Fix: require exactly one CSV member and raise otherwise.
- N-3. `pipeline/stream_consumer.py::main` reads `argv[argv.index("--duration") + 1]`. A missing or non-numeric value gives IndexError or ValueError with no usage message. Not tested.
- N-4. `_read_until` drops an SSE event that is cut off at the deadline. `DECISIONS.md` says "no event that it read is lost". A cut-off event is not complete, so this is probably correct, but the document does not say so.
- N-5. The skipped malformed event (build log, `make stream`) is logged by reason and SSE id only. Its payload is not kept, so it cannot be inspected later.
- N-6. `transform/tests/test_late_events_count.sql` reads `out/marts/late_events/*.parquet` through a relative path. The other tests use the `lake_dir` variable. The test depends on the working directory.
- N-7. `test_consumer_missingLength_countsOneEditWithZeroBytes` asserts net bytes for two events. The name is wrong. Minor.
- N-8. `mart_award_fy2024` uses `any_value` for state and county. An award with transactions in more than one place gets an arbitrary place. `dim_agency` uses `first(agency_name)`, which is also not deterministic. The published mart does not claim one place per award, so this is a nit.

## Reproductions

Commands run in the review copy (`/var/tmp/revieweval/antagonistic-vs-baselines/review-01/old_skill/run-1/repo`). I did not run `make build`, `tests/check_rerun.py`, `tests/test_rerun.py` or dbt. The build log was read as evidence.

1. `uv sync --frozen`: installed 81 packages, exit 0. This created `.venv` in the copy. It is ignored by git.
2. `uv run --frozen python -m unittest tests.test_stream_parsing tests.test_batch_parsing tests.test_lateness tests.test_stream_consumer`:
   ```
   Ran 42 tests in 15.957s
   OK (skipped=1)
   ```
   The skip is `test_consumer_replayAtLocalUrl_landsUniqueEdits`. The live replay at localhost:8099 is not running in this session.
3. `uv run --frozen python -m unittest tests.test_batch_load`: `Ran 6 tests`, `OK`. This loads the raw files into a temp lake. It is not the build.
4. MF-1 mutant (`_flush` no-op), two tests: `Ran 2 tests in 2.686s`, `OK`.
5. MF-2 unreachable endpoint: `run() returned normally; lake exists: False`, exit 0.
6. MF-3 quiet stream (`batch_seconds=0.2`): `landed rows = 0` at 1.5 s, `landed rows = 1` after the deadline at 3.17 s.
7. MF-4 macro check (Python emulation of the integer formula against `Decimal` ROUND_HALF_UP, 200,000 cases): 0 mismatches.
8. N-1 non-boolean `bot`: `problem: None | bot: True | actor_type: human`.
9. Raw zips: 8 zips, each with exactly one member (`namelist()` length 1, no directory entries).
10. Build log (`/var/tmp/revieweval/antagonistic-vs-baselines/review-01/build.log`), read only: `make build` passed with PASS=26 and ERROR=0. `make stream DURATION=90` passed with PASS=15 and ERROR=0. One malformed event was skipped.

## End-to-end walk

No `docs/quickstart.md` exists in the repo. The walk follows the Makefile targets and `DECISIONS.md`.

| Step | Cleared | Basis |
|---|---|---|
| `uv sync --frozen` | yes | run now (item 1) |
| `make build` | yes | build log only; not re-run |
| `make stream DURATION=90` | yes | build log only; not re-run. Stream tests and checks 5 to 7 passed in the build log. |
| Unit tests (stream, parsing, lateness, batch load) | yes | run now (items 2 and 3) |
| Live replay test | not run | replay not running in this session |
| `tests/check_rerun.py` (two `make build` runs) | not run | excluded by the run instructions |
| Check 3 to 7 oracles, dbt singular tests | not run now | build log shows PASS for the marts; the oracle issues are in MF-4 |

No PR test-plan items exist in the repo, so none are open.

## Adversarial inputs

Stream CLI (`pipeline.stream_consumer`):

| Input | Result |
|---|---|
| Missing `STREAM_URL` | Falls back to `.env.example`. Tested. |
| Corrupt data (not JSON, wrong types, bad length, bad timestamp) | Skipped with a logged reason; the stream continues. Tested. |
| Event without timestamp | Lands; not counted as late. Tested. |
| Replayed event on reconnect | Lands once. Tested. |
| Resume after disconnect (`Last-Event-ID`) | Sent with the checkpoint id. Tested. |
| Restart with an existing lake | High-water mark and seen set restored. Tested (`restartAfterStop`), but see MF-1. |
| Adjacent id (`cd-1` vs `cd-12`) | Not applicable; the stream uses `meta.id`. |
| Endpoint down | Exits 0 with nothing landed. Fails. See MF-2. |
| Quiet stream | Batch waits until the deadline. Fails. See MF-3. |
| Non-boolean `bot` | Rows disagree (N-1). |
| `--duration` without a value | Unhandled (N-3). |

Batch CLI (`pipeline.batch_load`):

| Input | Result |
|---|---|
| Missing listed zip | Raises `FileNotFoundError`. Tested. |
| Zip with two members, or a directory first | Drops rows silently (N-2). Not tested. |
| Census file in Latin-1 | Read as Latin-1. Row counts tested. |

No installers, hooks or gates are in this change.

## Contracts

- `spec/spec.md` is named by `oracle_map.yml`, and the A-, G- and N- ids appear in `DECISIONS.md`. The file is not in the repo copy. I could not check the A-, G- or N- ids against the spec. `DECISIONS.md` is the only written contract in the repo, so I checked the code against it.
- `DECISIONS.md` versus code:
  - Five-second flush: contradicted (MF-3).
  - Oracles read from the raw lake: contradicted for check 2 (MF-4). Check 4 uses the fact table for state totals; `DECISIONS.md` says so.
  - "The Python `Decimal` check agrees": no such check exists (MF-4).
  - Lateness rule ("more than 600 seconds after the window end", `is_late`): consistent between `pipeline/lateness.py`, the consumer and the SQL macro `stream_raw_arrivals`.
  - Per-person rounding "exact": consistent (MF-4 macro check).
  - Dedup on `meta.id` in `stream_raw`: consistent.
  - "No event that it read is lost" on stop: see N-4.
- `core:standalone-package`: no reads of `~/.cursor`, `~/`, `/root` or `CADENCE` paths in the repo. The only host-path read is `.env.example` inside the repo. No finding.
- `core:implement` (TDD rules of E1): the test files cover the seam contracts for the stream and the batch. Test quality issues are MF-1 and MF-4.
- `cadence.config.json`: not in the repo. The `layer_map` and `test_shape` rules could not be applied.
- Bugs (ruff) and types (mypy) records: the tools did not run in this review, so there is no record to cite. Not run.

## Design choices

- MF-2: two reasonable fixes (log and raise, or raise only when no connection succeeded). The scenario matrix was not built in this run. The author should choose and record the matrix in the next round.
- MF-3: two reasonable fixes (time check per line, or a socket-timeout flush). Same status.
- MF-1, MF-4, MF-5: one clear fix each. No matrix needed.

## Scope

- 45 files, +2085 / -2 lines, one commit, no PR title in the repo.
- The change has two features that do not share code paths: the batch load and marts (question A, `make build`) and the stream consumer and stream marts (question B, `make stream`). The docs (`DECISIONS.md`, `oracle_map.yml`) describe both.
- Recommendation: split into two PRs, batch first, stream second. The batch code has no stream dependency.

## Lookback

Failure classes behind the must-fix items:

1. Tests that pass on empty output (MF-1). Check each "same as prefix" or "same as subset" assertion for the empty case.
2. Fail-open on an unreachable dependency (MF-2). Every connection error path must end in a visible failure.
3. Written design that is not enforced in code (MF-3). Every number in `DECISIONS.md` that describes behavior needs a test.
4. Oracles that share the code under test (MF-4). An oracle must use an independent formula and independent inputs.
5. Copy-pasted helpers (MF-5). Grep for a helper's body before writing a test helper.

The combined tree was not re-tested after fixes, because no fixes exist yet. The lookback pass on the combined tree is due after the fix round.

## Reuse and extension

1. Reused helpers: `pipeline.stream_consumer` (`iter_sse`, `flatten`, `read_table`, `read_column`, `_field_problem`, `_lines`), `tests/stream_harness.py` (`FakeReplay`, `make_event`, `StreamTestCase`), `pipeline.batch_load` (`_read_csv`, `_listed_zip_names`), and the dbt macros `usaspending_raw`, `stream_raw_arrivals` and `obligations_per_person`. The test oracles reuse `usaspending_raw` and `stream_raw_arrivals`, which is good reuse, but `obligations_per_person` is also reused by the oracle (MF-4).
2. Duplication added: `tests/test_stream_consumer.py::_replay_ids` duplicates `_lines` and the connect code (MF-5). `tests/test_batch_load.py::_text_row_count` and `_csv_row_count` both count CSV rows with their own readers. The copies are small. `transform/macros/unique_combination_of_columns.sql` re-implements a dbt-utils test; the file says why (dbt-utils is not a dependency). Duplication removed: none.
3. Extension point: the change adds Makefile targets with `DURATION` as a parameter, and `STREAM_URL` read from the environment. No new `stages.json` field or pack gate.
4. Net test lines: Python tests 699 lines (`tests/`). The dbt singular tests (9 files in `transform/tests/`) were not counted.
- R2 record (`scripts/test_shape.py --change`): not produced. The run skipped the gates. No verdict is cited.
- R3 record (`scripts/cognitive_complexity_gate.py`): not produced. No verdict is cited.

ARTIFACT: /var/tmp/revieweval/antagonistic-vs-baselines/review-01/old_skill/run-1/outputs/final-review-review-01.md VERDICT: NO MERGE
