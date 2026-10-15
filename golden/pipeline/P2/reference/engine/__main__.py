"""The engine's command line.

    python -m engine validate pipelines/*.yml
    python -m engine run pipelines/batch.yml
    python -m engine run pipelines/stream.yml --duration 60

Every file is checked against the schema before anything runs; a problem is printed as
`<file>:<line>: <problem>` and the exit code is 2. Paths in a pipeline are relative to the working
directory (the repository root, where the Makefile runs).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import config, run


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="engine", description="Run pipelines declared in YAML.")
    sub = ap.add_subparsers(dest="command", required=True)
    check = sub.add_parser("validate", help="check pipeline files and exit")
    check.add_argument("files", nargs="+", type=Path)
    go = sub.add_parser("run", help="check, then run one pipeline file")
    go.add_argument("file", type=Path)
    go.add_argument("--duration", type=float, help="seconds to consume a stream for")
    args = ap.parse_args(argv)

    files = args.files if args.command == "validate" else [args.file]
    pipelines, problems = [], []
    for path in files:
        try:
            pipelines.append(config.load(path))
        except config.ConfigError as exc:
            problems.append(str(exc))
        except OSError as exc:
            problems.append(f"{path}:1: {exc.strerror}")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 2
    if args.command == "validate":
        print(f"{len(pipelines)} pipeline file(s) valid")
        return 0
    landed = run.run(pipelines[0], Path.cwd(), args.duration)
    for table, rows in landed.items():
        print(f"{pipelines[0].name}: lake/{table}: {rows} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
