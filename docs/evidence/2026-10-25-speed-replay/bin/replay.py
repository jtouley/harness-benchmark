"""Replay the stored shapes-r2 transcripts: measure phases, gate loops and removable time."""
import sys,re,json,glob,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from tl import load
BASIS={'P1':1882.6,'P2':1596.9}  # Oct 15 Haiku one-shot agent_wall_seconds (baselines.json)
def blk(c):
    if c['name'] not in('Agent','Task'): return None
    p=(c['input'].get('prompt') or '').strip().split('\n')[0]
    m=re.match(r'/(?:cadence:)?([\w-]+)(.*)',p)
    if not m: return 'freeform'
    s=m.group(1)
    if s=='test-benchmark': return 'P7' if m.group(2).strip().startswith('plan') else 'R2'
    return {'vibe-test':'A5','plan-create':'P1','plan-review':'P3','de-adversarial-reviewer':'P6','plan-update':'P4',
            'spec-driven':'E1','commit-push-pr':'E4','pr-review-local':'R1'}.get(s,s)
PROJECT=re.compile(r'\b(make|dbt|pytest|unittest|uv run|python3? -m|ruff|mypy)\b')
WAIT=re.compile(r'\bsleep\b|kill -0')
WRITE=re.compile(r'git commit|>\s*[\w./]|sed -i|cat >|tee |write_text|\.write\(|git add|patch')
def dur(c): return (c['end']-c['start']) if c['end'] else 0
def merge(iv):
    iv=sorted(i for i in iv if i[1]>i[0]); out=[]
    for a,b in iv:
        if out and a<=out[-1][1]: out[-1][1]=max(out[-1][1],b)
        else: out.append([a,b])
    return out
def total(iv): return sum(b-a for a,b in merge(iv))
def analyse(path,rec):
    ev,cs=load(path)
    t0=min(c['start'] for c in cs); end=t0+rec['timing']['agent_wall_seconds']
    main=[c for c in cs if not c['parent']]
    A=[(blk(c),c) for c in main if blk(c)]
    def first(b): return next((c for x,c in A if x==b),None)
    def all_(b): return [c for x,c in A if x==b]
    R={}
    # P phase: P1 start .. last P4 end
    p1=first('P1'); p4s=all_('P4'); rev=[c for x,c in A if x in('P3','P6','P7')]
    Pb=(max(c['end'] for c in p4s)-p1['start'])/60
    longest_rev=max(dur(c) for c in rev)
    Pa=(dur(p1)+longest_rev+max(dur(c) for c in p4s))/60
    R['P_before'],R['P_after']=round(Pb,1),round(min(Pa,Pb),1)
    # R phase: R1 start .. run end (agent wall)
    r1=first('R1'); r2=all_('R2')
    hs=[c for c in main if c['name']=='Bash' and ('--hard-stop' in c['input'].get('command','') or '--deactivate' in c['input'].get('command',''))]
    close=hs[0]['end'] if hs else None
    R['r2_calls']=len(r2)
    # R3 gate runs (any thread); a loop "for i in ..." around the gate counts its iterations
    r3=0
    for c in cs:
        cmd=c['input'].get('command','') if c['name']=='Bash' else ''
        if 'cognitive_complexity_gate' in cmd:
            m=re.search(r'for \w+ in ((?:\d+ )+\d+|\$\(seq 1 (\d+)\))',cmd)
            r3+= (len(m.group(1).split()) if m and not m.group(2) else int(m.group(2)) if m else 1)
    R['r3_runs']=r3
    # idle tail: from the run's close (or last non-wait tool end) to the agent wall end
    waits=[c for c in main if c['name'] in('ScheduleWakeup','CronCreate')]
    last_work=max(c['end'] or c['start'] for c in main if c['name'] not in('ScheduleWakeup','CronCreate','Monitor'))
    tail=max(0,end-last_work) if waits and waits[-1]['start']>=last_work-120 else 0
    R['tail_idle']=round(tail/60,1)
    # 1. gate budget: stop at the second failing R2 (later R2 calls mean the 2nd failed)
    budget=[]
    if len(r2)>2: budget.append((r2[1]['end'],min(end,last_work)))
    R['budget_cut']=round(total(budget)/60,1)
    # 2. R round: R2 || R3, one fix round. Saved: R3 gate time that ran after R2_1 serially (overlaps R2_1)
    r3c=[c for c in main if c['name']=='Bash' and 'cognitive_complexity_gate' in c['input'].get('command','')]
    par=min(sum(dur(c) for c in r3c), dur(r2[0])) if r2 and r3c else 0
    R['R_parallel']=round(par/60,1)
    # 3. bounded waits: polling (sleep loops, Monitor) beyond 10 min per wait chain; ScheduleWakeup before close
    chains=[];cur=None
    for c in sorted([c for c in cs if c['end'] and ((c['name']=='Bash' and WAIT.search(c['input'].get('command',''))) or c['name']=='Monitor')],key=lambda c:c['start']):
        if cur and c['start']-cur[1]<180: cur[1]=max(cur[1],c['end'])
        else:
            cur=[c['start'],c['end']]; chains.append(cur)
    bounded=[(a+600,b) for a,b in chains if b-a>600]
    R['wait_beyond_10m']=round(total(bounded)/60,1)
    # 4. reuse: an identical project command on an unchanged tree (no write between, same thread)
    reuse=[]
    for th in set(c['parent'] for c in cs):
        seq=[c for c in cs if c['parent']==th]; seen={}
        for c in seq:
            if c['name'] in('Edit','Write','MultiEdit','NotebookEdit'): seen={}; continue
            if c['name']!='Bash': continue
            cmd=c['input'].get('command','')
            if WRITE.search(cmd): seen={}; continue
            if PROJECT.search(cmd) and not WAIT.search(cmd):
                k=re.sub(r'\s+',' ',cmd)
                if k in seen and c['end']: reuse.append((c['start'],c['end']))
                seen[k]=1
    R['reuse']=round(total(reuse)/60,1)
    # orchestrator project commands (main thread)
    orch=[c for c in main if c['name']=='Bash' and PROJECT.search(c['input'].get('command','')) and 'SKILL_ROOT' not in c['input'].get('command','')[:40]]
    R['orch_cmd_min']=round(sum(dur(c) for c in orch)/60,1)
    R['e1_in_main']=first('E1') is None
    removed=merge(budget+bounded+reuse+([(last_work,end)] if tail else []))
    rem=total(removed)/60+par/60+(Pb-Pa if Pa<Pb else 0)
    R['before']=round(rec['timing']['agent_wall_seconds']/60,1)
    R['after']=round(R['before']-rem,1)
    R['R_before']=round(((close or last_work)-r1['start'])/60,1) if r1 else None
    rb=[(a,b) for a,b in removed if r1 and b>r1['start']]
    R['R_after']=round(R['R_before']-total([(max(a,r1['start']),b) for a,b in rb if b<= (close or last_work)+1])/60-par/60,1) if r1 else None
    task=os.path.basename(path)[:2]
    R['slo']=round(1.25*BASIS[task]/60,1)
    return R
if __name__=='__main__':
    rows=[]
    for f in sorted(glob.glob(sys.argv[1]+'/*.jsonl')):
        rec=json.load(open(f[:-6]+'.record.json'))
        r=analyse(f,rec); r['run']=os.path.basename(f)[:-6].replace('-cadence-haiku',''); rows.append(r)
    keys=['run','before','after','slo','P_before','P_after','R_before','R_after','r2_calls','r3_runs','budget_cut','R_parallel','wait_beyond_10m','reuse','tail_idle','orch_cmd_min','e1_in_main']
    print('\t'.join(keys))
    for r in rows: print('\t'.join(str(r[k]) for k in keys))
    json.dump(rows,open(sys.argv[2],'w'),indent=1)
