# Decisions

Each entry names a point that the spec left open, or a finding from discovery, and the choice made.

## Phase 1: discovery

### D1. An edit is one `recentchange` event

The spec does not define "edit". Every `recentchange` event counts as one edit. The `type` field stays in the edit fact, so analysts can filter by `edit`, `new`, `categorize`, `log` and other types. Check 5 says "every edit consumed", which supports this reading.

### D2. Money goes to place of performance

The spec does not say whether "where money went" means place of performance or recipient location. The model uses place of performance, from `prime_award_transaction_place_of_performance_state_fips_code` and `prime_award_transaction_place_of_performance_county_fips_code`. The rejected option is recipient location.

### D3. Net negative award means a negative sum per award key

An award is net negative when the sum of `federal_action_obligation` over its FY2024 rows is below zero. The award key is `contract_award_unique_key` for Contracts rows and `assistance_award_unique_key` for Assistance rows. The count is 1,122 in the FY2024 files.

### D4. Contracts and Assistance headers differ

The Contracts files have 297 columns. The Assistance files have 116 columns. Each file type has one column set across all four agencies. The shared columns are the fiscal year, action date, obligation, awarding agency, and place-of-performance columns. The transaction key names differ: `contract_transaction_unique_key` and `assistance_transaction_unique_key`.

### D5. Transaction key and duplicate rule

The transaction key is the file type's transaction unique key (D4). The rule keeps one row for each key. When a key is in both file types, the Contracts row wins. Within one file, the first row in file order wins. Discovery found no duplicate keys inside a file. It found no key that appears in both file types. The rule is still fixed here, so a later data drop with duplicates stays deterministic.

### D6. Arrival order sets lateness

The stream consumer stores an `arrival_seq` for each new event at ingest. Lateness is a function of `arrival_seq`, so a full rebuild gives the same flags. The `arrival_seq` value is ingest metadata. It is not part of the event.

### D7. Money fields stay text in the lake

dlt loads every money field as `VARCHAR`. dbt casts `federal_action_obligation` to `DECIMAL(18,2)`. A cast error fails the build. Discovery checked this with a test load of `-187158.88`. The value stayed the exact text.

### D8. dbt-duckdb `external` supports incremental builds

Discovery built a test model with `materialized='external'` and `incremental`. A second run appended the new row. A model contract with `DECIMAL(18,2)` and `INTEGER` columns was enforced. The plan needs no fallback to DuckDB tables. The mart folders must exist before the build, so the build creates `out/marts/<name>/`.

### D9. Census counties use SUMLEV 050

The census file has 51 state rows (SUMLEV 040) and 3,144 county rows (SUMLEV 050). The model uses SUMLEV 050 rows only. `county_fips` is `STATE` padded to two digits, then `COUNTY` padded to three.

### D10. Population uses July 1, 2024, with a 2021 fallback

Amendment A asks for the July 1, 2024 estimate. Eight Connecticut counties (`09001`, `09003`, `09005`, `09007`, `09009`, `09011`, `09013`, `09015`) have no 2024 row. The 2024 file uses nine planning regions for Connecticut instead (`09110` to `09190`). For these eight counties the population is the 2021 file value, `POPESTIMATE2021`. The `population_year` column records `2021`. Every other FY2024 county has `population_year` 2024. The discovery run found no blank 2024 values in the 2024 file.

### D11. Counties with no place of performance use an `UNK` member

Some Assistance rows have a state code and no county code. Some rows have neither. The `dim_place` table adds an unknown county for each state. Its code is `UNK` plus the state code, for example `UNK08`. A row with no state uses `UNK`. Each unknown county has its own key, so the monthly key stays unique. Those rows keep the totals equal to the source total. Their population is null, so `obligations_per_person` is null for them. Most Assistance rows have no county code. 7,781 of the 9,820 FY2024 transactions use an unknown county code, so county results cover 2,039 transactions.

### D12. Replay findings

- The replay sends each event with an `id:` line that holds a JSON array. The event key is `meta.id`, a UUID.
- The event time is the `timestamp` field, in seconds since the Unix epoch.
- `length` is absent for some event types, such as `categorize`. `length.old` and `length.new` are present for `edit` events.
- A fresh connect without `Last-Event-ID` replays from the first event. The consumer therefore must send `Last-Event-ID` after any restart.
- With `Last-Event-ID`, the replay resends events from a point a few events before the given id. Dedup on `meta.id` is required.
- The replay sends one data line that does not parse, at event 15,839, and keeps the connection open. A cut connection is a different case: its last data line is incomplete at the end of the connection. The consumer keeps a complete line that does not parse as a reject (D33). It resumes only after a cut.
- The replay sends canary events (`domain` is `canary`). They have no `timestamp`, `type` or `wiki`. The reachable replay has two. They stay in the lake. Staging drops them from the edit fact.

### D13. The stream key and the checkpoint share one file

Each micro-batch lands as one set of rows in the lake. Each row carries its `arrival_seq` and the `id:` line of its SSE event. The checkpoint is the `id:` line of the row with the highest `arrival_seq`. Events and checkpoint therefore commit in one file write. The consumer reads the checkpoint from the lake at start.

### D14. Stream duplicate filter and recovery

Before a micro-batch is written, the consumer drops every event whose `meta.id` is already in the lake or in the pending batch. This handles the look-back resume in D12. A kill loses only the pending batch in memory. The next start resumes from the checkpoint in the lake, so those events arrive again and are stored once. A Parquet file that DuckDB cannot read has no footer, so its load did not finish. Startup moves each such file to `lake/stream/_quarantine/`. The tests cover a drop, a duplicate, a stop and restart, and a kill during a flush.

### D22. Stream flush and backoff

A micro-batch lands after 500 new events or 5 seconds, whichever comes first. The consumer reconnects after a drop with a backoff that doubles, capped at 16 seconds. A clean end of the stream also reconnects, until `DURATION` ends. The run flushes the last batch before it exits.

### D23. Canary events stay in the lake

Canary events (`meta.domain` is `canary`) carry no `type` or `timestamp`. The lake stores them as raw JSON, because the lake keeps the source data. Staging drops them from the edit fact.

### D15. Repo config files

`.gitignore` lists `transform/dbt_project.yml` and `transform/profiles.yml`, but git tracks both files. The plan does not change either file.

### D16. The oracle runs as a module

The Phase 1 gate names `uv run python pipeline/oracle.py`. The module imports the `pipeline` package, so the run form is `uv run python -m pipeline.oracle`. The gate meaning does not change.

### D17. Fallback population uses the 2021 file, not the 2023 column

The Phase 4 plan text gives a 2023 example for a county with no 2024 value. The 2024 file has no row for the eight Connecticut counties in D10. Their latest earlier estimate is in the 2021 file. The model uses `POPESTIMATE2021` and `population_year` 2021 for them. A dbt unit test checks this fallback in `int_county_population`.

### D18. Guards for cast errors and contracts

Two Python tests run dbt on a copy of the transform project. One test checks that a cast error fails the build. One test checks that a contract type mismatch fails the build. A control model with valid SQL must pass. A view does not run its cast at build time, so the cast guard model is a table.

### D19. Monthly mart grain and the ratio of sums

The monthly mart has one row for each month, county and agency. `obligations_per_person` divides the row's summed `net_obligations` by `population`, then rounds to two decimals. The top-ten view ranks by the county's total divided by its population. It does not average the monthly ratios. The ranking uses the full ratio, and the output rounds it to two decimals.

### D20. Analyst checks read `out/marts/` only

`pipeline/check_marts.py` prints checks 1 to 4 and a sorted-row hash for each mart. Its checks match `pipeline/oracle.py`. `oracle_map.yml` names the table or view for each check.

### D21. Make targets

`make build` makes the mart folders, runs the batch and runs `dbt build`. Two runs give the same mart hashes.

### D24. Stream models are DuckDB tables with a Parquet post-hook

The Phase 6 plan uses dbt-duckdb's `external` materialization for the stream models. That materializer writes one all-NULL row when a result is empty. An empty stream would then show one phantom edit and one phantom late event. The stream models use DuckDB tables. A post-hook copies each table to `out/marts/<name>/<name>.parquet`. A `COPY` of zero rows writes an empty file. The plan lists this as its fallback. The Parquet outputs are the same. The batch marts keep `external`, because they are never empty.

### D25. Window mart increments from a checkpoint table

The window mart is incremental. The windows that the new arrivals touch are recomputed in full, and `delete+insert` replaces them on the grain key. The checkpoint table `edit_window_checkpoint` holds the highest `arrival_seq` that a finished build read. A pre-hook creates the table. A post-hook writes the new value. A mart column cannot hold the checkpoint, because the contract lists the columns.

### D26. Oracle comparisons for the stream run only with events

The singular tests `fct_edit_counts_match_oracle` and `late_events_match_oracle` compare the lake with the oracle values in the seed. They apply only when the stream has events. With an empty stream, `make build` still exits 0, as the Phase 6 gate requires.

### D27. Build without the partial parse cache

`make build` runs `dbt build --no-partial-parse`. A stale parse cache once hid four stream tests from a build. The flag makes each build parse the whole project.

### D28. Unit tests stand in for crafted seeds

The Phase 6 plan asks for a dbt seed of crafted events. The lateness, NULL bytes and dedup cases are dbt unit tests instead. They take the same inputs and expected rows, and they run in `dbt build`. The 1500 and 1501 boundary cases use `window_start` 600, as Update 1 of the plan says.

### D29. Check 6 uses enwiki

The `dbname` of en.wikipedia.org is `enwiki`. Check 6 filters on `wiki = 'enwiki'`, as Update 2 of the plan says. The window mart has no `server_name` column.

### D30. Full refresh and incremental builds agree

A scratch copy removed the last five stream files, built, restored them, and built again. The incremental result matched the full build, with 15,837 edits, 614 windows and 60 late events. A full refresh gave the same hashes.

### D31. The empty stream table starts through dlt

`make build` writes a zero-row file so the stream models build before any event arrives. dlt fails when its dataset folder exists without dlt's metadata. So the schema step first runs an empty dlt load, which creates the metadata. Then it writes the zero-row file.

### D32. Replay findings after the review

The first version of this consumer treated the malformed line as a disconnect. Every resume then hit the same line, and the stream stalled at event 15,839. A raw read shows the connection stays open past that line. The consumer now keeps reading the same connection. The stall is gone, and the replay's remaining events arrive.

### D33. Rejected data lines

A data line that does not parse is not an event. It is written with its `sse_id` to `lake/stream/_rejected.jsonl`. The consumer counts rejects and prints the count to stderr. Rejects do not enter the lake's event table, and the oracle skips them the same way.

### D34. Exit code for an unreachable endpoint

The consumer exits 1 when no connection to the endpoint ever succeeds. It prints `no connection` to stderr. A run that connects and finds no new events still exits 0.

### D35. Names come from the population source

Each county name comes from the file that gives its population. The eight Connecticut counties on the 2021 fallback keep their names. The top-ten view and the place dimension both read `int_county_population`. The view joins names before it ranks, so no county drops out of the ten.

### D36. Late events contract

`late_events` has an enforced model contract with explicit column types, as the spec requires for each mart.
