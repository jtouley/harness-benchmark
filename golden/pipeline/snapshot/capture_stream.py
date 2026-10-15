"""Record the live Wikimedia EventStreams `recentchange` stream for a fixed time.

Writes one JSON line per SSE frame, in arrival order: {"recv": <unix seconds>, "id": <raw SSE id>,
"data": <raw SSE data string>}. The raw strings are kept byte for byte, so the replay server can serve
exactly what the live service sent. A dropped connection is resumed with Last-Event-ID, as a client
should; a frame that the service re-sends after a resume is kept (dedupe happens in freeze_capture.py).

    python capture_stream.py --seconds 3600 --out raw_capture.jsonl.gz

Stdlib only. Needs the network once; the benchmark itself runs offline from the frozen capture.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
import urllib.request

URL = "https://stream.wikimedia.org/v2/stream/recentchange"
USER_AGENT = "harness-benchmark-snapshot/0.1 (https://github.com/jtouley/harness-benchmark)"


def frames(resp):
    """Yield (id, data) per SSE frame from a streaming HTTP response."""
    event_id, data = None, []
    for raw in resp:
        line = raw.decode("utf-8").rstrip("\r\n")
        if not line:
            if data:
                yield event_id, "\n".join(data)
            data = []
            continue
        if line.startswith(":"):
            continue
        field, _, value = line.partition(":")
        value = value[1:] if value.startswith(" ") else value
        if field == "id":
            event_id = value
        elif field == "data":
            data.append(value)


def capture(seconds: float, out: str) -> int:
    deadline = time.time() + seconds
    last_id: str | None = None
    count = 0
    with gzip.open(out, "wt", encoding="utf-8") as fh:
        while time.time() < deadline:
            headers = {"User-Agent": USER_AGENT, "Accept": "text/event-stream"}
            if last_id:
                headers["Last-Event-ID"] = last_id
            try:
                req = urllib.request.Request(URL, headers=headers)
                with urllib.request.urlopen(req, timeout=60) as resp:
                    for event_id, data in frames(resp):
                        fh.write(json.dumps({"recv": round(time.time(), 3), "id": event_id, "data": data},
                                            ensure_ascii=False) + "\n")
                        last_id = event_id or last_id
                        count += 1
                        if time.time() >= deadline:
                            break
            except Exception as exc:  # noqa: BLE001 - any drop: log and resume
                print(f"capture: reconnect after {type(exc).__name__}", file=sys.stderr)
                time.sleep(2)
    return count


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seconds", type=float, default=3600)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    n = capture(args.seconds, args.out)
    print(f"capture: {n} frames -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
