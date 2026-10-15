"""Sinks: the Parquet lake under lake/<table>/, and the commit of a stream's position.

- `replace` (batch): the new table is written beside the old one, then swapped in by renames, so a
  re-run leaves the same files and a crash never leaves half a table.
- `append` (stream): one file per micro-batch, `<batch>.parquet`, numbered by the commit sequence;
  each row gets the batch number in `_batch`.

Exactly once for a stream: a micro-batch commits in one step (`StreamCommit.commit`): its files are
written, then the checkpoint (the batch number and the source's position) replaces the old one by an
atomic rename. A file whose batch number is above the checkpoint belongs to a batch that never
committed; `StreamCommit.recover` deletes such files before the stream resumes, so the events in them
are read again from the saved position, once.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

BATCH_COLUMN = "_batch"  # load metadata on every streamed row: the micro-batch that landed it


def _write(table: pa.Table, path: Path) -> None:
    tmp = path.with_name(path.name + ".tmp")
    pq.write_table(table, tmp, compression="zstd")
    os.replace(tmp, path)


def replace_table(lake: Path, table: str, data: pa.Table) -> Path:
    final, staged, old = lake / table, lake / f".{table}.new", lake / f".{table}.old"
    for path in (staged, old):
        shutil.rmtree(path, ignore_errors=True)
    staged.mkdir(parents=True)
    _write(data, staged / "part-0.parquet")
    if final.exists():
        final.rename(old)
    staged.rename(final)
    shutil.rmtree(old, ignore_errors=True)
    return final


class StreamCommit:
    """The checkpoint of one stream pipeline: lake/_checkpoints/<pipeline>.json."""

    def __init__(self, lake: Path, pipeline: str, tables: list[str]):
        self.lake, self.tables = lake, tables
        self.path = lake / "_checkpoints" / f"{pipeline}.json"

    def load(self) -> tuple[int, dict]:
        """(the last committed batch number, the source position after it)."""
        if not self.path.exists():
            return 0, {}
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        return saved["batch"], saved["position"]

    def recover(self) -> list[Path]:
        """Delete the files of batches that never committed."""
        committed, _ = self.load()
        removed = []
        for table in self.tables:
            folder = self.lake / table
            for file in sorted(folder.glob("*.parquet*")) if folder.is_dir() else []:
                number = file.name.split(".", 1)[0]
                if not number.isdigit() or int(number) > committed or file.name.endswith(".tmp"):
                    file.unlink()
                    removed.append(file)
        return removed

    def commit(self, batch: int, data: dict[str, pa.Table], position: dict) -> None:
        for table, rows in data.items():
            if len(rows):
                (self.lake / table).mkdir(parents=True, exist_ok=True)
                rows = rows.append_column(BATCH_COLUMN, pa.array([batch] * len(rows), pa.int64()))
                _write(rows, self.lake / table / f"{batch:010d}.parquet")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"batch": batch, "position": position}, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.path)  # the commit point
