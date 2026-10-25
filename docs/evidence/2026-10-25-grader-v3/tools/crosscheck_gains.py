"""Independent check of every point grader v3 gains: hand-written DuckDB SQL over the same published marts
(no pipetask code), compared with the answer key's primary answer. A gain is correct data found only if this
reproduces the key exactly.   python -I crosscheck_gains.py W3DIR KEY"""
import json, sys
from decimal import Decimal, ROUND_HALF_UP
import duckdb

W, KEY = sys.argv[1], json.load(open(sys.argv[2]))
ANS = {**{n: c["answer"] for n, c in KEY["batch"]["checks"].items()},
       **{n: c["answer"] for n, c in KEY["stream"]["checks"].items()}}
C = Decimal("0.01")
cents = lambda x: str(Decimal(str(x)).quantize(C, rounding=ROUND_HALF_UP))
def m(run, mart): return f"read_parquet('{W}/{run}/g/repo/out/marts/{mart}/**/*.parquet', union_by_name=true)"

def c2(run, mart, county, money, pop, where="true"):
    rows = duckdb.sql(f"select {county}, sum({money}), min({pop}), max({pop}) from {m(run, mart)} where {where} "
                      f"group by 1").fetchall()
    assert all(lo == hi for _, _, lo, hi in rows)
    ranked = sorted(((f, Decimal(str(s)) / Decimal(lo)) for f, s, lo, _ in rows if lo), key=lambda r: (-r[1], r[0]))
    return [[f, cents(v)] for f, v in ranked[:10]]

def c4(run, mart, month, state, county, money):
    want = ANS["4"]
    rows = duckdb.sql(f"select {state}, {county}, {money} from {m(run, mart)} "
                      f"where strftime({month}::date, '%Y-%m') = '{want['month']}'").fetchall()
    total, st, co = Decimal(0), {}, {}
    for s, c, v in rows:
        v = Decimal(str(v)); total += v
        s = s if (s and len(s) == 2 and s.isdigit() and s != "00") else "unknown"
        st[s] = st.get(s, Decimal(0)) + v
        if c and len(c) == 5 and c.isdigit() and not c.endswith(("000", "999")):
            co[c] = co.get(c, Decimal(0)) + v
    return {"month": want["month"], "total": cents(total), "states": {k: cents(v) for k, v in sorted(st.items())},
            "counties": {k: cents(v) for k, v in sorted(co.items())}}

def scalar(sql): return duckdb.sql(sql).fetchone()[0]

GAINS = [
 ("20261024-P1-cadence-haiku-core-4", "3", lambda r: scalar(f"select count(*) from {m(r,'mart_award_net_fy2024')} where net_obligations < 0")),
 ("20261024-P1-cadence-haiku-core-5", "2", lambda r: c2(r, "mart_awards_monthly", "county_fips", "net_obligations_usd", "population")),
 ("20261024-P1-cadence-haiku-core-5", "3", lambda r: scalar(f"select count(*) from {m(r,'mart_awards_fy2024')} where is_net_negative")),
 ("20261024-P1-cadence-haiku-core-5", "4", lambda r: c4(r, "mart_awards_monthly", "month_start", "state_fips", "county_fips", "net_obligations_usd")),
 ("20261024-P1-cadence-haiku-core-6", "2", lambda r: c2(r, "mart_monthly_obligations", "county_fips", "net_obligations", "county_population_2024")),
 ("20261024-P1-cadence-haiku-core-6", "3", lambda r: scalar(f"select count(*) from {m(r,'mart_award_fy2024')} where net_obligations < 0")),
 ("20261024-P1-cadence-haiku-core-6", "4", lambda r: c4(r, "mart_monthly_obligations", "month_start", "state_fips", "county_fips", "net_obligations")),
 ("20261024-P1-cadence-haiku-full-6", "3", lambda r: scalar(f"select count(*) from (select award_key from {m(r,'fct_award_transaction')} group by 1 having sum(federal_action_obligation) < 0)")),
 ("20261024-P2-cadence-haiku-core-4", "3", lambda r: scalar(f"select count(*) from {m(r,'mart_award_fy2024')} where net_obligation < 0")),
 ("20261024-P2-cadence-haiku-core-6", "3", lambda r: scalar(f"select count(*) from (select award_type, award_key from {m(r,'fct_award_transaction')} group by all having sum(obligation_amount) < 0)")),
 ("20261024-P2-cadence-haiku-core-6", "5", lambda r: {f"{w}|{a}": [n, int(b)] for w, a, n, b in duckdb.sql(f"select wiki, actor_type, count(*), sum(bytes_added) from {m(r,'fct_edit')} group by all order by all").fetchall()}),
 ("20261024-P2-cadence-haiku-core-6", "7", lambda r: scalar(f"select count(*) from {m(r,'fct_edit')} where late")),
 ("20261024-P2-cadence-haiku-full-4", "2", lambda r: c2(r, "mart_obligations_monthly", "county_fips", "net_obligations", "population")),
 ("20261024-P2-cadence-haiku-full-4", "3", lambda r: scalar(f"select count(*) from {m(r,'mart_award_net_obligations')} where is_net_negative")),
 ("20261024-P2-cadence-haiku-full-5", "1", lambda r: {a: cents(v) for a, v in duckdb.sql(f"select agency_code, sum(net_obligations) from {m(r,'mart_fy2024_monthly')} where grain = 'agency' group by 1").fetchall()}),
]
ok = True
out = []
for run, n, fn in GAINS:
    got = fn(run)
    same = got == ANS[n]
    ok &= same
    out.append({"run": run, "check": n, "matches_key": same})
    print(f"{run:36s} check {n}: {'matches the key' if same else 'DIFFERS: ' + json.dumps(got, default=str)[:200]}")
json.dump(out, open(sys.argv[3], "w"), indent=1) if len(sys.argv) > 3 else None
sys.exit(0 if ok else 1)
