"""Recompute every committed result and byte-compare it with results/."""

from __future__ import annotations

import difflib

from .grade import golden_check, records, regrade_all
from .install import install_twice_check
from .lock import ensure_fetched, load_lock, select
from .report import render
from .util import RESULTS_DIR, canonical_json


def _compare(name: str, fresh: str) -> bool:
    path = RESULTS_DIR / name
    if not path.is_file():
        print(f"FAIL {name}: missing (run the command that writes it)")
        return False
    stored = path.read_text(encoding="utf-8")
    if stored == fresh:
        print(f"ok   {name}")
        return True
    print(f"FAIL {name}: recomputed bytes differ")
    diff = difflib.unified_diff(stored.splitlines(), fresh.splitlines(), "committed", "recomputed", lineterm="", n=1)
    for i, line in enumerate(diff):
        if i >= 40:
            print("     ...")
            break
        print("     " + line)
    return False


def verify(args) -> int:
    from .__main__ import compute_footprint, provenance
    from .probes import run_all

    lock = load_lock()
    fws = select(lock, None)
    ensure_fetched(fws)
    ok = True
    if not args.skip_install_check:
        for fw in fws:
            res = install_twice_check(fw, lock)
            print(f"{'ok  ' if res['deterministic'] else 'FAIL'} install {fw.name} installs identically twice")
            ok &= res["deterministic"]
    ok &= _compare("footprint.json", canonical_json(compute_footprint(lock, fws)))
    ok &= _compare("probes.json", canonical_json({"provenance": provenance(lock), **run_all(lock, fws)}))
    ok &= _compare("golden.json", canonical_json(golden_check()))
    if records():
        ok &= _compare("runs.json", canonical_json(regrade_all()))
    ok &= _compare("REPORT.md", render(RESULTS_DIR))
    print("VERIFIED: every committed result was reproduced byte-for-byte" if ok else "NOT VERIFIED")
    return 0 if ok else 1
