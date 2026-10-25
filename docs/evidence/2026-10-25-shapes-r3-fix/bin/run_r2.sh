#!/bin/bash
# run_r2.sh <id>: the stack's verify_tree.py on one stored shapes-r2 tree, with the branch's Cadence
id=$1; short=$(echo $id | sed 's/20261024-//; s/-cadence-haiku//')
cd $SCRATCH/r2 && UV_OFFLINE=1 TMPDIR=$SCRATCH/tmp1 timeout 2400 python3 -I $SCRATCH/bin/verify_tree.py $SCRATCH/ci $SCRATCH/r2/$id 400 $SCRATCH/ev/verify/$short.json > $SCRATCH/ev/verify/$short.log 2>&1
echo "$id exit=$?"
