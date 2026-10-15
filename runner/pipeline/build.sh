#!/usr/bin/env bash
# Build the pipeline trial images on top of the runner image. The build context holds only the three
# task skeletons and this folder's toolchain files: nothing else under golden/pipeline/ goes in.
#
#   runner/pipeline/build.sh [py|p3|all]     -> harness-benchmark/runner-pipeline:py, :p3
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
targets=${1:-all}
[ "$targets" = all ] && targets="py p3"
ctx=$(mktemp -d)
trap 'rm -rf "$ctx"' EXIT
for t in P1 P2 P3; do
  mkdir -p "$ctx/$t"
  rsync -a --exclude .venv --exclude target --exclude out --exclude lake "$root/golden/pipeline/$t/skeleton" "$ctx/$t/"
done
cp "$here/Dockerfile" "$here"/toolchain-*.env "$ctx/"
docker build -q -t "${HB_RUNNER_IMAGE:-harness-benchmark/runner:local}" "$root/runner" >/dev/null
for t in $targets; do
  docker build --build-arg BASE="${HB_RUNNER_IMAGE:-harness-benchmark/runner:local}" --target "$t" \
    -t "harness-benchmark/runner-pipeline:$t" "$ctx"
done
