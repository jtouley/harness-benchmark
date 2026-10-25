import duckdb,sys
c=duckdb.connect('out/warehouse.duckdb', read_only=True)
for q in sys.argv[1:]:
    print('>>',q); 
    try: print(c.sql(q))
    except Exception as e: print('ERR',e)
