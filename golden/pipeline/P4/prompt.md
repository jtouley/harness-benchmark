Build a pipeline that answers one question for the library's analysts, from the raw exports to
columnar tables a BI tool can query directly.

**Question: how were the branches used in 2025?** Checkouts, late returns, fines and what is still
out, by branch, item, patron and month.

### Inputs

- `data/raw/branches.csv`: the twelve branches (code, name, region).
- `data/raw/items.csv`: the catalog (item id, title, category, home branch, replacement cost).
- `data/raw/patrons.csv`: the patrons (patron id, home branch, year joined).
- `data/raw/loans_2025_h1.csv` and `data/raw/loans_2025_h2.csv`: the loan events of 2025 exported in
  two halves, one row per event (`checkout`, `renew` or `return`), with the event time in UTC.
- `data/raw/fines.csv`: the fines, one row per fine assessed or waived, with the amount in dollars.

### Architecture

- **Lake.** Ingestion writes every source to a Parquet lake under `lake/` (one folder per source
  table). The lake keeps the source's data and adds only load metadata.
- **Models.** Everything after the lake is built in DuckDB: staging models, a fact table of loans
  and the marts. Document the grain of each model.
- **Publish.** The marts are written as Parquet under `out/marts/` (one folder per mart). Anything
  downstream reads only `out/marts/`.

### Outputs

1. A fact table at the grain of one loan (one checkout), with its branch, item, patron, checkout
   time, return time, number of renewals and due time.
2. Marts that answer the checks below: checkouts per branch, checkouts per item, late returns,
   fines per month and branch, active patrons per home branch, and the items on loan at the end
   of the year with their replacement cost.
3. The lake under `lake/`, the model code, and the published marts under `out/marts/`.
4. `oracle_map.yml`: for each question in the "Checks" list below, the table and column (or SQL
   view) that answers it.
5. `DECISIONS.md`: each place where this spec left a choice to you, what you chose and why.

### Rules

- `make build` runs the whole pipeline from the raw files. Running it twice must not change any
  output.
- A loan event is one row of a loans file. An event that appears in both files, with the same loan
  id, event and time, is one event.
- A loan of 2025 is a checkout event in the files. A return or a renewal whose checkout is in no
  file belongs to a loan from the year before.
- A loan is due 21 days after its checkout, plus 21 days for each renewal before its return. A
  return after the due time is late.
- Money is in US dollars, summed exactly (no floating-point sums). A negative fine row is a waiver,
  and it counts in every sum.
- Codes are text: a branch code keeps its leading zero.

### Checks the analysts will run

1. Checkouts per branch in 2025 (the branch of the checkout event).
2. The ten items with the most checkouts in 2025, ties in item id order.
3. The number of loans of 2025 returned late.
4. For March 2025: net fines per branch add up to the system total for the month.
5. Net fine income per month, over every fine in the file.
6. Active patrons per home branch: patrons with at least one checkout in 2025, counted by the
   branch they belong to.
7. The replacement value of the items on loan at the end of 2025: the items whose last event of
   the year is a checkout or a renewal.

Use Python 3.12 and DuckDB for every step: land the raw files in the Parquet lake, build the models
in DuckDB (SQL or the Python API) and write the marts as Parquet. The skeleton pins the versions in
`pyproject.toml`; do not change them.
