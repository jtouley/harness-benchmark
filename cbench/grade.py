"""Golden-task grading.

A golden task is a small repo, an issue, hidden tests and a reference patch.
`golden_check` proves each task is well-formed: the hidden tests fail on the
untouched repo and all pass once the reference patch is applied.

Live grading is not done here: each Harbor task carries the same hidden tests
and writes its own reward (see harbor.py).
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from .util import GOLDEN_DIR, clean_env, git_init, load_json, run, sha256_bytes, sha256_file

HIDDEN_DIRNAME = "cbench_hidden_tests"


def task_dirs() -> list[Path]:
    return sorted(p.parent for p in (GOLDEN_DIR / "tasks").glob("*/task.json"))


def task_digest(task_dir: Path) -> str:
    rows = []
    for path in sorted(p for p in task_dir.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        rows.append(f"{path.relative_to(task_dir).as_posix()}\t{sha256_file(path)}\n")
    return sha256_bytes("".join(rows).encode("utf-8"))


def _commit(path: Path, message: str) -> str:
    env = clean_env(home=path)
    run(["git", "add", "-A"], cwd=path, env=env)
    run(["git", "commit", "-q", "--allow-empty", "-m", message], cwd=path, env=env)
    return run(["git", "rev-parse", "HEAD"], cwd=path, env=env).stdout.strip()


def run_hidden(workspace: Path, task_dir: Path) -> dict:
    task = load_json(task_dir / "task.json")
    dest = workspace / HIDDEN_DIRNAME
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(task_dir / task["hidden"], dest)
    with tempfile.TemporaryDirectory() as tmp:
        junit = Path(tmp) / "junit.xml"
        proc = run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "no:randomly",
                    f"--junitxml={junit}", "--rootdir", str(workspace), HIDDEN_DIRNAME],
                   cwd=workspace, env=clean_env(home=Path(tmp)), timeout=task.get("timeout_seconds", 120),
                   check=False)
        cases = []
        if junit.is_file():
            for case in ET.parse(junit).getroot().iter("testcase"):
                name = f"{case.get('classname')}::{case.get('name')}"
                failed = any(child.tag in ("failure", "error") for child in case)
                skipped = any(child.tag == "skipped" for child in case)
                cases.append({"test": name, "outcome": "failed" if failed else "skipped" if skipped else "passed"})
    shutil.rmtree(dest)
    cases.sort(key=lambda c: c["test"])
    passed = sum(1 for c in cases if c["outcome"] == "passed")
    return {"exit": proc.returncode, "passed": passed, "total": len(cases), "cases": cases}


def golden_check() -> dict:
    out = {"tasks": {}}
    for task_dir in task_dirs():
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "ws"
            shutil.copytree(task_dir / "repo", ws)
            env = clean_env(home=Path(tmp))
            git_init(ws, env)
            _commit(ws, "base")
            before = run_hidden(ws, task_dir)
            run(["git", "apply", "--whitespace=nowarn", str(task_dir / "reference.patch")], cwd=ws, env=env)
            after = run_hidden(ws, task_dir)
        valid = after["total"] > 0 and after["passed"] == after["total"] and before["passed"] < before["total"]
        out["tasks"][task_dir.name] = {
            "task_sha256": task_digest(task_dir),
            "valid": valid,
            "before": {k: before[k] for k in ("passed", "total")},
            "after": {k: after[k] for k in ("passed", "total")},
        }
    return out
