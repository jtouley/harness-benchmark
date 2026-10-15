"""A minimal Server-Sent Events client that resumes with Last-Event-ID.

It reads line by line from the socket (stdlib http.client), so a quiet stream still returns each
keep-alive at once and the caller can stop on time.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass

USER_AGENT = "open-data-pipeline/0.1 (stream consumer)"


@dataclass(frozen=True)
class Message:
    id: str | None
    data: str


def parse(lines: Iterator[str]) -> Iterator[Message | None]:
    """SSE frames from text lines. Yields None for comments and keep-alives, so callers can check time."""
    event_id, data = None, []
    for line in lines:
        if line == "":
            if data:
                yield Message(event_id, "\n".join(data))
            data = []
            continue
        if line.startswith(":"):
            yield None
            continue
        field, _, value = line.partition(":")
        value = value[1:] if value.startswith(" ") else value
        if field == "id":
            event_id = value
        elif field == "data":
            data.append(value)


def stream(url: str, last_event_id: str | None, deadline: float, retry_seconds: float = 1.0,
           read_timeout: float = 15.0) -> Iterator[Message | None]:
    """Messages until the deadline, reconnecting with the last yielded id whenever the connection drops."""
    while time.monotonic() < deadline:
        headers = {"Accept": "text/event-stream", "User-Agent": USER_AGENT}
        if last_event_id:
            headers["Last-Event-ID"] = last_event_id
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=read_timeout) as resp:
                lines = (raw.decode("utf-8").rstrip("\r\n") for raw in resp)
                for msg in parse(lines):
                    if msg is not None and msg.id:
                        last_event_id = msg.id
                    yield msg
                    if time.monotonic() >= deadline:
                        return
        except (OSError, urllib.error.URLError, UnicodeDecodeError):
            pass
        yield None
        time.sleep(retry_seconds)
