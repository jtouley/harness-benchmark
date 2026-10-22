#!/usr/bin/env bash
# Runs the cadence-core trials one at a time (they share localhost:8099). Touch STOP to end after the current one.
S=/tmp/claude-0/-home-user/5b20bc6c-3f91-5511-8000-71d5898a937e/scratchpad
export PIPE_ROOT=$S/pipe/2026-10-21
mkdir -p $PIPE_ROOT
for n in 1 2 3; do for t in P1 P2; do
  [ -e $S/STOP ] && { echo "$(date -u +%FT%TZ) stopped by STOP file" >>$S/queue.log; exit 0; }
  run=$t-cadence-core-haiku-$n
  [ -e $PIPE_ROOT/$run ] && continue
  echo "$(date -u +%FT%TZ) start $run" >>$S/queue.log
  bash $S/host_trial.sh $t $run >>$S/queue.log 2>&1
  echo "$(date -u +%FT%TZ) end $run exit $?" >>$S/queue.log
  started=$(sed -n 's/^\([^ ]*\) agent start$/\1/p' $PIPE_ROOT/$run/driver.log)
  printf '{"task": "%s", "mode": "agent", "model": "claude-haiku-5-5", "arm": "cadence-core", "harness": true,\n "backstop_seconds": 86400, "backstop_source": "default", "image": "host", "grader_deadline": 600,\n "replay_seed": 0, "started_at": "%s"}\n' $t "$started" >$PIPE_ROOT/$run/trial.json
done; done
echo "$(date -u +%FT%TZ) queue done" >>$S/queue.log
