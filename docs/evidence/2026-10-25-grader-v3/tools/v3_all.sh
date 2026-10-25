#!/bin/bash
# Grade every regraded tree's marts (left by the pinned trial) with the grader at $1 (default g3), from the repo root.
S=/tmp/claude-0/-home-user/fd6221f8-f79d-5dc4-b0f6-aa7efcbaf9ac/scratchpad
ROOT=${1:-$S/g3}; OUT=${2:-v3-marts.json}
for d in $S/w3/*/g; do id=$(basename $(dirname $d))
  (cd $d/repo && PYTHONPATH=$ROOT/golden/pipeline $S/g3/.venv/bin/python -m pipetask.grade --repo . --key $ROOT/golden/pipeline/key/answer_key.json > $d/$OUT 2>$d/$OUT.err)
  $S/g3/.venv/bin/python -c "
import json,sys
p=json.load(open('$d/pinned.json')); v=json.load(open('$d/$OUT'))
f=lambda r:''.join('P' if r['checks'].get(str(n),{}).get('pass') else '.' for n in range(1,8))
print(f'{\"$id\":40s}', f(p), f(v), p.get('stream_ok'), p.get('idempotent'))"
done
