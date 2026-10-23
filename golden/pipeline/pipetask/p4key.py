"""The P4 answer key: the expected answer of each check, and the wrong answer each single trap produces.

    python -m pipetask.p4key --raw P4/data/raw --out P4/key/answer_key.json

Plain Python over the CSV files (the csv module and Decimal), independent of the P4 reference, which
is DuckDB SQL. The reference must agree with this key; that agreement is the evidence the key is right.

Interpretations the key fixes (the spec states each as a rule):
- A loan event is one row of a loans file. The same event in both files (loan_id, event, event_time
  equal) is one event. Trap D1 keeps both copies (D1-rows: one late loan per duplicate checkout row).
- A loan is checked out in 2025 when its checkout event is in the files. A return or renewal whose
  checkout is in no file belongs to a loan from before the year.
- Late: the return is after the due time, which is the checkout plus 21 days for the loan and 21 days
  for each renewal before the return. Trap D3 ignores renewals.
- Fines are summed exactly, waivers (negative rows) included. Trap D2 drops the negative rows.
- Branch codes are text with their leading zeros.
- On loan at the end of the year: an item whose last event of the year is a checkout or a renewal.
  Trap D4 reads each loans file on its own, so a loan returned in the second file counts as open.
- Trap D6 reads a replacement cost up to its thousands separator ('$1,234.50' as 1). Trap D7 takes a
  loan's first event in the files for its checkout (check 3) and counts a patron active on any event
  (check 6; the data does not reproduce it: every patron with an event has a checkout). Trap D8 keeps
  only the months of 2025 (check 5), and loses the January 2026 waiver.
D5 (codes as integers) shows only as a lost join, since the grader reads `7` as `07`, and D9 in the
idempotence check; neither has a wrong answer here.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

LOAN_DAYS = 21
CHECK4_MONTH = "2025-03"
TOP_ITEMS = 10
CENTS = Decimal("0.01")
LOAN_FILES = ("loans_2025_h1.csv", "loans_2025_h2.csv")


def cents(x) -> str:
    return str(Decimal(x).quantize(CENTS, rounding=ROUND_HALF_UP))


def digest(answer) -> str:
    return hashlib.sha256(json.dumps(answer, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def money_text(text: str) -> Decimal:
    """'$1,234.50' or '18.00' as a Decimal."""
    return Decimal(text.strip().replace("$", "").replace(",", ""))


def money_text_truncated(text: str) -> Decimal:
    """Trap D6: the text read up to its first comma ('$1,234.50' as 1)."""
    return Decimal(text.strip().replace("$", "").split(",")[0])


def _time(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")


def _rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load(raw: Path) -> dict:
    files = {name: _rows(raw / name) for name in LOAN_FILES}
    all_events = [e for name in LOAN_FILES for e in files[name]]
    seen, events = set(), []
    for e in all_events:
        k = (e["loan_id"], e["event"], e["event_time"])
        if k not in seen:
            seen.add(k)
            events.append(e)
    return {"branches": _rows(raw / "branches.csv"), "items": _rows(raw / "items.csv"),
            "patrons": _rows(raw / "patrons.csv"), "fines": _rows(raw / "fines.csv"),
            "events": events, "events_with_duplicates": all_events, "files": files}


# --- the answers ---------------------------------------------------------------------------------------


def checkouts_per_branch(events) -> dict[str, int]:
    out: dict[str, int] = {}
    for e in events:
        if e["event"] == "checkout":
            out[e["branch_code"]] = out.get(e["branch_code"], 0) + 1
    return dict(sorted(out.items()))


def top_items(events, top: int = TOP_ITEMS) -> list[list]:
    counts: dict[str, int] = {}
    for e in events:
        if e["event"] == "checkout":
            counts[e["item_id"]] = counts.get(e["item_id"], 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
    return [[item, n] for item, n in ranked]


def _loans(events) -> dict[str, list[dict]]:
    by_loan: dict[str, list[dict]] = {}
    for e in events:
        by_loan.setdefault(e["loan_id"], []).append(e)
    for rows in by_loan.values():
        rows.sort(key=lambda e: (e["event_time"], e["event"]))
    return by_loan


def late_returns(events, renewals_count: bool = True, per_row: bool = False, first_event_as_checkout: bool = False) -> int:
    """Late loans. `per_row` counts one late loan per checkout row, as a pipeline with one fact row per
    checkout row does when the rows hold duplicates (trap D1 in that form). `first_event_as_checkout`
    takes a loan's first event in the files for its checkout when it has none (trap D7)."""
    late = 0
    for rows in _loans(events).values():
        checkouts = [r for r in rows if r["event"] == "checkout"]
        ret = next((r for r in rows if r["event"] == "return"), None)
        if not checkouts and first_event_as_checkout and rows[0] is not ret:
            checkouts = rows[:1]
        if not checkouts or ret is None:
            continue
        renewals = sum(1 for r in rows if r["event"] == "renew" and checkouts[0]["event_time"] < r["event_time"]
                       < ret["event_time"]) if renewals_count else 0
        due = _time(checkouts[0]["event_time"]) + timedelta(days=LOAN_DAYS * (1 + renewals))
        if _time(ret["event_time"]) > due:
            late += len(checkouts) if per_row else 1
    return late


def fines_for_month(fines, month: str = CHECK4_MONTH, waivers: bool = True) -> dict:
    total, by_branch = Decimal(0), {}
    for f in fines:
        amount = Decimal(f["amount"])
        if f["assessed_time"][:7] != month or (not waivers and amount < 0):
            continue
        total += amount
        by_branch[f["branch_code"]] = by_branch.get(f["branch_code"], Decimal(0)) + amount
    return {"month": month, "total": cents(total), "branches": {k: cents(v) for k, v in sorted(by_branch.items())}}


def fines_per_month(fines, waivers: bool = True, year: str | None = None) -> dict[str, str]:
    """Net fines per month. `year` keeps that year's months only (trap D8)."""
    out: dict[str, Decimal] = {}
    for f in fines:
        amount = Decimal(f["amount"])
        if not waivers and amount < 0:
            continue
        month = f["assessed_time"][:7]
        if year and not month.startswith(year):
            continue
        out[month] = out.get(month, Decimal(0)) + amount
    return {k: cents(v) for k, v in sorted(out.items())}


def active_patrons_per_home_branch(events, patrons, any_event: bool = False) -> dict[str, int]:
    """Patrons with a checkout, by home branch. `any_event` counts a return or renewal too (trap D7)."""
    home = {p["patron_id"]: p["home_branch"] for p in patrons}
    active = {e["patron_id"] for e in events if any_event or e["event"] == "checkout"}
    out: dict[str, int] = {}
    for p in active:
        out[home[p]] = out.get(home[p], 0) + 1
    return dict(sorted(out.items()))


def open_items(events) -> set[str]:
    """Items whose last event of the year is a checkout or a renewal."""
    last: dict[str, dict] = {}
    for e in events:
        prev = last.get(e["item_id"])
        if prev is None or (e["event_time"], e["event"]) > (prev["event_time"], prev["event"]):
            last[e["item_id"]] = e
    return {item for item, e in last.items() if e["event"] in ("checkout", "renew")}


def replacement_value(items, item_ids: set[str], parse=money_text) -> str:
    cost = {i["item_id"]: parse(i["replacement_cost"]) for i in items}
    return cents(sum((cost[i] for i in item_ids), Decimal(0)))


def build_key(raw: Path) -> dict:
    d = load(raw)
    events, dupes, fines = d["events"], d["events_with_duplicates"], d["fines"]
    per_file_open = set().union(*(open_items(rows) for rows in d["files"].values()))
    answers = {
        "1": (checkouts_per_branch(events), {"D1": checkouts_per_branch(dupes)}),
        "2": (top_items(events), {"D1": top_items(dupes)}),
        "3": (late_returns(events), {"D1": late_returns(dupes), "D1-rows": late_returns(dupes, per_row=True),
                                     "D3": late_returns(events, renewals_count=False),
                                     "D7": late_returns(events, first_event_as_checkout=True)}),
        "4": (fines_for_month(fines), {"D2": fines_for_month(fines, waivers=False)}),
        "5": (fines_per_month(fines), {"D2": fines_per_month(fines, waivers=False),
                                       "D8": fines_per_month(fines, year="2025")}),
        "6": (active_patrons_per_home_branch(events, d["patrons"]),
              {"D7": active_patrons_per_home_branch(events, d["patrons"], any_event=True)}),
        "7": (replacement_value(d["items"], open_items(events)),
              {"D4": replacement_value(d["items"], per_file_open),
               "D6": replacement_value(d["items"], open_items(events), parse=money_text_truncated)}),
    }
    checks = {}
    for n, (answer, traps) in answers.items():
        reproduced = {t: v for t, v in traps.items() if v != answer}
        checks[n] = {"answer": answer, "sha256": digest(answer), "traps": reproduced,
                     "traps_not_reproduced": sorted(set(traps) - set(reproduced))}
    raw_sha = hashlib.sha256()
    for path in sorted(raw.iterdir()):
        raw_sha.update(path.name.encode() + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    return {"version": 1, "task": "P4", "inputs": {"raw_sha256": raw_sha.hexdigest(),
                                                   "files": sorted(p.name for p in raw.iterdir())},
            "branches": {b["branch_code"]: b["branch_name"] for b in d["branches"]},
            "check4_month": CHECK4_MONTH, "loan_days": LOAN_DAYS, "checks": checks}


def main(argv: list[str] | None = None) -> None:
    here = Path(__file__).resolve().parents[1] / "P4"
    ap = argparse.ArgumentParser(description="Compute the P4 answer key from the raw files.")
    ap.add_argument("--raw", type=Path, default=here / "data" / "raw")
    ap.add_argument("--out", type=Path, default=here / "key" / "answer_key.json")
    args = ap.parse_args(argv)
    key = build_key(args.raw)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(key, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print({n: c["answer"] if n in ("3", "7") else f"{len(c['answer'])} entries" for n, c in key["checks"].items()})
    print({n: sorted(c["traps"]) for n, c in key["checks"].items()})


if __name__ == "__main__":
    main()
