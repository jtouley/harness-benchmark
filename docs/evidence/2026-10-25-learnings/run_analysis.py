"""Run R8's collect, propose and gate over every stored Cadence run of harness-benchmark (read only).

    HB=. CADENCE_EVIDENCE=../cadence R8=../cadence python3 -I docs/evidence/2026-10-25-learnings/run_analysis.py OUT
"""
import gzip, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

# HB: this repository (with origin/runs-store fetched); CAD: a cadence clone that has the live-run evidence
# commits (9008b0e, 9954da6); R8: a cadence checkout of the R8 commit named in README.md.
HB = Path(os.environ.get("HB", "."))
CAD = Path(os.environ["CADENCE_EVIDENCE"])
R8 = Path(os.environ["R8"])
OUT = Path(sys.argv[1])  # e.g. docs/evidence/2026-10-25-learnings/runs
REV = "origin/main"
REPOS = {"jtouley/harness-benchmark": HB, "jtouley/cadence": CAD}

def git(repo, *a, binary=False):
    p = subprocess.run(["git", "-C", str(repo), *a], capture_output=True, check=False)
    return p.stdout if binary else p.stdout.decode()

def blob(ref, dest):
    if not ref or not ref.get("path") or not ref.get("store", "").startswith("git:"):
        return None
    repo, rev = ref["store"][4:].split("@", 1)
    raw = git(REPOS[repo], "show", f"origin/{rev}:{ref['path']}" if rev == "runs-store" else f"{rev}:{ref['path']}", binary=True)
    if not raw:
        return None
    if ref["path"].endswith(".gz") or raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    dest.write_bytes(raw)
    return dest

def ledger_from(bare, dest):
    for sha in git(bare, "log", "--all", "--format=%H", "--", ".context/findings.jsonl").split():
        text = git(bare, "show", f"{sha}:.context/findings.jsonl")
        if text.strip():
            dest.write_text(text); return dest
    return None

runs = [l.split("/")[1] for l in git(HB, "ls-tree", "--name-only", f"{REV}", "runs/").split() if "cadence" in l]
OUT.mkdir(parents=True, exist_ok=True)
env = {**os.environ, "CADENCE_HOME": str(R8)}
for run in runs:
    with tempfile.TemporaryDirectory(prefix="r8-", dir=os.environ.get("TMPDIR")) as tmp:
        tmp = Path(tmp)
        rec_text = git(HB, "show", f"{REV}:runs/{run}/record.json")
        rec = json.loads(rec_text); (tmp / "record.json").write_text(rec_text)
        args = ["collect", "--run-id", run, "--record", str(tmp / "record.json"), "--out-dir", str(tmp / "out"),
                "--cadence-sha", ((rec.get("cadence") or {}).get("sha") or "unrecorded"), "--ledger", str(tmp / "none")]
        t = blob(rec.get("transcript"), tmp / "t.jsonl")
        if t: args += ["--transcript", str(t)]
        b = blob(rec.get("tree"), tmp / "tree.bundle")
        if b:
            bare = tmp / "bare.git"
            subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
            subprocess.run(["git", "-C", str(bare), "fetch", "-q", str(b), "+refs/*:refs/*"], capture_output=True)
            args += ["--repo", str(bare)]
            led = ledger_from(bare, tmp / "findings.jsonl")
            if led: args[args.index("--ledger") + 1] = str(led)
        else:
            args += ["--repo", str(tmp / "none")]
        work = tmp / "ws"; work.mkdir()
        r = subprocess.run([sys.executable, str(R8 / "scripts/run_learnings.py"), *args], cwd=work, env=env, capture_output=True, text=True)
        if r.returncode: print(run, "collect failed", r.stdout, r.stderr[-500:]); continue
        p = subprocess.run([sys.executable, str(R8 / "scripts/run_learnings.py"), "propose", "--packet", str(tmp / "out" / f"{run}.packet.json"), "--out", str(OUT / f"{run}.md")], cwd=work, env=env, capture_output=True, text=True)
        if p.returncode:
            print(run, p.stderr[-800:]); break
        shutil.copy(OUT / f"{run}.md", tmp / "out" / f"{run}.md")
        c = subprocess.run([sys.executable, str(R8 / "scripts/run_learnings.py"), "--check", "--doc", str(tmp / "out" / f"{run}.md")], cwd=work, env=env, capture_output=True, text=True)
        print(run, c.stdout[:600] if c.returncode else "", "T" if t else "-", "B" if b else "-", p.stdout.strip().split("  ")[-1].split(" ->")[0], "| gate:", c.stdout.splitlines()[0][:60] if c.stdout else c.stderr[-200:])
