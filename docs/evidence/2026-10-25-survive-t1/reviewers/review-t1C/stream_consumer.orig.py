"""Stream consumer: reads the recentchange SSE stream and lands micro-batches in the lake.

Each received event goes to lake/stream_raw/ (before any filter). Edits (type edit or new) also go to
lake/stream_events/. lake/stream_checkpoint/ keeps the SSE id of the last landed event. A reconnect sends that id as
Last-Event-ID. An event whose meta.id is already in lake/stream_raw/ is skipped (A-2).
"""

import http.client
import json
import os
import pathlib
import sys
import time
import urllib.parse

import dlt
import pyarrow.dataset as ds

from pipeline.lateness import is_late, window_start

EDIT_TYPES = {"edit", "new"}
BATCH_EVENTS = 2000
BATCH_SECONDS = 5.0
RECONNECT_SECONDS = 1.0
SOCKET_TIMEOUT = 5.0
ROOT = pathlib.Path(__file__).resolve().parents[1]

RAW_COLUMNS = {
    "event_id": {"data_type": "text"},
    "sse_id": {"data_type": "text"},
    "type": {"data_type": "text"},
    "namespace": {"data_type": "bigint"},
    "wiki": {"data_type": "text"},
    "server_name": {"data_type": "text"},
    "timestamp": {"data_type": "bigint"},
    "bot": {"data_type": "bool"},
    "length_old": {"data_type": "bigint"},
    "length_new": {"data_type": "bigint"},
}
EVENT_COLUMNS = {
    **RAW_COLUMNS,
    "actor_type": {"data_type": "text"},
    "net_bytes": {"data_type": "bigint"},
    "window_start": {"data_type": "bigint"},
    "is_late": {"data_type": "bool"},
}


def read_stream_url(env=None, example_path=None):
    """STREAM_URL from the environment, else the default in .env.example."""
    value = (env if env is not None else os.environ).get("STREAM_URL")
    if value:
        return value
    path = pathlib.Path(example_path) if example_path else ROOT / ".env.example"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("STREAM_URL="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError(f"STREAM_URL is not set and {path} has no default")


def iter_sse(lines):
    """Yield (id, data) for each SSE event. A blank line ends an event."""
    sse_id = None
    data: list[str] = []
    for raw in lines:
        line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        line = line.rstrip("\r\n")
        if line == "":
            if data:
                yield sse_id, "\n".join(data)
            data = []
        elif line.startswith("id:"):
            sse_id = line[3:].lstrip(" ")
        elif line.startswith("data:"):
            data.append(line[5:].lstrip(" "))


def flatten(event, sse_id):
    """One received event as a flat row. Missing length counts as 0 bytes (A-7)."""
    length = event.get("length") or {}
    old = length.get("old")
    new = length.get("new")
    return {
        "event_id": event["meta"]["id"],
        "sse_id": sse_id,
        "type": event.get("type"),
        "namespace": event.get("namespace"),
        "wiki": event.get("wiki"),
        "server_name": event.get("server_name"),
        "timestamp": event.get("timestamp"),
        "bot": bool(event.get("bot")),
        "length_old": old,
        "length_new": new,
        "actor_type": "bot" if event.get("bot") is True else "human",
        "net_bytes": (new or 0) - (old or 0),
    }


def read_table(folder, columns=None):
    """The rows of the Parquet files in folder as a table, or None when the folder has no file yet."""
    if not folder.exists() or not list(folder.glob("*.parquet")):
        return None
    return ds.dataset(folder, format="parquet").to_table(columns=columns)


def read_column(folder, column):
    table = read_table(folder, columns=[column])
    return [] if table is None else table.column(column).to_pylist()


class StreamConsumer:
    def __init__(
        self,
        lake_dir,
        url,
        duration,
        batch_events=BATCH_EVENTS,
        batch_seconds=BATCH_SECONDS,
        reconnect_seconds=RECONNECT_SECONDS,
        socket_timeout=SOCKET_TIMEOUT,
        clock=time.monotonic,
    ):
        self.lake = pathlib.Path(lake_dir).resolve()
        self.url = url
        self.duration = duration
        self.batch_events = batch_events
        self.batch_seconds = batch_seconds
        self.reconnect_seconds = reconnect_seconds
        self.socket_timeout = socket_timeout
        self.clock = clock
        self.seen = set(read_column(self.lake / "stream_raw", "event_id"))
        checkpoint = read_column(self.lake / "stream_checkpoint", "last_event_id")
        self.last_landed_id = checkpoint[-1] if checkpoint else None
        high_water = read_column(self.lake / "stream_checkpoint", "high_water")
        self.high_water = high_water[-1] if high_water else None
        self._pending_raw = []
        self._pending_events = []
        self._pending_last_id = None
        self._batch_started = clock()
        self._pipeline = dlt.pipeline(
            pipeline_name="stream_consumer",
            destination=dlt.destinations.filesystem(bucket_url=self.lake.parent.as_uri()),
            dataset_name=self.lake.name,
            pipelines_dir=str(self.lake.parent / "out" / "dlt-stream"),
        )

    def run(self):
        deadline = self.clock() + self.duration
        while self.clock() < deadline:
            self._read_until(deadline)
            self._flush()
            if self.clock() < deadline:
                time.sleep(self.reconnect_seconds)
        self._flush()

    def _read_until(self, deadline):
        try:
            conn, resp = self._connect()
        except OSError:
            return
        try:
            for sse_id, data in iter_sse(_lines(resp, self.clock, deadline)):
                try:
                    event = json.loads(data)
                except ValueError:
                    _skip("data is not JSON", sse_id)
                    continue
                self._accept(event, sse_id)
                if self._batch_full():
                    self._flush()
        except (OSError, http.client.HTTPException):
            pass
        finally:
            conn.close()

    def _connect(self):
        parts = urllib.parse.urlsplit(self.url)
        conn_class = http.client.HTTPSConnection if parts.scheme == "https" else http.client.HTTPConnection
        conn = conn_class(parts.hostname, parts.port, timeout=self.socket_timeout)
        path = parts.path + (f"?{parts.query}" if parts.query else "")
        headers = {"Accept": "text/event-stream"}
        if self.last_landed_id is not None:
            headers["Last-Event-ID"] = self.last_landed_id
        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        if resp.status != 200:
            conn.close()
            raise OSError(f"stream answered HTTP {resp.status}")
        return conn, resp

    def _accept(self, event, sse_id):
        problem = _field_problem(event)
        if problem:
            _skip(problem, sse_id)
            return
        event_id = (event.get("meta") or {}).get("id")
        if event_id is None:
            _skip("event has no meta.id", sse_id)
            return
        if event_id in self.seen:
            return
        self.seen.add(event_id)
        row = flatten(event, sse_id)
        event_time = row["timestamp"]
        self._pending_raw.append(row)
        if row["type"] in EDIT_TYPES:
            late = event_time is not None and is_late(event_time, self.high_water)
            window = None if event_time is None else window_start(event_time)
            self._pending_events.append({**row, "window_start": window, "is_late": late})
        if event_time is not None:
            self.high_water = event_time if self.high_water is None else max(self.high_water, event_time)
        self._pending_last_id = sse_id

    def _batch_full(self):
        if len(self._pending_raw) >= self.batch_events:
            return True
        return self.clock() - self._batch_started >= self.batch_seconds and bool(self._pending_raw)

    def _flush(self):
        if not self._pending_raw:
            self._batch_started = self.clock()
            return
        resources = [
            dlt.resource(self._pending_raw, name="stream_raw", write_disposition="append", columns=RAW_COLUMNS),
            dlt.resource(
                [{"last_event_id": self._pending_last_id, "high_water": self.high_water}],
                name="stream_checkpoint",
                write_disposition="replace",
                columns={"last_event_id": {"data_type": "text"}, "high_water": {"data_type": "bigint"}},
            ),
        ]
        if self._pending_events:
            resources.append(
                dlt.resource(
                    self._pending_events,
                    name="stream_events",
                    write_disposition="append",
                    columns=EVENT_COLUMNS,
                )
            )
        self._pipeline.run(resources, loader_file_format="parquet")
        self.last_landed_id = self._pending_last_id
        self._pending_raw = []
        self._pending_events = []
        self._pending_last_id = None
        self._batch_started = self.clock()


def _is_int_or_none(value):
    return value is None or (isinstance(value, int) and not isinstance(value, bool))


def _field_problem(event):
    """The reason an event cannot be flattened, or None. Length and timestamp must be integers or null."""
    if not isinstance(event, dict):
        return "event is not an object"
    meta = event.get("meta")
    if meta is not None and not isinstance(meta, dict):
        return "meta is not an object"
    length = event.get("length")
    if length is not None and not isinstance(length, dict):
        return "length is not an object"
    if not _is_int_or_none(event.get("timestamp")):
        return "timestamp is not an integer"
    if length and not all(_is_int_or_none(length.get(key)) for key in ("old", "new")):
        return "length.old or length.new is not an integer"
    return None


def _skip(reason, sse_id):
    """An event that cannot be landed is logged and skipped, so one bad event does not stop the stream."""
    print(f"stream consumer skipped an event ({reason}), sse id {sse_id!r}", file=sys.stderr)


def _lines(resp, clock, deadline):
    """Lines of the stream until EOF or the deadline. Checked per line, so heartbeats cannot hold the run past DURATION."""
    while clock() < deadline:
        line = resp.readline()
        if not line:
            return
        yield line


def main(argv):
    duration = float(argv[argv.index("--duration") + 1]) if "--duration" in argv else 60.0
    consumer = StreamConsumer(
        lake_dir=ROOT / "lake", url=read_stream_url(), duration=duration
    )
    consumer.run()


if __name__ == "__main__":
    main(sys.argv[1:])
