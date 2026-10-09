"""Plain-text reports."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from ledgerlite.models import Ledger


def balances(ledger: Ledger) -> list[str]:
    lines = [f"{name}: {account.balance():.2f}" for name, account in sorted(ledger.accounts.items())]
    total = sum((a.balance() for a in ledger.accounts.values()), Decimal("0"))
    lines.append(f"TOTAL: {total:.2f}")
    return lines


def monthly(ledger: Ledger, month: str) -> list[str]:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for tx in ledger.all_transactions():
        if tx.month == month:
            totals[tx.category] += tx.amount
    lines = [f"{category}: {amount:.2f}" for category, amount in sorted(totals.items())]
    lines.append(f"NET: {sum(totals.values(), Decimal('0')):.2f}")
    return lines
