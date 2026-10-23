"""The saved golden inputs for Cadence runs (golden/cadence/) are specs only (golden/cadence/README.md).

Each file is exactly the text a run is given. No answer key, grader or reference solution text sits
there, and the P1 and P2 copies equal the pipeline prompts, which are built word for word from the specs.
"""

from __future__ import annotations

import re
from pathlib import Path

from loop import fingerprints

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "golden" / "cadence"
SAMPLES = sorted(p for p in GOLDEN.glob("*.md") if p.name != "README.md")


def test_the_folder_holds_the_readme_and_the_samples_only():
    assert [p.name for p in SAMPLES] == ["P1.md", "P2.md", "d1.md", "d2.md", "d3.md", "d4.md"]
    assert sorted(p.name for p in GOLDEN.iterdir()) == sorted(["README.md"] + [p.name for p in SAMPLES])


def test_the_pipeline_samples_equal_the_pipeline_prompts():
    from pipetask import prompt
    for task in ("P1", "P2"):
        text = (GOLDEN / f"{task}.md").read_text(encoding="utf-8")
        assert text == (ROOT / "golden" / "pipeline" / task / "prompt.md").read_text(encoding="utf-8")
        assert text == prompt.prompt(task)


def test_each_scenario_sample_is_one_spec_and_nothing_else():
    texts = {p.name: p.read_text(encoding="utf-8") for p in SAMPLES if p.name.startswith("d")}
    for name, text in texts.items():
        assert text.endswith("\n") and text.count("\n") == 1, name  # one line, one final newline
        assert text.startswith("Add a CSV export to the CLI."), name
        assert not text.startswith("/cadence"), name  # the command prefix is the execution, not the spec
    assert texts["d2.md"] == texts["d3.md"] == texts["d4.md"]
    assert texts["d1.md"] != texts["d2.md"]
    # d2 asks for the two deferrals on top of d1's request; d1 holds nothing that d2 does not.
    assert set(re.findall(r"[A-Za-z0-9-]+", texts["d1.md"])) <= set(re.findall(r"[A-Za-z0-9-]+", texts["d2.md"]))


def test_no_reference_material_sits_under_golden_cadence():
    """No fingerprint of a sample is a fingerprint of the answer key, a hidden test or a reference solution."""
    reference: set[str] = set()
    for path in fingerprints.reference_sources(ROOT):
        reference |= fingerprints.fingerprints(path.read_text(encoding="utf-8", errors="ignore"),
                                               patch=path.suffix == ".patch")
    assert reference
    for sample in SAMPLES:
        assert fingerprints.fingerprints(sample.read_text(encoding="utf-8")) & reference == set(), sample.name
    words = ("answer_key", "answer key", "grader", "reference solution", "hidden/")  # oracle_map.yml is a deliverable the spec names
    for sample in SAMPLES:
        low = sample.read_text(encoding="utf-8").lower()
        assert not any(w in low for w in words), sample.name


def test_the_inputs_are_fingerprinted():
    assert fingerprints.input_sources(ROOT) == SAMPLES
    data = fingerprints.build(ROOT)
    assert sorted(data["inputs"]) == [p.relative_to(ROOT).as_posix() for p in SAMPLES]
    assert all(len(h) == 64 for h in data["inputs"].values())
    assert data["inputs"]["golden/cadence/d2.md"] == data["inputs"]["golden/cadence/d3.md"]
    assert data["inputs"]["golden/cadence/d1.md"] != data["inputs"]["golden/cadence/d2.md"]
    p1 = fingerprints.fingerprints((GOLDEN / "P1.md").read_text(encoding="utf-8"))
    assert p1 and p1 <= set(data["sha256"])
