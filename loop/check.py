"""Checks on runs/: every record and score validates, and a change keeps records append-only.

    python -m loop.check [--base REF]     # exit 1 with one line per problem

Against a base ref: a record.json that existed there must be unchanged, and a scores.jsonl must start
with the lines it had there.

Postmortems (runs/README.md, "After a merge"): every counted run and every run a finding cites is in a
committed postmortem under postmortems/; every committed postmortem is what the generator writes from
its notes; scoreboard.md is what the scoreboard writes. `python -m loop.postmortem --all` and
`python -m loop.scoreboard --out scoreboard.md` make them so.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from loop import findings, postmortem, record, scoreboard

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
        if rec.get("kind") in record.NON_COUNTING_KINDS and (rec.get("counts") or {}).get("counts") is True:
            problems.append(f"{run.name}/record.json: a {rec['kind']} run never counts (counts.counts is true)")
        graded = any((s.get("grader") or {}).get("repo") == record.GRADER_REPO for s in record.scores(run))
        if (rec.get("provenance") or {}).get("source") == "backfill" and (rec.get("counts") or {}).get("counts") \
                is True and not graded:
            problems.append(f"{run.name}/record.json: a backfilled record counts only with a score from the "
                            "harness-benchmark grader")
        if rec.get("run_id") != run.name:
            problems.append(f"{run.name}/record.json: run_id {rec.get('run_id')!r} is not the folder name")
        for i, score in enumerate(record.scores(run), 1):
            problems += [f"{run.name}/scores.jsonl:{i}: {e}" for e in record.validate(score, record.SCORE_SCHEMA)]
            if score.get("run_id") != run.name:
                problems.append(f"{run.name}/scores.jsonl:{i}: run_id is not the folder name")
    return problems


def postmortem_problems(runs: Path, postmortems: Path, findings_path: Path = findings.FINDINGS,
                        scoreboard_path: Path | None = None, citations: dict | None = None) -> list[str]:
    """Runs whose batch no committed postmortem covers, a notes file that names a batch with no run,
    postmortems that are not the generator's output, and a scoreboard that is not the scoreboard's output.

    Coverage is by batch, never by a run id in the text: a notes line that cites a run of another batch
    (a decision with run_ids) does not document that run's batch."""
    problems = []
    covering = postmortem.covering(postmortems)
    texts = {name: (postmortems / f"{name}.md").read_text(encoding="utf-8") for name in covering}
    covered = {b for bs in covering.values() for b in bs}
    cited = {rid for row in findings.load(findings_path) for rid in row["run_ids"]}
    known_batches = set()
    for run in sorted(p for p in runs.iterdir() if (p / "record.json").exists()):
        rec = record.load(run)
        known_batches.add(rec["batch"])
        why = "counted" if rec["counts"]["counts"] else "cited by a finding" if run.name in cited else None
        if why and rec["batch"] not in covered:
            problems.append(f"{run.name}: {why}, and its batch {rec['batch']} is in no committed postmortem under "
                            f"{postmortems.name}/ (python -m loop.postmortem {rec['batch']})")
    for name, batches in covering.items():
        for batch in batches:
            if batch not in known_batches:
                problems.append(f"{postmortems.name}/{name}.notes.json: names batch {batch!r}, which no run in "
                                f"{runs.name}/ has")
    for name, batches in covering.items():
        try:
            expected = postmortem.render(name, batches, runs, postmortems, findings_path, citations)
        except postmortem.PostmortemError as exc:
            problems.append(f"{postmortems.name}/{name}.md: cannot be generated: {exc}")
            continue
        if texts[name] != expected:
            problems.append(f"{postmortems.name}/{name}.md: not what the generator writes (python -m loop.postmortem --all)")
    if scoreboard_path is not None:
        current = scoreboard_path.read_text(encoding="utf-8") if scoreboard_path.exists() else None
        if current != scoreboard.table(runs):
            problems.append(f"{scoreboard_path.name}: not what the scoreboard writes (python -m loop.scoreboard --out "
                            f"{scoreboard_path.name})")
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
    problems += postmortem_problems(ROOT / "runs", postmortem.POSTMORTEMS, scoreboard_path=ROOT / "scoreboard.md")
    if args.base:
        problems += append_only(ROOT, args.base)
    for p in problems:
        print(p)
    print(f"{len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
