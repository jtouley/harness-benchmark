"""findings.jsonl: one row per failure, each tied to the runs that show it. A finding closes by script.

    python -m loop.findings check  [--cadence ../cadence]   # exit 1 on a bad row or a status the records do not give
    python -m loop.findings status [--cadence ../cadence]   # each finding's computed status and why
    python -m loop.findings update [--cadence ../cadence]   # write the computed statuses into findings.jsonl

A row: {"id": "F-n", "title", "run_ids": [...], "root_cause", "component": "cadence", "gone_when": {...},
"status": "open" | "closed", "owner": {"session", "branch"}}. A row with no run id, or with a run id that has
no record, is refused. `owner` names the session that fixes the finding and its branch; both are null while
nobody does, so two sessions never fix one finding unknowingly.

`status` is never set by hand: `check` refuses a status that differs from the computed one. A finding is
closed when there are later runs that:

- were started by the driver (not backfilled), count, and ran on a clean, published cadence commit that
  contains a commit with the trailer `Finding: F-n` (searched in the --cadence checkout);
- are benchmark runs on the task set (TASKS), and none of them is a run of the finding or a run of a
  non-benchmark request that found it;
- all meet `gone_when`, and their mean reward is not lower than the mean reward of the finding's runs.

`gone_when` keys (all given ones must hold for each run): `stop_block_not` (list of block ids),
`stop_reason_excludes` (text), `min_passed` (checks passed, from the latest score), `max_time_ratio` (the
run's agent session over the one-shot's of the same task and model, loop.scoreboard.time_ratio).
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
FINDINGS = ROOT / "findings.jsonl"
TASKS = ("P1", "P2")
FINDING_ID = re.compile(r"F-[1-9][0-9]*")
KEYS = {"id", "title", "run_ids", "root_cause", "component", "gone_when", "status", "owner"}
GONE_KEYS = {"stop_block_not", "stop_reason_excludes", "min_passed", "max_time_ratio"}



def scoreboard_passed(score: dict) -> int:
    """The checks a score earns: loop.scoreboard._passed (reward x total), the scoreboard's and the gate's rule."""
    from loop import scoreboard

    return scoreboard._passed(score)

def load(path: Path = FINDINGS) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def row_problems(row: dict, runs: Path) -> list[str]:
    """What is wrong with one row, apart from its status."""
    fid = row.get("id", "?")
    problems = [f"{fid}: missing {k}" for k in sorted(KEYS - set(row))]
    problems += [f"{fid}: unknown key {k}" for k in sorted(set(row) - KEYS)]
    if not FINDING_ID.fullmatch(str(row.get("id", ""))):
        problems.append(f"{fid}: id must be F-<n>")
    ids = row.get("run_ids")
    if not isinstance(ids, list) or not ids:
        problems.append(f"{fid}: no run id; a finding without a run is refused")
        ids = []
    for rid in ids:
        if not isinstance(rid, str) or not record.RUN_ID.fullmatch(rid):
            problems.append(f"{fid}: {rid!r} is not a run id (YYYYMMDD-words)")
        elif not (runs / rid / "record.json").exists():
            problems.append(f"{fid}: run {rid} has no record in {runs}")
    gone = row.get("gone_when")
    if not isinstance(gone, dict) or not gone or set(gone) - GONE_KEYS:
        problems.append(f"{fid}: gone_when must use only {sorted(GONE_KEYS)}")
    if row.get("component") != "cadence":
        problems.append(f"{fid}: component must be cadence (the only fix repository the close rule reads)")
    if row.get("status") not in ("open", "closed"):
        problems.append(f"{fid}: status must be open or closed")
    owner = row.get("owner")
    if "owner" in row and not (isinstance(owner, dict) and set(owner) == {"session", "branch"}
                               and all(v is None or isinstance(v, str) for v in owner.values())):
        problems.append(f'{fid}: owner must be {{"session": <id or null>, "branch": <name or null>}}')
    return problems


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def fix_commits(cadence: Path, fid: str) -> list[str]:
    """Commits in the cadence checkout whose message has the trailer `Finding: <fid>`."""
    out = _git(cadence, "log", "--all", "--format=%H%x00%B%x01").stdout
    found = []
    for entry in out.split("\x01"):
        sha, _, body = entry.strip().partition("\x00")
        if sha and re.search(rf"^Finding:\s*{re.escape(fid)}\s*$", body, re.M):
            found.append(sha)
    return found


def _contains(cadence: Path, sha: str, fixes: list[str]) -> bool:
    return any(_git(cadence, "merge-base", "--is-ancestor", f, sha).returncode == 0 for f in fixes)


def _latest(run: Path) -> dict | None:
    scores = record.scores(run)
    return scores[-1] if scores else None


def _gone(rec: dict, score: dict, gone: dict, runs: Path) -> bool:
    block = rec["stop_point"].get("block")
    reason = rec["stop_point"].get("reason") or ""
    if "stop_block_not" in gone and block in gone["stop_block_not"]:
        return False
    if "stop_reason_excludes" in gone and gone["stop_reason_excludes"] in reason:
        return False
    if "min_passed" in gone and scoreboard_passed(score) < gone["min_passed"]:
        return False
    if "max_time_ratio" in gone:
        from loop.scoreboard import time_ratio

        ratio = time_ratio(runs, rec)
        if ratio is None or ratio > gone["max_time_ratio"]:
            return False
    return True


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def compute(row: dict, runs: Path, cadence: Path | None) -> tuple[str, str]:
    """(status, why) of one finding, from the records alone."""
    if cadence is None:
        return "open", "no cadence checkout given, so no fix commit can be found"
    fixes = fix_commits(cadence, row["id"])
    if not fixes:
        return "open", f"no cadence commit has the trailer 'Finding: {row['id']}'"
    found = {rid: record.load(runs / rid) for rid in row["run_ids"]}
    latest_found = max((r["started_at"] or "" for r in found.values()), default="")
    requests = {r["request_id"] for r in found.values() if r["kind"] != "benchmark" and r["request_id"]}
    candidates = []
    for run in sorted(p for p in runs.iterdir() if (p / "record.json").exists()):
        rec = record.load(run)
        score = _latest(run)
        c = rec.get("cadence") or {}
        if (rec["run_id"] in found or rec["provenance"]["source"] != "driver" or not rec["counts"]["counts"]
                or rec["kind"] != "benchmark" or rec["task"] not in TASKS or rec["request_id"] in requests
                or not c.get("tree_clean") or (rec["started_at"] or "") <= latest_found or score is None
                or not _contains(cadence, c["sha"], fixes)):
            continue
        candidates.append((rec, score))
    if not candidates:
        return "open", "no later counted benchmark run on a clean cadence commit with the fix"
    still = [rec["run_id"] for rec, score in candidates if not _gone(rec, score, row["gone_when"], runs)]
    if still:
        return "open", f"the failure is still there in {', '.join(still)}"
    before = _mean([(_latest(runs / rid) or {}).get("reward", 0.0) for rid, r in found.items() if r["counts"]["counts"]])
    after = _mean([score["reward"] for _, score in candidates])
    if before is not None and after < before:
        return "open", f"the failure is gone, but the mean reward fell from {before:.4f} to {after:.4f}"
    ids = ", ".join(rec["run_id"] for rec, _ in candidates)
    return "closed", f"gone in {ids} (mean reward {after:.4f}, before {before if before is None else round(before, 4)})"


def check(path: Path, runs: Path, cadence: Path | None) -> list[str]:
    rows = load(path)
    problems = []
    seen = set()
    for row in rows:
        problems += row_problems(row, runs)
        if row.get("id") in seen:
            problems.append(f"{row.get('id')}: duplicate id")
        seen.add(row.get("id"))
    if problems:
        return problems
    for row in rows:
        status, why = compute(row, runs, cadence)
        if row["status"] != status:
            problems.append(f"{row['id']}: status is {row['status']!r}, the records give {status!r} ({why}); "
                            "run python -m loop.findings update")
    return problems


def update(path: Path, runs: Path, cadence: Path | None) -> None:
    rows = load(path)
    for row in rows:
        row["status"] = compute(row, runs, cadence)[0]
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m loop.findings", description=__doc__.split("\n\n")[0])
    ap.add_argument("action", choices=["check", "status", "update"])
    ap.add_argument("--findings", type=Path, default=FINDINGS)
    ap.add_argument("--runs", type=Path, default=ROOT / "runs")
    ap.add_argument("--cadence", type=Path, help="a checkout of jtouley/cadence with every branch fetched")
    args = ap.parse_args(argv)
    if args.action == "check":
        problems = check(args.findings, args.runs, args.cadence)
        for p in problems:
            print(p)
        print(f"{len(problems)} problem(s)", file=sys.stderr)
        return 1 if problems else 0
    if args.action == "update":
        bad = [p for row in load(args.findings) for p in row_problems(row, args.runs)]
        if bad:
            print("\n".join(bad))
            return 1
        update(args.findings, args.runs, args.cadence)
    for row in load(args.findings):
        status, why = compute(row, args.runs, args.cadence)
        print(f"{row['id']}\t{status}\t{why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
