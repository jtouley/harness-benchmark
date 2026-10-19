# Decisions

This file lists each place where the spec left a choice open, and what the pipeline does. It also lists the facts
that Phase 0 checked. Each fact names its source.

## Verified facts (Phase 0)

Source of each fact: a query on the lake, a probe of the replay, or the library docs of the pinned version.

- USAspending: 8 zip files, one CSV each, 9,820 transaction rows (sum of the CSV row counts). Source: `data/raw/usaspending`.
- USAspending key columns differ by file type. Assistance rows use `assistance_transaction_unique_key` and `assistance_award_unique_key`. Contract rows use `contract_transaction_unique_key` and `contract_award_unique_key`. The transaction key is unique within each file type: 9,404 assistance rows and 416 contract rows.
- USAspending amounts: `federal_action_obligation` parses as a decimal in all 9,820 rows. No value has more than two decimal places. The range is -11,416,848.00 to 39,110,267.00. 1,226 rows are negative. These values fit `DECIMAL(18,2)` without rounding (D12).
- USAspending dates: `action_date` runs from 2023-10-01 to 2024-09-30, and every row has fiscal year 2024.
- USAspending place: the state FIPS code has 2 characters in 9,763 rows and is blank in 57 rows. The county FIPS code has 5 characters in 2,039 rows and is blank in 7,781 rows (state-wide places).
- USAspending place codes that the census files do not match: 39 rows have a county code that is absent from the 2024 census file. Sixteen of them are Connecticut counties that exist only in the 2021 file. The other 23 are territory codes. 195 rows have a state code that is absent from the census files (72, 66, 78, 69, 60, or blank).
- Census 2024 file: 3,144 county rows (SUMLEV 050). Every row has `POPESTIMATE2024`. Census 2021 file: 3,143 county rows. It has no 2022 to 2024 columns.
- Census county codes: the 2021 file has 8 Connecticut counties (09001 to 09015) that the 2024 file does not have. The 2024 file has 9 Connecticut planning regions (09110 to 09190) that the 2021 file does not have.
- Site matrix: 1,073 sites, including `aawiki` at `https://aa.wikipedia.org`. The count matches the `count` field of the file.
- Replay: the stream sends `:ok` comment lines. Each event `id` is a JSON array string (topic, partition, timestamp, offset). The ids have no numeric order.
- Replay resume: a request with `Last-Event-ID` gets the event with that id first. The consumer drops that repeat (see A2).
- Replay determinism: two fresh connections gave the same first 200 ids in the same order. The Phase 9 asserts are therefore hard gates (MF-11).
- Replay event time: `meta.dt` and the `timestamp` field differ. In a sample of 300 events, `meta.dt` is 0.02 to 15 seconds after `timestamp` (median 2.2 seconds). The D9 check "they match" fails, and D9 uses `meta.dt` (see D9).
- Replay span: 15,399 consumed events cover 2026-10-14T23:46:52Z to 2026-10-15T00:46:48Z. That is the replayed hour.
- Replay field presence: `bot` is never null (0 of 15,399 rows). Among `edit` and `new` events, `length.new` is never null. `length.old` is null in 412 of 9,210 such events (new pages).
- Replay malformed events: one event sent as truncated JSON on an early resume. A later run did not show it (see A3).
- dlt 1.31.0 filesystem destination: with `layout="{table_name}/{load_id}.{file_id}.{ext}"`, files land in `lake/<dataset>/<table>/`. The dataset folder is always added, so the lake path is `lake/open_data/<table>/`. Replace disposition removes earlier files of that table. Append keeps them.
- dbt-duckdb 1.11.0: relative paths in `profiles.yml` and in `external` locations resolve from the working directory. The Makefile runs from the repository root. The `out/` and `out/marts/` folders must exist before the run.
- dbt 1.11 enforced contracts: each model column must appear in the contract, with its type. `SUM` of `DECIMAL(18,2)` returns `DECIMAL(38,2)`, so the marts cast money back to `DECIMAL(18,2)`.

## Choices from the spec (D1 to D13)

- **D1 Place.** Place is the place of performance (`prime_award_transaction_place_of_performance_*`). Reason: the ticket asks where the money went.
- **D2 Unknown places.** A county code that is in `dim_place` maps to that county. A known state with no matching county maps to the state's `UNKNOWN` county, code `SS000`. Any other place maps to the global `UNKNOWN`, code `00000`. Reason: check 4 needs the state totals to add up to the source total. A state-only award must stay in its state. Foreign codes and territory codes are not in the census files, so they map to the global member.
- **D3 Population.** Population is `POPESTIMATE2024` (July 1, 2024). When a county has no 2024 value, the chain is 2023, then 2022 (both from the 2024 file), then 2021 (from the 2021 file). The pipeline never uses `POPESTIMATE2020` or `ESTIMATESBASE2020`. Eight Connecticut counties have no 2024 county row, so they use `POPESTIMATE2021` from the 2021 file. Those eight rows have `population_source_year = 2021` and `is_population_fallback = true`. The 3,144 counties of the 2024 file all use 2024.
- **D4 Summary level.** Only summary level 050 rows are county rows. Summary level 040 rows are not used.
- **D5 Per person.** Per-person values are ratios: obligations divided by population. The pipeline never sums a per-person column. A state's per-person value uses only counties with a 2024 population, in the numerator and the denominator. This is a narrower rule than MF-5 (see A8).
- **D6 Edit types.** An edit is an event of type `edit` or `new`. Other types do not count as edits, but they count for the watermark (D7).
- **D7 Watermark.** The watermark is the highest event time of all earlier arrivals, any type. Reason: a non-edit event still shows how far the stream has moved.
- **D8 Late events.** An edit is late when its `watermark_before` is more than 10 minutes after its window end. The comparison is strict: an event at exactly 10 minutes is not late. A late edit stays in `fct_edit` with `is_late = true`. It is also copied to the `late_events` table. The window mart counts on-time edits only. In the replay, 0 edits are late (checked by a second scan in arrival order, see the summary).
- **D9 Event time.** Event time is `meta.dt`, read as UTC. Reason: it is the stream's event time field. The `timestamp` field is the revision time, 0 to 15 seconds earlier. The Phase 0 match check failed, so the pipeline does not use `timestamp`.
- **D10 Null lengths.** A null `length.old` or `length.new` adds 0 bytes. The edit still counts. In the replay, 412 edits and new pages have a null old length.
- **D11 Dedupe.** The consumer drops a repeated SSE id before it writes a row (A2). The fact keeps the first arrival of each `meta_id` (`row_number` by `arrival_seq`).
- **D12 Money.** Money is `DECIMAL(18,2)`. Per-person values are `DECIMAL(18,6)`. The Phase 0 check showed that no source value needs rounding.
- **D13 Incremental state.** Incremental tables live in `out/warehouse.duckdb`. Published marts are Parquet, written by the dbt-duckdb `external` materialization. Each incremental model has a full-refresh test (`pipeline/tests/test_stream_models.py`).

## Other choices

- **A1 Stream checkpoint.** The plan named `lake/_state/stream.json`. The checkpoint is a DuckDB file, `lake/_state/stream_checkpoint.duckdb`. It holds the last committed position and the set of recorded SSE ids. A JSON list of every id grows without limit: at the replay's rate, one hour holds about 15,000 ids. A DuckDB transaction keeps the position and the new ids together.
- **A2 Resume rule.** The plan said to drop an event whose id is "at or before" the checkpoint (MF-13). The ids are JSON arrays with no numeric order (Phase 0). The consumer drops an event whose id is already recorded. A resume starts at the last committed id, so the replay sends that event again, and it is dropped. Resends of older events are dropped the same way.
- **A3 Malformed events.** An event whose data is not valid JSON, or has no `meta.id` and `meta.dt`, is skipped. Its SSE id goes into the `skipped` table. A good copy of the same id is still accepted, and the malformed record does not count against it. The run prints `skipped_malformed`, the count of malformed events that no good copy replaced.
- **A4 Deadline.** The reader checks the `--duration` deadline on each line, not only on each event. Reason: the replay can send keep-alive comments with no events. Without the check, a run did not end (observed once, then fixed).
- **A5 Stream writes through dlt.** The ticket asks for dlt in the stream path. Each micro-batch is one dlt run with `append`. Each file carries `_batch_id`, which ties it to the checkpoint. On a start, the consumer deletes any file whose `_batch_id` is above the checkpoint, and it aborts pending dlt packages.
- **A6 Incremental window state.** `edit_windows_5min_state` recomputes a window when `window_start >= latest event time - 15 minutes`. A later on-time edit can only fall into such a window. Older windows cannot change, so they are final. The full-refresh test shows the same result.
- **A7 Late events table.** `late_events` is a dbt `table`, rebuilt from `fct_edit` in each stream run (MF-3).
- **A8 State per person.** The plan (MF-5) said state per person uses all counties with a known population. The eight Connecticut fallback counties carry the same people as the 2024 planning regions, so they would be counted twice. The state ratio therefore uses 2024 counties only, in both terms. The state's obligations from the fallback counties stay in the state totals (check 4).
- **A9 Fixture target.** The stream model tests run on a separate dbt target, `fixture`, at `out/fixture/`. The dev warehouse is never touched by a test.
- **A10 Make targets.** `make build` runs the batch ingestion and the batch models (`--exclude tag:stream`). `make stream` runs the consumer, then the stream models (`--select tag:stream`). `make build` does not depend on the stream lake.
- **A11 Acceptance.** The determinism gate (Phase 0) passed. The Phase 9 restart asserts therefore run as hard gates. The restart check is `python -m pipeline.verify restart`.
- **A12 Exit codes.** A run where the stream never answers exits with an error (`StreamUnavailable`). `pipeline.verify stream` and `pipeline.verify hash` exit 1 when a check fails.
