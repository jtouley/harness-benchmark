"""One build per tree: build each prepared review tree once, so parallel reviewers never contend for builds.

    python -m revieweval.build --work WORK [CASE ...]

This is the operator's step, not an agent's. The trees are built one at a time, because the dev replay listens
on the spec's port (8099) and a second build would contend for it. For each WORK/trees/<case>/repo:

1. `uv sync --frozen` in a copy at WORK/built/<case>/repo (the `review` branch).
2. The dev replay (seed 0, as scripts/host_trial.py runs it for the agent) on 127.0.0.1:8099. The step stops
   with an error when the port is taken: it never shares a replay with another process.
3. `make build`, then `make stream DURATION=<seconds>`, each with a timeout.

WORK/built/<case>/build.log is what the reviewers get: the commands, their output and exit codes.
WORK/built/<case>/replay.log is harness material (the replay's own log) and is never given to a reviewer.
WORK/built/<case>/build.json has the exit codes and durations.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GP = ROOT / "golden" / "pipeline"
PORT = 8099


def port_free(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def run_step(argv: list[str], cwd: Path, log, timeout: int) -> dict:
    log.write(f"$ {' '.join(argv)}\n")
    log.flush()
    start = time.monotonic()
    try:
        code = subprocess.run(argv, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        code = "timeout"
    took = round(time.monotonic() - start, 1)
    log.write(f"[exit {code} after {took} s]\n\n")
    log.flush()
    return {"argv": argv, "exit": code, "seconds": took}


def build(work: Path, case: str, duration: int, timeout: int) -> dict:
    src = work / "trees" / case / "repo"
    dest = work / "built" / case
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    subprocess.run(["git", "clone", "-q", "-b", "review", str(src), str(dest / "repo")], check=True)
    repo = dest / "repo"
    if not port_free(PORT):
        raise SystemExit(f"port {PORT} is taken: stop the other replay first (builds never share one)")
    steps = []
    with open(dest / "build.log", "w") as log, open(dest / "replay.log", "w") as rlog:
        steps.append(run_step(["uv", "sync", "--frozen"], repo, log, timeout))
        replay = subprocess.Popen([sys.executable, "-m", "pipetask.replay", "--capture",
                                   "data/capture/recentchange.jsonl.gz", "--seed", "0", "--port", str(PORT)],
                                  cwd=GP, stdout=rlog, stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                if not port_free(PORT):
                    break
                time.sleep(0.2)
            steps.append(run_step(["make", "build"], repo, log, timeout))
            steps.append(run_step(["make", "stream", f"DURATION={duration}"], repo, log, duration + timeout))
        finally:
            replay.terminate()
            replay.wait(timeout=30)
    info = {"case": case, "steps": steps, "duration": duration}
    (dest / "build.json").write_text(json.dumps(info, indent=1) + "\n")
    return info


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--duration", type=int, default=90)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("cases", nargs="*")
    args = ap.parse_args(argv)
    cases = args.cases or sorted(p.name for p in (args.work / "trees").iterdir())
    os.environ.pop("VIRTUAL_ENV", None)
    for case in cases:
        info = build(args.work, case, args.duration, args.timeout)
        print(case, [s["exit"] for s in info["steps"]])


if __name__ == "__main__":
    main()
