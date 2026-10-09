import json

from _cli import cli  # noqa: F401


def _setup(cli):
    cli("account", "add", "checking")
    cli("account", "add", "card")
    assert cli("budget", "set", "groceries", "100")[0] == 0


def test_budget_set_and_list(cli):
    _setup(cli)
    cli("budget", "set", "dining", "50")
    code, out, _ = cli("budget", "list")
    assert code == 0 and out == ["dining: 50.00", "groceries: 100.00"]


def test_non_positive_limit_is_an_error(cli):
    assert cli("budget", "set", "groceries", "0")[0] == 2
    assert cli("budget", "set", "groceries", "-5")[0] == 2


def test_budget_report_across_accounts(cli):
    _setup(cli)
    cli("tx", "add", "checking", "2026-01-05", "-40", "groceries")
    cli("tx", "add", "card", "2026-01-09", "-10", "groceries")
    cli("tx", "add", "card", "2026-01-10", "15", "groceries")  # a refund does not count as spending
    cli("tx", "add", "card", "2026-02-01", "-99", "groceries")
    code, out, _ = cli("report", "budget", "2026-01")
    assert code == 0 and out == ["groceries: spent 50.00 of 100.00 (50%)"]


def test_over_budget_is_marked(cli):
    _setup(cli)
    cli("tx", "add", "checking", "2026-01-05", "-120", "groceries")
    code, out, _ = cli("report", "budget", "2026-01")
    assert out == ["groceries: spent 120.00 of 100.00 (120%) OVER"]


def test_tx_add_alerts_when_crossing_the_limit(cli):
    _setup(cli)
    _, out, _ = cli("tx", "add", "checking", "2026-01-05", "-90", "groceries")
    assert not any(line.startswith("alert:") for line in out)
    _, out, _ = cli("tx", "add", "card", "2026-01-06", "-20", "groceries")
    assert "alert: groceries over budget for 2026-01 (110.00/100.00)" in out


def test_import_alerts_once_per_category(cli):
    _setup(cli)
    csv = cli.tmp / "s.csv"
    csv.write_text("date,amount,category\n2026-01-01,-80,groceries\n2026-01-02,-30,groceries\n2026-01-03,-30,groceries\n")
    code, out, _ = cli("import", "checking", str(csv))
    alerts = [line for line in out if line.startswith("alert:")]
    assert code == 0 and alerts == ["alert: groceries over budget for 2026-01 (140.00/100.00)"]


def test_store_without_budgets_still_works(cli):
    cli.store.write_text(json.dumps({"version": 1, "accounts": {"checking": {"transactions": []}}}))
    assert cli("report", "balances")[0] == 0
    assert cli("budget", "list") == (0, [], "")
