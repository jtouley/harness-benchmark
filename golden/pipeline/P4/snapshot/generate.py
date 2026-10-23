"""Generate the P4 inputs: one year of a fictional public library's loans and fines (synthetic, CC0).

    python3 golden/pipeline/P4/snapshot/generate.py [--out golden/pipeline/P4/data/raw]

Standard library only, one fixed seed, so the files regenerate byte for byte (tests/test_pipeline_p4.py).
No download: every name and number here is made up. The data holds the traps of
docs/plans/tasks/P4-holdout-library-loans.md (hidden from arms): the two loan files overlap by one week,
branch codes have leading zeros, replacement costs are money text with a dollar sign and thousands
separators, fines include negative waiver rows, some loans were checked out before the year and only
return in it, and some loans are still out at the end of the year.

Files (CSV, UTF-8, header row):
- branches.csv: branch_code, branch_name, region
- items.csv: item_id, title, category, home_branch, replacement_cost
- patrons.csv: patron_id, home_branch, joined_year
- loans_2025_h1.csv, loans_2025_h2.csv: loan_id, event, event_time, branch_code, item_id, patron_id
  (one row per loan event: checkout, renew or return; event_time is UTC, ISO 8601 with Z)
- fines.csv: fine_id, loan_id, branch_code, assessed_time, amount (dollars; a waiver is negative)
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

SEED = 20251031
YEAR = 2025
LOAN_DAYS = 21
OVERLAP_START = datetime(2025, 6, 24)  # H2 restates H1's events from here to the end of June
H2_START = datetime(2025, 7, 1)
BRANCHES = [("01", "Central", "north"), ("02", "Riverside", "north"), ("03", "Hillcrest", "north"),
            ("04", "Oakwood", "east"), ("05", "Lakeside", "east"), ("06", "Pinecrest", "east"),
            ("07", "Meadowbrook", "south"), ("08", "Harbor", "south"), ("09", "Elm Street", "south"),
            ("10", "Westgate", "west"), ("11", "Fairview", "west"), ("12", "Summit", "west")]
CATEGORIES = [("fiction", 14, 32), ("nonfiction", 18, 60), ("children", 8, 24), ("media", 20, 45),
              ("reference", 90, 1800)]
WORDS = ["River", "Winter", "Garden", "Atlas", "Harbor", "Lantern", "Meadow", "Orchard", "Quiet", "Signal",
         "Thread", "Voyage", "Window", "Copper", "Ember", "Field", "Glass", "Hollow", "Island", "Journey"]


def _stamp(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _money(d: Decimal) -> str:
    """Money text as the library's system exports it: a dollar sign and thousands separators."""
    return "${:,.2f}".format(d)


def generate(out: Path, seed: int = SEED) -> dict[str, int]:
    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)
    branch_codes = [b[0] for b in BRANCHES]

    items = []
    for i in range(1, 1501):
        cat, low, high = CATEGORIES[rng.choices(range(5), weights=[40, 30, 15, 10, 5])[0]]
        cost = Decimal(rng.randint(low * 100, high * 100)) / 100
        title = f"{rng.choice(WORDS)} {rng.choice(WORDS)} {i}"
        items.append((f"I{i:06d}", title, cat, rng.choice(branch_codes), cost))
    patrons = [(f"P{i:05d}", rng.choice(branch_codes), rng.randint(2001, 2025)) for i in range(1, 801)]
    # A few patrons borrow much more than the rest, so the top items are clear.
    weights = [rng.choice([1, 1, 1, 1, 2, 2, 3, 6]) for _ in patrons]
    popular = rng.sample(range(len(items)), 60)
    item_weights = [1] * len(items)
    for k in popular:
        item_weights[k] = rng.randint(6, 14)

    events: list[tuple[str, str, datetime, str, str, str]] = []
    fines: list[tuple[str, str, str, datetime, Decimal]] = []
    year_start, year_end = datetime(YEAR, 1, 1), datetime(YEAR + 1, 1, 1)
    seconds = int((year_end - year_start).total_seconds())
    loan_n, fine_n = 0, 0

    def add_fine(loan_id: str, branch: str, when: datetime, amount: Decimal) -> None:
        nonlocal fine_n
        fine_n += 1
        fines.append((f"F{fine_n:06d}", loan_id, branch, when, amount))

    def add_loan(checkout: datetime, in_files: bool) -> None:
        nonlocal loan_n
        loan_n += 1
        loan_id = f"L{loan_n:06d}"
        item = items[rng.choices(range(len(items)), weights=item_weights)[0]]
        patron = patrons[rng.choices(range(len(patrons)), weights=weights)[0]]
        branch = rng.choice([item[3], item[3], patron[1]])
        if in_files:
            events.append((loan_id, "checkout", checkout, branch, item[0], patron[0]))
        renewals = rng.choices([0, 1, 2], weights=[60, 30, 10])[0]
        t = checkout
        for _ in range(renewals):
            t = t + timedelta(days=rng.randint(10, LOAN_DAYS), hours=rng.randint(0, 23))
            if t >= year_end:
                return
            if t >= year_start:
                events.append((loan_id, "renew", t, branch, item[0], patron[0]))
        due = checkout + timedelta(days=LOAN_DAYS * (1 + renewals))
        if rng.random() < 0.03:
            return  # never returned
        late = rng.random() < 0.18
        ret = due + timedelta(days=rng.randint(1, 40), hours=rng.randint(0, 23)) if late else \
            t + timedelta(days=rng.randint(1, LOAN_DAYS - 1), hours=rng.randint(0, 23))
        ret = max(ret, t + timedelta(hours=1))
        if ret >= year_end:
            return  # still out at the end of the year
        if ret >= year_start:
            events.append((loan_id, "return", ret, branch, item[0], patron[0]))
        if late and ret >= year_start:
            days_late = max(1, (ret - due).days)
            amount = min(Decimal(days_late) * Decimal("0.25"), Decimal("10.00"))
            add_fine(loan_id, branch, ret + timedelta(minutes=5), amount)
            if rng.random() < 0.12:
                add_fine(loan_id, branch, ret + timedelta(days=rng.randint(1, 20)), -amount)

    for _ in range(120):  # loans from the year before: their checkout is in no file
        add_loan(datetime(YEAR - 1, 12, 1) + timedelta(seconds=rng.randint(0, 30 * 86400)), in_files=False)
    for _ in range(6000):
        add_loan(year_start + timedelta(seconds=rng.randint(0, seconds - 1)), in_files=True)
    events.sort(key=lambda e: (e[2], e[0], e[1]))
    fines.sort(key=lambda f: (f[3], f[0]))

    def write(name: str, header: list[str], rows) -> None:
        with (out / name).open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(header)
            w.writerows(rows)

    write("branches.csv", ["branch_code", "branch_name", "region"], BRANCHES)
    write("items.csv", ["item_id", "title", "category", "home_branch", "replacement_cost"],
          [(i, t, c, b, _money(cost)) for i, t, c, b, cost in items])
    write("patrons.csv", ["patron_id", "home_branch", "joined_year"], patrons)
    h1 = [e for e in events if e[2] < H2_START]
    h2 = [e for e in events if e[2] >= OVERLAP_START]
    header = ["loan_id", "event", "event_time", "branch_code", "item_id", "patron_id"]
    write("loans_2025_h1.csv", header, [(a, b, _stamp(t), c, d, e) for a, b, t, c, d, e in h1])
    write("loans_2025_h2.csv", header, [(a, b, _stamp(t), c, d, e) for a, b, t, c, d, e in h2])
    write("fines.csv", ["fine_id", "loan_id", "branch_code", "assessed_time", "amount"],
          [(f, l, b, _stamp(t), f"{a:.2f}") for f, l, b, t, a in fines])
    return {"events": len(events), "h1": len(h1), "h2": len(h2), "fines": len(fines)}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "raw")
    args = ap.parse_args(argv)
    print(generate(args.out))


if __name__ == "__main__":
    main()
