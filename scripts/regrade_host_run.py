"""Grade a host-method run again and append the score: for a run that host_trial.py graded wrongly.

    python scripts/regrade_host_run.py RUN_ID --tree RUN/repo-as-left --why "..." [--runs runs]
    python scripts/regrade_host_run.py RUN_ID --bundle ../runs-store/blobs/<sha>.gz --why "..." [--runs runs]

The tree is the delivered repository the driver stored (repo-as-left; its bundle is the record's `tree`).
With --bundle, the record's stored bundle itself (plain or gzipped): the commit it keeps as
refs/graded/<run_id>, the exact tree the grader graded (loop.graded), is checked out and graded; a bundle
without that ref is refused, since it does not hold the work that was graded. A copy is graded with host_trial.grade, from the repository as the container runner grades, and the score is
appended with source "regrade", the grader's commit and tree, and `note` (why). The record is not changed.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import host_trial  # noqa: E402
from loop import driver, graded, record  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("run_id")
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--tree", type=Path, help="the run's delivered repository (repo-as-left)")
    source.add_argument("--bundle", type=Path, help="the run's stored tree bundle: its refs/graded/<run_id> is graded")
    ap.add_argument("--why", required=True)
    ap.add_argument("--runs", type=Path, default=ROOT / "runs")
    args = ap.parse_args(argv)
    if not (args.runs / args.run_id / "record.json").is_file():
        print(f"regrade: no record for {args.run_id}", file=sys.stderr)
        return 2
    grader = driver.grader_identity(ROOT)
    with tempfile.TemporaryDirectory() as tmp:
        repo, out = Path(tmp) / "repo", Path(tmp) / "out"
        if args.bundle:
            try:
                graded.checkout(args.bundle, args.run_id, repo)
            except graded.GradedError as exc:
                print(f"regrade: {exc}", file=sys.stderr)
                return 2
        else:
            shutil.copytree(args.tree, repo, symlinks=True)
        out.mkdir()
        host_trial.grade(repo, out)
        try:
            grade = json.loads((out / "grade.json").read_text(encoding="utf-8"))
        except ValueError:
            grade = {"reward": 0.0, "error": "the grader wrote no JSON: " + (out / "grade.stderr").read_text()[-300:]}
    score = {"run_id": args.run_id, "grader": grader, "reward": grade.get("reward", 0.0), "passed": grade.get("passed"),
             "total": grade.get("total"), "idempotent": grade.get("idempotent"), "stream_ok": grade.get("stream_ok"),
             "error": grade.get("error"), "source": "regrade",
             "graded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "note": args.why}
    record.append_score(args.runs, score)
    print(json.dumps({k: score[k] for k in ("run_id", "reward", "passed", "total")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
