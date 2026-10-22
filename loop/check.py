"""Checks on runs/: every record and score validates, and a change keeps records append-only.

    python -m loop.check [--base REF]     # exit 1 with one line per problem

Against a base ref: a record.json that existed there must be unchanged, and a scores.jsonl must start
with the lines it had there.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from loop import record

ROOT = Path(__file__).resolve().parents[1]


def validate_tree(runs: Path) -> list[str]:
    problems = []
    if not runs.is_dir():
        return problems
    for run in sorted(p for p in runs.iterdir() if p.is_dir()):
        if not (run / "record.json").exists():
            problems.append(f"{run.name}: no record.json")
            continue
        try:
            rec = record.load(run)
        except ValueError as exc:
            problems.append(f"{run.name}/record.json: {exc}")
            continue
        problems += [f"{run.name}/record.json: {e}" for e in record.validate(rec, record.RECORD_SCHEMA)]
        if rec.get("run_id") != run.name:
            problems.append(f"{run.name}/record.json: run_id {rec.get('run_id')!r} is not the folder name")
        for i, score in enumerate(record.scores(run), 1):
            problems += [f"{run.name}/scores.jsonl:{i}: {e}" for e in record.validate(score, record.SCORE_SCHEMA)]
            if score.get("run_id") != run.name:
                problems.append(f"{run.name}/scores.jsonl:{i}: run_id is not the folder name")
    return problems


def _show(repo: Path, ref: str, rel: str) -> str | None:
    proc = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=repo, capture_output=True, text=True)
    return proc.stdout if proc.returncode == 0 else None


def append_only(repo: Path, base: str, runs: str = "runs") -> list[str]:
    """Problems with the working tree of `repo` against `base`: changed or deleted records, rewritten scores."""
    listed = subprocess.run(["git", "ls-tree", "-r", "--name-only", base, "--", runs], cwd=repo,
                            capture_output=True, text=True, check=True).stdout.split()
    problems = []
    for rel in listed:
        now = repo / rel
        before = _show(repo, base, rel)
        if rel.endswith("/record.json"):
            if not now.exists():
                problems.append(f"{rel}: deleted (records are append-only)")
            elif now.read_text(encoding="utf-8") != before:
                problems.append(f"{rel}: changed (records are append-only; write a new run instead)")
        elif rel.endswith("/scores.jsonl"):
            if not now.exists() or not now.read_text(encoding="utf-8").startswith(before or ""):
                problems.append(f"{rel}: rewritten (scores are appended, never edited)")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m loop.check", description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", help="git ref to compare with (e.g. origin/main)")
    args = ap.parse_args(argv)
    problems = validate_tree(ROOT / "runs")
    if args.base:
        problems += append_only(ROOT, args.base)
    for p in problems:
        print(p)
    print(f"{len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
