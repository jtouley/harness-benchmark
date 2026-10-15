"""The replay server's schedule and its faults (docs/tasks/pipeline-traps.md#stream-faults-injected-by-the-replay-server-from-a-seed).

The schedule tests use a small synthetic capture, so each fault's position can be checked exactly.
"""

from __future__ import annotations

import gzip
import json
import socket
import threading
import urllib.request
from pathlib import Path

import pytest

from pipetask import key as keymod
from pipetask import replay, schedule

CAPTURE = Path(__file__).resolve().parents[1] / "golden" / "pipeline" / "data" / "capture" / "recentchange.jsonl.gz"

T0 = 1_790_000_000  # a multiple of 300, so windows start at T0


def synthetic_frames(n: int = 3000, seconds: int = 3600) -> list[schedule.Frame]:
    """n events evenly over `seconds`, two wikis, some sharing a millisecond id timestamp."""
    frames = []
    for i in range(n):
        t = T0 + i * seconds // n
        ev = {
            "meta": {"id": f"id-{i}", "domain": "en.wikipedia.org" if i % 3 else "fr.wikipedia.org",
                     "dt": "2026-09-21T00:00:00Z"},
            "wiki": "enwiki" if i % 3 else "frwiki",
            "type": "edit" if i % 5 else "log",
            "timestamp": t,
            "bot": i % 7 == 0,
            "length": {"old": 10, "new": 15},
        }
        ms = t * 1000 + (i % 2)  # pairs of frames share a millisecond
        fid = json.dumps([{"topic": schedule.TOPIC, "partition": 0, "timestamp": ms}])
        frames.append(schedule.Frame(fid, json.dumps(ev), float(t)))
    return frames


@pytest.fixture(scope="module")
def frames():
    return synthetic_frames()


@pytest.fixture(scope="module")
def plan(frames):
    return schedule.build(frames, seed=7)


def test_same_seed_same_schedule_other_seed_differs(frames, plan):
    again = schedule.build(frames, seed=7)
    assert [p.data for p in again.positions] == [p.data for p in plan.positions]
    assert again.disconnects == plan.disconnects
    other = schedule.build(frames, seed=8)
    assert [p.data for p in other.positions] != [p.data for p in plan.positions]


def test_every_captured_frame_is_delivered_once_plus_one_invalid_frame(frames, plan):
    delivered = [p.frame for p in plan.positions]
    assert sorted(i for i in delivered if i is not None) == list(range(len(frames)))
    assert delivered.count(None) == 1


def test_f5_the_invalid_frame_is_not_json_and_sits_where_scheduled(plan):
    bad = plan.positions[plan.invalid_at]
    assert bad.frame is None
    with pytest.raises(ValueError):
        json.loads(bad.data)
    assert len(plan.positions) // 4 <= plan.invalid_at <= 3 * len(plan.positions) // 4 + 1


def test_f4_the_late_batch_arrives_12_to_20_minutes_after_its_window(frames, plan):
    at, size = plan.late_insert_at, len(plan.late_batch)
    assert size > 0
    assert [p.frame for p in plan.positions[at:at + size]] == plan.late_batch
    window_end = plan.late_window_start + schedule.WINDOW_SECONDS
    seen = [json.loads(p.data)["timestamp"] for p in plan.positions[:at] if p.frame is not None]
    assert window_end + 12 * 60 <= max(seen) <= window_end + 20 * 60 + 60
    for idx in plan.late_batch:
        ts = json.loads(frames[idx].data)["timestamp"]
        assert plan.late_window_start <= ts < window_end
        assert json.loads(frames[idx].data)["type"] in schedule.EDIT_TYPES


def test_f3_events_arrive_out_of_order_by_a_few_seconds_only(frames, plan):
    late = set(plan.late_batch)
    stamps = [json.loads(p.data)["timestamp"] for p in plan.positions if p.frame is not None and p.frame not in late]
    inversions = sum(a > b for a, b in zip(stamps, stamps[1:], strict=False))
    assert inversions > 0
    running_max, worst = 0, 0
    for t in stamps:
        worst = max(worst, running_max - t)
        running_max = max(running_max, t)
    assert worst <= 90  # within a block of at most 60 frames at about one frame per 1.2 s


def test_ids_never_go_back(plan):
    stamps = [p.id_ts for p in plan.positions]
    assert stamps == sorted(stamps)


def test_f1_f2_each_disconnect_is_inside_a_timestamp_group_so_a_resume_resends(plan):
    assert len(plan.disconnects) == 3
    for pos in plan.disconnects:
        resume = plan.resume_position(plan.sse_id(pos))
        assert resume < pos  # at least two frames are sent again
        assert {p.id_ts for p in plan.positions[resume:pos + 1]} == {plan.positions[pos].id_ts}


def test_resume_without_or_with_a_bad_id_starts_at_the_beginning(plan):
    assert plan.resume_position(None) == 0
    assert plan.resume_position("not json") == 0


# ---------------------------------------------------------------------------------------- server


def _write_capture(frames, path: Path) -> Path:
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for f in frames:
            fh.write(json.dumps({"id": f.id, "data": f.data, "recv": f.recv}) + "\n")
    return path


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _read_frames(port: int, last_event_id: str | None = None, limit: int = 10**6) -> list[tuple[str, str]]:
    headers = {"Last-Event-ID": last_event_id} if last_event_id else {}
    req = urllib.request.Request(f"http://127.0.0.1:{port}{replay.PATH}", headers=headers)
    out, event_id, data = [], None, []
    with urllib.request.urlopen(req, timeout=10) as resp:
        for raw in resp:
            line = raw.decode("utf-8").rstrip("\n")
            if line.startswith("id: "):
                event_id = line[4:]
            elif line.startswith("data: "):
                data.append(line[6:])
            elif line == "" and data:
                out.append((event_id, "\n".join(data)))
                data = []
                if len(out) >= limit:
                    break
    return out


def test_server_closes_at_the_scheduled_point_and_resumes_from_last_event_id(frames, tmp_path):
    capture = _write_capture(frames[:1200], tmp_path / "capture.jsonl.gz")
    port = _free_port()
    server = replay.serve(capture, seed=3, port=port, speed=1e9, keepalive=0.05)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        plan = schedule.build(schedule.load_capture(capture), seed=3)
        first = _read_frames(port)
        assert len(first) == plan.disconnects[0] + 1  # F1: closed right after the scheduled position
        assert first[-1][1] == plan.positions[plan.disconnects[0]].data
        resumed = _read_frames(port, last_event_id=first[-1][0], limit=5)
        expected = plan.resume_position(first[-1][0])
        assert resumed[0][1] == plan.positions[expected].data  # F2: the shared timestamp is sent again
        assert resumed[0][1] in [d for _, d in first]
        # each disconnect fires once per server: a fresh reader now passes the first point
        again = _read_frames(port, limit=plan.disconnects[0] + 5)
        assert len(again) == plan.disconnects[0] + 5
    finally:
        server.shutdown()
        server.server_close()


def test_server_answers_404_off_the_stream_path(frames, tmp_path):
    capture = _write_capture(frames[:200], tmp_path / "capture.jsonl.gz")
    port = _free_port()
    server = replay.serve(capture, seed=1, port=port, speed=1e9)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with pytest.raises(urllib.error.HTTPError) as err:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/nope", timeout=5)
        assert err.value.code == 404
    finally:
        server.shutdown()
        server.server_close()


# ------------------------------------------------------------------ the frozen capture under the late rule


@pytest.fixture(scope="module")
def captured():
    return schedule.load_capture(CAPTURE)


def test_the_capture_holds_canary_events(captured):
    events = [schedule.event(f) for f in captured]
    assert any((ev or {}).get("meta", {}).get("domain") == "canary" for ev in events)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_f4_the_held_back_batch_is_late_by_the_rule_and_no_other_event_is(captured, seed):
    plan = schedule.build(captured, seed)
    batch = {json.loads(captured[i].data)["meta"]["id"] for i in plan.late_batch}
    assert keymod.late_ids(plan) == batch
