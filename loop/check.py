"""Checks on runs/: every record and score validates, and a change keeps records append-only.

    python -m loop.check [--base REF]     # exit 1 with one line per problem

Against a base ref: a record.json that existed there must be unchanged, and a scores.jsonl must start
with the lines it had there.

Speed (loop.speed): a counted Cadence run has an agent session time and a time per block, or the loop
cannot measure it against the one-shot.

Postmortems (runs/README.md, "After a merge"): every counted run and every run a finding cites is in a
committed postmortem under postmortems/; every committed postmortem is what the generator writes from
its notes; scoreboard.md is what the scoreboard writes. `python -m loop.postmortem --all` and
`python -m loop.scoreboard --out scoreboard.md` make them so.

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

from loop import baselines, findings, postmortem, record, scoreboard, speed

ROOT = Path(__file__).resolve().parents[1]
GRADER_PATH = "golden/pipeline/pipetask"
CAUSE_PATHS = (GRADER_PATH + "/", "scripts/host_trial.py")
_SHA = re.compile(r"\b[0-9a-f]{7,40}\b")

# A run id that names a run shape (owner, 2026-10-24): <date>-<task>-cadence-<model>-core|full-<n>. Not the older
# ...-cadence-core-<model>-... ids, where "core" names cadence-core.
SHAPE_IN_ID = re.compile(r"-cadence-[a-z]+-(core|full)-")


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


def _batch_file(repo: Path, batch: str) -> dict | None:
    path = repo / "batches" / f"{batch}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _batch_pin(repo: Path, batch: str, cache: dict) -> set[str] | None:
    if batch not in cache:
        pin = _batch_file(repo, batch)
        cache[batch] = pinned_trees(repo, pin["grader_commit"]) if pin and pin.get("grader_commit") else None
    return cache[batch]


def score_problem(score: dict) -> str | None:
    """Why a score's reward is not its grade's, or None: the share of checks passed, and 0 when the grade failed
    its build or stream gate (idempotent or stream_ok false; pipetask.trial.reward). The loop scores reward x
    total (loop.scoreboard._passed), so a reward that disagrees would move a score."""
    passed, total, reward = score.get("passed"), score.get("total"), score.get("reward")
    if passed is None or not total or not isinstance(reward, (int, float)):
        return None
    voided = score.get("idempotent") is False or score.get("stream_ok") is False
    expected = 0.0 if voided else round(passed / total, 4)
    return None if abs(reward - expected) <= 1e-4 else f"reward {reward} does not agree with its grade (expected {expected})"


def cadence_problem(rec: dict, pin: dict | None) -> str | None:
    """Why a record's cadence commit is not its batch's pin, or None. A pin's `cadence_commit` is one sha for
    every run, or one per run shape (batch 2026-10-24-shapes: the core arm on 085bfdc, the full arm on d3c2ffe)."""
    pinned = (pin or {}).get("cadence_commit")
    sha = (rec.get("cadence") or {}).get("sha")
    if pinned is None or sha is None:
        return None
    where = f"batches/{rec.get('batch')}.json"
    if isinstance(pinned, dict):
        shape = rec.get("shape")
        if shape not in pinned:
            return f"{where} pins no cadence commit for shape {shape}"
        if sha != pinned[shape]:
            return f"cadence {sha[:7]} is not {where}'s pin {pinned[shape][:7]} for shape {shape}"
        return None
    return None if sha == pinned else f"cadence {sha[:7]} is not {where}'s pin {pinned[:7]}"


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
        if rec.get("api_error") and (rec.get("counts") or {}).get("counts") is True:
            problems.append(f"{run.name}/record.json: the API cut the run off ({rec['api_error']}); it never counts")
        if rec.get("kind") in record.NON_COUNTING_KINDS and (rec.get("counts") or {}).get("counts") is True:
            problems.append(f"{run.name}/record.json: a {rec['kind']} run never counts (counts.counts is true)")
        graded = any((s.get("grader") or {}).get("repo") == record.GRADER_REPO for s in record.scores(run))
        if (rec.get("provenance") or {}).get("source") == "backfill" and (rec.get("counts") or {}).get("counts") \
                is True and not graded:
            problems.append(f"{run.name}/record.json: a backfilled record counts only with a score from the "
                            "harness-benchmark grader")
        named = SHAPE_IN_ID.search(run.name)
        if named and rec.get("shape") != named.group(1):
            problems.append(f"{run.name}/record.json: the run id names shape {named.group(1)}, the record's shape is "
                            f"{rec.get('shape')!r}")
        if rec.get("run_id") != run.name:
            problems.append(f"{run.name}/record.json: run_id {rec.get('run_id')!r} is not the folder name")
        scores = record.scores(run)
        problems += regrade_problems(run.name, scores, repo)
        if (why := cadence_problem(rec, _batch_file(repo, str(rec.get("batch"))))) is not None:
            problems.append(f"{run.name}/record.json: {why}")
        pin = _batch_pin(repo, str(rec.get("batch")), pins)
        if pin is not None and scores and (rec.get("counts") or {}).get("counts") is True \
                and (scores[-1].get("grader") or {}).get("tree") not in pin:
            problems.append(f"{run.name}/scores.jsonl: the latest score's grader tree is not the batch's pinned "
                            f"grader (batches/{rec.get('batch')}.json) or a later one")
        for i, score in enumerate(scores, 1):
            problems += [f"{run.name}/scores.jsonl:{i}: {e}" for e in record.validate(score, record.SCORE_SCHEMA)]
            if (why := score_problem(score)) is not None:
                problems.append(f"{run.name}/scores.jsonl:{i}: {why}")
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
    problems += speed.problems(ROOT / "runs")
    problems += baselines.problems(ROOT / "runs")
    problems += postmortem_problems(ROOT / "runs", postmortem.POSTMORTEMS, scoreboard_path=ROOT / "scoreboard.md")
    if args.base:
        problems += append_only(ROOT, args.base)
    for p in problems:
        print(p)
    print(f"{len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
