"""Tier 1: static context footprint, in tokens and dollars.

Three measures per framework, each fully determined by the pinned install:

always_on   Paid on every request: the skill/command/agent listing
            ("- name: description"), text injected by SessionStart hooks, and
            CLAUDE.md memory files the installer wrote.
corpus      Every context-eligible body (SKILL.md, command, agent, memory).
workflow    The framework's documented plan-to-code path, step by step.
            lower = the step's own file only;
            upper = lower plus its @file references (recursive) and every other
            text file in the skill package. Live runs (tier 3) show where real
            sessions land between the two.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

from . import tokens
from .context import Item, claude_hooks, discover, expand_at_refs, find, package_text
from .hookrun import run_hook, session_context
from .install import Sandbox, fingerprint, normalizer, read_text, restore
from .lock import Framework, Lock
from .util import load_json, sha256_text

MILLION = Decimal(1_000_000)
CENTI_MICRO = Decimal("0.000001")


def listing_line(item: Item) -> str:
    return f"- {item.name}: {item.description}\n"


def _usd(tokens_n: int, per_million: str) -> Decimal:
    return (Decimal(tokens_n) * Decimal(per_million) / MILLION).quantize(CENTI_MICRO, rounding=ROUND_HALF_EVEN)


def cadence_steps(fw: Framework) -> list[str]:
    stages = load_json(fw.src / "stages.json")["stages"]
    peers = {p["slash"]: p for p in load_json(fw.src / "references" / "bundled-peers.json")["peers"]}
    # Default path: the orchestrator skill, then every slash-command stage whose
    # trigger is "always" (conditional stages such as P4 plan-update are skipped).
    steps = ["skill:cadence"]
    for stage in stages:
        cmd = stage.get("command", "")
        if not cmd.startswith("/") or stage.get("trigger", "always") != "always":
            continue
        slash = cmd.split()[0]
        peer = peers.get(slash)
        if peer is None:
            raise LookupError(f"cadence stage {stage['block']} uses {slash}, not in bundled-peers.json")
        steps.append(f"{peer['kind']}:{slash.lstrip('/')}")
    return steps


def workflow_steps(fw: Framework) -> list[str]:
    if fw.workflow.get("derive") == "cadence-stages":
        return cadence_steps(fw)
    return list(fw.workflow.get("steps", []))


def run_session_start(sb: Sandbox) -> list[dict]:
    rows = []
    payload = {"session_id": "cbench", "transcript_path": "/dev/null", "cwd": str(sb.proj),
               "hook_event_name": "SessionStart", "source": "startup"}
    for hook in claude_hooks(sb):
        if hook.event != "SessionStart":
            continue
        result = run_hook(hook, sb, payload, timeout=30)
        text = session_context(hook, result)
        rows.append({
            "origin": hook.origin,
            "command": hook.command.replace(str(sb.root), "<ROOT>"),
            "exit": result["exit"],
            "context_sha256": sha256_text(text),
            "tokens": tokens.count(text),
        })
    return rows


def measure(fw: Framework, lock: Lock, pricing: dict) -> dict:
    sb = restore(fw, lock)
    fp = fingerprint(sb, lock)
    norm = normalizer(lock)
    items = discover(sb)
    listed = [i for i in items if i.kind in ("skill", "command", "agent")]
    memory = [i for i in items if i.kind == "memory"]

    listing_tokens = tokens.count("".join(listing_line(i) for i in listed))
    memory_tokens = 0
    for item in memory:
        text, _ = expand_at_refs(norm(read_text(item.path) or ""), sb, item.path.parent)
        memory_tokens += tokens.count(text)
    session = run_session_start(sb)
    session_tokens = sum(r["tokens"] for r in session)
    always_on = listing_tokens + memory_tokens + session_tokens

    corpus = sum(tokens.count(norm(read_text(i.path) or "")) for i in items)

    steps_out = []
    for ref in workflow_steps(fw):
        item = find(items, ref)
        body = norm(read_text(item.path) or "")
        lower = tokens.count(body)
        expanded, included = expand_at_refs(body, sb, item.path.parent)
        extra = tokens.count(expanded) - lower
        if item.root is not None:
            extra += sum(tokens.count(norm(t)) for p, t in package_text(item, sb)
                         if p != f"{item.root.name}/SKILL.md")
        steps_out.append({
            "ref": ref,
            "resolved_name": item.name,
            "origin": item.origin,
            "lower_tokens": lower,
            "upper_tokens": lower + extra,
            "at_includes": len(included),
        })
    lower_total = sum(s["lower_tokens"] for s in steps_out)
    upper_total = sum(s["upper_tokens"] for s in steps_out)

    cost = {}
    for model, p in sorted(pricing["models"].items()):
        cost[model] = {
            "always_on_per_request_uncached": _usd(always_on, p["input"]),
            "always_on_per_request_cache_read": _usd(always_on, p["cache_read"]),
            "always_on_100_requests_cached": _usd(always_on, p["cache_write_5m"]) + _usd(always_on * 99, p["cache_read"]),
            "workflow_load_lower": _usd(lower_total, p["input"]),
            "workflow_load_upper": _usd(upper_total, p["input"]),
        }

    counts = {}
    for item in items:
        counts[item.kind] = counts.get(item.kind, 0) + 1
    hooks = {}
    for h in claude_hooks(sb):
        hooks[h.event] = hooks.get(h.event, 0) + 1

    return {
        "framework": fw.name,
        "title": fw.title,
        "sha": fw.sha,
        "install": fp,
        "items": counts,
        "claude_code_hooks": hooks,
        "always_on": {
            "listing_tokens": listing_tokens,
            "memory_tokens": memory_tokens,
            "session_start_tokens": session_tokens,
            "total_tokens": always_on,
            "session_start": session,
        },
        "corpus_tokens": corpus,
        "workflow": {
            "source": fw.workflow.get("source", ""),
            "steps": steps_out,
            "lower_tokens": lower_total,
            "upper_tokens": upper_total,
        },
        "cost_usd": cost,
    }
