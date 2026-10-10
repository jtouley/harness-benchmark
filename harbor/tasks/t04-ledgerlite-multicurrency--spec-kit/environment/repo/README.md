# ledgerlite

A small personal ledger. Accounts hold transactions; a JSON file stores everything;
CSV files import transactions; reports print balances and monthly category totals.

```
python -m ledgerlite.cli --store ledger.json account add checking
python -m ledgerlite.cli --store ledger.json tx add checking 2026-01-05 -42.50 groceries "corner shop"
python -m ledgerlite.cli --store ledger.json import checking statement.csv
python -m ledgerlite.cli --store ledger.json report balances
python -m ledgerlite.cli --store ledger.json report monthly 2026-01
```

Run tests: `python -m pytest`.
