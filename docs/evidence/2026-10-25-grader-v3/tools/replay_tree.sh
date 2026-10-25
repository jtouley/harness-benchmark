#!/bin/bash
# replay_tree.sh RUN_ID WORKDIR : WORKDIR holds tree.bundle and transcript.jsonl; writes WORKDIR/rebuilt (the tree)
# and WORKDIR/replay.jsonl. Private mount + network namespace: /home is a tmpfs holding only the run's original
# repository path (bound to WORKDIR/rebuilt), /tmp is a fresh tmpfs, and there is no external network.
set -eu
S=/tmp/claude-0/-home-user/fd6221f8-f79d-5dc4-b0f6-aa7efcbaf9ac/scratchpad
id=$1; W=$2
rm -rf "$W/rebuilt"; git clone -q "$W/tree.bundle" "$W/rebuilt"
git -C "$W/rebuilt" remote remove origin
ORIG=/home/user/bf/runs/$id/repo
unshare -mn --propagation private bash -c "
set -e
mount -t tmpfs tmpfs /home
mkdir -p $ORIG /home/.replay
mount --bind '$W/rebuilt' $ORIG
cp '$S/v3tools3/replay_transcript.py' '$W/transcript.jsonl' /home/.replay/
mount --bind '$W' /mnt
mount -t tmpfs tmpfs /tmp
cd $ORIG && python3 -I /home/.replay/replay_transcript.py /home/.replay/transcript.jsonl $ORIG /mnt/replay.jsonl
"
