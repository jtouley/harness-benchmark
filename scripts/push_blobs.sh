#!/usr/bin/env bash
# Push one run's new blobs to the runs-store branch, safe against other runs pushing at the same time.
#
#   scripts/push_blobs.sh <runs-store checkout> <run-id> [attempts]
#
# The blobs are content-addressed files under blobs/ that the driver wrote into the checkout (untracked), so two
# runs never write the same path with different bytes. Each attempt fetches the branch's current tip, puts this
# run's files on it, commits and pushes: a push that loses a race to another run is retried on the new tip, never
# rebased. After the push every one of the run's blobs is checked on the remote tip; exit 1 if one is missing
# (batch 2026-10-24-shapes: parallel runs got "HTTP 403" and "rejected non-fast-forward" on this push).
set -euo pipefail

STORE=$1
RID=$2
ATTEMPTS=${3:-8}
say() { printf '%s push_blobs %s: %s\n' "$(date -u +%FT%TZ)" "$RID" "$*" >&2; }

mapfile -t FILES < <(git -C "$STORE" ls-files --others --exclude-standard -- blobs/)
if [ "${#FILES[@]}" -eq 0 ]; then say "no new blobs"; exit 0; fi
HOLD=$(mktemp -d)
trap 'rm -rf "$HOLD"' EXIT
for f in "${FILES[@]}"; do mkdir -p "$HOLD/$(dirname "$f")"; cp -p "$STORE/$f" "$HOLD/$f"; done
say "${#FILES[@]} new blob(s)"

pushed=0
for i in $(seq 1 "$ATTEMPTS"); do
  if git -C "$STORE" fetch -q --depth 1 origin runs-store; then
    git -C "$STORE" reset -q --hard FETCH_HEAD
    for f in "${FILES[@]}"; do mkdir -p "$STORE/$(dirname "$f")"; cp -p "$HOLD/$f" "$STORE/$f"; done
    git -C "$STORE" add -- "${FILES[@]}"
    if git -C "$STORE" diff --cached --quiet; then pushed=1; break; fi   # every blob is already there
    git -C "$STORE" commit -q -m "blobs: $RID"
    if git -C "$STORE" push -q origin HEAD:runs-store; then pushed=1; break; fi
  fi
  say "attempt $i of $ATTEMPTS failed; retrying on the branch's new tip"
  sleep $(( ((2 ** (i < 5 ? i : 5)) + RANDOM % 3) * ${PUSH_BLOBS_BACKOFF:-1} ))   # PUSH_BLOBS_BACKOFF=0 in tests
done
[ "$pushed" = 1 ] || { say "runs-store push failed $ATTEMPTS times"; exit 1; }

git -C "$STORE" fetch -q --depth 1 origin runs-store
missing=0
for f in "${FILES[@]}"; do
  git -C "$STORE" cat-file -e "FETCH_HEAD:$f" 2>/dev/null || { say "missing on runs-store: $f"; missing=1; }
done
[ "$missing" = 0 ] || exit 1
say "every blob is on runs-store ($(git -C "$STORE" rev-parse --short FETCH_HEAD))"
