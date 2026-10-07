"""cbench: deterministic, replayable benchmark of agent harnesses.

  python -m cbench fetch [FW...]          clone pinned SHAs and build
  python -m cbench install-check [FW...]  install twice, compare normalized tree hashes
  python -m cbench footprint [FW...]      tier 1: context tokens and cost  -> results/footprint.json
  python -m cbench probes [FW...]         tier 2: golden hook probes        -> results/probes.json
  python -m cbench golden-check           golden tasks: hidden tests fail before, pass with reference
  python -m cbench live ...               tier 3: run agents on golden tasks (needs ANTHROPIC_API_KEY)
  python -m cbench grade                  regrade every recorded run from its stored patch
  python -m cbench report                 results/*.json -> results/REPORT.md
  python -m cbench verify                 recompute everything and byte-compare with results/
"""

from __future__ import annotations

import argparse
import sys

from . import tokens
from .lock import ensure_fetched, fetch, load_lock, select
from .util import PRICING_PATH, RESULTS_DIR, canonical_json, load_json, sha256_file, write_json


def provenance(lock) -> dict:
    return {
        "lockfile_sha256": lock.sha256,
        "pricing_sha256": sha256_file(PRICING_PATH),
        "tokenizer": tokens.provenance(),
        "canonical_root": str(lock.canonical_root),
    }


def cmd_fetch(args) -> int:
    lock = load_lock()
    for fw in select(lock, args.frameworks):
        print(f"fetch {fw.name} @ {fw.sha}", flush=True)
        fetch(fw, rebuild=args.rebuild)
    return 0


def cmd_install_check(args) -> int:
    from .install import install_twice_check

    lock = load_lock()
    fws = select(lock, args.frameworks)
    ensure_fetched(fws)
    ok = True
    out = {}
    for fw in fws:
        res = install_twice_check(fw, lock)
        out[fw.name] = res
        ok &= res["deterministic"]
        print(f"{fw.name:12} files={res['first']['files']:5} deterministic={res['deterministic']}", flush=True)
    if args.write:
        write_json(RESULTS_DIR / "install.json", {"provenance": provenance(lock), "frameworks": out})
    return 0 if ok else 1


def compute_footprint(lock, fws) -> dict:
    from .footprint import measure

    pricing = load_json(PRICING_PATH)
    return {
        "provenance": provenance(lock),
        "pricing_as_of": pricing["as_of"],
        "frameworks": {fw.name: measure(fw, lock, pricing) for fw in fws},
    }


def cmd_footprint(args) -> int:
    lock = load_lock()
    fws = select(lock, args.frameworks)
    ensure_fetched(fws)
    data = compute_footprint(lock, fws)
    for name, row in data["frameworks"].items():
        print(f"{name:12} always_on={row['always_on']['total_tokens']:7} corpus={row['corpus_tokens']:8} "
              f"workflow={row['workflow']['lower_tokens']}..{row['workflow']['upper_tokens']}", flush=True)
    if not args.frameworks:
        write_json(RESULTS_DIR / "footprint.json", data)
    else:
        sys.stdout.write(canonical_json(data))
    return 0


def cmd_probes(args) -> int:
    from .probes import run_all

    lock = load_lock()
    fws = select(lock, args.frameworks)
    ensure_fetched(fws)
    data = {"provenance": provenance(lock), **run_all(lock, fws)}
    if not args.frameworks:
        write_json(RESULTS_DIR / "probes.json", data)
    else:
        sys.stdout.write(canonical_json(data))
    return 0


def cmd_golden_check(args) -> int:
    from .grade import golden_check

    data = golden_check()
    write_json(RESULTS_DIR / "golden.json", data)
    bad = [t for t, r in data["tasks"].items() if not r["valid"]]
    for t, r in data["tasks"].items():
        print(f"{t:28} valid={r['valid']} before={r['before']['passed']}/{r['before']['total']} "
              f"after={r['after']['passed']}/{r['after']['total']}")
    return 1 if bad else 0


def cmd_live(args) -> int:
    from .live import run_matrix

    return run_matrix(args)


def cmd_grade(args) -> int:
    from .grade import regrade_all

    data = regrade_all()
    write_json(RESULTS_DIR / "runs.json", data)
    print(f"graded {len(data['runs'])} recorded run(s)")
    return 0


def cmd_report(args) -> int:
    from .report import build

    path = build()
    print(path)
    return 0


def cmd_verify(args) -> int:
    from .verify import verify

    return verify(args)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cbench", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("fetch")
    p.add_argument("frameworks", nargs="*")
    p.add_argument("--rebuild", action="store_true")
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("install-check")
    p.add_argument("frameworks", nargs="*")
    p.add_argument("--write", action="store_true", help="write results/install.json")
    p.set_defaults(func=cmd_install_check)

    for name, func in (("footprint", cmd_footprint), ("probes", cmd_probes)):
        p = sub.add_parser(name, help="with no names: all frameworks, written to results/")
        p.add_argument("frameworks", nargs="*")
        p.set_defaults(func=func)

    sub.add_parser("golden-check").set_defaults(func=cmd_golden_check)

    p = sub.add_parser("live")
    p.add_argument("--frameworks", nargs="*", default=None)
    p.add_argument("--tasks", nargs="*", default=None)
    p.add_argument("--trials", type=int, default=3)
    p.add_argument("--model", default="claude-sonnet-5-5")
    p.add_argument("--max-budget-usd", type=float, default=5.0)
    p.add_argument("--timeout", type=int, default=3600, help="seconds per run")
    p.add_argument("--agent-cmd", default="claude", help="agent CLI (a scripted stand-in is used by tests)")
    p.add_argument("--yes", action="store_true", help="skip the cost confirmation")
    p.set_defaults(func=cmd_live)

    sub.add_parser("grade").set_defaults(func=cmd_grade)
    sub.add_parser("report").set_defaults(func=cmd_report)

    p = sub.add_parser("verify")
    p.add_argument("--skip-install-check", action="store_true")
    p.set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
