"""Grade a P4 candidate's published marts against the P4 answer key, one check at a time.

    python -m pipetask.p4grade --repo REPO --key P4/key/answer_key.json

The candidate names its own tables and columns through oracle_map.yml (read by pipetask.oracle, as for
P1 to P3), so each check reads the rows an entry returns and finds the columns by their values: the key
column is the one whose values are branch codes, item ids or months, and each numeric column is tried
as the measure. A check passes when some reading matches the key exactly (money to the cent, counts
exact). When none does, the answer is compared with the wrong answer each single trap produces, so a
failure names its trap when it can (docs/plans/tasks/P4-holdout-library-loans.md, traps).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

from . import oracle
from .grade import _verdict, integer, key_columns, money, numeric_columns, year_month


def branch_code_fn(branches: dict[str, str]):
    """A normalizer for a branch: its code ('07', 7, '7') or its name."""
    by_name = {name.strip().lower(): code for code, name in branches.items()}

    def branch(v):
        if v is None or isinstance(v, bool):
            return None
        s = str(v).strip()
        if re.fullmatch(r"\d{1,2}", s) and s.zfill(2) in branches:
            return s.zfill(2)
        return by_name.get(s.lower())
    return branch


def item_id(v) -> str | None:
    """An item id: 'I000855', or its number 855."""
    if v is None or isinstance(v, bool):
        return None
    s = str(v).strip().upper()
    if re.fullmatch(r"I\d{6}", s):
        return s
    if re.fullmatch(r"\d{1,6}", s):
        return f"I{int(s):06d}"
    return None


def _sum_by(res: oracle.Result, k: int, key_fn, v: int, fmt):
    out: dict = {}
    for row in res.rows:
        key = key_fn(row[k])
        if key is None or row[v] is None:
            return None
        out[key] = out.get(key, Decimal(0)) + Decimal(str(row[v]))
    return {key: fmt(x) for key, x in sorted(out.items())}


def _count_by_key(res: oracle.Result, key_fn, key: dict, what: str, fmt=integer) -> dict:
    """Checks 1 and 6: a count per branch, either as (branch, count) rows or as one row per counted thing."""
    cands = []
    for k in key_columns(res, key_fn):
        for v in numeric_columns(res, exclude={k}):
            ans = _sum_by(res, k, key_fn, v, lambda x: fmt(x))
            if ans is not None:
                cands.append((f"{res.columns[k]} -> {res.columns[v]}", ans))
        per: dict[str, int] = {}
        for row in res.rows:
            b = key_fn(row[k])
            if b is not None:
                per[b] = per.get(b, 0) + 1
        cands.append((f"{res.columns[k]} -> row count", dict(sorted(per.items()))))
    return _verdict(cands, key) if cands else {"pass": False, "error": f"no {what} column found"}


def check2(res: oracle.Result, key: dict, top: int) -> dict:
    """The top items by checkouts, ranked from the candidate's own rows: ties in item id order."""
    cands = []
    for k in key_columns(res, item_id):
        for v in numeric_columns(res, exclude={k}):
            counts: dict[str, int] = {}
            ok = True
            for row in res.rows:
                i, n = item_id(row[k]), integer(row[v])
                if i is None or n is None:
                    ok = False
                    break
                counts[i] = counts.get(i, 0) + n
            if ok and counts:
                ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
                cands.append((f"{res.columns[k]} -> {res.columns[v]}", [[i, n] for i, n in ranked]))
    return _verdict(cands, key) if cands else {"pass": False, "error": "no item column and count column found"}


def scalar(res: oracle.Result, key: dict, fmt) -> dict:
    """Checks 3 and 7: one number in one row, or (check 3) the row count of a table of the counted loans."""
    cands = []
    if len(res.rows) == 1:
        for i in numeric_columns(res):
            n = fmt(res.rows[0][i])
            if n is not None:
                cands.append((res.columns[i], n))
    if fmt is integer:
        cands.append(("row count", len(res.rows)))
    return _verdict(cands, key) if cands else {"pass": False, "error": "no single numeric value found"}


def check4(res: oracle.Result, key: dict, branch_fn) -> dict:
    want = key["answer"]
    months = key_columns(res, year_month)
    branches = key_columns(res, branch_fn, 0.5)
    cands = []
    b = (branches[:1] or [None])[0]
    for m in months[:1]:
        for v in numeric_columns(res, exclude={m, b}):
            total, by_branch = Decimal(0), {}
            for r in res.rows:
                if year_month(r[m]) != want["month"] or r[v] is None:
                    continue
                amount = Decimal(str(r[v]))
                total += amount
                code = branch_fn(r[b]) if b is not None else None
                by_branch[code or "unknown"] = by_branch.get(code or "unknown", Decimal(0)) + amount
            cands.append((f"month {res.columns[m]}, branch {res.columns[b] if b is not None else '-'} -> {res.columns[v]}",
                          {"month": want["month"], "total": money(total),
                           "branches": {k: money(x) for k, x in sorted(by_branch.items())}}))
    if not months:  # one row per branch for the month, with no month column
        for k in key_columns(res, branch_fn):
            for v in numeric_columns(res, exclude={k}):
                ans = _sum_by(res, k, branch_fn, v, money)
                if ans is not None:
                    total = sum((Decimal(x) for x in ans.values()), Decimal(0))
                    cands.append((f"{res.columns[k]} -> {res.columns[v]} (no month column)",
                                  {"month": want["month"], "total": money(total), "branches": ans}))
    return _verdict(cands, key) if cands else {"pass": False, "error": "no month, branch and money column found"}


def check5(res: oracle.Result, key: dict) -> dict:
    cands = []
    for m in key_columns(res, year_month):
        for v in numeric_columns(res, exclude={m}):
            ans = _sum_by(res, m, year_month, v, money)
            if ans is not None:
                cands.append((f"{res.columns[m]} -> {res.columns[v]}", ans))
    return _verdict(cands, key) if cands else {"pass": False, "error": "no month column and money column found"}


def grade(repo: Path, key: dict) -> dict:
    checks = key["checks"]
    branch_fn = branch_code_fn(key["branches"])
    out: dict[str, dict] = {}
    try:
        entries = oracle.load_map(repo)
        con = oracle.connect(repo)
    except oracle.MapError as exc:
        return {"checks": {n: {"pass": False, "error": str(exc)} for n in oracle.CHECKS}, "passed": 0,
                "total": len(oracle.CHECKS)}
    for n in oracle.CHECKS:
        if n not in entries:
            out[n] = {"pass": False, "error": f"oracle_map.yml has no entry for check {n}"}
            continue
        try:
            res = oracle.resolve(entries[n], con)
        except oracle.MapError as exc:
            out[n] = {"pass": False, "error": str(exc)}
            continue
        if n == "1":
            out[n] = _count_by_key(res, branch_fn, checks[n], "branch")
        elif n == "2":
            out[n] = check2(res, checks[n], len(checks[n]["answer"]))
        elif n == "3":
            out[n] = scalar(res, checks[n], integer)
        elif n == "4":
            out[n] = check4(res, checks[n], branch_fn)
        elif n == "5":
            out[n] = check5(res, checks[n])
        elif n == "6":
            out[n] = _count_by_key(res, branch_fn, checks[n], "branch")
        else:
            out[n] = scalar(res, checks[n], money)
        out[n]["source"] = res.source
    return {"checks": out, "passed": sum(c["pass"] for c in out.values()), "total": len(out)}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Grade a P4 candidate's published marts against the P4 answer key.")
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--key", type=Path, required=True)
    args = ap.parse_args(argv)
    json.dump(grade(args.repo, json.loads(args.key.read_text(encoding="utf-8"))), sys.stdout, indent=1,
              sort_keys=True, default=str)
    print()


if __name__ == "__main__":
    main()
