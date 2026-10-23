"""Checks on runs/: every record and score validates, and a change keeps records append-only.

    python -m loop.check [--base REF]     # exit 1 with one line per problem

Against a base ref: a record.json that existed there must be unchanged, and a scores.jsonl must start
with the lines it had there.

A score with source "regrade" needs a traceable cause (review of #73): its grader commit is in this
repository's history, and its grader tree differs from the line before it, or its note names a commit of
this repository that changed golden/pipeline/pipetask/ or scripts/host_trial.py. A batch with a pin,
batches/<batch>.json {"grader_commit": sha}, has every counted run's latest score on that commit's grader
tree or on the tree of a later commit in this repository's history.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from loop import record

ROOT = Path(__file__).resolve().parents[1]
GRADER_PATH = "golden/pipeline/pipetask"
CAUSE_PATHS = (GRADER_PATH + "/", "scripts/host_trial.py")
_SHA = re.compile(r"\b[0-9a-f]{7,40}\b")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def _in_history(repo: Path, commit: str | None) -> bool:
    return bool(commit) and _git(repo, "merge-base", "--is-ancestor", commit, "HEAD").returncode == 0


def _touches_cause(repo: Path, commit: str) -> bool:
    if not _in_history(repo, commit):
        return False
    files = _git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "-m", commit).stdout.splitlines()
    return any(f.startswith(CAUSE_PATHS[0]) or f == CAUSE_PATHS[1] for f in files)


def regrade_problems(run: str, scores: list[dict], repo: Path) -> list[str]:
    problems = []
    for i, score in enumerate(scores):
        if score.get("source") != "regrade":
            continue
        grader = score.get("grader") or {}
        where = f"{run}/scores.jsonl:{i + 1}"
        if not _in_history(repo, grader.get("commit")):
            problems.append(f"{where}: regrade grader commit {grader.get('commit')!r} is not a commit of this "
                            "repository's history")
            continue
        previous = (scores[i - 1].get("grader") or {}).get("tree") if i else None
        named = [sha for sha in _SHA.findall(score.get("note") or "") if _touches_cause(repo, sha)]
        if grader.get("tree") == previous and not named:
            problems.append(f"{where}: regrade without a traceable cause (same grader tree as the line before, and "
                            f"the note names no commit that changed {' or '.join(CAUSE_PATHS)})")
    return problems


def pinned_trees(repo: Path, commit: str) -> set[str]:
    """The grader trees of the pin commit and of every later commit in this repository's history."""
    commits = [commit] + _git(repo, "rev-list", f"{commit}..HEAD").stdout.split()
    return {_git(repo, "rev-parse", f"{c}:{GRADER_PATH}").stdout.strip() for c in commits} - {""}


def _batch_pin(repo: Path, batch: str, cache: dict) -> set[str] | None:
    if batch not in cache:
        path = repo / "batches" / f"{batch}.json"
        cache[batch] = pinned_trees(repo, json.loads(path.read_text(encoding="utf-8"))["grader_commit"]) \
            if path.is_file() else None
    return cache[batch]


def validate_tree(runs: Path, repo: Path = ROOT) -> list[str]:
    problems: list[str] = []
    pins: dict = {}
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
        if rec.get("kind") in record.NON_COUNTING_KINDS and (rec.get("counts") or {}).get("counts") is True:
            problems.append(f"{run.name}/record.json: a {rec['kind']} run never counts (counts.counts is true)")
        graded = any((s.get("grader") or {}).get("repo") == record.GRADER_REPO for s in record.scores(run))
        if (rec.get("provenance") or {}).get("source") == "backfill" and (rec.get("counts") or {}).get("counts") \
                is True and not graded:
            problems.append(f"{run.name}/record.json: a backfilled record counts only with a score from the "
                            "harness-benchmark grader")
        if rec.get("run_id") != run.name:
            problems.append(f"{run.name}/record.json: run_id {rec.get('run_id')!r} is not the folder name")
        scores = record.scores(run)
        problems += regrade_problems(run.name, scores, repo)
        pin = _batch_pin(repo, str(rec.get("batch")), pins)
        if pin is not None and scores and (rec.get("counts") or {}).get("counts") is True \
                and (scores[-1].get("grader") or {}).get("tree") not in pin:
            problems.append(f"{run.name}/scores.jsonl: the latest score's grader tree is not the batch's pinned "
                            f"grader (batches/{rec.get('batch')}.json) or a later one")
        for i, score in enumerate(scores, 1):
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
        if rel.endswith("/record.json") or rel.endswith("/blocks.json"):
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
