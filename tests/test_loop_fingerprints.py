"""Fingerprints of the benchmark's reference material, for Cadence's contamination test (loop/fingerprints.py).

Cadence must never carry text from golden/ (references, hidden tests, the answer key). Cadence keeps only
these sha256 values, never the text; its contract test applies the same algorithm to its own files.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from loop import fingerprints

ROOT = Path(__file__).resolve().parents[1]

# The fixed vector both repositories test: the same input must give the same fingerprints in each.
VECTOR = ("def answer(rows):\n"
          "    totals = {}  # a comment line counts too, as text\n"
          "    for row in rows:\n"
          "        totals[row.agency_name] = totals.get(row.agency_name, 0) + row.net_obligations\n"
          "    return totals\n")
VECTOR_SHA256 = sorted(hashlib.sha256(s.encode()).hexdigest() for s in [
    "def answer(rows):\ntotals = {} # a comment line counts too, as text\nfor row in rows:",
    "totals = {} # a comment line counts too, as text\nfor row in rows:\n"
    "totals[row.agency_name] = totals.get(row.agency_name, 0) + row.net_obligations",
    "for row in rows:\ntotals[row.agency_name] = totals.get(row.agency_name, 0) + row.net_obligations\n"
    "return totals",
])


def test_the_fixed_vector():
    assert sorted(fingerprints.fingerprints(VECTOR)) == VECTOR_SHA256


def test_boilerplate_gives_no_fingerprint():
    text = "import sys\nfrom pathlib import Path\n\ndef main():\n    return 0\n\nif __name__ == \"__main__\":\n    sys.exit(main())\n"
    assert fingerprints.fingerprints(text) == set()


def test_whitespace_and_case_do_not_change_a_fingerprint():
    assert fingerprints.fingerprints(VECTOR.upper().replace("    ", "\t")) == fingerprints.fingerprints(VECTOR)


def test_a_patch_is_read_as_its_lines():
    patch = "diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -0,0 +1,5 @@\n" + "".join(
        f"+{line}\n" for line in VECTOR.splitlines())
    assert fingerprints.fingerprints(patch, patch=True) == fingerprints.fingerprints(VECTOR)


def test_lockfiles_are_not_reference_material():
    assert not any(p.name.endswith(".lock") for p in fingerprints.sources(ROOT))
    assert any("answer_key" in p.name for p in fingerprints.sources(ROOT))
    assert any(p.name == "reference.patch" for p in fingerprints.sources(ROOT))


def test_the_cli_writes_the_hashes_and_never_the_text(tmp_path):
    out = tmp_path / "fp.json"
    subprocess.run([sys.executable, "-m", "loop.fingerprints", "--out", str(out)], cwd=ROOT, check=True)
    data = json.loads(out.read_text())
    assert data["algorithm"] == fingerprints.ALGORITHM and data["count"] == len(data["sha256"]) > 1000
    assert all(len(h) == 64 for h in data["sha256"]) and data["source_commit"]
    assert "select" not in out.read_text().lower()  # no reference text, only hashes
