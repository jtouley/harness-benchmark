"""Summarize the 11 verify/<run>.json records against the recorded stream_ok (scores.jsonl)."""
import json
import sys
from pathlib import Path

verify = Path(sys.argv[1])
STREAM_OK = {"P1-core-4": False, "P1-core-5": False, "P1-core-6": True, "P1-full-4": False, "P1-full-6": True,
             "P2-core-4": False, "P2-core-5": False, "P2-core-6": True, "P2-full-4": False, "P2-full-5": True,
             "P2-full-6": True}  # runs/20261024-<run>/scores.jsonl on harness-benchmark main
rows, match = [], 0
print("| Run | Tree | recorded stream_ok | gate stream verdict (after build) | match | fresh clone, run first | output check |")
print("|---|---|---|---|---|---|---|")
for run, ok in STREAM_OK.items():
    d = json.loads((verify / f"{run}.json").read_text())
    fresh = [e for e in d.get("entries", []) if e.get("fresh")]
    built = [e for e in d.get("entries", []) if not e.get("fresh")]
    if not built:
        stream, why = "no verdict", f"build failed: {(d.get('failed') or {}).get('command')}"
    else:
        sp = [p for p in built[0]["problems"] if "the output " not in p]
        stream, why = ("PASS" if not sp else "FAIL"), "; ".join(sp)[:160]
    outp = [p for e in built for p in e["problems"] if "the output " in p]
    fr = "PASS" if fresh and not fresh[0]["problems"] else ("FAIL: " + "; ".join(fresh[0]["problems"])[:140] if fresh else "-")
    m = (stream == "PASS") == ok and stream != "no verdict"
    match += m
    print(f"| {run} | {str(d.get('head'))[:12]} | {ok} | {stream}{(': ' + why) if why and stream != 'PASS' else ''} | "
          f"{'yes' if m else 'NO'} | {fr} | {'; '.join(outp)[:160] or 'PASS'} |")
print(f"\nstream verdict matches stream_ok on {match} of {len(STREAM_OK)}")
