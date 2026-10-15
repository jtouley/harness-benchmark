"""Run pipeline-family trials (P1, P2, P3) on the isolated runner, and summarize them.

    # one trial: assemble the starting repository, bundle replay.pyz and grader.pyz, run the runner
    python scripts/pipeline_trial.py run P1 --model claude-haiku-5-5 --out results/runs/pipeline/P1-haiku-1
    # the smoke trial (the reference, no agent) and the negative control (the skeleton, no agent)
    python scripts/pipeline_trial.py run P1 --mode reference --out results/runs/pipeline/P1-ref-1
    python scripts/pipeline_trial.py run P1 --mode skeleton --out results/runs/pipeline/P1-skel-1
    # set a task's grader caps from its reference trials: the measured worst case plus 50%
    python scripts/pipeline_trial.py caps P1 results/runs/pipeline/P1-ref-*
    # the results table (markdown) and its rows (JSON)
    python scripts/pipeline_trial.py summary results/runs/pipeline/* [--json FILE]

The image per task and the caps are in runner/pipeline/caps.json. The API key comes from the
environment, as run_trial.sh reads it; this script never prints it, and drops it for runs with no agent.
Cost is computed from token counts at pricing.json list prices, per model in the session.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "golden" / "pipeline"
CAPS = ROOT / "runner" / "pipeline" / "caps.json"
PRICING = ROOT / "pricing.json"
RUN_TRIAL = ROOT / "runner" / "run_trial.sh"
NO_AGENT = "#!/usr/bin/env bash\n# No agent: the repository is graded as delivered.\nexit 0\n"

API_ERROR = re.compile(r"API Error|Request timed out|overloaded|Connection error|ECONNRESET|socket hang up",
                       re.IGNORECASE)
STALL_IDLE_SECONDS = 600  # a session silent this long before the guard cap ended it was stalled


# --- cost --------------------------------------------------------------------------------------------

def _price(model: str, pricing: dict) -> dict:
    models = pricing["models"]
    name = re.sub(r"\[.*\]$", "", model)
    for candidate in (name, re.sub(r"-\d{8}$", "", name)):
        if candidate in models:
            return models[candidate]
    raise KeyError(f"no price for model {model!r} in pricing.json")


def cost_and_tokens(result: dict, pricing: dict, model: str | None = None) -> tuple[Decimal, dict]:
    """Cost at list prices and token totals, from Claude Code's per-model usage (or `usage` for `model`)."""
    per_model = result.get("modelUsage")
    if not per_model:
        u = result.get("usage") or {}
        if not u:
            return Decimal(0), {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0}
        per_model = {model or "unknown": {"inputTokens": u.get("input_tokens", 0),
                                          "outputTokens": u.get("output_tokens", 0),
                                          "cacheCreationInputTokens": u.get("cache_creation_input_tokens", 0),
                                          "cacheReadInputTokens": u.get("cache_read_input_tokens", 0)}}
    total, tokens = Decimal(0), {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0}
    for name, u in per_model.items():
        p = _price(name, pricing)
        n = {"input": u.get("inputTokens", 0), "output": u.get("outputTokens", 0),
             "cache_write": u.get("cacheCreationInputTokens", 0), "cache_read": u.get("cacheReadInputTokens", 0)}
        for k in tokens:
            tokens[k] += n[k]
        total += (n["input"] * Decimal(p["input"]) + n["output"] * Decimal(p["output"])
                  + n["cache_write"] * Decimal(p["cache_write_5m"]) + n["cache_read"] * Decimal(p["cache_read"])
                  ) / Decimal(1_000_000)
    return total, tokens


# --- one run -----------------------------------------------------------------------------------------

def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, ValueError):
        return {}


def _session_span(run: Path) -> float | None:
    """Seconds between the first and last timestamp of Claude Code's session logs."""
    stamps = []
    for f in (run / "claude-projects").rglob("*.jsonl") if (run / "claude-projects").is_dir() else []:
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                ts = json.loads(line).get("timestamp")
            except (ValueError, AttributeError):
                continue
            if isinstance(ts, str):
                stamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
    return (max(stamps) - min(stamps)).total_seconds() if stamps else None


def outcome(run: Path, result: dict, timing: dict) -> str:
    """graded, api_stall (not a model failure), guard_cap (attempted, not delivered) or infra_error."""
    if not timing:
        return "infra_error"
    if result.get("is_error") and API_ERROR.search(str(result.get("result", ""))):
        return "api_stall"
    if timing.get("agent_exit") in (124, 137):
        span = _session_span(run)
        if span is not None and timing.get("agent_seconds", 0) - span > STALL_IDLE_SECONDS:
            return "api_stall"
        return "guard_cap"
    return "graded"


def summarize(run: Path, pricing: dict) -> dict:
    meta, result = _load(run / "trial.json"), _load(run / "result.json")
    grade, timing = _load(run / "grade.json"), _load(run / "timing.json")
    cost, tokens = cost_and_tokens(result, pricing, meta.get("model"))
    kind = outcome(run, result, timing)
    builds = grade.get("build") or []
    first = builds[0]["seconds"] if builds else None
    wall = round(timing.get("agent_seconds", 0) + timing.get("grader_seconds", 0), 1) if timing else None
    reward = grade.get("reward", 0.0)
    return {
        "run": run.name, "task": meta.get("task"), "mode": meta.get("mode", "agent"), "model": meta.get("model"),
        "outcome": kind,
        "counts_as_model_failure": {"graded": reward < 1.0, "guard_cap": True}.get(kind, False),
        "reward": reward, "checks": f"{grade.get('passed', 0)}/{grade.get('total', 7)}",
        "idempotent": grade.get("idempotent"), "stream_ok": grade.get("stream_ok"), "error": grade.get("error"),
        "tokens": tokens, "cost_usd": format(cost.quantize(Decimal("0.000001")), "f"),
        "num_turns": result.get("num_turns"),
        "agent_seconds": timing.get("agent_seconds"), "grader_seconds": timing.get("grader_seconds"),
        "first_build_seconds": first, "wall_seconds": wall,
        "wall_seconds_without_first_build": round(wall - first, 1) if wall is not None and first is not None else wall,
        "agent_exit": timing.get("agent_exit"),
    }


# --- caps --------------------------------------------------------------------------------------------

RUNNER_MARGIN = 120  # the runner's backstop above the grader's own deadline (the grader reports first)


def caps_from_measurements(grades: list[dict]) -> dict:
    """The grading deadline: the measured worst case of the reference trials plus 50%, rounded up
    (owner default, TASK-81). Each item holds `grader_seconds` from a reference trial's timing.json."""
    seconds = [g["grader_seconds"] for g in grades]
    deadline = math.ceil(1.5 * max(seconds))
    return {"grader_deadline": deadline, "grader_timeout": deadline + RUNNER_MARGIN,
            "measured": {"grader_seconds": seconds, "worst": max(seconds)}}


# --- running -----------------------------------------------------------------------------------------

def run_trial(task: str, out: Path, *, mode: str, model: str | None, plugin_dir: Path | None,
              replay_seed: int, caps: dict) -> int:
    sys.path.insert(0, str(PIPELINE))
    from pipetask import assemble, bundle  # noqa: PLC0415 - builder code, hidden from arms

    task_caps = caps["tasks"][task]
    with tempfile.TemporaryDirectory(prefix=f"hb-{task}-") as tmp:
        tmp_path = Path(tmp)
        repo = assemble.assemble(task, tmp_path / "repo", with_reference=mode == "reference")
        dist = tmp_path / "dist"
        bundle.bundle(dist)
        cmd = [str(RUN_TRIAL), "--repo", str(repo), "--prompt", str(PIPELINE / task / "prompt.md"),
               "--grader", str(dist / "grader.pyz"), "--replay", str(dist / "replay.pyz"),
               "--replay-seed", str(replay_seed), "--out", str(out), "--image", task_caps["image"],
               "--agent-timeout", str(caps["agent_timeout"]),
               "--grader-timeout", str(task_caps["grader_timeout"])]
        grader_args = ["--make-user", "agent", "--make-env-file", "/opt/hb/toolchain.env",
                       "--logs", "/trial/out/grade-logs", "--snapshot-worktree"]
        if "grader_deadline" in task_caps:
            grader_args += ["--deadline", str(task_caps["grader_deadline"])]
        for arg in grader_args:
            cmd += ["--grader-arg", arg]
        env = dict(os.environ)
        if mode == "agent":
            cmd += ["--model", model]
            if plugin_dir:
                cmd += ["--plugin-dir", str(plugin_dir)]
        else:
            stub = tmp_path / "no-agent.sh"
            stub.write_text(NO_AGENT)
            cmd += ["--agent-cmd", str(stub), "--model", "none"]
            env.pop("ANTHROPIC_API_KEY", None)
        meta = {"task": task, "mode": mode, "model": model if mode == "agent" else None,
                "arm": "one-shot" if mode == "agent" and not plugin_dir else (plugin_dir.name if plugin_dir else mode),
                "image": task_caps["image"], "agent_timeout": caps["agent_timeout"],
                "grader_timeout": task_caps["grader_timeout"], "grader_deadline": task_caps.get("grader_deadline"),
                "replay_seed": replay_seed,
                "started_at": datetime.now().astimezone().isoformat(timespec="seconds")}
        rc = subprocess.call(cmd, env=env)
    out.mkdir(parents=True, exist_ok=True)
    (out / "trial.json").write_text(json.dumps(meta, indent=1) + "\n")
    return rc


def table(rows: list[dict]) -> str:
    head = ("| Run | Task | Model / mode | Outcome | Reward | Checks | Tokens in / cache write / cache read / out "
            "| Cost (USD) | Agent s | Grader s | Wall s | Wall s w/o 1st build |")
    lines = [head, "|" + "---|" * 12]
    for r in rows:
        t = r["tokens"]
        lines.append(
            f"| {r['run']} | {r['task']} | {r['model'] or r['mode']} | {r['outcome']} | {r['reward']} | {r['checks']} "
            f"| {t['input']:,} / {t['cache_write']:,} / {t['cache_read']:,} / {t['output']:,} | {r['cost_usd']} "
            f"| {r['agent_seconds']} | {r['grader_seconds']} | {r['wall_seconds']} "
            f"| {r['wall_seconds_without_first_build']} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run one trial")
    r.add_argument("task", choices=["P1", "P2", "P3"])
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--mode", choices=["agent", "reference", "skeleton"], default="agent")
    r.add_argument("--model")
    r.add_argument("--plugin-dir", type=Path)
    r.add_argument("--replay-seed", type=int, default=0, help="the dev replay's seed (the grading seed is 1)")
    c = sub.add_parser("caps", help="set a task's grader caps from its reference trials")
    c.add_argument("task", choices=["P1", "P2", "P3"])
    c.add_argument("runs", type=Path, nargs="+")
    s = sub.add_parser("summary", help="the results table")
    s.add_argument("runs", type=Path, nargs="+")
    s.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    caps = json.loads(CAPS.read_text(encoding="utf-8"))
    if args.cmd == "run":
        if args.mode == "agent" and not args.model:
            ap.error("--model is required for an agent trial")
        return run_trial(args.task, args.out, mode=args.mode, model=args.model, plugin_dir=args.plugin_dir,
                         replay_seed=args.replay_seed, caps=caps)
    if args.cmd == "caps":
        grades = [{**_load(run / "grade.json"), "grader_seconds": _load(run / "timing.json")["grader_seconds"]}
                  for run in args.runs]
        if any(_load(run / "trial.json").get("mode") != "reference" for run in args.runs):
            sys.exit("caps come from reference trials only")
        bad = [run.name for run, g in zip(args.runs, grades) if g.get("reward") != 1.0]
        if bad:
            sys.exit(f"not every reference trial scored 1.0: {bad}")
        caps["tasks"][args.task].update(caps_from_measurements(grades), from_runs=[run.name for run in args.runs])
        CAPS.write_text(json.dumps(caps, indent=1) + "\n", encoding="utf-8")
        print(json.dumps(caps["tasks"][args.task], indent=1))
        return 0
    pricing = json.loads(PRICING.read_text(encoding="utf-8"))
    rows = [summarize(run, pricing) for run in args.runs if (run / "timing.json").exists() or (run / "trial.json").exists()]
    print(table(rows))
    if args.json:
        args.json.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
