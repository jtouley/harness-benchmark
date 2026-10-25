import sys, pathlib, tempfile
sys.path.insert(0, sys.argv[1])
import dlt
from pipeline.stream_consumer import StreamConsumer, flatten, read_column, RAW_COLUMNS, EVENT_COLUMNS
from tests.stream_harness import FakeReplay, make_event, sse_id_for_event
tmp = pathlib.Path(tempfile.mkdtemp(dir=sys.argv[2])); lake = tmp / "lake"
ev = [make_event(i) for i in range(1, 11)]
with FakeReplay(ev[:3]) as r:
    StreamConsumer(lake_dir=lake, url=r.url, duration=0.5, reconnect_seconds=0.05, socket_timeout=1).run()
print("after run 1:", read_column(lake / "stream_raw", "event_id"))
# Simulate a crash after dlt normalize, before load: the next batch (4, 5) is a pending package.
c = StreamConsumer(lake_dir=lake, url="http://unused", duration=0)
rows = [flatten(e, sse_id_for_event(e)) for e in ev[3:5]]
p = c._pipeline
p.extract([dlt.resource(rows, name="stream_raw", write_disposition="append", columns=RAW_COLUMNS),
           dlt.resource([{**x, "window_start": 0, "is_late": False} for x in rows], name="stream_events", write_disposition="append", columns=EVENT_COLUMNS),
           dlt.resource([{"last_event_id": rows[-1]["sse_id"], "high_water": 0}], name="stream_checkpoint", write_disposition="replace")])
p.normalize()
print("pending package:", p.has_pending_data)
with FakeReplay(ev) as r:
    StreamConsumer(lake_dir=lake, url=r.url, duration=0.5, reconnect_seconds=0.05, socket_timeout=1).run()
raw = read_column(lake / "stream_raw", "event_id"); evs = read_column(lake / "stream_events", "event_id")
print("after restart stream_raw:", raw); print("stream_events:", evs)
print("DUPLICATES:", len(raw) - len(set(raw)), len(evs) - len(set(evs)))
