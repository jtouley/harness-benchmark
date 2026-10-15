# Summary

Added monthly category budgets to ledgerlite on branch `feat/category-budgets`, committed and pushed to origin. No GitHub here, so the PR text is in `PR.md`.

## Stages
1. **Explore**: read the CLI, models, storage, reports, importer and tests. Commands are argparse-based, the store is a single JSON file, and `LedgerError` maps to exit 2.
2. **Implement**:
   - `models.py`: `Ledger.budgets`, `set_budget` (checks the limit is positive and finite), `spending(category, month)`, and an `outflow()` helper.
   - `storage.py`: load and save an optional `budgets` map. Old stores still load.
   - `reports.py`: `budget_list`, `budget` report (half-up PCT, OVER flag, YYYY-MM check), and `budget_alerts`. It works out spending before the command by subtracting the added outflows, so it only alerts when the limit is crossed, once per category/month.
   - `cli.py`: `budget set|list`, `report budget`, alerts after `tx add` and `import`, and a shared `parse_amount`.
   - README: added usage and semantics.
3. **Test**: added `tests/test_budgets.py` (16 cases). `uv run --extra dev python -m pytest` gives 22 passed. Also checked by hand through the CLI: a negative limit exits 2, and the alert and OVER lines print as specified.
4. **Commit/push**: one commit on `feat/category-budgets`, pushed to origin.
5. **PR**: written to `outputs/PR.md`.

## Judgment calls
- Alerts fire only when a command crosses the limit, not on every transaction while a category is over.
- If one import crosses the same category in two different months, it prints one alert per month.
- PCT uses half-up rounding.
- `report budget` rejects a malformed month.
