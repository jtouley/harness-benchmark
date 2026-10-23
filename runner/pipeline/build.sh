#!/usr/bin/env bash
# Build the pipeline trial images on top of the runner image. The build context holds only the four
# task skeletons and this folder's toolchain files: nothing else under golden/pipeline/ goes in.
#
#   runner/pipeline/build.sh [py|p3|all]     -> harness-benchmark/runner-pipeline:py, :p3
#
# Behind a TLS-terminating proxy, set HB_BUILD_CA to its CA file (and HTTPS_PROXY): the builds then run
# on the host network with the CA as a build secret (runner/build-net.sh), so it is in no layer.
# HTTPS_PROXY must then be http://HOST:PORT, with no user, password or path: a credential in the URL would
# reach every build container as a build argument. Any other value is refused before anything runs, and
# the URL is never printed (the same rule as run_trial.sh --auth proxy).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
targets=${1:-all}
[ "$targets" = all ] && targets="py p3"
net=()
if [ -n "${HB_BUILD_CA:-}" ]; then
  [ -f "$HB_BUILD_CA" ] || { echo "build.sh: HB_BUILD_CA is not a file: $HB_BUILD_CA" >&2; exit 2; }
  proxy_url="${HTTPS_PROXY:-${https_proxy:-}}"
  [ -n "$proxy_url" ] || { echo "build.sh: HB_BUILD_CA needs HTTPS_PROXY (http://HOST:PORT)" >&2; exit 2; }
  [[ "$proxy_url" =~ ^http://([A-Za-z0-9.-]+):([0-9]+)/?$ ]] ||
    { echo "build.sh: HTTPS_PROXY must be http://HOST:PORT only (no user, password or path); not started" >&2; exit 2; }
  net=(--network host --secret "id=ca,src=$HB_BUILD_CA" --build-arg HTTPS_PROXY="$proxy_url" --build-arg HTTP_PROXY="$proxy_url")
  unset proxy_url
fi
ctx=$(mktemp -d)
trap 'rm -rf "$ctx"' EXIT
for t in P1 P2 P3 P4; do
  mkdir -p "$ctx/$t"
  rsync -a --exclude .venv --exclude target --exclude out --exclude lake "$root/golden/pipeline/$t/skeleton" "$ctx/$t/"
done
cp "$here/Dockerfile" "$here"/toolchain-*.env "$ctx/"
docker build "${net[@]}" -q -t "${HB_RUNNER_IMAGE:-harness-benchmark/runner:local}" "$root/runner" >/dev/null
for t in $targets; do
  docker build "${net[@]}" --build-arg BASE="${HB_RUNNER_IMAGE:-harness-benchmark/runner:local}" --target "$t" \
    -t "harness-benchmark/runner-pipeline:$t" "$ctx"
done
