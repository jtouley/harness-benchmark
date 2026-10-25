import sys, tempfile, pathlib
sys.path.insert(0, sys.argv[1])
from tests.stream_harness import FakeReplay, make_event
from pipeline.stream_consumer import StreamConsumer, read_table
for label, mutate in [("namespace string", lambda e: e.__setitem__("namespace","Talk")),
                      ("bot string 'false'", lambda e: e.__setitem__("bot","false"))]:
    lake=pathlib.Path(tempfile.mkdtemp())/"lake"
    bad=make_event(2); mutate(bad)
    with FakeReplay([make_event(1), bad, make_event(3)]) as r:
        StreamConsumer(lake_dir=lake,url=r.url,duration=0.6,reconnect_seconds=0.05,socket_timeout=2.0).run()
    for t in ("stream_raw","stream_events"):
        tb=read_table(lake/t)
        print(label,t,tb.column_names)
        print("  ", [{k:v for k,v in row.items() if k in ("event_id","namespace","namespace__v_text","bot","actor_type")} for row in tb.to_pylist()])
