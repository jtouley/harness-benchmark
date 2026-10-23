"""P4, the hold-out task (docs/plans/tasks/P4-holdout-library-loans.md): its data regenerates, its key
regenerates, its prompt is the spec, its reference grades 7 of 7 and rebuilds identically, a variant
with one check removed grades 6 of 7, and the driver refuses it without --holdout."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import duckdb
import pytest
import yaml

from loop import driver, fingerprints
from pipetask import assemble, oracle, p4grade, p4key, p4trial, prompt, trial

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "golden" / "pipeline"
P4 = PIPELINE / "P4"
RAW = P4 / "data" / "raw"
KEY_PATH = P4 / "key" / "answer_key.json"
GENERATE = P4 / "snapshot" / "generate.py"
needs_uv = pytest.mark.skipif(shutil.which("uv") is None or shutil.which("make") is None,
                              reason="the reference builds with uv and make")


def _files(folder: Path) -> set[str]:
    return {p.relative_to(folder).as_posix() for p in folder.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and ".venv" not in p.parts}


@pytest.fixture(scope="module")
def key() -> dict:
    return json.loads(KEY_PATH.read_text(encoding="utf-8"))


# --- the data and the key

def test_the_data_regenerates_byte_for_byte(tmp_path):
    subprocess.run([sys.executable, "-I", str(GENERATE), "--out", str(tmp_path)], check=True, capture_output=True)
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(p.name for p in RAW.iterdir())
    for p in RAW.iterdir():
        assert (tmp_path / p.name).read_bytes() == p.read_bytes(), p.name


def test_the_data_stays_small_and_holds_the_overlap():
    assert sum(p.stat().st_size for p in RAW.iterdir()) < 1024 * 1024
    h1 = (RAW / "loans_2025_h1.csv").read_text(encoding="utf-8").splitlines()[1:]
    h2 = (RAW / "loans_2025_h2.csv").read_text(encoding="utf-8").splitlines()[1:]
    assert set(h1) & set(h2), "the two loans files overlap by one week (trap D1)"
    fines = (RAW / "fines.csv").read_text(encoding="utf-8")
    assert re.search(r",-\d+\.\d\d$", fines, re.M), "a waiver is a negative row (trap D2)"
    assert '"$1,' in (RAW / "items.csv").read_text(encoding="utf-8"), "money text with a thousands separator (D6)"


def test_the_committed_key_is_what_the_data_gives(key):
    assert json.loads(json.dumps(p4key.build_key(RAW))) == key
    for n, check in key["checks"].items():
        assert check["sha256"] == p4key.digest(check["answer"]), n
    assert set(key["checks"]) == set(oracle.CHECKS)


def test_each_trap_the_catalog_maps_changes_its_checks_answer(key):
    traps = {n: set(c["traps"]) for n, c in key["checks"].items()}
    assert traps["1"] == {"D1"} and traps["2"] == {"D1"} and traps["3"] == {"D1", "D1-rows", "D3", "D7"}
    assert traps["4"] == {"D2"} and traps["5"] == {"D2", "D8"} and traps["6"] == set() and traps["7"] == {"D4", "D6"}
    # D7 on check 6: every patron with a return or a renewal in 2025 also has a checkout, so the data does
    # not reproduce it there; the key says so rather than faking it.
    assert {n: c["traps_not_reproduced"] for n, c in key["checks"].items() if c["traps_not_reproduced"]} == {"6": ["D7"]}


# --- the prompt and the skeleton

def test_the_prompt_is_the_request_word_for_word():
    assert (P4 / "prompt.md").read_text(encoding="utf-8") == prompt.prompt("P4")


def test_the_prompt_carries_no_trap_or_answer_knowledge():
    text = (P4 / "prompt.md").read_text(encoding="utf-8").lower()
    # "leading zero" is a stated rule of this spec, not a hint: P4's requirements are literal by design.
    for hint in ("trap", "overlap", "duplicate", "dedup", "thousands", "answer key", "grader",
                 "hold-out", "holdout", "d1", "january 2026", "the year before: "):
        assert hint not in text, hint
    numbered = re.findall(r"^\d\. ", text.split("### checks the analysts will run")[1].split("\n\n")[1], re.M)
    assert numbered == [f"{n}. " for n in range(1, 8)]  # one check per numbered requirement


def test_the_skeleton_pins_duckdb_exactly_and_fails_its_build(tmp_path):
    project = tomllib.loads((P4 / "skeleton" / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["requires-python"] == "==3.12.*" and project["dependencies"] == ["duckdb==1.5.6"]
    assert 'name = "duckdb"\nversion = "1.5.6"' in (P4 / "skeleton" / "uv.lock").read_text(encoding="utf-8")
    repo = assemble.assemble("P4", tmp_path / "repo", git=False)
    assert subprocess.run(["make", "build"], cwd=repo, capture_output=True).returncode != 0
    assert "stream" not in (repo / "Makefile").read_text(encoding="utf-8")


def test_the_starting_repository_holds_the_skeleton_and_the_p4_data_only(tmp_path):
    repo = assemble.assemble("P4", tmp_path / "repo", git=False)
    files = _files(repo)
    assert files == _files(P4 / "skeleton") | {"data/raw/" + f for f in _files(RAW)}
    assert not any(h in f for f in files for h in ("usaspending", "census", "answer_key", "pipetask", "reference",
                                                    "oracle_map", "DECISIONS", "generate"))


# --- the reference and the broken variants (the proof)

@pytest.fixture(scope="module")
def reference_result(tmp_path_factory, key) -> dict:
    repo = assemble.assemble("P4", tmp_path_factory.mktemp("p4") / "repo", with_reference=True)
    return p4trial.run(repo, key, build_timeout=600, logs=repo.parent / "logs")


@needs_uv
def test_the_reference_passes_every_check_and_rebuilds_identically(reference_result):
    failed = {n: c for n, c in reference_result["checks"].items() if not c["pass"]}
    assert reference_result["idempotent"], reference_result["changed_by_second_build"]
    assert failed == {} and reference_result["passed"] == 7 and reference_result["reward"] == 1.0
    assert all(c["interpretation"] == "primary" for c in reference_result["checks"].values())


@needs_uv
def test_the_reference_with_one_check_removed_grades_six_of_seven(tmp_path, key):
    repo = assemble.assemble("P4", tmp_path / "repo", with_reference=True, git=False)
    doc = yaml.safe_load((repo / "oracle_map.yml").read_text(encoding="utf-8"))
    del doc["checks"][3]
    (repo / "oracle_map.yml").write_text(yaml.safe_dump(doc), encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "broken"], cwd=repo, check=True)
    result = p4trial.run(repo, key, build_timeout=600, logs=tmp_path / "logs")
    assert result["idempotent"] and result["passed"] == 6 and result["total"] == 7
    assert result["reward"] == round(6 / 7, 4)
    assert "no entry for check 3" in result["checks"]["3"]["error"]


@needs_uv
def test_a_reference_that_keeps_the_overlap_fails_checks_one_to_three_and_the_grader_names_d1(tmp_path, key):
    repo = assemble.assemble("P4", tmp_path / "repo", with_reference=True, git=False)
    build = repo / "pipeline" / "build.py"
    text = build.read_text(encoding="utf-8")
    assert "select distinct loan_id, event" in text
    build.write_text(text.replace("select distinct loan_id, event", "select loan_id, event"), encoding="utf-8")
    subprocess.run(["make", "build"], cwd=repo, check=True, capture_output=True)
    result = p4grade.grade(repo, key)
    assert {n for n, c in result["checks"].items() if not c["pass"]} == {"1", "2", "3"}
    assert result["checks"]["1"]["traps"] == ["D1"] and result["checks"]["2"]["traps"] == ["D1"]
    assert result["checks"]["3"]["traps"] == ["D1-rows"]


# --- the grader reads what the run-twice check digests (issue #49)

def test_single_file_marts_are_graded_and_digested_alike(tmp_path, key):
    """A mart published as one Parquet file at the top of out/marts/ is read by the checks and by the
    idempotence digest, so a mart cannot be graded without being checked for a changed second build."""
    marts = tmp_path / "out" / "marts"
    marts.mkdir(parents=True)
    con = duckdb.connect()
    answer = key["checks"]["3"]["answer"]
    con.execute(f"copy (select {answer}::bigint as late_returns) to '{(marts / 'late.parquet').as_posix()}' (format parquet)")
    (tmp_path / "oracle_map.yml").write_text(yaml.safe_dump({"checks": {3: {"sql": "select late_returns from late"}}}),
                                             encoding="utf-8")
    assert p4grade.grade(tmp_path, key)["checks"]["3"]["pass"]
    assert set(trial.mart_digests(tmp_path)) == {"late"}


# --- the hold-out rules

def test_the_driver_refuses_p4_without_holdout(tmp_path, capsys):
    store = tmp_path / "store"
    store.mkdir()
    args = ["--run-id", "20261023-P4-cadence-haiku-1", "--kind", "benchmark", "--batch", "2026-10-23-final",
            "--task", "P4", "--arm", "baseline", "--transcript", str(tmp_path / "t.jsonl"), "--runs", str(tmp_path / "runs"),
            "--store", str(store), "--cwd", str(tmp_path), "--", "true"]
    assert driver.main(args) == 2
    assert "hold-out" in capsys.readouterr().err and not (tmp_path / "runs").exists()
    assert driver.main(["--holdout", *args]) == 0
    assert (tmp_path / "runs" / "20261023-P4-cadence-haiku-1" / "record.json").exists()


def test_p4_is_fingerprinted_and_is_no_golden_cadence_input():
    sources = fingerprints.reference_sources(ROOT)
    assert KEY_PATH in sources
    for name in ("pipeline/build.py", "oracle_map.yml", "DECISIONS.md", "Makefile"):
        assert P4 / "reference" / name in sources, name
    assert not (ROOT / "golden" / "cadence" / "P4.md").exists()
    assert all("P4" not in p.name for p in fingerprints.input_sources(ROOT))
    readme = (PIPELINE / "README.md").read_text(encoding="utf-8")
    assert "P4" in readme and "final check" in readme
