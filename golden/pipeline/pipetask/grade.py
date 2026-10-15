"""Grade a candidate's published marts against the answer key, one check at a time.

    python -m pipetask.grade --repo REPO --key key/answer_key.json

The candidate names its own tables and columns (through oracle_map.yml), so each check reads the rows
an entry returns and finds the columns by their values: the key column is the one whose values are
agencies, county codes, wikis or window starts; each numeric column is tried as the measure. A check
passes when some reading matches the key exactly (money to the cent, counts exact). When none does, the
candidate's answer is compared with the wrong answer each single trap produces, so a failure names its
trap when it can (docs/tasks/pipeline-traps.md#mapping-for-the-audit).
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

from . import oracle

CENTS = Decimal("0.01")
# USPS code -> state FIPS, for states, DC and the territories USAspending uses.
USPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10", "DC": "11",
    "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21",
    "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29", "MT": "30",
    "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49",
    "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56", "AS": "60", "FM": "64", "GU": "66",
    "MH": "68", "MP": "69", "PW": "70", "PR": "72", "UM": "74", "VI": "78",
}
STATE_NAMES = {
    "alabama": "01", "alaska": "02", "arizona": "04", "arkansas": "05", "california": "06", "colorado": "08",
    "connecticut": "09", "delaware": "10", "district of columbia": "11", "florida": "12", "georgia": "13",
    "hawaii": "15", "idaho": "16", "illinois": "17", "indiana": "18", "iowa": "19", "kansas": "20",
    "kentucky": "21", "louisiana": "22", "maine": "23", "maryland": "24", "massachusetts": "25",
    "michigan": "26", "minnesota": "27", "mississippi": "28", "missouri": "29", "montana": "30",
    "nebraska": "31", "nevada": "32", "new hampshire": "33", "new jersey": "34", "new mexico": "35",
    "new york": "36", "north carolina": "37", "north dakota": "38", "ohio": "39", "oklahoma": "40",
    "oregon": "41", "pennsylvania": "42", "rhode island": "44", "south carolina": "45", "south dakota": "46",
    "tennessee": "47", "texas": "48", "utah": "49", "vermont": "50", "virginia": "51", "washington": "53",
    "west virginia": "54", "wisconsin": "55", "wyoming": "56", "american samoa": "60",
    "federated states of micronesia": "64", "guam": "66", "marshall islands": "68",
    "northern mariana islands": "69", "palau": "70", "puerto rico": "72", "virgin islands of the u.s.": "78",
    "u.s. virgin islands": "78",
}
FIPS_STATES = set(USPS.values())


# ------------------------------------------------------------------------------ value normalizers


def money(v) -> str | None:
    if v is None or isinstance(v, bool):
        return None
    try:
        return str(Decimal(str(v)).quantize(CENTS, rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError):
        return None


def integer(v) -> int | None:
    if v is None or isinstance(v, bool):
        return None
    try:
        d = Decimal(str(v))
    except (InvalidOperation, ValueError):
        return None
    return int(d) if d == d.to_integral_value() else None


def is_number(v) -> bool:
    return isinstance(v, (int, float, Decimal)) and not isinstance(v, bool)


def county_fips(v) -> str | None:
    if v is None or isinstance(v, bool):
        return None
    s = str(v).strip()
    if isinstance(v, (int, Decimal)) or re.fullmatch(r"\d{4,5}", s):
        s = s.zfill(5)
    return s if re.fullmatch(r"\d{5}", s) and s[:2] in FIPS_STATES and s[2:] not in ("000", "999") else None


def state_fips(v) -> str | None:
    if v is None or isinstance(v, bool):
        return None
    s = str(v).strip()
    if re.fullmatch(r"\d{1,2}", s) and s.zfill(2) in FIPS_STATES:
        return s.zfill(2)
    return USPS.get(s.upper()) or STATE_NAMES.get(s.lower())


def year_month(v) -> str | None:
    """A month as 'YYYY-MM' from a date, a timestamp, 'YYYY-MM[-DD...]' or the integer YYYYMM."""
    if isinstance(v, (date, datetime)):
        return f"{v.year:04d}-{v.month:02d}"
    if isinstance(v, int) and not isinstance(v, bool):
        s = str(v) if 190001 <= v <= 210012 else ""
        return f"{s[:4]}-{s[4:]}" if s and 1 <= int(s[4:]) <= 12 else None
    m = re.fullmatch(r"(\d{4})-(\d{2})(?:-\d{2}.*)?", str(v).strip()) if isinstance(v, str) else None
    return f"{m.group(1)}-{m.group(2)}" if m and 1 <= int(m.group(2)) <= 12 else None


def epoch(v) -> int | None:
    """Unix seconds from a timestamp (naive means UTC), an ISO string, or Unix seconds or milliseconds."""
    if isinstance(v, datetime):
        dt = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    if is_number(v):
        n = int(v)
        if n >= 10**11:
            return n // 1000
        return n if n >= 10**9 else None
    if isinstance(v, str):
        try:
            return epoch(datetime.fromisoformat(v.strip().replace("Z", "+00:00")))
        except ValueError:
            return None
    return None


def actor(v) -> str | None:
    if isinstance(v, bool):
        return "bot" if v else "human"
    s = str(v).strip().lower() if v is not None else ""
    if s in ("bot", "bots", "true", "1", "t"):
        return "bot"
    if s in ("human", "humans", "user", "users", "false", "0", "f", "person"):
        return "human"
    return None


def _column(res: oracle.Result, i: int) -> list:
    return [r[i] for r in res.rows]


def key_columns(res: oracle.Result, normalize, min_share: float = 0.8) -> list[int]:
    """Columns whose non-null values mostly normalize; best first."""
    scored = []
    for i in range(len(res.columns)):
        values = [v for v in _column(res, i) if v is not None]
        if not values:
            continue
        share = sum(normalize(v) is not None for v in values) / len(values)
        if share >= min_share:
            scored.append((-share, i))
    return [i for _, i in sorted(scored)]


def numeric_columns(res: oracle.Result, exclude=()) -> list[int]:
    cols = [i for i in range(len(res.columns)) if i not in exclude
            and any(is_number(v) for v in _column(res, i))
            and all(v is None or is_number(v) for v in _column(res, i))]
    hinted = [i for i in cols if res.columns[i].lower() in res.hints]
    return hinted + [i for i in cols if i not in hinted]


# ----------------------------------------------------------------------------------- the checks


def _accepted(key: dict) -> dict:
    """The accepted answers, the primary reading first."""
    accepted = dict(key.get("accepted") or {})
    return {"primary": key["answer"], **{k: v for k, v in accepted.items() if k != "primary"}}


def _verdict(candidates: list[tuple[str, object]], key: dict) -> dict:
    """candidates: (reading, normalized answer). Pass if one equals an accepted answer."""
    accepted = _accepted(key)
    for reading, answer in candidates:
        for name, value in accepted.items():
            if answer == value:
                return {"pass": True, "reading": reading, "interpretation": name}
    for reading, answer in candidates:
        traps = [t for t, value in key.get("traps", {}).items() if answer == value]
        if traps:
            return {"pass": False, "reading": reading, "traps": traps, "got": _short(answer)}
    got = _short(candidates[0][1]) if candidates else None
    return {"pass": False, "traps": [], "unexplained": True, "got": got, "expected": _short(key["answer"])}


def _short(x, limit: int = 400) -> str:
    text = json.dumps(x, sort_keys=True, default=str)
    return text if len(text) <= limit else text[:limit] + "..."


def _sum_by(res, key_fns: list[tuple[int, object]], value_col: int, fmt=money):
    out: dict = {}
    for row in res.rows:
        keys = tuple(fn(row[i]) for i, fn in key_fns)
        if any(k is None for k in keys) or row[value_col] is None:
            return None
        k = keys if len(keys) > 1 else keys[0]
        out[k] = out.get(k, Decimal(0)) + Decimal(str(row[value_col]))
    return {k: fmt(v) for k, v in out.items()}


def check1(res, key, agencies: dict[str, str]) -> dict:
    by_name = {name.strip().lower(): code for code, name in agencies.items()}

    def agency(v):
        s = str(v).strip() if v is not None else ""
        return s.zfill(3) if s.zfill(3) in agencies else by_name.get(s.lower())

    cands = []
    for k in key_columns(res, agency):
        for v in numeric_columns(res, exclude={k}):
            ans = _sum_by(res, [(k, agency)], v)
            if ans is not None:
                cands.append((f"{res.columns[k]} -> {res.columns[v]}", ans))
    return _verdict(cands, key) if cands else {"pass": False, "error": "no agency column and money column found"}


def check2(res, key, top: int = 10) -> dict:
    cands = []
    for k in key_columns(res, county_fips):
        for v in numeric_columns(res, exclude={k}):
            per: dict[str, str] = {}
            consistent = True
            for row in res.rows:
                f, x = county_fips(row[k]), money(row[v])
                if f is None or x is None:
                    continue
                if per.get(f, x) != x:
                    consistent = False
                    break
                per[f] = x
            if consistent and per:
                ranked = sorted(per.items(), key=lambda kv: (-Decimal(kv[1]), kv[0]))[:top]
                cands.append((f"{res.columns[k]} -> {res.columns[v]}", [[f, x] for f, x in ranked]))
    return _verdict(cands, key) if cands else {"pass": False, "error": "no county column and per-person column found"}


def scalar_check(res, key) -> dict:
    """Checks 3 and 7: one number, or the row count of a table of the counted things."""
    cands = []
    if len(res.rows) == 1:
        for i in numeric_columns(res):
            n = integer(res.rows[0][i])
            if n is not None:
                cands.append((res.columns[i], n))
    cands.append(("row count", len(res.rows)))
    return _verdict(cands, key)


def check4(res, key) -> dict:
    want = key["answer"]
    months = key_columns(res, year_month)
    counties = key_columns(res, lambda v: county_fips(v) or (None if v is not None else "unknown"), 0.5)
    states = key_columns(res, state_fips, 0.5)
    if not months:
        return {"pass": False, "error": "no month column found"}
    cands = []
    county_col, state_col = (counties[:1] or [None])[0], (states[:1] or [None])[0]
    for m, v in itertools.product(months[:1], numeric_columns(res, exclude={months[0], county_col, state_col})):
        rows = [r for r in res.rows if year_month(r[m]) == want["month"]]
        for c, s in [(county_col, state_col)]:
            total, by_state, by_county = Decimal(0), {}, {}
            for r in rows:
                if r[v] is None:
                    continue
                amount = Decimal(str(r[v]))
                cf = county_fips(r[c]) if c is not None else None
                sf = state_fips(r[s]) if s is not None else (cf[:2] if cf else None)
                total += amount
                by_state[sf or "unknown"] = by_state.get(sf or "unknown", Decimal(0)) + amount
                if cf:
                    by_county[cf] = by_county.get(cf, Decimal(0)) + amount
            ans = {"month": want["month"], "total": money(total),
                   "states": {k: money(x) for k, x in sorted(by_state.items())},
                   "counties": {k: money(x) for k, x in sorted(by_county.items())}}
            reading = f"month {res.columns[m]}, state {res.columns[s] if s is not None else '-'}, " \
                      f"county {res.columns[c] if c is not None else '-'} -> {res.columns[v]}"
            cands.append((reading, ans))
    return _verdict(cands, key) if cands else {"pass": False, "error": "no money column found"}


def check5(res, key, wikis: dict[str, str]) -> dict:
    by_domain = {d: w for w, d in wikis.items()}

    def wiki(v):
        s = str(v).strip().lower() if v is not None else ""
        s = re.sub(r"^https?://", "", s).rstrip("/")
        return s if s in wikis else by_domain.get(s)

    cands = []
    for w in key_columns(res, wiki):
        for a in key_columns(res, actor):
            nums = numeric_columns(res, exclude={w, a})
            for e, b in itertools.permutations(nums, 2):
                out: dict[str, list[int]] = {}
                for r in res.rows:
                    k = f"{wiki(r[w])}|{actor(r[a])}"
                    row = out.setdefault(k, [0, 0])
                    row[0] += integer(r[e]) or 0
                    row[1] += integer(r[b]) or 0
                cands.append((f"{res.columns[w]}, {res.columns[a]} -> {res.columns[e]}, {res.columns[b]}",
                              dict(sorted(out.items()))))
    return _verdict(cands, key) if cands else {"pass": False, "error": "no wiki, actor and two count columns found"}


def check6(res, key, top: int = 5) -> dict:
    accepted = _accepted(key)
    wiki_cols = [i for i in range(len(res.columns))
                 if any(str(v).lower() in ("enwiki", "en.wikipedia.org") for v in _column(res, i))]
    rows = res.rows
    if wiki_cols:
        rows = [r for r in rows if str(r[wiki_cols[0]]).lower() in ("enwiki", "en.wikipedia.org")]
    sub = oracle.Result(res.columns, res.types, rows, res.hints, res.source)
    starts = [i for i in key_columns(sub, epoch) if i not in wiki_cols]
    readings = []
    for s in starts:
        for v in numeric_columns(sub, exclude={s} | set(wiki_cols)):
            for shift in (0, -300):  # a window labelled by its end
                got: dict[int, int] = {}
                for r in rows:
                    t, n = epoch(r[s]), integer(r[v])
                    if t is not None and n is not None:
                        got[t + shift] = got.get(t + shift, 0) + n
                readings.append((f"{res.columns[s]}{' (end)' if shift else ''} -> {res.columns[v]}", got))
    if not readings:
        return {"pass": False, "error": "no window start column and edit count column found"}

    def matches(got: dict[int, int], answer: dict) -> bool:
        windows = {int(k): v for k, v in answer["windows"].items()}
        mine = sorted(got.values(), reverse=True)[:top]
        return bool(got) and mine == [n for _, n in answer["top"]] and all(windows.get(t) == n for t, n in got.items())

    for reading, got in readings:
        for name, answer in accepted.items():
            if matches(got, answer):
                return {"pass": True, "reading": reading, "interpretation": name}
    for reading, got in readings:
        traps = [t for t, answer in key.get("traps", {}).items() if matches(got, answer)]
        if traps:
            return {"pass": False, "reading": reading, "traps": traps}
    reading, got = readings[0]
    top_got = sorted(got.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
    return {"pass": False, "traps": [], "unexplained": True, "reading": reading,
            "got": _short(top_got), "expected": _short(key["answer"]["top"])}


def grade(repo: Path, key: dict) -> dict:
    batch, stream = key["batch"], key["stream"]
    keys = {**batch["checks"], **stream["checks"]}
    out: dict[str, dict] = {}
    try:
        entries = oracle.load_map(repo)
    except oracle.MapError as exc:
        return {"checks": {n: {"pass": False, "error": str(exc)} for n in oracle.CHECKS}, "passed": 0, "total": 7}
    con = oracle.connect(repo)
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
            out[n] = check1(res, keys[n], batch["agencies"])
        elif n == "2":
            out[n] = check2(res, keys[n])
        elif n in ("3", "7"):
            out[n] = scalar_check(res, keys[n])
        elif n == "4":
            out[n] = check4(res, keys[n])
        elif n == "5":
            out[n] = check5(res, keys[n], stream["wikis"])
        else:
            out[n] = check6(res, keys[n])
        out[n]["source"] = res.source
    return {"checks": out, "passed": sum(c["pass"] for c in out.values()), "total": len(out)}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Grade published marts against the answer key.")
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--key", type=Path, required=True)
    args = ap.parse_args(argv)
    result = grade(args.repo, json.loads(args.key.read_text(encoding="utf-8")))
    json.dump(result, sys.stdout, indent=1, sort_keys=True, default=str)
    print()


if __name__ == "__main__":
    main()
