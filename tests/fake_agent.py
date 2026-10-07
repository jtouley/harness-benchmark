#!/usr/bin/env python3
"""Scripted stand-in for `claude` used to test the live pipeline offline.

It applies the golden reference patch for $CBENCH_TASK_ID, commits, and prints
a minimal stream-json transcript with fixed usage numbers.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

if "--version" in sys.argv:
    print("0.0.0 (cbench fake agent)")
    raise SystemExit(0)

task = os.environ["CBENCH_TASK_ID"]
patch = Path(__file__).resolve().parents[1] / "golden" / "tasks" / task / "reference.patch"
subprocess.run(["git", "apply", str(patch)], check=True)
subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "commit", "-q", "-m", f"fix {task}"], check=True)

model = sys.argv[sys.argv.index("--model") + 1]
usage = {"input_tokens": 120, "cache_creation_input_tokens": 9000, "cache_read_input_tokens": 0, "output_tokens": 300}
events = [
    {"type": "system", "subtype": "init", "model": model},
    {"type": "assistant", "message": {"id": "m1", "model": model, "usage": usage,
                                      "content": [{"type": "tool_use", "name": "Edit", "input": {}}]}},
    {"type": "assistant", "message": {"id": "m2", "model": model,
                                      "usage": {"input_tokens": 80, "cache_creation_input_tokens": 400,
                                                "cache_read_input_tokens": 9000, "output_tokens": 200},
                                      "content": [{"type": "text", "text": "done"}]}},
    {"type": "result", "subtype": "success", "is_error": False, "num_turns": 2, "total_cost_usd": 0.05,
     "modelUsage": {model: {"inputTokens": 200, "outputTokens": 500, "cacheCreationInputTokens": 9400,
                            "cacheReadInputTokens": 9000}}},
]
for event in events:
    print(json.dumps(event))
