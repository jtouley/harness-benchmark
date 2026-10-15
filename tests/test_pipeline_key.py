"""The answer key: it regenerates from the frozen inputs, and each catalogued trap that the data holds
changes the answer of the check the catalog maps it to (docs/tasks/pipeline-traps.md)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipetask import key as keymod

PIPELINE = Path(__file__).resolve().parents[1] / "golden" / "pipeline"
KEY_PATH = PIPELINE / "key" / "answer_key.json"
RAW = PIPELINE / "data" / "raw"
CAPTURE = PIPELINE / "data" / "capture" / "recentchange.jsonl.gz"


@pytest.fixture(scope="module")
def committed():
    return json.loads(KEY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def regenerated(committed):
    return json.loads(json.dumps(keymod.build_key(RAW, CAPTURE, committed["stream"]["seed"])))


def test_the_committed_key_is_what_the_frozen_inputs_give(committed, regenerated):
    assert regenerated == committed


def test_each_answer_hash_is_the_hash_of_the_answer(committed):
    for section in ("batch", "stream"):
        for n, check in committed[section]["checks"].items():
            assert check["sha256"] == keymod.digest(check["answer"]), n


# Traps the frozen data reproduces, per check (the catalog's mapping, minus what the data lacks).
EXPECTED_TRAPS = {
    "1": {"B1", "B2", "B6", "B7"},
    "2": {"B3", "B6", "B7", "S1"},
    "3": {"B2", "B6"},
    "4": {"B4", "B5", "B7"},
    "5": {"W1", "W2", "W4", "W5", "F2", "F5"},
    "6": {"S3", "F4", "F5"},
    "7": {"S3", "F4"},
}


@pytest.mark.parametrize("check", sorted(EXPECTED_TRAPS))
def test_the_data_reproduces_the_catalogued_traps(committed, check):
    checks = {**committed["batch"]["checks"], **committed["stream"]["checks"]}
    assert EXPECTED_TRAPS[check] <= set(checks[check]["traps"])


def test_the_stream_has_late_events_and_the_batch_has_every_trap_fact(committed):
    assert committed["stream"]["checks"]["7"]["answer"] > 0
    facts = committed["batch"]["facts"]
    assert facts["negative_transactions"] > 0  # B2
    assert facts["no_county_transactions"] > 0 and facts["no_state_transactions"] > 0  # B5
    assert {"09001", "09110"} <= set(facts["ct_county_codes"])  # B4: old counties and planning regions
    assert any(f.startswith("09") for f in facts["counties_without_2024_estimate"])  # amendment fallback
