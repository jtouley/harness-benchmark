#!/usr/bin/env bash
# Round 2, one trial at a time; stop if Docker is down before a job starts.
set -u
cd "$(dirname "$0")"
run() {
  docker info >/dev/null 2>&1 || { echo "$(date) docker down before $1; stopping"; exit 1; }
  harbor run -p "$2" -a claude-code -m "$3" -o jobs --job-name "$1" ${4:-} -n 1 --delete -y -q
  echo "$(date) finished $1"
}
run opus-hard3-r2 hard3 anthropic/claude-opus-5-5 "-k 3"
run sonnet-sample20-r1 sample20 anthropic/claude-sonnet-5-5
run haiku-sample20-r1 sample20 anthropic/claude-haiku-5-5
echo "$(date) ROUND2 DONE"
