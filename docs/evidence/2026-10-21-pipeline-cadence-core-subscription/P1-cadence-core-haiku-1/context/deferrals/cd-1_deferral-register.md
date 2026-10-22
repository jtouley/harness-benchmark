RUN_BY_COMMAND: plan-create

# Deferral register: cd-1

Ticket: cd-1
Pipeline-Run: 81d6f968-0843-449a-b3ac-e0fffa47a255

The register logs what the run assumes and what it defers. Each assumption is built by the phase named in
"Settled by". The vibe-test verdict is NOT READY FOR PLANNING; these assumptions stand in for the answers the
request does not give. The owner can overturn one; the cost is the named phase.

## Approved deferrals

No approved deferrals.

## Assumptions

| Gap | Assumption | Settled by |
|---|---|---|
| G-1 | Dedupe key is meta.id checked against the landed lake; the lake is the state; Last-Event-ID is a hint; a replay that restarts from the top is deduped. The live URL is not tested. | Phase 5 (cd-1-stream-dedupe-resume; tests a to d) |
| G-2 | The watermark is the running max of event time over all first arrivals, kept in fct_edit, so it persists across runs and reconnects; late events are included in the max but cannot raise it. | Phase 6 (unit tests S4, S5, boundary) |
| G-3 | Award key is generated_unique_award_id; net obligation is summed per award over FY2024, then the sign test is applied. | Phase 3 and Phase 4 (check 3 test) |
| G-4 | Place means place of performance; no valid state goes to Unplaced (99, 99999); a state without a county goes to Unknown county (state FIPS plus 000); no row is dropped. | Phase 3 (no-loss and key singular tests); Phase 4 (check 4) |
| G-5 | Every table analysts query is published under out/marts/ (star, award net mart, fct_edit, late_events, window mart, dim_wiki); oracle_map.yml names only those objects. | Phase 4 and Phase 6 (publish tests) |
| G-6 | Mart column names and types are set by this plan (Phase 4 and Phase 6 column lists) and enforced by dbt contracts. | Phase 4 and Phase 6 (dbt contract tests) |
| G-7 | Source amounts are cast to DECIMAL(18,2) in staging; the per-person ratio is DECIMAL(18,4); no DOUBLE or FLOAT. | Phase 3 (type contract) |
| G-8 | A missing length gives bytes_delta 0 and has_length false; the event still counts as an edit. | Phase 6 (unit test) |
| G-9 | A missing bot flag gives actor_type human; the count of such events goes to DECISIONS.md. | Phase 6 (unit test) |
| G-10 | The wiki key is the sitematrix dbname (enwiki); check 6 filters server_name en.wikipedia.org through dim_wiki. | Phase 6 (dim_wiki join test) and Phase 7 (check 6) |
| G-11 | The replayed hour is every landed event; its first and last event time are written to DECISIONS.md from the data. | Phase 7 (check 5 oracle) |
| G-12 | The join key is the 5-digit state plus county FIPS; the 2024 estimate (July 1 2024) is used; an absent key uses the 2021 vintage estimate with population_year and population_source recorded; the 2020 base is never read. | Phase 3 (population fallback tests) |
| G-13 | Batch raw sources use replace; the stream uses append with the meta.id dedupe; marts are overwritten. | Phase 2 (idempotence hash test) and Phase 4 (repeat-run hash) |
| G-14 | Check 2 ties are broken by county FIPS ascending; no population threshold is applied. | Phase 4 (check 2 oracle) |
| G-15 | The stack section is read as the Stack paragraph of the request (Python 3.12, dlt, dbt-duckdb, DuckDB); no separate heading is needed. | Phase 1 (wiring tests, pins unchanged) |
