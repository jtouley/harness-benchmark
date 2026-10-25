import pathlib, sys, tempfile
REPO = pathlib.Path("/var/tmp/revieweval/r1-current-vs-pr228/review-01/new_skill/run-1/repo")
sys.path.insert(0, str(REPO))
from pipeline.stream_consumer import StreamConsumer, read_table
sys.path.insert(0, str(pathlib.Path(__file__).parent))
def good(i, **c):
    e = {"meta": {"id": f"ev-{i}"}, "type": "edit", "namespace": 0, "wiki": "enwiki",
         "timestamp": 1792021600 + i, "bot": False, "length": {"old": 1, "new": 2}}
    e.update(c); return e
for label, ev in [("bot='false'", good(1, bot="false")), ("namespace='zero'", good(1, namespace="zero"))]:
    lake = pathlib.Path(tempfile.mkdtemp()) / "lake"
    c = StreamConsumer(lake_dir=lake, url="http://127.0.0.1:1/", duration=0.1, clock=lambda: 0.0)
    c._accept(ev, "s"); c._flush()
    raw = read_table(lake / "stream_raw").to_pylist()[0]
    evs = read_table(lake / "stream_events").to_pylist()[0]
    print(label, "-> raw bot:", raw["bot"], "| raw namespace:", raw["namespace"], "| events actor_type:", evs["actor_type"], "| events bot:", evs["bot"])
