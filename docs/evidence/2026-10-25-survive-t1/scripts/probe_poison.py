"""A poison event after a successful flush: does a restart get past it?"""
import sys, json, http.server, threading, tempfile, pathlib
sys.path.insert(0, sys.argv[1])
from pipeline.stream_consumer import StreamConsumer, read_column
def ev(i, **kw):
    e = {"meta": {"id": f"e{i}"}, "type": "edit", "namespace": 0, "wiki": "enwiki", "timestamp": 1792021600 + i, "bot": False}
    e.update(kw); return e
events = [ev(1), ev(2), ev(3, meta={"id": ["x"]}), ev(4), ev(5)]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        last = self.headers.get("Last-Event-ID")
        start = 0 if last is None else int(last) - 1   # inclusive resume, like the replay
        self.send_response(200); self.end_headers()
        for i, e in enumerate(events[start:], start + 1):
            self.wfile.write(f"id: {i}\ndata: {json.dumps(e)}\n\n".encode()); self.wfile.flush()
            if i == 2 and last is None:
                return   # first connection drops after e2 so e1, e2 get flushed and checkpointed
s = http.server.ThreadingHTTPServer(("127.0.0.1",0),H); threading.Thread(target=s.serve_forever,daemon=True).start()
with tempfile.TemporaryDirectory() as tmp:
    lake = pathlib.Path(tmp)/"lake"
    for attempt in (1, 2, 3):
        try:
            StreamConsumer(lake_dir=lake, url=f"http://127.0.0.1:{s.server_address[1]}/", duration=0.8, reconnect_seconds=0.05, socket_timeout=1).run()
            print(attempt, "completed")
        except Exception as exc:
            print(attempt, "CRASHED", type(exc).__name__, exc)
        print("   stream_raw:", read_column(lake/"stream_raw","event_id"), "checkpoint:", read_column(lake/"stream_checkpoint","last_event_id"))
