"""Search every run transcript for contact with the benchmark's own files and with a second copy of the arm.

Usage (from the repository root):
    python3 evidence/scripts/isolation_search.py > evidence/outputs/isolation_search.txt

Scans evidence/runs/*/transcript.jsonl.gz: the input of every tool call (what an agent, main or peer,
asked to run, read or write) and the text of every tool result (what came back, such as a `find`
listing). Patterns:
  benchmark_repo   /home/user/harness-benchmark (the repository holding the key, grader and references)
  answer_key       answer_key
  grader           pipetask, grader.pyz, hb-grader, golden/pipeline
  reference        P1/reference, P2/reference, P3/reference, --with-reference
  cadence_copy     /home/user/cadence-core (this machine's checkout of the arm, at the same commit)
  other_harness    another harness's checkout or install from the tier 1-2 measurements (cbench cache, /tmp/cbench)
  tier12_sandbox   cadence-core's own tier 1-2 install sandbox (same commit)
Prints per run the number of tool calls and tool results that match each pattern, and the first
matches in context for the first five patterns.
"""
from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATTERNS = {
    "benchmark_repo": re.compile(r"/home/user/harness-benchmark"),
    "answer_key": re.compile(r"answer_key"),
    "grader": re.compile(r"pipetask|grader\.pyz|hb-grader|golden/pipeline"),
    "reference": re.compile(r"P[123]/reference\b|--with-reference"),
    "cadence_copy": re.compile(r"/home/user/cadence-core"),
    "other_harness": re.compile(r"cadence-bench/(?:src|installs)/(?!cadence-core@)[\w-]+@|/tmp/cbench/(?!cadence-core\b)[\w-]+"),
    "tier12_sandbox": re.compile(r"/tmp/cbench/cadence-core/|cadence-bench/installs/cadence-core@"),
}
SHOW = ("benchmark_repo", "answer_key", "grader", "reference", "other_harness")


def text_of(content) -> str:
    return content if isinstance(content, str) else json.dumps(content)


def main() -> None:
    total = {k: 0 for k in PATTERNS}
    for path in sorted((ROOT / "evidence/runs").glob("*/transcript.jsonl.gz")):
        calls = {k: 0 for k in PATTERNS}
        results = {k: 0 for k in PATTERNS}
        examples: list[str] = []
        n_calls = n_results = 0
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                msg = e.get("message")
                content = msg.get("content") if isinstance(msg, dict) else None
                if not isinstance(content, list):
                    continue
                for c in content:
                    if e.get("type") == "assistant" and c.get("type") == "tool_use":
                        n_calls += 1
                        s, bucket, kind = json.dumps(c.get("input")), calls, "call"
                    elif e.get("type") == "user" and c.get("type") == "tool_result":
                        n_results += 1
                        s, bucket, kind = text_of(c.get("content")), results, "result"
                    else:
                        continue
                    for name, pat in PATTERNS.items():
                        m = pat.search(s)
                        if m:
                            bucket[name] += 1
                            total[name] += 1
                            if name in SHOW and len(examples) < 5:
                                examples.append(f"    {kind} {name}: ...{s[max(0, m.start() - 80):m.end() + 80]}...")
        print(f"{path.parent.name}: {n_calls} tool calls, {n_results} tool results")
        print(f"  tool calls matching:   {calls}")
        print(f"  tool results matching: {results}")
        for ex in examples:
            print(ex)
    print(f"all runs, calls + results matching: {total}")


if __name__ == "__main__":
    main()
