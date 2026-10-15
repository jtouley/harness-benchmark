"""Run a delivered pipeline the way the analysts would, then grade it.

    python -m pipetask.trial --repo REPO --key key/answer_key.json \
        --capture data/capture/recentchange.jsonl.gz [--seed 1] [--port 8099]

0. The repository is reset to what was committed: `git clean -ffdx` removes every untracked and
   ignored file, then `out/` and `lake/` are removed even when committed. Outputs and consumer state
   left from development are never graded (a repository that is not a git checkout is not graded).
1. `make build`, then a digest of every published mart; `make build` again and compare (rule: running
   it twice must not change any output; traps B7, D2).
2. The replay server starts with the grading seed on the spec's port.
3. `make stream DURATION=<first>`, then `make stream DURATION=<second>`: the consumer is stopped and
   started once while the stream is still running (F6), and the scheduled faults F1 to F5 happen.
4. The checks ([grade]).

How the candidate's `make` runs (the runner passes these; golden/pipeline/README.md, runner wiring):
`--make-env-file` gives it exactly the variables of that file (the trial image's toolchain) plus a
fresh, empty HOME that all four runs share and that is removed afterwards, so state kept under HOME in
development (dlt's `~/.dlt/pipelines/`) is not graded. `--make-user` runs it as that user (`setpriv`;
the grader must run as root), so the build cannot read the grader's archive or temporary files.
`--stream-grace` is how long a `make stream` run may take beyond its DURATION before it is killed.

Prints one JSON object. `reward` is the share of the seven checks that pass, and 0 when a second build
changed an output, no `make stream` run exited 0, or the consumer never read the grading stream up to
the late batch (F4). The stream answers do not depend on the seed, so marts copied in from development
would otherwise score without any consumer. A trial that cannot run (no git checkout, the port
taken) prints `{"error": ..., "reward": 0.0}`.
"""

from __future__ import annotations

import argparse
import json
import os
import pwd
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import duckdb

from . import grade, replay
from .oracle import sql_string

OUTPUTS = ("out", "lake")  # the spec's output folders: removed even when committed


def run(cmd: list[str], cwd: Path, timeout: float, log: Path, *, env: dict[str, str] | None = None,
        prefix: tuple[str, ...] = ()) -> dict:
    t0 = time.monotonic()
    with log.open("w", encoding="utf-8") as fh:
        proc = subprocess.Popen([*prefix, *cmd], cwd=cwd, env=env, stdout=fh, stderr=subprocess.STDOUT,
                                start_new_session=True)
        try:
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            rc = proc.wait()
            fh.write(f"\n[trial] killed after {timeout} s\n")
    return {"cmd": " ".join(cmd), "exit": rc, "seconds": round(time.monotonic() - t0, 1), "log": log.name}


ENV_LINE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)")


def read_env_file(path: Path) -> dict[str, str]:
    """NAME=VALUE lines (no quoting); blank lines and `#` comments are skipped."""
    env = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = ENV_LINE.fullmatch(line)
        if not m:
            raise ValueError(f"{path}: not a NAME=VALUE line: {line!r}")
        env[m.group(1)] = m.group(2)
    return env


class MakeRunner:
    """Runs the candidate's make: as `user` (root required), with `env` and a fresh HOME, or as the
    grader does when both are None."""

    def __init__(self, env: dict[str, str] | None, user: str | None):
        self.user, self.home, self.env, self.prefix = user, None, None, ()
        if env is None and user is None:
            return
        self.home = Path(tempfile.mkdtemp(prefix="hb-make-home-"))
        name = user or pwd.getpwuid(os.getuid()).pw_name
        self.env = {"PATH": "/usr/local/bin:/usr/bin:/bin", **(env or {}),
                    "HOME": str(self.home), "USER": name, "LOGNAME": name}
        if user:
            entry = pwd.getpwnam(user)
            os.chown(self.home, entry.pw_uid, entry.pw_gid)
            self.prefix = ("setpriv", f"--reuid={user}", f"--regid={user}", "--init-groups")

    def __call__(self, cmd: list[str], cwd: Path, timeout: float, log: Path) -> dict:
        return run(cmd, cwd, timeout, log, env=self.env, prefix=self.prefix)

    def close(self) -> None:
        if self.home is not None:
            shutil.rmtree(self.home, ignore_errors=True)


def mart_digests(repo: Path) -> dict[str, str]:
    """An order-independent digest of each published mart's rows."""
    out = {}
    marts = repo / "out" / "marts"
    if not marts.is_dir():
        return out
    con = duckdb.connect()
    for folder in sorted(p for p in marts.iterdir() if p.is_dir() and any(p.rglob("*.parquet"))):
        glob = sql_string((folder / "**" / "*.parquet").as_posix())
        row = con.execute(f"select count(*), coalesce(md5(string_agg(h, '' order by h)), '') from "
                          f"(select md5(t::varchar) as h from read_parquet({glob}, union_by_name=true) t)").fetchone()
        out[folder.name] = f"{row[0]}:{row[1]}"
    return out


def reset(repo: Path) -> str | None:
    """Back to the committed tree, minus the output folders. An error message, or None."""
    proc = subprocess.run(["git", "clean", "-ffdxq"], cwd=repo, capture_output=True, text=True)
    if proc.returncode != 0:
        return f"git clean failed, so outputs left from development could be graded: {proc.stderr.strip()}"
    for name in OUTPUTS:
        path = repo / name
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.exists():
            shutil.rmtree(path)
    return None


def reward(result: dict) -> float:
    """The share of checks that pass; 0 when a build changed an output or no stream run exited 0."""
    if not result["idempotent"] or not result["stream_ok"]:
        return 0.0
    return round(result["passed"] / result["total"], 4)


def trial(repo: Path, key: dict, capture: Path, *, seed: int, port: int, speed: float,
          durations: tuple[int, int], build_timeout: float, logs: Path, stream_grace: float = 300,
          make_env: dict[str, str] | None = None, make_user: str | None = None) -> dict:
    result: dict = {"seed": seed, "durations": list(durations), "speed": speed,
                    "build_timeout": build_timeout, "stream_grace": stream_grace,
                    "make_user": make_user, "make_fresh_home": make_env is not None or make_user is not None}
    if make_user and os.geteuid() != 0:
        return {**result, "error": "--make-user needs the grader to run as root", "reward": 0.0}
    error = reset(repo)
    if error:
        return {**result, "error": error, "reward": 0.0}
    logs.mkdir(parents=True, exist_ok=True)
    make = MakeRunner(make_env, make_user)
    try:
        return _trial(repo, key, capture, result, make, seed=seed, port=port, speed=speed,
                      durations=durations, build_timeout=build_timeout, logs=logs, stream_grace=stream_grace)
    finally:
        make.close()


def _trial(repo: Path, key: dict, capture: Path, result: dict, make: MakeRunner, *, seed: int, port: int,
           speed: float, durations: tuple[int, int], build_timeout: float, logs: Path,
           stream_grace: float) -> dict:
    first = make(["make", "build"], repo, build_timeout, logs / "build-1.log")
    digests1 = mart_digests(repo)
    second = make(["make", "build"], repo, build_timeout, logs / "build-2.log")
    digests2 = mart_digests(repo)
    changed = sorted(k for k in set(digests1) | set(digests2) if digests1.get(k) != digests2.get(k))
    result["build"] = [first, second]
    result["idempotent"] = first["exit"] == 0 and second["exit"] == 0 and not changed and bool(digests1)
    result["changed_by_second_build"] = changed

    try:
        server = replay.serve(capture, seed, port, speed)
    except OSError as exc:
        return {**result, "error": f"the replay server cannot listen on port {port} (is the dev server "
                                   f"still running?): {exc}", "reward": 0.0}
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result["stream"] = [
            make(["make", "stream", f"DURATION={d}"], repo, d + stream_grace, logs / f"stream-{i}.log")
            for i, d in enumerate(durations, 1)
        ]
    finally:
        server.shutdown()
        server.server_close()

    state = server.state
    result["stream_connections"] = state.connections
    result["stream_positions_served"] = state.served + 1
    result["stream_positions_needed"] = state.plan.late_insert_at + len(state.plan.late_batch)
    result["stream_ok"] = (any(s["exit"] == 0 for s in result["stream"]) and state.connections > 0
                           and result["stream_positions_served"] >= result["stream_positions_needed"])
    result.update(grade.grade(repo, key))
    result["reward"] = reward(result)
    return result


def main(argv: list[str] | None = None, key: dict | None = None) -> None:
    """`key`: the answer key already in memory (grader.pyz), in place of --key."""
    ap = argparse.ArgumentParser(description="Build, stream and grade a delivered pipeline.")
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--key", type=Path, required=key is None)
    ap.add_argument("--capture", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--speed", type=float, default=60.0)
    ap.add_argument("--durations", default="30,90", help="the two make stream DURATION values, seconds")
    ap.add_argument("--build-timeout", type=float, default=1800)
    ap.add_argument("--logs", type=Path, default=None)
    ap.add_argument("--stream-grace", type=float, default=300,
                    help="seconds a make stream run may take beyond its DURATION")
    ap.add_argument("--make-env-file", type=Path, default=None,
                    help="NAME=VALUE lines: the whole environment of make, plus a fresh HOME")
    ap.add_argument("--make-user", default=None, help="run make as this user (the grader runs as root)")
    args = ap.parse_args(argv)
    if key is None:
        key = json.loads(args.key.read_text(encoding="utf-8"))
    if key["stream"]["seed"] != args.seed:
        sys.exit(f"the key was computed for seed {key['stream']['seed']}, not {args.seed}")
    d1, d2 = (int(x) for x in args.durations.split(","))
    result = trial(args.repo.resolve(), key, args.capture.resolve(), seed=args.seed, port=args.port,
                   speed=args.speed, durations=(d1, d2), build_timeout=args.build_timeout,
                   logs=(args.logs or args.repo / "_grade_logs").resolve(), stream_grace=args.stream_grace,
                   make_env=read_env_file(args.make_env_file) if args.make_env_file else None,
                   make_user=args.make_user)
    json.dump(result, sys.stdout, indent=1, sort_keys=True, default=str)
    print()


if __name__ == "__main__":
    main()
