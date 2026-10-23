"""Run a delivered P4 pipeline the way the analysts would, then grade it.

    python -m pipetask.p4trial --repo REPO --key P4/key/answer_key.json [--build-timeout 600]

P4 is batch only (no stream), so the trial is the batch half of pipetask.trial, with its steps reused:
0. The repository is reset to what was committed (`trial.reset`: `git clean -ffdx`, then `out/` and
   `lake/` removed even when committed). `--snapshot-worktree` first commits the tree the agent left.
1. `make build`, a digest of every published mart (`trial.mart_digests`), `make build` again, compare.
   The digest reads the same marts the checks read, folders and single files (#49), so a mart the
   checks grade is always checked for idempotence too.
2. The seven checks (pipetask.p4grade).

`reward` is the share of the seven checks that pass, and 0 when a second build changed an output or a
build failed. A trial that cannot run prints `{"error": ..., "reward": 0.0}`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import p4grade, trial


def reward(result: dict) -> float:
    return 0.0 if not result["idempotent"] else round(result["passed"] / result["total"], 4)


def run(repo: Path, key: dict, *, build_timeout: float, logs: Path, make_env: dict[str, str] | None = None,
        make_user: str | None = None, snapshot_worktree: bool = False) -> dict:
    result: dict = {"task": "P4", "build_timeout": build_timeout, "make_user": make_user,
                    "make_fresh_home": make_env is not None or make_user is not None}
    if make_user and os.geteuid() != 0:
        return {**result, "error": "--make-user needs the grader to run as root", "reward": 0.0}
    as_user = ("setpriv", f"--reuid={make_user}", f"--regid={make_user}", "--init-groups") if make_user else ()
    if snapshot_worktree:
        result["snapshot"] = trial.snapshot(repo, as_user)
        if "error" in result["snapshot"]:
            return {**result, "error": result["snapshot"]["error"], "reward": 0.0}
    error = trial.reset(repo, as_user)
    if error:
        return {**result, "error": error, "reward": 0.0}
    logs.mkdir(parents=True, exist_ok=True)
    make = trial.MakeRunner(make_env, make_user)
    try:
        first = make(["make", "build"], repo, build_timeout, logs / "build-1.log")
        digests1 = trial.mart_digests(repo)
        second = make(["make", "build"], repo, build_timeout, logs / "build-2.log")
        digests2 = trial.mart_digests(repo)
    finally:
        make.close()
    changed = sorted(k for k in set(digests1) | set(digests2) if digests1.get(k) != digests2.get(k))
    result["build"] = [first, second]
    result["idempotent"] = first["exit"] == 0 and second["exit"] == 0 and not changed and bool(digests1)
    result["changed_by_second_build"] = changed
    result.update(p4grade.grade(repo, key))
    result["reward"] = reward(result)
    return result


def main(argv: list[str] | None = None, key: dict | None = None) -> None:
    ap = argparse.ArgumentParser(description="Build twice and grade a delivered P4 pipeline.")
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--key", type=Path, required=key is None)
    ap.add_argument("--build-timeout", type=float, default=600)
    ap.add_argument("--logs", type=Path, default=None)
    ap.add_argument("--make-env-file", type=Path, default=None,
                    help="NAME=VALUE lines: the whole environment of make, plus a fresh HOME")
    ap.add_argument("--make-user", default=None, help="run make as this user (the grader runs as root)")
    ap.add_argument("--snapshot-worktree", action="store_true",
                    help="commit the working tree the agent left before the reset")
    args = ap.parse_args(argv)
    if key is None:
        key = json.loads(args.key.read_text(encoding="utf-8"))
    result = run(args.repo.resolve(), key, build_timeout=args.build_timeout,
                 logs=(args.logs or args.repo / "_grade_logs").resolve(),
                 make_env=trial.read_env_file(args.make_env_file) if args.make_env_file else None,
                 make_user=args.make_user, snapshot_worktree=args.snapshot_worktree)
    json.dump(result, sys.stdout, indent=1, sort_keys=True, default=str)
    print()


if __name__ == "__main__":
    main()
