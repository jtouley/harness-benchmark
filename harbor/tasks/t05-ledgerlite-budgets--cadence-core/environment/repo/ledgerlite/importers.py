"""CSV import. Columns: date, amount, category, memo (memo optional)."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerlite.models import Ledger, LedgerError, Transaction


def import_csv(ledger: Ledger, account: str, path: Path) -> list[Transaction]:
    ledger.account(account)
    added: list[Transaction] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for lineno, row in enumerate(csv.DictReader(handle), start=2):
            try:
                amount = Decimal(row["amount"])
            except (InvalidOperation, KeyError) as exc:
                raise LedgerError(f"line {lineno}: bad amount") from exc
            tx = Transaction(
                account=account,
                on=row["date"],
                amount=amount,
                category=row["category"],
                memo=row.get("memo", "") or "",
            )
            added.append(ledger.add_transaction(tx))
    return added
