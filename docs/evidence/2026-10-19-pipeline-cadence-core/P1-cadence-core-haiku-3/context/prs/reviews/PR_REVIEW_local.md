RUN_BY_COMMAND: pr-review-local
Last reviewed commit: c6ab925f8ce37da9ee7df64f1dc260e6ee360d0e

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)

# PR review (local): feature/gh-1-pipeline, open data pipeline (gh-1), round 5

Branch: `feature/gh-1-pipeline`. Base: `d07bfe3b039fe0900660b3937031c0b81b4aed47` (`git merge-base origin/main HEAD`).
Head reviewed: `c6ab925f8ce37da9ee7df64f1dc260e6ee360d0e` ("R1 round 4: namespace fits the staging INTEGER type").
Previous review: `Last reviewed commit: 816461a` (round 4 review, now replaced by this file). This review covers the round-4 fix commit (`816461a..c6ab925`, 2 files, +9 / -7) and the whole stream path as it now stands.
PR text: no `PR: local:<path>` record exists in `.context/`. The review uses the plan `.cursor/plans/open-data-pipeline_gh-1.plan.md`, `DECISIONS.md`, and the commit messages as the PR text.
Adapter: `cadence.config.json` sets `"adapter": "none"`. There is no PR number. This is a local review (`/pr-review-local local`). `gh` cannot read a PR because no GitHub remote is configured.
Throwaway workspaces: `git worktree add --detach c6ab925` and `git worktree add --detach 816461a` under the scratch directory (`/tmp/claude-0/-home-user/a08112b2-70f8-5c85-83c0-3c1d7290b3c5/scratchpad/rr4/`). Both use the repo `.venv` through a symlink. The user's tree was not changed.

## Verdict

**NO MUST-FIX at `c6ab925`.** MF-7 from round 4 is fixed. Five nits remain open or carried (N-2, N-3, N-4, N-5, N-6).

- MF-7 (round 4): fixed. The validator now uses the INTEGER range for `namespace`. Values 2**31 and above are skipped and counted, so they never reach the staging cast. Reproduced below.
- Round-4 test change: `test_largest_integer_namespace_lands` now lands `2**31 - 1`, and the `NotAnEventTest` row `{"namespace": 2**31}` expects a skip. A mutation that restores the bigint bound fails the skip test.
- Full unit suite at `c6ab925`: 30 tests, OK.

Status of earlier items:

| Item | Status at c6ab925 | Evidence |
|------|-------------------|----------|
| MF-4 run-level test for odd shapes | Fixed (round 3) | Unchanged. Suite passes. |
| MF-5a timestamp forms the cast rejects | Fixed (round 3) | Unchanged. Suite passes. |
| MF-5a staging-cast test | Partly fixed | `StagingCastTest` covers event time only. The namespace bound is now covered by the validator tests, not by a cast test. See N-6. |
| MF-6 integer outside int64 | Fixed | `namespace` and `length.old` boundaries probed below. |
| MF-7 namespace outside INTEGER | Fixed | Reproduction 1 and 2. |
| N-2 `--duration 0` gives `StreamUnavailable` on a live stream | Open | `run()` not changed. |
| N-3 doc drift (A3, module docstring) | Open, wider | See Contracts. |
| N-4 no test for `verify` exit paths | Open | No test imports `pipeline.verify`. |
| N-5 round-1 nits | Carried | Not in this commit. |

## Must-fix

None.

## Nits

- **N-2.** `run()` with `--duration 0` on a live stream raises `StreamUnavailable`. Carried from round 4. Not changed here.
- **N-3.** Doc drift. See Contracts. Carried and extended.
- **N-4.** No test imports `pipeline.verify`, so its exit paths (exit 1 on failure) have no test. Carried.
- **N-5.** Round-1 nits. Carried.
- **N-6.** `StagingCastTest` runs the cast only on event-time samples. Nothing sends the `namespace` boundary values (`-2**31`, `2**31 - 1`) through the staging cast in `transform/models/stream/stg_recentchange.sql`. The validator tests guard the bound, but the Python literal `INTEGER_MAX` and the SQL `cast(namespace as integer)` are still two sources of truth with no test that joins them. Suggested fix: add a parametrized row to `StagingCastTest` that casts both boundary values with DuckDB, in the same style as the event-time check. This is a row in an existing table, not a new test file.

## Reproductions

Reproduction 1, probe of the validator at `c6ab925` (`pipeline/stream_consumer.py` `_parse_event`):

```
command: python probe (builds one event, varies namespace, calls _parse_event, in the c6ab925 worktree)
namespace 2**31-1     ACCEPTED
namespace 2**31       SKIPPED
namespace -2**31      ACCEPTED
namespace -2**31-1    SKIPPED
namespace 2**63-1     SKIPPED
```

Reproduction 2, the round-4 must-fix at the prior head `816461a`:

```
command: python probe at the 816461a worktree
prior head validator: ACCEPTED (namespace 2**31)
staging cast error: Conversion Error: Type INT64 with value 2147483648 can't be cast because the value is out of range for the destination type INT32
```

At `c6ab925` the same value is skipped before the cast runs. The staging cast on the admitted boundary values passes:

```
command: duckdb: select cast(2147483647 as integer), cast(-2147483648 as integer)
output: [(2147483647, -2147483648)]
```

Reproduction 3, mutation at `c6ab925`: restore the bigint bound for `namespace` (`_is_int_or_none(event.get("namespace"))`).

```
command: sed on pipeline/stream_consumer.py; python -m unittest pipeline.tests.test_stream_consumer; restore file
output: FAIL: test_valid_json_that_is_not_an_event_is_skipped (NotAnEventTest)
        Ran 16 tests. FAILED (failures=1)
```

Reproduction 4, unit suite at `c6ab925`:

```
command: .venv/bin/python -m unittest discover -s pipeline/tests -t . -p 'test_*.py'
output: Ran 30 tests in 57.336s. OK
```

Note: `pytest` is not installed in the repo `.venv`. The suite runs under `unittest`.

## Adversarial inputs

This change touches a stream consumer validator, not a gate, CLI, hook or installer. The hook and installer cases do not apply. The table lists each input for the changed validator. Each result comes from `_parse_event` at `c6ab925`.

| Input | Result | Why |
|-------|--------|-----|
| `namespace` missing | Accepted | `None` is allowed; the cast gives NULL. |
| `namespace` null | Accepted | Same as missing. |
| `namespace` = 2**31 - 1 | Accepted | Largest INTEGER. |
| `namespace` = 2**31 | Skipped, counted | Round-4 fix. |
| `namespace` = -2**31 | Accepted | Smallest INTEGER. |
| `namespace` = -2**31 - 1 | Skipped, counted | Out of INTEGER. |
| `namespace` = "0" (string) | Skipped, counted | Type check. |
| `namespace` = 1.0 (float) | Skipped, counted | Type check. |
| `namespace` = true | Skipped, counted | Bool excluded. |
| `length.old` = 2**63 - 1 | Accepted | bigint column. |
| `length.old` = 2**63 | Skipped, counted | Out of bigint. |
| `length` missing | Accepted | Lengths become NULL. |
| Corrupt JSON | Skipped, recorded by SSE id | `record_skipped` at the consumer loop. |
| Another ticket's leftovers, `--resume`, adjacent id, offline host, no `gh` | Not applicable | No ticket, gate or `gh` path in this change. |

Skipped events go to `checkpoint.record_skipped(event_id)`, so they are counted in `skipped_malformed`. They are not dropped silently.

## Contracts

- `DECISIONS.md` A3 (line 50) says a malformed event is one whose data is not valid JSON, or that has no `meta.id` and `meta.dt`. The code also skips events with wrong field types or out-of-range integers (namespace, bot, length). Those events are recorded and counted the same way. The behavior matches the intent of A3. The text does not. This is N-3, now wider. Fix the A3 wording, not the code.
- The module docstring (`pipeline/stream_consumer.py` lines 12 to 13) says only "not valid JSON" is skipped. Same drift as A3. N-3.
- The new INTEGER bound for `namespace` matches the staging model `cast(namespace as integer)` (`transform/models/stream/stg_recentchange.sql` line 12). It is a contract decision, not a code bug. No written contract sets the namespace type.
- `_is_int_or_none` keeps its bigint default. Other callers are unchanged.

## Design choices

None open. MF-7 is fixed and has no second fix under review.

For the record: the author chose to narrow the validator bound to the staging cast type. The other option was to widen the staging cast to bigint in `stg_recentchange.sql`. That option was not built in a worktree. The chosen option keeps the lake and the staging model in step, and it keeps out-of-range rows out of the checkpoint. The cost is that a real edit with an out-of-range namespace is counted as skipped. Wikimedia namespaces are small, so the cost is low.

## Scope

- Branch `d07bfe3..c6ab925`: 52 files, +2913 / -2. Round 4 alone: 2 files, +9 / -7.
- The branch mixes runtime code (`pipeline/`, `transform/`, `Makefile`) with planning and decision files (`.cursor/plans/`, `DECISIONS.md`, `oracle_map.yml`). For a single feature branch this is acceptable. If it goes out as one PR, the plan and decision files can ship with the feature. No split is needed for this round.
- The title type must match the diff. There is no PR title in this local run. Use `feat:` for the branch as a whole.

## Lookback

Failure class behind MF-7: two bounds for one column live in two places, the Python validator and the SQL cast, and they drift apart. MF-5a (event time) is the same class. The second recurrence means the fix should include a test that joins the two bounds. N-6 asks for that test.

Re-run after the fix:

- Suite on the combined tree (`c6ab925`): 30 tests, OK.
- Boundary probe on the combined tree: the admitted range and the rejected range match the INTEGER bounds.
- Adversarial pass on the combined diff (`816461a..c6ab925`): no new must-fix. Checked the namespace bound, the length bound, the bool exclusion, and the skip path through `record_skipped`.

## End-to-end walk

Run for real:

1. Unit suite at `c6ab925`: cleared (30 tests, OK).
2. Boundary probe through the consumer validator: cleared.
3. Staging cast in DuckDB on the admitted boundary values: cleared.

Not run:

4. `make build`: not run. The batch path is unchanged in this round.
5. `make stream DURATION=...`: not run against the live Wikimedia stream. A 15-second probe of the endpoint returned no status line, so the live path was not verified here.
6. `dbt build --select tag:stream` on a lake with a boundary event: not run end to end. The cast that dbt uses was run directly in DuckDB (step 3). The stream test in `test_stream_consumer.py` covers the landing path up to the parquet file.

## Reuse and extension

Helpers and modules the change reuses:

- `pipeline/tests/fake_sse.py`: `FakeStream`, `make_event` (used by `test_stream_consumer.py`).
- `_is_int_or_none` in `pipeline/stream_consumer.py`: the new bounds are passed as arguments, not copied.

Duplication the change adds or removes:

- None added. The round-4 change adds two constants (`INTEGER_MIN`, `INTEGER_MAX`) and two default-valued parameters on `_is_int_or_none`. The test change renames one test and adds one row to an existing table.

Extension point used: a parameter with a default (`low`, `high`) on the core helper, not a new branch. This is open for extension under `core:dry-extension`, rule 4.

Net change in test lines: +1 (3 lines added, 2 removed, in `pipeline/tests/test_stream_consumer.py`).

Three labeled lists:

- `helpers_reimplemented`: none. `pipeline/tests/test_stream_models.py` defines `events`, `write_fixture`, `dbt`, `warehouse`, `snapshot`. None of these matches a helper in `test_stream_consumer.py` (`batch_files`, `lake_rows`, `ordered_kept_ids`, `batches_by_id`). No shared `tests/conftest.py` exists in this repo.
- `helpers_reused`: `pipeline/tests/fake_sse.py: FakeStream`, `pipeline/tests/fake_sse.py: make_event`, from `pipeline/tests/test_stream_consumer.py`.
- `thin_files`: none. The only changed test file in this round is `pipeline/tests/test_stream_consumer.py` (16 tests).

Note: `lake_rows`, `batch_files` and `ordered_kept_ids` are local to `test_stream_consumer.py`. No other changed test file needs them, so they are not duplicates.
