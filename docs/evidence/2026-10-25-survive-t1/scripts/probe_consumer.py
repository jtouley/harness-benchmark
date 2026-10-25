"""Adversarial probes of pipeline.stream_consumer against a raw-bytes fake SSE server."""
import http.server, json, sys, tempfile, threading, pathlib, traceback, socketserver
sys.path.insert(0, sys.argv[1])
from pipeline.stream_consumer import StreamConsumer, read_column

def ev(i, **kw):
    e = {"meta": {"id": f"e{i}"}, "type": "edit", "namespace": 0, "wiki": "enwiki", "server_name": "en.wikipedia.org",
         "timestamp": 1792021600 + i, "bot": False, "length": {"old": 1, "new": 2}}
    e.update(kw); return e

def block(i, payload):
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    return b"id: " + f"[{{\"t\":{i}}}]".encode() + b"\ndata: " + body + b"\n\n"

def serve(chunks, raw_response=None):
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            if raw_response is not None:
                self.wfile.write(raw_response); return
            self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.end_headers()
            for c in chunks: self.wfile.write(c)
            self.wfile.flush()
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s

def probe(name, chunks, raw_response=None, duration=1.0):
    s = serve(chunks, raw_response)
    with tempfile.TemporaryDirectory() as tmp:
        lake = pathlib.Path(tmp) / "lake"
        url = f"http://127.0.0.1:{s.server_address[1]}/x"
        try:
            StreamConsumer(lake_dir=lake, url=url, duration=duration, reconnect_seconds=0.05, socket_timeout=1).run()
            res = "completed"
        except BaseException as exc:
            res = f"CRASHED {type(exc).__name__}: {str(exc)[:160]}"
        raw = read_column(lake / "stream_raw", "event_id")
        evs = read_column(lake / "stream_events", "event_id")
        print(f"[{name}] {res}\n    stream_raw={sorted(set(raw))} n={len(raw)} stream_events n={len(evs)}")
    s.shutdown()

good = [block(1, ev(1)), block(2, ev(2))]
probe("baseline", good + [block(3, ev(3))])
probe("invalid utf-8 in data line", good + [block(3, b'{"meta":{"id":"e3"},"x":"\xff\xfe"}'), block(4, ev(4))])
probe("meta.id is a list", good + [block(3, ev(3, meta={"id": [1, 2]})), block(4, ev(4))])
probe("meta.id is an int", good + [block(3, ev(3, meta={"id": 3})), block(4, ev(4))])
probe("namespace is a string", good + [block(3, ev(3, namespace="talk")), block(4, ev(4))])
probe("wiki is an object", good + [block(3, ev(3, wiki={"x": 1})), block(4, ev(4))])
probe("bot is string 'false'", good + [block(3, ev(3, bot="false")), block(4, ev(4))])
probe("timestamp float", good + [block(3, ev(3, timestamp=1792021603.5)), block(4, ev(4))])
probe("timestamp huge int", good + [block(3, ev(3, timestamp=10**20)), block(4, ev(4))])
probe("type is a list", good + [block(3, ev(3, type=["edit"])), block(4, ev(4))])
probe("bad status line", [], raw_response=b"garbage\r\n\r\n", duration=0.5)
