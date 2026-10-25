import json,sys,re,collections,hashlib
from datetime import datetime
def ts(s): return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
TEST=re.compile(r'(/tests?/|test_|_test\.|fake|conftest|fixture|oracle)',re.I)
PROC=re.compile(r'(\.context/|DECISIONS|\.cursor/plans|\.plan\.md|ledger|findings|closure|/handoff/)',re.I)
CAD=re.compile(r'(CADENCE_HOME[}"]*/scripts|SKILL_ROOT|/plugin/scripts|\$C/|\$P/|"\$S"|\$S |_gate\.py|phase_ledger|entry_invariant|closure\.py|findings_io|ledger_verify|acceptance_checks|activate_session|pipeline_status|clean_checkout|test_shape\.py|DECISIONS|\.context/|\.cursor/plans)')
LONG=re.compile(r'(\bpytest\b|\bdbt\s+(build|run|test|seed|deps|parse|compile)|\bmake\s+(build|stream|test|all|check)|\bmake\b\s*(>|&|;|$)|\buv\s+sync|\bsleep\s+\d|\buntil\s|kill -0|\bpgrep\b|tail --pid|python3? -m \w+|\buv run\b)',re.M)
PYW=re.compile(r'(write_text|open\([^)]*[\'"]w)')
PATHS=re.compile(r'[\'"]?((?:[\w./-]+/)?[\w.-]+\.(?:py|sql|yml|yaml|toml|md|json|jsonl|csv))[\'"]?')
WRITE=re.compile(r'(cat\s*>>?\s*(\S+)|tee\s+(-a\s+)?(\S+)|sed\s+-i\S*\s.*?(\S+)\s*$|>\s*(\S+\.(py|sql|yml|yaml|toml|md|json)))')
def path_bucket(p):
    if PROC.search(p): return 'd'
    if TEST.search(p): return 'b'
    return 'a'
def bash_bucket(cmd):
    if CAD.search(cmd): return 'd'
    if re.search(r'(cat\s*>|>>?)\s*\S*(DECISIONS|\.context/)',cmd): return 'd'
    m=WRITE.search(cmd); tgt=None
    if m:
        tgt=next((g for g in m.groups()[1:] if g and g.strip() not in ('-a',)),None)
    elif PYW.search(cmd):
        ps=[p for p in PATHS.findall(cmd) if not p.startswith('/tmp')]
        tgt=ps[0] if ps else None
    if tgt and not tgt.startswith('/tmp') and not tgt.startswith('/dev') and not LONG.search(cmd): return path_bucket(tgt)
    if LONG.search(cmd): return 'c'
    if tgt and not tgt.startswith('/tmp') and not tgt.startswith('/dev'): return path_bucket(tgt)
    return 'h'
def gen_bucket(tu):
    if tu['name']=='Bash':
        cmd=tu['input'].get('command','')
        if re.search(r'(cat\s*>|>>?)\s*\S*(DECISIONS|\.context/)',cmd): return 'd'
        m=WRITE.search(cmd); tgt=None
        if m: tgt=next((g for g in m.groups()[1:] if g and g.strip() not in ('-a',)),None)
        elif PYW.search(cmd):
            ps=[p for p in PATHS.findall(cmd) if not p.startswith('/tmp')]; tgt=ps[0] if ps else None
        if tgt and not tgt.startswith('/tmp') and not tgt.startswith('/dev'): return path_bucket(tgt)
    return tool_bucket(tu)
def tool_bucket(tu):
    n=tu['name'];i=tu['input']
    if n in('Write','Edit','NotebookEdit'): return path_bucket(i.get('file_path',''))
    if n=='Bash': return bash_bucket(i.get('command',''))
    if n=='Monitor':
        s=json.dumps(i); return 'd' if CAD.search(s) else ('c' if LONG.search(s) or 'sleep' in s or 'kill -0' in s else 'h')
    if n=='Skill': return 'd'
    return 'h'
def rtext(c):
    if isinstance(c,str): return c
    if isinstance(c,list): return ''.join(x.get('text','') for x in c if isinstance(x,dict))
    return str(c)

def load(f):
    th=collections.defaultdict(list)
    for l in open(f):
        d=json.loads(l)
        if d.get('type') not in('assistant','user') or 'timestamp' not in d: continue
        th[d.get('parent_tool_use_id')].append(d)
    for k in th: th[k].sort(key=lambda d:ts(d['timestamp']))
    return th

def run(f):
    th=load(f)
    SEG=collections.defaultdict(collections.Counter); cur={'seg':'start@'}
    GEN=collections.Counter(); GENT=collections.Counter()
    B=collections.Counter(); peers=collections.Counter(); cmds=[]; stops=[]; sinks=[]; rev=[]
    class _A:
        def __getitem__(self,k): return B[k]
        def __setitem__(self,k,v):
            SEG[cur['seg']][k]+=v-B[k]; B[k]=v
    ADD=_A()
    def walk(tid,label,t0=None,t1=None):
        ev=th.get(tid,[])
        pending={}  # id->(tu,t)
        prev=t0 if t0 is not None else (ts(ev[0]['timestamp']) if ev else None)
        seen_cmd={}; edits=[]; st8={'bg':None,'closed':False,'prevtype':None}
        uses={}
        for d in ev:
            if d['type']=='assistant':
                for c in d['message']['content']:
                    if c.get('type')=='tool_use': uses[c['id']]=(c,ts(d['timestamp']))
        results={}
        for d in ev:
            if d['type']=='user' and isinstance(d['message']['content'],list):
                for c in d['message']['content']:
                    if c.get('type')=='tool_result': results[c['tool_use_id']]=(ts(d['timestamp']),rtext(c.get('content')))
        # redundancy flags
        redundant=set(); lastout={}
        for uid,(tu,t) in sorted(uses.items(),key=lambda x:x[1][1]):
            if tu['name']=='Bash':
                k=re.sub(r'\s+',' ',tu['input'].get('command','')).strip()
                out=results.get(uid,(0,''))[1]
                h=hashlib.md5(re.sub(r'[0-9]+','',out[-300:]).encode()).hexdigest()
                if lastout.get(k)==h and not re.search(r'sleep|kill -0|until |while ',k): redundant.add(uid)
                lastout[k]=h
            if tu['name']=='Edit':
                i=tu['input']
                for (p,o,n) in edits:
                    if p==i.get('file_path') and o==i.get('new_string') and n==i.get('old_string'): redundant.add(uid); rev.append((label,tu['input'].get('file_path')))
                edits.append((i.get('file_path'),i.get('old_string'),i.get('new_string')))
        for idx,d in enumerate(ev):
            t=ts(d['timestamp'])
            if t1 is not None: t=min(t,t1)
            dt=max(0,t-prev) if prev is not None else 0
            # what does the interval belong to?
            if pending:
                uid=min(pending,key=lambda u:pending[u][1]); tu=pending[uid][0]
                if tu['name'] in ('Agent','Task'):
                    pass  # handled by recursion
                else:
                    b='f' if uid in redundant else tool_bucket(tu)
                    ADD[b]+=dt
            else:
                if d['type']=='assistant':
                    c=d['message']['content'][0] if d['message']['content'] else {}
                    if c.get('type')=='tool_use':
                        gb='f' if c['id'] in redundant else gen_bucket(c); ADD[gb]+=dt; GEN[gb]+=dt; GENT[(c['name'],gb)]+=dt
                    elif st8['prevtype']=='text' and dt>60:
                        kb='h' if st8['closed'] else (st8['bg'] or 'g')
                        ADD[kb]+=dt; sinks.append((dt,label,d['timestamp'],f'IDLE turn-ended wait ->{kb} closed={st8["closed"]}'))
                    else:
                        ADD['g']+=dt
                        if dt>120: sinks.append((dt,label,d['timestamp'],'model gen '+c.get('type','')+': '+(c.get('thinking') or c.get('text') or '')[:100]))
                else:
                    txt=rtext(d['message']['content'])
                    if 'Stop hook feedback' in txt:
                        ADD['e']+=dt; cur['seg']='after-stop@'+d['timestamp'][11:16]; stops.append((label,d['timestamp'],round(dt),txt.replace('\n',' ')[:160]))
                    else:
                        if 'task-notification' in txt or 'Monitor' in txt or 'background' in txt.lower(): ADD['c']+=dt; k='c-wait'
                        else: ADD['h']+=dt; k='h-user'
                        if dt>60: sinks.append((dt,label,d['timestamp'],k+' idle until user msg: '+txt.replace(chr(10),' ')[:120]))
            prev=t
            if d['type']=='assistant':
                st8['prevtype']=(d['message']['content'][-1].get('type') if d['message']['content'] else None)
            else: st8['prevtype']='user'
            if d['type']=='assistant':
                for c in d['message']['content']:
                    if c.get('type')=='tool_use' and c['name']=='Bash' and re.search(r'--deactivate|--hard-stop',c['input'].get('command','')): st8['closed']=True
                    if c.get('type')=='tool_use' and (c['input'].get('run_in_background') or c['name']=='Monitor'): st8['bg']=tool_bucket(c)
            else:
                if isinstance(d['message']['content'],list):
                    for c in d['message']['content']:
                        if c.get('type')=='tool_result' and 'moved to the background' in rtext(c.get('content')) and c['tool_use_id'] in uses: st8['bg']=tool_bucket(uses[c['tool_use_id']][0])
            if d['type']=='assistant':
                for c in d['message']['content']:
                    if c.get('type')=='tool_use':
                        pending[c['id']]=(c,t)
                        if tid is None and c['name'] in ('Skill','Agent','Task'):
                            nm=c['input'].get('skill') or (c['input'].get('prompt') or '?').split()[0]
                            cur['seg']=('inline ' if c['name']=='Skill' else 'peer ')+nm+'@'+d['timestamp'][11:16]
                        elif tid is None and c['name']=='Bash' and re.search(r'scripts/(\w+_gate)\.py',c['input'].get('command','')) and not cur['seg'].startswith('gate'):
                            pass
            else:
                if isinstance(d['message']['content'],list):
                    for c in d['message']['content']:
                        if c.get('type')=='tool_result' and c['tool_use_id'] in pending:
                            tu,st=pending.pop(c['tool_use_id'])
                            dur=t-st
                            if tu['name'] in('Agent','Task'):
                                lab=tu['input'].get('prompt','').split()[0] if tu['input'].get('prompt') else '?'
                                peers[lab]+=dur
                                walk(tu['id'],lab,st,t)
                                if tid is None: cur['seg']='orch after '+lab+'@'+d['timestamp'][11:16]
                                sinks.append((dur,label,datetime.fromtimestamp(st,__import__('datetime').timezone.utc).strftime('%H:%M'),'peer '+tu['input'].get('prompt','')[:90]))
                            else:
                                k=tu['input'].get('command') or tu['input'].get('file_path') or json.dumps(tu['input'])[:120]
                                cmds.append((dur,label,datetime.fromtimestamp(st,__import__('datetime').timezone.utc).strftime('%H:%M'),tu['name'],tool_bucket(tu)+('*' if c['tool_use_id'] in redundant else ''),k.replace('\n',' ')[:140]))
        if t1 is not None and prev is not None and t1>prev:
            ADD['g' if not pending else 'h']+=t1-prev  # tail inside peer before handback returns
    walk(None,'main')
    main=th[None]; wall=ts(main[-1]['timestamp'])-ts(main[0]['timestamp'])
    return dict(GEN=GEN,GENT=GENT,SEG=SEG,B=B,peers=peers,cmds=cmds,stops=stops,sinks=sinks,wall=wall,rev=rev,start=main[0]['timestamp'],end=main[-1]['timestamp'])
if __name__=='__main__':
    import os
    for f in sys.argv[1:]:
        r=run(f);B=r['B'];tot=sum(B.values())
        name=os.path.basename(f)[9:-6]
        print(f"\n### {name} wall={r['wall']/60:.0f}m sum={tot/60:.0f}m  "+' '.join(f"{k}={B[k]/60:.0f}" for k in 'abcdefgh'))
        print(' peers(min):',{k:round(v/60) for k,v in r['peers'].items()})
        print(' reverted edits:',len(r['rev']))
        print(' top tool calls:')
        for x in sorted(r['cmds'],reverse=True)[:8]: print('  %.1fm'%(x[0]/60),*x[1:])
        print(' redundant:',sum(1 for x in r['cmds'] if '*' in x[4]),'%.1fm'%(sum(x[0] for x in r['cmds'] if '*' in x[4])/60))
        print(' stops:')
        for s in r['stops']: print('  ',s)
        print(' segments:')
        for k,v in sorted(r['SEG'].items(),key=lambda x:-sum(x[1].values()))[:9]: print('   %5.1fm %-45s'%(sum(v.values())/60,k),' '.join(f"{b}={v[b]/60:.0f}" for b in 'abcdefgh' if v[b]>=30))
        print(' sinks(peers/gen):')
        for x in sorted(r['sinks'],reverse=True)[:6]: print('  %.1fm'%(x[0]/60),*x[1:])
