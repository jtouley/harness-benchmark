"""Stream ingestion: the recentchange SSE stream into the lake, in micro-batches.

Each micro-batch is one dlt load. The consumer's position (the last SSE id, the next arrival number and
the event-time watermark) is saved in the dlt resource state, which dlt writes into the lake with the
same load as the batch. A restart reads it back, so it resumes where the last committed batch ended.
The server re-sends some events on a resume; the staging model keeps the first copy of each meta.id.

Each landed row is the event exactly as received (`event`, the JSON text) plus load metadata:
`sse_id`, `arrival_seq` (arrival order, across restarts), `watermark_before` (the largest event time
seen before this event arrived, in Unix seconds) and `received_at`. Frames that are not valid JSON go
to `recentchange_rejects` with their raw text.

    python -m pipeline.stream --duration 60
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

import dlt

from . import sse
from .lake import pipeline

STREAM_URL = os.environ.get("STREAM_URL", "http://localhost:8099/v2/stream/recentchange")
EVENTS = "recentchange_events"
FLUSH_EVENTS = 5000
FLUSH_SECONDS = 5.0


@dataclass
class Position:
    last_event_id: str | None = None
    next_seq: int = 0
    watermark: int = 0


def load_position(p: dlt.Pipeline) -> Position:
    try:
        p.sync_destination()  # the lake's copy of the state wins over a lost or stale local one
    except Exception:  # noqa: BLE001 - no lake yet: start from the beginning
        pass
    for source in p.state.get("sources", {}).values():
        saved = source.get("resources", {}).get(EVENTS, {}).get("position")
        if saved:
            return Position(**saved)
    return Position()


def commit(p: dlt.Pipeline, events: list[dict], rejects: list[dict], position: Position) -> None:
    """Land one micro-batch; the position travels in the same dlt load as the events."""
    saved = asdict(position)

    @dlt.resource(name=EVENTS, write_disposition="append")
    def landed():
        dlt.current.resource_state()["position"] = saved
        yield events

    @dlt.resource(name="recentchange_rejects", write_disposition="append")
    def rejected():
        yield rejects

    p.run([landed(), rejected()], loader_file_format="parquet")


def event_time(event: dict) -> int | None:
    ts = event.get("timestamp")
    return ts if isinstance(ts, int) and not isinstance(ts, bool) else None


def consume(duration: float) -> int:
    p = pipeline("stream")
    position = load_position(p)
    deadline = time.monotonic() + duration
    stop = {"now": False}
    signal.signal(signal.SIGTERM, lambda *_: stop.update(now=True))
    events: list[dict] = []
    rejects: list[dict] = []
    last_flush, total = time.monotonic(), 0
    try:
        for msg in sse.stream(STREAM_URL, position.last_event_id, deadline):
            if stop["now"]:
                break
            if msg is not None:
                now = datetime.now(timezone.utc)
                try:
                    event = json.loads(msg.data)
                except ValueError:
                    rejects.append({"raw": msg.data, "sse_id": msg.id, "arrival_seq": position.next_seq,
                                    "received_at": now})
                    event = None
                if event is not None:
                    events.append({"event": msg.data, "sse_id": msg.id, "arrival_seq": position.next_seq,
                                   "watermark_before": position.watermark, "received_at": now})
                    t = event_time(event)
                    if t is not None and (event.get("meta") or {}).get("domain") != "canary":
                        position.watermark = max(position.watermark, t)
                position.next_seq += 1
                position.last_event_id = msg.id or position.last_event_id
            due = len(events) >= FLUSH_EVENTS or time.monotonic() - last_flush >= FLUSH_SECONDS
            if due and (events or rejects):
                commit(p, events, rejects, position)
                total += len(events)
                events, rejects, last_flush = [], [], time.monotonic()
    except KeyboardInterrupt:
        pass
    if events or rejects:
        commit(p, events, rejects, position)
        total += len(events)
    return total


def main() -> None:
    ap = argparse.ArgumentParser(description="Consume the recentchange stream into the lake.")
    ap.add_argument("--duration", type=float, required=True, help="seconds to consume")
    args = ap.parse_args()
    print(f"stream: landed {consume(args.duration)} events")


if __name__ == "__main__":
    main()
