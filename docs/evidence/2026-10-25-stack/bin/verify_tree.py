"""Enforcement-gate verification on one stored shapes-r2 tree, with the stack's own clean_checkout.clean_build.

usage: python3 -I verify_tree.py <cadence checkout> <tree worktree> <duration> <out.json>

The dev replay (seed 0, localhost:8099) must already run. The plan entry is the spec's stream command:
`make stream DURATION=<duration>`, input `sse http://localhost:8099/v2/stream/recentchange`, output `out/marts`.
The build step is the spec's `make build` only (the trees' `make test`/`make check` are not part of stream_ok).
Each entry runs first in a fresh clone (no build), then after `make build` in another clone.
"""
import json
import os
import sys
import time
from pathlib import Path

cadence, tree, duration, out = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), Path(sys.argv[4])
sys.path[:0] = [str(cadence / "scripts"), str(cadence / "shared" / "scripts")]
for key, value in {"UV_OFFLINE": "1", "DBT_SEND_ANONYMOUS_USAGE_STATS": "false", "DO_NOT_TRACK": "1",
                   "RUNTIME__DLTHUB_TELEMETRY": "false"}.items():
    os.environ[key] = value  # no network beyond localhost: the uv cache, no telemetry

import clean_checkout  # noqa: E402
import entry_points  # noqa: E402

entry = entry_points.Entry(f"make stream DURATION={duration}", "sse http://localhost:8099/v2/stream/recentchange",
                           ("out/marts",), duration + 300)
clean_checkout._plan_entries = lambda *_a, **_k: ([entry], [])
clean_checkout.entry_points = lambda _tree: ["make build"]
start = time.time()
result = clean_checkout.clean_build(tree, context_dir=tree / ".context")
result["wall_seconds"] = round(time.time() - start, 1)
out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
print(tree.name, "ok" if result["ok"] else "FAIL", result["wall_seconds"])
