"""Sources: each turns one `sources:` entry into Arrow tables.

- `file` reads every file its globs match, all at once (batch). CSV columns are always read as text,
  so codes keep their leading zeros and amounts their exact digits; a transform types them.
- `sse` reads a Server-Sent Events stream in micro-batches and resumes from a saved position.

A new kind of source is one function here and one entry in SOURCES (and in the schema).
"""

from __future__ import annotations

import csv
import io
import json
import time
import zipfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pacsv

from . import sse


# ------------------------------------------------------------------------------------- file source


def _csv_as_text(data: bytes, encoding: str) -> pa.Table:
    header = data.split(b"\n", 1)[0].decode(encoding).lstrip("﻿")
    names = next(csv.reader(io.StringIO(header)), [])
    return pacsv.read_csv(
        io.BytesIO(data),
        read_options=pacsv.ReadOptions(encoding=encoding),
        parse_options=pacsv.ParseOptions(newlines_in_values=True),  # quoted text may span lines
        convert_options=pacsv.ConvertOptions(column_types={n: pa.string() for n in names},
                                             strings_can_be_null=True),
    )


def _records(data: bytes, encoding: str, records: str | None) -> pa.Table:
    value = json.loads(data.decode(encoding))
    for part in (records.split(".") if records else []):
        value = value[part]
    if isinstance(value, dict):
        return pa.table({"key": [str(k) for k in value],
                         "value": [json.dumps(v, ensure_ascii=False, sort_keys=True) for v in value.values()]})
    if isinstance(value, list):
        return pa.table({"value": [json.dumps(v, ensure_ascii=False, sort_keys=True) for v in value]})
    raise ValueError(f"records path {records!r} is neither an object nor a list")


def _files(root: Path, patterns: list[str]) -> Iterator[tuple[str, bytes]]:
    """(name, bytes) of each matched file, a zip's members one by one, in a stable order."""
    paths = sorted({p for pattern in patterns for p in root.glob(pattern) if p.is_file()})
    if not paths:
        raise FileNotFoundError(f"no file matches {patterns}")
    for path in paths:
        rel = path.relative_to(root).as_posix()
        if path.suffix == ".zip":
            with zipfile.ZipFile(path) as zf:
                for member in sorted(m for m in zf.namelist() if not m.endswith("/")):
                    yield f"{rel}/{member}", zf.read(member)
        else:
            yield rel, path.read_bytes()


def read_file(spec: dict, root: Path) -> dict[str, pa.Table]:
    encoding = spec.get("encoding", "utf8")
    parts = []
    for name, data in _files(root, spec["paths"]):
        table = _csv_as_text(data, encoding) if spec["format"] == "csv" else _records(data, encoding, spec.get("records"))
        if spec.get("source_file_column"):
            table = table.append_column(spec["source_file_column"], pa.array([name] * len(table), pa.string()))
        parts.append(table)
    return {spec["name"]: pa.concat_tables(parts, promote_options="permissive")}


# -------------------------------------------------------------------------------------- SSE source

FRAMES = pa.schema([("event", pa.string()), ("sse_id", pa.string()), ("arrival_seq", pa.int64()),
                    ("received_at", pa.timestamp("us", tz="UTC"))])
REJECTS = pa.schema([("raw", pa.string()), ("sse_id", pa.string()), ("arrival_seq", pa.int64()),
                     ("received_at", pa.timestamp("us", tz="UTC"))])


@dataclass
class SsePosition:
    """Where a consumer stands: the last SSE id received and the arrival number of the next frame."""
    last_event_id: str | None = None
    next_seq: int = 0


@dataclass
class _Buffer:
    frames: list[dict] = field(default_factory=list)
    rejects: list[dict] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.frames) + len(self.rejects)


def read_sse(spec: dict, position: dict, deadline: float, max_rows: int, max_seconds: float,
             stopped: Callable[[], bool]) -> Iterator[tuple[dict[str, pa.Table], dict]]:
    """Micro-batches until the deadline: ({table: rows}, the position after the batch).

    Every frame gets an arrival number, so arrival order survives restarts. A frame whose data is not
    JSON goes to the rejects table (when the spec names one) with its raw text.
    """
    pos = SsePosition(**position)
    buf, last_flush = _Buffer(), time.monotonic()

    def flush():
        tables = {spec["name"]: pa.Table.from_pylist(buf.frames, FRAMES)}
        if spec.get("rejects"):
            tables[spec["rejects"]] = pa.Table.from_pylist(buf.rejects, REJECTS)
        return tables, dict(pos.__dict__)

    for msg in sse.stream(spec["url"], pos.last_event_id, deadline):
        if stopped():
            break
        if msg is not None:
            row = {"sse_id": msg.id, "arrival_seq": pos.next_seq, "received_at": datetime.now(timezone.utc)}
            try:
                json.loads(msg.data)
                buf.frames.append({"event": msg.data, **row})
            except ValueError:
                buf.rejects.append({"raw": msg.data, **row})
            pos.next_seq += 1
            pos.last_event_id = msg.id or pos.last_event_id
        if buf and (len(buf) >= max_rows or time.monotonic() - last_flush >= max_seconds):
            yield flush()
            buf, last_flush = _Buffer(), time.monotonic()
    if buf:
        yield flush()


SOURCES: dict[str, Callable] = {"file": read_file}
STREAMS: dict[str, Callable] = {"sse": read_sse}
