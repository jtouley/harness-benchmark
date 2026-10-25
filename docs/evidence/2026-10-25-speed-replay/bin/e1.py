import sys,re,json,collections
sys.path.insert(0,sys.argv[0].rsplit('/',1)[0])
from tl import load,label
def blk(c):
    if c['name'] not in('Agent','Task'): return None
    p=(c['input'].get('prompt') or '').split('\n')[0]
    m=re.match(r'/(?:cadence:)?([\w-]+)',p)
    if m: return m.group(1)
    return 'freeform'
def cat(cmd):
    s=cmd
    if re.search(r'\bsleep\b|kill -0|while .*sleep',s): return 'wait-loop'
    if 'make stream' in s or 'stream' in s and 'make' in s: return 'make-stream'
    if 'make build' in s or 'dbt ' in s: return 'build/dbt'
    if 'pytest' in s or 'unittest' in s: return 'tests'
    if 'cognitive_complexity_gate' in s: return 'R3-gate'
    if 'ledger_verify' in s: return 'ledger_verify'
    if 'clean_checkout' in s or 'draft_pr_gate' in s: return 'E4-gate'
    if re.search(r'scripts/\w+\.py',s): return 'cadence-script'
    return 'other-cmd'
def run(path):
    ev,cs=load(path)
    t0=min(c['start'] for c in cs)
    main=[c for c in cs if not c['parent']]
    byid={c['id']:c for c in cs}
    # E1 window
    e1=[c for c in main if blk(c)=='spec-driven']
    p9=[c for c in main if c['name']=='Bash' and 'entry_invariant' in c['input'].get('command','')]
    e4=[c for c in main if blk(c)=='commit-push-pr']
    pu=[c for c in main if blk(c)=='plan-update']
    if e1: s,e=e1[0]['start'],e1[0]['end']; where='agent'
    else:
        s=max(c['end'] for c in pu); e=e4[0]['start'] if e4 else max(c['start'] for c in main); where='main'
    inwin=[c for c in cs if c['end'] and s<=c['start']<e and c['name'] in('Bash','Monitor')]
    # top-level-ish durations of commands inside E1 (any depth)
    agg=collections.Counter()
    for c in inwin:
        if c['name']=='Monitor': agg['wait-loop']+=c['end']-c['start']; continue
        agg[cat(c['input'].get('command',''))]+=c['end']-c['start']
    return dict(where=where,e1=(e-s)/60,agg={k:round(v/60,1) for k,v in agg.most_common()})
if __name__=='__main__':
    for f in sys.argv[1:]:
        r=run(f); print(f.split('/')[-1][:24], r['where'], round(r['e1'],1), r['agg'])
