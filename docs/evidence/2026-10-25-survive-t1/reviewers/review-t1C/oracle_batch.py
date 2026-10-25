import csv, io, zipfile, glob, collections, sys
from decimal import Decimal, ROUND_HALF_UP
import duckdb
raw="data/raw"
rows=[]
for z in sorted(glob.glob(f"{raw}/usaspending/*.zip")):
    kind="contract" if "_Contracts_" in z else "assistance"
    with zipfile.ZipFile(z) as a:
        txt=a.read(a.namelist()[0]).decode("utf-8")
    for r in csv.DictReader(io.StringIO(txt,newline="")):
        if not ("2023-10-01"<=r["action_date"]<="2024-09-30"): continue
        st=r["prime_award_transaction_place_of_performance_state_fips_code"] or "UNKNOWN"
        co=r["prime_award_transaction_place_of_performance_county_fips_code"]
        co = co if (co and st!="UNKNOWN") else "UNKNOWN"
        rows.append((r[f"{kind}_award_unique_key"], r["awarding_agency_code"], st, co, r["action_date"][:7], Decimal(r["federal_action_obligation"])))
print("rows", len(rows))
pop={}
for f,col,yr in [("co-est2021-alldata.csv","POPESTIMATE2021",2021),("co-est2024-alldata.csv","POPESTIMATE2024",2024)]:
    for r in csv.DictReader(open(f"{raw}/census/{f}",encoding="latin-1",newline="")):
        if r["SUMLEV"]=="050": pop[r["STATE"]+r["COUNTY"]]=(int(r[col]),yr)
by_ag=collections.defaultdict(Decimal); by_award=collections.defaultdict(Decimal); by_co=collections.defaultdict(Decimal)
for k,ag,st,co,m,v in rows:
    by_ag[ag]+=v; by_award[k]+=v
    if co!="UNKNOWN": by_co[co]+=v
con=duckdb.connect()
M="read_parquet('out/marts/mart_monthly_obligations/*.parquet')"
mart_ag=dict(con.sql(f"select agency_code, sum(net_obligations) from {M} group by 1").fetchall())
print("check1 match:", mart_ag==dict(by_ag), dict(by_ag))
neg=sum(1 for v in by_award.values() if v<0)
mneg=con.sql("select count(*) from read_parquet('out/marts/mart_award_fy2024/*.parquet') where net_obligations<0").fetchone()[0]
print("check3 python",neg,"mart",mneg, "awards", len(by_award))
pp={c:(v/pop[c][0]) for c,v in by_co.items() if c in pop and pop[c][0]>0}
top=sorted(pp.items(), key=lambda x:-x[1])[:12]
for c,v in top: print("  py", c, v.quantize(Decimal("0.0001"),ROUND_HALF_UP), pop[c])
mt=con.sql(f"select county_fips, any_value(county_name), sum(net_obligations)/any_value(county_population_2024) pp from {M} where county_fips<>'UNKNOWN' group by 1 having any_value(county_population_2024)>0 order by pp desc limit 12").fetchall()
for r in mt: print("  mart", r)
# check4: per month state totals vs source
tot=collections.defaultdict(Decimal); st_tot=collections.defaultdict(Decimal)
for k,ag,st,co,m,v in rows: tot[m]+=v; st_tot[(m,st)]+=v
ms=dict(((str(a)[:7],b),c) for a,b,c in con.sql(f"select month_start, state_fips, sum(net_obligations) from {M} group by 1,2").fetchall())
print("check4 state totals match:", ms==dict(st_tot))
