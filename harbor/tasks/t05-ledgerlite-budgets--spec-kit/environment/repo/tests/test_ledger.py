from decimal import Decimal

import pytest

from ledgerlite import storage
from ledgerlite.models import LedgerError


def test_balances_and_total(ledger):
    ledger("account", "add", "checking")
    ledger("account", "add", "savings")
    ledger("tx", "add", "checking", "2026-01-05", "-42.50", "groceries")
    ledger("tx", "add", "savings", "2026-01-06", "100", "transfer")
    assert ledger("report", "balances") == ["checking: -42.50", "savings: 100.00", "TOTAL: 57.50"]


def test_monthly_groups_by_category(ledger):
    ledger("account", "add", "checking")
    ledger("tx", "add", "checking", "2026-01-05", "-40", "groceries")
    ledger("tx", "add", "checking", "2026-01-20", "-10", "groceries")
    ledger("tx", "add", "checking", "2026-02-01", "-5", "groceries")
    assert ledger("report", "monthly", "2026-01") == ["groceries: -50.00", "NET: -50.00"]


def test_import_csv(ledger):
    ledger("account", "add", "checking")
    csv = ledger.tmp / "s.csv"
    csv.write_text("date,amount,category,memo\n2026-01-01,-3.10,coffee,cafe\n2026-01-02,1200,salary,\n")
    assert ledger("import", "checking", str(csv)) == ["imported 2 transactions"]
    assert ledger("report", "balances")[0] == "checking: 1196.90"


def test_import_rejects_bad_amount(ledger):
    ledger("account", "add", "checking")
    csv = ledger.tmp / "bad.csv"
    csv.write_text("date,amount,category\n2026-01-01,abc,coffee\n")
    with pytest.raises(LedgerError, match="line 2"):
        ledger("import", "checking", str(csv))


def test_storage_round_trip(ledger):
    ledger("account", "add", "checking")
    ledger("tx", "add", "checking", "2026-03-01", "-1.25", "snacks", "vending")
    loaded = storage.load(ledger.store)
    tx = loaded.account("checking").transactions[0]
    assert (tx.amount, tx.category, tx.memo) == (Decimal("-1.25"), "snacks", "vending")


def test_unknown_account_is_an_error(ledger):
    with pytest.raises(LedgerError):
        ledger("tx", "add", "nope", "2026-01-01", "1", "x")
