import json,sys
path=sys.argv[1]; w=int(sys.argv[2]) if len(sys.argv)>2 else 300
for i,l in enumerate(open(path)):
    try: e=json.loads(l)
    except: continue
    t=e.get("type"); m=e.get("message") or {}
    side="S" if e.get("isSidechain") or e.get("parent_tool_use_id") else "M"
    c=m.get("content") if isinstance(m,dict) else None
    ts=e.get("timestamp","")[11:19]
    if isinstance(c,str): print(i,ts,side,t,"TEXT",c[:w].replace("\n"," ")); continue
    for b in c or []:
        bt=b.get("type")
        if bt=="text": print(i,ts,side,t,"TEXT",b["text"][:w].replace("\n"," "))
        elif bt=="tool_use": print(i,ts,side,t,"USE",b.get("name"),json.dumps(b.get("input"))[:w])
        elif bt=="tool_result":
            cc=b.get("content"); 
            if isinstance(cc,list): cc=" ".join(x.get("text","") for x in cc if isinstance(x,dict))
            print(i,ts,side,t,"RES",str(cc)[:w].replace("\n"," "))
    if t not in("user","assistant") : print(i,ts,side,t, json.dumps(e)[:w])
