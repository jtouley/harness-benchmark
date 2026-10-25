#!/bin/bash
# replay_gates.sh <cadence> <tree>: the P1 and P4 gates (--check) on one stored tree
cad=$1; tree=$2
cd "$tree"
for g in plan_create_gate plan_update_gate; do
  out=$(CADENCE_HOME=$cad timeout 120 python3 $cad/scripts/$g.py --check 2>&1); code=$?
  echo "$g exit=$code"; echo "$out" | sed "s#$tree/##g" | cut -c1-330 | head -12
done
