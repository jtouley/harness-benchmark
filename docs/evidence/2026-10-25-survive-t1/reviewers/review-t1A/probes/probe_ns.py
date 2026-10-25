import sys, tempfile, pathlib, traceback
sys.path.insert(0, sys.argv[1])
from tests.stream_harness import FakeReplay, make_event
from pipeline.stream_consumer import StreamConsumer, read_column
for label, mutate in [
    ("namespace string", lambda e: e.__setitem__("namespace","Talk")),
    ("bot string 'true'", lambda e: e.__setitem__("bot","true")),
    ("meta.id int", lambda e: e["meta"].__setitem__("id",12345)),
    ("wiki dict", lambda e: e.__setitem__("wiki",{"x":1})),
]:
    tmp=tempfile.mkdtemp(); lake=pathlib.Path(tmp)/"lake"
    bad=make_event(2); mutate(bad)
    evs=[make_event(1), bad, make_event(3)]
    try:
        with FakeReplay(evs) as r:
            StreamConsumer(lake_dir=lake,url=r.url,duration=0.6,reconnect_seconds=0.05,socket_timeout=2.0).run()
        print(label, "OK raw=", read_column(lake/"stream_raw","event_id"), "events=", [ (x) for x in read_column(lake/"stream_events","actor_type")])
    except Exception as ex:
        print(label, "CRASH:", type(ex).__name__, str(ex).splitlines()[0][:200])
        print("   lake raw after crash:", read_column(lake/"stream_raw","event_id"))
