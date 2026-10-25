"""Replay the stored shapes-r2 transcripts through the supervisor rules of cadence fix/speed-slo.

For each run: where each rule steps in, and the minutes it removes. Projected time = agent wall time minus the
union of the removed intervals. Usage: replay2.py <tx dir> <cadence worktree> <out.json>
"""
import sys,os,re,json,glob
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from tl import load
from replay import blk, BASIS
CAD=sys.argv[2]; sys.path.insert(0,CAD+'/scripts')
import supervisor as S
STAGES={r['block']:r for r in json.load(open(CAD+'/stages.json'))['stages']}
CAP=600; IDLE=15*60
def dur(c): return (c['end']-c['start']) if c['end'] else 0
def merge(iv):
    out=[]
    for a,b in sorted(i for i in iv if i[1]>i[0]):
        if out and a<=out[-1][1]: out[-1][1]=max(out[-1][1],b)
        else: out.append([a,b])
    return out
def total(iv): return sum(b-a for a,b in merge(iv))
def plugin_root(cs):
    for c in cs:
        m=re.search(r'(/var/tmp/run-one/[^/]+/plugin)',json.dumps(c['input']))
        if m: return m.group(1)
    return CAD
def norm(cmd,proot): return cmd.replace(proot,CAD)
def analyse(f,rec):
    ev,cs=load(f); t0=min(c['start'] for c in cs); end=t0+rec['timing']['agent_wall_seconds']
    proot=plugin_root(cs)
    main=[c for c in cs if not c['parent']]
    agents={c['id']:c for c in cs if c['name'] in('Agent','Task')}
    ev_rows=[]; removed=[]; moved=0.0
    def note(rule,c,minutes,detail): ev_rows.append(dict(rule=rule,at=round((c['start']-t0)/60,1),minutes=round(minutes,1),detail=detail[:90]))
    # 1. bounded commands (every thread): deny the unbounded call; the waits it caused above the bound go
    chains=[];cur=None
    for c in sorted([c for c in cs if c['end'] and c['name'] in('Bash','Monitor')],key=lambda c:c['start']):
        cmd=c['input'].get('command','') if c['name']=='Bash' else 'monitor'
        why=S.bound_reason(cmd,CAP) if c['name']=='Bash' else ('monitor wait' if dur(c)>60 else None)
        if not why: cur=None; continue
        if cur and c['start']-cur[1]<180: cur[1]=max(cur[1],c['end']); cur[2]+=1
        else: cur=[c['start'],c['end'],1,c]; chains.append(cur)
    for a,b,n,c in chains:
        if b-a>CAP:
            removed.append((a+CAP,b)); note('bound',c,(b-a-CAP)/60,f'{n} calls: '+(c['input'].get('command') or 'Monitor').replace('\n',' '))
    # 2. orchestrator project commands: moved into the block subagent (no minutes removed)
    for c in main:
        if c['name']=='Bash' and c['end'] and S.project_command(norm(c['input'].get('command',''),proot),__import__('pathlib').Path(CAD)):
            moved+=dur(c)
    # 3. waits on a timer by the orchestrator: idle until its next call
    for i,c in enumerate(main):
        if c['name'] in S.WAIT_TOOLS:
            nxt=next((d['start'] for d in main[i+1:] if d['name'] not in S.WAIT_TOOLS),end)
            removed.append((c['start'],nxt)); note('wait',c,(nxt-c['start'])/60,'ScheduleWakeup')
    # 4. dispatch budget: the 3rd dispatch of a block is denied and the run stops there
    seen={}; stop_at=None
    for c in main:
        b=blk(c)
        if b is None: continue
        if c['end'] and c['end']-c['start']<5 and 'BLOCKED' in c['result']: continue  # the handoff denied it
        if b=='freeform': b='E1'  # a prose fix round is a /spec-driven dispatch under ADR-0030
        seen[b]=seen.get(b,0)+1
        lim=(STAGES.get(b,{}).get('budget') or {}).get('dispatches')
        if lim and seen[b]>lim and stop_at is None:
            stop_at=c['start']; note('dispatches',c,(end-c['start'])/60,f'{b} dispatch {seen[b]}: hard stop, the run ends')
    # free-form agents: a fix round sent as prose; counted as a /spec-driven dispatch (E1 budget)
    ff=[c for c in main if blk(c)=='freeform']
    # 5. subagent budgets on the timeline with the bounded waits removed
    for aid,a in agents.items():
        b=blk(a); lim=(STAGES.get(b,{}).get('budget') or {})
        if not a['end'] or not lim.get('minutes'): continue
        busy=(a['end']-a['start'])-total([(max(x,a['start']),min(y,a['end'])) for x,y in removed if y>a['start'] and x<a['end']])
        if busy>lim['minutes']*60:
            note('minutes',a,(busy-lim['minutes']*60)/60,f'{b} {busy/60:.0f} min > {lim["minutes"]}')
    # 6. repeat and idle inside subagents
    for aid,a in agents.items():
        kids=sorted([c for c in cs if c['parent']==aid and c['end']],key=lambda c:c['start'])
        res={}; last=a['start']; outs=set(); hit=None
        for c in kids:
            k=S.digest([c['name'],c['input']]); o=S.digest(c['result'])
            if c['start']-last>IDLE and hit is None: hit=('idle',c)
            same=res.setdefault(k,[])
            if len(same)>=2 and len(set(same[-2:]))==1 and hit is None: hit=('repeat',c)
            same.append(o)
            if c['name'] in S.WRITE_TOOLS or o not in outs: last=c['end']
            outs.add(o)
        if hit:
            r,c=hit; note(r,c,0,f'{blk(a)}: '+str(c['input'].get('command') or c['name'])[:70])
    if stop_at: removed.append((stop_at,end))
    cut=total(removed)/60
    # P phase: P1 start .. last P4 end; after: P1 + the longest review of the round + one P4 (in parallel)
    live=[c for c in main if blk(c) and not (c['end'] and c['end']-c['start']<5 and 'BLOCKED' in c['result'])]
    p1=next(c for c in live if blk(c)=='P1'); p4=[c for c in live if blk(c)=='P4']; rv=[c for c in live if blk(c) in('P3','P6','P7')]
    Pb=(max(c['end'] for c in p4)-p1['start'])/60; Pa=min(Pb,(dur(p1)+max(dur(c) for c in rv)+max(dur(c) for c in p4))/60)
    # R phase: R1 start .. the close (hard stop or deactivate) or the last work; after: minus removed, minus R3 run beside R2
    r1=next((c for c in live if blk(c)=='R1'),None); r2=[c for c in live if blk(c)=='R2']
    closes=[c for c in main if c['name']=='Bash' and re.search(r'--hard-stop|--deactivate',c['input'].get('command',''))]
    last=max(c['end'] or c['start'] for c in main if c['name'] not in S.WAIT_TOOLS)
    rend=closes[0]['end'] if closes else last
    if r1:
        Rb=(rend-r1['start'])/60
        r3=[c for c in main if c['name']=='Bash' and 'cognitive_complexity_gate' in c['input'].get('command','') and c['start']>r1['start']]
        par=min(sum(dur(c) for c in r3),dur(r2[0]))/60 if r2 and r3 else 0
        win=[(max(a,r1['start']),min(b,rend)) for a,b in merge(removed) if b>r1['start'] and a<rend]
        Ra=max(0,Rb-total(win)/60-par); cut+=par
    else: Rb=Ra=None
    phases=dict(P_before=round(Pb,1),P_after=round(Pa,1),R_before=round(Rb,1) if Rb is not None else None,R_after=round(Ra,1) if Ra is not None else None)
    cut+=Pb-Pa
    return dict(**phases,events=ev_rows,removed=round(cut,1),moved_out_of_orchestrator=round(moved/60,1),freeform_fix_agents=len(ff),
                before=round(rec['timing']['agent_wall_seconds']/60,1),after=round(rec['timing']['agent_wall_seconds']/60-cut,1))
if __name__=='__main__':
    out={}
    for f in sorted(glob.glob(sys.argv[1]+'/*.jsonl')):
        rec=json.load(open(f[:-6]+'.record.json')); name=os.path.basename(f)[:-6].replace('-cadence-haiku','')
        r=analyse(f,rec); r['slo']=round(1.25*BASIS[name[:2]]/60,1); out[name]=r
        print(f"{name:10} before {r['before']:6} after {r['after']:6} slo {r['slo']}  removed {r['removed']}  P {r['P_before']}->{r['P_after']}  R {r['R_before']}->{r['R_after']}  orch-cmds {r['moved_out_of_orchestrator']} freeform {r['freeform_fix_agents']}")
        for e in r['events']: print('     ',e)
    json.dump(out,open(sys.argv[3],'w'),indent=1)
