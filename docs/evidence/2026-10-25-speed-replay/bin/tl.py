"""Timeline of a stream-json transcript: main-thread tool calls with start/end."""
import json,sys,datetime as dt
def ts(s): return dt.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def load(path):
    ev=[json.loads(l) for l in open(path)]
    calls={}; order=[]
    for e in ev:
        t=e.get('timestamp')
        if e.get('type')=='assistant':
            for c in e['message'].get('content',[]):
                if c.get('type')=='tool_use':
                    calls[c['id']]=dict(id=c['id'],name=c['name'],input=c['input'],start=ts(t),end=None,parent=e.get('parent_tool_use_id'),result='')
                    order.append(c['id'])
        elif e.get('type')=='user':
            cont=e['message'].get('content')
            if isinstance(cont,list):
                for c in cont:
                    if c.get('type')=='tool_result' and c['tool_use_id'] in calls:
                        k=calls[c['tool_use_id']]; k['end']=ts(t)
                        r=c.get('content'); 
                        if isinstance(r,list): r=' '.join(x.get('text','') for x in r if isinstance(x,dict))
                        k['result']=str(r)
    return ev,[calls[i] for i in order]
def label(c):
    i=c['input']
    if c['name'] in('Agent','Task'): return (i.get('prompt') or '').split('\n')[0][:70]
    if c['name']=='Bash': return (i.get('command') or '').replace('\n',' ')[:110]
    return str(i.get('file_path') or i.get('description') or '')[:90]
if __name__=='__main__':
    ev,cs=load(sys.argv[1])
    t0=min(c['start'] for c in cs)
    for c in cs:
        if c['parent'] and '--all' not in sys.argv: continue
        d=(c['end']-c['start']) if c['end'] else -1
        print(f"{(c['start']-t0)/60:7.1f} {d/60:6.1f}m {c['name']:6} {label(c)}")
