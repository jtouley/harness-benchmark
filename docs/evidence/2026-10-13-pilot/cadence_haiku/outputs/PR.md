# PR status: not opened

No PR was opened. The Cadence run stopped at P6 with a retries hard stop, and no code was written. The text below is the draft that would open the PR after the open P6 items are fixed and E1 has run. No GitHub or Linear access was available, so nothing was posted to any tracker.

## Title

Add monthly category budgets to ledgerlite

## Body

## Summary

- Add `budget set CATEGORY LIMIT` and `budget list`. Budgets persist under a `budgets` key in the JSON store.
- Add `report budget YYYY-MM`. It prints spent, limit, percent, and OVER for each budgeted category.
- `tx add` and `import` print an alert when they push a category past its limit for the month. The alert counts spending after the whole command, and prints once per category per command.
- Reject non-finite amounts, amounts outside 0.01 to below 1e12, and non-`YYYY-MM-DD` dates in `tx add` and `import`. These are behavior changes. The store loader rejects malformed stored data with exit 2.

## Test plan

- [ ] `python -m pytest` passes. Covers the acceptance criteria 1 to 26 in `.context/specs/ledgerlite-budgets.md`.
- [ ] Manual run: `budget set groceries 100`, `tx add ... -120 groceries`, and `report budget <month>` show `OVER` and the alert.
- [ ] A store file from before this change loads with no budgets.

Ticket: TICKET_SKIPPED (no tracker in this environment).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
