"""The answer key: it regenerates from the frozen inputs, and each catalogued trap that the data holds
changes the answer of the check the catalog maps it to (docs/plans/tasks/pipeline-traps.md)."""

from __future__ import annotations

import json
import socket
import threading
import urllib.request
from pathlib import Path

import pytest

from pipetask import key as keymod
from pipetask import replay
from pipetask import schedule as sched

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
    "5": {"W1", "W2", "W4", "W5", "F2", "F5", "S3-drops"},
    "6": {"S3", "F4", "F5", "F2"},
    "7": {"S3", "F4", "S3-drops"},
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


def test_check_5_accepts_only_readings_that_count_late_edits(committed):
    # the spec: check 5 counts every edit consumed, on time or late
    assert set(committed["stream"]["checks"]["5"]["accepted"]) == {"primary", "meta-dt"}


def test_the_late_set_is_the_same_whatever_moves_the_watermark(committed):
    rule = committed["stream"]["late_rule"]
    assert len(rule["readings"]) == 8 and rule["same_late_set"]
    assert set(rule["readings"].values()) == {committed["stream"]["schedule"]["late_batch_size"]}


def _consume_counting_resends(port: int) -> list[dict]:
    """A consumer with trap F2: it resumes with Last-Event-ID and counts every frame it is sent,
    skipping only frames that are not JSON. Stops at the first keepalive after the last frame."""
    events, last_id = [], None
    while True:
        headers = {"Last-Event-ID": last_id} if last_id else {}
        req = urllib.request.Request(f"http://127.0.0.1:{port}{replay.PATH}", headers=headers)
        data: list[str] = []
        with urllib.request.urlopen(req, timeout=30) as resp:
            for raw in resp:
                line = raw.decode("utf-8").rstrip("\n")
                if line == ":":
                    return events  # idle: the replay has sent everything
                if line.startswith("id: "):
                    last_id = line[4:]
                elif line.startswith("data: "):
                    data.append(line[6:])
                elif line == "" and data:
                    try:
                        events.append(json.loads("\n".join(data)))
                    except ValueError:
                        pass
                    data = []


def test_the_f2_trap_answers_are_what_a_consumer_counting_resends_gets_on_the_wire(committed):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    seed = committed["stream"]["seed"]
    server = replay.serve(CAPTURE, seed, port, speed=1e9, keepalive=0.2)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        wire = keymod._stream_answers(_consume_counting_resends(port))
    finally:
        server.shutdown()
        server.server_close()
    assert len(sched.build(sched.load_capture(CAPTURE), seed).disconnects) > 0
    for n in "567":
        check = committed["stream"]["checks"][n]
        assert wire[n] == check["traps"].get("F2", check["answer"]), n
