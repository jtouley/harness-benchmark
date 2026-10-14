import json

from _cli import cli  # noqa: F401


def test_balances_show_account_currency_and_base_total(cli):
    assert cli("account", "add", "checking")[0] == 0
    assert cli("account", "add", "savings", "--currency", "EUR")[0] == 0
    assert cli("rate", "set", "EUR", "USD", "1.10")[0] == 0
    cli("tx", "add", "checking", "2026-01-05", "-42.50", "groceries")
    cli("tx", "add", "savings", "2026-01-06", "100", "transfer")
    code, out, _ = cli("report", "balances")
    assert code == 0
    assert out == ["checking: -42.50 USD", "savings: 100.00 EUR", "TOTAL: 67.50 USD"]


def test_total_in_another_base(cli):
    cli("account", "add", "savings", "--currency", "EUR")
    cli("tx", "add", "savings", "2026-01-06", "100", "transfer")
    code, out, _ = cli("report", "balances", "--base", "EUR")
    assert code == 0 and out[-1] == "TOTAL: 100.00 EUR"


def test_missing_rate_is_an_error_naming_the_pair(cli):
    cli("account", "add", "checking")
    cli("account", "add", "savings", "--currency", "EUR")
    cli("tx", "add", "savings", "2026-01-06", "100", "transfer")
    code, _, err = cli("report", "balances")
    assert code == 2 and "EUR" in err and "USD" in err


def test_monthly_converts_to_base(cli):
    cli("account", "add", "savings", "--currency", "EUR")
    cli("rate", "set", "EUR", "USD", "1.10")
    cli("tx", "add", "savings", "2026-01-06", "-10", "groceries")
    code, out, _ = cli("report", "monthly", "2026-01")
    assert code == 0 and out[0] == "groceries: -11.00"


def test_import_currency_column_must_match_account(cli):
    cli("account", "add", "savings", "--currency", "EUR")
    good = cli.tmp / "g.csv"
    good.write_text("date,amount,category,currency\n2026-01-01,-3,coffee,EUR\n")
    assert cli("import", "savings", str(good))[0] == 0
    bad = cli.tmp / "b.csv"
    bad.write_text("date,amount,category,currency\n2026-01-02,-3,coffee,USD\n")
    assert cli("import", "savings", str(bad))[0] == 2


def test_legacy_store_loads_as_usd(cli):
    cli.store.write_text(json.dumps({"version": 1, "accounts": {"checking": {"transactions": [
        {"id": "a1", "on": "2026-01-05", "amount": "-42.50", "category": "groceries", "memo": ""}]}}}))
    code, out, _ = cli("report", "balances")
    assert code == 0 and out[0] == "checking: -42.50 USD"
