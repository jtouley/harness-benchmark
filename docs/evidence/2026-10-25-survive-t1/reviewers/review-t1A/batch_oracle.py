import zipfile, csv, io, glob, collections, duckdb
from decimal import Decimal, ROUND_HALF_UP
raw='w/data/raw'
rows=[]
for z in sorted(glob.glob(raw+'/usaspending/*.zip')):
    kind='contract' if '_Contracts_' in z else 'assistance'
    with zipfile.ZipFile(z) as a:
        for r in csv.DictReader(io.TextIOWrapper(a.open(a.namelist()[0]),encoding='utf-8')):
            rows.append((kind,r))
print('rows',len(rows), 'members check')
hdr=collections.Counter()
fy=[(k,r) for k,r in rows if '2023-10-01'<=r['action_date']<='2024-09-30']
print('fy rows',len(fy))
# check1
ag=collections.defaultdict(Decimal)
for k,r in fy: ag[r['awarding_agency_code']]+=Decimal(r['federal_action_obligation'])
c=duckdb.connect()
m=dict(c.sql("select agency_code, sum(net_obligations) from read_parquet('w/out/marts/mart_monthly_obligations/*.parquet') group by 1").fetchall())
print('check1', {a:(v, m.get(a)) for a,v in ag.items() if m.get(a)!=v} or 'match', dict(ag))
# check3
aw=collections.defaultdict(Decimal)
for k,r in fy: aw[r[f'{k}_award_unique_key']]+=Decimal(r['federal_action_obligation'])
neg=sum(1 for v in aw.values() if v<0)
mneg=c.sql("select count(*) from read_parquet('w/out/marts/mart_award_fy2024/*.parquet') where net_obligations<0").fetchone()[0]
print('check3 oracle',neg,'mart',mneg, 'awards',len(aw))
# population from census raw
pop={}; pyear={}
for f,col,yr in (('co-est2024-alldata.csv','POPESTIMATE2024',2024),('co-est2021-alldata.csv','POPESTIMATE2021',2021)):
    for r in csv.DictReader(open(f'{raw}/census/{f}',encoding='latin-1')):
        if r['SUMLEV']!='050': continue
        k=r['STATE']+r['COUNTY']
        if k not in pop: pop[k]=int(r[col]); pyear[k]=yr
cty=collections.defaultdict(Decimal)
for k,r in fy:
    cf=r['prime_award_transaction_place_of_performance_county_fips_code']
    if cf: cty[cf]+=Decimal(r['federal_action_obligation'])
pp=[(cf,(v/pop[cf]).quantize(Decimal('0.0001'),ROUND_HALF_UP)) for cf,v in cty.items() if cf in pop and pop[cf]>0]
pp.sort(key=lambda x:-x[1])
print('check2 oracle top 12', [(a,str(b),pyear[a]) for a,b in pp[:12]])
print(c.sql("select county_fips, sum(net_obligations)/any_value(county_population_2024) pp from read_parquet('w/out/marts/mart_monthly_obligations/*.parquet') where county_population_2024>0 group by 1 order by pp desc limit 12").fetchall())
# check4 for every month: county sums vs state vs source
mon=collections.defaultdict(Decimal); st=collections.defaultdict(Decimal)
for k,r in fy:
    s=r['prime_award_transaction_place_of_performance_state_fips_code'] or 'UNKNOWN'
    mon[r['action_date'][:7]]+=Decimal(r['federal_action_obligation']); st[(r['action_date'][:7],s)]+=Decimal(r['federal_action_obligation'])
ms=dict(((str(a)[:7],b),v) for a,b,v in c.sql("select month_start, state_fips, sum(net_obligations) from read_parquet('w/out/marts/mart_monthly_obligations/*.parquet') group by 1,2").fetchall())
print('check4 state diffs', [k for k in set(st)|set(ms) if st.get(k)!=ms.get(k)][:5], 'months', len(mon))
