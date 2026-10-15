#!/bin/sh
# A P3 trial in the pinned toolchain container: assemble the starting repository, optionally overlay
# the reference and run its ScalaTest suites, then build, stream and grade it (pipetask.trial).
# Nothing runs on the host but docker; the JVM, sbt, pip and coursier caches live in the docker volume
# hb-p3-cache. The repository is built inside the container's own file system, not a bind mount.
#
#   golden/pipeline/P3/image/trial.sh OUT [--with-reference] [--scalatest]
#
# Writes OUT/result.json (the grader's JSON) and OUT/logs/ (build, stream and test logs).
set -eu
out=$1; shift
reference=""; scalatest=""
for arg in "$@"; do
  case $arg in
    --with-reference) reference="--with-reference" ;;
    --scalatest) scalatest=1 ;;
    *) echo "unknown option $arg" >&2; exit 2 ;;
  esac
done
here=$(cd "$(dirname "$0")" && pwd)
golden=$(cd "$here/../.." && pwd)
mkdir -p "$out/logs"
out=$(cd "$out" && pwd)
docker build -q -t hb-pipeline-p3 "$here" >/dev/null
docker volume create hb-p3-cache >/dev/null
exec docker run --rm -e PYTHONDONTWRITEBYTECODE=1 -e SCALATEST="$scalatest" \
  -v hb-p3-cache:/cache -v "$golden:/golden:ro" -v "$out:/out" -w /golden hb-pipeline-p3 sh -euc "
    python3 -m pipetask.assemble P3 --out /work/repo $reference >/dev/null
    if [ -n \"\$SCALATEST\" ]; then (cd /work/repo && make test) > /out/logs/scalatest.log 2>&1; fi
    /opt/grader/bin/python -m pipetask.trial --repo /work/repo --key key/answer_key.json \
      --capture data/capture/recentchange.jsonl.gz --logs /out/logs > /out/result.json
  "
