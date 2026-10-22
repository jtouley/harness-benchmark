RUN_BY_COMMAND: plan-create
Ticket: cd-1 (task gh-1)
Pipeline-Run: 5c0a2846-be0c-4861-b63f-0189a220b806

# Deferral register: cd-1

Plan: `.cursor/plans/gh-1-pipeline_cd-1.plan.md`. Vibe test: `.context/vibetest/cd-1_2026-10-22-rev2.md`.

## Assumptions

| Gap | Assumption | Settled by |
|---|---|---|
| G-1 | "Where the money went" is the place of performance, mapped per file type from `primary_place_of_performance_country_code`, `prime_award_transaction_place_of_performance_state_fips_code` and `prime_award_transaction_place_of_performance_county_fips_code`. Foreign places go to `FOREIGN`. A blank country goes to `UNKNOWN`, not `FOREIGN`. A US row with no state FIPS goes to `UNKNOWN`. A US row with no county FIPS goes to county `UNKNOWN` in its state. The county FIPS is the file's 5-digit key, not a concatenation. Every row is in exactly one bucket, so the reconciliation is exact. (Plan update 2026-10-22, MF-2 and the second update, MF-2.) | Phase 2 (column names per file type), Phase 3 (`stg_usaspending__transactions`, `dim_place`), Phase 4 (reconciliation test) |
| G-2 | "Month" is the calendar month of `action_date`. FY2024 is `action_date_fiscal_year = 2024`. The engine fails if an FY2024 row is outside 2023-10-01 to 2024-09-30. | Phase 2 (engine assertion), Phase 3 (filter, `dim_date`) |
| G-3 | An award is one value of `award_key`, the award-level key of each file (`contract_award_unique_key` for Contracts, `assistance_award_unique_key` for Assistance), kept with its prefix as the file holds it (`CONT_AWD_`, `CONT_IDV_`, `ASST_NON_`, `ASST_AGG_`). `generated_unique_award_id` is not in the files. Check 3 counts awards whose summed FY2024 obligation is below zero, all four prefixes, with a count per prefix. (Plan update 2026-10-22, MF-1; second update, MF-9.) | Phase 3 (`dim_award`), Phase 4 (check 3 view) |
| G-4 | Per-person is obligations divided by the July 1, 2024 county population (`POPESTIMATE2024`), NULL where N-1 leaves no population. Population is never summed across agency rows. State population is the SUMLEV 040 row of the 2024 file, which the Phase 3 test ties to the sum of its county rows. Connecticut uses the 2024 planning regions (second update, MF-10). | Phase 3 (mart columns, uniqueness test, state sum test), Phase 4 (check 2) |
| G-5 | Money is `DECIMAL(18,2)`. Per-person is `DECIMAL(18,2)`, rounded half away from zero. No float cast anywhere. | Phase 2 (decimal parse and test), Phase 3 (contract types) |
| G-6 | `edit` and `new` are edits. `log` and `categorize` stay in `fct_edit` and are not edits. Null length gives a 0 byte delta and `has_length = false`. Lateness is computed in the engine at ingest and the edit fact keeps late events. | Phase 5 (classification), Phase 6 (`fct_edit`, `late_events`, window filters) |
| G-7 | The dedupe key is `meta.id`. The position (last SSE id) and the running maximum event time are in the footer of the micro-batch file, which appears by one `os.replace`. | Phase 5 (sink and commit), Phase 5 crash tests |
| G-8 | Idempotence is checked by sorted row content with all columns. No load timestamp or run id is stored. Byte equality is reported, not required. | Phase 2 (deterministic writes), Phase 7 (double-build integration test) |
| G-9 | `make build` runs `dbt build --exclude tag:stream`. `make stream DURATION=<s>` runs the engine then `dbt build --select tag:stream`. A replay that ends early still runs the dbt step. | Phase 6 (stream models), Phase 7 (Makefile, end-to-end run) |
| G-10 | "The replayed hour" is the first UTC event-time hour in `fct_edit` (from the floor hour of the minimum `timestamp`, end exclusive). Check 5 counts every consumed edit in it, late included. | Phase 6 (check 5 view and test), Phase 7 (value in DECISIONS.md) |
| G-11 | The stack is the pins in `pyproject.toml` plus stdlib `urllib`. Output 3 is `Makefile`, `oracle_map.yml`, `DECISIONS.md`, `pipelines/`, `engine/`, `transform/`, `out/marts/`. | Phase 1 (pins unchanged), Phase 7 (deliverable list) |
| G-12 | A mart is a dbt SQL model with a schema YAML contract and no Python. The engine YAML covers sources, transforms and sinks. Marts publish by folder config in `dbt_project.yml`. | Phase 3 (folder config and exit check) |

## Approved deferrals

No approved deferrals.
