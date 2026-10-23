"""Fingerprints of the benchmark's reference material, so Cadence can prove it carries none of it.

    python -m loop.fingerprints --out <cadence>/tests/contract/benchmark_fingerprints.json

Reference material: the pipeline references (golden/pipeline/P*/reference), the answer key, and the live
tier's reference patches and hidden tests (golden/tasks/*). Lockfiles are left out: they list public
packages, not solutions.

Algorithm 1 (Cadence's contract test implements the same; the fixed vector in tests/test_loop_fingerprints.py
is tested in both repositories):
1. Each line is stripped, runs of whitespace become one space, and it is lower-cased. In a patch, the
   header lines (diff, index, ---, +++, @@) are dropped and the first +, - or space is removed.
2. Lines shorter than 8 characters, and lines that start with #, //, `import ` or `from `, are dropped.
3. Each run of 3 consecutive kept lines that has a line of 40 or more characters is a shingle: the 3 lines
   joined with a newline. Its fingerprint is the sha256 of its UTF-8 bytes.
Boilerplate (`if __name__ == "__main__":` and the like) gives no shingle; copied reference code does.
The output holds the hashes only, never the text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALGORITHM = 1
SHINGLE, MIN_LINE, LONG_LINE = 3, 8, 40
_PATCH_HEADER = ("diff ", "index ", "--- ", "+++ ", "@@")
_SKIP = ("#", "//", "import ", "from ")


def _lines(text: str, patch: bool) -> list[str]:
    out = []
    for line in text.splitlines():
        if patch:
            if line.startswith(_PATCH_HEADER):
                continue
            line = line[1:] if line[:1] in ("+", "-", " ") else line
        norm = re.sub(r"\s+", " ", line.strip()).lower()
        if len(norm) >= MIN_LINE and not norm.startswith(_SKIP):
            out.append(norm)
    return out


def fingerprints(text: str, patch: bool = False) -> set[str]:
    lines = _lines(text, patch)
    return {hashlib.sha256("\n".join(lines[i:i + SHINGLE]).encode()).hexdigest()
            for i in range(len(lines) - SHINGLE + 1) if max(map(len, lines[i:i + SHINGLE])) >= LONG_LINE}


def sources(root: Path = ROOT) -> list[Path]:
    found = [p for p in root.glob("golden/pipeline/P*/reference/**/*") if p.is_file()]
    found += list(root.glob("golden/tasks/*/reference.patch"))
    found += [p for p in root.glob("golden/tasks/*/hidden/**/*") if p.is_file()]
    found += [root / "golden/pipeline/key/answer_key.json"]
    return sorted(p for p in found if not p.name.endswith(".lock") and "__pycache__" not in p.parts)


def build(root: Path = ROOT) -> dict:
    hashes: set[str] = set()
    for path in sources(root):
        hashes |= fingerprints(path.read_text(encoding="utf-8", errors="ignore"), patch=path.suffix == ".patch")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
    return {"algorithm": ALGORITHM, "source": "jtouley/harness-benchmark", "source_commit": commit,
            "sources": ["golden/pipeline/P*/reference/**", "golden/pipeline/key/answer_key.json",
                        "golden/tasks/*/reference.patch", "golden/tasks/*/hidden/**"],
            "count": len(hashes), "sha256": sorted(hashes)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m loop.fingerprints", description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    data = build()
    args.out.write_text(json.dumps(data, indent=0) + "\n", encoding="utf-8")
    print(f"{data['count']} fingerprints of {len(sources())} files at {data['source_commit'][:7]} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
