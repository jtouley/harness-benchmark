"""The one driver for every run (benchmark, live, stub): check the plugin tree, run the command, record.

    python -m loop.driver --run-id 20261022-P1-cadence-haiku-1 --kind benchmark --batch 2026-10-22-p1p2 \\
        --task P1 --request-id gh-1 --arm cadence --model claude-haiku-5-5 --plugin-dir ../cadence \\
        --transcript OUT/transcript.jsonl [--grade OUT/grade.json] [--stop-point-file OUT/stop_point.json] \\
        -- runner/run_trial.sh ...

Before the command runs it refuses (exit 2) a run id that exists, and a plugin directory that is not
the top of a git work tree whose HEAD is on a remote branch, with nothing modified, untracked or
ignored: the plugin must be a published cadence commit, never a hand-patched tree. After the command it
writes runs/<run_id>/record.json (the cadence SHA, the models the transcript says served the session,
the request id, the command, start and end time, cost), stores the transcript and the delivered tree in
the blob store, and, with --grade, appends the harness-benchmark grader's score with the grader's commit
and the git tree of golden/pipeline/pipetask. The grader must be a clean checkout for that.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from loop import record, store

ROOT = Path(__file__).resolve().parents[1]
GRADER_PATH = "golden/pipeline/pipetask"


class DriverError(Exception):
    pass


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if proc.returncode != 0:
        raise DriverError(f"git {' '.join(args)} in {repo}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def plugin_commit(plugin: Path) -> dict:
    """The published commit `plugin` is exactly at, or DriverError."""
    plugin = plugin.resolve()
    top = Path(_git(plugin, "rev-parse", "--show-toplevel")).resolve()
    if top != plugin:
        raise DriverError(f"{plugin} is not the top of its git work tree ({top})")
    dirty = _git(plugin, "status", "--porcelain", "--ignored", "--untracked-files=all")
    if dirty:
        raise DriverError(f"{plugin} differs from its commit (modified, untracked or ignored files):\n{dirty}")
    sha = _git(plugin, "rev-parse", "HEAD")
    remotes = [b.strip() for b in _git(plugin, "branch", "-r", "--contains", sha).splitlines()]
    remotes = [b for b in remotes if "->" not in b]
    if not remotes:
        raise DriverError(f"{sha} in {plugin} is on no remote branch: push it first, so the run names a commit "
                          "anyone can fetch")
    url = subprocess.run(["git", "remote", "get-url", remotes[0].split("/")[0]], cwd=plugin,
                         capture_output=True, text=True).stdout.strip()
    return {"repo": url, "sha": sha, "tree_clean": True, "published_in": remotes}


def _source_changes(plugin: Path) -> list[str]:
    """`git status` lines of the plugin, without Python bytecode (a run's hooks import plugin modules)."""
    lines = _git(plugin, "status", "--porcelain", "--ignored", "--untracked-files=all").splitlines()
    return [line for line in lines if "__pycache__/" not in line and not line.rstrip().endswith(".pyc")]


def plugin_unchanged(plugin: Path, sha: str) -> bool:
    """After the run: HEAD is still `sha` and no source file changed, was added or was ignored-and-added.
    Bytecode does not count; before the run, plugin_commit refuses it too."""
    try:
        return _git(plugin, "rev-parse", "HEAD") == sha and not _source_changes(plugin)
    except DriverError:
        return False


SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "site-packages", ".tox", "proc"}


def _is_cadence(folder: Path) -> bool:
    manifest = folder / ".claude-plugin" / "plugin.json"
    try:
        if manifest.is_file() and "cadence" in str(json.loads(manifest.read_text(encoding="utf-8")).get("name", "")):
            return True
    except (OSError, ValueError, AttributeError):
        pass
    return (folder / "stages.json").is_file() and (folder / "SKILL.md").is_file()


def other_checkouts(roots: list[Path], plugin: Path | None, depth: int = 5) -> list[str]:
    """Every Cadence checkout under `roots` (to `depth` levels) other than the plugin itself: a run's peers
    could read it in place of the plugin (21 Oct: /home/user/cadence-core)."""
    skip = plugin.resolve() if plugin else None
    found: set[str] = set()
    for root in roots:
        stack = [(root.resolve(), 0)] if root.is_dir() else []
        while stack:
            folder, level = stack.pop()
            if folder == skip:
                continue
            if _is_cadence(folder):
                found.add(str(folder))
                continue
            if level >= depth:
                continue
            try:
                children = [c for c in folder.iterdir() if c.is_dir() and not c.is_symlink() and c.name not in SKIP_DIRS]
            except OSError:
                continue
            stack += [(c, level + 1) for c in children]
    return sorted(found)


def grader_identity(repo: Path) -> dict:
    """The harness-benchmark commit and grader tree, refusing a grader with local changes."""
    dirty = _git(repo, "status", "--porcelain", "--untracked-files=all", "--", GRADER_PATH)
    if dirty:
        raise DriverError(f"the grader in {repo} has local changes, so no commit names it:\n{dirty}")
    commit = _git(repo, "rev-parse", "HEAD")
    return {"repo": "jtouley/harness-benchmark", "commit": commit, "tree": _git(repo, "rev-parse", f"HEAD:{GRADER_PATH}")}


def transcript_facts(lines) -> dict:
    """Models served, session, Claude Code version and cost, from a stream-json transcript."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from pipeline_trial import PRICING, cost_and_tokens

    served, session, version, result, active_ms = [], None, None, None, 0
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        session = session or event.get("session_id")
        if event.get("type") == "system" and event.get("subtype") == "init":
            version = event.get("claude_code_version") or version
        model = (event.get("message") or {}).get("model") if event.get("type") == "assistant" else None
        if model and model != "<synthetic>" and model not in served:
            served.append(model)
        if event.get("type") == "result":
            result = event
            active_ms += event.get("duration_ms") or 0
    for model in (result or {}).get("modelUsage") or {}:
        if model not in served:
            served.append(model)
    cost = {"list_usd": None, "reported_usd": None}
    if result:
        cost["reported_usd"] = result.get("total_cost_usd")
        try:
            usd, tokens = cost_and_tokens(result, json.loads(PRICING.read_text(encoding="utf-8")))
            cost.update(list_usd=str(usd.quantize(Decimal("0.000001"))), tokens=tokens)
        except KeyError:
            pass  # a model with no list price: the list cost stays unknown
    return {"models_served": sorted(served) or None, "session_id": session, "claude_version": version,
            "cost": cost, "agent_active_seconds": round(active_ms / 1000, 3) if result else None}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tree_blob(tree: Path, root: Path) -> dict:
    """A git bundle of every ref in the delivered repository, so the grader can run on it again."""
    with tempfile.TemporaryDirectory() as tmp:
        bundle = Path(tmp) / "tree.bundle"
        _git(tree, "bundle", "create", str(bundle), "--all")
        return store.put(bundle, root)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m loop.driver", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--kind", required=True, choices=["benchmark", "live", "stub"])
    ap.add_argument("--batch", required=True)
    ap.add_argument("--task")
    ap.add_argument("--request-id")
    ap.add_argument("--arm", required=True)
    ap.add_argument("--model")
    ap.add_argument("--plugin-dir", type=Path, help="the cadence checkout loaded with --plugin-dir; omit for a one-shot")
    ap.add_argument("--transcript", type=Path, required=True, help="the stream-json transcript the command writes")
    ap.add_argument("--tree", type=Path, help="the delivered git repository, kept as a bundle for regrades")
    ap.add_argument("--grade", type=Path, help="grade.json the harness-benchmark grader wrote")
    ap.add_argument("--grader-repo", type=Path, default=ROOT)
    ap.add_argument("--stop-point-file", type=Path, help='JSON {"block": "E4", "reason": "..."} the command wrote')
    ap.add_argument("--cwd", type=Path, default=Path.cwd(), help="where the command runs")
    ap.add_argument("--fresh-home", type=Path, help="an empty or new folder to give the command as HOME")
    ap.add_argument("--timing", type=Path, help='JSON with "agent_seconds" (the agent session) that the command wrote')
    ap.add_argument("--runs", type=Path, default=ROOT / "runs")
    ap.add_argument("--store", type=Path, required=True, help="a checkout of the runs-store branch")
    ap.add_argument("command", nargs=argparse.REMAINDER)
    args = ap.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        ap.error("give the command after --")

    try:
        if not record.RUN_ID.fullmatch(args.run_id):
            raise DriverError(f"run id {args.run_id!r} is not YYYYMMDD-words (e.g. 20261022-P1-cadence-haiku-1)")
        if (args.runs / args.run_id).exists():
            raise DriverError(f"{args.runs / args.run_id} exists; run ids are never reused")
        cadence = plugin_commit(args.plugin_dir) if args.plugin_dir else None
        grader = grader_identity(args.grader_repo) if args.grade else None
        home = args.fresh_home or Path(os.environ.get("HOME", "/"))
        if args.fresh_home:
            if args.fresh_home.exists() and any(args.fresh_home.iterdir()):
                raise DriverError(f"--fresh-home {args.fresh_home} is not empty")
            args.fresh_home.mkdir(parents=True, exist_ok=True)
        others = other_checkouts([args.cwd, home], args.plugin_dir)
        if others:
            raise DriverError(f"the run could read another Cadence checkout: {', '.join(others)}; move it, or run "
                              "with --fresh-home and a --cwd that holds only the task")
    except DriverError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **({"HOME": str(home)} if args.fresh_home else {})}
    started, t0 = _now(), time.monotonic()
    exit_code = subprocess.run(command, cwd=args.cwd, env=env).returncode
    ended, run_wall = _now(), round(time.monotonic() - t0, 3)
    if cadence and not plugin_unchanged(args.plugin_dir, cadence["sha"]):
        cadence["tree_clean"] = False  # the run changed its own plugin tree

    facts = transcript_facts(args.transcript.read_text(encoding="utf-8", errors="replace").splitlines()) \
        if args.transcript.exists() else {"models_served": None, "session_id": None, "claude_version": None,
                                          "cost": {"list_usd": None, "reported_usd": None}}
    stop = {"block": None, "reason": None}
    if args.stop_point_file and args.stop_point_file.exists():
        stop.update(json.loads(args.stop_point_file.read_text(encoding="utf-8")))
    active = facts.pop("agent_active_seconds", None)
    agent_wall = None
    if args.timing and args.timing.exists():
        agent_wall = json.loads(args.timing.read_text(encoding="utf-8")).get("agent_seconds")
    counts = {"counts": True, "why": "driver run" + (" on a clean published plugin tree" if cadence else "")}
    if cadence and not cadence["tree_clean"]:
        counts = {"counts": False, "why": "the plugin tree changed during the run"}
    rec = {
        "schema": 1, "run_id": args.run_id, "kind": args.kind, "batch": args.batch,
        "provenance": {"source": "driver", "evidence": []}, "task": args.task, "request_id": args.request_id,
        "arm": args.arm, "cadence": cadence, "model_requested": args.model, **facts, "command": command,
        "started_at": started, "ended_at": ended, "exit_code": exit_code, "stop_point": stop,
        "transcript": store.put(args.transcript, args.store) if args.transcript.exists()
        else store.missing("the command wrote no transcript"),
        "tree": _tree_blob(args.tree, args.store) if args.tree else store.missing("--tree not given"),
        "counts": counts,
        "timing": {"agent_wall_seconds": agent_wall, "run_wall_seconds": run_wall, "agent_active_seconds": active,
                   "blocks": None},
        "isolation": {"cwd": str(args.cwd.resolve()), "home": str(home), "fresh_home": bool(args.fresh_home),
                      "other_cadence_checkouts": others},
    }
    record.write_record(args.runs, rec)
    if grader:
        grade = json.loads(args.grade.read_text(encoding="utf-8")) if args.grade.exists() else \
            {"reward": 0.0, "error": "the grader wrote no grade.json"}
        record.append_score(args.runs, {
            "run_id": args.run_id, "grader": grader, "reward": grade.get("reward", 0.0),
            "passed": grade.get("passed"), "total": grade.get("total"), "idempotent": grade.get("idempotent"),
            "stream_ok": grade.get("stream_ok"), "error": grade.get("error"), "source": "driver",
            "graded_at": ended})
    print(args.runs / args.run_id / "record.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
