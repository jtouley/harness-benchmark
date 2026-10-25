"""Per block subagent: work done after it first wrote its document."""
import sys,os,re,glob,json,fnmatch
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from tl import load
from replay import blk
GL=("vibetest/*.md","reviews/plan_*.md","adversarial/*.md","benchmarks/*.json","prs/reviews/*.md","reviews/pr_*.md")
def art(p):
    if '/.context/' not in p and not p.startswith('.context/'): return False
    rel=p.split('.context/',1)[1]
    return any(fnmatch.fnmatch(rel,g) for g in GL)
SCRIPT=re.compile(r'^\s*(?:[A-Z_]+=\S+\s+)*(?:export [^;&]+[;&]+\s*)?python3?\s+\S*scripts/[\w_]+\.py')
def run(f):
    ev,cs=load(f); out=[]
    agents=[c for c in cs if c['name'] in('Agent','Task')]
    for a in agents:
        kids=sorted([c for c in cs if c['parent']==a['id']],key=lambda c:c['start'])
        w=next((c for c in kids if c['name'] in('Write','Edit','MultiEdit') and art(str(c['input'].get('file_path','')))),None)
        if not w or not a['end']: continue
        doc=w['input']['file_path']
        after=[c for c in kids if c['start']>w['start']]
        bad=[c for c in after if not ((c['name'] in('Write','Edit','MultiEdit','Read') and c['input'].get('file_path')==doc) or (c['name']=='Bash' and SCRIPT.match(c['input'].get('command',''))))]
        if not bad: continue
        cut=bad[0]['start']
        out.append(dict(block=blk(a),after_min=round((a['end']-cut)/60,1),calls=len(bad),first=(bad[0]['name']+' '+str(bad[0]['input'].get('command') or bad[0]['input'].get('file_path'))[:80])))
    return out
if __name__=='__main__':
    tot=0
    for f in sorted(glob.glob(sys.argv[1]+'/*.jsonl')):
        r=run(f); s=sum(x['after_min'] for x in r); tot+=s
        print(os.path.basename(f)[:-6], round(s,1), [(x['block'],x['after_min'],x['calls']) for x in r])
        for x in r: print('     ',x['block'],x['first'])
    print('total',round(tot,1))
