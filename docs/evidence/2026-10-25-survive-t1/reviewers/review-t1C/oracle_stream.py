import http.client, json, time, collections, duckdb
conn=http.client.HTTPConnection("localhost",8099,timeout=10)
conn.request("GET","/v2/stream/recentchange",headers={"Accept":"text/event-stream"})
resp=conn.getresponse()
events=[]; data=[]; bad=0; t0=time.time()
while time.time()-t0<75:
    try: line=resp.readline()
    except Exception as e: print("read end", e); break
    if not line: break
    line=line.decode().rstrip("\r\n")
    if line=="":
        if data:
            try: events.append(json.loads("\n".join(data)))
            except ValueError: bad+=1
        data=[]
    elif line.startswith("data:"): data.append(line[5:].lstrip())
print("received", len(events), "bad", bad, "secs", round(time.time()-t0,1))
seen=set(); hw=None; edits=[]
for e in events:
    i=e["meta"]["id"]
    if i in seen: continue
    seen.add(i); ts=e.get("timestamp")
    if e.get("type") in ("edit","new"):
        w=ts-ts%300
        late = hw is not None and hw-(w+300)>600
        L=e.get("length") or {}
        edits.append((e["wiki"], "bot" if e.get("bot") is True else "human", (L.get("new") or 0)-(L.get("old") or 0), w, late, i))
    if ts is not None: hw=ts if hw is None else max(hw,ts)
print("unique", len(seen), "edits", len(edits), "late", sum(x[4] for x in edits))
c=duckdb.connect()
exp5=collections.Counter(); expb=collections.Counter()
for w,a,nb,_,_,_ in edits: exp5[(w,a)]+=1; expb[(w,a)]+=nb
got=c.sql("select wiki,actor_type,edit_count,net_bytes from read_parquet('out/marts/edits_by_wiki_actor/*.parquet')").fetchall()
print("check5 match", {(w,a):(n,b) for w,a,n,b in got}=={k:(exp5[k],expb[k]) for k in exp5})
dom=dict(c.sql("select dbname, regexp_replace(url,'^https?://','') from read_parquet('lake/sitematrix_sites/*.parquet')").fetchall())
win=collections.Counter(w for wk,a,nb,w,l,_ in edits if not l and dom.get(wk)=="en.wikipedia.org")
print("check6 py ", sorted(win.items(), key=lambda x:(-x[1],x[0]))[:10])
print("check6 mart", c.sql("select window_start, sum(edit_count) n from read_parquet('out/marts/window_5min/*.parquet') where domain='en.wikipedia.org' group by 1 order by n desc, 1 limit 10").fetchall())
lateids={x[5] for x in edits if x[4]}
mart7={r[0] for r in c.sql("select event_id from read_parquet('out/marts/late_events/*.parquet')").fetchall()}
print("check7 py", len(lateids), "mart", len(mart7), "same set", lateids==mart7)
