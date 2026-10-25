"""Independent oracle for checks 1-4 straight from data/raw (no lake, no dbt)."""
import csv, io, sys, zipfile, pathlib, datetime
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import duckdb
tree = pathlib.Path(sys.argv[1])
raw = tree / "data/raw"
rows = []
for z in sorted((raw/"usaspending").glob("*.zip")):
    kind = "contract" if "_Contracts_" in z.name else "assistance"
    with zipfile.ZipFile(z) as a:
        text = a.read(a.namelist()[0]).decode("utf-8")
    for r in csv.DictReader(io.StringIO(text, newline="")):
        d = datetime.date.fromisoformat(r["action_date"][:10])
        if not (datetime.date(2023,10,1) <= d <= datetime.date(2024,9,30)): continue
        st = r["prime_award_transaction_place_of_performance_state_fips_code"] or "UNKNOWN"
        co = r["prime_award_transaction_place_of_performance_county_fips_code"]
        co = "UNKNOWN" if st == "UNKNOWN" or not co else co
        rows.append(dict(award=r[f"{kind}_award_unique_key"], agency=r["awarding_agency_code"], st=st, co=co,
                         month=d.replace(day=1), amt=Decimal(r["federal_action_obligation"])))
print("rows", len(rows))
pop = {}
for fn, col in (("co-est2024-alldata.csv","POPESTIMATE2024"),("co-est2021-alldata.csv","POPESTIMATE2021")):
    with open(raw/"census"/fn, encoding="latin-1", newline="") as h:
        for r in csv.DictReader(h):
            if r["SUMLEV"] == "050":
                pop.setdefault(r["STATE"]+r["COUNTY"], int(r[col]))
con = duckdb.connect()
mart = con.sql(f"select * from read_parquet('{tree}/out/marts/mart_monthly_obligations/*.parquet')")
# check 1
exp = defaultdict(Decimal)
for r in rows: exp[r["agency"]] += r["amt"]
act = dict(con.sql(f"select agency_code, sum(net_obligations) from read_parquet('{tree}/out/marts/mart_monthly_obligations/*.parquet') group by 1").fetchall())
print("check1", "OK" if dict(exp)==act else ("DIFF", dict(exp), act))
# check 2
by_c = defaultdict(Decimal)
for r in rows:
    if r["co"] != "UNKNOWN": by_c[r["co"]] += r["amt"]
pp = {c: (v/pop[c]).quantize(Decimal("0.0001"), ROUND_HALF_UP) for c,v in by_c.items() if c in pop and pop[c]>0}
top = sorted(pp.items(), key=lambda kv: -kv[1])[:12]
print("check2 oracle top12", top)
act2 = con.sql(f"select county_fips, any_value(county_name), sum(net_obligations)/any_value(county_population_2024) pp from read_parquet('{tree}/out/marts/mart_monthly_obligations/*.parquet') where county_population_2024>0 group by 1 order by pp desc limit 12").fetchall()
print("check2 mart (oracle_map recipe)", act2)
# check 3
aw = defaultdict(Decimal)
for r in rows: aw[r["award"]] += r["amt"]
print("check3 oracle", sum(1 for v in aw.values() if v<0), "mart", con.sql(f"select count(*) from read_parquet('{tree}/out/marts/mart_award_fy2024/*.parquet') where net_obligations<0").fetchone())
print("check3 awards", len(aw), "zero-net", sum(1 for v in aw.values() if v==0))
# check 4
src = defaultdict(Decimal); stt = defaultdict(Decimal)
for r in rows: src[r["month"]] += r["amt"]; stt[(r["month"], r["st"])] += r["amt"]
m_st = dict(((m, s), v) for m, s, v in con.sql(f"select month_start, state_fips, sum(net_obligations) from read_parquet('{tree}/out/marts/mart_monthly_obligations/*.parquet') group by 1,2").fetchall())
m_src = dict(con.sql(f"select month_start, sum(net_obligations) from read_parquet('{tree}/out/marts/mart_monthly_obligations/*.parquet') group by 1").fetchall())
print("check4 state", "OK" if dict(stt)==m_st else "DIFF", "source", "OK" if dict(src)==m_src else "DIFF")
