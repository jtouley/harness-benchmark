"""Run a checked pipeline: sources, then transforms in order, then sinks.

A pipeline with only file sources runs once (batch). A pipeline with a stream source runs once per
micro-batch until the duration ends; its other sources (files) are read once and stay available to
every micro-batch. The engine never looks at the pipeline's name or its tables: what runs is what the
YAML says.
"""

from __future__ import annotations

import signal
import time
from pathlib import Path

import pyarrow as pa

from . import sinks, sources, transforms
from .config import Pipeline


def _sink_all(pipeline: Pipeline, tables: dict[str, pa.Table]) -> dict[str, pa.Table]:
    return {sink["table"]: tables[sink["input"]] for sink in pipeline.sinks}


def run_batch(pipeline: Pipeline, root: Path) -> dict[str, int]:
    tables: dict[str, pa.Table] = {}
    for spec in pipeline.sources:
        tables.update(sources.SOURCES[spec["type"]](spec, root))
    tables = transforms.apply(pipeline.transforms, tables)
    landed = {}
    for table, data in _sink_all(pipeline, tables).items():
        sinks.replace_table(root / "lake", table, data)
        landed[table] = len(data)
    return landed


def run_stream(pipeline: Pipeline, root: Path, duration: float) -> dict[str, int]:
    stream = next(s for s in pipeline.sources if s["type"] in sources.STREAMS)
    static: dict[str, pa.Table] = {}
    for spec in pipeline.sources:
        if spec is not stream:
            static.update(sources.SOURCES[spec["type"]](spec, root))
    commit = sinks.StreamCommit(root / "lake", pipeline.name, [s["table"] for s in pipeline.sinks])
    commit.recover()
    batch, position = commit.load()

    stop = {"now": False}
    signal.signal(signal.SIGTERM, lambda *_: stop.update(now=True))
    landed = {s["table"]: 0 for s in pipeline.sinks}
    micro = pipeline.micro_batch
    batches = sources.STREAMS[stream["type"]](
        stream, position, deadline=time.monotonic() + duration, max_rows=micro.get("max_rows", 5000),
        max_seconds=micro.get("max_seconds", 5.0), stopped=lambda: stop["now"])
    try:
        for new_tables, new_position in batches:
            tables = transforms.apply(pipeline.transforms, {**static, **new_tables})
            out = _sink_all(pipeline, tables)
            batch += 1
            commit.commit(batch, out, new_position)
            for table, data in out.items():
                landed[table] += len(data)
    except KeyboardInterrupt:
        pass  # the last committed batch stands; the next run resumes after it
    return landed


def run(pipeline: Pipeline, root: Path, duration: float | None = None) -> dict[str, int]:
    if any(s["type"] in sources.STREAMS for s in pipeline.sources):
        if duration is None:
            raise SystemExit(f"{pipeline.path}: a stream pipeline needs --duration")
        return run_stream(pipeline, root, duration)
    return run_batch(pipeline, root)
