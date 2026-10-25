import sys, pathlib, json, http.server, threading
sys.path.insert(0, sys.argv[1])
from pipeline.stream_consumer import StreamConsumer
import duckdb
out = pathlib.Path(sys.argv[2])
def ev(i, **kw):
    e = {"meta": {"id": f"e{i}"}, "type": "edit", "namespace": 0, "wiki": "enwiki", "timestamp": 1792021600 + i, "bot": False}
    e.update(kw); return e
for name, bad in [("ns", ev(3, namespace="talk")), ("wiki", ev(3, wiki={"x": 1})), ("bot", ev(3, bot="false"))]:
    chunks = [f"id: {i}\ndata: {json.dumps(e)}\n\n".encode() for i, e in enumerate([ev(1), ev(2), bad, ev(4)])]
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self,*a): pass
        def do_GET(self):
            self.send_response(200); self.end_headers()
            for c in chunks: self.wfile.write(c)
    s = http.server.ThreadingHTTPServer(("127.0.0.1",0),H); threading.Thread(target=s.serve_forever,daemon=True).start()
    lake = out / name / "lake"
    StreamConsumer(lake_dir=lake, url=f"http://127.0.0.1:{s.server_address[1]}/", duration=0.6, reconnect_seconds=0.05, socket_timeout=1).run()
    s.shutdown()
    c = duckdb.connect()
    print(name, c.sql(f"describe select * from read_parquet('{lake}/stream_events/*.parquet', union_by_name=true)").fetchall())
    print(name, c.sql(f"select * exclude (_dlt_id) from read_parquet('{lake}/stream_events/*.parquet', union_by_name=true) where event_id='e3'").fetchall())
