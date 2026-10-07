"""Run a registered hook against a payload and classify its decision.

Interpretation rules are explicit and per host, so a verdict can be traced to a rule:

claude-code (Claude Code hooks reference):
  exit 2                                  -> block
  exit 0 + JSON continue:false            -> block
  exit 0 + JSON decision:"block"          -> block
  exit 0 + hookSpecificOutput.permissionDecision deny|ask|allow -> block|ask|allow
  exit 0 + additionalContext/systemMessage/reason -> advise
  exit 0 otherwise                        -> allow
  any other exit                          -> error (non-blocking)

cursor (Cursor hooks reference):
  exit 2                                  -> block (same as permission:"deny")
  exit 0 + JSON permission deny|ask       -> block|ask
  exit 0 + JSON followup_message (stop)   -> block (agent is sent back to work)
  exit 0 + unparseable JSON, failClosed   -> block
  any other exit: failClosed -> block, else error (action proceeds)
"""

from __future__ import annotations

import json
import subprocess

from .context import Hook
from .install import Sandbox
from .util import clean_env

RANK = {"no_hook": 0, "allow": 1, "error": 2, "advise": 3, "ask": 4, "block": 5}


def run_hook(hook: Hook, sb: Sandbox, payload: dict, timeout: int = 60) -> dict:
    env = clean_env(
        home=sb.home,
        extra={
            "CLAUDE_PROJECT_DIR": str(sb.proj),
            "CURSOR_PROJECT_DIR": str(sb.proj),
            **hook.env,
        },
    )
    try:
        proc = subprocess.run(
            ["bash", "-c", hook.command], cwd=str(sb.proj), env=env,
            input=json.dumps(payload), capture_output=True, text=True, timeout=timeout,
        )
        code, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        code, out, err = -9, "", "timeout"
    return {"exit": code, "stdout": out, "stderr": err}


def _json(text: str):
    text = text.strip()
    if not text:
        return None
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return "invalid"
    return value if isinstance(value, dict) else "invalid"


def classify(hook: Hook, result: dict) -> tuple[str, str]:
    """Return (verdict, via). `via` names the rule that produced the verdict."""
    code, data = result["exit"], _json(result["stdout"])
    if hook.host == "claude-code":
        if code == 2:
            return "block", "exit-2"
        if code != 0:
            return "error", f"exit-{code}"
        if isinstance(data, dict):
            if data.get("continue") is False:
                return "block", "continue-false"
            if data.get("decision") == "block":
                return "block", "decision-block"
            hso = data.get("hookSpecificOutput") or {}
            decision = hso.get("permissionDecision")
            if decision == "deny":
                return "block", "permission-deny"
            if decision == "ask":
                return "ask", "permission-ask"
            if hso.get("additionalContext") or data.get("systemMessage") or data.get("reason"):
                return "advise", "context"
        return "allow", "default"
    # cursor
    if code == 2:
        return "block", "exit-2"
    if code != 0:
        return ("block", "fail-closed:exit") if hook.fail_closed else ("error", f"exit-{code}")
    if data == "invalid":
        return ("block", "fail-closed:invalid-json") if hook.fail_closed else ("error", "invalid-json")
    if isinstance(data, dict):
        perm = data.get("permission")
        if perm == "deny":
            return "block", "permission-deny"
        if perm == "ask":
            return "ask", "permission-ask"
        if data.get("followup_message"):
            return "block", "followup-message"
        if data.get("agent_message") or data.get("user_message") or data.get("additional_context"):
            return "advise", "message"
    return "allow", "default"


def aggregate(verdicts: list[str]) -> str:
    if not verdicts:
        return "no_hook"
    return max(verdicts, key=lambda v: RANK[v])


def session_context(hook: Hook, result: dict) -> str:
    """Text a SessionStart hook adds to the model's context (Claude Code semantics)."""
    if result["exit"] != 0:
        return ""
    data = _json(result["stdout"])
    if isinstance(data, dict):
        hso = data.get("hookSpecificOutput") or {}
        return hso.get("additionalContext") or data.get("additionalContext") or data.get("additional_context") or ""
    if data is None:
        return ""
    return result["stdout"].strip()
