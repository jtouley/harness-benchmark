import sys, duckdb
con = duckdb.connect("out/warehouse.duckdb", read_only=True)
for q in sys.argv[1:]:
    print(">>", q[:200]); 
    try:
        r = con.sql(q)
        print(r.fetchall()[:40] if r is not None else None)
    except Exception as e: print("ERR", e)
