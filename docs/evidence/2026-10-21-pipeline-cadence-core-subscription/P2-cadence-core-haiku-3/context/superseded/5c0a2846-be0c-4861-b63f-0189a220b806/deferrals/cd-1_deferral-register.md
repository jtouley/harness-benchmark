RUN_BY_COMMAND: plan-create
Ticket: cd-1
Pipeline-Run: a4a4146f-ee60-4507-90b6-b015e00c812a

# Deferral register: cd-1 (gh-1 pipeline)

## Approved deferrals

No approved deferrals.

## Assumptions

| Gap | Assumption | Settled by |
|---|---|---|
| G-1 | "Where the money went" uses place of performance; foreign places go to FOREIGN, US rows without county FIPS go to UNKNOWN in their state. Every row lands in one bucket. | Phase 2 (bucketing), Phase 3 (check 4 reconciliation test) |
| G-2 | "Month" is the calendar month of action_date (YYYY-MM); FY2024 is action_date_fiscal_year = 2024, and the engine fails on dates outside 2023-10-01 to 2024-09-30. | Phase 2 (filter and check), Phase 3 (monthly mart grain) |
| G-3 | An award is generated_unique_award_id; check 3 counts awards with negative summed FY2024 obligations. | Phase 3 (dim_award), Phase 4 (check 3 view) |
| G-4 | Per person is obligations divided by POPESTIMATE2024 of the county; population is not summed across agency rows; state population is the sum of its counties. | Phase 3 (mart and uniqueness test), Phase 4 (check 2) |
| G-5 | Money is DECIMAL(18,2); per-person is DECIMAL(18,2) rounded half away from zero; no float sums. | Phase 2 (decimal parse), Phase 3 (dbt contract) |
| G-6 | edit and new are edits; log and categorize stay in the fact but are not edits; lateness applies to all events; null length is a 0 byte delta. Late is computed at ingest: the running maximum event time starts from the footer of the last committed batch and advances on every first arrival in arrival order, including late ones and events earlier in the same micro-batch; late is max > window_end + 10 min (plan update MF-1). | Phase 5 (classification, including the same-batch max case), Phase 6 (fact and window filters) |
| G-7 | The dedupe key is meta.id; the position (last SSE id) and max event time are in the micro-batch file footer, committed by one rename. The footer stores the running maximum after the batch; a restart reads the highest committed batch id, ignoring _tmp/ (plan update MF-1). | Phase 5 (sink and commit, restart), Phase 5 crash tests |
| G-8 | Idempotence is checked by sorted row content; the lake and marts hold no load timestamp, only _source_sha256 and _source_file. | Phase 2 (deterministic writes), Phase 7 (double-build check) |
| G-9 | make build runs dbt build --exclude tag:stream; make stream DURATION=<s> runs the engine, then dbt build --select tag:stream; an early replay end exits 0. | Phase 6 (Makefile), Phase 7 (end-to-end run) |

## Deferrals rejected

None.
