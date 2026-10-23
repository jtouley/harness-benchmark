# Task P4: the library-loans pipeline (the hold-out)

Status: **proposed** (2026-10-23). Part of the [pipeline family](pipeline-family.md), as its hold-out:
the contamination guard of the improvement loop. P1 and P2 are the tasks the loop iterates on, and their
specs are saved golden inputs (`golden/cadence/`). P4 is not: it runs only when the owner calls for the
final check of a Cadence commit, and the driver refuses it otherwise (`python -m loop.driver --holdout`).
P3 was meant for this, and its Scala image does not build on the loop's host.

P4 is batch only: the same architecture as P1 and P2 (a Parquet lake, models, marts published under
`out/marts/`, `oracle_map.yml`, seven checks, `make build` twice), on a small dataset that a script
generates (`golden/pipeline/P4/snapshot/generate.py`, CC0, no download), with plain SQL on DuckDB. The
stack section is part of the request, since P4 has no sibling stacks.

## The request (the text the arm gets)

> Build a pipeline that answers one question for the library's analysts, from the raw exports to
> columnar tables a BI tool can query directly.
>
> **Question: how were the branches used in 2025?** Checkouts, late returns, fines and what is still
> out, by branch, item, patron and month.
>
> ### Inputs
>
> - `data/raw/branches.csv`: the twelve branches (code, name, region).
> - `data/raw/items.csv`: the catalog (item id, title, category, home branch, replacement cost).
> - `data/raw/patrons.csv`: the patrons (patron id, home branch, year joined).
> - `data/raw/loans_2025_h1.csv` and `data/raw/loans_2025_h2.csv`: the loan events of 2025 exported in
>   two halves, one row per event (`checkout`, `renew` or `return`), with the event time in UTC.
> - `data/raw/fines.csv`: the fines, one row per fine assessed or waived, with the amount in dollars.
>
> ### Architecture
>
> - **Lake.** Ingestion writes every source to a Parquet lake under `lake/` (one folder per source
>   table). The lake keeps the source's data and adds only load metadata.
> - **Models.** Everything after the lake is built in DuckDB: staging models, a fact table of loans
>   and the marts. Document the grain of each model.
> - **Publish.** The marts are written as Parquet under `out/marts/` (one folder per mart). Anything
>   downstream reads only `out/marts/`.
>
> ### Outputs
>
> 1. A fact table at the grain of one loan (one checkout), with its branch, item, patron, checkout
>    time, return time, number of renewals and due time.
> 2. Marts that answer the checks below: checkouts per branch, checkouts per item, late returns,
>    fines per month and branch, active patrons per home branch, and the items on loan at the end
>    of the year with their replacement cost.
> 3. The lake under `lake/`, the model code, and the published marts under `out/marts/`.
> 4. `oracle_map.yml`: for each question in the "Checks" list below, the table and column (or SQL
>    view) that answers it.
> 5. `DECISIONS.md`: each place where this spec left a choice to you, what you chose and why.
>
> ### Rules
>
> - `make build` runs the whole pipeline from the raw files. Running it twice must not change any
>   output.
> - A loan event is one row of a loans file. An event that appears in both files, with the same loan
>   id, event and time, is one event.
> - A loan of 2025 is a checkout event in the files. A return or a renewal whose checkout is in no
>   file belongs to a loan from the year before.
> - A loan is due 21 days after its checkout, plus 21 days for each renewal before its return. A
>   return after the due time is late.
> - Money is in US dollars, summed exactly (no floating-point sums). A negative fine row is a waiver,
>   and it counts in every sum.
> - Codes are text: a branch code keeps its leading zero.
>
> ### Checks the analysts will run
>
> 1. Checkouts per branch in 2025 (the branch of the checkout event).
> 2. The ten items with the most checkouts in 2025, ties in item id order.
> 3. The number of loans of 2025 returned late.
> 4. For March 2025: net fines per branch add up to the system total for the month.
> 5. Net fine income per month, over every fine in the file.
> 6. Active patrons per home branch: patrons with at least one checkout in 2025, counted by the
>    branch they belong to.
> 7. The replacement value of the items on loan at the end of 2025: the items whose last event of
>    the year is a checkout or a renewal.
>
> Use Python 3.12 and DuckDB for every step: land the raw files in the Parquet lake, build the models
> in DuckDB (SQL or the Python API) and write the marts as Parquet. The skeleton pins the versions in
> `pyproject.toml`; do not change them.

## Skeleton

`data/raw/` (the generated files), a `Makefile` with a `build` target that fails, `pyproject.toml` and
`uv.lock` pinning DuckDB, `.python-version` and `.gitignore`.

## Traps (hidden from arms; checked against the generated data when the key is built)

Each trap is a known cause of a wrong answer. The key (`pipetask.p4key`) computes the wrong answer each
single trap produces for D1 to D4 and D6 to D8, and the grader names the trap when a candidate's answer
equals it. D5 has no wrong answer: the grader reads `7` as `07`, so it shows only as a lost join. D9
shows in the idempotence check, not in an answer. A trap the data does not reproduce for a check is
listed in the key as `traps_not_reproduced` and not faked: D7 on check 6, because every patron with a
return or a renewal in 2025 also has a checkout.

| Id | Trap | What a shallow solution does | Detected by | Cause class |
|---|---|---|---|---|
| D1 | The two loans files overlap by one week: the same events are in both | Counts the overlap twice | Checks 1, 2, 3 | data-semantics |
| D2 | A waiver is a negative fine row | Drops negative rows, or takes their absolute value | Checks 4, 5 | spec-reading |
| D3 | A renewal moves the due time by 21 days | Measures lateness from the checkout alone | Check 3 | spec-reading |
| D4 | A loan checked out in the first half of the year can return in the second file | Reads each file on its own and counts the item as still out | Check 7 | data-semantics |
| D5 | Branch codes have leading zeros (`07`) | Reads them as integers; joins to the branch table fail or codes merge | Checks 1, 4, 6 (the grader accepts `7` for `07`, so only a lost join shows) | data-semantics |
| D6 | Replacement costs are money text with a dollar sign and thousands separators (`$1,234.50`) | Casts fail, or the comma truncates the number | Check 7 | data-semantics |
| D7 | Some returns and renewals belong to loans checked out the year before (72 loans) | Takes the loan's first event for its checkout, or counts the patron as active | Check 3 (check 6: not reproduced by the data) | data-semantics |
| D8 | A waiver assessed in January 2026 for a fine of December 2025 | Filters the months to 2025 and loses it | Check 5 | spec-reading |
| D9 | Re-running the build | Appends a second copy, or publishes beside the old files | Idempotence check | idempotence |

## Oracle

The seven checks, read from `out/marts/` through `oracle_map.yml` by `pipetask.p4grade`, with the shared
map reader (`pipetask.oracle`). The trial (`pipetask.p4trial`) resets the repository, builds twice,
digests the marts the checks read (folders and single files alike, issue #49) and grades.

## Proof

`tests/test_pipeline_p4.py`: the data regenerates byte for byte, the key regenerates from the data, the
reference grades 7 of 7 and rebuilds identically, and a variant with one check removed from its map
grades 6 of 7. A variant that reads the two loans files without deduplication fails checks 1 to 3 and
the grader names D1.
