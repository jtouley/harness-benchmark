Build a pipeline that answers two questions for analysts, from raw public data to columnar tables a
BI tool can query directly.

**Question A (batch): where did federal contract and grant money go in fiscal year 2024?** In total and
per person, by state, county, awarding agency and month.

**Question B (stream): how is Wikipedia being edited right now?** Edits per wiki, per namespace and per
5-minute window, split by human and bot, with the net bytes added.

### Inputs

- `data/raw/usaspending/`: USAspending.gov prime award transactions, FY2024, for the agencies listed in
  `data/raw/usaspending/README.md`.
- `data/raw/census/`: the Census Bureau county population estimates.
- `data/raw/sitematrix.json`: the Wikimedia site matrix (wiki id, language, project).
- The edit stream: a Server-Sent Events endpoint with the Wikimedia EventStreams `recentchange` format.
  During development and grading it is `http://localhost:8099/v2/stream/recentchange`, a replay of a
  recorded capture. The replay server behaves like the real service, including disconnects. In a live
  demo the same code points at `https://stream.wikimedia.org/v2/stream/recentchange`.

### Architecture

- **Lake.** Ingestion writes every source to a Parquet lake under `lake/` (one folder per source table,
  partitioned where it helps). The lake keeps the source's data and adds only load metadata.
- **Models.** A dbt project in `transform/` builds everything after the lake: staging models, the star
  schema and the marts. Each mart has a dbt model contract (column names and types enforced).
- **Publish.** The marts are materialized as Parquet under `out/marts/` (one folder per mart). Anything
  downstream reads only `out/marts/`.

### Outputs

1. A star schema for Question A: one fact table at the grain of one award transaction, and dimensions
   for agency, place (state and county) and date. A monthly mart by state, county and agency, with
   net obligations, population and obligations per person.
2. For Question B: a fact table of edits at the grain of one change event, and a mart of 5-minute
   windows by wiki, namespace and actor type (human or bot), with the edit count and the net bytes
   added. The stream consumer lands micro-batches in the lake; incremental dbt models build the edit
   fact and the window mart from them.
3. The lake under `lake/`, the dbt project under `transform/`, and the published marts under
   `out/marts/`, plus whatever the stack section asks for.
4. `oracle_map.yml`: for each question in the "Checks" list below, the table and column (or SQL view)
   that answers it.
5. `DECISIONS.md`: each place where this spec left a choice to you, what you chose and why.

### Rules

- `make build` runs the batch part from the raw files. Running it twice must not change any output.
- `make stream DURATION=<seconds>` consumes the stream for that long and updates the stream tables.
  If the connection drops, the consumer resumes where it stopped. Stopping and starting the consumer
  must not count any event twice or lose one.
- Event time, not arrival time, places an edit in a window. An event that arrives more than 10 minutes
  after its window ended is not added to that window; count it in a `late_events` table instead.
- Money is in US dollars, summed exactly (no floating-point sums).
- Document the grain of each model. Test the keys of each model with dbt tests.

### Checks the analysts will run

1. FY2024 net obligations per awarding agency.
2. The ten counties with the highest FY2024 obligations per person.
3. The number of awards with a net negative obligation in FY2024.
4. For one month: county totals add up to state totals, and state totals add up to the source total.
5. For the stream: edits and net bytes per wiki for the replayed hour, split human and bot.
6. For the stream: the 5-minute windows with the most edits on `en.wikipedia.org`.
7. For the stream: the count of late events.

### Amendment A (from the analysts, after the first review)

"Per person" means per resident in the population estimate for **July 1, 2024**, not the 2020 census
count. Where a county has no 2024 estimate, use the latest earlier estimate and say so in
`DECISIONS.md`.

Build a small pipeline engine in Python 3.12 and express this pipeline as configuration for it.

- `pipelines/*.yml` declares sources (file, HTTP SSE stream), transforms and sinks. The engine reads the
  YAML and runs it. Adding a new source or mart of the same kinds needs YAML only, no Python.
- Data moves between steps as Apache Arrow tables or record batches (`pyarrow`). Use Polars for
  row-wise and dataframe transforms and Apache DataFusion (`datafusion` Python package) for SQL
  transforms. A transform in the YAML names its engine.
- Sinks write the Parquet lake under `lake/`. The stream sink writes in micro-batches and commits the
  consumer's position in the same step as the data, so a crash between them cannot lose or repeat an
  event.
- The engine does ingestion and the transforms needed to land clean source tables. Everything after the
  lake is the dbt project (dbt-duckdb reading the lake), as the shared spec says. DataFusion has no
  mature dbt adapter, so DataFusion and Polars work on the ingestion side.
- The engine validates each YAML file against a schema before it runs, and reports the file, line and
  problem on an error.
- `make build` and `make stream` call the engine with the matching YAML.

The skeleton pins `pyarrow`, `polars` and `datafusion` in `pyproject.toml`.
