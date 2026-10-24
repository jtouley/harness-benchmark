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
and the git tree of golden/pipeline/pipetask. The grader must be a clean checkout for that. Then it
writes the batch's postmortem again (every committed postmortem that covers the batch, or a new
<batch>.md) and scoreboard.md, so the record, the postmortem and the scoreboard go in one commit
(runs/README.md, "After a merge").

Only Cadence is run (owner, 2026-10-23): the one-shot baselines are pinned (baselines.json), so the
driver refuses any arm but `cadence`, of every kind.

The entry (owner, 2026-10-22): the only prompt a Cadence run gets is `/cadence <spec path>`. A Cadence
benchmark or live run needs --spec; the driver gives the command HB_AGENT_PROMPT, exactly `/cadence <the
spec's absolute path>`, and refuses a command that passes the agent any other `-p` text. With --agent-argv (the argv the command started the agent with) a run whose agent got another
prompt does not count. What the entry does is the result: an exit 1 at activation is recorded, not worked
around. The record keeps the spec's path, sha256 and the prompt.

After the run the transcript's tool calls are scanned for the benchmark (harness-benchmark, golden/, the
answer key, the grader) and for another Cadence checkout; a run with a hit does not count, and the hits are
in isolation.contact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from loop import blocks, postmortem, record, scoreboard, store

ROOT = Path(__file__).resolve().parents[1]
GRADER_PATH = "golden/pipeline/pipetask"
# The hold-out task (golden/pipeline/README.md): it runs only when the owner calls for the final check, so the
# driver refuses it unless --holdout says this is that check.
HOLDOUT_TASKS = ("P4",)


class DriverError(Exception):
    pass


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if proc.returncode != 0:
        raise DriverError(f"git {' '.join(args)} in {repo}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def plugin_commit(plugin: Path, bytecode_ok: bool = False) -> dict:
    """The published commit `plugin` is exactly at, or DriverError. With `bytecode_ok` (--finish: the run's
    hooks already imported plugin modules), Python bytecode is not a difference."""
    plugin = plugin.resolve()
    top = Path(_git(plugin, "rev-parse", "--show-toplevel")).resolve()
    if top != plugin:
        raise DriverError(f"{plugin} is not the top of its git work tree ({top})")
    dirty = "\n".join(_source_changes(plugin)) if bytecode_ok else \
        _git(plugin, "status", "--porcelain", "--ignored", "--untracked-files=all")
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
    return {"repo": url, "sha": sha, "tree": _git(plugin, "rev-parse", f"{sha}^{{tree}}"), "tree_clean": True,
            "published_in": remotes}


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
        model = _message(event).get("model") if event.get("type") == "assistant" else None
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


CONTACT_MARKERS = ("harness-benchmark", "golden/", "answer_key", "pipetask", "grader.pyz")
_OTHER_CADENCE = re.compile(r"(?:~|/[\w.-]+)*/cadence[\w.-]*(?=/)")


def _message(event: dict) -> dict:
    """A transcript event's `message`, or {}: an event's message can be a string (run
    20261024-P2-cadence-haiku-core-1: the driver crashed on it after 88 minutes and wrote no record)."""
    message = event.get("message")
    return message if isinstance(message, dict) else {}


def contact(lines, plugin: Path | None) -> list[str]:
    """Each tool-call input of the transcript that names the benchmark or a Cadence checkout other than the
    plugin (the run's own plugin path is not a hit), as `<tool>: <marker>`."""
    hits: list[str] = []
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        content = _message(event).get("content") if isinstance(event, dict) else None
        for item in content if isinstance(content, list) else []:
            if not isinstance(item, dict) or item.get("type") != "tool_use":
                continue
            text = json.dumps(item.get("input"), ensure_ascii=False)
            if plugin is not None:
                text = text.replace(str(plugin.resolve()), "<plugin>")
            found = [m for m in (str(ROOT), *CONTACT_MARKERS) if m in text] + _OTHER_CADENCE.findall(text)
            hits += [f"{item.get('name')}: {m}" for m in found if f"{item.get('name')}: {m}" not in hits]
    return hits


def api_error(lines) -> str | None:
    """The API error a transcript's result reports (a 429 usage limit, a 529 overload), or None: such a run was
    cut off from outside the agent, an infrastructure loss and not a result."""
    found = None
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "result" and event.get("is_error") \
                and (event.get("api_error_status") or event.get("api_error")):
            found = f"{event.get('api_error_status')} {event.get('api_error') or ''}".strip()
    return found


def agent_prompt(spec: Path) -> str:
    """`/cadence <the spec's absolute path>`: a Cadence run's only prompt."""
    return f"/cadence {spec.resolve()}"


# The flags a benchmark agent's `claude` call may carry (scripts/host_trial.py): none adds prompt text.
CLAUDE_VALUE_FLAGS = frozenset({"--model", "--permission-mode", "--output-format", "--plugin-dir", "--add-dir",
                                "--max-budget-usd"})
CLAUDE_BARE_FLAGS = frozenset({"--verbose"})
_SEPARATORS = frozenset({";", "&&", "||", "|", "&", "(", ")", "\n"})


def _words(arg: str) -> list[str]:
    lexer = shlex.shlex(arg, posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return arg.split()


def claude_calls(command: list[str]) -> list[tuple[list[str], bool]]:
    """Each `claude` call in an argv, also inside a shell-script argument (`bash -c`): (its arguments, whether
    something is piped into it)."""
    streams = [list(command)] + [_words(arg) for arg in command if any(c.isspace() or c in ";|&" for c in arg)]
    calls = []
    for words in streams:
        for i, word in enumerate(words):
            if Path(word).name != "claude":
                continue
            rest = []
            for w in words[i + 1:]:
                if w in _SEPARATORS:
                    break
                rest.append(w)
            calls.append((rest, i > 0 and words[i - 1] == "|"))
    return calls


def claude_call_problem(args: list[str], prompt: str, piped: bool = False) -> str | None:
    """Why one `claude` call gives the agent more than `prompt`, or None: `-p <prompt>` once, then only flags that
    carry no prompt text. A bare -p, a positional argument, stdin and any other flag are refused."""
    if piped:
        return "something is piped into claude (stdin is prompt text)"
    seen, i = 0, 0
    while i < len(args):
        word = args[i]
        if word in ("-p", "--print"):
            if i + 1 >= len(args) or args[i + 1] != prompt:
                return f"{word} is not followed by the one prompt"
            seen, i = seen + 1, i + 2
        elif word in CLAUDE_VALUE_FLAGS and i + 1 < len(args):
            i += 2
        elif word in CLAUDE_BARE_FLAGS:
            i += 1
        else:
            return f"{word[:60]!r} is not an allowed claude argument"
    return None if seen == 1 else f"the prompt is given {seen} times"


def repo_profile(cwd: Path) -> str | None:
    """The run shape the run repo used: `profile` of <cwd>/repo/.cadence.json after the run (host_trial writes
    it from its own --shape), or None without one. The driver's --shape is a separate argument (review of #95),
    so a record states a shape only when the repo used it."""
    try:
        return json.loads((cwd / "repo" / ".cadence.json").read_text(encoding="utf-8")).get("profile")
    except (OSError, ValueError, AttributeError):
        return None


def _finished_times(args: argparse.Namespace) -> tuple[str | None, str | None, float | None, None]:
    """--finish: (start, end, wall seconds, exit code None) of a command that already ran: the start is when it
    wrote the agent argv (else the spec), the end its last output (grade, timing, stop point or transcript)."""
    def mtime(paths):
        found = [p.stat().st_mtime for p in paths if p is not None and p.exists()]
        return found
    start = mtime([args.agent_argv]) or mtime([args.spec])
    end = mtime([args.grade, args.timing, args.stop_point_file, args.transcript])
    iso = lambda s: datetime.fromtimestamp(s, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not start or not end:
        return None, None, None, None
    return iso(min(start)), iso(max(end)), round(max(end) - min(start), 3), None


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tree_blob(tree: Path, root: Path) -> dict:
    """A git bundle of every ref in the delivered repository, so the grader can run on it again."""
    with tempfile.TemporaryDirectory() as tmp:
        bundle = Path(tmp) / "tree.bundle"
        _git(tree, "bundle", "create", str(bundle), "--all")
        return store.put(bundle, root)


def _load_argv(path: Path) -> list[str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [str(v) for v in value] if isinstance(value, list) else []


def _agent_argv_problem(path: Path, prompt: str) -> str | None:
    argv = _load_argv(path)
    if not argv or Path(argv[0]).name != "claude":
        return f"{path} holds no claude argv"
    return claude_call_problem(argv[1:], prompt)


def _check_entry(args: argparse.Namespace, command: list[str]) -> str | None:
    """The agent prompt (HB_AGENT_PROMPT), or None without --spec; DriverError for a run the rule refuses."""
    if args.spec is None:
        if args.kind in ("benchmark", "live"):
            raise DriverError("a Cadence benchmark or live run needs --spec: its only prompt is /cadence <spec path>")
        return None
    if not args.spec.is_file():
        raise DriverError(f"--spec {args.spec} is not a file")
    prompt = agent_prompt(args.spec)
    for call, piped in claude_calls(command):
        problem = claude_call_problem(call, prompt, piped)
        if problem:
            raise DriverError(f"the command's claude call carries other prompt text ({problem}); the agent's only "
                              f"prompt is {prompt.splitlines()[0][:80]!r}, from HB_AGENT_PROMPT")
    if args.kind in ("benchmark", "live") and args.agent_argv is None:
        raise DriverError("a Cadence benchmark or live run needs --agent-argv: the argv the agent was started with "
                          "shows that its only prompt was the spec")
    return prompt


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m loop.driver", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--kind", required=True, choices=["benchmark", "live", "stub"])
    ap.add_argument("--batch", required=True)
    ap.add_argument("--task")
    ap.add_argument("--holdout", action="store_true",
                    help="this run is the owner's final check on the hold-out task (P4); without it P4 is refused")
    ap.add_argument("--request-id")
    ap.add_argument("--arm", required=True)
    ap.add_argument("--model")
    ap.add_argument("--plugin-dir", type=Path, help="the cadence checkout loaded with --plugin-dir")
    ap.add_argument("--transcript", type=Path, required=True, help="the stream-json transcript the command writes")
    ap.add_argument("--tree", type=Path, help="the delivered git repository, kept as a bundle for regrades")
    ap.add_argument("--grade", type=Path, help="grade.json the harness-benchmark grader wrote")
    ap.add_argument("--grader-repo", type=Path, default=ROOT)
    ap.add_argument("--stop-point-file", type=Path, help='JSON {"block": "E4", "reason": "..."} the command wrote')
    ap.add_argument("--cwd", type=Path, default=Path.cwd(), help="where the command runs")
    ap.add_argument("--fresh-home", type=Path, help="an empty or new folder to give the command as HOME")
    ap.add_argument("--context", type=Path, help="the run's .context (a copy is fine): time per block comes from it")
    ap.add_argument("--timing", type=Path, help='JSON the command wrote: "agent_seconds" (the agent session), and '
                    '"hit_cap" and "agent_cap_seconds" when it knows them (scripts/host_trial.py writes all three)')
    ap.add_argument("--runs", type=Path, default=ROOT / "runs")
    ap.add_argument("--postmortems", type=Path, help="the postmortems folder (default: beside --runs)")
    ap.add_argument("--scoreboard", type=Path, help="the scoreboard file (default: scoreboard.md beside --runs)")
    ap.add_argument("--store", type=Path, required=True, help="a checkout of the runs-store branch")
    ap.add_argument("--spec", type=Path, help="the spec, the run's only input: `/cadence <path>` (given to the "
                    "command as HB_AGENT_PROMPT)")
    ap.add_argument("--agent-argv", type=Path, help="JSON list: the argv the command started the agent with")
    ap.add_argument("--isolation-method", default="host", help="host, or container:<image id>")
    ap.add_argument("--finish", action="store_true",
                    help="the command already ran: write the record from what it left in --cwd (transcript, grade, "
                    "timing, stop point, context) without running it again, with the same checks")
    ap.add_argument("--shape", choices=["core", "full"], help="the Cadence run shape (owner, 2026-10-24), on the record")
    ap.add_argument("--auth", choices=["proxy", "oauth-file"], default="proxy",
                    help="how the agent authenticates: proxy (the host's HTTPS proxy adds the credentials; HOME gets "
                    "none) or oauth-file (the operator's ~/.claude/.credentials.json, copied into the fresh HOME)")
    ap.add_argument("command", nargs=argparse.REMAINDER)
    args = ap.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        ap.error("give the command after --")

    try:
        if not record.RUN_ID.fullmatch(args.run_id):
            raise DriverError(f"run id {args.run_id!r} is not YYYYMMDD-words (e.g. 20261022-P1-cadence-haiku-1)")
        if args.arm != "cadence":
            raise DriverError(f"arm {args.arm!r}: only Cadence is run; the one-shot baselines are pinned in "
                              f"baselines.json (docs/rules.md)")
        if (args.runs / args.run_id).exists():
            raise DriverError(f"{args.runs / args.run_id} exists; run ids are never reused")
        if args.task in HOLDOUT_TASKS and not args.holdout:
            raise DriverError(f"{args.task} is the hold-out task: it runs only when the owner calls for the final "
                              f"check (pass --holdout for that run; golden/pipeline/README.md)")
        cadence = plugin_commit(args.plugin_dir, bytecode_ok=args.finish) if args.plugin_dir else None
        grader = grader_identity(args.grader_repo) if args.grade else None
        home = args.fresh_home or Path(os.environ.get("HOME", "/"))
        if args.finish and not args.transcript.exists():
            raise DriverError(f"--finish: no transcript at {args.transcript}; the command did not run there")
        if args.fresh_home and not args.finish:
            if args.fresh_home.exists() and any(args.fresh_home.iterdir()):
                raise DriverError(f"--fresh-home {args.fresh_home} is not empty")
            args.fresh_home.mkdir(parents=True, exist_ok=True)
        others = other_checkouts([args.cwd, home], args.plugin_dir)
        if others:
            raise DriverError(f"the run could read another Cadence checkout: {', '.join(others)}; move it, or run "
                              "with --fresh-home and a --cwd that holds only the task")
        prompt = _check_entry(args, command)
        cwd_contents = sorted(c.name + ("/" if c.is_dir() else "") for c in args.cwd.iterdir()) \
            if args.cwd.is_dir() else []
    except DriverError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **({"HOME": str(home)} if args.fresh_home else {}),
           **({"HB_AGENT_PROMPT": prompt} if prompt is not None else {})}
    if args.finish:  # the command ran before; its start and end are its files' times, its exit code is lost
        started, ended, run_wall, exit_code = _finished_times(args)
    else:
        started, t0 = _now(), time.monotonic()
        exit_code = subprocess.run(command, cwd=args.cwd, env=env).returncode
        ended, run_wall = _now(), round(time.monotonic() - t0, 3)
    if cadence and not plugin_unchanged(args.plugin_dir, cadence["sha"]):
        cadence["tree_clean"] = False  # the run changed its own plugin tree

    lines = args.transcript.read_text(encoding="utf-8", errors="replace").splitlines() \
        if args.transcript.exists() else []
    hits = contact(lines, args.plugin_dir)
    lost = api_error(lines)
    facts = transcript_facts(lines) \
        if args.transcript.exists() else {"models_served": None, "session_id": None, "claude_version": None,
                                          "cost": {"list_usd": None, "reported_usd": None}}
    stop = {"block": None, "reason": None}
    if args.stop_point_file and args.stop_point_file.exists():
        stop.update(json.loads(args.stop_point_file.read_text(encoding="utf-8")))
    active = facts.pop("agent_active_seconds", None)
    agent_wall, hit_cap, cap_seconds = None, None, None
    if args.timing and args.timing.exists():
        timing = json.loads(args.timing.read_text(encoding="utf-8"))
        agent_wall, hit_cap, cap_seconds = timing.get("agent_seconds"), timing.get("hit_cap"), timing.get("agent_cap_seconds")
    counts = {"counts": True, "why": "driver run" + (" on a clean published plugin tree" if cadence else "")}
    if args.kind in record.NON_COUNTING_KINDS:
        counts = {"counts": False, "why": "stub: a session's own probe, not graded"}
    if cadence and not cadence["tree_clean"]:
        counts = {"counts": False, "why": "the plugin tree changed during the run"}
    elif hits:
        counts = {"counts": False, "why": f"the transcript touched the benchmark or another checkout: {hits[0]}"}
    elif lost is not None:
        counts = {"counts": False, "why": f"infrastructure loss: the API answered {lost}"}
    elif prompt is not None and args.agent_argv and (argv_problem := _agent_argv_problem(args.agent_argv, prompt)):
        counts = {"counts": False, "why": f"the agent's argv: {argv_problem}"}
    elif args.shape is not None and (used := repo_profile(args.cwd)) != args.shape:
        counts = {"counts": False, "why": f"the run repo's .cadence.json profile is {used!r}, not --shape {args.shape}"}
    rec = {
        "schema": 1, "run_id": args.run_id, "kind": args.kind, "batch": args.batch,
        "provenance": {"source": "driver", "evidence": [], **({"note": "finished with loop.driver --finish from the "
                       "run's saved directory: the command was not run again; exit_code is unknown"} if args.finish else {})},
        "task": args.task, "request_id": args.request_id,
        "arm": args.arm, "cadence": cadence, "model_requested": args.model, **facts, "command": command,
        "api_error": lost, "shape": args.shape,
        "spec": None if args.spec is None else {"path": str(args.spec.resolve()), "prompt": prompt,
                                                "sha256": hashlib.sha256(args.spec.read_bytes()).hexdigest()},
        "started_at": started, "ended_at": ended, "exit_code": exit_code, "stop_point": stop,
        "transcript": store.put(args.transcript, args.store) if args.transcript.exists()
        else store.missing("the command wrote no transcript"),
        "tree": _tree_blob(args.tree, args.store) if args.tree else store.missing("--tree not given"),
        "counts": counts,
        "timing": {"agent_wall_seconds": agent_wall, "run_wall_seconds": run_wall, "agent_active_seconds": active,
                   # A Cadence run that died before any peer (no .context, or no attest calls) spent zero time
                   # per block: {} (run 20261024-P1-cadence-haiku-core-1r), so it can be timed and published.
                   "blocks": (blocks.peer_time(args.context) or {}) if args.context else None,
                   "hit_cap": hit_cap if isinstance(hit_cap, bool) else None,
                   "cap_seconds": cap_seconds if isinstance(cap_seconds, (int, float)) and not isinstance(cap_seconds, bool) else None},
        "isolation": {"cwd": str(args.cwd.resolve()), "home": str(home), "fresh_home": bool(args.fresh_home),
                      "other_cadence_checkouts": others, "method": args.isolation_method, "auth": args.auth, "contact": hits,
                      "cwd_contents": cwd_contents},
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
    postmortems = args.postmortems or args.runs.resolve().parent / "postmortems"
    board = args.scoreboard or args.runs.resolve().parent / "scoreboard.md"
    for path in postmortem.refresh(args.batch, args.runs, postmortems):
        print(path)
    board.write_text(scoreboard.table(args.runs), encoding="utf-8")
    print(board)
    return 0


if __name__ == "__main__":
    sys.exit(main())
