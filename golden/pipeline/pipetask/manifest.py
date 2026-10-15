"""The checksum manifest of the frozen inputs (data/MANIFEST.json).

    python -m pipetask.manifest          # write it
    python -m pipetask.manifest --check  # exit 1 when a file differs from it

Each entry: the path under data/, its sha256 and size, and where it came from. The answer key records
the manifest's own sha256, so a key always names the exact inputs it was computed from.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"
MANIFEST = DATA / "MANIFEST.json"
RETRIEVED = "2026-10-14"
CAPTURE_SOURCE = ("https://stream.wikimedia.org/v2/stream/recentchange (one hour recorded live with "
                  "snapshot/capture_stream.py, reduced with snapshot/freeze_capture.py)")


def _sources() -> dict[str, str]:
    sys.path.insert(0, str(HERE / "snapshot"))
    from fetch_inputs import sources  # noqa: PLC0415 - a script, not a package

    return {f"raw/{rel}": url for rel, url in sources().items()}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build() -> dict:
    urls = _sources()
    files = []
    for path in sorted(p for p in DATA.rglob("*") if p.is_file() and p != MANIFEST):
        rel = path.relative_to(DATA).as_posix()
        source = urls.get(rel) or (CAPTURE_SOURCE if rel.startswith("capture/") else "written for this task")
        files.append({"path": rel, "sha256": sha256(path), "bytes": path.stat().st_size, "source": source})
    return {"retrieved": RETRIEVED, "files": files}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Write or check data/MANIFEST.json.")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    current = build()
    if args.check:
        saved = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if saved != current:
            sys.exit("data/ differs from data/MANIFEST.json")
        print("data/ matches data/MANIFEST.json")
        return
    MANIFEST.write_text(json.dumps(current, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
