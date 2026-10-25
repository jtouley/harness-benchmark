"""Edits with no namespace, landed in two loads that touch the same window, then dbt incremental."""
import sys, json, http.server, threading, pathlib, subprocess
root = pathlib.Path(sys.argv[1]); sys.path.insert(0, str(root))
from pipeline.stream_consumer import StreamConsumer
def ev(i):
    return {"meta": {"id": f"n{i}"}, "type": "edit", "wiki": "enwiki", "timestamp": 1792021800 + i, "bot": False}
def run(batch):
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self,*a): pass
        def do_GET(self):
            self.send_response(200); self.end_headers()
            for e in batch: self.wfile.write(f"id: {e['meta']['id']}\ndata: {json.dumps(e)}\n\n".encode())
    s = http.server.ThreadingHTTPServer(("127.0.0.1",0),H); threading.Thread(target=s.serve_forever,daemon=True).start()
    StreamConsumer(lake_dir=root/"lake", url=f"http://127.0.0.1:{s.server_address[1]}/", duration=0.5, reconnect_seconds=0.05, socket_timeout=1).run()
    s.shutdown()
    for d in ("window_5min","late_events","edits_by_wiki_actor"): (root/"out"/"marts"/d).mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(root/".venv/bin/dbt"),"build","--project-dir","transform","--profiles-dir","transform","--select","+mart_window_5min","+late_events","+edits_by_wiki_actor"], cwd=root, capture_output=True, text=True)
    print("\n".join(l for l in r.stdout.splitlines() if "FAIL" in l or "Done" in l or "ERROR" in l))
run([ev(1), ev(2)])
run([ev(3)])
import duckdb
print(duckdb.connect(str(root/"out/warehouse.duckdb"), read_only=True).sql("select * from main.window_5min").fetchall())
