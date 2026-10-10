"""JSON file storage. The whole ledger is read and written at once."""

from __future__ import annotations

import json
import os
from decimal import Decimal
from pathlib import Path

from ledgerlite.models import Account, Ledger, Transaction

FORMAT_VERSION = 1


def load(path: Path) -> Ledger:
    path = Path(path)
    if not path.exists():
        return Ledger()
    data = json.loads(path.read_text(encoding="utf-8"))
    ledger = Ledger()
    for name, raw in data.get("accounts", {}).items():
        account = Account(name)
        for t in raw.get("transactions", []):
            account.transactions.append(
                Transaction(
                    account=name,
                    on=t["on"],
                    amount=Decimal(t["amount"]),
                    category=t["category"],
                    memo=t.get("memo", ""),
                    id=t["id"],
                )
            )
        ledger.accounts[name] = account
    return ledger


def save(ledger: Ledger, path: Path) -> None:
    path = Path(path)
    data = {
        "version": FORMAT_VERSION,
        "accounts": {
            name: {
                "transactions": [
                    {"id": t.id, "on": t.on, "amount": str(t.amount), "category": t.category, "memo": t.memo}
                    for t in account.transactions
                ]
            }
            for name, account in ledger.accounts.items()
        },
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
