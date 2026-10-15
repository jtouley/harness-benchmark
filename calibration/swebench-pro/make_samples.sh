#!/usr/bin/env bash
# Download SWE-bench Pro task definitions from the Harbor registry and build the sample folders
# (symlinks) from the committed lists. sample20.txt was drawn with random.seed(20261013) from the
# 265 Python tasks (ansible, openlibrary, qutebrowser) excluding openlibrary-92db3454 (the feasibility task).
set -euo pipefail
cd "$(dirname "$0")"
[ -d tasks/swe-bench-pro ] || harbor datasets download scale-ai/swe-bench-pro -o tasks
for list in sample20 hard3; do
  mkdir -p "$list"
  while read -r name; do
    [ -n "$name" ] && ln -sfn "$PWD/tasks/swe-bench-pro/$name" "$list/$name"
  done < "$list.txt"
done
echo "samples ready"
