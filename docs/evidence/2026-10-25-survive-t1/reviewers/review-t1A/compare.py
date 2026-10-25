import pickle, collections, duckdb, json
evs=pickle.load(open('replay.pkl','rb'))
seen=set(); uniq=[]
for e in evs:
    i=e['meta']['id']
    if i in seen: continue
    seen.add(i); uniq.append(e)
print('unique',len(uniq), 'dups', len(evs)-len(uniq))
hw=None; late=set(); per=collections.Counter(); bytes_=collections.Counter(); win=collections.Counter()
types=collections.Counter(e.get('type') for e in uniq); print(types)
botvals=collections.Counter(repr(e.get('bot')) for e in uniq); print('bot values',botvals)
tsnull=sum(1 for e in uniq if not isinstance(e.get('timestamp'),int)); print('ts non-int',tsnull)
nolen=sum(1 for e in uniq if e.get('type') in ('edit','new') and not e.get('length')); print('edits without length',nolen)
c=duckdb.connect('w/out/warehouse.duckdb',read_only=True)
dom=dict(c.sql("select dbname, regexp_replace(url,'^https?://','') from read_parquet('w/lake/sitematrix_sites/*.parquet')").fetchall())
for e in uniq:
    ts=e.get('timestamp')
    if e.get('type') in ('edit','new'):
        a='bot' if e.get('bot') is True else 'human'
        L=e.get('length') or {}
        nb=(L.get('new') or 0)-(L.get('old') or 0)
        per[(e['wiki'],a)]+=1; bytes_[(e['wiki'],a)]+=nb
        if ts is not None:
            ws=ts-ts%300
            is_l = hw is not None and hw-(ws+300)>600
            if is_l: late.add(e['meta']['id'])
            elif dom.get(e['wiki'])=='en.wikipedia.org': win[ws]+=1
    if ts is not None: hw=ts if hw is None else max(hw,ts)
print('late',len(late))
m=c.sql("select event_id from read_parquet('w/out/marts/late_events/*.parquet')").fetchall()
ml={x[0] for x in m}; print('late mart',len(ml),'symdiff',len(ml^late))
mw=dict(c.sql("select wiki||'|'||actor_type, edit_count from read_parquet('w/out/marts/edits_by_wiki_actor/*.parquet')").fetchall())
mb=dict(c.sql("select wiki||'|'||actor_type, net_bytes from read_parquet('w/out/marts/edits_by_wiki_actor/*.parquet')").fetchall())
diffs=[(k,v,mw.get(f'{k[0]}|{k[1]}')) for k,v in per.items() if mw.get(f'{k[0]}|{k[1]}')!=v]
print('wiki/actor rows oracle',len(per),'mart',len(mw),'count diffs',len(diffs), diffs[:5])
bd=[k for k,v in bytes_.items() if mb.get(f'{k[0]}|{k[1]}')!=v]; print('bytes diffs',len(bd))
top=sorted(win.items(), key=lambda kv:(-kv[1],kv[0]))[:12]; print('oracle top en windows',top)
print(c.sql("select window_start, sum(edit_count) n from read_parquet('w/out/marts/window_5min/*.parquet') where domain='en.wikipedia.org' group by 1 order by n desc, 1 limit 12").fetchall())
# full window recompute
full=collections.Counter()
hw=None
for e in uniq:
    ts=e.get('timestamp')
    if e.get('type') in ('edit','new') and ts is not None:
        ws=ts-ts%300
        if not (hw is not None and hw-(ws+300)>600):
            full[(ws,e['wiki'],e.get('namespace'),'bot' if e.get('bot') is True else 'human')]+=1
    if ts is not None: hw=ts if hw is None else max(hw,ts)
mm=dict(((r[0],r[1],r[2],r[3]),r[4]) for r in c.sql("select window_start,wiki,namespace,actor_type,edit_count from read_parquet('w/out/marts/window_5min/*.parquet')").fetchall())
print('window rows oracle',len(full),'mart',len(mm),'diffs',sum(1 for k in set(full)|set(mm) if full.get(k)!=mm.get(k)))
print('wikis without domain', c.sql("select count(*), count(distinct wiki) from fact_edit where domain is null").fetchall())
