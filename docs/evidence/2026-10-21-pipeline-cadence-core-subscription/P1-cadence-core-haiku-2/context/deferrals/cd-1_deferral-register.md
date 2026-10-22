RUN_BY_COMMAND: plan-create
Ticket: cd-1
Pipeline-Run: 1a240cbc-2484-4175-b2ce-b76ba5272a21

# Deferral register: cd-1

## Approved deferrals

No approved deferrals.

## Assumptions

| Gap | Assumption | Settled by |
|---|---|---|
| G-1 | Checks 1 to 7 are the plan's rules in Phase 8, because the issue gh-1 body is not on disk. The P3 review replaces them with the issue text if they differ. | Phase 8 `tests/test_checks.py`; P3 review |
| G-2 | Money is `federal_action_obligation`. Sign is kept as recorded (no abs). Scale is 2 decimals; a value must match `-?[0-9]+(\.[0-9]{1,2})?` or it fails ingest. | Phase 2 tests (`test_amount_pattern`); decision cd-1-money-decimal |
| G-3 | Geography is place of performance (state FIPS and county FIPS columns, all eight zips). Blank county or a county not in the 2024 county rows goes to `<state_fips>-UNKNOWN-COUNTY`: in state totals, not in county totals. Territory rows go to `OUTSIDE-50-STATES-DC`; blank state to `UNKNOWN-STATE`; both in money totals, in no per-person row. CT 2021 county codes go to `09-UNKNOWN-COUNTY`. | Phase 4 dbt singular tests (`transform/tests/geography_buckets.sql`); check 3 |
| G-4 | Per-person for agency and month uses the national population (sum of the 3,144 county rows of the 2024 census file). Numerator and denominator cover the 51 state geographies only. | Phase 4; decision cd-1-population-denominator; check 4 |
| G-5 | Dedupe key is meta.id. Checkpoint is the last committed Last-Event-ID and arrival_seq. Dedupe keeps counts exact for replayed events. Events the endpoint skips during a disconnect are not detected; no gap report is built (MF-8). | Phase 6 fake-server tests; decision cd-1-stream-dedupe-checkpoint; check 5 |
| G-6 | Stream time is the arrival-order watermark. Late means watermark more than 10 minutes past window end at first arrival. Published windows are not restated. | Phase 7 tests; decision cd-1-late-event-watermark; check 7 |
