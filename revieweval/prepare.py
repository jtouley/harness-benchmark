"""Turn stored run trees into blinded review trees: one per case of the review eval set.

    python -m revieweval.prepare --out WORK [--ref origin/main] [--store-ref origin/runs-store] [RUN_ID ...]

For each run (default: every case in revieweval/cases.json), in WORK/trees/<case>/:

1. The record's tree blob is read from the runs-store branch (`git show <store-ref>:<path>`) and its sha256 is
   checked against record.json. Nothing is fetched or re-run.
2. The bundle is cloned. The reviewed head is refs/graded/<run id> when the bundle has it (the tree the grader
   graded), else the run's work branch (the one ref that is not `main`).
3. Blinding: a new two-commit repository. `base` is the task skeleton (the bundle's first commit on main);
   `review` is one commit, "Change under review", with the head's tree minus the arm's own files
   (`.cadence.json`, `.context/`, `.claude/`, `.cursor/`). Authors, dates, branch names and commit messages of
   the run are gone, so a reviewer cannot tell a one-shot from a Cadence run.

WORK/trees/<case>/source.json records the run id, the blob sha256, the head and base commits it came from.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = Path(__file__).resolve().parent / "cases.json"
ARM_FILES = (".cadence.json", ".context", ".claude", ".cursor")
BLIND_ENV = {"GIT_AUTHOR_NAME": "author", "GIT_AUTHOR_EMAIL": "author@example.invalid",
             "GIT_COMMITTER_NAME": "author", "GIT_COMMITTER_EMAIL": "author@example.invalid",
             "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"}


def git(cwd: Path, *args: str, env: dict | None = None, text: bool = True) -> str:
    import os
    full = {**os.environ, **(env or {})}
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=text, env=full).stdout


def load_cases() -> list[dict]:
    return json.loads(CASES.read_text())["cases"]


def record(run_id: str, ref: str) -> dict:
    return json.loads(git(ROOT, "show", f"{ref}:runs/{run_id}/record.json"))


def bundle_bytes(rec: dict, store_ref: str) -> bytes:
    tree = rec["tree"]
    gz = subprocess.run(["git", "show", f"{store_ref}:{tree['path']}"], cwd=ROOT, check=True,
                        capture_output=True).stdout
    raw = gzip.decompress(gz)
    got = hashlib.sha256(raw).hexdigest()
    if got != tree["sha256"]:
        raise SystemExit(f"{rec['run_id']}: blob sha256 {got} is not the record's {tree['sha256']}")
    return raw


def pick_head(clone: Path, run_id: str) -> str:
    refs = dict(line.split(" ", 1)[::-1] for line in git(clone, "show-ref").split("\n") if line)
    graded = f"refs/graded/{run_id}"
    if graded in refs:
        return refs[graded]
    work = [r for r in refs if r.startswith("refs/remotes/origin/") and not r.endswith(("/main", "/HEAD"))]
    if len(work) != 1:
        raise SystemExit(f"{run_id}: cannot tell the work branch from {sorted(refs)}")
    return refs[work[0]]


def blind(clone: Path, head: str, dest: Path) -> dict:
    base = git(clone, "rev-list", "--max-parents=0", "origin/main").split()[0]
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    git(dest, "init", "-q", "-b", "base")
    for commit, message in ((base, "Base"), (head, "Change under review")):
        for p in dest.iterdir():
            if p.name != ".git":
                shutil.rmtree(p) if p.is_dir() and not p.is_symlink() else p.unlink()
        archive = subprocess.run(["git", "archive", commit], cwd=clone, check=True, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)
        for name in ARM_FILES:
            p = dest / name
            if p.is_dir():
                shutil.rmtree(p)
            elif p.exists():
                p.unlink()
        ignore = dest / ".gitignore"
        if ignore.is_file():  # an arm's own ignore lines name it
            lines = ignore.read_text().splitlines(keepends=True)
            ignore.write_text("".join(x for x in lines if "cadence" not in x.lower()))
        git(dest, "add", "-A")
        git(dest, "commit", "-q", "--allow-empty", "-m", message, env=BLIND_ENV)
        if commit == base:
            git(dest, "checkout", "-q", "-b", "review")
    return {"base_commit": base, "head_commit": head, "base_blind": git(dest, "rev-parse", "base").strip(),
            "review_blind": git(dest, "rev-parse", "review").strip()}


def prepare(case: dict, out: Path, ref: str, store_ref: str) -> dict:
    rec = record(case["run_id"], ref)
    raw = bundle_bytes(rec, store_ref)
    with tempfile.TemporaryDirectory() as tmp:
        b = Path(tmp) / "tree.bundle"
        b.write_bytes(raw)
        clone = Path(tmp) / "clone"
        subprocess.run(["git", "clone", "-q", str(b), str(clone)], check=True, capture_output=True)
        head = pick_head(clone, case["run_id"])
        dest = out / "trees" / case["name"] / "repo"
        info = blind(clone, head, dest)
    info.update(run_id=case["run_id"], case=case["name"], blob_sha256=rec["tree"]["sha256"], record_ref=ref,
                task=rec["task"])
    (dest.parent / "source.json").write_text(json.dumps(info, indent=1) + "\n")
    return info


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--store-ref", default="origin/runs-store")
    ap.add_argument("runs", nargs="*")
    args = ap.parse_args(argv)
    cases = [c for c in load_cases() if not args.runs or c["run_id"] in args.runs or c["name"] in args.runs]
    for c in cases:
        info = prepare(c, args.out, args.ref, args.store_ref)
        print(f"{c['name']}: {info['run_id']} head {info['head_commit'][:10]} -> review {info['review_blind'][:10]}")


if __name__ == "__main__":
    main()
