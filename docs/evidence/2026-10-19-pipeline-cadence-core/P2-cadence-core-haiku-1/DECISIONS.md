# Decisions

Each entry names a choice that the spec left open, what was chosen, and why.

## Profiling results (Phase 3)

- **Q-a, natural key.** One USAspending row is one prime award transaction. The key is
  `transaction_key`, which is `assistance_transaction_unique_key` for assistance files and
  `contract_transaction_unique_key` for contract files. Profiling found 9,820 rows and 0 duplicate keys.
- **Q-b, column shapes.** Assistance files have 116 columns and contract files have 297. The columns the
  pipeline needs are present in both shapes, except the award and transaction key columns. The engine maps
  by name, and a column missing from one shape becomes null when the files are concatenated.
- **Award key.** `award_id` is `award_id_fain` for assistance and `award_id_piid` for contracts (D4).
- **Census encoding.** Both census files are Windows-1252 (cp1252), not UTF-8. The census source sets
  `encoding: cp1252`.
- **Raw totals.** The lake total of `federal_action_obligation` matches a separate exact decimal sum of
  the raw CSVs for each of the 8 zip files. The grand total is 1,442,017,216.67 over 9,820 rows.

## Choices

- **D1. Place of performance.** State and county come from the place-of-performance FIPS fields, not the
  recipient fields. The question asks where money went. A row with a known state and a blank county keeps
  its state and uses county `000` (an unknown county in that state). A row with a blank state uses state
  `00`. No row is dropped, and each state sum still equals the sum of its counties. (Update 5 of the plan
  left this open. This entry closes it.)
- **D2. Population.** Use `POPESTIMATE2024` (July 1, 2024), per Amendment A. A county with a blank 2024
  value uses its latest earlier non-blank `POPESTIMATE` value from the same row. A county with no 2024 row
  uses its 2021 file value. The 2024 file has a value for all 3,144 counties, so the first rule never fires
  on this data. Eight Connecticut counties exist only in the 2021 file (the state moved to planning regions
  in 2022). Their population comes from the 2021 file: 09001, 09003, 09005, 09007, 09009, 09011, 09013 and
  09015. Their `population_year` is 2021. Places in no census file (56 unknown-county places and 7 others)
  have no population, and their per-person value is null.
- **D3. Money.** Money stays `decimal(18,2)` from the lake to the marts. Sums are exact. DuckDB divides
  decimals in double precision, so `obligations_per_person` is a double ratio rounded to cents. Only that
  column rounds. Every money sum stays exact.
- **D4. Award.** An award is one `award_id` within FY2024. Its net obligation is the sum of
  `federal_action_obligation` over its transactions. 68 rows have no award id. Each of them counts as its
  own award, keyed by its transaction key.
- **D5. Casts.** The lake keeps source text. The one cast is `federal_action_obligation` to
  `decimal(18,2)`. A value with more than two decimal places, a blank value, or a value that cannot cast
  fails the run. The `reject_sql` query in `pipelines/batch.yml` makes the first two cases fail. A value
  that cannot cast fails through DataFusion.
- **Lake metadata.** Each file source adds `_source_file` (the repo-relative path) and `_loaded_at` (the
  file modification time in UTC). Neither value depends on the wall clock, so a rebuild writes the same
  values.
- **Lake layout.** The USAspending lake folder is partitioned by `awarding_agency_code`. The sink sorts
  rows by every column before it writes, so a rebuild gives the same row order.

- Replay start probe for run 20260101T000000Z: first ids [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}] and [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}]. Result: BLOCKED. The server restarts each connect. Two runs overlap by design (see the overlap warning).

- Replay start probe for run 20261019T060000Z: first ids [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}] and [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}]. Result: BLOCKED. The server restarts each connect. Two runs overlap by design (see the overlap warning).

- Overlap warning: run 20261019T060000Z and run 20260101T000000Z share 343 meta.id values. Each meta.id appears once in the lake.

- Replay start probe for run 20261019T061000Z: first ids [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}] and [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}]. Result: BLOCKED. The server restarts each connect. Two runs overlap by design (see the overlap warning).

- Run 20261019T061000Z reconnected 45 times. Malformed frames and drops both reconnect.

- Replay start probe for run 20261019T062000Z: first ids [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}] and [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}]. Result: BLOCKED. The server restarts each connect. Two runs overlap by design (see the overlap warning).

- Run 20261019T062000Z reconnected 976 times. Malformed frames and drops both reconnect.

- Replay start probe for run 20261019T070000Z: first ids [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}] and [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}]. Result: BLOCKED. The server restarts each connect. Two runs overlap by design (see the overlap warning).

- Run 20261019T070000Z reconnected 960 times. Malformed frames and drops both reconnect.

- Replay start probe for run 20261019T073000Z: first ids [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}] and [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}]. Result: BLOCKED. The server restarts each connect. Two runs overlap by design (see the overlap warning).

- Replay start probe for run 20261019T080000Z: first ids [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}] and [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}]. Result: BLOCKED. The server restarts each connect. Two runs overlap by design (see the overlap warning).

- Run 20261019T080000Z skipped 1 frames whose JSON was cut off. SSE ids: [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792024186253},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}]. These events are not in the lake.

- Replay start probe for run 20261019T060000Z: first ids [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}] and [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}]. Result: BLOCKED. The server restarts each connect. Two runs overlap by design (see the overlap warning).

- Replay start probe for run 20261019T060000Z: first ids [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}] and [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021612166},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}]. Result: BLOCKED. The server restarts each connect. Two runs overlap by design (see the overlap warning).

- Replay start probe for run 20261019T064653Z: first ids [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021613419},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}] and [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021613419},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}]. Result: BLOCKED. The server restarts each connect. Two runs overlap by design (see the overlap warning).

- Run 20261019T064653Z skipped 1 frames whose JSON was cut off. SSE ids: [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792022530321},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}]. These events are not in the lake.

- Replay start probe for run 20261019T064729Z: first ids [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021613419},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}] and [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792021613419},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}]. Result: BLOCKED. The server restarts each connect. Two runs overlap by design (see the overlap warning).

- Overlap warning: run 20261019T064729Z and run 20261019T064653Z share 10719 meta.id values. Each meta.id appears once in the lake.

- Run 20261019T064729Z skipped 1 frames whose JSON was cut off. SSE ids: [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1792022530321},{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1}]. These events are not in the lake.
