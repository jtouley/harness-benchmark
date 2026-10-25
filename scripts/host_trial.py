"""One pipeline trial on the host, the command loop.driver runs for batch F (owner, 2026-10-23: "use the
subscription"; the container runner cannot authenticate the agent yet, see runner/README.md).

    python -m loop.driver ... --spec RUN/spec/spec.md --cwd RUN --fresh-home RUN/home \\
        --agent-argv RUN/agent-argv.json --transcript RUN/transcript.jsonl --grade RUN/grade.json \\
        --stop-point-file RUN/stop.json --timing RUN/timing.json --context RUN/context --tree RUN/repo-as-left \\
        --graded-repo RUN/repo -- python scripts/host_trial.py P1 --out RUN --model claude-haiku-5-5 [--plugin-dir PLUGIN --peer-model haiku] \
           [--auth proxy | --auth oauth-file --oauth-file ~/.claude/.credentials.json]

Auth (the driver's --auth records the same value in isolation.auth):
- proxy: this cloud host. Outbound HTTPS goes through a proxy that adds the operator's credentials, so the fresh
  HOME gets no credential file and the agent's environment keeps HTTPS_PROXY and the CA variables only.
- oauth-file: the owner's machine. Claude Code's OAuth credential is ~/.claude/.credentials.json; that one file is
  copied into the fresh HOME (mode 0600) and nothing else from the operator's HOME.
In both, ANTHROPIC_API_KEY and ANTHROPIC_AUTH_TOKEN are dropped from the agent's environment.

The agent's prompt is HB_AGENT_PROMPT, as the driver sets it (`/cadence <spec path>`, or the spec's text for a
one-shot): this script adds no prompt text. In order:

1. The starting repository (pipetask.assemble) in RUN/repo on `main`, with a local bare origin and a committed
   `.cadence.json` that selects the `none` tracker adapter; no feature branch and no ticket (the spec is the
   whole input; F-9 is what Cadence does with that).
2. The dev replay (seed 0) on localhost:8099 while the agent runs.
3. The agent: `claude -p "$HB_AGENT_PROMPT"` in RUN/repo, in its own session (the operator's Claude Code
   variables dropped), HOME as the driver gives it, with the plugin and, for a Cadence arm, peer models from
   `--peer-model` in $HOME/.config/cadence/config.json. It stops at its cap (criteria v2 5.3): a one-shot's guard cap, a Cadence arm's backstop.
   Every process it leaves is stopped before grading. It runs in a jail (jail_argv): its own mount and PID
   namespaces, /home, /root, /tmp, /var/tmp and this checkout covered by empty tmpfs, only the run's repo, origin,
   HOME, spec and plugin bound back, so golden/, the key, the grader and the replay's process are absent.
   Before it starts, a scan from inside the same jail (jail_preflight) must find no harness material:
   RUN/jail.json, and exit 5 if it finds any.
4. The records the grader's reset would lose: RUN/context (a copy of .context), RUN/repo-as-left, the stop
   point (Cadence's own headless.py `next` on a copy of the repository, and the session's hard stop).
5. The grader (pipetask.trial, grading seed 1) on RUN/repo, run from RUN/repo as the container runs it: RUN/grade.json. RUN/timing.json has agent_seconds.
   With --grader-root, pipetask, the key and the capture come from that checkout (scripts/run_one.sh: a worktree at
   the batch's pinned grader_commit), not from this one; the jail hides it too.
   The grader commits the working tree the agent left (--snapshot-worktree) in RUN/repo and grades that commit;
   the driver's --graded-repo RUN/repo puts it into the stored bundle as refs/graded/<run-id> (loop.graded).
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GP = ROOT / "golden" / "pipeline"
CAPS = ROOT / "runner" / "pipeline" / "caps.json"
PORT = 8099
GATED = ["src/", "lib/", "app/", "packages/", "pipeline/", "engine/", "pipelines/", "transform/", "Makefile"]
DROPPED_PREFIXES = ("CLAUDE", "CCR_", "AI_AGENT", "DOCUMENTS_", "TYPESAFE_")  # TYPESAFE_: no verdict judge in a run


def agent_cap(plugin: Path | None, override: int | None = None) -> int:
    """Seconds after which the agent is stopped (criteria v2 section 5.3, runner/pipeline/caps.json): a one-shot
    at its guard cap, a harness arm (a plugin) only at the harness backstop; `override` is a batch's own cap
    (batch F: 21,600 s for the Cadence arm, 3 x the one-shot cap)."""
    if override:
        return override
    caps = json.loads(CAPS.read_text(encoding="utf-8"))
    return caps["harness_backstop"]["default"]["seconds"] if plugin is not None else caps["agent_timeout"]


def _port_open() -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


def _git(repo: Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "-c", "user.name=cbench", "-c", "user.email=cbench@localhost", *args], cwd=repo,
                   env=env, check=True, capture_output=True)


SHAPES = ("core", "full")


def cadence_config(shape: str | None) -> dict:
    """The run repo's .cadence.json: the `none` tracker adapter, the gated prefixes, and with a run shape
    (owner, 2026-10-24: core and full, head to head) its `profile`, the key cadence PR 2 defines."""
    config = {"adapter": "none", "gated_prefixes": GATED}
    if shape is not None:
        config["profile"] = shape
    return config


# The agent's jail (2026-10-24, run 20261024-P2-cadence-haiku-core-3: the agent's `ps` listed the dev replay,
# `$WORK/hb/.venv/bin/python3 -m pipetask.replay`, and $WORK/hb held golden/ and the key). The agent runs as root,
# so permissions do not hide anything: in its own mount and PID namespaces, empty tmpfs mounts cover these
# folders and this checkout, and only the run's own folders are bound back. Processes outside (the replay, the
# driver, this script) are not in its /proc.
JAIL_HIDE = ("/home", "/root", "/tmp", "/var/tmp")
# The proxy's CA bundle; uv; and the cloud session's OAuth token, which claude reads at this fixed path whatever
# HOME is (--auth proxy: without it the agent is "Not logged in"; it was readable to the agent before the jail too).
JAIL_KEEP = ("/root/.ccr", "/root/.local/bin", "/home/claude/.claude/remote/.oauth_token")
_JAIL = r"""set -euo pipefail
hide=(); while [ "$1" != -- ]; do hide+=("$1"); shift; done; shift
keep=(); while [ "$1" != -- ]; do keep+=("$1"); shift; done; shift
mount -t tmpfs -o size=1m jail /mnt
for i in "${!keep[@]}"; do
  if [ -d "${keep[i]}" ]; then mkdir "/mnt/$i"; else : >"/mnt/$i"; fi
  mount --bind "${keep[i]}" "/mnt/$i"
done
for h in "${hide[@]}"; do mount -t tmpfs -o mode=1777 jail "$h"; done
for i in "${!keep[@]}"; do
  if [ -d "/mnt/$i" ]; then mkdir -p "${keep[i]}"; else mkdir -p "$(dirname "${keep[i]}")"; : >"${keep[i]}"; fi
  mount --bind "/mnt/$i" "${keep[i]}"
done
umount -l /mnt
cd -- "$PWD"
exec "$@"
"""


def _outermost(paths) -> list[Path]:
    paths = sorted({Path(p) for p in paths})
    return [p for p in paths if not any(q in p.parents for q in paths)]


def jail_paths(out: Path, home: Path, plugin: Path | None, spec_dir: Path | None,
               grader_root: Path | None = None) -> tuple[list[Path], list[Path]]:
    """(hidden, kept): the folders covered while the agent runs, this checkout and the grader's always among them,
    and the ones bound back: the run's repository, its origin, HOME, the spec, the plugin, and the host's CA bundle
    and uv."""
    hide = _outermost([*map(Path, JAIL_HIDE), ROOT, *([grader_root] if grader_root else [])])
    keep = [out / "repo", out / "origin.git", home, *(p for p in (plugin, spec_dir) if p), *map(Path, JAIL_KEEP)]
    keep = [k for k in _outermost(keep) if k.exists() and any(h == k or h in k.parents for h in hide)]
    return [h for h in hide if h.is_dir()], keep


def jail_argv(hide, keep, argv: list[str]) -> list[str]:
    return ["unshare", "--mount", "--pid", "--fork", "--kill-child", "--mount-proc", "--propagation", "private",
            "bash", "-c", _JAIL, "jail", *map(str, hide), "--", *map(str, keep), "--", *argv]


def scan_for_harness(top) -> list[str]:
    """The paths under `top` that are this harness's material: a golden/ of tasks, the grader, a key, a
    reference patch, the pipetask package, a harness-benchmark checkout (not Cadence's own tests/fixtures/golden)."""
    import os
    names = ("pipetask", "harness-benchmark", "grader.pyz", "reference.patch")
    hits = []
    for d, dirs, files in os.walk(top):
        if d in ("/proc", "/sys", "/dev"):
            dirs[:] = []
            continue
        for n in dirs + files:
            path = os.path.join(d, n)
            if n in names or n.startswith("answer_key") or (n == "golden" and n in dirs and any(
                    os.path.isdir(os.path.join(path, sub)) for sub in ("pipeline", "probes", "tasks"))):
                hits.append(path)
        dirs[:] = [n for n in dirs if os.path.join(d, n) not in hits]
    return hits


def jail_preflight(hide, keep) -> list[str]:
    """scan_for_harness over the whole filesystem, from inside the agent's jail: what the agent could list."""
    code = inspect.getsource(scan_for_harness) + "\nimport sys\nprint('\\n'.join(scan_for_harness('/')))\n"
    python = shutil.which("python3", path="/usr/local/bin:/usr/bin:/bin") or "python3"
    proc = subprocess.run(jail_argv(hide, keep, [python, "-I", "-c", code]), cwd="/", capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"the agent's jail does not start: {proc.stderr.strip()}")
    return proc.stdout.split()


def setup_repo(task: str, out: Path, shape: str | None = None) -> Path:
    repo = out / "repo"
    subprocess.run([sys.executable, "-m", "pipetask.assemble", task, "--out", str(repo)], cwd=GP, check=True,
                   capture_output=True)
    (repo / ".cadence.json").write_text(json.dumps(cadence_config(shape), indent=1) + "\n")
    _git(out, "init", "-q", "--bare", str(out / "origin.git"))
    _git(repo, "add", ".cadence.json")
    _git(repo, "commit", "-q", "-m", "cadence config for the trial")
    _git(repo, "remote", "add", "origin", str(out / "origin.git"))
    _git(repo, "push", "-q", "-u", "origin", "HEAD")
    return repo


def agent_env(home: Path, plugin: Path | None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(DROPPED_PREFIXES + ("UV_",))
           and k not in ("HB_AGENT_PROMPT", "VIRTUAL_ENV", "PYTHONPATH", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    # This script runs in harness-benchmark's environment (uv run): its python must not be the agent's.
    venv = os.environ.get("VIRTUAL_ENV")
    env["PATH"] = os.pathsep.join(d for d in env.get("PATH", "").split(os.pathsep)
                                  if d and not (venv and d.startswith(venv)) and str(ROOT) not in d)
    env.update(HOME=str(home), DISABLE_AUTOUPDATER="1", CLAUDE_AUTO_BACKGROUND_TASKS="false",
               CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS="0", PYTHONDONTWRITEBYTECODE="1")
    if plugin is not None:
        env["CADENCE_HOME"] = str(plugin)
    return env


def grade_command(repo: Path, out: Path, grader_root: Path | None = None) -> tuple[list[str], Path, dict[str, str]]:
    """The grader's argv, working directory and environment. It runs from the task repository, as the
    container runner runs it from /trial/repo: oracle.py allows DuckDB only the repository's out/marts/, and an
    oracle_map path such as `out/marts/x.parquet` resolves against the working directory. The grader's code, key
    and capture are grader_root's golden/pipeline (the batch's pinned grader), else this checkout's."""
    gp = grader_root / "golden" / "pipeline" if grader_root else GP
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, [str(gp), os.environ.get("PYTHONPATH")]))}
    argv = [sys.executable, "-m", "pipetask.trial", "--repo", str(repo), "--key", str(gp / "key" / "answer_key.json"),
            "--capture", str(gp / "data" / "capture" / "recentchange.jsonl.gz"), "--deadline", "600",
            "--snapshot-worktree", "--logs", str(out / "grade-logs")]
    return argv, repo, env


def grade(repo: Path, out: Path, grader_root: Path | None = None) -> int:
    """Grade `repo` (seed 1): out/grade.json and out/grade.stderr; the grader's exit code."""
    argv, cwd, env = grade_command(repo, out, grader_root)
    with open(out / "grade.json", "w") as stdout, open(out / "grade.stderr", "w") as stderr:
        return subprocess.run(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr).returncode


def prepare_home(home: Path, auth: str, oauth_file: Path | None) -> None:
    """Give the fresh HOME exactly what the auth route needs: nothing for proxy, the one OAuth file for oauth-file."""
    if auth == "proxy":
        return
    if auth != "oauth-file" or oauth_file is None or not oauth_file.is_file():
        raise SystemExit(f"host_trial: --auth {auth} needs --oauth-file, the operator's .credentials.json")
    target = home / ".claude" / ".credentials.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(oauth_file.read_bytes())
    target.chmod(0o600)


_BLOCK_CLASS = re.compile(r"^([a-z])(\d+)-")
_BLOCK_REASON = re.compile(r"^([AEPR])(\d)\b")


def stop_block(open_block: str | None, hard: dict | str | None) -> str | None:
    """The block a run stopped at: the one a hard stop's class names (`a5-gap` is A5), else a block id that
    opens its reason (class `retries`: "A5 validate-gate fails ..."), else the open block. A hard stop sends
    the run back to activation, so headless `next` reports A1 (review of #81)."""
    if not isinstance(hard, dict):
        return open_block
    match = _BLOCK_CLASS.match(str(hard.get("class") or "")) or _BLOCK_REASON.match(str(hard.get("reason") or ""))
    return f"{match.group(1).upper()}{match.group(2)}" if match else open_block


_OPEN_BLOCK = re.compile(r"Continue paceline: next ([AEPR]\d+) \(([\w-]+)\)")
_STAMP = re.compile(r'"timestamp": ?"([^"]+)"')
_REFUSED = re.compile(r"stop refused (\d+) times")


def open_block(lines) -> dict | None:
    """The last block Cadence's Stop hook named open in the transcript ("Continue paceline: next R5 (closure)"),
    with how many times it refused the stop, or None. Run 20261024-P2-cadence-haiku-core-1 ended stuck at R5,
    and the headless probe, run later in a copy with no live session, said A1."""
    found = None
    for line in lines:
        for block, slug in _OPEN_BLOCK.findall(line):
            stamp = _STAMP.search(line)
            found = {"block": block, "slug": slug, "refused": None, "at": stamp.group(1) if stamp else None}
        refused = _REFUSED.findall(line)
        if refused and found is not None:
            found["refused"] = int(refused[-1])
    return found


def closed_session(repo: Path) -> str | None:
    """When Cadence closed the run's session at R7 (session-close: `activate_session.py --deactivate` sets status
    "completed", which it allows only once E1 through R6 pass or with a hard stop) and no hard stop is recorded:
    its completed_at, from the run's own .context. Else None."""
    for path in sorted((repo / ".context" / "sessions" / "by-worktree").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and data.get("status") == "completed" and not data.get("hard_stop"):
            return str(data.get("completed_at") or "unknown")
    return None


def choose_stop(headless_block: str | None, hard: dict | str | None, opened: dict | None, why: str,
                closed: str | None = None) -> dict:
    """The stop of a run that did not finish (headless reports a block): the block a hard stop names; done (R7)
    when Cadence closed the session and the Stop hook never refused a stop (run 20261024-P2-cadence-haiku-core-3:
    the probe's A1 was "no active cadence session", the closed session); else the last block the Stop hook named
    open; else the headless probe's block."""
    if headless_block is None:
        return {"block": None, "reason": None}
    if hard:
        return {"block": stop_block(headless_block, hard), "reason": why[:300] or None}
    if closed is not None and (opened is None or _before(opened.get("at"), closed)):
        # --deactivate closes a run only after R6 passed (no hard stop here), so a refusal before the close is
        # history, not the stop: 20261024-P1-cadence-haiku-full-6 closed at 21:22 after refusals at a stale E4.
        return {"block": "R7", "reason": f"done: the session closed at R7 (session-close) at {closed}, with no "
                                          f"Stop-hook refusal ({why})"[:300]}
    if opened is not None:
        refused = f": the Stop hook refused the stop {opened['refused']} times" if opened["refused"] else ""
        return {"block": opened["block"],
                "reason": f"open at {opened['block']} ({opened['slug']}){refused} ({why})"[:300]}
    return {"block": headless_block, "reason": why[:300] or None}


def _before(at: str | None, closed: str) -> bool:
    """True when the refusal time `at` is known and earlier than the close time."""
    from datetime import datetime
    try:
        return at is not None and datetime.fromisoformat(at.replace("Z", "+00:00")) < \
            datetime.fromisoformat(closed.replace("Z", "+00:00"))
    except ValueError:
        return False


def rebind_sessions(copy: Path) -> None:
    """Give the copy its own worktree session. Cadence keys a session by sha256 of the git toplevel, so in a copy
    activate_session.py --check found none: A1 failed and every stop reason of shapes-r2 ended in
    "(FAIL  no active cadence session)", whatever the real open gate was."""
    import hashlib
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=copy, capture_output=True, text=True)
    root = Path(top.stdout.strip() if top.returncode == 0 and top.stdout.strip() else copy).resolve()
    key = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:16]
    folder = copy / ".context" / "sessions" / "by-worktree"
    for path in sorted(folder.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and "ref" not in data and data.get("status") != "completed":
            (folder / f"{key}.json").write_text(json.dumps({**data, "workspace": str(root)}, indent=2) + "\n",
                                                encoding="utf-8")
            return


def stop_point(repo: Path, plugin: Path, env: dict[str, str], transcript: list[str] = ()) -> dict:
    """The block the run stopped at, and why: from Cadence's headless runner in a copy of the repository, the
    session's hard stop and the transcript's last open block (choose_stop)."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "repo"
        shutil.copytree(repo, copy, symlinks=True)
        rebind_sessions(copy)
        proc = subprocess.run([sys.executable, str(plugin / "scripts" / "headless.py"), "next", "--json"], cwd=copy,
                              env=env, capture_output=True, text=True, timeout=900)
        hard = None
        for session in sorted((copy / ".context" / "sessions" / "by-worktree").glob("*.json")):
            data = json.loads(session.read_text(encoding="utf-8"))
            hard = data.get("hard_stop") or hard
    try:
        report = json.loads(proc.stdout)
    except ValueError:
        return {"block": "?", "reason": f"headless.py next exited {proc.returncode}: {proc.stderr.strip()[-200:]}"}
    nxt = report.get("next")
    if not nxt:
        return {"block": None, "reason": None}
    failing = [r for r in report.get("results", []) if not r.get("ok")]
    why = next((line.strip() for line in str((failing[-1] if failing else {}).get("output") or "").splitlines()
                if line.strip()), "")
    if hard:
        why = f"hard stop {hard.get('class') if isinstance(hard, dict) else hard}: " + \
              (hard.get("reason", "") if isinstance(hard, dict) else "") + (f" ({why})" if why else "")
    return choose_stop(nxt.get("block"), hard, open_block(transcript), why, closed_session(repo))


def jail_check(out: Path, plugin: Path | None, model: str) -> int:
    """The agent's jail on this host as a run would build it, with no run: nothing of the harness can be listed
    from inside, and the agent can log in there (the session's token is bound back). Exit 0, or 5."""
    home = out / "home"
    home.mkdir(parents=True, exist_ok=True)
    hide, keep = jail_paths(out, home, plugin, out / "spec" if (out / "spec").is_dir() else None)
    visible = jail_preflight(hide, keep)
    proc = subprocess.run(jail_argv(hide, keep, ["timeout", "120", "claude", "-p", "Reply with the one word OK.",
                                                  "--model", model]),
                          cwd=home, env=agent_env(home, plugin), capture_output=True, text=True)
    report = {"hidden": [str(p) for p in hide], "kept": [str(p) for p in keep], "visible": visible,
              "agent_exit": proc.returncode, "agent_reply": proc.stdout.strip()[-200:]}
    (out / "jail-check.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report))
    return 0 if not visible and proc.returncode == 0 else 5


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("task", choices=["P1", "P2", "P3"])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--plugin-dir", type=Path)
    ap.add_argument("--peer-model", help="Cadence arm: peer_models.default in the run's Cadence config")
    ap.add_argument("--agent-cap", type=int, help="seconds: the batch's cap for this arm (see agent_cap)")
    ap.add_argument("--shape", choices=SHAPES, help="Cadence arm: the run shape, as the run repo's .cadence.json profile")
    ap.add_argument("--stop-file", type=Path, help="--stop-only: where to write the stop (default: --out/stop.json)")
    ap.add_argument("--stop-only", action="store_true",
                    help="the run already ran in --out: derive its stop point again (stop.json) and do nothing else")
    ap.add_argument("--auth", choices=["proxy", "oauth-file"], default="proxy")
    ap.add_argument("--grader-root", type=Path, help="a harness-benchmark checkout at the batch's pinned "
                    "grader_commit: the grade runs its golden/pipeline/pipetask (default: this checkout)")
    ap.add_argument("--oauth-file", type=Path, help="--auth oauth-file: the operator's ~/.claude/.credentials.json")
    ap.add_argument("--jail-check", action="store_true",
                    help="run_one --dry-run: the agent's jail on this host, without the run: the scan from inside "
                         "(jail_preflight) and a one-line claude -p in it (--out/jail-check.json)")
    args = ap.parse_args(argv)
    if args.jail_check:
        return jail_check(args.out.resolve(), args.plugin_dir.resolve() if args.plugin_dir else None, args.model)
    if args.stop_only:  # run_one --finish: the stop of a run that already ran, with this checkout's rules
        out = args.out.resolve()
        plugin = args.plugin_dir.resolve() if args.plugin_dir else None
        if plugin is None or not (out / "repo-as-left").is_dir():
            print(f"host_trial: --stop-only needs --plugin-dir and {out}/repo-as-left", file=sys.stderr)
            return 2
        lines = (out / "transcript.jsonl").read_text(encoding="utf-8", errors="replace").splitlines() \
            if (out / "transcript.jsonl").exists() else []
        stop = stop_point(out / "repo-as-left", plugin, agent_env(out / "home", plugin), lines)
        (args.stop_file or out / "stop.json").write_text(json.dumps(stop) + "\n")
        print(json.dumps(stop))
        return 0
    prompt = os.environ.get("HB_AGENT_PROMPT")
    if not prompt:
        print("host_trial: HB_AGENT_PROMPT is not set; run this through loop.driver --spec", file=sys.stderr)
        return 2
    out, home = args.out.resolve(), Path(os.environ["HOME"])
    plugin = args.plugin_dir.resolve() if args.plugin_dir else None
    prepare_home(home, args.auth, args.oauth_file)
    repo = setup_repo(args.task, out, args.shape)
    if plugin is not None and args.peer_model:
        (home / ".config" / "cadence").mkdir(parents=True, exist_ok=True)
        (home / ".config" / "cadence" / "config.json").write_text(
            json.dumps({"peer_models": {"default": args.peer_model}}) + "\n")
    spec_dir = Path(prompt.split(" ", 1)[1]).parent if plugin is not None else None

    grader_root = args.grader_root.resolve() if args.grader_root else None
    if grader_root is not None and not (grader_root / "golden" / "pipeline" / "pipetask").is_dir():
        print(f"host_trial: --grader-root {grader_root} has no golden/pipeline/pipetask", file=sys.stderr)
        return 2
    hide, keep = jail_paths(out, home, plugin, spec_dir, grader_root)
    visible = jail_preflight(hide, keep)
    (out / "jail.json").write_text(json.dumps({"hidden": [str(p) for p in hide], "kept": [str(p) for p in keep],
                                               "visible": visible}, indent=1) + "\n")
    if visible:
        print(f"host_trial: the agent could list harness material: {visible[:5]}", file=sys.stderr)
        return 5
    if _port_open():
        print(f"host_trial: port {PORT} is taken before the dev replay starts", file=sys.stderr)
        return 4
    replay = subprocess.Popen([sys.executable, "-m", "pipetask.replay", "--capture",
                               "data/capture/recentchange.jsonl.gz", "--seed", "0", "--port", str(PORT)],
                              cwd=GP, stdout=open(out / "replay-dev.log", "w"), stderr=subprocess.STDOUT)
    for _ in range(60):
        if _port_open():
            break
        time.sleep(1)

    argv_agent = ["claude", "-p", prompt, "--model", args.model, "--permission-mode", "auto",
                  "--output-format", "stream-json", "--verbose"]
    if plugin is not None:
        argv_agent += ["--plugin-dir", str(plugin)]
    if spec_dir is not None:
        argv_agent += ["--add-dir", str(spec_dir)]
    (out / "agent-argv.json").write_text(json.dumps(argv_agent) + "\n")
    env = agent_env(home, plugin)
    cap = agent_cap(plugin, args.agent_cap)
    t0 = time.monotonic()
    with open(out / "transcript.jsonl", "w") as stdout, open(out / "agent.stderr", "w") as stderr:
        agent = subprocess.Popen(jail_argv(hide, keep, ["timeout", str(cap), *argv_agent]), cwd=repo, env=env, stdout=stdout,
                                 stderr=stderr, start_new_session=True)
        rc = agent.wait()
    agent_seconds = round(time.monotonic() - t0, 1)
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(agent.pid, sig)
        except ProcessLookupError:
            pass
        time.sleep(2)
    replay.terminate()
    replay.wait(30)

    if (repo / ".context").is_dir():
        shutil.copytree(repo / ".context", out / "context", symlinks=True)
    shutil.copytree(repo, out / "repo-as-left", symlinks=True)
    lines = (out / "transcript.jsonl").read_text(encoding="utf-8", errors="replace").splitlines() \
        if (out / "transcript.jsonl").exists() else []
    stop = stop_point(out / "repo-as-left", plugin, env, lines) if plugin is not None else {"block": None, "reason": None}
    (out / "stop.json").write_text(json.dumps(stop) + "\n")

    t1 = time.monotonic()
    grc = grade(repo, out, grader_root)
    (out / "timing.json").write_text(json.dumps({
        "agent_seconds": agent_seconds, "grader_seconds": round(time.monotonic() - t1, 1), "agent_exit": rc,
        "grader_exit": grc, "agent_cap_seconds": cap, "hit_cap": rc == 124}, indent=1) + "\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
