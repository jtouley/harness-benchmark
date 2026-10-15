#!/usr/bin/env bash
# Run CONTRACT.md: setup blocks, then each check block; print one line per check. Exit 1 if any fails,
# if a setup block fails, or if no ```check block parses (a contract without checks must not pass).
# Block output goes to a temp file with stdin closed, so a setup that backgrounds a server (`cmd &`) does
# not hold the runner open. Timeouts (setup 600 s, check/teardown 300 s) are caught for every block kind.
set -u
F="${1:-CONTRACT.md}"
[ -f "$F" ] || { echo "no CONTRACT.md"; exit 1; }
python3 - "$F" <<'PY'
import re, subprocess, sys, tempfile
text = open(sys.argv[1]).read()
blocks = re.findall(r"^([^\n]*)\n```(setup|check|teardown)[^\n]*\n(.*?)^```", text, re.M | re.S)
def run(body, t):
    with tempfile.TemporaryFile("w+") as out:
        try:
            rc = subprocess.run(["bash", "-c", body], stdout=out, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, timeout=t).returncode
        except subprocess.TimeoutExpired:
            rc = "timeout"
        out.seek(0)
        return rc, out.read()
checks = [(label, body) for label, kind, body in blocks if kind == "check"]
print(f"CHECKS {len(checks)}")
if not checks:
    print("NO CHECKS: CONTRACT.md has no ```check blocks (a ```bash or ```sh fence is not a check)"); sys.exit(1)
for _, kind, body in blocks:
    if kind == "setup":
        rc, out = run(body, 600)
        if rc != 0:
            print("SETUP FAILED:", rc, out[-400:]); sys.exit(1)
fails = 0
for label, body in checks:
    rc, out = run(body, 300); ok = rc == 0
    fails += not ok
    print(("PASS " if ok else "FAIL ") + (label.strip() or "(unlabelled check)")[:160]
          + ("" if ok else " :: " + str(rc) + " " + out[-300:].replace("\n", " ")))
for _, kind, body in blocks:
    if kind == "teardown":
        run(body, 300)
sys.exit(1 if fails else 0)
PY
