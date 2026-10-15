# Shared spec: the open-data pipeline (P1, P2, P3)

Status: **proposed** (2026-10-14). This is the request text. Each of the three tasks
([P1](P1-duckdb-dlt-dbt.md), [P2](P2-config-arrow-polars-datafusion.md), [P3](P3-scala-spark.md)) gives
an arm this spec plus a short stack section. The three tasks answer the same questions from the same
inputs, so their answers must agree ([family](pipeline-family.md#conformance)).

The spec is written the way a lead would hand it to an engineer: complete on outcomes, open on design.
It contains deliberate traps. They are listed only in the hidden [trap catalog](pipeline-traps.md), never
in the text an arm gets.

---

## The request (the text every arm gets)

> Build a pipeline that answers two questions for analysts, from raw public data to columnar tables a
> BI tool can query directly.
>
> **Question A (batch): where did federal contract and grant money go in fiscal year 2024?** In total and
> per person, by state, county, awarding agency and month.
>
> **Question B (stream): how is Wikipedia being edited right now?** Edits per wiki, per namespace and per
> 5-minute window, split by human and bot, with the net bytes added.
>
> ### Inputs
>
> - `data/raw/usaspending/`: USAspending.gov prime award transactions, FY2024, for the agencies listed in
>   `data/raw/usaspending/README.md`.
> - `data/raw/census/`: the Census Bureau county population estimates.
> - `data/raw/sitematrix.json`: the Wikimedia site matrix (wiki id, language, project).
> - The edit stream: a Server-Sent Events endpoint with the Wikimedia EventStreams `recentchange` format.
>   During development and grading it is `http://localhost:8099/v2/stream/recentchange`, a replay of a
>   recorded capture. The replay server behaves like the real service, including disconnects. In a live
>   demo the same code points at `https://stream.wikimedia.org/v2/stream/recentchange`.
>
> ### Architecture
>
> - **Lake.** Ingestion writes every source to a Parquet lake under `lake/` (one folder per source table,
>   partitioned where it helps). The lake keeps the source's data and adds only load metadata.
> - **Models.** A dbt project in `transform/` builds everything after the lake: staging models, the star
>   schema and the marts. Each mart has a dbt model contract (column names and types enforced).
> - **Publish.** The marts are materialized as Parquet under `out/marts/` (one folder per mart). Anything
>   downstream reads only `out/marts/`.
>
> ### Outputs
>
> 1. A star schema for Question A: one fact table at the grain of one award transaction, and dimensions
>    for agency, place (state and county) and date. A monthly mart by state, county and agency, with
>    net obligations, population and obligations per person.
> 2. For Question B: a fact table of edits at the grain of one change event, and a mart of 5-minute
>    windows by wiki, namespace and actor type (human or bot), with the edit count and the net bytes
>    added. The stream consumer lands micro-batches in the lake; incremental dbt models build the edit
>    fact and the window mart from them.
> 3. The lake under `lake/`, the dbt project under `transform/`, and the published marts under
>    `out/marts/`, plus whatever the stack section asks for.
> 4. `oracle_map.yml`: for each question in the "Checks" list below, the table and column (or SQL view)
>    that answers it.
> 5. `DECISIONS.md`: each place where this spec left a choice to you, what you chose and why.
>
> ### Rules
>
> - `make build` runs the batch part from the raw files. Running it twice must not change any output.
> - `make stream DURATION=<seconds>` consumes the stream for that long and updates the stream tables.
>   If the connection drops, the consumer resumes where it stopped. Stopping and starting the consumer
>   must not count any event twice or lose one.
> - Event time, not arrival time, places an edit in a window. Windows are 5 minutes long and start on
>   the multiples of 5 minutes (UTC).
> - Lateness is measured in stream time, not by a clock: an event is **late** when, at its first
>   arrival, the highest event time among the events that arrived before it is more than 10 minutes
>   after the end of its window. A late event is not added to its window; put it in a `late_events`
>   table instead. The replay can run faster than real time, so a wall-clock reading of "late" is wrong.
> - Money is in US dollars, summed exactly (no floating-point sums).
> - Document the grain of each model. Test the keys of each model with dbt tests.
>
> ### Checks the analysts will run
>
> 1. FY2024 net obligations per awarding agency.
> 2. The ten counties with the highest FY2024 obligations per person.
> 3. The number of awards with a net negative obligation in FY2024.
> 4. For one month: county totals add up to state totals, and state totals add up to the source total.
> 5. For the stream: edits and net bytes per wiki for the replayed hour, split human and bot. Late
>    events are included: this check counts every edit consumed, on time or late.
> 6. For the stream: the 5-minute windows with the most edits on `en.wikipedia.org` (on-time edits only).
> 7. For the stream: the count of late events.
>
> ### Amendment A (from the analysts, after the first review)
>
> "Per person" means per resident in the population estimate for **July 1, 2024**, not the 2020 census
> count. Where a county has no 2024 estimate, use the latest earlier estimate and say so in
> `DECISIONS.md`.

---

## Notes for task builders (not given to arms)

- The amendment is part of the request on purpose: a plan made from the first part only uses the wrong
  denominator. It tests whether the plan follows later requirements (trap S1 in the catalog).
- "Exactly once" under disconnects and event time windows are stated as outcomes, and late data as one
  rule. How to get there (offsets, `Last-Event-ID`, dedupe keys, where the watermark is kept) is the
  arm's design.
- The replay server is part of the task, not the solution. It serves a fixed capture and injects
  scheduled faults from a seed (the [catalog](pipeline-traps.md#stream-faults-injected-by-the-replay-server-from-a-seed)).
  Grading uses fixed seeds; development can use any seed.
- The lateness rule is a watermark (the highest event time seen so far), so the late set depends only
  on the capture and the seed, never on replay speed or runner load. The replay server sends the
  captured event times unchanged and may replay faster than real time, so a graded `make stream` does
  not cost an hour. "First arrival" settles F2's re-sent events: a re-sent copy keeps the lateness of
  its first copy. The key must show that the late set is the same whether or not canary events (W1),
  non-edit events and the invalid frame (F5) advance the watermark; where it is not the same, the key
  accepts each reading.
