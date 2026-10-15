# Decisions

Each place the request left a choice open, what this solution chose and why. The answers to the
questions (sections Batch and Stream) are the same choices as any other stack would make; the engine
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
6. **Money is exact.** CSV columns are read as text; a Polars transform casts
   `federal_action_obligation` from that text to `DECIMAL(18,2)` (never through a float), and staging
   keeps it a decimal.
   Per-person values are computed in integer micro-dollars and stored as `DECIMAL(18,6)`, because
   DuckDB turns decimal division into `DOUBLE`.
7. **Codes are text.** The engine never infers CSV types, so county and state FIPS codes keep their
   leading zeros (`01001`).
8. **Transactions without a county** stay in the totals through an unknown member of the place
   dimension: `<state FIPS>-unknown` when the state is known, `unknown` when it is not (foreign places
   and a few domestic rows with no state). So county totals add up to state totals, and state totals
   add up to the source total.
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
    emitted, not when the change was made.
16. **Late events.** The watermark is the largest event time seen so far. Every landed frame has an
    arrival number (`arrival_seq`, continued across restarts), so staging computes each event's
    watermark at arrival (`watermark_before`) as the largest event time of the frames that arrived
    before it. The engine stays general: it records arrival order, not a property of this stream. An event is late when that
    watermark is more than 10 minutes past the end of its 5-minute window. Late edits go to
    `late_events` and never into `mart_edit_windows`. Measuring arrival against the stream's own
    event time, not the wall clock, makes the result the same for a replay at any speed.
17. **Exactly once.** Each micro-batch commits in one step: its Parquet files are written, then the
    checkpoint `lake/_checkpoints/stream.json` (batch number, last SSE id, next arrival number) is
    replaced by an atomic rename. On start the engine deletes any file numbered above the checkpoint
    (a batch that never committed) and resumes from the saved id with `Last-Event-ID`. The server re-sends events on a resume; the staging model
    keeps the first landed copy of each `meta.id`, and the incremental fact only appends ids it does
    not have.
18. **Frames that are not JSON** go to `lake/recentchange_rejects/` with their raw text; the consumer
    keeps going.
19. **Edits per wiki (check 5)** count every edit consumed, late ones included (`mart_wiki_edits`,
    with a `late_edits` column). The 5-minute windows (check 6) count on-time edits only.

## The engine

20. **Pipelines are data.** `pipelines/batch.yml` and `pipelines/stream.yml` declare sources, transforms
    and sinks; `engine/` runs any such file and never branches on a pipeline's name or tables. Kinds:
    sources `file` (CSV or JSON, globs, a zip read member by member) and `sse`; transforms `polars`
    (filter, JSON fields, SQL expressions, casts, rename, select) and `datafusion` (one SQL statement
    over named inputs); sink `parquet` into `lake/<table>/`. A new kind is one function and one schema
    entry. Run one file with `uv run python -m engine run pipelines/<file>.yml` (`--duration` for a stream).
21. **Validation.** `engine/pipeline.schema.yml` (JSON Schema 2020-12) checks each file's shape; the
    engine then checks that every name a step reads is made by an earlier step and that a lake table is
    written once. Every problem is printed as `<file>:<line>: <problem>`, exit code 2, before anything
    runs. `make build` and `make stream` validate every file under `pipelines/` first.
22. **Which engine does what.** Polars types the USAspending text (money to `DECIMAL(18,2)`, dates)
    and pulls the event id out of each stream frame; DataFusion SQL types the Census estimate of each
    vintage. Everything else is dbt.
23. **The lake keeps the source.** Batch tables keep every source column (text unless typed above)
    plus `source_file` for USAspending. Stream tables keep each frame as received (`event`, its JSON
    text) plus load metadata: `event_id`, `sse_id`, `arrival_seq`, `received_at`, `_batch`. The site
    matrix lands as one row per group of the `sitematrix` object (`key`, `value` as JSON text).
24. **Polars 2 has no text-to-date cast**, so a `cast` to `date` or `timestamp` from text parses it
    (`str.to_date`, strict). All casts are strict: a value that does not convert stops the run.

## Lake, models, publishing

25. `make build` replaces every batch table in the lake (written beside the old one, then swapped in by
    renames), so a second run leaves the same lake and the same marts. `make build` builds only the
    batch models; `make stream` builds only the stream models (dbt tag `stream`).
26. Batch marts use dbt-duckdb's `external` materialization (one Parquet folder per mart). The stream
    marts are incremental or rebuilt tables, which `external` cannot be, so a post-hook copies each
    to its folder under `out/marts/`.
27. Every mart has an enforced contract. dbt-duckdb rejects constraints on external models, so keys
    are checked with `not_null`, `unique` and a combined-key test.
