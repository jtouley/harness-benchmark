"""The pipeline task as an arm sees it: frozen inputs, an unpoisoned prompt, and a starting repository
that holds nothing hidden (docs/tasks/pipeline-family.md#prompt-hygiene)."""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from pathlib import Path

import pytest

from pipetask import assemble, manifest, prompt

PIPELINE = Path(__file__).resolve().parents[1] / "golden" / "pipeline"
TASKS = ("P1", "P2", "P3")
# The stack each Python skeleton pins (docs/tasks/P1-*.md, docs/tasks/P2-*.md), plus the shared
# modeling layer. P3 pins in build.sbt and requirements.txt instead (docs/tasks/P3-scala-spark.md).
STACK_PINS = {
    "P1": ("dlt[parquet]", "dbt-duckdb", "dbt-core", "duckdb"),
    "P2": ("pyarrow", "polars", "datafusion", "dbt-duckdb", "dbt-core", "duckdb"),
}


def _files(folder: Path) -> set[str]:
    return {p.relative_to(folder).as_posix() for p in folder.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and ".venv" not in p.parts}


def test_the_frozen_inputs_match_their_checksum_manifest():
    assert manifest.build() == json.loads(manifest.MANIFEST.read_text(encoding="utf-8"))


def test_the_frozen_inputs_stay_small():
    total = sum(p.stat().st_size for p in (PIPELINE / "data").rglob("*") if p.is_file())
    assert total < 20 * 1024 * 1024, total


@pytest.mark.parametrize("task", TASKS)
def test_the_prompt_is_the_spec_word_for_word(task):
    assert (PIPELINE / task / "prompt.md").read_text(encoding="utf-8") == prompt.prompt(task)


@pytest.mark.parametrize("task", TASKS)
def test_the_prompt_carries_no_trap_or_answer_knowledge(task):
    text = (PIPELINE / task / "prompt.md").read_text(encoding="utf-8").lower()
    for hint in ("trap", "canary", "connecticut", "planning region", "leading zero", "last-event-id",
                 "dedup", "watermark", "de-obligation", "notes for task builders", "answer key",
                 "staff", "production quality", "follow-up", "streamlit"):
        assert hint not in text, hint


@pytest.mark.parametrize("task", TASKS)
def test_the_starting_repository_holds_only_the_skeleton_and_the_raw_data(task, tmp_path):
    repo = assemble.assemble(task, tmp_path / "repo", git=False)
    files = _files(repo)
    skeleton = _files(PIPELINE / task / "skeleton")
    raw = {"data/raw/" + f for f in _files(PIPELINE / "data" / "raw")}
    assert files == skeleton | raw
    hidden = ("capture", "answer_key", "pipetask", "reference", "oracle_map", "DECISIONS", "trap")
    assert not [f for f in files if any(h in f for h in hidden)]
    # nothing the reference adds on top of the skeleton (its code, YAML, models) reaches the arm
    reference_only = _files(PIPELINE / task / "reference") - skeleton
    assert reference_only
    assert not files & reference_only
    # nor anything else of the task's builder folder (its prompt, P3's toolchain image and trial script)
    builder_only = {f.split("/", 1)[1] if "/" in f else f for f in _files(PIPELINE / task)
                    if not f.startswith(("skeleton/", "reference/"))}
    assert builder_only
    assert not files & (builder_only - skeleton)


@pytest.mark.parametrize("task", TASKS)
def test_the_reference_is_an_overlay_on_the_skeleton(task, tmp_path):
    repo = assemble.assemble(task, tmp_path / "repo", with_reference=True, git=False)
    assert _files(PIPELINE / task / "reference") <= _files(repo)
    assert (repo / "oracle_map.yml").exists() and (repo / "DECISIONS.md").exists()


@pytest.mark.parametrize("task", TASKS)
def test_the_untouched_skeleton_fails_both_targets(task, tmp_path):
    repo = assemble.assemble(task, tmp_path / "repo", git=False)
    for target in ("build", "stream"):
        assert subprocess.run(["make", target], cwd=repo, capture_output=True).returncode != 0


@pytest.mark.parametrize("task", ["P1", "P2"])
def test_the_skeleton_pins_its_stack_exactly(task):
    skeleton = PIPELINE / task / "skeleton"
    project = tomllib.loads((skeleton / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    deps = project["dependencies"]
    assert all("==" in d for d in deps), deps
    assert {d.split("==")[0] for d in deps} >= set(STACK_PINS[task])
    assert project["requires-python"] == "==3.12.*"
    lock = (skeleton / "uv.lock").read_text(encoding="utf-8")
    for dep in deps:
        name, version = dep.split("[")[0].split("==")[0], dep.split("==")[1]
        assert f'name = "{name}"\nversion = "{version}"' in lock, dep
    profiles = (skeleton / "transform" / "profiles.yml").read_text(encoding="utf-8")
    assert "out/warehouse.duckdb" in profiles


P3_SKELETON = PIPELINE / "P3" / "skeleton"
P3_IMAGE = PIPELINE / "P3" / "image" / "Dockerfile"


def test_the_p3_skeleton_pins_scala_spark_and_sbt_exactly():
    build = (P3_SKELETON / "build.sbt").read_text(encoding="utf-8")
    assert re.search(r'scalaVersion := "2\.13\.\d+"', build)
    deps = re.findall(r'"([\w.-]+)" %%? "([\w.-]+)" % "([^"]+)"', build)
    assert {(g, a) for g, a, _ in deps} == {("org.apache.spark", "spark-sql"), ("org.scalatest", "scalatest")}
    assert all(re.fullmatch(r"\d+\.\d+\.\d+", v) for _, _, v in deps), deps
    spark = next(v for _, a, v in deps if a == "spark-sql")
    assert spark.startswith("3.5.")
    sbt = (P3_SKELETON / "project" / "build.properties").read_text(encoding="utf-8")
    assert re.fullmatch(r"sbt\.version=1\.\d+\.\d+\n", sbt)


def test_the_p3_requirements_pin_every_package_with_hashes():
    text = (P3_SKELETON / "requirements.txt").read_text(encoding="utf-8")
    pins = dict(re.findall(r"^([a-z0-9][a-z0-9._-]*)==([^ ;\\]+)", text, re.MULTILINE))
    entries = re.findall(r"^[a-z0-9]", text, re.MULTILINE)
    assert len(pins) == len(entries)
    assert text.count("--hash=sha256:") >= len(pins)
    build = (P3_SKELETON / "build.sbt").read_text(encoding="utf-8")
    spark = re.search(r'"spark-sql" % "([^"]+)"', build).group(1)
    # dbt's Spark is the ingestion's Spark: the same version on both sides
    assert pins["pyspark"] == spark
    assert {"dbt-core", "dbt-spark", "pyspark"} <= set(pins)
    profiles = (P3_SKELETON / "transform" / "profiles.yml").read_text(encoding="utf-8")
    assert "type: spark" in profiles and "method: session" in profiles


def test_the_p3_toolchain_image_is_pinned_by_digest():
    text = P3_IMAGE.read_text(encoding="utf-8")
    froms = re.findall(r"^FROM (\S+)", text, re.MULTILINE)
    assert froms and all(re.search(r"@sha256:[0-9a-f]{64}$", f) for f in froms), froms
    assert re.search(r"temurin:17\.", text)  # JDK 17
    sbt = re.search(r"sbt\.version=(\S+)", (P3_SKELETON / "project" / "build.properties").read_text()).group(1)
    assert f"ARG SBT_VERSION={sbt}\n" in text
    assert re.search(r"ARG SBT_SHA256=[0-9a-f]{64}\n", text) and "sha256sum -c" in text
