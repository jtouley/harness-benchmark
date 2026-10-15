# Decisions

Each place the request left a choice open, what this solution chose and why. The answers to the
questions (sections Batch and Stream) are the same choices as any other stack would make; the Spark
section is what this stack adds.

## Batch (Question A)

1. **A transaction is one source row.** The USAspending files hold one row per transaction action. Its
   money is `federal_action_obligation`; `total_obligated_amount` and `total_dollars_obligated` repeat
   the award's running total on every row and are never summed.
2. **Fiscal year 2024** is action dates from 2023-10-01 to 2024-09-30.
3. **Contracts and grants together.** Assistance and contract rows share one fact table with an
   `award_category` column. Award keys of the two kinds never collide (`ASST_` and `CONT_` prefixes).
4. **Agency** is the awarding agency at toptier level (`awarding_agency_code`, `awarding_agency_name`).
5. **Place** is the place of performance, not the recipient's address.
6. **Money is exact.** The lake keeps `federal_action_obligation` as the text the source wrote; staging
   casts it to `DECIMAL(18,2)` (never through a double), and every sum stays a decimal.
   Per-person values are computed in integer micro-dollars (`div`) and stored as `DECIMAL(18,6)`,
   truncated: Spark caps decimals at precision 38, and a decimal quotient can lose scale.
7. **Codes are text.** The batch job never infers CSV types, so county and state FIPS codes keep their
   leading zeros (`01001`).
8. **Transactions without a county** stay in the totals through an unknown member of the place
   dimension: `<state FIPS>-unknown` when the state is known, `unknown` when it is not (foreign places
   and a few domestic rows with no state). The fact always has a place key, so no join is on a null
   key, and county totals add up to state totals, and state totals to the source total.
9. **Population (Amendment A):** the July 1, 2024 estimate (`POPESTIMATE2024`, vintage 2024). Counties
   that vintage 2024 lacks take their latest earlier estimate:
   - Connecticut's eight former counties (`09001` to `09015`). From vintage 2022 the Census Bureau
     publishes Connecticut's nine planning regions (`09110` to `09190`) instead. USAspending uses both
     sets of codes in FY2024, so both stay as separate places: a former county takes its July 1, 2021
     estimate from vintage 2021, a planning region its 2024 estimate. No money is moved between them.
   - Territories (American Samoa, Guam, Northern Mariana Islands, Puerto Rico, US Virgin Islands) have
     no county estimate in either file, so they have no per-person value.
10. **Monthly mart grain** is month x place x agency; per person in a monthly row is that month's net
    obligations divided by the county population.

## Stream (Question B)

11. **An edit** is a `recentchange` event of type `edit` or `new`. `log` and `categorize` events are
    kept in the event fact (`is_edit = false`) but never counted as edits and have no net bytes.
12. **Canary events** (`meta.domain = 'canary'`) are discarded, as Wikimedia asks.
13. **Bot or human** comes from the event's `bot` flag, not from the user name.
14. **Net bytes** are `length.new - length.old`; a new page has no `length.old`, so it counts as 0.
15. **Event time** is the event's `timestamp` (Unix seconds, UTC). `meta.dt` is when the event was
    emitted, not when the change was made. Times in the marts are UTC timestamps without a zone
    (`timestamp_ntz`).
16. **Late events.** The watermark is the largest event time seen so far. Every spooled frame has an
    arrival number (`arrival_seq`, continued across restarts), so staging computes each event's
    watermark at arrival (`watermark_before`) as the largest event time of the frames that arrived
    before it. An event is late when that watermark is more than 10 minutes past the end of its
    5-minute window. Late edits go to `late_events` and never into `mart_edit_windows`. The windows are
    built in dbt, not with a Structured Streaming watermark, which would drop late rows instead of
    counting them. Measuring arrival against the stream's own event time, not the wall clock, makes
    the result the same for a replay at any speed.
17. **Exactly once.** See the Spark section (items 21 and 22). The server re-sends events on a resume;
    the staging model keeps the first landed copy of each `meta.id`, and the incremental fact only
    appends ids it does not have.
18. **Frames that are not JSON**, or are JSON with no `meta.id` (no event can be keyed by them), go to
    `lake/recentchange_rejects/` with their raw text; the consumer keeps going.
19. **Edits per wiki (check 5)** count every edit consumed, late ones included (`mart_wiki_edits`,
    with a `late_edits` column). The 5-minute windows (check 6) count on-time edits only.

## Spark and sbt

20. **Batch job** (`pipeline.Batch`): Spark reads files, not zip members, so each agency zip's CSV is
    extracted to a temporary folder for the run and deleted after. CSVs are read with a header, no
    schema inference, multi-line quoted values and `"` as the escape (RFC 4180, as USAspending writes
    them); the Census files as Latin-1. The site matrix is parsed with Jackson (Spark's own) and lands
    one row per site. Every lake table is written with `SaveMode.Overwrite`.
21. **Stream: a small reader feeds Structured Streaming.** Spark has no SSE source. An SSE client
    thread (`SseClient`, resuming with `Last-Event-ID`) commits what it receives every 2 seconds to a
    spool, `lake/_checkpoints/recentchange/spool/`: one JSON Lines file per flush, written under a
    hidden name and renamed into place, so the frames and the position they end at (the last SSE id,
    the next arrival number) commit in one step. On start the reader resumes after the last spooled
    frame. A frame read but not yet spooled when the consumer stops is read again on the next run.
22. **Stream: landing.** A Structured Streaming query reads the spool as a file source, with its
    checkpoint in `lake/_checkpoints/recentchange/query/`, every 5 seconds. `foreachBatch` splits each
    micro-batch into events and rejects and writes each to its own folder,
    `lake/<table>/batch_id=<N>/`, by overwrite. A batch that ran but did not commit in the checkpoint
    runs again with the same id and the same files after a restart, and replaces its own output. When
    the duration ends, the reader stops and the query lands everything spooled before it stops.
23. **The lake keeps the source.** Batch tables keep every source column as text, plus `source_file`
    (`<zip>/<member>`) for USAspending. Stream tables keep each frame as received (`event`, its JSON
    text) plus load metadata: `event_id` (`meta.id`), `sse_id`, `arrival_seq`, `received_at` and the
    `batch_id` partition. Parquet timestamps are written as microseconds, not INT96.
24. **dbt on the same Spark.** dbt-spark's `session` method starts a local Spark 3.5.9 (pyspark) in
    dbt's process; tables live in `out/warehouse`, the catalog in an embedded Derby metastore in
    `out/metastore_db`, so incremental models keep their state between runs. pyspark ships Spark built
    for Scala 2.12, the ingestion job uses Spark's Scala 2.13 build; the version is the same, and the two
    share only the Parquet lake.
25. **Tests.** `make test` runs the ScalaTest suites: SSE parsing, the spool's atomic commit and
    position, the split of frames into events and rejects, re-landing a micro-batch, CSV reading as
    text (leading zeros, multi-line quotes, Latin-1) and the site matrix flattening, each on small
    in-memory data and a local Spark. `make build` does not run them, so a build stays a build.

## Lake, models, publishing

26. `make build` replaces every batch table in the lake and rebuilds every batch model, so a second
    run leaves the same lake and the same marts. `make build` builds only the batch models; `make
    stream` builds only the stream models (dbt tag `stream`); when the query has no checkpoint
    before the run (a reset lake), it rebuilds them in full, because the window mart's incremental
    filter compares batch numbers, which start over with a new checkpoint. Staging models are tables, not views, so
    Spark reads and types the lake once per run, not once per test; dbt runs four threads on its one
    Spark session.
27. **Publishing.** Every mart is a table in the warehouse; a post-hook copies it to
    `out/marts/<mart>/` with `insert overwrite directory ... using parquet` (one file per mart), so a
    rebuild replaces the folder and never appends. The window mart is incremental with the
    `insert_overwrite` strategy, partitioned by `window_epoch` (the window start in Unix seconds; the
    Hive metastore takes no `timestamp_ntz` partition column): a run recomputes the windows that newly
    landed events touch and replaces only those partitions. The event fact is incremental (`append`).
28. Every mart has an enforced contract (Spark types). Parquet tables enforce no constraints, so keys
    are checked with `not_null`, `unique` and a combined-key test.
