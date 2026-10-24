"""The graded commit: the stored tree bundle holds the exact commit the grader graded, as refs/graded/<run-id>.

The grader grades the working tree the agent left (criteria-v2 §2.3: committing is not asked for): with
`--snapshot-worktree` it first commits that tree (pipetask.trial.snapshot) in the repository it grades, and
grades that commit. The agent's own refs do not reach that commit, so a bundle of the refs alone loses every
change the agent never committed (run 20261023-P1-oneshot-haiku-1: scored 5/7, its bundle held only the
starting skeleton). The driver therefore bundles the delivered repository's refs and HEAD plus
refs/graded/<run-id> at the graded commit, fetched from the repository the grader ran in, and the record
keeps that commit's sha (`graded`). `checkout` rebuilds the graded tree from a bundle for a regrade.

    python -m loop.graded --store ../runs-store [--runs runs] [--run RUN_ID]

lists every record graded by the harness-benchmark grader whose stored bundle lacks the graded work, one
line each, and exits 1 when there is one. It reads the bundles and changes nothing.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from loop import record, store

ROOT = Path(__file__).resolve().parents[1]
# Never run configuration from the agent's repository (pipetask.trial.SAFE_GIT).
SAFE_GIT = ("git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null", "-c", "core.untrackedCache=false")
# The starting repository's authors (pipetask.assemble's skeleton, host_trial.setup_repo's config commit): a
# bundle with no other commit holds none of the agent's work.
SETUP_AUTHORS = ("harness-benchmark", "cbench")


class GradedError(Exception):
    pass


def ref(run_id: str) -> str:
    return f"refs/graded/{run_id}"


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    proc = subprocess.run([*SAFE_GIT, *args], cwd=cwd, env=env, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise GradedError(f"git {' '.join(args)} in {cwd}: {proc.stderr.strip()[-300:]}")
    return proc


def graded_commit(grade: dict | None, repo: Path | None) -> tuple[str | None, str | None]:
    """(sha, None) of the commit the grader graded, or (None, why). With --snapshot-worktree it is the
    snapshot's commit; a grade without a snapshot graded `repo`'s HEAD (the grader resets to it)."""
    if grade is None:
        return None, "the grader wrote no grade.json"
    if "snapshot" in grade:
        commit = (grade.get("snapshot") or {}).get("commit")
        return (commit, None) if commit else (None, f"the grader's snapshot failed: {grade.get('error')}")
    if repo is None:
        return None, "the grade has no snapshot and no graded repository was given"
    proc = _git(repo, "rev-parse", "--verify", "HEAD^{commit}", check=False)
    return (proc.stdout.strip(), None) if proc.returncode == 0 else (None, f"{repo} has no HEAD commit")


def _fetch(dest: Path, source: Path, *specs: str) -> bool:
    return _git(dest, "fetch", "-q", "--no-tags", "--upload-pack",
                "git -c uploadpack.allowAnySHA1InWant=true upload-pack", str(source), *specs, check=False).returncode == 0


def bundle(tree: Path, out: Path, run_id: str, commit: str | None, sources: list[Path]) -> dict:
    """Write to `out` a bundle of every ref and HEAD of `tree` plus refs/graded/<run_id> at `commit`, fetched
    from the first of `sources` (and then `tree`) that has it. Returns the record's `graded`."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "bundle.git"
        _git(Path(tmp), "init", "-q", "--bare", str(work))
        if not _fetch(work, tree, "+refs/*:refs/*"):
            raise GradedError(f"cannot read the refs of {tree}")
        head = _git(tree, "symbolic-ref", "-q", "HEAD", check=False).stdout.strip()
        sha = _git(tree, "rev-parse", "--verify", "-q", "HEAD^{commit}", check=False).stdout.strip()
        if head and _git(work, "rev-parse", "--verify", "-q", head, check=False).returncode == 0:
            _git(work, "symbolic-ref", "HEAD", head)
        elif sha and _fetch(work, tree, sha):
            _git(work, "update-ref", "--no-deref", "HEAD", sha)
        graded = {"commit": commit, "ref": None}
        if commit is None:
            graded["missing"] = "no graded commit"
        elif any(_fetch(work, src, commit) for src in [*sources, tree] if src is not None and src.exists()):
            _git(work, "update-ref", ref(run_id), commit)
            graded["ref"] = ref(run_id)
        else:
            graded["missing"] = f"commit {commit} is in none of {', '.join(map(str, [*sources, tree]))}"
        _git(work, "bundle", "create", "-q", str(out), "--all")
    if graded["ref"] and heads(out).get(graded["ref"]) != commit:
        raise GradedError(f"the bundle {out} lacks {graded['ref']} at {commit}")
    return graded


def _plain(path: Path, tmp: Path) -> Path:
    """`path` itself, or its gunzipped copy in `tmp` (the store keeps blobs gzipped)."""
    with open(path, "rb") as f:
        gz = f.read(2) == b"\x1f\x8b"
    if not gz:
        return path
    plain = tmp / "tree.bundle"
    with gzip.open(path, "rb") as fin, open(plain, "wb") as fout:
        shutil.copyfileobj(fin, fout)
    return plain


def heads(path: Path) -> dict[str, str]:
    """{ref: sha} of a bundle, plain or gzipped."""
    with tempfile.TemporaryDirectory() as tmp:
        listed = _git(Path(tmp), "bundle", "list-heads", str(_plain(path, Path(tmp)))).stdout
    return {name: sha for sha, name in (line.split(" ", 1) for line in listed.splitlines() if " " in line)}


def checkout(path: Path, run_id: str, dest: Path) -> str:
    """Clone the bundle at `path` (plain or gzipped) into `dest` with the graded commit checked out on branch
    `graded`: the tree the grader graded, to grade again. Returns the commit; GradedError without the ref."""
    with tempfile.TemporaryDirectory() as tmp:
        plain = _plain(path, Path(tmp))
        commit = heads(plain).get(ref(run_id))
        if commit is None:
            raise GradedError(f"{path} has no {ref(run_id)}: the work that was graded is not in it")
        _git(Path(tmp), "clone", "-q", "--no-checkout", str(plain), str(dest))
        _git(dest, "fetch", "-q", "--no-tags", str(plain), f"+{ref(run_id)}:{ref(run_id)}")
    _git(dest, "-c", "advice.detachedHead=false", "checkout", "-q", "-B", "graded", commit)
    return commit


def _agent_commits(path: Path) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        mirror = Path(tmp) / "m.git"
        _git(Path(tmp), "clone", "-q", "--mirror", str(_plain(path, Path(tmp))), str(mirror))
        authors = _git(mirror, "log", "--all", "--format=%an").stdout.splitlines()
    return sum(1 for a in authors if a not in SETUP_AUTHORS)


def problem(rec: dict, store_root: Path) -> str | None:
    """Why the record's stored bundle lacks the graded work, or None when it holds it."""
    run_id, tree = rec["run_id"], rec.get("tree") or {}
    if not tree.get("sha256"):
        return f"no bundle ({tree.get('missing')})"
    path = store_root / tree.get("path", "")
    if not path.is_file():
        return f"the bundle {tree.get('path')} is not in {store_root}"
    found = heads(path).get(ref(run_id))
    graded = rec.get("graded")
    if isinstance(graded, dict) and graded.get("commit"):
        if found != graded["commit"]:
            return f"the bundle's {ref(run_id)} is {found}, not the graded commit {graded['commit']}"
        return None
    if isinstance(graded, dict):
        return f"the record names no graded commit ({graded.get('missing')})"
    if found is not None:
        return None
    agent = _agent_commits(path)
    if not agent:
        return (f"no {ref(run_id)} and no graded commit on the record; the bundle holds only the starting "
                "repository, so none of the graded work is in it")
    return (f"no {ref(run_id)} and no graded commit on the record; the bundle holds {agent} commit(s) of the "
            "agent's, but the grader's snapshot of the working tree (any uncommitted work) is not in it")


def audit(runs: Path, store_root: Path, only: str | None = None) -> list[tuple[str, str]]:
    """(run id, why) for each record scored by the harness-benchmark grader whose tree is meant for the
    runs-store and whose bundle lacks the graded work. Records whose tree was never kept (backfills that say
    why in `missing`, or a tree in another store) are not this check's: they have no bundle to fix."""
    found = []
    for run in sorted(p for p in runs.iterdir() if (p / "record.json").is_file()):
        if only and run.name != only:
            continue
        rec = record.load(run)
        if not any((s.get("grader") or {}).get("repo") == record.GRADER_REPO for s in record.scores(run)):
            continue
        tree = rec.get("tree") or {}
        if tree.get("sha256") and tree.get("store") != store.STORE:
            continue
        if not tree.get("sha256") and (rec.get("provenance") or {}).get("source") == "backfill":
            continue
        why = problem(rec, store_root)
        if why:
            found.append((run.name, why))
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m loop.graded", description=__doc__.split("\n\n")[0])
    ap.add_argument("--store", type=Path, required=True, help="a checkout of the runs-store branch")
    ap.add_argument("--runs", type=Path, default=ROOT / "runs")
    ap.add_argument("--run", help="check this run only")
    ap.add_argument("--json", action="store_true", help="print the list as JSON")
    args = ap.parse_args(argv)
    found = audit(args.runs, args.store, args.run)
    if args.json:
        print(json.dumps([{"run_id": r, "why": w} for r, w in found], indent=1))
    else:
        for run_id, why in found:
            print(f"{run_id}: {why}")
    print(f"{len(found)} record(s) whose bundle lacks the graded work", file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
