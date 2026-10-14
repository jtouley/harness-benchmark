"""Domain objects. Amounts are Decimal; dates are ISO strings (YYYY-MM-DD)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import uuid4


class LedgerError(ValueError):
    """A user-facing error: bad input or an impossible operation."""


@dataclass(frozen=True)
class Transaction:
    account: str
    on: str
    amount: Decimal
    category: str
    memo: str = ""
    id: str = field(default_factory=lambda: uuid4().hex[:12])

    def __post_init__(self) -> None:
        try:
            date.fromisoformat(self.on)
        except ValueError as exc:
            raise LedgerError(f"bad date {self.on!r}") from exc
        if not self.category:
            raise LedgerError("category is required")

    @property
    def month(self) -> str:
        return self.on[:7]


@dataclass
class Account:
    name: str
    transactions: list[Transaction] = field(default_factory=list)

    def balance(self) -> Decimal:
        return sum((t.amount for t in self.transactions), Decimal("0"))


@dataclass
class Ledger:
    accounts: dict[str, Account] = field(default_factory=dict)

    def add_account(self, name: str) -> Account:
        if not name or name in self.accounts:
            raise LedgerError(f"account {name!r} exists or is empty")
        self.accounts[name] = Account(name)
        return self.accounts[name]

    def account(self, name: str) -> Account:
        try:
            return self.accounts[name]
        except KeyError as exc:
            raise LedgerError(f"no account {name!r}") from exc

    def add_transaction(self, tx: Transaction) -> Transaction:
        self.account(tx.account).transactions.append(tx)
        return tx

    def all_transactions(self) -> list[Transaction]:
        return [t for a in self.accounts.values() for t in a.transactions]
