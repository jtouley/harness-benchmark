import pathlib, sys, tempfile
REPO = pathlib.Path("/var/tmp/revieweval/r1-current-vs-pr228/review-01/new_skill/run-1/repo")
sys.path.insert(0, str(REPO))
from pipeline.stream_consumer import StreamConsumer, read_column
def good(i, **c):
    e = {"meta": {"id": f"ev-{i}"}, "type": "edit", "namespace": 0, "wiki": "enwiki",
         "timestamp": 1792021600 + i, "bot": False, "length": {"old": 1, "new": 2}}
    e.update(c); return e
lake = pathlib.Path(tempfile.mkdtemp()) / "lake"
c = StreamConsumer(lake_dir=lake, url="http://127.0.0.1:1/", duration=0.1, clock=lambda: 0.0)
for i in range(1, 4):
    c._accept(good(i), f"sse-{i}"); c._flush()
folder = lake / "stream_checkpoint"
print("checkpoint files:", sorted(p.name for p in folder.glob("*.parquet")))
print("checkpoint rows:", read_column(folder, "last_event_id"), read_column(folder, "high_water"))
c2 = StreamConsumer(lake_dir=lake, url="http://127.0.0.1:1/", duration=0.1, clock=lambda: 0.0)
print("restored last_landed_id:", c2.last_landed_id, "| high_water:", c2.high_water, "| seen:", len(c2.seen))
