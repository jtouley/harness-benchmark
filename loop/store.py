"""The blob store for transcripts and delivered trees, which are too large for the main branch.

The store is the orphan branch `runs-store` of jtouley/harness-benchmark: each blob is
blobs/<sha256 of the original>.gz. A record keeps the sha256, the size and the path, so a blob can be
fetched (`git fetch origin runs-store`) and checked against the record. See runs/README.md.
"""

from __future__ import annotations

import gzip
import hashlib
import shutil
from pathlib import Path

STORE = "git:jtouley/harness-benchmark@runs-store"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def put(src: Path, root: Path) -> dict:
    """Copy `src` into the store under `root` (a checkout of the store branch), gzipped. Idempotent."""
    digest = sha256(src)
    rel = f"blobs/{digest}.gz"
    dest = root / rel
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".tmp")
        with open(src, "rb") as fin, gzip.GzipFile(tmp, "wb", mtime=0) as fout:
            shutil.copyfileobj(fin, fout)
        tmp.replace(dest)
    return {"sha256": digest, "bytes": src.stat().st_size, "store": STORE, "path": rel}


def verify(blob: dict, root: Path) -> bool:
    """The stored blob decompresses to the bytes the record names."""
    path = root / blob["path"]
    if not path.exists():
        return False
    h, n = hashlib.sha256(), 0
    with gzip.open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest() == blob["sha256"] and n == blob.get("bytes", n)


def missing(why: str) -> dict:
    return {"sha256": None, "missing": why}
