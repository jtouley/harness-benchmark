# Add monthly category budgets with over-budget alerts

Branch: `feat/category-budgets` → `main`

## What
- `budget set CATEGORY LIMIT` — sets a monthly spending limit for a category across all accounts. LIMIT must be a positive finite number; otherwise the command exits 2 (`error: ...`). Setting again replaces the limit.
- `budget list` — prints `CATEGORY: LIMIT` sorted by category.
- `report budget YYYY-MM` — one line per budgeted category: `CATEGORY: spent SPENT of LIMIT (PCT%)`, with ` OVER` when spent > limit.
- `tx add` / `import` print `alert: CATEGORY over budget for YYYY-MM (SPENT/LIMIT)` when the command pushes a budgeted category from within its limit to over it.
- Budgets are stored under a new optional `budgets` key in the JSON store. Stores without it load fine (no format version bump needed).

## Semantics
- Spending = sum of negative amounts for the category and month, shown as a positive number. Refunds (positive amounts) don't reduce it.
- PCT = spent / limit × 100, rounded half-up to an integer (so 100.5% shows as 101%, not banker's rounding).
- Money is shown with 2 decimals everywhere, limits included.
- Alerts fire only when the command crosses the limit (spending before the command ≤ limit < spending after). Spending exactly at the limit isn't over. A category that was already over doesn't alert again. SPENT is the month's total after the whole command. An import alerts once per category, after all rows are added.

## Interpretation notes
- If one import pushes the same category over budget in **two different months**, it prints one alert per (category, month), because each alert names its month. Within a single month it's exactly one alert per category.
- `report budget` rejects a month that isn't `YYYY-MM` (exit 2). `report monthly` is unchanged.

## Tests
`tests/test_budgets.py` (16 cases): set/list/replace, invalid limits (0, negative, non-numeric, NaN, Infinity) including exit code 2, cross-account spending, refunds ignored, other months excluded, OVER flag and the exactly-at-limit boundary, half-up rounding, crossing-only alerts, a new month starting fresh, unbudgeted/refund transactions, one import alert using the final total, persistence, and loading a legacy store. Full suite: 22 passed.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
