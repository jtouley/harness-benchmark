RUN_BY_COMMAND: spec-driven
Run: cd-1 (task gh-1), Pipeline-Run: a4a4146f-ee60-4507-90b6-b015e00c812a
Plan: .cursor/plans/gh-1-pipeline_cd-1.plan.md (sha256 3089051dfaf05d9081d5358df02335406245e4c5bb1160e15129d0252c132786)
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)

Status: STOPPED at Phase 2 (plan section 8 stop rule). Phase 1 is done and committed.

## Step 0

- Problem: Phase 2 starts by checking the USAspending and census column names against the CSV headers. Section 8 of the plan says "a mismatch stops Phase 2". The check found two names the plan relies on that the files do not have.
- Done means: each phase exit criterion holds and each phase is committed as `phase N`. This run covers Phase 1 only.
- Design decisions: none taken in Phase 2. The award key (G-3) and the state column (G-1) are plan decisions, so they go back to a plan update (P4), not to E1.
- Blast radius: Phases 2 to 7, DECISIONS.md, oracle checks 1 and 3, dim_award and the award fact. Phase 1 has no dependency on either name.
- Is the plan wrong: yes, in two column names. The plan cites `generated_unique_award_id` (G-3) and `primary_place_of_performance_state_code` (G-1). Neither appears in the headers.

## Implementation summary

### Phase 1: Engine skeleton, YAML schema and validation (done)

- Commit `3007ac4` (`feat(engine): phase 1 skeleton, schema and validation`).
- Files: `engine/__init__.py`, `engine/__main__.py`, `engine/config.py`, `engine/schema/pipeline.schema.json`, `engine/tests/test_validate.py`, `engine/tests/__init__.py`, `pyproject.toml` (pytest config and `integration` marker), `uv.lock`.
- Dependencies: `jsonschema` (direct), `pytest` (dev group), via `uv add`.
- Schema: draft 2020-12. Sources `file` (format csv, zip_csv, json; path) and `sse` (url). Transforms `polars` (steps) and `datafusion` (sql). Sinks `parquet_lake` and `parquet_stream` (input, path, key). Conditional fields use `if`/`then` with `unevaluatedProperties: false`.
- Errors: `file:line: problem`. The line comes from the PyYAML node tree. A YAML syntax error uses PyYAML's problem mark.
- Tests written first (red: import error on `engine.config`), then green.
- Deviation: the `run` subcommand is not in Phase 1. Phase 1's exit criterion needs only `validate`. `run` is added with the runner in Phase 2.
- Options tried: one option (the schema plus validator). No other options were needed.

### Phase 2: Batch sources to the lake (stopped, not started in code)

Header check run before any mapping, as section 8 requires:

| Name in plan | Where the plan uses it | Result in the CSV headers |
|---|---|---|
| `generated_unique_award_id` | G-3 award key, Phase 3 `dim_award`, Phase 4 check 3 | Absent from all 16 USAspending files (8 Contracts, 8 Assistance). |
| `primary_place_of_performance_state_code` | G-1 state of place | Absent from the 8 Assistance files. Present in the Contracts files. |

Names that match:

- USAspending, both file types: `action_date`, `action_date_fiscal_year`, `federal_action_obligation`, `awarding_agency_code`, `awarding_agency_name`, `prime_award_transaction_place_of_performance_state_fips_code`, `prime_award_transaction_place_of_performance_county_fips_code`, `primary_place_of_performance_country_code`, `primary_place_of_performance_county_name`.
- Transaction keys (N-6): `contract_transaction_unique_key`, `assistance_transaction_unique_key`.
- Award keys present per type: `contract_award_unique_key` (Contracts), `assistance_award_unique_key` (Assistance).
- Census 2024 file (`co-est2024-alldata.csv`): `SUMLEV`, `STATE`, `COUNTY`, `POPESTIMATE2024`, `POPESTIMATE2021`.
- Census 2021 file (`co-est2021-alldata.csv`): `SUMLEV`, `STATE`, `COUNTY`, `POPESTIMATE2021`. No `POPESTIMATE2024`, so the 2021 fallback (N-1) uses it.

Other facts from the check:

- The Census 2024 file does not decode as UTF-8 (fails at byte 6703, 0xF1). It reads as latin-1. The engine needs an explicit encoding for it.
- Connecticut in the 2024 file has planning-region rows under SUMLEV 050 (codes 110 to 190, not county codes). The 2021 file has county rows 001 to 015. This matches plan note N-1.

Why Phase 2 stopped:

- The plan says a mismatch stops Phase 2. Replacing the award key silently would change G-3 (one award across both files). Using `contract_award_unique_key` and `assistance_award_unique_key` would give two keys that do not join. Changing G-1 to a different state column would change the place rule. Each is a plan decision.
- No Phase 2 code or tests were written. The working tree has no Phase 2 change.

Options for the plan update (P4), not chosen here:

1. Build the award key from the USAspending data dictionary, if the archive has the field under another name. The plan must then name the construction.
2. Define the award key per file type and join the two files on a derived key. The plan must then state how an award that appears in both files is counted (G-3).
3. For G-1, use `prime_award_transaction_place_of_performance_state_fips_code` (present in both file types) and change the G-1 text from state code to state FIPS.

## Verification

- `uv run pytest engine/tests -q`: 8 passed (Phase 1 tests).
- `uv run python -m engine validate <bad file>`: prints `file:line: problem` on stderr and exits 1.
- `python3 .../scripts/cognitive_complexity_gate.py --check`: OK (ruff and mypy were not in the uv cache; the gate still passed).
- `scripts/entry_invariant.py --phase execution`: OK before the first gated edit.
- `scripts/phase_ledger.py --json`: phase 1 is the only commit that names a phase.

## Next

Run `/plan-update` on the plan for the two names above. Then `/spec-driven` resumes at Phase 2. The Phase 1 commit stays as it is.
