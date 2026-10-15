# Follow-up task: a new data mart and a dashboard (P1f, P2f, P3f)

Status: **proposed** (2026-10-14, owner direction). It measures extensibility directly: how well the
system an arm built takes the next change ([quality model](../quality-model.md#owner-criteria-2026-10-14-dry-solid-extensible-traceable-cheap)).

The arm that built the base task gets this request on its own delivered repository, in a new session,
after the base task is graded. It never sees this request before. The base result is frozen first, so
the follow-up cannot change the base score.

## The request (the text every arm gets)

> The analysts want two more things on top of the pipeline in this repository.
>
> **1. A recipient concentration mart.** For each state, county and month of fiscal year 2024: the number
> of distinct recipients, the share of net obligations that went to the top 10 recipients, and the change
> in net obligations from the previous month. Recipients are identified by their UEI; where the UEI is
> missing, use the recipient name, and count how many rows that applies to.
>
> **2. A dashboard.** A Streamlit app (`make dashboard` starts it) with two pages:
> - *Federal spending*: filters for state, agency and month; a table of the concentration mart and a
>   chart of net obligations per person by county.
> - *Wikipedia edits*: the latest 5-minute windows by wiki, human against bot, refreshed while
>   `make stream` runs.
>
> The new mart is a dbt model with a contract, published under `out/marts/` like the others. The
> dashboard reads only `out/marts/`, never the lake, the raw data or dbt's internal tables. Add the new
> mart to `oracle_map.yml`. Keep `make build` and `make stream` working as before.

## Checks (hidden)

1. The concentration mart: top-10 share for five fixed (state, county, month) keys; distinct-recipient
   counts; month-over-month change for one county across all twelve months (the first month has no
   previous month, so the change is empty, not zero).
2. The UEI fallback count matches the key.
3. Every base check still passes (no regression).
4. Dashboard smoke test with Streamlit's `AppTest`, run in a sandbox: a fresh temporary directory that
   holds only a copy of `out/marts/` and the app's own source (the Streamlit entry point and the
   repository modules it imports). The lake, the raw data, the dbt project and its target, and
   `out/warehouse.duckdb` are not there. Both pages must render, and each filter must change the shown
   rows. An app that reads anything outside `out/marts/` fails here, because the file does not exist.
   This works for files opened in native code (DuckDB, pyarrow), which a Python audit hook on `open`
   does not see.
5. Edit radius: the diff of the follow-up against the frozen base, split into new files and changed
   existing files.

## Traps

| Id | Trap | Shallow behavior | Detected by |
|---|---|---|---|
| X1 | The top-10 share needs net obligations per recipient first, then the ranking | Ranks transactions, not recipients | Check 1 |
| X2 | The first month has no previous month | Shows 0, or the full amount, as the change | Check 1 |
| X3 | Recipients without a UEI | Drops them, or groups all of them as one recipient | Checks 1, 2 |
| X4 | The dashboard reads internal tables because they are easier to query | Couples the UI to the warehouse layout | Check 4 |
| X5 | A base mart is changed to make the new mart easier | Base checks regress | Check 3 |
