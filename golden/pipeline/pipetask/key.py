"""The answer key: the expected answer of each check, and the wrong answer each single trap produces.

    python -m pipetask.key --raw data/raw --capture data/capture/recentchange.jsonl.gz \
        --seed 1 --out key/answer_key.json

This is an implementation independent of the P1 reference (plain DuckDB SQL and Python, no dlt or dbt).
The reference must agree with it; that agreement is the evidence the key is right.

Interpretations the key fixes (the spec leaves them open; see golden/pipeline/README.md):
- A transaction is one CSV row; its money is `federal_action_obligation`, summed as DECIMAL(18,2).
- FY2024 is action dates 2023-10-01 to 2024-09-30. The place is the place of performance.
- Population: POPESTIMATE2024 of vintage 2024; for a county that vintage lacks, the latest earlier
  estimate (POPESTIMATE2021 of vintage 2021); none for territories, which then have no per-person value.
- Stream: an edit is an event of type `edit` or `new` whose meta.domain is not `canary`, counted once per
  meta.id. Net bytes are length.new - length.old (old absent: 0). Event time is `timestamp`; meta.dt is
  accepted as an alternative. An event is late when, at its first arrival, the largest event time seen
  before it is more than 600 s past the end of its 5-minute window.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import duckdb

from . import schedule as sched

CHECK4_MONTH = "2024-07"
TOP_COUNTIES = 10
TOP_WINDOWS = 5
CT = "09"
FY_START, FY_END = "2023-10-01", "2024-09-30"
CENTS = Decimal("0.01")


def cents(x) -> str:
    return str(Decimal(x).quantize(CENTS, rounding=ROUND_HALF_UP))


def digest(answer) -> str:
    return hashlib.sha256(json.dumps(answer, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# ----------------------------------------------------------------------------------------- batch


def _connect(raw: Path, workdir: Path) -> duckdb.DuckDBPyConnection:
    for z in sorted((raw / "usaspending").glob("*.zip")):
        with zipfile.ZipFile(z) as zf:
            zf.extractall(workdir)
    con = duckdb.connect()
    csv = "read_csv('{}', all_varchar=true, union_by_name=true)"
    a, c = (csv.format((workdir / f"*_{k}_*.csv").as_posix()) for k in ("Assistance", "Contracts"))
    con.execute(f"""
        create table tx as
        select assistance_transaction_unique_key as tx_key, assistance_award_unique_key as award_key,
               awarding_agency_code as agency_code, awarding_agency_name as agency_name,
               federal_action_obligation as amount_text, total_obligated_amount as award_total_text,
               action_date::date as action_date,
               prime_award_transaction_place_of_performance_state_fips_code as state_fips,
               prime_award_transaction_place_of_performance_county_fips_code as county_fips
        from {a}
        union all
        select contract_transaction_unique_key, contract_award_unique_key, awarding_agency_code,
               awarding_agency_name, federal_action_obligation, total_dollars_obligated,
               action_date::date, prime_award_transaction_place_of_performance_state_fips_code,
               prime_award_transaction_place_of_performance_county_fips_code
        from {c}
    """)
    pop = "read_csv('{}', all_varchar=true, encoding='latin-1')"
    for vintage in ("2024", "2021"):
        path = (raw / "census" / f"co-est{vintage}-alldata.csv").as_posix()
        con.execute(f"create table pop{vintage} as select * from {pop.format(path)} where SUMLEV = '050'")
    return con


def _population(con, *, column24="POPESTIMATE2024", column21="POPESTIMATE2021", fallback=True,
                first_file_only=False) -> str:
    """SQL for (fips, population) under one population rule."""
    if first_file_only:
        return f"select STATE || COUNTY as fips, {column21}::bigint as population from pop2021"
    base = f"select STATE || COUNTY as fips, {column24}::bigint as population from pop2024"
    if not fallback:
        return base
    return (base + f" union all select STATE || COUNTY, {column21}::bigint from pop2021 "
            "where STATE || COUNTY not in (select STATE || COUNTY from pop2024)")


def _facts(*, money="amount_text", drop_negative=False, calendar_year=False, drop_ct=False,
           drop_no_county=False, copies=1, numeric="decimal(18,2)") -> str:
    lo, hi = ("2024-01-01", "2024-12-31") if calendar_year else (FY_START, FY_END)
    where = [f"action_date between '{lo}' and '{hi}'"]
    if drop_negative:
        where.append(f"{money}::{numeric} >= 0")
    if drop_ct:
        where.append(f"coalesce(state_fips, '') <> '{CT}'")
    if drop_no_county:
        where.append("county_fips is not null")
    dup = " union all ".join(["select 1"] * copies)
    return (f"select tx.*, {money}::{numeric} as amount, strftime(action_date, '%Y-%m') as month "
            f"from tx, ({dup}) where {' and '.join(where)}")


def check1(con, **facts) -> dict:
    rows = con.execute(f"select agency_code, sum(amount) from ({_facts(**facts)}) group by 1 order by 1").fetchall()
    return {code: cents(total) for code, total in rows}


def check2(con, *, pop_sql: str | None = None, int_fips=False, **facts) -> list:
    pop_sql = pop_sql or _population(con)
    county = "ltrim(county_fips, '0')" if int_fips else "county_fips"
    rows = con.execute(f"""
        with f as ({_facts(**facts)}), c as (select {county} as fips, sum(amount) as net from f
                                             where county_fips is not null group by 1)
        select c.fips, c.net, p.population from c join ({pop_sql}) p on p.fips = c.fips
        where p.population > 0
    """).fetchall()
    ranked = sorted(((f, Decimal(net) / Decimal(pop)) for f, net, pop in rows), key=lambda r: (-r[1], r[0]))
    return [[f, cents(v)] for f, v in ranked[:TOP_COUNTIES]]


def check3(con, **facts) -> int:
    return con.execute(f"select count(*) from (select award_key from ({_facts(**facts)}) "
                       "group by 1 having sum(amount) < 0)").fetchone()[0]


def check4(con, **facts) -> dict:
    f = f"select * from ({_facts(**facts)}) where month = '{CHECK4_MONTH}'"
    total = con.execute(f"select sum(amount) from ({f})").fetchone()[0]
    states = con.execute(f"select coalesce(state_fips, 'unknown'), sum(amount) from ({f}) group by 1").fetchall()
    counties = con.execute(f"select county_fips, sum(amount) from ({f}) where county_fips is not null group by 1").fetchall()
    return {"month": CHECK4_MONTH, "total": cents(total),
            "states": {s: cents(v) for s, v in sorted(states)},
            "counties": {c: cents(v) for c, v in sorted(counties)}}


def batch_key(raw: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        con = _connect(raw, Path(tmp))
        names = dict(con.execute("select distinct agency_code, agency_name from tx").fetchall())
        award_total = {"money": "award_total_text"}
        float_money = {"numeric": "double"}
        checks = {
            "1": (check1(con), {"B1": check1(con, **award_total), "B2": check1(con, drop_negative=True),
                                "B6": check1(con, calendar_year=True), "B7": check1(con, copies=2),
                                "B8": check1(con, **float_money)}),
            "2": (check2(con), {"B3": check2(con, int_fips=True), "B4": check2(con, drop_ct=True),
                                "B4-no-fallback": check2(con, pop_sql=_population(con, fallback=False)),
                                "B6": check2(con, calendar_year=True), "B7": check2(con, copies=2),
                                "S1": check2(con, pop_sql=_population(con, column24="ESTIMATESBASE2020",
                                                                      column21="ESTIMATESBASE2020")),
                                "S1-first-file": check2(con, pop_sql=_population(con, first_file_only=True))}),
            "3": (check3(con), {"B2": check3(con, drop_negative=True), "B6": check3(con, calendar_year=True)}),
            "4": (check4(con), {"B4": check4(con, drop_ct=True), "B5": check4(con, drop_no_county=True),
                                "B7": check4(con, copies=2), "B8": check4(con, **float_money)}),
        }
        facts = {
            "transactions": con.execute("select count(*) from tx").fetchone()[0],
            "awards": con.execute("select count(distinct award_key) from tx").fetchone()[0],
            "negative_transactions": con.execute("select count(*) from tx where amount_text::decimal(18,2) < 0").fetchone()[0],
            "no_county_transactions": con.execute("select count(*) from tx where county_fips is null").fetchone()[0],
            "no_state_transactions": con.execute("select count(*) from tx where state_fips is null").fetchone()[0],
            "ct_county_codes": [r[0] for r in con.execute(
                "select distinct county_fips from tx where state_fips = '09' and county_fips is not null order by 1").fetchall()],
            "counties_without_2024_estimate": [r[0] for r in con.execute(
                "select distinct county_fips from tx where county_fips is not null and county_fips not in "
                "(select STATE || COUNTY from pop2024) order by 1").fetchall()],
        }
    return {"agencies": names, "facts": facts, "checks": _with_traps(checks)}


def _with_traps(checks: dict) -> dict:
    out = {}
    for num, (answer, traps) in checks.items():
        distinct = {t: a for t, a in traps.items() if a != answer}
        out[num] = {"answer": answer, "sha256": digest(answer), "traps": distinct,
                    "traps_not_reproduced": sorted(t for t, a in traps.items() if a == answer)}
    return out


# ---------------------------------------------------------------------------------------- stream


def _event_time(ev: dict, basis: str) -> int:
    if basis == "timestamp" and "timestamp" in ev:
        return int(ev["timestamp"])
    # meta.dt basis, and canary events, which carry only `meta`
    return int(datetime.fromisoformat(ev["meta"]["dt"].replace("Z", "+00:00")).timestamp())


def _arrivals(plan: sched.Schedule, *, stop_at_invalid=False, count_resends=False) -> list[dict]:
    """Events in first-arrival order (or every delivery, with count_resends), invalid frames skipped."""
    seen, out = set(), []
    deliveries = list(range(len(plan.positions)))
    if count_resends:
        for p in plan.disconnects:  # each fires once; the client resumes and gets these again
            start = plan.resume_position(plan.sse_id(p))
            deliveries += list(range(start, p + 1))
    for pos in deliveries:
        if stop_at_invalid and pos >= plan.invalid_at:
            continue
        ev = sched.event(plan.positions[pos]) if plan.positions[pos].frame is not None else None
        if ev is None:
            continue
        mid = ev["meta"]["id"]
        if mid in seen and not count_resends:
            continue
        seen.add(mid)
        out.append(ev)
    return out


def _stream_answers(events: list[dict], *, basis="timestamp", canary=False, all_types=False,
                    name_bots=False, new_length=False, late_in_windows=False) -> dict:
    per_wiki: dict[str, list[int]] = {}
    per_wiki_on_time: dict[str, list[int]] = {}
    windows: dict[int, int] = {}
    late_edits = late_all = 0
    watermark = 0
    for ev in events:
        is_canary = (ev.get("meta") or {}).get("domain") == "canary"
        if is_canary and not canary:
            continue
        t = _event_time(ev, basis)
        window = t - t % sched.WINDOW_SECONDS
        late = watermark > window + sched.WINDOW_SECONDS + sched.LATE_AFTER_SECONDS
        watermark = max(watermark, t)
        is_edit = all_types or ev.get("type") in sched.EDIT_TYPES or is_canary  # W1 counts canaries
        late_all += late
        if not is_edit:
            continue
        late_edits += late
        bot = ev.get("user", "").lower().endswith("bot") if name_bots else bool(ev.get("bot"))
        length = ev.get("length") or {}
        delta = (length.get("new") or 0) - (0 if new_length else (length.get("old") or 0))
        key = f"{ev.get('wiki')}|{'bot' if bot else 'human'}"
        for table, include in ((per_wiki, True), (per_wiki_on_time, not late)):
            if include:
                row = table.setdefault(key, [0, 0])
                row[0] += 1
                row[1] += delta
        if ev.get("wiki") == "enwiki" and (late_in_windows or not late):
            windows[window] = windows.get(window, 0) + 1
    top = sorted(windows.items(), key=lambda kv: (-kv[1], kv[0]))[:TOP_WINDOWS]
    if late_in_windows:  # S3, F4: the late events went into their windows, none into late_events
        late_edits = late_all = 0
    return {"5": dict(sorted(per_wiki.items())), "5-on-time": dict(sorted(per_wiki_on_time.items())),
            "6": {"windows": {str(k): v for k, v in sorted(windows.items())}, "top": [[k, v] for k, v in top]},
            "7": late_edits, "7-all-types": late_all}


def stream_key(capture: Path, seed: int) -> dict:
    plan = sched.build(sched.load_capture(capture), seed)
    events = _arrivals(plan)
    main = _stream_answers(events)
    alt = _stream_answers(events, basis="meta_dt")
    variants = {
        "W1": _stream_answers(events, canary=True), "W2": _stream_answers(events, all_types=True),
        "W4": _stream_answers(events, name_bots=True), "W5": _stream_answers(events, new_length=True),
        "S3": _stream_answers(events, late_in_windows=True),
        "F2": _stream_answers(_arrivals(plan, count_resends=True)),
        "F5": _stream_answers(_arrivals(plan, stop_at_invalid=True)),
    }
    variants["F4"] = variants["S3"]

    def check(num: str, accepted: dict[str, object]) -> dict:
        answer = accepted["primary"]
        traps = {t: v[num] for t, v in variants.items() if v[num] != answer and v[num] not in accepted.values()}
        same = sorted(t for t, v in variants.items() if v[num] == answer)
        return {"answer": answer, "sha256": digest(answer), "accepted": accepted, "traps": traps,
                "traps_not_reproduced": same}

    wikis = {}
    for ev in events:
        wikis.setdefault(ev.get("wiki"), (ev.get("meta") or {}).get("domain"))
    return {
        "seed": seed,
        "schedule": {"positions": len(plan.positions), "disconnects": plan.disconnects,
                     "late_window_start": plan.late_window_start, "late_insert_at": plan.late_insert_at,
                     "late_batch_size": len(plan.late_batch), "invalid_at": plan.invalid_at},
        "wikis": dict(sorted((k, v) for k, v in wikis.items() if k)),
        "checks": {
            "5": check("5", {"primary": main["5"], "excluding-late": main["5-on-time"],
                             "meta-dt": alt["5"], "meta-dt-excluding-late": alt["5-on-time"]}),
            "6": check("6", {"primary": main["6"], "meta-dt": alt["6"]}),
            "7": check("7", {"primary": main["7"], "all-types": main["7-all-types"],
                             "meta-dt": alt["7"], "meta-dt-all-types": alt["7-all-types"]}),
        },
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_key(raw: Path, capture: Path, seed: int) -> dict:
    raw_files = {p.relative_to(raw).as_posix(): _sha256(p) for p in sorted(raw.rglob("*")) if p.is_file()}
    inputs = {"raw_sha256": digest(raw_files), "capture_sha256": _sha256(capture)}
    return {"version": 1, "inputs": inputs, "batch": batch_key(raw), "stream": stream_key(capture, seed)}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Compute the pipeline answer key.")
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--capture", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    key = build_key(args.raw, args.capture, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(key, indent=1, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
