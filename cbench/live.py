"""Tier 3: run an agent on golden tasks and record everything needed to regrade.

Model sampling is not deterministic, so a live run is treated as an observation:
the transcript and the final patch are stored with hashes, and every number in
the report is derived from those stored files (`cbench grade`). Re-running the
live step gives a new sample from the same distribution; use several trials.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .grade import prepare_workspace, task_digest, task_dirs
from .lock import ensure_fetched, load_lock, select
from .usage import parse_transcript
from .util import RESULTS_DIR, clean_env, load_json, run, sha256_file, sha256_text, write_json

AGENT_ENV_PASSTHROUGH = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL")


def run_dir(fw: str, task: str, trial: int) -> Path:
    return RESULTS_DIR / "runs" / fw / task / f"trial-{trial:02d}"


def agent_version(agent_cmd: str) -> str:
    try:
        proc = subprocess.run([agent_cmd, "--version"], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f"cannot run agent {agent_cmd!r}: {exc}")
    return proc.stdout.strip() or proc.stderr.strip()


def build_argv(agent_cmd: str, prompt: str, model: str, budget: float, plugin_dirs) -> list[str]:
    argv = [
        agent_cmd, "-p", prompt,
        "--model", model,
        "--output-format", "stream-json", "--verbose",
        "--max-budget-usd", f"{budget:.2f}",
        "--permission-mode", "bypassPermissions",
        "--setting-sources", "user,project,local",
    ]
    for plugin in plugin_dirs:
        argv += ["--plugin-dir", str(plugin)]
    return argv


def run_one(fw, lock, task_dir: Path, trial: int, args, version: str) -> Path:
    out = run_dir(fw.name, task_dir.name, trial)
    if (out / "record.json").is_file():
        print(f"skip  {fw.name}/{task_dir.name}/trial-{trial:02d} (recorded)", flush=True)
        return out
    sb, base = prepare_workspace(fw, lock, task_dir)
    issue = (task_dir / load_json(task_dir / "task.json")["issue"]).read_text(encoding="utf-8").strip()
    prompt = fw.drive_prompt.format(issue=issue) + lock.drive_suffix
    argv = build_argv(args.agent_cmd, prompt, args.model, args.max_budget_usd, sb.plugin_dirs)

    passthrough = {k: os.environ[k] for k in AGENT_ENV_PASSTHROUGH if k in os.environ}
    env = clean_env(home=sb.home, network=True, extra={
        **passthrough,
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "DISABLE_AUTOUPDATER": "1",
        "CBENCH_TASK_ID": task_dir.name,
    })
    print(f"run   {fw.name}/{task_dir.name}/trial-{trial:02d}", flush=True)
    start = time.monotonic()
    timed_out = False
    try:
        proc = subprocess.run(argv, cwd=str(sb.proj), env=env, capture_output=True, text=True,
                              timeout=args.timeout, stdin=subprocess.DEVNULL)
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        code, timed_out = None, True
    wall = round(time.monotonic() - start, 1)

    genv = clean_env(home=sb.home)
    run(["git", "add", "-A"], cwd=sb.proj, env=genv)
    patch = run(["git", "diff", "--cached", "--binary", base], cwd=sb.proj, env=genv).stdout
    changed = run(["git", "diff", "--cached", "--name-only", base], cwd=sb.proj, env=genv).stdout.split()

    tmp = out.with_name(out.name + ".partial")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    (tmp / "transcript.jsonl").write_text(stdout, encoding="utf-8")
    (tmp / "stderr.txt").write_text(stderr[-20000:], encoding="utf-8")
    (tmp / "patch.diff").write_text(patch, encoding="utf-8")
    record = {
        "schema": 1,
        "framework": fw.name,
        "framework_sha": fw.sha,
        "task": task_dir.name,
        "task_sha256": task_digest(task_dir),
        "trial": trial,
        "model": args.model,
        "agent": Path(args.agent_cmd).name,
        "agent_version": version,
        "argv_without_prompt": [a for a in argv if a != prompt],
        "prompt_sha256": sha256_text(prompt),
        "lock_sha256": lock.sha256,
        "base_commit": base,
        "exit_code": code,
        "timed_out": timed_out,
        "wall_seconds": wall,
        "transcript_sha256": sha256_file(tmp / "transcript.jsonl"),
        "patch_sha256": sha256_file(tmp / "patch.diff"),
        "files_changed": sorted(changed),
        "usage": parse_transcript(stdout),
    }
    write_json(tmp / "record.json", record)
    if out.exists():
        shutil.rmtree(out)
    tmp.rename(out)
    return out


def run_matrix(args) -> int:
    lock = load_lock()
    fws = select(lock, args.frameworks)
    ensure_fetched(fws)
    tasks = task_dirs()
    if args.tasks:
        tasks = [t for t in tasks if t.name in set(args.tasks)]
    n = len(fws) * len(tasks) * args.trials
    ceiling = n * args.max_budget_usd
    print(f"{len(fws)} framework(s) x {len(tasks)} task(s) x {args.trials} trial(s) = {n} runs; "
          f"spend ceiling ${ceiling:.2f} at --max-budget-usd {args.max_budget_usd:.2f} on {args.model}")
    if not args.yes:
        if not sys.stdin.isatty():
            print("refusing to spend without --yes in a non-interactive shell")
            return 2
        if input("proceed? [y/N] ").strip().lower() != "y":
            return 1
    version = agent_version(args.agent_cmd)
    for fw in fws:
        for task_dir in tasks:
            for trial in range(1, args.trials + 1):
                run_one(fw, lock, task_dir, trial, args, version)
    print("done; next: python -m cbench grade && python -m cbench report")
    return 0
