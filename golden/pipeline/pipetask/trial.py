"""Run a delivered pipeline the way the analysts would, then grade it.

    python -m pipetask.trial --repo REPO --key key/answer_key.json \
        --capture data/capture/recentchange.jsonl.gz [--seed 1] [--port 8099]

1. `make build`, then a digest of every published mart; `make build` again and compare (rule: running
   it twice must not change any output; traps B7, D2).
2. The replay server starts with the grading seed on the spec's port.
3. `make stream DURATION=<first>`, then `make stream DURATION=<second>`: the consumer is stopped and
   started once while the stream is still running (F6), and the scheduled faults F1 to F5 happen.
4. The checks ([grade]).

Prints one JSON object. `reward` is the share of the seven checks that pass, and 0 when a second build
changed an output.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import duckdb

from . import grade, replay


def run(cmd: list[str], cwd: Path, timeout: float, log: Path) -> dict:
    t0 = time.monotonic()
    with log.open("w", encoding="utf-8") as fh:
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            rc = proc.wait()
            fh.write(f"\n[trial] killed after {timeout} s\n")
    return {"cmd": " ".join(cmd), "exit": rc, "seconds": round(time.monotonic() - t0, 1), "log": log.name}


def mart_digests(repo: Path) -> dict[str, str]:
    """An order-independent digest of each published mart's rows."""
    out = {}
    marts = repo / "out" / "marts"
    if not marts.is_dir():
        return out
    con = duckdb.connect()
    for folder in sorted(p for p in marts.iterdir() if p.is_dir() and any(p.rglob("*.parquet"))):
        glob = (folder / "**" / "*.parquet").as_posix()
        row = con.execute(f"select count(*), coalesce(md5(string_agg(h, '' order by h)), '') from "
                          f"(select md5(t::varchar) as h from read_parquet('{glob}', union_by_name=true) t)").fetchone()
        out[folder.name] = f"{row[0]}:{row[1]}"
    return out


def trial(repo: Path, key: dict, capture: Path, *, seed: int, port: int, speed: float,
          durations: tuple[int, int], build_timeout: float, logs: Path) -> dict:
    logs.mkdir(parents=True, exist_ok=True)
    result: dict = {"seed": seed, "durations": list(durations), "speed": speed}
    first = run(["make", "build"], repo, build_timeout, logs / "build-1.log")
    digests1 = mart_digests(repo)
    second = run(["make", "build"], repo, build_timeout, logs / "build-2.log")
    digests2 = mart_digests(repo)
    changed = sorted(k for k in set(digests1) | set(digests2) if digests1.get(k) != digests2.get(k))
    result["build"] = [first, second]
    result["idempotent"] = first["exit"] == 0 and second["exit"] == 0 and not changed and bool(digests1)
    result["changed_by_second_build"] = changed

    server = replay.serve(capture, seed, port, speed)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result["stream"] = [
            run(["make", "stream", f"DURATION={d}"], repo, d + 300, logs / f"stream-{i}.log")
            for i, d in enumerate(durations, 1)
        ]
    finally:
        server.shutdown()
        server.server_close()

    graded = grade.grade(repo, key)
    result.update(graded)
    result["reward"] = round(graded["passed"] / graded["total"], 4) if result["idempotent"] else 0.0
    return result


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Build, stream and grade a delivered pipeline.")
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--key", type=Path, required=True)
    ap.add_argument("--capture", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--speed", type=float, default=60.0)
    ap.add_argument("--durations", default="30,90", help="the two make stream DURATION values, seconds")
    ap.add_argument("--build-timeout", type=float, default=1800)
    ap.add_argument("--logs", type=Path, default=None)
    args = ap.parse_args(argv)
    key = json.loads(args.key.read_text(encoding="utf-8"))
    if key["stream"]["seed"] != args.seed:
        sys.exit(f"the key was computed for seed {key['stream']['seed']}, not {args.seed}")
    d1, d2 = (int(x) for x in args.durations.split(","))
    result = trial(args.repo.resolve(), key, args.capture.resolve(), seed=args.seed, port=args.port,
                   speed=args.speed, durations=(d1, d2), build_timeout=args.build_timeout,
                   logs=(args.logs or args.repo / "_grade_logs").resolve())
    json.dump(result, sys.stdout, indent=1, sort_keys=True, default=str)
    print()


if __name__ == "__main__":
    main()
