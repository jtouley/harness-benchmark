#!/usr/bin/env bash
# Run CONTRACT.md: setup blocks, then each check block; print one line per check. Exit 1 if any fails,
# if a setup block fails, or if no ```check block parses (a contract without checks must not pass).
# Block output goes to a temp file with stdin closed, so a setup that backgrounds a server (`cmd &`) does
# not hold the runner open. Timeouts (setup 600 s, check/teardown 300 s) are caught for every block kind.
# Each setup block runs in its own process group, and every group is killed when the run ends (early exits
# included), so a server from this run cannot answer the next run's checks with old code.
set -u
F="${1:-CONTRACT.md}"
[ -f "$F" ] || { echo "no CONTRACT.md"; exit 1; }
python3 - "$F" <<'PY'
import os, re, signal, subprocess, sys, tempfile, time
text = open(sys.argv[1]).read()
blocks = re.findall(r"^([^\n]*)\n```(setup|check|teardown)[^\n]*\n(.*?)^```", text, re.M | re.S)
groups = []
def run(body, t, own_group=False):
    with tempfile.TemporaryFile("w+") as out:
        p = subprocess.Popen(["bash", "-c", body], stdout=out, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, start_new_session=own_group)
        if own_group:
            groups.append(p.pid)
        try:
            rc = p.wait(timeout=t)
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(); rc = "timeout"
        out.seek(0)
        return rc, out.read()
def signal_groups(sig):
    alive = []
    for g in groups:
        try:
            os.killpg(g, sig); alive.append(g)
        except (ProcessLookupError, PermissionError):
            pass
    return alive
def kill_groups():
    deadline = time.time() + 3
    while signal_groups(signal.SIGTERM) and time.time() < deadline:
        time.sleep(0.1)
    signal_groups(signal.SIGKILL)
def main():
    checks = [(label, body) for label, kind, body in blocks if kind == "check"]
    print(f"CHECKS {len(checks)}")
    if not checks:
        print("NO CHECKS: CONTRACT.md has no ```check blocks (a ```bash or ```sh fence is not a check)"); return 1
    for _, kind, body in blocks:
        if kind == "setup":
            rc, out = run(body, 600, own_group=True)
            if rc != 0:
                print("SETUP FAILED:", rc, out[-400:]); return 1
    fails = 0
    for label, body in checks:
        rc, out = run(body, 300); ok = rc == 0
        fails += not ok
        print(("PASS " if ok else "FAIL ") + (label.strip() or "(unlabelled check)")[:160]
              + ("" if ok else " :: " + str(rc) + " " + out[-300:].replace("\n", " ")))
    for _, kind, body in blocks:
        if kind == "teardown":
            run(body, 300)
    return 1 if fails else 0
try:
    code = main()
finally:
    kill_groups()
sys.exit(code)
PY
