RUN_BY_COMMAND: plan-review
Pipeline-Run: 81d6f968-0843-449a-b3ac-e0fffa47a255
Task ID: cd-1
Verdict: BLOCKING ITEMS

# Plan review: cd-1 (block P3)

**Plan:** `.context/plans/cd-1.plan.md` sha256 1bcaebe94f36f5e405b92a06f80b91d984452d67c5af014ef32463e827996e1f
**Vibe test:** `.context/vibetest/cd-1_2026-10-21.md` sha256 3febdc71ca850fa5ea5f9ef4992acf32d6013de8d79511c8b28611524f6bac87
**Contract:** `commands/plan-review.md` is not in this repo; the review used the packet and the plan's own gates.

## Verdict

VERDICT: BLOCKING ITEMS (not READY TO EXECUTE)

All five vibe-test blocking gaps (G-1 to G-5) have an assumption and a decision record, and the 11 `cd-1-*` proposals and the deferral register exist with the names the plan cites. The blocking items below are defects in the plan text itself, found by checking the plan against the repo data and the spec.

## Blocking items

B-1. Phase 6 S4 test case uses the wrong window. The plan says "event 12:21, window 12:15 start, prior max 12:31 gives is_late = true". An event at 12:21 falls in the window 12:20 to 12:25, not 12:15. With window start 12:20 the threshold is 12:35, so prior max 12:31 gives is_late = false. The spec rule gives on time here (12:31 is 6 minutes after the window end 12:25). The vibe test S4 has the same error. Fix: use event 12:17 (window 12:15, threshold 12:30) with prior max 12:31, which gives late. Add the 12:21 case as an explicit on-time case. Also correct the S4 wording in the vibe test or note it in DECISIONS.

B-2. Cross-batch prior_max is not defined for incremental rows. Phase 6 says prior_max is "from fct_edit itself for old rows and from ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING over arrival_seq for new rows". A window function over the new batch alone does not see the maximum event time already in fct_edit. The plan must state the formula for new rows: max(event_time) over existing fct_edit rows, combined with the in-batch running max. It must also state that is_late is set once at first landing and is never recomputed by a later incremental merge. Otherwise the Phase 6 check "full rebuild gives the same hash as the incremental path" is not guaranteed. Also say how arrival_seq is numbered inside one flush (receipt order).

B-3. Check 2 ranking has no rule for rows without population. Phase 3 puts unplaced members into dim_place (state 99 / county 99999 "Unplaced", and XX000 "Unknown county"). Those rows have no census population. Phase 4 defines the ties rule (G-14) but not whether these rows are excluded from the "ten counties with highest obligations per person" ranking. The plan must exclude rows with null population from check 2 and record it in DECISIONS (new gap entry). Without this, the top-10 answer is undefined.

B-4. dim_wiki misses the sitematrix specials. `data/raw/sitematrix.json` has 376 top-level keys under `sitematrix`: numbered language entries with a `site` list, plus a `specials` list of 124 sites (for example abstractwiki, advisorswiki, arbcom_cswiki). Phase 2 says "flatten sitematrix entries into one row per site", which reads only the numbered entries. Stream edits from special wikis (for example commonswiki or wikidatawiki) would then have no dim_wiki row. Fix: flatten both `sitematrix.<n>.site` and `sitematrix.specials`, and add a Phase 2 test that the flattened row count equals the sum of both lists.

## Non-blocking corrections

N-1. Phase 2 zip count is wrong. The plan says "for each of the 8 assistance and 8 contracts zips". The repo has 4 assistance and 4 contracts zips (agencies 417, 418, 474, 485). The count of 8 is the total. Correct the text and the test expectation.

N-2. The Phase 1 seed count should be read from the file, not from "50 states, DC and the inhabited territories". The census 2024 file has 51 state rows (COUNTY = 000) out of 3195 rows, which gives 3144 county rows. The plan's exit criterion already reads the count from the file, so only the description needs fixing.

N-3. Phase 3 join key `state_fips || county_fips` must be zero-padded to 2 and 3 digits (LPAD) before it becomes the 5-digit key. Say so in the staging description.

N-4. The spec says "each mart has a dbt model contract". The plan enforces contracts only on mart_obligations_monthly and mart_edit_windows_5min. State contracts for dim_agency, dim_place, dim_date, fct_award_transaction, mart_award_net_fy2024, fct_edit, late_events, dim_wiki, or say which marts are exempt and why.

N-5. Phase 7 check 5 uses "all consumed events" as the replayed hour (G-11). This is acceptable only if the stream run for the check is the one-hour replay with no extra events. State the first and last event time check that the plan already asks for, and note the DURATION used.

N-6. Phase 5 and Phase 6 `make stream` runs `dbt build --select tag:stream` before any stream model exists in Phase 5. Confirm that dbt exits 0 when a selector matches no nodes. If it does not, Phase 5 exit fails for a reason unrelated to the consumer.

## What holds

- The late rule, watermark persistence, and the claim that a late event never raises prior_max are correct. A late event's time is at most its window end, and it is late only when prior_max is greater than window start + 15, so it cannot raise the maximum.
- The window boundary cases (12:04:59 and 12:05:00) and the S5 and boundary cases are correct.
- Each blocking gap G-1 to G-5 maps to a named phase and a proposal file that exists.
- The pinned dependencies are not changed, and the version pins in pyproject.toml are untouched.

## Next step

Apply B-1 to B-4 and N-1 to N-4 with `/plan-update` against this review, then run P3 again.
