"""Build iteration-4 blind folders: one anonymous letter per arm that delivered code."""
import json, random, re, shutil, subprocess, sys, tarfile, io
from pathlib import Path

# Usage: python build_blind.py [iteration-dir]   (default: the folder this script is in)
HERE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
PATHS = ["ledgerlite", "tests", "README.md", "pyproject.toml"]
ARMS = {
    "multicurrency": ["with_skill", "old_skill", "sonnet_oneshot", "haiku_oneshot", "opus_oneshot"],
    "budgets": ["with_skill", "with_skill_fixed", "old_skill", "sonnet_oneshot", "haiku_oneshot", "opus_oneshot"],
    "audit-undo": ["with_skill_fixed", "sonnet_oneshot", "haiku_oneshot", "opus_oneshot"],
}
SCRUB = [
    (re.compile(r"(?i)\s*\(phase \d+[a-z]?\)"), ""),
    (re.compile(r"(?i)\bphase \d+[a-z]?:\s*"), ""),
    (re.compile(r"review fixes \(R\d\)"), "review fixes"),
    (re.compile(r"\s*\((?:the ticket-)?(?:R\d-)?F\d+(?:,\s*(?:the ticket-)?(?:R\d-)?F\d+)*\)"), ""),
    (re.compile(r"\bR\d (fix(?:es)?)\b"), r"\1"),
    (re.compile(r"(?:the ticket-)?R\d-F\d+"), ""),
    (re.compile(r"the ticket-F\d+"), ""),
    (re.compile(r"(?i)\bship-feature\b"), "the change"),
    (re.compile(r"(?i)\bcadence\b"), "the change"),
    (re.compile(r"(?i)\bpipeline[- ]run\b[^\n]*"), ""),
    (re.compile(r"\b(?:cd|gh)-1\b"), "the ticket"),
    (re.compile(r"\((?:D|MF|SF|AC|G-[A-Z]{1,2}|R\d-?F|F)\d+[a-z]?\)"), ""),
    (re.compile(r"\b(?:MF|SF|AC|G-[A-Z]{1,2})-?\d+\b"), "the review"),
    (re.compile(r"\bD\d{1,2}\b(?=[ :,.)])"), "the plan"),
    (re.compile(r"\b(?:[APER][1-9]|P\d|E\d)\s+(?:review|gate|block)\b"), "review"),
    (re.compile(r"\s*\((?:the ticket-\w*(?:,\s*)?)+\)"), ""),
]

def git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True).stdout.strip()

def branch(repo):
    base = git(repo, "rev-list", "--max-parents=0", "HEAD").split()[0]
    best, ahead = "main", -1
    for ref in git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads").splitlines():
        n = int(git(repo, "rev-list", "--count", f"{base}..{ref}") or 0)
        if n > ahead:
            best, ahead = ref, n
    return base, best

def scrub(text):
    for rx, rep in SCRUB:
        text = rx.sub(rep, text)
    return text

out, mapping = HERE / "blind5", {}
random.seed(20261012)
shutil.rmtree(out, ignore_errors=True)
for task, arms in ARMS.items():
    letters = list("PQRSTU")[: len(arms)]
    shuffled = arms[:]
    random.shuffle(shuffled)
    mapping[task] = dict(zip(letters, shuffled))
    for letter, arm in mapping[task].items():
        repo = HERE / f"eval-{task}" / arm / "repo"
        base, ref = branch(repo)
        dest = out / task / letter
        dest.mkdir(parents=True)
        if git(repo, "branch", "--show-current") == ref:
            # The delivered working tree: committed, uncommitted and new files (two Haiku arms never committed).
            files = set(git(repo, "ls-files", "--", *PATHS).splitlines())
            files |= set(git(repo, "ls-files", "--others", "--exclude-standard", "--", *PATHS).splitlines())
            for rel in sorted(files):
                src = repo / rel
                if src.is_file() and "__pycache__" not in rel:
                    (dest / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest / rel)
            subprocess.run(["git", "-C", str(repo), "add", "-N", "--", *PATHS], capture_output=True)
            diff = git(repo, "diff", base, "--", *PATHS)
            subprocess.run(["git", "-C", str(repo), "reset", "-q", "--", *PATHS], capture_output=True)
            ref += " (working tree)"
        else:
            data = subprocess.run(["git", "-C", str(repo), "archive", ref, *[p for p in PATHS if git(repo, "ls-tree", ref, p)]],
                                  capture_output=True).stdout
            tarfile.open(fileobj=io.BytesIO(data)).extractall(dest)
            diff = git(repo, "diff", f"{base}..{ref}", "--", *PATHS)
        (dest / "CHANGE.diff").write_text(scrub(diff) + "\n", encoding="utf-8")
        for f in dest.rglob("*"):
            if f.is_file() and f.suffix in (".py", ".md", ".toml"):
                raw = f.read_text(encoding="utf-8")
                f.write_text(scrub(raw), encoding="utf-8")
        proc = subprocess.run(["uv", "run", "-q", "--with", "pytest", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rN"],
                              cwd=dest, capture_output=True, text=True)
        import re as _re
        last = (_re.findall(r"\d+ passed[^\n]*|\d+ failed[^\n]*", proc.stdout) or [proc.stdout.strip()[-80:]])[-1]
        print(f"{task}/{letter} <- {arm} ({ref}): {last}")
(HERE / "blind5_mapping.json").write_text(json.dumps(mapping, indent=2) + "\n")

# Fail before any grader starts if a harness clue survived the scrub.
CLUES = re.compile(r"(?i)cadence|ship-feature|pipeline|stages\.json|vibe-test|adversarial|plan-review|"
                   r"phase ?\d|\.context|RUN_BY|mutmut|mutant|\bR[1-7]\b|\bE[1-4]\b|ticket|\bD\d+\b|\bMF-|\bF0\d")
left = []
for f in out.rglob("*"):
    if f.is_file() and f.suffix in (".py", ".md", ".diff", ".toml") and ".venv" not in f.parts:
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if CLUES.search(line):
                left.append(f"{f.relative_to(out)}:{n}: {line.strip()[:120]}")
if left:
    print("harness clues left after the scrub:", *left, sep="\n")
    raise SystemExit(1)
print("scrub check: no harness clues")
