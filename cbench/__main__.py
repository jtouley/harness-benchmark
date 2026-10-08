"""cbench: deterministic, replayable benchmark of agent harnesses.

  python -m cbench fetch [FW...]          clone pinned SHAs and build
  python -m cbench install-check [FW...]  install twice, compare normalized tree hashes
  python -m cbench footprint [FW...]      tier 1: context tokens and cost  -> results/footprint.json
  python -m cbench probes [FW...]         tier 2: golden hook probes        -> results/probes.json
  python -m cbench golden-check           golden tasks: hidden tests fail before, pass with reference
  python -m cbench harbor-build [--check] tier 3: generate Harbor tasks from the lockfile and golden tasks
  python -m cbench harbor-collect DIR     tier 3: Harbor job results -> results/live.json
  python -m cbench report                 results/*.json -> results/REPORT.md
  python -m cbench verify                 recompute everything and byte-compare with results/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

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


def cmd_harbor_build(args) -> int:
    from . import harbor

    if args.check:
        return harbor.check()
    paths = harbor.generate(args.arms or None, args.tasks or None, proxy_ca=Path(args.proxy_ca) if args.proxy_ca else None)
    print(f"wrote {len(paths)} Harbor task(s) under {harbor.TASKS_DIR}")
    return 0


def cmd_harbor_collect(args) -> int:
    from . import harbor

    data = harbor.collect(Path(args.jobs_dir))
    write_json(RESULTS_DIR / "live.json", data)
    print(f"collected {len(data['trials'])} trial(s) into {RESULTS_DIR / 'live.json'}")
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

    p = sub.add_parser("harbor-build")
    p.add_argument("--arms", nargs="*", default=None)
    p.add_argument("--tasks", nargs="*", default=None)
    p.add_argument("--proxy-ca", default=None, help="CA bundle to trust inside the image (sandboxes that re-terminate TLS)")
    p.add_argument("--check", action="store_true", help="fail if harbor/tasks differs from what would be generated")
    p.set_defaults(func=cmd_harbor_build)

    p = sub.add_parser("harbor-collect")
    p.add_argument("jobs_dir")
    p.set_defaults(func=cmd_harbor_collect)

    sub.add_parser("report").set_defaults(func=cmd_report)

    p = sub.add_parser("verify")
    p.add_argument("--skip-install-check", action="store_true")
    p.set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
