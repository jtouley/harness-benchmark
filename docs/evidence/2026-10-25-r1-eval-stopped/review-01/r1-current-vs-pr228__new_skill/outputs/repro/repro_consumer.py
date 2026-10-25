"""Adversarial probes of pipeline.stream_consumer.StreamConsumer, one fresh lake per case."""
import json
import pathlib
import sys
import tempfile
import traceback

REPO = pathlib.Path("/var/tmp/revieweval/r1-current-vs-pr228/review-01/new_skill/run-1/repo")
sys.path.insert(0, str(REPO))

from pipeline.stream_consumer import StreamConsumer, read_column  # noqa: E402


def good(i, **changes):
    event = {
        "meta": {"id": f"ev-{i}"},
        "type": "edit",
        "namespace": 0,
        "wiki": "enwiki",
        "server_name": "en.wikipedia.org",
        "timestamp": 1792021600 + i,
        "bot": False,
        "length": {"old": 1, "new": 2},
    }
    event.update(changes)
    return event


def run_case(name, events):
    tmp = tempfile.mkdtemp(prefix="probe-")
    lake = pathlib.Path(tmp) / "lake"
    consumer = StreamConsumer(lake_dir=lake, url="http://127.0.0.1:1/", duration=0.1,
                              clock=lambda: 0.0)
    outcome = "ok"
    try:
        for i, ev in enumerate(events):
            consumer._accept(ev, f"sse-{i}")
        consumer._flush()
    except Exception as exc:  # report, do not hide
        outcome = f"CRASH {type(exc).__name__}: {str(exc).splitlines()[0][:160]}"
    raw = read_column(lake / "stream_raw", "event_id") if lake.exists() else []
    events_landed = read_column(lake / "stream_events", "actor_type") if lake.exists() else []
    print(f"[{name}] {outcome}")
    print(f"    raw landed: {raw}")
    if events_landed:
        print(f"    stream_events actor_type: {events_landed}")


run_case("baseline: good events", [good(1), good(2)])
run_case("meta.id is a list (unhashable), then good events in same batch",
         [good(1), {**good(2), "meta": {"id": ["x"]}}, good(3)])
run_case("meta.id is an int", [good(1), {**good(2), "meta": {"id": 2}}, good(3)])
run_case("namespace is a string, then good events in same batch",
         [good(1), good(2, namespace="zero"), good(3)])
run_case("wiki is an int", [good(1), good(2, wiki=7), good(3)])
run_case("bot is the string 'false' (actor_type vs bot column)", [good(1, bot="false")])
run_case("bot is the int 0 (actor_type vs bot column)", [good(1, bot=0)])
run_case("bot is the string 'true'", [good(1, bot="true")])
