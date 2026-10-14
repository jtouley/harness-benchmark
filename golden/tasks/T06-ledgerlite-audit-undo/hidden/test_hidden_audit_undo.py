import json

from _cli import cli  # noqa: F401


def test_every_change_is_audited_in_order(cli):
    cli("account", "add", "checking")
    cli("tx", "add", "checking", "2026-01-05", "-42.50", "groceries")
    cli("report", "balances")  # reads only: not audited
    code, out, _ = cli("audit")
    assert code == 0 and len(out) == 2
    assert out[0].startswith("1 account add") and out[1].startswith("2 tx add")


def test_undo_reverts_the_last_change(cli):
    cli("account", "add", "checking")
    cli("tx", "add", "checking", "2026-01-05", "-42.50", "groceries")
    cli("tx", "add", "checking", "2026-01-06", "-7.50", "coffee")
    assert cli("undo")[0] == 0
    assert cli("report", "balances")[1][0] == "checking: -42.50"


def test_undo_n_and_import_is_one_change(cli):
    cli("account", "add", "checking")
    csv = cli.tmp / "s.csv"
    csv.write_text("date,amount,category\n2026-01-01,-3,coffee\n2026-01-02,-4,coffee\n")
    cli("import", "checking", str(csv))
    cli("tx", "add", "checking", "2026-01-03", "-5", "coffee")
    assert cli("undo", "2")[0] == 0
    assert cli("report", "balances")[1][0] == "checking: 0.00"


def test_undo_is_audited_and_not_undoable(cli):
    cli("account", "add", "checking")
    cli("tx", "add", "checking", "2026-01-05", "-1", "x")
    cli("undo")
    _, out, _ = cli("audit")
    assert out[-1].split()[1] == "undo"
    cli("undo")  # undoes the account add, not the undo
    _, out, _ = cli("report", "balances")
    assert out == ["TOTAL: 0.00"]


def test_undo_more_than_exists_changes_nothing(cli):
    cli("account", "add", "checking")
    cli("tx", "add", "checking", "2026-01-05", "1", "x")
    cli("tx", "add", "checking", "2026-01-06", "2", "y")
    # `undo N` must work first: an unknown subcommand or argument also exits 2.
    assert cli("undo", "1")[0] == 0
    assert cli("undo", "5")[0] == 2
    assert cli("report", "balances")[1][0] == "checking: 1.00"


def test_store_without_audit_still_works(cli):
    cli.store.write_text(json.dumps({"version": 1, "accounts": {"checking": {"transactions": []}}}))
    assert cli("report", "balances")[0] == 0
    assert cli("undo")[0] == 2  # nothing to undo
    # undo exists: after a change it succeeds (an unknown subcommand would also exit 2).
    cli("account", "add", "savings")
    assert cli("undo")[0] == 0
