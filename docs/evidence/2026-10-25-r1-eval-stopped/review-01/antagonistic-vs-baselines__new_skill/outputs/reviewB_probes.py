"""Reviewer B reproduction probes for pipeline/stream_consumer.py.

Each probe serves a crafted SSE stream from a local HTTP server, runs StreamConsumer against it in a
temporary lake, and reports whether the consumer crashed, what it logged, and what landed.
Run with the project interpreter, isolated:

    <repo>/.venv/bin/python -I <this file> <repo>

No network access beyond 127.0.0.1. No build targets are run.
"""

import contextlib
import http.server
import io
import json
import pathlib
import sys
import tempfile
import threading
import time

REPO = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path.cwd()
sys.path.insert(0, str(REPO))

from pipeline.stream_consumer import StreamConsumer, read_table  # noqa: E402


def event(i, **changes):
    e = {
        "meta": {"id": f"event-{i:06d}"},
        "type": "edit",
        "namespace": 0,
        "wiki": "enwiki",
        "server_name": "en.wikipedia.org",
        "timestamp": 1792021600 + i,
        "bot": False,
        "length": {"old": 1, "new": 2},
    }
    e.update(changes)
    return e


def sse(event_index, payload_bytes):
    return b"id: x%d\ndata: " % event_index + payload_bytes + b"\n\n"


def serve(chunks, status_line=b"HTTP/1.1 200 OK\r\n", hold_seconds=0.05):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.wfile.write(status_line + b"Content-Type: text/event-stream\r\nConnection: close\r\n\r\n")
            for chunk in chunks:
                self.wfile.write(chunk)
                self.wfile.flush()
            time.sleep(hold_seconds)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/v2/stream/recentchange"


GOOD = sse(9, json.dumps(event(9)).encode())


def probe(name, chunks, status_line=b"HTTP/1.1 200 OK\r\n", duration=1.0):
    tmp = pathlib.Path(tempfile.mkdtemp()) / "lake"
    server, url = serve(chunks, status_line)
    stderr = io.StringIO()
    outcome = "no crash"
    try:
        with contextlib.redirect_stderr(stderr):
            StreamConsumer(
                lake_dir=tmp, url=url, duration=duration, reconnect_seconds=0.05, socket_timeout=2.0
            ).run()
    except Exception as exc:  # the probe reports the crash; it does not hide it
        outcome = f"CRASH {type(exc).__name__}: {str(exc)[:100]}"
    finally:
        server.shutdown()
        server.server_close()
    landed = read_table(tmp / "stream_raw")
    rows = [] if landed is None else [(r["event_id"], r["namespace"], r["wiki"]) for r in landed.to_pylist()]
    print(f"[{name}]")
    print(f"  outcome: {outcome}")
    print(f"  stderr:  {stderr.getvalue().strip()[:160]!r}")
    print(f"  landed stream_raw rows (event_id, namespace, wiki): {rows}")


def main():
    probe("baseline: one good event", [GOOD])
    probe("invalid UTF-8 byte in a data line", [b"id: b\ndata: \xff\xfe\n\n", GOOD])
    probe(
        "meta.id is a list (unhashable)",
        [sse(2, json.dumps(event(2, meta={"id": ["x"]})).encode()), GOOD],
    )
    probe("type is a list (unhashable)", [sse(3, json.dumps(event(3, type=["edit"])).encode()), GOOD])
    probe("garbage HTTP status line", [], status_line=b"HTTP/1.1 garbage\r\n")
    probe("namespace is a non-numeric string", [sse(4, json.dumps(event(4, namespace="Talk")).encode()), GOOD])
    probe("namespace is numeric string, wiki is integer", [sse(5, json.dumps(event(5, namespace="0", wiki=123)).encode()), GOOD])

    # Silent stream: one event, then no heartbeat and no EOF. DURATION is 0.5 s.
    tmp = pathlib.Path(tempfile.mkdtemp()) / "lake"
    server, url = serve([GOOD], hold_seconds=30)
    started = time.monotonic()
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            StreamConsumer(
                lake_dir=tmp, url=url, duration=0.5, reconnect_seconds=0.05, socket_timeout=5.0
            ).run()
    finally:
        server.shutdown()
        server.server_close()
    print("[silent stream, no heartbeats]")
    print(f"  DURATION 0.5 s, run() returned after {time.monotonic() - started:.2f} s (socket_timeout 5.0)")


if __name__ == "__main__":
    main()
