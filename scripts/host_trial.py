"""One pipeline trial on the host, the command loop.driver runs for batch F (owner, 2026-10-23: "use the
subscription"; the container runner cannot authenticate the agent yet, see runner/README.md).

    python -m loop.driver ... --spec RUN/spec/spec.md --cwd RUN --fresh-home RUN/home \\
        --agent-argv RUN/agent-argv.json --transcript RUN/transcript.jsonl --grade RUN/grade.json \\
        --stop-point-file RUN/stop.json --timing RUN/timing.json --context RUN/context --tree RUN/repo-as-left \\
        -- python scripts/host_trial.py P1 --out RUN --model claude-haiku-5-5 [--plugin-dir PLUGIN --peer-model haiku] \
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
   Every process it leaves is stopped before grading.
4. The records the grader's reset would lose: RUN/context (a copy of .context), RUN/repo-as-left, the stop
   point (Cadence's own headless.py `next` on a copy of the repository, and the session's hard stop).
5. The grader (pipetask.trial, grading seed 1) on RUN/repo, run from RUN/repo as the container runs it: RUN/grade.json. RUN/timing.json has agent_seconds.
"""

from __future__ import annotations

import argparse
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
DROPPED_PREFIXES = ("CLAUDE", "CCR_", "AI_AGENT", "DOCUMENTS_")


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


def setup_repo(task: str, out: Path) -> Path:
    repo = out / "repo"
    subprocess.run([sys.executable, "-m", "pipetask.assemble", task, "--out", str(repo)], cwd=GP, check=True,
                   capture_output=True)
    (repo / ".cadence.json").write_text(json.dumps({"adapter": "none", "gated_prefixes": GATED}, indent=1) + "\n")
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


def grade_command(repo: Path, out: Path) -> tuple[list[str], Path, dict[str, str]]:
    """The grader's argv, working directory and environment. It runs from the task repository, as the
    container runner runs it from /trial/repo: oracle.py allows DuckDB only the repository's out/marts/, and an
    oracle_map path such as `out/marts/x.parquet` resolves against the working directory."""
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, [str(GP), os.environ.get("PYTHONPATH")]))}
    argv = [sys.executable, "-m", "pipetask.trial", "--repo", str(repo), "--key", str(GP / "key" / "answer_key.json"),
            "--capture", str(GP / "data" / "capture" / "recentchange.jsonl.gz"), "--deadline", "600",
            "--snapshot-worktree", "--logs", str(out / "grade-logs")]
    return argv, repo, env


def grade(repo: Path, out: Path) -> int:
    """Grade `repo` (seed 1): out/grade.json and out/grade.stderr; the grader's exit code."""
    argv, cwd, env = grade_command(repo, out)
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


def stop_block(open_block: str | None, hard: dict | str | None) -> str | None:
    """The block a run stopped at: the one a hard stop's class names (`a5-gap` is A5), else the open block. A
    hard stop sends the run back to activation, so headless `next` reports A1 (review of #81)."""
    match = _BLOCK_CLASS.match(str(hard.get("class") or "")) if isinstance(hard, dict) else None
    return f"{match.group(1).upper()}{match.group(2)}" if match else open_block


def stop_point(repo: Path, plugin: Path, env: dict[str, str]) -> dict:
    """The block Cadence's own headless runner reports open in a copy of the repository, and why."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "repo"
        shutil.copytree(repo, copy, symlinks=True)
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
    return {"block": stop_block(nxt.get("block"), hard), "reason": why[:300] or None}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("task", choices=["P1", "P2", "P3"])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--plugin-dir", type=Path)
    ap.add_argument("--peer-model", help="Cadence arm: peer_models.default in the run's Cadence config")
    ap.add_argument("--agent-cap", type=int, help="seconds: the batch's cap for this arm (see agent_cap)")
    ap.add_argument("--auth", choices=["proxy", "oauth-file"], default="proxy")
    ap.add_argument("--oauth-file", type=Path, help="--auth oauth-file: the operator's ~/.claude/.credentials.json")
    args = ap.parse_args(argv)
    prompt = os.environ.get("HB_AGENT_PROMPT")
    if not prompt:
        print("host_trial: HB_AGENT_PROMPT is not set; run this through loop.driver --spec", file=sys.stderr)
        return 2
    out, home = args.out.resolve(), Path(os.environ["HOME"])
    plugin = args.plugin_dir.resolve() if args.plugin_dir else None
    prepare_home(home, args.auth, args.oauth_file)
    repo = setup_repo(args.task, out)
    if plugin is not None and args.peer_model:
        (home / ".config" / "cadence").mkdir(parents=True, exist_ok=True)
        (home / ".config" / "cadence" / "config.json").write_text(
            json.dumps({"peer_models": {"default": args.peer_model}}) + "\n")
    spec_dir = Path(prompt.split(" ", 1)[1]).parent if plugin is not None else None

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
        agent = subprocess.Popen(["timeout", str(cap), *argv_agent], cwd=repo, env=env, stdout=stdout,
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
    stop = stop_point(out / "repo-as-left", plugin, env) if plugin is not None else {"block": None, "reason": None}
    (out / "stop.json").write_text(json.dumps(stop) + "\n")

    t1 = time.monotonic()
    grc = grade(repo, out)
    (out / "timing.json").write_text(json.dumps({
        "agent_seconds": agent_seconds, "grader_seconds": round(time.monotonic() - t1, 1), "agent_exit": rc,
        "grader_exit": grc, "agent_cap_seconds": cap, "hit_cap": rc == 124}, indent=1) + "\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
