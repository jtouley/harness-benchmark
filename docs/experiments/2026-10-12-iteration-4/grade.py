"""Grade one eval run: pipeline compliance (C*) and delivered quality (Q*), by script.

usage: python grade.py <run_dir> <eval_name>
Writes <run_dir>/grading.json with expectations [{text, passed, evidence}].
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
HIDDEN = WORKSPACE / "hidden"
QUESTION = re.compile(r"(?i)\b(should I|do you want|want me to|please confirm|let me know if|shall I|your call|your decision)\b")
PHASE_HEADER = re.compile(r"^#{2,4}\s+(?:Stage\s+4\s+)?Phase\s+\d+\b", re.M | re.I)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout.strip()


def baseline(repo: Path) -> str:
    """The fixture's "ledgerlite baseline" commit: the same start for every arm.

    origin/main is not a fixed point: a run with no PR flow may push to main.
    """
    return git(repo, "rev-list", "--max-parents=0", "HEAD").split()[0]


def feature_checkout(repo: Path) -> tuple[Path, str, list[str]]:
    """The branch furthest ahead of the baseline commit, and a checkout of it."""
    base = baseline(repo)
    best, ahead = "main", -1
    for ref in git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads").splitlines():
        n = int(git(repo, "rev-list", "--count", f"{base}..{ref}") or 0)
        if n > ahead:
            best, ahead = ref, n
    worktrees = git(repo, "worktree", "list", "--porcelain").split("\n\n")
    path = None
    for block in worktrees:
        lines = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        if lines.get("branch") == f"refs/heads/{best}":
            path = Path(lines["worktree"])
    if path is None:
        path = Path(tempfile.mkdtemp(prefix="grade-")) / "co"
        subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", "--detach", str(path), best], check=True)
    subjects = git(repo, "log", f"{base}..{best}", "--format=%ct %s").splitlines()
    return path, best, subjects


def files(ctx: Path, *globs: str) -> list[Path]:
    out: list[Path] = []
    for g in globs:
        out.extend(p for p in ctx.glob(g) if p.is_file())
    return out


def has(paths: list[Path], pattern: str) -> list[Path]:
    rx = re.compile(pattern, re.I)
    return [p for p in paths if rx.search(p.read_text(encoding="utf-8", errors="replace"))]


def count_tests(root: Path) -> int:
    return sum(len(re.findall(r"^\s*def test_", p.read_text(encoding="utf-8", errors="replace"), re.M))
               for p in (root / "tests").rglob("test_*.py"))


def pytest(root: Path, extra: list[str] | None = None) -> tuple[int, str]:
    proc = subprocess.run(["uv", "run", "--with", "pytest", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider", *(extra or [])],
                          cwd=root, capture_output=True, text=True, timeout=600)
    return proc.returncode, (proc.stdout + proc.stderr).strip().splitlines()[-1:][0] if (proc.stdout + proc.stderr).strip() else ""


def hidden_results(root: Path, eval_name: str) -> tuple[int, int, str]:
    name = {"multicurrency": "multicurrency", "budgets": "budgets", "audit-undo": "audit_undo"}[eval_name]
    tmp = Path(tempfile.mkdtemp(prefix="hidden-"))
    shutil.copy(HIDDEN / "_cli.py", tmp / "_cli.py")
    shutil.copy(HIDDEN / f"test_hidden_{name}.py", tmp / f"test_hidden_{name}.py")
    proc = subprocess.run(
        ["uv", "run", "--with", "pytest", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rA", str(tmp)],
        cwd=root, capture_output=True, text=True, timeout=600,
        env={**__import__("os").environ, "PYTHONPATH": f"{root}:{tmp}"},
    )
    out = proc.stdout + proc.stderr
    passed = len(re.findall(r"^PASSED", out, re.M))
    failed = len(re.findall(r"^(?:FAILED|ERROR)", out, re.M))
    return passed, passed + failed, "; ".join(re.findall(r"^FAILED \S+::(\S+)", out, re.M))[:400]


def grade(run_dir: Path, eval_name: str) -> dict:
    repo = run_dir / "repo"
    outputs = run_dir / "outputs"
    ctx = repo / ".context"
    checkout, branch, subjects = feature_checkout(repo)
    commit_times = [int(s.split(" ", 1)[0]) for s in subjects]
    exp = []

    def add(text, passed, evidence):
        exp.append({"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]})

    plans = files(ctx, "plans/*.md") + files(repo, "plans/*.md", ".cursor/plans/*.md") + files(checkout, "plans/*.md", ".cursor/plans/*.md")
    phased = [p for p in plans if len(PHASE_HEADER.findall(p.read_text(encoding="utf-8", errors="replace"))) >= 3]
    add("C1 plan with at least 3 numbered phases", phased, phased[:1] or [p.name for p in plans])
    reviews = has(files(ctx, "reviews/*.md", "**/reviews/plan_*.md"), r"RUN_BY_COMMAND:\s*plan-review")
    add("C2 plan reviewed by a plan-review peer", reviews, [p.name for p in reviews])
    adv = has(files(ctx, "adversarial/*.md", "**/adversarial*.md"), r"de-adversarial|adversarial")
    add("C3 adversarial review ran", adv, [p.name for p in adv])
    phase_commits = [s for s in subjects if re.search(r"(?i)\bphase\s*\d+", s)]
    add("C4 work committed in phases (>=3 commits, phase-named or not)", len(subjects) >= 3,
        f"branch {branch}: {len(subjects)} commits, {len(phase_commits)} name a phase")
    pr = outputs / "PR.md"
    add("C5 PR record written", pr.is_file() and len(pr.read_text(encoding="utf-8").strip()) > 50, pr)
    pr_reviews = files(ctx, "prs/reviews/*.md", "**/PR_REVIEW*.md", "reviews/pr_*.md")
    add("C6 PR reviewed (review artifact)", pr_reviews, [p.name for p in pr_reviews])
    # Re-review evidence: the review artifacts cite two or more distinct branch commits,
    # i.e. a later head was reviewed after an earlier one (files are updated in place,
    # so mtimes cannot tell a first review from a re-review).
    shas = git(repo, "rev-list", "--reverse", f"{baseline(repo)}..{branch}").splitlines()
    review_text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in pr_reviews)
    cited = sorted({i for i, sha in enumerate(shas) if sha[:7] in review_text})
    fixes_after_first = len(shas) - 1 - cited[0] if cited else 0
    add("C7 review -> fix commits -> re-review of a later head", len(cited) >= 2,
        f"review cites {len(cited)} branch commits {[shas[i][:7] for i in cited]}; {fixes_after_first} commits after the first reviewed head")
    cards = files(ctx, "benchmarks/*.json", "test-benchmarks/*", "**/*code*.json")
    add("C8 test scorecard produced", cards, [p.name for p in cards][:3])
    texts = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in (outputs / "summary.md", pr) if p.is_file())
    q = QUESTION.findall(texts)
    add("C9 ran autonomously (no questions to the user in outputs)", (outputs / "summary.md").is_file() and not q, q or "summary present")

    done, why = own_completion_gate(run_dir, repo)
    if done is not None:
        add("C10 run ended without a hard stop (session record)", done, why)

    passed, total, failing = hidden_results(checkout, eval_name)
    add("Q1 all hidden acceptance tests pass", total and passed == total, f"{passed}/{total} {failing}")
    code, tail = pytest(checkout)
    add("Q2 full test suite green", code == 0, tail)
    added = count_tests(checkout) - 6
    add("Q3 at least 5 new tests", added >= 5, f"{added} test functions added")
    return {"expectations": exp, "hidden": {"passed": passed, "total": total}, "branch": branch,
            "checkout": str(checkout), "attestation": attestation_coverage(ctx)}


def own_completion_gate(run_dir: Path, repo: Path) -> tuple[bool | None, str]:
    """Did the run end without a hard stop? Reads the session record the run left.

    Both harnesses keep a per-worktree session record with `hard_stop`. Re-running
    their gates after the run is not valid: Cadence's A1 fails once R7 closes the
    session. A run with no session record (a one-shot baseline) gives None (n/a).
    """
    records = sorted((repo / ".context" / "sessions" / "by-worktree").glob("*.json"))
    if not records:
        return None, "no session record (no harness)"
    stops = []
    for path in records:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False, f"unreadable session record {path.name}"
        if data.get("hard_stop"):
            stops.append(f"{path.name}: {data.get('hard_stop_reason') or 'hard_stop set'}")
    return (not stops), ("; ".join(stops) if stops else f"{len(records)} session record(s), no hard stop")


def attestation_coverage(ctx: Path) -> dict:
    """Cadence on Claude Code: verdict files whose current content a hook attested (informational)."""
    import hashlib

    verdict_globs = ("vibetest/*.md", "reviews/plan_*.md", "adversarial/*.md", "benchmarks/*.json", "prs/reviews/*.md")
    verdicts = [p for g in verdict_globs for p in ctx.glob(g) if p.is_file()]
    entries = []
    for log in ctx.glob("attest/*.jsonl"):
        if log.name.endswith(".agents.jsonl"):
            continue
        for line in log.read_text(encoding="utf-8").splitlines():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    latest = {}
    for e in entries:
        latest[e.get("path")] = e.get("sha256")
    covered = [p for p in verdicts
               if latest.get(p.relative_to(ctx).as_posix()) == hashlib.sha256(p.read_bytes()).hexdigest()]
    return {"verdict_files": len(verdicts), "attested_current": len(covered),
            "uncovered": [p.relative_to(ctx).as_posix() for p in verdicts if p not in covered][:10]}


if __name__ == "__main__":
    run_dir, eval_name = Path(sys.argv[1]), sys.argv[2]
    result = grade(run_dir, eval_name)
    (run_dir / "grading.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    ok = sum(e["passed"] for e in result["expectations"])
    print(f"{run_dir.parent.name}/{run_dir.name}: {ok}/{len(result['expectations'])} hidden {result['hidden']}")
