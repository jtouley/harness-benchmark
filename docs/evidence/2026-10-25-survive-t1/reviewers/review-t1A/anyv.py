import duckdb, collections
seen=collections.Counter()
for t in (1,2,4,8):
  for i in range(10):
    c=duckdb.connect(); c.sql(f"set threads={t}")
    r=c.sql("""select award_key, any_value(state_fips) s, any_value(county_fips) cf from (
      select assistance_award_unique_key award_key,
        prime_award_transaction_place_of_performance_state_fips_code state_fips,
        prime_award_transaction_place_of_performance_county_fips_code county_fips
      from read_parquet('lake/usaspending_assistance/*.parquet') order by random())
      where award_key in ('ASST_NON_21FXDWY001_485','ASST_NON_FEL29493424_418') group by 1 order by 1""").fetchall()
    seen[tuple(r)]+=1
for k,v in seen.items(): print(v,k)
