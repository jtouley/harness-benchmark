**Tracker:** github-issues
**Ticket:** TICKET_SKIPPED (github-issues adapter; no issue id is bound to task ledgerlite-budgets)
Pipeline-Run: 32906c13-98f1-4114-b9a9-f3da5bec9690

VERDICT: PASS
RUN_BY_COMMAND: vibe-test

Scope: spec "Add monthly category budgets to ledgerlite", checked against ledgerlite/{cli,models,storage,reports,importers}.py at commit e35c542. Python checks: `Decimal("NaN")` parses but raises InvalidOperation on `<` or `>`; `Decimal("Infinity") > 0` is True; `format(Decimal, ".2f")` and `quantize` default to ROUND_HALF_EVEN.

Gaps. All non-blocking. Each has a default to adopt.

1. "Pushes past" is ambiguous. Default: crossing only. Alert for a (category, month) pair iff pre-command spent <= limit < post-command spent. A category already over before the command does not alert again. Zero and positive amounts (refunds) never change spent, so they never alert.

2. Multi-month commands. The spec says "once per category per command", but the alert text carries YYYY-MM. Default: once per (category, month) pair, ordered by category then month. Amend the spec wording to match.

3. Alert format. Default: `alert: food over budget for 2026-10 (120.00/100.00)`. SPENT is the month total after the whole command. Print alerts after the primary line (`added ID` or `imported N transactions`). Exit code stays 0.

4. PCT .5 cases. Half-even turns 1 of 8 (12.5%) into 12. Default: `quantize(Decimal(1), ROUND_HALF_UP)` for PCT only. Money keeps the existing `:.2f` (matches `balances` and `monthly`).

5. `budget set` output. Unspecified. Default: print `budget food: 100.00`, exit 0, matching the one-line style of `account add` and `tx add`. A repeat set overwrites. `budget set` never prints alerts.

6. Non-numeric LIMIT. `Decimal("abc")` raises InvalidOperation, which `cli.run` does not map to a LedgerError. Default: wrap it as LedgerError, exit 2, as `tx add` does.

7. Other invalid LIMIT. `Infinity` passes "> 0". `NaN` raises during the comparison and produces a traceback. A limit with more than 2 decimals (0.004) is positive but displays as 0.00. Default: reject non-finite values and values with more than 2 decimals, exit 2.

8. Empty category. Default: LedgerError "category is required", exit 2, matching `Transaction.__post_init__`.

9. Budget with no transactions. Default: print it, e.g. `food: spent 0.00 of 100.00 (0%)`. The spec's "one line per budgeted category" implies this. With no budgets, `report budget` prints nothing and exits 0.

10. Category matching and order. Default: exact, case-sensitive, no trimming, as transactions already work. Sort with plain Python string order in both `budget list` and `report budget`.

11. Invalid month for `report budget`. `report monthly` does not validate either. Default: require `^\d{4}-(0[1-9]|1[0-2])$`, else LedgerError, exit 2.

12. Pre-existing NaN amounts. `tx add a 2026-10-01 NaN food` is accepted and saved today. The spent sum then raises InvalidOperation for that category and month. Default: reject non-finite amounts in `tx add` and `import` with LedgerError, exit 2. This changes existing behavior, so the owner should confirm it.

13. Persistence. Default: add `"budgets": {"food": "100"}` (strings, as amounts are stored). `load` reads `data.get("budgets", {})`. `save` always writes the key. Keep FORMAT_VERSION at 1, because old stores load and old code ignores the key. Add tests for loading an old store and for the round trip.

14. Import atomicity. `import_csv` raises before `save` on a bad row, so there is no partial write and no alert. Default: keep this and add a test.

15. Budget removal. Not in the spec. Default: out of scope. Only overwrite-by-set exists.

RUN_BY_COMMAND: vibe-test
