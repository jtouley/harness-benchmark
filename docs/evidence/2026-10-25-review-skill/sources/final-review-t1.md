# Final review: commit 736d6fe "change under review"

This review merges findings A, B and C, checks them against PR-description.md (the spec), and adds what the
consolidation found. Every item below was re-checked in a scratch clone. The tracked tree was not modified and
nothing was committed. A tested patch that fixes most items is at the end, so the author does not have to work
out the fixes.

Paths used below:
- `$T` = `.../survive/run2/t1/tree` (the PR, untouched).
- Scratch clones `w`, `orig` and `f3`, made with `git clone $T`. They used `$T/.venv` with `UV_NO_SYNC=1`. They are
  deleted now.
- Probe scripts that are still on disk: `.../survive/run2/t1/scripts/` (B), `.../scratchpad/review_t1C/w/` (C),
  `.../scratchpad/review-t1A/` (A).
- Replay: `http://localhost:8099/v2/stream/recentchange` (it was up).

## Verdict

**Request changes.** The batch numbers are correct: all three reviewers checked checks 1 to 4 against independent
Decimal oracles. The stream numbers on the replay are also correct: 21,502 events, 12,876 edits, 60 late and
674 windows. The blocking problems are these:
- The consumer cannot read the live Wikimedia endpoint, which the spec names, and it fails silently when it cannot
  connect.
- A stop or crash in the middle of a flush loses events, which the spec forbids.
- `make stream` fails on a fresh tree.
- The check-7 test never runs, and when it is wired in it exposes a false count on an empty mart.
- The lake does not keep the source data as the spec requires.
- The date dimension is never built.

## How the spec changes the reviewers' spec-dependent findings

All three reviewers marked these findings as blocked because `spec/spec.md` was missing (A-F0, B-F0, C-P0).
Checked against PR-description.md:

| Reviewer item | What the spec says | Result |
|---|---|---|
| Population year not in the published mart (A-F4, B-F7, C-F4) | Amendment A asks only to "use the latest earlier estimate and **say so in DECISIONS.md**". DECISIONS does say so. The "year is recorded" wording comes from the author's own test comment, not the spec. | **Downgraded to LOW.** The only remaining issue is the misleading column name (L4). |
| Check 4 is not answerable from the marts (A-F2) | Check 4: "county totals add up to state totals, and state totals add up to the source total". `oracle_map.yml` must name the table and column for each check. | **Holds, MEDIUM** (M5). |
| `make stream` needs `make build` first (A-F1, B-F3, C-F6) | `make stream` is defined as its own rule. Nothing says it runs after build. | **Holds, MEDIUM** (M1). |
| Lake is not raw (C-F7, A-F9) | "The lake keeps the source's data and adds only load metadata." | **Upgraded to MEDIUM.** The consolidation also found that the stream lake drops most source fields (M4). |
| dim_date is never built (B-F10) | "dimensions for agency, place (state and county) and date." | **Holds, MEDIUM** (M3). |
| Dedup reads stream_raw, not stream_events, against "A-2" (B-F0) | The spec says nothing about where dedup reads from. | **Moot.** The design is fine. |
| Lateness high-water mark over all events | "the highest event time among the events that arrived before it" means all events, not only edits. | **Matches** the code. |
| The A-/G-/N- ids and `spec/spec.md` cited in DECISIONS and `oracle_map.yml` | The PR description has no such ids. | **LOW doc fix** (L5): cite the PR description, or drop the ids. |

## Findings

Severity levels: HIGH means it breaks a spec rule or a deliverable in a realistic run. MEDIUM means a spec gap or a
wrong deliverable. LOW means hardening, docs or nits.

### H1. HIGH. The live endpoint answers 403 because the consumer sends no User-Agent, and every connect failure is silent with exit 0
- Found by: **C** (the silent exit, C-F3). **New** in the consolidation: the 403 from the live endpoint.
- The spec says "In a live demo the same code points at `https://stream.wikimedia.org/v2/stream/recentchange`."
  `http.client` sends no User-Agent, and Wikimedia rejects requests without one. `_read_until` swallows the
  `OSError` raised for the non-200 status. So the live demo would land nothing, print nothing and exit 0. On an
  existing lake it would then republish stale marts.
- **Reproduced:**
  ```
  $ curl -sS -A "" -w "http=%{http_code}\n" https://stream.wikimedia.org/v2/stream/recentchange
  Please set a user-agent and respect our robot policy https://w.wiki/4wJS. See also https://phabricator.wikimedia.org/T400119.
  http=403
  $ curl -sS -m 6 -N -A "some-agent/0.1" ... -> http=200, ":ok / event: message / id: [...]"
  ```
  Next, a local server that returns 403 when the User-Agent is missing, with the PR's `StreamConsumer`:
  `requests: 3 headers sent: {'Host': ..., 'Accept-Encoding': 'identity', 'Accept': 'text/event-stream'}`. It
  returned normally and printed nothing.
  ```
  $ STREAM_URL=http://127.0.0.1:1/nope python -m pipeline.stream_consumer --duration 2   -> rc=0, no output
  $ STREAM_URL=http://localhost:8099/wrong/path python -m pipeline.stream_consumer --duration 2 -> rc=0, no output, no lake/
  ```
- **Fix (verified):** send `User-Agent` (configurable through `STREAM_USER_AGENT`; Wikimedia asks for contact
  info in it), and log each connect failure to stderr. With the patch, the 403 server lands the event (`['u1']`).
  Optionally, exit non-zero when no connection succeeded during the run.

### H2. HIGH. Stopping or crashing during a flush makes the next run read events and then drop them
- Found by: **C** (C-F2, reproduced). **A** reasoned it (A-F7, non-atomic landing plus the pending-package retry).
- The spec says "Stopping and starting the consumer must not count any event twice or lose one." When the process
  dies between dlt normalize and load (Ctrl-C, SIGKILL or OOM in `_flush`), a pending package stays in
  `out/dlt-stream`. The next start builds `seen` and the checkpoint without that package. Its first
  `pipeline.run()` then loads only the old package and ignores the new data. `_flush` still clears the batch and
  moves `last_landed_id` forward.
- **Reproduced** (`python review_t1C/w/pending.py <clone> <tmp>`):
  ```
  after run 1: ['event-000001', 'event-000002', 'event-000003']
  pending package: True
  after restart stream_raw: [... 'event-000004', 'event-000005']        <- 6..10 were read and dropped
  ```
- **Fix (verified):** create the dlt pipeline before reading `seen` and the checkpoint, and call
  `self._pipeline.load()` when `has_pending_data`. After the patch: `stream_raw = event-000001..event-000010`,
  `DUPLICATES: 0 0`. This also covers A-F7's partial-load cases, because the package finishes before the state is
  read. `pipeline/batch_load.py` has the same exposure (C). A `pipeline.load()` before `run()` there would fix it,
  but that is not in the patch.

### M1. MEDIUM. `make stream` fails on a fresh tree unless `make build` ran first
- Found by: **A** (HIGH), **B** (MEDIUM), **C** (LOW-MEDIUM; C did not run it).
- **Reproduced** (fresh clone, no `lake/` and no `out/`):
  ```
  $ make stream DURATION=3
  Runtime Error in model fact_edit (models/star/fact_edit.sql)
    IO Error: No files found that match the pattern "lake/sitematrix_sites/*.parquet"
  Done. PASS=0 WARN=0 ERROR=1 SKIP=14 NO-OP=0 TOTAL=15
  make: *** [Makefile:14: stream] Error 1
  ```
- **Fix (verified):** make the first line of the `stream` target
  `test -d lake/sitematrix_sites || uv run python -m pipeline.batch_load`. A fresh clone with the patch ran
  `make stream DURATION=5` and then `make build`, and both passed. A lighter alternative is a sitematrix-only
  entry point.

### M2. MEDIUM. The check-7 test never runs. Wired in, it shows that `out/marts/late_events` reports 1 late event when there are none
- Found by: **B** (B-F2) and **C** (C-F1, HIGH): the test is not selected. **New** in the consolidation: the
  placeholder row.
- `test_late_events_count` reads `read_parquet('out/marts/late_events/*.parquet')` and has no `ref()`, so neither
  `make` selection nor the DECISIONS "quality gate" runs it.
  **Reproduced:** `dbt ls --select +mart_window_5min +late_events +edits_by_wiki_actor --resource-type test` lists
  10 tests, and this test is not one of them. The DECISIONS gate command does not select it either.
- After adding `-- depends_on: {{ ref('late_events') }}`, the test **failed** on a short run from a fresh lake,
  where there were 0 late edits:
  ```
  13 of 16 FAIL 1 test_late_events_count
  fact_edit late [(0, 1002)]   mart late [(1,)]
  select * from read_parquet('out/marts/late_events/*.parquet') -> [(None, None, None, None, None, None, None, None, None, None)]
  ```
  The PR's original code, with `make stream DURATION=5`, gives the same file. On an empty result, dbt-duckdb's
  `external` materialization writes one all-NULL placeholder row. Only the warehouse view filters it out
  (`... WHERE event_id IS NOT NULL AND ...`). So the dbt `not_null`/`unique` tests pass, while the published file
  (what analysts read, and what `oracle_map.yml` check 7 says to "count rows" of) has 1 row with a NULL key. Any
  other external mart that comes out empty would have the same row.
- **Fix (verified):** add the `depends_on` line, and use `count(event_id)` in the test and in the
  `oracle_map.yml` check 7 recipe, or filter the placeholder when reading. Note the behavior in DECISIONS. With the
  patch, the test passes both on the 0-late run and on the full replay (60 = 60). Also list the `+` selectors
  under "Quality gate" in DECISIONS (C).

### M3. MEDIUM. The date dimension is never built
- Found by: **B** (B-F10, LOW). Upgraded, because the spec requires a date dimension.
- **Reproduced:** `dbt ls --select +mart_monthly_obligations +mart_award_fy2024 | grep dim_date` returns nothing.
  After `make build` the warehouse tables are `['dim_agency', 'dim_place', 'fact_award_transaction',
  'mart_award_fy2024', 'mart_monthly_obligations', 'stg_census_counties', 'stg_usaspending_awards']`, with no
  `dim_date`. Its two key tests never run.
- **Fix (verified):** add `dim_date` to the build selection, giving `PASS=29` (the `dim_date` view is built, and
  `not_null`/`unique` on `date_day` pass). `fact_award_transaction.action_date` is the natural key into
  `dim_date.date_day`. Say so in the docs, or add a `relationships` test.

### M4. MEDIUM. The lake does not keep the source data and adds derived columns
- Found by: **C** (C-F7, timestamp inference and variant columns) and **A** (A-F9, derived columns in
  stream_raw). **New** in the consolidation: the source fields that are dropped.
- The spec says "The lake keeps the source's data and adds only load metadata."
  - **Stream.** **Reproduced:** a replay event has 17 top-level fields (`$schema, bot, comment, id, meta, namespace,
    notify_url, parsedcomment, server_name, server_script_path, server_url, timestamp, title, title_url, type, user,
    wiki`, plus `length`, `revision`, `minor` and others on edits). `lake/stream_raw` keeps only
    `event_id, sse_id, type, namespace, wiki, server_name, timestamp, bot, length_old, length_new`. It adds the
    derived `actor_type` and `net_bytes`, and `stream_events` adds `window_start` and `is_late`. So title, user,
    comment, revision and all of `meta` except `id` are lost.
  - **Batch.** **Reproduced:** in `usaspending_contracts`, dlt typed `period_of_performance_potential_end_date`,
    `initial_report_date` and `last_modified_date` as `TIMESTAMP WITH TIME ZONE`. In assistance it typed the last
    two. It also moved 28 empty strings into a variant column `period_of_performance_potential_end_date__v_text`,
    which gives 300 and 118 columns. DECISIONS says "Values stay strings in the lake", which is false. None of the
    columns the models use is affected, and money is exact.
- **Fix:**
  - Batch (verified): wrap the resources in a `dlt.source` and call
    `source.schema.remove_type_detection("iso_timestamp")`. After the change the lake has 299 and 118 columns, all
    VARCHAR, no variant columns, and the 28 `''` values kept. `make build` gives PASS=29, and `check_rerun` gives
    "2724 rows, 12 data columns unchanged".
  - Stream (not applied, design choice): land the full event in `stream_raw`, for example as a JSON text column
    plus the flattened keys. Move `actor_type`, `net_bytes`, `window_start` and `is_late` into the staging and fact
    models, or say in DECISIONS why the lake carries them. `is_late` depends on arrival order, so it has to be
    computed in the consumer. Documenting it as consumer metadata is reasonable.

### M5. MEDIUM. Check 4 cannot be answered from `out/marts/`, and the batch oracles are not independent of the models
- Found by: **A** (A-F2), **B** (B-F11), **C** (C-F9).
- `mart_monthly_obligations` has no state total and no source total. **Reproduced:** its columns are
  `obligation_key, month_start, state_fips, state_name, county_fips, county_name, state_population_2024,
  county_population_2024, agency_code, agency_name, net_obligations, obligations_per_person`. The `oracle_map.yml`
  check 4 recipe ("compare with the state total ... with the source total") names columns that do not exist. Summing
  county rows by state agrees with itself by construction.
- In the tests, `test_county_state_source_reconcile` takes state totals from `fact_award_transaction` and
  `dim_place`. `test_top_ten_counties_per_person` takes population from `dim_place`, uses a one-way `EXCEPT` and
  has no tie-breaker. All four batch oracles go through the same `usaspending_raw()` macro as the models
  (read from code; all three reviewers agree).
- The numbers are right today. A, B and C each matched checks 1 to 4 with their own Python Decimal oracles reading
  the raw zips and CSVs: check 1 `417=164,522,022.53, 418=166,315,027.20, 474=279,998,069.91, 485=831,182,097.03`;
  check 2 top ten `11001 .. 02164`, with no tie at #10 (38.0228 vs 37.9291); check 3 `1,122`; check 4 every
  (month, state) total matches.
- **Fix:**
  - Publish a small `mart_monthly_state_obligations` (month by state, built straight from the staging rows) plus a
    source-total row or a mart. Point `oracle_map.yml` check 4 at it.
  - In the tests, read population from the census lake tables and the raw columns inline. Make the comparisons
    symmetric, and add `county_fips` as a tie-breaker.

### M6. MEDIUM. One malformed event crashes the consumer on every restart, and wrong-typed fields land inconsistent rows
- Found by: **B** (B-F1 HIGH, B-F5, B-F6) and **A** (A-F6). Downgraded from HIGH: none of the 21,502 replay events
  triggers it (A checked them all), and the live service is well typed. But the failure is permanent once it
  happens.
- **Reproduced** with the PR code (`scripts/probe_poison.py`, `scripts/probe_consumer.py`):
  ```
  1 CRASHED TypeError unhashable type: 'list'    stream_raw: ['e1', 'e2'] checkpoint: ['2']
  2 CRASHED ... 3 CRASHED ...                      (e4, e5 never land)
  [timestamp huge int] CRASHED PipelineStepFailed ... Integer exceeds 64-bit
  [type is a list]     CRASHED TypeError: unhashable type: 'list'
  [bad status line]    CRASHED BadStatusLine: garbage
  ```
  `bot="false"` lands as `bot=True` with `actor_type='human'`, so the check-5 test (which groups by `bot`) and the
  mart (which groups by `actor_type`) would disagree. `namespace="Talk"` lands as a dlt variant column
  `namespace__v_text` with `namespace=NULL`.
- **Fix (verified):**
  - Type checks in `_field_problem`: `meta.id`, `type`, `wiki` and `server_name` must be strings, `namespace` an
    integer within int64, `bot` a boolean, and the integers bounded to int64.
  - `decode("utf-8", errors="replace")`.
  - Catch `http.client.HTTPException` around `_connect`.
  - Set `"bot": event.get("bot") is True`.
  - After the patch, all 13 probe cases complete, and the poison probe lands `['e1','e2','e4','e5']` on the first
    run.

### M7. MEDIUM. Territories are published as state_name 'UNKNOWN', the same label as the no-state sentinel
- Found by: **A** (A-F3), **B** (B-F8), **C** (C-F5).
- **Reproduced** (`mart_monthly_obligations`, `state_name='UNKNOWN'`):
  `60: 8 rows $827,238.00; 66: 15 rows $5,685,941.95; 69: 9 rows $1,382,703.51; 72: 33 rows $12,372,178.72;
  78: 9 rows $740,219.32`. These sit next to the real `UNKNOWN` state (18 rows, $6,296,142.19). 19 rows have a
  NULL `county_name`. The spec asks for totals "by state", and grouping by name lumps about $21.0M of territory
  money into "unknown".
- **Fix:** take the names from `primary_place_of_performance_state_name` and
  `primary_place_of_performance_county_name` (present in the award files, columns 77 and 75 of the assistance CSV),
  or add a 5-row FIPS-to-name seed.

### L1. LOW. A NULL namespace or wiki duplicates rows in the incremental `window_5min`
- Found by: **B** (B-F4, MEDIUM) and **C** (C-F11). Downgraded: the replay has 0 NULLs (C), and the live
  recentchange stream always sends `namespace` on edits.
- **Reproduced** (`scripts/probe_nullns.py`): after the second load, `window_5min` holds
  `(1792021800,'enwiki',...,None,'human',2,...)` and `(...,None,'human',3,...)`, and
  `FAIL 1 unique_combination_of_columns_window_5min_...`. A delete+insert on a key that contains NULL never matches.
- **Fix (verified):** `unique_key='window_start'`. The model already recomputes every row of each touched window,
  so deleting by window alone is correct and safe with NULLs. Keep the 4-column uniqueness test. The probe then
  leaves one row with count 3. Feeding the 13 real replay loads one at a time with a dbt run after each gave 674
  rows, identical to a full build.

### L2. LOW. `mart_award_fy2024` uses `any_value()` for place and agency, and the rerun check covers only one mart
- Found by: **A** (A-F5), **B** (B-F9), **C** (C-F10).
- **Reproduced:** two awards have more than one place:
  `ASST_NON_FEL29493424_418 ['09/09170','09/09009']` and `ASST_NON_21FXDWY001_485 ['56/UNKNOWN','35/UNKNOWN']`.
  A's `anyv.py` on shuffled input returned all four combinations (18/10/4/8 of 40 runs). Rebuilds of the real lake
  were stable (A: 4 runs, B: 6, C: 3), so this is latent. `tests/check_rerun.py` has
  `MART_GLOB = "out/marts/mart_monthly_obligations/*.parquet"` only.
- **Fix:** use `arg_max(..., (action_date, transaction_key))` or a `'MULTIPLE'` value, and compare every
  `out/marts/*` mart in `check_rerun.py`. `dim_agency`'s `first()` (A, C) is the same pattern. It is harmless
  today, because each code has one name.

### L3. LOW. The consumer's command line and timing
- `--duration=60` is ignored silently, and the run uses the 60 s default. Found by **A** and **C**.
  **Reproduced:** parsing `['--duration=1']` gives `60.0`. Fix: use argparse.
- An empty URL path is not defaulted to `/` (A; read from code).
- The 5 s flush is checked only when an event arrives, and the deadline can overrun by up to `SOCKET_TIMEOUT`
  (A-F10; reasoned). C measured that DURATION holds in practice (5.0 s and 31.3 s).

### L4. LOW. `county_population_2024` holds 2021 values for the Connecticut fallback counties
- Found by: **A**, **B**, **C** (downgraded, see the spec table).
- **Reproduced:** 13 mart rows across 6 counties, for example `09001 -> 959768` (the 2021 estimate). The spec only
  asks for a note in DECISIONS, and it is there.
- Optional fix: rename the column to `county_population`, or publish `population_year`.

### L5. LOW. DECISIONS and oracle_map text
- They cite `spec/spec.md` and A-/G-/N- ids that do not exist (A, B, C). Cite the PR description instead.
- "the six Connecticut codes": `stg_census_counties` has **8** 2021 rows (09007 and 09015 as well). Found by
  **A** and **C**. **Reproduced:** `dim_place 2021 rows: 8`. Only six are used by awards.
- "7,724 awards have a state and no county, and 57 have neither": these count transactions (A, confirmed by B and C).
- The "Replay behavior" and "Data step" paragraphs (C-F8). **Reproduced:** a 60 s `make stream` already landed all
  21,502 events. The replay drains in under a minute and then idles, so the "6 events per second over an hour"
  figure is an artifact.
- "Values stay strings in the lake": see M4.
- `oracle_map.yml` check 5 says "one row per actor type". Make it "one row per wiki and actor type that has edits"
  (**B**, **C**).
- `oracle_map.yml` check 2's recipe yields a DOUBLE (**B**). **Reproduced:** `('DOUBLE', 129.0682318262727)` for
  11001. Point it at the exact macro, or publish an FY per-county value.

### L6. LOW. Hygiene
- `tests/test_rerun.py` runs `make build` twice in the real repo root as part of the unit suite (about 50 s; it
  rewrites `lake/` and `out/`). Found by **A**, **B**, **C**; read from code and seen in the suite run. Gate it with
  an env var or use a temp copy.
- Two canary events (no type, timestamp or wiki) land in `stream_raw` (**A**). **Reproduced:**
  `canary in stream_raw: (2, 0, 0)`. They do not affect the marts. Mention them in DECISIONS, or filter them.
- `MissingArgumentsPropertyInGenericTestDeprecation` is printed by dbt (**A**). **Reproduced:** 2 occurrences in
  `dbt.log`. Move the argument under `arguments:`.
- The `obligations_per_person` macro overflows near 1e14 to 1e16 dollars (**B**; reasoned, not reachable).
- The stream tests and the profile use cwd-relative paths (**C**). Document that they run from the repo root.

## Verified, no action needed
(Re-run in the consolidation unless a reviewer is named.)
- `make build`: PASS=26, rc 0, about 11 s. `check_rerun`: "2724 rows, 12 data columns unchanged". Unit suite:
  49 tests OK, including the live-replay test.
- `make stream DURATION=60` after build: PASS=15. `stream_raw` has 21,502 events, all unique. 12,876 edits in
  `edits_by_wiki_actor` (18 rows). 60 late events. 674 windows. One non-JSON event was skipped and logged. These
  match DECISIONS and A's, B's and C's independent SSE oracles (C: 41 restarts converged with 0 duplicates).
- Incremental equals full: B and C did this, and the consolidation repeated it with the 13 real loads.
- Checks 1 to 4 against independent Decimal oracles (A, B, C). Money is exact and every action_date is in FY2024
  (B, C). The half-up rounding of `obligations_per_person` is correct (B fuzzed 3,005 cases with 0 mismatches).
- Every model has a grain description and a key test, and all five published marts have enforced contracts
  (read from `schema.yml`). This is a spec rule, and it holds.
- The window and lateness rules match the spec (event time, 5-minute UTC windows, a strict 600 s threshold, a
  high-water mark over all events).
- The pinned versions are unchanged: `pyproject.toml` is not in the diff.

## Patch we already tested
It covers H1, H2, M1, M2, M3, M4 (batch half), M6 and L1. On a fresh clone with the patch:
- `make stream DURATION=5` and then `make build` both pass (PASS=16 and PASS=29).
- `make stream DURATION=60` gives PASS=16, including `test_late_events_count`, with 21,502 events, 60 late,
  18 per-wiki rows and 674 windows.
- `check_rerun` OK, and the unit suite runs 49 tests, OK.

Still for the author:
- M4 stream half (keep the full event).
- M5 (state and source totals for check 4, independent oracles).
- M7 (territory names).
- L2 through L6.
- Regression tests for H2 and M6. `review_t1C/w/pending.py` and `scripts/probe_consumer.py` can be turned into
  unit tests.

The hunk headers are abridged, so apply these hunks by hand. `git apply` will not take them as written.

```diff
--- a/Makefile
+++ b/Makefile
 build:
 	mkdir -p out/marts/mart_monthly_obligations out/marts/mart_award_fy2024
 	uv run python -m pipeline.batch_load
-	$(DBT) --select +mart_monthly_obligations +mart_award_fy2024
+	$(DBT) --select +mart_monthly_obligations +mart_award_fy2024 dim_date
 
 stream:
+	test -d lake/sitematrix_sites || uv run python -m pipeline.batch_load
 	uv run python -m pipeline.stream_consumer --duration $(DURATION)

--- a/pipeline/batch_load.py
+++ b/pipeline/batch_load.py   (end of load_batch)
-    pipeline.run(
-        [
+    @dlt.source(name="batch_sources")
+    def batch_sources():
+        return [
             usaspending_contracts(),
             usaspending_assistance(),
             census_county_estimates(),
             census_county_estimates_2021(),
             sitematrix_sites(),
-        ],
-        loader_file_format="parquet",
-    )
+        ]
+
+    source = batch_sources()
+    source.schema.remove_type_detection("iso_timestamp")  # keep source strings as strings in the lake
+    pipeline.run(source, loader_file_format="parquet")

--- a/pipeline/stream_consumer.py
+++ b/pipeline/stream_consumer.py
 SOCKET_TIMEOUT = 5.0
+# Wikimedia answers 403 to requests without a User-Agent (https://w.wiki/4wJS).
+USER_AGENT = os.environ.get("STREAM_USER_AGENT", "open-data-pipeline/0.1 (stream consumer)")
 (iter_sse)
-        line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
+        line = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
 (flatten)
-        "bot": bool(event.get("bot")),
+        "bot": event.get("bot") is True,
 (StreamConsumer.__init__: move the dlt.pipeline(...) block from the end to here, then finish pending packages)
         self.clock = clock
+        self._pipeline = dlt.pipeline(
+            pipeline_name="stream_consumer",
+            destination=dlt.destinations.filesystem(bucket_url=self.lake.parent.as_uri()),
+            dataset_name=self.lake.name,
+            pipelines_dir=str(self.lake.parent / "out" / "dlt-stream"),
+        )
+        if self._pipeline.has_pending_data:
+            self._pipeline.load()  # finish a package a crashed run left behind, before reading seen and the checkpoint
         self.seen = set(read_column(self.lake / "stream_raw", "event_id"))
 (_read_until)
-        except OSError:
+        except (OSError, http.client.HTTPException) as exc:
+            print(f"stream consumer could not connect to {self.url}: {exc!r}", file=sys.stderr)
             return
 (_connect)
-        headers = {"Accept": "text/event-stream"}
+        headers = {"Accept": "text/event-stream", "User-Agent": USER_AGENT}
 (validation)
+INT64_MIN, INT64_MAX = -(2**63), 2**63 - 1
+
 def _is_int_or_none(value):
-    return value is None or (isinstance(value, int) and not isinstance(value, bool))
+    return value is None or (isinstance(value, int) and not isinstance(value, bool) and INT64_MIN <= value <= INT64_MAX)
 (_field_problem, before the final return None)
+    if meta is not None and not isinstance(meta.get("id"), (str, type(None))):
+        return "meta.id is not a string"
+    for key in ("type", "wiki", "server_name"):
+        if not isinstance(event.get(key), (str, type(None))):
+            return f"{key} is not a string"
+    if not _is_int_or_none(event.get("namespace")):
+        return "namespace is not an integer"
+    if not isinstance(event.get("bot"), (bool, type(None))):
+        return "bot is not a boolean"
     return None

--- a/transform/models/star/window_5min.sql
+++ b/transform/models/star/window_5min.sql
-    unique_key=['window_start', 'wiki', 'namespace', 'actor_type']
+    unique_key='window_start'

--- a/transform/tests/test_late_events_count.sql
+++ b/transform/tests/test_late_events_count.sql
+-- depends_on: {{ ref('late_events') }}
 ...
-    select count(*) as late_count
+    -- count(event_id): dbt-duckdb writes one all-null placeholder row when the mart is empty
+    select count(event_id) as late_count
     from read_parquet('out/marts/late_events/*.parquet')
```
DECISIONS changes that go with the patch: lake column counts (299 and 118), the quality-gate selectors, the
empty-mart placeholder row, and the User-Agent / `STREAM_USER_AGENT` setting.
