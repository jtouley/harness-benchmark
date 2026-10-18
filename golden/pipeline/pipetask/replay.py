"""Replay server: serves the frozen recentchange capture as Wikimedia EventStreams SSE.

    python -m pipetask.replay --capture data/capture/recentchange.jsonl.gz --seed 1 --port 8099

GET /v2/stream/recentchange answers like the real service: `:ok`, then one `event: message` frame per
event with an `id:` (a JSON list of Kafka positions) and a `data:` line. A client that sends
Last-Event-ID resumes from that id ([schedule.Schedule.resume_position]); without it, the replay starts
at the beginning of the capture. Frames are paced by the capture's receive times, `--speed` times
faster than real time. After the last frame the connection stays open and gets a comment every few
seconds, like an idle live stream. The faults are the schedule's ([schedule]).

Stdlib only, so it runs in any trial container without a virtual environment.
"""

from __future__ import annotations

import argparse
import functools
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import schedule as sched

PATH = "/v2/stream/recentchange"


class ReplayState:
    def __init__(self, plan: sched.Schedule, speed: float, keepalive: float = 5.0):
        self.plan = plan
        self.speed = speed
        self.keepalive = keepalive
        self._fired: set[int] = set()
        self._lock = threading.Lock()
        self.connections = 0
        self.served = -1  # the highest position sent on any connection

    def should_close_after(self, pos: int) -> bool:
        """True once per scheduled disconnect position (F1), for the server's lifetime."""
        if pos not in self.plan.disconnects:
            return False
        with self._lock:
            if pos in self._fired:
                return False
            self._fired.add(pos)
            return True


def make_handler(state: ReplayState):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):  # quiet; the server logs connections itself
            pass

        def do_GET(self):  # noqa: N802 - http.server API
            if self.path.split("?")[0] != PATH:
                self.send_error(404)
                return
            state.connections += 1
            start = state.plan.resume_position(self.headers.get("Last-Event-ID"))
            print(f"replay: connection {state.connections} from position {start}", file=sys.stderr, flush=True)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                self._stream(start)
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                pass
            self.close_connection = True

        def _write(self, text: str) -> None:
            self.wfile.write(text.encode("utf-8"))
            self.wfile.flush()

        def _stream(self, start: int) -> None:
            plan, positions = state.plan, state.plan.positions
            self._write(":ok\n\n")
            t0 = time.monotonic()
            v0 = positions[start].vrecv if start < len(positions) else 0.0
            for pos in range(start, len(positions)):
                d = positions[pos]
                delay = (d.vrecv - v0) / state.speed - (time.monotonic() - t0)
                if delay > 0:
                    time.sleep(delay)
                data = "".join(f"data: {line}\n" for line in d.data.split("\n"))
                self._write(f"event: message\nid: {plan.sse_id(pos)}\n{data}\n")
                state.served = max(state.served, pos)
                if state.should_close_after(pos):
                    print(f"replay: closing after position {pos} (scheduled)", file=sys.stderr, flush=True)
                    return
            while True:
                time.sleep(state.keepalive)
                self._write(":\n\n")

    return Handler


@functools.lru_cache(maxsize=4)
def _plan(capture: Path, seed: int) -> sched.Schedule:
    # A schedule is read-only once built; per-server state lives in ReplayState.
    return sched.build(sched.load_capture(capture), seed)


def serve(capture: Path, seed: int, port: int, speed: float, host: str = "127.0.0.1",
          keepalive: float = 5.0) -> ThreadingHTTPServer:
    """Build the schedule and return a server bound to (host, port); call serve_forever() on it.
    `server.state` is its ReplayState (connections made, highest position served)."""
    plan = _plan(capture, seed)
    state = ReplayState(plan, speed, keepalive)
    server = ThreadingHTTPServer((host, port), make_handler(state))
    server.daemon_threads = True
    server.state = state
    return server


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Replay the frozen recentchange capture as SSE.")
    ap.add_argument("--capture", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--speed", type=float, default=60.0, help="times faster than real time")
    args = ap.parse_args(argv)
    server = serve(args.capture, args.seed, args.port, args.speed, args.host)
    print(f"replay: serving {args.capture} seed {args.seed} on {args.host}:{args.port}{PATH}",
          file=sys.stderr, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
