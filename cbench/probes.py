"""Tier 2: golden hook probes.

For every framework, host and scenario: reset the sandbox to its pristine
install, write the framework's fixture for the scenario's state, build the hook
payload the host would send for the action, run every matching registered hook
(in registration order, network disabled), and classify the combined decision
with the rules in hookrun.py.
"""

from __future__ import annotations

import re

from .context import Hook, claude_hooks, cursor_hooks, matches
from .hookrun import aggregate, classify, run_hook
from .install import Sandbox, canonicalize_host_text, restore
from .lock import Framework, Lock
from .util import GOLDEN_DIR, cache_dir, load_json, sha256_file

LONG_PLAN = "# Plan\n\n" + "".join(f"- Step {n}: implement part {n} of the feature and test it.\n" for n in range(1, 301))
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
# Homebrew bash warns when C.UTF-8 is missing. Linux bash does not. Verdicts ignore stderr.
_LOCALE_WARN = re.compile(
    r"bash: warning: setlocale: LC_ALL: cannot change locale \([^)]*\): No such file or directory\n?"
)


def _fixture_text(text: str) -> str:
    return LONG_PLAN if text == "@@LONG_PLAN@@" else text


def apply_state(sb: Sandbox, states: dict, common: dict, state: str) -> None:
    files = dict(common.get("every_state", {}))
    files.update(states["states"][state])
    for rel, text in sorted(files.items()):
        path = sb.proj / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_fixture_text(text), encoding="utf-8")


def resolve_action(action: dict, targets: dict) -> dict | None:
    """Turn a scenario action into a concrete one for this framework (None = n/a)."""
    if action["kind"] != "write" or "target" not in action:
        return action
    target = targets.get(action["target"])
    if target is None:
        return None
    if isinstance(target, str):
        return {"kind": "write", "path": target, "content": action.get("content", "")}
    return {"kind": "write", "path": target["path"], "content": target["content"]}


def payloads(host: str, action: dict, sb: Sandbox) -> list[tuple[str, str | None, dict]]:
    """(event, tool_name, payload) tuples the host emits for this action."""
    base_cc = {"session_id": "cbench", "transcript_path": "/dev/null", "cwd": str(sb.proj)}
    abspath = str(sb.proj / action["path"]) if "path" in action else None
    kind = action["kind"]
    if host == "claude-code":
        if kind == "write":
            return [("PreToolUse", "Write", {**base_cc, "hook_event_name": "PreToolUse", "tool_name": "Write",
                                             "tool_input": {"file_path": abspath, "content": action["content"]}})]
        if kind == "shell":
            return [("PreToolUse", "Bash", {**base_cc, "hook_event_name": "PreToolUse", "tool_name": "Bash",
                                            "tool_input": {"command": action["command"]}})]
        if kind == "read":
            return [("PreToolUse", "Read", {**base_cc, "hook_event_name": "PreToolUse", "tool_name": "Read",
                                            "tool_input": {"file_path": abspath}})]
        if kind == "stop":
            return [("Stop", None, {**base_cc, "hook_event_name": "Stop", "stop_hook_active": False})]
    else:
        base_cu = {"conversation_id": "cbench", "generation_id": "cbench", "workspace_roots": [str(sb.proj)]}
        if kind == "write":
            return [("preToolUse", "Write", {**base_cu, "hook_event_name": "preToolUse", "tool_name": "Write",
                                             "tool_input": {"path": abspath, "contents": action["content"]}})]
        if kind == "shell":
            return [
                ("preToolUse", "Shell", {**base_cu, "hook_event_name": "preToolUse", "tool_name": "Shell",
                                         "tool_input": {"command": action["command"]}}),
                ("beforeShellExecution", None, {**base_cu, "hook_event_name": "beforeShellExecution",
                                                "command": action["command"], "cwd": str(sb.proj)}),
            ]
        if kind == "read":
            return [
                ("preToolUse", "Read", {**base_cu, "hook_event_name": "preToolUse", "tool_name": "Read",
                                        "tool_input": {"path": abspath}}),
                ("beforeReadFile", None, {**base_cu, "hook_event_name": "beforeReadFile", "file_path": abspath}),
            ]
        if kind == "stop":
            return [("stop", None, {**base_cu, "hook_event_name": "stop", "status": "completed", "loop_count": 0})]
    raise ValueError(f"unknown action kind {kind!r}")


def _clean(text: str, sb: Sandbox, limit: int) -> str:
    """Strip colors and machine-specific paths so evidence is identical on every machine."""
    text = canonicalize_host_text(_ANSI.sub("", text))
    text = text.replace(str(sb.root), "<ROOT>").replace(str(cache_dir()), "<CACHE>")
    text = _LOCALE_WARN.sub("", text).strip()
    return text[:limit]


def _short(command: str, sb: Sandbox) -> str:
    names = re.findall(r"[\w.-]+\.(?:py|js|cjs|sh|cmd)\b", command)
    return names[-1] if names else _clean(command, sb, 80)


def run_scenario(fw: Framework, lock: Lock, host: str, scenario: dict, states: dict, common: dict) -> dict:
    action = resolve_action(scenario["action"], states["targets"])
    if action is None:
        return {"verdict": "n/a", "reason": "framework has no artifact for this target", "hooks": []}
    sb = restore(fw, lock)
    apply_state(sb, states, common, scenario["state"])
    hooks: list[Hook] = claude_hooks(sb) if host == "claude-code" else cursor_hooks(sb)
    evidence, verdicts = [], []
    for event, tool, payload in payloads(host, action, sb):
        for hook in hooks:
            if hook.event != event or not matches(hook, tool):
                continue
            result = run_hook(hook, sb, payload)
            verdict, via = classify(hook, result)
            verdicts.append(verdict)
            evidence.append({
                "event": event,
                "hook": _short(hook.command, sb),
                "origin": hook.origin,
                "exit": result["exit"],
                "verdict": verdict,
                "via": via,
                "stdout": _clean(result["stdout"], sb, 300),
                "stderr": _clean(result["stderr"], sb, 200),
            })
    return {"verdict": aggregate(verdicts), "hooks": evidence}


def scores(verdict: str, intent: str) -> bool | None:
    if verdict == "n/a" or intent == "informational":
        return None
    if intent == "block":
        return verdict == "block"
    return verdict in ("allow", "advise", "no_hook", "error")


def run_all(lock: Lock, fws: list[Framework]) -> dict:
    scen_path = GOLDEN_DIR / "probes" / "scenarios.json"
    state_path = GOLDEN_DIR / "probes" / "states.json"
    scenarios = load_json(scen_path)["scenarios"]
    states_doc = load_json(state_path)
    out: dict = {
        "golden": {"scenarios_sha256": sha256_file(scen_path), "states_sha256": sha256_file(state_path)},
        "frameworks": {},
    }
    for fw in fws:
        states = states_doc["frameworks"][fw.name]
        sb = restore(fw, lock)
        hosts = {"claude-code": len(claude_hooks(sb)), "cursor": len(cursor_hooks(sb))}
        fw_out = {"registered_hooks": hosts, "hosts": {}}
        for host, count in hosts.items():
            if host == "cursor" and count == 0:
                continue
            rows = {}
            for scenario in scenarios:
                res = run_scenario(fw, lock, host, scenario, states, states_doc["common"])
                res["intent"] = scenario["intent"]
                res["meets_intent"] = scores(res["verdict"], scenario["intent"])
                rows[scenario["id"]] = res
            scored = [r["meets_intent"] for r in rows.values() if r["meets_intent"] is not None]
            fw_out["hosts"][host] = {
                "scenarios": rows,
                "score": {"met": sum(1 for s in scored if s), "scored": len(scored)},
            }
        out["frameworks"][fw.name] = fw_out
    out["scenario_index"] = {s["id"]: {"slug": s["slug"], "title": s["title"], "intent": s["intent"]} for s in scenarios}
    return out
