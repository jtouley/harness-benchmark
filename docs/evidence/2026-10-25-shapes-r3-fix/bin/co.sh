#!/bin/bash
# co.sh <r3dir> <id>: a worktree of the run's graded commit at co/<id>, branch cadence/spec at the graded commit
set -e
cd "$1"; id=$2
rm -rf co/$id; git clone -q "$id.git" co/$id
cd co/$id
git fetch -q origin "+refs/graded/$id:refs/remotes/origin/graded" 2>/dev/null || true
git checkout -q -B cadence/spec origin/graded
