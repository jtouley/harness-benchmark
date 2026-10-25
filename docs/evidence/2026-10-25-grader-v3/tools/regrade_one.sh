#!/bin/bash
# regrade_one.sh RUN_ID REPO OUTDIR V3ROOT
# In a private network namespace (loopback only; no external network, own port 8099):
#  1. the pinned grader (c344bea, golden/pipeline/pipetask tree 8a0977e) grades a copy of REPO with host_trial.grade
#     (from the repository root, --snapshot-worktree, seed 1): OUTDIR/pinned.json
#  2. on the marts that trial left, pipetask.grade at the pinned tree and at V3ROOT each grade again, from the repo
#     root: OUTDIR/pinned-marts.json, OUTDIR/v3-marts.json
set -u
S=/tmp/claude-0/-home-user/fd6221f8-f79d-5dc4-b0f6-aa7efcbaf9ac/scratchpad
id=$1; src=$2; out=$3; v3=$4
PIN=$S/pin3; PY=$S/g3/.venv/bin/python
mkdir -p "$out"; rm -rf "$out/repo"; cp -a "$src" "$out/repo"
export UV_OFFLINE=1
unshare -n $PY -I $S/lo_up.py bash -c "
cd '$out/repo' && $PY -c \"
import sys; from pathlib import Path
sys.path.insert(0,'$PIN/scripts')
import host_trial
o=Path('$out'); rc=host_trial.grade(Path('$out/repo'), o)
(o/'grade.json').rename(o/'pinned.json'); print('trial rc', rc)\"
for which in pinned:$PIN v3:$v3; do n=\${which%%:*}; root=\${which#*:}
  PYTHONPATH=\$root/golden/pipeline $PY -m pipetask.grade --repo . --key \$root/golden/pipeline/key/answer_key.json > '$out/'\$n-marts.json 2>'$out/'\$n-marts.err
done"
$PY -c "
import json;d=json.load(open('$out/pinned.json'))
p=json.load(open('$out/pinned-marts.json')); v=json.load(open('$out/v3-marts.json'))
f=lambda r:''.join('P' if r['checks'].get(str(n),{}).get('pass') else '.' for n in range(1,8))
print('$id', 'trial', d.get('passed'), d.get('reward'), 'idem', d.get('idempotent'), 'stream', d.get('stream_ok'), d.get('error'), f(d) if 'checks' in d else '-', 'pinned-marts', f(p), 'v3', f(v))"
rm -rf "$out/repo/.venv" "$out/repo/lake"
