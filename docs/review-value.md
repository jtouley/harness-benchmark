# Review value

The question: do review cycles raise new findings that add value, and how do we count that?
`scripts/review_value.py` (stdlib only) counts it from two inputs:

- a Cadence findings ledger (`findings.jsonl`), per stage (plan-review, adversarial-review,
  test-benchmark-plan, pr-review-local, test-benchmark-pr, architecture-review-*, ...);
- a folder of `/pr-review` reports (`PR_REVIEW_#<n>.md`), per review round. The first
  review is round 0. Each appended `## Update [...]` section is one more round.

```bash
python scripts/review_value.py --findings path/to/findings.jsonl \
    --reviews path/to/reviews/ [--tokens tokens.csv] [--json out.json] [--markdown out.md]
```

The output holds counts, stage names, PR numbers and normalized verdicts only. It never
copies finding text, so the input stays private: the ledger and the review reports live in
`.context/` and are never committed.

## Definitions

| Measure | Ledger (per stage) | Review reports (per round) |
|---|---|---|
| raised | distinct ids filed at that stage (the last row of an id gives its final status) | finding lines in the round: a line with an evidence tag (`[V]`, `[L]`, `[I]`, `[U]`, bare or in backticks) then a severity word |
| blocking | severity `must-fix` | Critical, Required or Must-fix |
| should-fix | severity `should-fix` | Should-fix or Optional |
| confirmed defect | blocking, and the id's final status is `verified` (fixed with a test). `rejected`, `deferred`, `open`, `spec_gap` and `fixed` do not count | blocking, and a later round's "Previous issues" status section marks the item resolved: the first ✅, ⚠️ or ❌ marker in the item is ✅. A ⚠️ (partly) item is not resolved. The credit goes to the round that raised it |
| new vs repeat | repeat id: the id was filed at an earlier stage. Repeat text: the same evidence after task ids (`cd-47`) are removed, so one boilerplate finding filed again per task | repeat: the same normalized title was raised in an earlier round of the same PR. `kind` is `new` (raised a new finding), `confirm-only` (only confirmed earlier fixes) or `empty` |
| fix-induced | evidence or note matches the phrases below | finding text matches the phrases below |
| cost | `--tokens` CSV `stage,round,tokens`: tokens summed per stage, divided by confirmed defects | the same CSV, with stage `PR#<n>` and the round number |

A stage or round with no row in the tokens CSV has unknown cost (`null` in JSON, "unknown" in
Markdown), never zero. A tokens cell that is not a number stops the run with its line number.

Fix-induced phrases (case-insensitive): "the fix", "fix commit", "introduced by", "from my
own earlier recommendation".

## Limits

- Severity is the reviewer's own claim. Nothing here checks that a Required item was a real
  defect. The confirmed-defect count is the check: a blocking finding counts only after a fix
  closes it.
- In the review reports, "confirmed" means a later round wrote ✅ for the item. It does not
  prove a test was added. Items the author fixed after the last round, or fixed without a
  re-review, never count. The last round of each PR can never have confirmed defects.
- Status items are matched to findings by the id at the start of the item's header (`#3`,
  `R1`, `N2`, `A`, `§4.1`, also after "Original"). An id cited later in the header, such as
  "nit (see F1)", is not read. A status item with no leading id is credited to the round
  before it only when its header names a blocking severity. Items written in tables are not
  read.
- A finding restated in two sections of the same round (for example §4 and §7) counts twice.
  The "Specific inline comments", "Dropped findings", "Recommendations", "Verification
  checklist" and "Spec-driven proof" sections are skipped. The report title (the H1) never
  causes a skip.
- Verdicts are read from a `Verdict:` line or a `## Verdict` heading. Older reports have no
  verdict line, so the column is empty for them.
- A report that records its re-reviews without `## Update` sections (#7 does this) counts as
  one round, and its status table is not read. Snapshot copies such as
  `PR_REVIEW_#8.ceb1500.md` are ignored.
- `repeat` matches exact normalized titles only. It is 0 in every current round, so a
  reworded repeat counts as new. `kind` therefore says in practice whether a round raised
  anything.
- The fix-induced phrases are a heuristic. They miss a fix-induced finding that does not use
  them, and "the fix" also matches a finding that only mentions an earlier fix.
- The ledger sample has no `plan-review` or `adversarial-review` rows, so those stages do not
  show yet. No tokens file exists yet, so cost per confirmed defect is not in the first table.

## First results (14 October 2026)

Inputs: the 18 review reports in `.context/prs/reviews/` of this repo (this PR's own review,
#29, has no re-review yet), and the Cadence ledger (`cadence/.context/findings.jsonl`, 30
rows, 29 ids). Both are live files, so a rerun can differ.

### PR review rounds, by round index

| round | rounds | raised | blocking | new | confirmed defects | fix-induced | confirm-only rounds |
|---|---|---|---|---|---|---|---|
| 0 | 18 | 202 | 62 | 202 | 40 | 1 | 0 |
| 1 | 15 | 46 | 6 | 46 | 5 | 1 | 1 |
| 2 | 8 | 18 | 6 | 18 | 6 | 0 | 2 |
| 3+ | 5 | 10 | 0 | 10 | 0 | 0 | 0 |

Reading:

- The first review does most of the work: 40 of the 51 confirmed defects (78%).
- Re-review rounds are not only confirmations. Rounds 1 and 2 raised 12 blocking findings,
  and 11 were confirmed fixed later. That is 22% of all confirmed defects. Only 3 of the 28
  re-review rounds raised nothing.
- Rounds 3 and later raised 10 findings, none blocking. On this sample, a fourth round adds
  nits and should-fixes, not defects.
- Only 2 findings say they come from an earlier fix.

### PR review rounds, per PR

| PR | round | verdict | raised | blocking | should-fix | new | repeat | fix-induced | resolved (confirmed here) | confirmed defects | kind |
|---|---|---|---|---|---|---|---|---|---|---|---|
| #1 | 0 | OTHER | 12 | 3 | 1 | 12 | 0 | 0 | 0 | 2 | new |
| #1 | 1 | - | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | confirm-only |
| #1 | 2 | APPROVE | 1 | 0 | 0 | 1 | 0 | 0 | 2 | 0 | new |
| #2 | 0 | - | 10 | 4 | 1 | 10 | 0 | 0 | 0 | 2 | new |
| #2 | 1 | - | 2 | 1 | 1 | 2 | 0 | 0 | 3 | 1 | new |
| #2 | 2 | - | 1 | 0 | 1 | 1 | 0 | 0 | 2 | 0 | new |
| #4 | 0 | - | 6 | 1 | 0 | 6 | 0 | 0 | 0 | 1 | new |
| #4 | 1 | - | 1 | 0 | 0 | 1 | 0 | 0 | 5 | 0 | new |
| #5 | 0 | - | 19 | 7 | 3 | 19 | 0 | 0 | 0 | 4 | new |
| #5 | 1 | - | 8 | 2 | 2 | 8 | 0 | 0 | 11 | 2 | new |
| #5 | 2 | - | 4 | 1 | 2 | 4 | 0 | 0 | 11 | 1 | new |
| #5 | 3 | APPROVE | 1 | 0 | 0 | 1 | 0 | 0 | 3 | 0 | new |
| #6 | 0 | - | 5 | 2 | 2 | 5 | 0 | 0 | 0 | 1 | new |
| #6 | 1 | APPROVE | 2 | 0 | 1 | 2 | 0 | 0 | 3 | 0 | new |
| #7 | 0 | APPROVE | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 0 | new |
| #8 | 0 | REQUEST CHANGES | 17 | 8 | 2 | 17 | 0 | 1 | 0 | 4 | new |
| #8 | 1 | REQUEST CHANGES | 5 | 1 | 3 | 5 | 0 | 0 | 5 | 1 | new |
| #8 | 2 | REQUEST CHANGES | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | confirm-only |
| #8 | 3 | APPROVE WITH NITS | 3 | 0 | 3 | 3 | 0 | 0 | 2 | 0 | new |
| #9 | 0 | REQUEST CHANGES | 14 | 5 | 3 | 14 | 0 | 0 | 0 | 5 | new |
| #9 | 1 | APPROVE WITH NITS | 3 | 0 | 0 | 3 | 0 | 0 | 6 | 0 | new |
| #9 | 2 | REQUEST CHANGES | 6 | 3 | 0 | 6 | 0 | 0 | 0 | 3 | new |
| #9 | 3 | APPROVE WITH NITS | 2 | 0 | 0 | 2 | 0 | 0 | 3 | 0 | new |
| #18 | 0 | REQUEST CHANGES | 10 | 2 | 1 | 10 | 0 | 0 | 0 | 2 | new |
| #18 | 1 | APPROVE WITH NITS | 5 | 0 | 0 | 5 | 0 | 0 | 6 | 0 | new |
| #19 | 0 | - | 16 | 5 | 1 | 16 | 0 | 0 | 0 | 5 | new |
| #19 | 1 | APPROVE WITH CONDITIONS | 2 | 0 | 1 | 2 | 0 | 1 | 13 | 0 | new |
| #19 | 2 | APPROVE | 2 | 0 | 0 | 2 | 0 | 0 | 3 | 0 | new |
| #20 | 0 | - | 15 | 8 | 2 | 15 | 0 | 0 | 0 | 6 | new |
| #20 | 1 | - | 6 | 2 | 1 | 6 | 0 | 0 | 12 | 1 | new |
| #20 | 2 | - | 4 | 2 | 0 | 4 | 0 | 0 | 4 | 2 | new |
| #20 | 3 | - | 3 | 0 | 1 | 3 | 0 | 0 | 5 | 0 | new |
| #20 | 4 | - | 1 | 0 | 0 | 1 | 0 | 0 | 3 | 0 | new |
| #21 | 0 | APPROVE WITH CONDITIONS | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | new |
| #21 | 1 | APPROVE | 1 | 0 | 0 | 1 | 0 | 0 | 5 | 0 | new |
| #22 | 0 | REQUEST CHANGES | 12 | 2 | 4 | 12 | 0 | 0 | 0 | 1 | new |
| #22 | 1 | APPROVE WITH CONDITIONS | 2 | 0 | 1 | 2 | 0 | 0 | 7 | 0 | new |
| #22 | 2 | APPROVE | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | confirm-only |
| #23 | 0 | - | 9 | 3 | 2 | 9 | 0 | 0 | 0 | 3 | new |
| #23 | 1 | APPROVE WITH CONDITIONS | 4 | 0 | 1 | 4 | 0 | 0 | 10 | 0 | new |
| #24 | 0 | REQUEST CHANGES | 8 | 2 | 2 | 8 | 0 | 0 | 0 | 1 | new |
| #24 | 1 | APPROVE | 2 | 0 | 1 | 2 | 0 | 0 | 5 | 0 | new |
| #26 | 0 | REQUEST CHANGES | 12 | 6 | 1 | 12 | 0 | 0 | 0 | 3 | new |
| #26 | 1 | APPROVE WITH CONDITIONS | 3 | 0 | 1 | 3 | 0 | 0 | 5 | 0 | new |
| #27 | 0 | APPROVE WITH CONDITIONS | 10 | 0 | 3 | 10 | 0 | 0 | 0 | 0 | new |
| #29 | 0 | REQUEST CHANGES | 14 | 4 | 1 | 14 | 0 | 0 | 0 | 0 | new |

### Cadence findings ledger, per stage

| stage | raised | blocking | should-fix | confirmed defects | new | repeat id | repeat text | fix-induced |
|---|---|---|---|---|---|---|---|---|
| architecture-review-plan | 8 | 2 | 0 | 0 | 2 | 0 | 6 | 0 |
| test-benchmark-pr | 13 | 13 | 0 | 12 | 13 | 0 | 0 | 1 |
| pr-review-local | 2 | 2 | 0 | 2 | 2 | 0 | 0 | 0 |
| architecture-review-impl | 3 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| test-benchmark-plan | 3 | 3 | 0 | 3 | 3 | 0 | 0 | 0 |

Unique ids: 29; blocking: 20; confirmed defects: 17; skipped rows: 0.

Reading:

- test-benchmark-pr is the most productive stage in this ledger: 12 of its 13 findings were
  confirmed defects.
- The architecture-review stages raised 11 rows and no confirmed defect. 9 of the 11 are the
  same evidence filed again for each task (repeat text). Their 2 blocking rows are deferred.
- 17 of the ledger's 20 blocking findings are confirmed.
