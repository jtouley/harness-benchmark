# PR (draft, not opened)

Status: not opened. Implementation has not started. The Cadence run stopped at the P9 entry invariant. See `summary.md`. This environment has no GitHub, so this text is the PR that would be created.

## Title

Add monthly category budgets to ledgerlite

## Body

## Summary

- Add `budget set CATEGORY LIMIT` and `budget list` to set and show monthly limits per category across all accounts.
- Add `report budget YYYY-MM`, which prints spent, limit, and percent used for each budgeted category. It appends ` OVER` when spent is above the limit.
- `tx add` and `import` print `alert: CATEGORY over budget for YYYY-MM (SPENT/LIMIT)` when a command crosses a category's limit for a month. One alert is printed per (category, month) per command.
- Budgets are stored under a `"budgets"` key in the JSON store. The store format version stays 1, and stores without budgets still load.

## Behavior notes

- Spending is the sum of negative amounts in a category and month. Refunds do not reduce it.
- An alert fires only when a command crosses the limit. A category that is already over does not alert again in a later command.
- The alert total is the month's spending after the whole command.
- LIMIT must be a plain decimal with at most 2 decimal places and above zero. Other input exits 2.
- `tx add` and `import` now reject non-finite amounts (`NaN`, `Infinity`) with exit 2. This changes existing behavior.
- Percent rounds half-up to an integer.

## Known limits

- Older ledgerlite versions drop the `"budgets"` key when they save the store.
- `Transaction.month` still uses `on[:7]`, so `report monthly` misses compact dates such as `20261001`. The budget code uses the parsed date.

## Test plan

- [ ] `uv run --with pytest python -m pytest` passes, including the 6 existing tests
- [ ] Budget tests cover limit validation (exit 2), listing order, report rounding and OVER, refund handling, alert crossing and once-per-(category, month), atomic import, and store compatibility
- [ ] Spec ambiguities are settled as listed in `.context/plans/ledgerlite-budgets.plan.md`

## Open items

- The spec says "once per category per command". This change alerts once per (category, month). The spec should be amended.
- Cadence P9 (entry invariant) does not pass on Claude Code. See `summary.md`.
