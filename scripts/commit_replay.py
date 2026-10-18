#!/usr/bin/env python3
"""Measure each commit of a run, not only the whole change: what a reviewer gets, step by step.

A one-shot usually leaves one commit, so its reviewer reads the whole change at once. A harness
commits along the way, so each step is smaller. The final code can be the same; what differs is
how the complexity reached the reviewer. This script replays the commits from BASE to HEAD
(first parent only) and, for each one, measures:

- change size: lines added and deleted in the package (git numstat; binary files skipped);
- complexity added and removed: the change in radon cyclomatic complexity (McCabe 1976) per
  function, against the commit's parent. A new function adds its whole value, a deleted one
  removes it. Pinned radon, as in scripts/quality_metrics.py;
- functions over 10: functions the commit takes over cyclomatic complexity 10 (radon's and the
  SlopCodeBench erosion threshold);
- green: whether --test-cmd exits 0 on the commit's tree within --test-timeout seconds (a timeout is
  not green; None when no command is given);
- time since the previous commit, from commit timestamps.

A commit whose code does not parse cannot be measured: its complexity fields are None, it names the
files, and the next commit is compared with the last commit that did parse. Without that, a broken
commit would look like it deleted every function, and the commit after it like it added them back.

The summary gives, for the whole run: the number of commits, the largest and median commit by
lines and by complexity added, the share of green commits, the commits that removed more
complexity than they added (clean-up steps), the total churn (all lines and all complexity added
along the way, which is what drafting and cleaning up costs), and the final state, so that small
steps bought by ending at worse code show up. Fewer than one commit, or uncommitted work, is reported, not scored.

usage: commit_replay.py REPO BASE HEAD [--package DIR] [--test-cmd CMD] [--test-timeout SECONDS]
Prints one JSON object. Needs git and uv (radon runs through `uvx`).
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quality_metrics import TOOLS, ToolError, _json, _run  # noqa: E402

THRESHOLD = 10
UNMEASURED = {"complexity_added": None, "complexity_removed": None, "newly_over_10": None}


def _git(repo: Path, *args: str) -> str:
    return _run(["git", "-C", str(repo), *args], repo).stdout


def commits(repo: Path, base: str, head: str) -> list[str]:
    return _git(repo, "rev-list", "--reverse", "--first-parent", f"{base}..{head}").split()


def _export(repo: Path, sha: str, dest: Path) -> Path:
    """The commit's tree as plain files (no checkout, so the repository is never touched)."""
    archive = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", sha],
                             capture_output=True, check=True).stdout
    with tarfile.open(fileobj=BytesIO(archive)) as tar:
        tar.extractall(dest, filter="data")
    return dest


def complexity(tree: Path, package: str) -> tuple[dict[tuple[str, str], int], list[str]]:
    """({(file, function): cyclomatic complexity}, files radon could not parse)."""
    if not (tree / package).exists():
        return {}, []
    data = _json(_run(["uvx", "--quiet", TOOLS["radon"], "cc", "-j", package], tree).stdout, "radon cc")
    functions, unparsed = {}, []
    for file, blocks in data.items():
        file = file.removeprefix("./")
        if isinstance(blocks, dict) and "error" in blocks:
            unparsed.append(file)
            continue
        for b in blocks:
            if b.get("type") in ("function", "method"):
                name = f"{b['classname']}.{b['name']}" if b.get("classname") else b["name"]
                functions[(file, name)] = b["complexity"]
    return functions, sorted(unparsed)


def change_size(repo: Path, sha: str, package: str) -> tuple[int, int]:
    added = deleted = 0
    for line in _git(repo, "show", "--numstat", "--format=", "--first-parent", sha, "--", package).splitlines():
        a, d, _ = line.split("\t", 2)
        if a != "-":  # binary file
            added, deleted = added + int(a), deleted + int(d)
    return added, deleted


def complexity_delta(before: dict, after: dict) -> dict:
    added = removed = 0
    for key in before.keys() | after.keys():
        diff = after.get(key, 0) - before.get(key, 0)
        added, removed = added + max(diff, 0), removed + max(-diff, 0)
    over = sorted(f"{file}:{name}={value}" for (file, name), value in after.items()
                  if value > THRESHOLD and before.get((file, name), 0) <= THRESHOLD)
    return {"complexity_added": added, "complexity_removed": removed, "newly_over_10": over}


def green(tree: Path, test_cmd: str | None, timeout: float = 600) -> bool | None:
    if not test_cmd:
        return None
    try:
        return subprocess.run(test_cmd, shell=True, cwd=tree, capture_output=True, timeout=timeout).returncode == 0
    except subprocess.TimeoutExpired:
        return False


def final_state(after: dict) -> dict:
    return {"functions": len(after), "total_complexity": sum(after.values()),
            "functions_over_10": sum(1 for v in after.values() if v > THRESHOLD)}


def summarize(rows: list[dict], final: dict) -> dict:
    if not rows:
        return {"commits": 0, "measurable": False, "final": final}
    lines = [r["lines_added"] + r["lines_deleted"] for r in rows]
    tested = [r["green"] for r in rows if r["green"] is not None]
    measured = [r for r in rows if r["complexity_added"] is not None]
    added = [r["complexity_added"] for r in measured] or [None]
    return {
        "commits": len(rows),
        "measurable": True,
        "largest_commit_lines": max(lines),
        "median_commit_lines": statistics.median(lines),
        "total_lines_changed": sum(lines),
        "largest_commit_complexity_added": None if added == [None] else max(added),
        "median_commit_complexity_added": None if added == [None] else statistics.median(added),
        "unparsed_commits": len(rows) - len(measured),
        "green_share": sum(tested) / len(tested) if tested else None,
        "cleanup_commits": sum(1 for r in measured if r["complexity_removed"] > r["complexity_added"]),
        "complexity_added_total": sum(r["complexity_added"] for r in measured),
        "complexity_removed_total": sum(r["complexity_removed"] for r in measured),
        "seconds_base_to_head": sum(r["seconds_since_previous"] for r in rows),
        "final": final,
    }


def replay(repo: Path, base: str, head: str, package: str = ".", test_cmd: str | None = None,
           test_timeout: float = 600) -> dict:
    shas = commits(repo, base, head)
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        before, _ = complexity(_export(repo, base, Path(tmp) / "base"), package)
        previous_time = int(_git(repo, "show", "-s", "--format=%ct", base))
        for i, sha in enumerate(shas):
            tree = _export(repo, sha, Path(tmp) / f"c{i}")
            after, unparsed = complexity(tree, package)
            added, deleted = change_size(repo, sha, package)
            when = int(_git(repo, "show", "-s", "--format=%ct", sha))
            delta = UNMEASURED if unparsed else complexity_delta(before, after)
            rows.append({"sha": sha, "subject": _git(repo, "show", "-s", "--format=%s", sha).strip(),
                         "lines_added": added, "lines_deleted": deleted, **delta, "unparsed": unparsed,
                         "green": green(tree, test_cmd, test_timeout), "seconds_since_previous": when - previous_time})
            previous_time = when
            if not unparsed:
                before = after
    # The final state is the head's; when the head does not parse it is unmeasured, not the last good one.
    final = final_state(before) if not rows or not rows[-1]["unparsed"] else None
    uncommitted = _git(repo, "status", "--porcelain", "--", package).strip()
    return {"base": base, "head": head, "package": package, "test_cmd": test_cmd,
            "uncommitted_changes": bool(uncommitted), "commits": rows,
            "summary": summarize(rows, final)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo", type=Path)
    ap.add_argument("base")
    ap.add_argument("head")
    ap.add_argument("--package", default=".", help="the directory to measure, relative to the repository root")
    ap.add_argument("--test-cmd", default=None, help="shell command run in each commit's tree; exit 0 is green")
    ap.add_argument("--test-timeout", type=float, default=600, help="seconds before a test command counts as not green")
    args = ap.parse_args(argv)
    try:
        result = replay(args.repo.resolve(), args.base, args.head, args.package, args.test_cmd, args.test_timeout)
    except (ToolError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
