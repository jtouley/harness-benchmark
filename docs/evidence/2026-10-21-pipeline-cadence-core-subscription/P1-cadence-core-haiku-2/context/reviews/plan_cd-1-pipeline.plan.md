RUN_BY_COMMAND: plan-review
Verdict: READY WITH CHANGES
Last reviewed plan sha256: f0b82aee4827a725fd986cc9a853d9fea5b154b8ba95e334dfbd769290d6bc9a
Pipeline-Run: 1a240cbc-2484-4175-b2ce-b76ba5272a21

**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Ticket token: cd-1

# Plan review: cd-1-pipeline.plan.md (cycle 2)

Inputs: `.context/plans/cd-1-pipeline.plan.md` (sha256 f0b82aee...), `.context/reviews/plan_cd-1-pipeline.plan.md` (cycle 1, sha256 5e67b861..., MF-1 to MF-6, verdict READY WITH CHANGES), `.context/vibetest/cd-1_2026-10-21.md` (sha256 87234335..., NOT READY FOR PLANNING, G-1 to G-6). Also read: the six `.context/proposals/cd-1-*.md` records, `.context/deferrals/cd-1_deferral-register.md`, `.context/proposals/cd-1.md`, `.context/issues/cd-1.md`.

The cycle-1 review file is overwritten by this run at the same path. Its content is in the cycle-1 section of the orchestrator packet.

## Summary

The MF-1 to MF-6 edits are applied in the phase text. All six are closed. The new text adds five open must-fix items (MF-7 to MF-11). Four are spec gaps or wrong order. One is a header test that would fail on every real zip. The data facts the plan states were checked against the files in `data/raw/`: column names, amount format, FY2024 dates, FIPS buckets, and the census counts. All of them hold.

## Status of earlier items

| Id | Status | Evidence |
|---|---|---|
| MF-1 | closed | Phase 4 scope adds `dim_wiki` (`wiki_key`, `url`, `code`, `sitename`, `closed`, plus an `unknown` row) with `unique` and `not_null` on `wiki_key`. Phase 7 adds the `relationships` test from `fct_edit.wiki_key` to `dim_wiki.wiki_key`. |
| MF-2 | closed | Phase 2 names one state FIPS column for both award types and drops the 2-letter state code. Each type gets a header test. Checked: all eight zips carry the named columns for their type. `source_file` is the exception, see MF-7. |
| MF-3 | closed | Phase 4 geography rules 1 to 5 answer (a) territory rows to `OUTSIDE-50-STATES-DC`, (b) bucket money stays out of the per-person denominator (Phase 4 per-person text and the national denominator = 3,144 county rows), (c) the 16 CT 2021 rows to `09-UNKNOWN-COUNTY`. `transform/tests/geography_buckets.sql` tests CT 09001 and state 72. |
| MF-4 | closed | Phase 2 pins `-?\d+(\.\d{1,2})?`. `test_amount_pattern` rejects `1e3`, `1.005`, `+1`, `1,000` and empty. Checked: all 9,820 amounts in the eight zips match. |
| MF-5 | closed | Phase 6 batch size is a parameter (test value 5). The test kills after the first batch commit, asserts `Last-Event-ID: 5` on the second run, and expects 10 rows with no duplicate `meta.id`. |
| MF-6 | closed | Phase 5 no longer writes `oracle_map.yml` or `stream_available`. Phase 7 adds `stream_available`. Phase 8 writes `oracle_map.yml` as the last build step. Phase 1 is the only phase that creates `DECISIONS.md`. |

## Must-fix items

- MF-7 (Phase 2, header test defines a column that no zip has): Phase 2 says to keep `source_file` and `award_type`, and the header test "asserts the columns above". `source_file` is not a header in any of the eight zips (checked: absent in all eight). The test would fail on every real zip before any row is read. State that `source_file` (zip member name) and `award_type` (from the zip file name) are derived fields, not header columns. The header test asserts only the header names.
- MF-8 (Phase 6, gap reporting is promised but not built or tested): The G-5 assumption and the register row say a gap during a disconnect is "logged as `gap` in the stream report" and "reported, not hidden". The R-2 probe text says the endpoint behaviour "affects only gap reporting". No phase names a stream report, a file or field for the gap, or a test that produces one. Name the file and field in Phase 6 scope. Add a fake-server case where the server skips events on reconnect and assert that the gap row exists. Or remove the claim from G-5 and from the register row. Until then "Settled by Phase 6" does not hold.
- MF-9 (Phase 6 and Phase 7, `arrival_seq` has no assignment rule): Phase 6 checkpoints "the last committed `arrival_seq`". Phase 7 defines lateness by `arrival_seq` ("the position of first arrival in the lake"). No phase says what writes `arrival_seq`, when, or how a replay keeps it. The late set cannot be reproduced without that rule. Name the rule (for example: on first insert of a `meta.id`, `arrival_seq` = max stored + 1 in batch order, written in the same commit as the merge). Add a Phase 6 or Phase 7 test that a replayed event keeps its first `arrival_seq`. The Phase 7 duplicate-`meta.id` test depends on it.
- MF-10 (Phase 9, steps 2 and 4 cannot both pass): Step 3 (`make stream DURATION=60`) writes `lake/stream`. Phase 7 marts (`fct_edit`, `mart_edit_window_5min`) read it. Step 4 requires the `sha256sum out/marts/*` after the stream run to equal the hash from step 2, which was taken before the stream run. Those hashes differ unless the stream marts are empty. Also state which marts are published when `stream_available = false`. Fix the gate: compare two builds that both run after step 3, and make the step-2 hash cover the batch-only build.
- MF-11 (`make stream` when the endpoint is down): Success signals and Phase 9 step 3 require `make stream DURATION=60` to exit 0 on a clean checkout. The endpoint is `http://localhost:8099/...`, and no phase says what the stream client does when the connection is refused or returns a non-200 status. Name the exit code and the record written in each case (for example: exit 0 with zero events and a `stream_available`-style record, or exit non-zero with a usage line). Phase 9 step 3 and the success signal must match that rule. Add a test for it.

## Notes (not blocking)

- Revision ledger: the plan's `## Revision ledger` says "None." No `## Revision ledger (review <sha>)` table answers MF-1 to MF-6. The closure evidence above therefore cites the plan text. The next `/plan-update` should write a ledger keyed to the sha256 of this review file, with one row for each of MF-7 to MF-11.
- No commit checkpoint per phase (unchanged from cycle 1). The contract's review list names commit checkpoints. Add one line per phase, or state that the phases are one commit.
- Blast radius: Phase 4 writes `transform/tests/geography_buckets.sql`, which is not in the blast radius list. The list names `transform/models/` only. Add `transform/tests/` and `transform/models/schema.yml`.
- Merge mechanism: the plan says "merged on `meta.id`" and "a commit merges the batch into the lake" but does not name the dlt write disposition or the destination that performs the merge into Parquet under `lake/`. Name it, and confirm it is supported at the pinned dlt 1.31.0. This review did not run dlt.
- `population_source` for fallback rows has no named values. Phase 4 says "the fallback vintage", and Phase 8 check 4 matches on it. Name the values (for example `co-est2024`, `co-est2021`, and the fallback year), so the check and the build report agree.
- Phase 2 regex: `\d` in Python `re` matches non-ASCII digits. Write `[0-9]` or compile with `re.ASCII` so the rule matches its stated pattern.
- Phase 8 `test_checks.py` reads `out/marts`. The Phase 8 exit criterion runs `unittest discover` without saying that `make build` runs first. Phase 9 step 6 does run it after step 2. Add the ordering to the Phase 8 exit criterion.
- Check 5 (stream resume) runs its own fake server, while checks 1 to 4 and 6 to 7 read built output. Phase 8 does not say which checks need a built `out/`. State it per check.
- G-1 (checks 1 to 7): the issue gh-1 body is not on disk and not in the packet. The comparison with the issue text cannot be made here, and the assumption stands. The orchestrator should supply the issue body if one exists.
- Reuse section: placing shared test helpers in `tests/support.py` rather than `tests/conftest.py` is correct for `unittest discover`, which does not load `conftest.py`. No change needed.

## Checks run

- Hashes: the plan (f0b82aee...), the cycle-1 review (5e67b861...) and the vibe-test (87234335...) match the packet.
- Headers of all eight USAspending zips read with `python3 -I` from outside the repo. Columns checked: the Phase 2 list. Present in every zip for its type, except `source_file`, which is absent from all eight.
- All 9,820 `federal_action_obligation` values match `-?\d+(\.\d{1,2})?`. `action_date` runs from 2023-10-01 to 2024-09-30.
- State FIPS: 57 blank rows. Territory rows (60, 66, 69, 72, 78): 138. No state FIPS outside the 51 census state rows. In-state rows with a county FIPS outside the 2024 county rows: 16 (CT, the 2021 codes 09001 to 09015). All other in-state county rows are in the 2024 county list.
- Census: `co-est2024-alldata.csv` has 51 SUMLEV 040 rows and 3,144 SUMLEV 050 rows. `co-est2021-alldata.csv` has the CT county codes 09001 to 09015.
- Not run: `make build`, `make stream`, `dbt`, `uv`. The plan's commands were not executed.

## Verdict

READY WITH CHANGES. MF-7 to MF-11 block E1. Run `/plan-update` on this plan, answer each id in its revision ledger, then run `/plan-review` again.
