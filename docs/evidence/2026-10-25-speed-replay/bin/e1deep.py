"""E1 (or a one-shot) decomposed: model time, tool time by kind, calls, context, output tokens."""
import sys,os,json,re,datetime as dt,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from replay import blk
def ts(s): return dt.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def kind(c):
    n=c['name']
    if n!='Bash': return n
    s=c['input'].get('command','')
    if re.search(r'\bsleep\b|kill -0',s): return 'Bash:wait'
    if 'make stream' in s or 'stream' in s and ('make' in s or 'curl' in s): return 'Bash:stream'
    if 'make build' in s or 'dbt ' in s: return 'Bash:build/dbt'
    if re.search(r'pytest|unittest',s): return 'Bash:tests'
    if 'git ' in s: return 'Bash:git'
    if re.search(r'scripts/\w+\.py',s): return 'Bash:cadence'
    return 'Bash:other'
def run(path, parent):
    """parent: the Agent tool_use id of E1, or None for the one-shot main thread."""
    ev=[json.loads(l) for l in open(path)]
    th=[e for e in ev if e.get('type') in('assistant','user') and e.get('parent_tool_use_id')==parent and e.get('timestamp')]
    calls={};model=0.0;last_user=None;outtok=0;ctx=[];n=0;think=0
    for e in th:
        t=ts(e['timestamp'])
        if e['type']=='assistant':
            if last_user is not None: model+=max(0,t-last_user); last_user=None
            u=e['message'].get('usage') or {}
            outtok+=int(u.get('output_tokens') or 0)
            ctx.append(sum(int(u.get(k) or 0) for k in('input_tokens','cache_read_input_tokens','cache_creation_input_tokens')))
            for c in e['message']['content']:
                if c.get('type')=='tool_use': calls[c['id']]=dict(name=c['name'],input=c['input'],start=t); n+=1
        else:
            last_user=t
            for c in e['message']['content'] if isinstance(e['message']['content'],list) else []:
                if c.get('type')=='tool_result' and c['tool_use_id'] in calls: calls[c['tool_use_id']]['end']=t
    span=ts(th[-1]['timestamp'])-ts(th[0]['timestamp'])
    by=collections.Counter()
    for c in calls.values():
        if 'end' in c: by[kind(c)]+=c['end']-c['start']
    return dict(span=round(span/60,1),model=round(model/60,1),calls=n,requests=len(ctx),ctx_med=sorted(ctx)[len(ctx)//2] if ctx else 0,ctx_max=max(ctx) if ctx else 0,out_tok=outtok,
                tools={k:round(v/60,1) for k,v in by.most_common()})
if __name__=='__main__':
    for f in sys.argv[1:]:
        if 'oneshot' in f: print(os.path.basename(f), run(f,None)); continue
        ev=[json.loads(l) for l in open(f)]
        ids=[c['id'] for e in ev if e.get('type')=='assistant' and not e.get('parent_tool_use_id') for c in e['message']['content'] if c.get('type')=='tool_use' and c['name'] in('Agent','Task') and blk({'name':c['name'],'input':c['input']})=='E1']
        if ids: print(os.path.basename(f)[:24], run(f,ids[0]))
