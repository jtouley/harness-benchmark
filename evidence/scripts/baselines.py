"""Print the baseline rows the cadence-core runs are compared with, from the commits that hold them.

Usage (from the repository root, with origin fetched):
    git fetch origin main ccr-3d2e0c73-lr6bdt
    python3 evidence/scripts/baselines.py > evidence/outputs/baselines.txt

1. The 15 October one-shots: docs/evidence/2026-10-15-pipeline-trials.json on origin/main (rows with
   counted: true and mode agent or regrade: the P1 one-shots are counted as regrades of their own trees). The rows record the requested model. The session results that would
   show the served model (results/runs/, git-ignored) are not in the repository.
2. The 19 October cadence-core Haiku P1 run (5 of 7): docs/evidence/2026-10-19-pipeline-cadence-core/
   P1-cadence-core-haiku-1/ on branch ccr-3d2e0c73-lr6bdt at d4f9b00. Its result.json carries Claude
   Code's modelUsage, the models that actually served the session.
"""
from __future__ import annotations

import json
import subprocess


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def show(rev: str, path: str):
    return json.loads(git("show", f"{rev}:{path}"))


def main() -> None:
    path = "docs/evidence/2026-10-15-pipeline-trials.json"
    head = git("rev-parse", "origin/main").strip()
    history = git("log", "--follow", "--format=%h %ad %s", "--date=short", "origin/main", "--", path).strip().splitlines()
    print(f"1. {path} at origin/main {head}")
    print("   history of the file (newest first):")
    for line in history:
        print(f"     {line}")
    print(f"   {'run':24} {'task':4} {'model (recorded)':20} {'reward':8} {'checks':6} {'counted'}")
    for r in show(head, path):
        if r.get("mode") in ("agent", "regrade") and r.get("counted"):
            print(f"   {r['run']:24} {r['task']:4} {r['model']:20} {r['reward']!s:8} {r['checks']:6} {r['counted']}")

    rev = "d4f9b00"
    base = "docs/evidence/2026-10-19-pipeline-cadence-core/P1-cadence-core-haiku-1"
    full = git("rev-parse", rev).strip()
    grade, prov, result = (show(rev, f"{base}/{f}") for f in ("grade.json", "provenance.json", "result.json"))
    print(f"\n2. {base} at {full} (branch ccr-3d2e0c73-lr6bdt)")
    print(f"   provenance: cadence {prov.get('cadence_sha')} ({prov.get('cadence_branch')}), requested model {prov.get('model')}, "
          f"{prov.get('claude_version')}")
    print(f"   served models (result.json modelUsage): {sorted((result.get('modelUsage') or {}).keys())}")
    print(f"   grade: reward {grade.get('reward')}, passed {grade.get('passed')}/{grade.get('total')}, "
          f"idempotent {grade.get('idempotent')}, stream_ok {grade.get('stream_ok')}")
    for k, v in sorted((grade.get("checks") or {}).items()):
        print(f"     check {k}: pass={v.get('pass')}")


if __name__ == "__main__":
    main()
