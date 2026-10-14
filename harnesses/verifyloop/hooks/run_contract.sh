#!/usr/bin/env bash
# Run CONTRACT.md: setup blocks, then each check block; print one line per check. Exit 1 if any fails.
set -u
F="${1:-CONTRACT.md}"
[ -f "$F" ] || { echo "no CONTRACT.md"; exit 1; }
python3 - "$F" <<'PY'
import re, subprocess, sys
text = open(sys.argv[1]).read()
blocks = re.findall(r"^([^\n]*)\n```(setup|check|teardown)[^\n]*\n(.*?)^```", text, re.M | re.S)
run = lambda body, t: subprocess.run(["bash", "-c", body], capture_output=True, text=True, timeout=t)
for _, kind, body in blocks:
    if kind == "setup":
        r = run(body, 600)
        if r.returncode:
            print("SETUP FAILED:", (r.stdout + r.stderr)[-400:]); sys.exit(1)
fails = 0
for label, kind, body in blocks:
    if kind != "check":
        continue
    try:
        r = run(body, 300); ok = r.returncode == 0; tail = (r.stdout + r.stderr)[-300:]
    except subprocess.TimeoutExpired:
        ok, tail = False, "timeout"
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label.strip()[:160] + ("" if ok else " :: " + tail.replace("\n", " ")))
for _, kind, body in blocks:
    if kind == "teardown":
        run(body, 300)
sys.exit(1 if fails else 0)
PY
