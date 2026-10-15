"""Freeze the raw live capture into the replay capture the benchmark serves.

    python freeze_capture.py raw_capture.jsonl.gz ../data/capture/recentchange.jsonl.gz

- Keeps the first hour (by receive time) of frames, in arrival order.
- Keeps the events of the wikis in WIKIS, and every canary event. The full stream is about 90,000
  events an hour (Wikidata and Commons are half of it); this subset keeps the committed capture near
  5 MB. The kept frames are byte for byte as the live service sent them.
- Drops a frame whose meta.id was already kept: the live service re-sends a few frames when the
  capture client reconnects. The replay server adds its own re-sends from a seed.
- Writes gzip with a fixed mtime, so the same input gives the same bytes.

Stdlib only.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
from pathlib import Path

SECONDS = 3600
WIKIS = ("enwiki", "frwiki", "eswiki", "dewiki", "itwiki", "jawiki", "ptwiki", "simplewiki", "enwiktionary")


def _lines(fh):
    """Lines of a gzip text file; a capture that was cut off ends at its last complete member."""
    try:
        yield from fh
    except EOFError:
        return


def freeze(src: Path, dest: Path, wikis=WIKIS, seconds: float = SECONDS) -> dict:
    kept, seen, t0 = [], set(), None
    with gzip.open(src, "rt", encoding="utf-8") as fh:
        for line in _lines(fh):
            try:
                frame = json.loads(line)
            except ValueError:
                break  # a capture cut mid-line ends there
            t0 = frame["recv"] if t0 is None else t0
            if frame["recv"] - t0 > seconds:
                break
            event = json.loads(frame["data"])
            meta = event.get("meta") or {}
            if meta.get("domain") != "canary" and event.get("wiki") not in wikis:
                continue
            if meta.get("id") in seen:
                continue
            seen.add(meta.get("id"))
            kept.append({"id": frame["id"], "data": frame["data"], "recv": frame["recv"]})
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0, filename="") as gz:
        for frame in kept:
            gz.write((json.dumps(frame, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(buf.getvalue())
    return {"frames": len(kept), "seconds": round(kept[-1]["recv"] - kept[0]["recv"], 1) if kept else 0}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", type=Path)
    ap.add_argument("dest", type=Path)
    args = ap.parse_args()
    print(freeze(args.src, args.dest))


if __name__ == "__main__":
    main()
