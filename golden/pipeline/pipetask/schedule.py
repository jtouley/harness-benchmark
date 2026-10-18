"""The replay schedule: which frame the replay server sends at each position, from a seed.

The frozen capture is a list of frames in arrival order. The schedule turns it into the delivered
sequence and injects the stream faults of the trap catalog (docs/plans/tasks/pipeline-traps.md, "Stream faults"):

- F3: frames are shuffled inside short blocks, so events arrive out of event-time order by a few seconds.
- F4: a batch of edits from one 5-minute window is held back and delivered once the stream has moved
  12 to 20 minutes past that window's end.
- F5: one frame whose data is not valid JSON.
- F1: the server closes the connection after a few scheduled positions (each fires once per server).
- F2: follows from the SSE ids. Each id carries a Kafka-style timestamp (the running maximum of the
  captured ids, so ids never go back). A reconnect with Last-Event-ID resumes at the first position whose
  timestamp is at least that one, so the frames that share it are sent again. Disconnects are placed
  inside such groups, so every F1 also causes F2.
- F6 (stop and start) is the grader's doing, not the server's.

Everything here is a pure function of the capture and the seed, so the answer key can be computed from
the same schedule the server serves.
"""

from __future__ import annotations

import gzip
import json
import random
from dataclasses import dataclass, field
from pathlib import Path

WINDOW_SECONDS = 300
LATE_AFTER_SECONDS = 600
EDIT_TYPES = ("edit", "new")
TOPIC = "eqiad.mediawiki.recentchange"


@dataclass(frozen=True)
class Frame:
    """One captured SSE frame: the raw id and data strings, and the capture's receive time."""

    id: str
    data: str
    recv: float

    def id_timestamp(self) -> int:
        """The Kafka timestamp of this event's own topic in the SSE id (the live service lists both
        data centres' positions; the other entry is the last position seen there, often older)."""
        stamps = {p.get("topic"): int(p["timestamp"]) for p in json.loads(self.id) if "timestamp" in p}
        if not stamps:
            raise ValueError(f"frame id has no timestamp: {self.id}")
        try:
            topic = (json.loads(self.data).get("meta") or {}).get("topic")
        except ValueError:
            topic = None
        return stamps.get(topic, max(stamps.values()))


@dataclass(frozen=True)
class Delivered:
    """One position of the delivered sequence."""

    frame: int | None  # index into the capture; None for the injected invalid frame
    data: str
    id_ts: int  # the timestamp written into the SSE id at this position
    vrecv: float  # virtual receive time, used for pacing


@dataclass(frozen=True)  # cached and shared by the replay server (replay._plan)
class Schedule:
    seed: int
    positions: list[Delivered]
    disconnects: list[int]  # close the connection after sending these positions
    late_batch: list[int] = field(default_factory=list)  # capture indices held back (F4)
    late_window_start: int = 0
    late_insert_at: int = 0  # position of the first held-back frame
    invalid_at: int = 0  # position of the invalid frame (F5)

    def sse_id(self, pos: int) -> str:
        ts = self.positions[pos].id_ts
        return json.dumps(
            [{"topic": TOPIC, "partition": 0, "timestamp": ts},
             {"topic": "codfw.mediawiki.recentchange", "partition": 0, "offset": -1}],
            separators=(",", ":"),
        )

    def resume_position(self, last_event_id: str | None) -> int:
        """First position to send for a client that sends this Last-Event-ID (0 when absent)."""
        if not last_event_id:
            return 0
        try:
            parts = json.loads(last_event_id)
            ts = max(int(p["timestamp"]) for p in parts if isinstance(p, dict) and "timestamp" in p)
        except (ValueError, TypeError):
            return 0
        for pos, d in enumerate(self.positions):
            if d.id_ts >= ts:
                return pos
        return len(self.positions)


def load_capture(path: Path) -> list[Frame]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [Frame(r["id"], r["data"], float(r["recv"])) for r in map(json.loads, fh)]


def event(frame: Frame) -> dict | None:
    try:
        return json.loads(frame.data)
    except ValueError:
        return None


def _is_countable_edit(ev: dict | None) -> bool:
    return bool(ev) and ev.get("type") in EDIT_TYPES and (ev.get("meta") or {}).get("domain") != "canary"


def _shuffle_blocks(order: list[int], rng: random.Random, share: float = 0.3) -> list[int]:
    out: list[int] = []
    i = 0
    while i < len(order):
        size = rng.randint(20, 60)
        block = order[i:i + size]
        if rng.random() < share:
            rng.shuffle(block)
        out.extend(block)
        i += size
    return out


def _pick_late_batch(frames: list[Frame], events: list[dict | None], rng: random.Random,
                     batch_size: int) -> tuple[int, list[int]]:
    """The window with the most en.wikipedia edits among the full windows that leave room for the
    20-minute delay before the capture ends, and a sample of its en.wikipedia edits (so the held-back
    batch moves that window's count, which check 6 reads)."""
    lo, hi = frames[0].id_timestamp() // 1000, frames[-1].id_timestamp() // 1000
    first, last = lo + WINDOW_SECONDS, hi - 2 * WINDOW_SECONDS - 20 * 60
    counts: dict[int, int] = {}
    for ev in events:
        if _is_countable_edit(ev) and ev.get("wiki") == "enwiki" and first <= ev["timestamp"] <= last:
            w = ev["timestamp"] - ev["timestamp"] % WINDOW_SECONDS
            counts[w] = counts.get(w, 0) + 1
    if not counts:  # a capture too short for the delay: any window with edits (tests)
        for ev in events:
            if _is_countable_edit(ev):
                w = ev["timestamp"] - ev["timestamp"] % WINDOW_SECONDS
                counts[w] = counts.get(w, 0) + 1
    window = max(sorted(counts), key=lambda w: counts[w])
    members = [i for i, ev in enumerate(events) if _is_countable_edit(ev) and ev.get("wiki") == "enwiki"
               and window <= ev["timestamp"] < window + WINDOW_SECONDS]
    if not members:  # tests with other wikis only
        members = [i for i, ev in enumerate(events)
                   if _is_countable_edit(ev) and window <= ev["timestamp"] < window + WINDOW_SECONDS]
    batch = sorted(rng.sample(members, min(batch_size, len(members))))
    return window, batch


def build(frames: list[Frame], seed: int, *, late_batch_size: int = 60, disconnects: int = 3) -> Schedule:
    rng = random.Random(seed)
    events = [event(f) for f in frames]
    window, batch = _pick_late_batch(frames, events, rng, late_batch_size)
    held = set(batch)

    order = _shuffle_blocks([i for i in range(len(frames)) if i not in held], rng)

    # F4: insert the held batch where the stream's event time first passes window end + 12..20 min.
    due = window + WINDOW_SECONDS + rng.randint(12 * 60, 20 * 60)
    watermark, insert_at = 0, len(order)
    for pos, idx in enumerate(order):
        ev = events[idx]
        if ev and isinstance(ev.get("timestamp"), int):
            watermark = max(watermark, ev["timestamp"])
        if watermark >= due:
            insert_at = pos + 1
            break
    order = order[:insert_at] + batch + order[insert_at:]

    # F5: one frame that is not valid JSON, in the middle half of the stream.
    invalid_at = rng.randint(len(order) // 4, 3 * len(order) // 4)
    refs: list[int | None] = order[:invalid_at] + [None] + order[invalid_at:]

    positions: list[Delivered] = []
    id_ts, vrecv = 0, 0.0
    for ref in refs:
        if ref is None:
            nxt = frames[order[invalid_at]]
            positions.append(Delivered(None, nxt.data[: len(nxt.data) // 2], id_ts, vrecv))
            continue
        f = frames[ref]
        id_ts = max(id_ts, f.id_timestamp())
        vrecv = max(vrecv, f.recv)
        positions.append(Delivered(ref, f.data, id_ts, vrecv))

    # F1 (and F2): close after a position that shares its id timestamp with the next one.
    inside = [p for p in range(len(positions) // 10, len(positions) - 1)
              if positions[p].id_ts == positions[p + 1].id_ts]
    span = inside or list(range(1, len(positions) - 1))
    picks = sorted(rng.sample(span, min(disconnects, len(span))))

    late_at = insert_at + 1 if invalid_at <= insert_at else insert_at
    return Schedule(seed=seed, positions=positions, disconnects=picks, late_batch=batch,
                    late_window_start=window, late_insert_at=late_at, invalid_at=invalid_at)
