"""Command line interface. Every command loads the store, acts, and saves."""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerlite import reports, storage
from ledgerlite.importers import import_csv
from ledgerlite.models import LedgerError, Transaction


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ledger")
    parser.add_argument("--store", default="ledger.json")
    sub = parser.add_subparsers(dest="command", required=True)

    account = sub.add_parser("account").add_subparsers(dest="action", required=True)
    add = account.add_parser("add")
    add.add_argument("name")

    tx = sub.add_parser("tx").add_subparsers(dest="action", required=True)
    tx_add = tx.add_parser("add")
    tx_add.add_argument("account")
    tx_add.add_argument("on")
    tx_add.add_argument("amount")
    tx_add.add_argument("category")
    tx_add.add_argument("memo", nargs="?", default="")

    imp = sub.add_parser("import")
    imp.add_argument("account")
    imp.add_argument("csv")

    report = sub.add_parser("report").add_subparsers(dest="kind", required=True)
    report.add_parser("balances")
    monthly = report.add_parser("monthly")
    monthly.add_argument("month")
    return parser


def run(argv: list[str]) -> list[str]:
    args = build_parser().parse_args(argv)
    path = Path(args.store)
    ledger = storage.load(path)
    out: list[str] = []
    if args.command == "account":
        ledger.add_account(args.name)
        out.append(f"added account {args.name}")
    elif args.command == "tx":
        try:
            amount = Decimal(args.amount)
        except InvalidOperation as exc:
            raise LedgerError(f"bad amount {args.amount!r}") from exc
        tx = ledger.add_transaction(Transaction(args.account, args.on, amount, args.category, args.memo))
        out.append(f"added {tx.id}")
    elif args.command == "import":
        added = import_csv(ledger, args.account, Path(args.csv))
        out.append(f"imported {len(added)} transactions")
    elif args.command == "report":
        out.extend(reports.balances(ledger) if args.kind == "balances" else reports.monthly(ledger, args.month))
    storage.save(ledger, path)
    return out


def main(argv: list[str] | None = None) -> int:
    try:
        for line in run(sys.argv[1:] if argv is None else argv):
            print(line)
    except LedgerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
