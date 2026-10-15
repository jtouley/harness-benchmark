"""The pipeline task as an arm sees it: frozen inputs, an unpoisoned prompt, and a starting repository
that holds nothing hidden (docs/tasks/pipeline-family.md#prompt-hygiene)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pipetask import assemble, manifest, prompt

PIPELINE = Path(__file__).resolve().parents[1] / "golden" / "pipeline"
TASKS_WITH_PROMPTS = ("P1",)


def test_the_frozen_inputs_match_their_checksum_manifest():
    assert manifest.build() == json.loads(manifest.MANIFEST.read_text(encoding="utf-8"))


def test_the_frozen_inputs_stay_small():
    total = sum(p.stat().st_size for p in (PIPELINE / "data").rglob("*") if p.is_file())
    assert total < 20 * 1024 * 1024, total


@pytest.mark.parametrize("task", TASKS_WITH_PROMPTS)
def test_the_prompt_is_the_spec_word_for_word(task):
    assert (PIPELINE / task / "prompt.md").read_text(encoding="utf-8") == prompt.prompt(task)


@pytest.mark.parametrize("task", TASKS_WITH_PROMPTS)
def test_the_prompt_carries_no_trap_or_answer_knowledge(task):
    text = (PIPELINE / task / "prompt.md").read_text(encoding="utf-8").lower()
    for hint in ("trap", "canary", "connecticut", "planning region", "leading zero", "last-event-id",
                 "dedup", "watermark", "de-obligation", "notes for task builders", "answer key",
                 "staff", "production quality", "follow-up", "streamlit"):
        assert hint not in text, hint


def test_the_starting_repository_holds_only_the_skeleton_and_the_raw_data(tmp_path):
    repo = assemble.assemble("P1", tmp_path / "repo", git=False)
    files = {p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file()}
    skeleton = {p.relative_to(PIPELINE / "P1" / "skeleton").as_posix()
                for p in (PIPELINE / "P1" / "skeleton").rglob("*") if p.is_file()}
    raw = {"data/raw/" + p.relative_to(PIPELINE / "data" / "raw").as_posix()
           for p in (PIPELINE / "data" / "raw").rglob("*") if p.is_file()}
    assert files == skeleton | raw
    hidden = ("capture", "answer_key", "pipetask", "reference", "oracle_map", "DECISIONS", "trap")
    assert not [f for f in files if any(h in f for h in hidden)]


def test_the_untouched_skeleton_fails_both_targets(tmp_path):
    repo = assemble.assemble("P1", tmp_path / "repo", git=False)
    for target in ("build", "stream"):
        assert subprocess.run(["make", target], cwd=repo, capture_output=True).returncode != 0


def test_the_skeleton_pins_its_stack():
    pyproject = (PIPELINE / "P1" / "skeleton" / "pyproject.toml").read_text(encoding="utf-8")
    for pin in ('"dlt[parquet]==', '"dbt-duckdb==', '"dbt-core==', '"duckdb=='):
        assert pin in pyproject
    assert (PIPELINE / "P1" / "skeleton" / "uv.lock").exists()
    profiles = (PIPELINE / "P1" / "skeleton" / "transform" / "profiles.yml").read_text(encoding="utf-8")
    assert "out/warehouse.duckdb" in profiles
