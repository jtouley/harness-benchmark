#!/usr/bin/env python3
"""Check that an agent run saw and used only the skills its arm is allowed.

A run is graded only when it ran in a clean room: no user-level skill, rule, command or
memory that its arm did not bring. Every Claude Code session is shown a list of skills,
and their descriptions can prime a model ("strict TDD discipline") or be invoked on a
wake word, so a one-shot baseline that can see them is not neutral (criteria v1 section 2).

Input: a run's transcripts. Give the run agent's transcript, and either the other
transcripts of the run or `--agents-dir DIR` with the run agent's id: then every nested
agent the run spawned (found through `parentAgentId` in `agent-*.meta.json`) is read
too. Nested peers are where a user-level skill can stand in for a harness's own.

The check reads three things in every transcript:

- exposure: `skill_listing` attachments, and the plain-text form "The following skills
  are available ...";
- use: `Skill` tool calls;
- contact: a path field of a tool call (file_path, path, pattern, notebook_path) or a
  shell command that names a skill, rule, command, plugin or memory location. Text that
  a tool writes (content, new_string) is not a contact.

Skills the host always lists (scripts/clean_room_builtin_skills.json) are allowed for
every arm. Allowed paths match by whole path components.

Verdicts (exit code): clean (0), exposed (1: skills outside the allowlist were listed,
none used), contaminated (2: a skill outside the allowlist was called, or a location
outside the allowed paths was touched), unassessable (3: no transcript records, or no
skill listing at all, so the check cannot tell what the run was offered).

usage: clean_room_check.py TRANSCRIPT [TRANSCRIPT ...] [--agents-dir DIR --agent ID]
       [--allow SKILL ...] [--allow-path PATH ...] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BUILTIN = Path(__file__).with_name("clean_room_builtin_skills.json")
LISTING_BLOCK = re.compile(r"The following skills are available[^\n]*\n(.*?)(?:</system-reminder>|\Z)", re.S)
LISTING_NAME = re.compile(r"^- ([^:\s]+(?::[^:\s]+)?):", re.M)
LOCATION = re.compile(
    r"\.(?:claude|cursor)/(?:skills|rules|commands|plugins|agents)(?:/|$|(?=[\s'\"]))"
    r"|\.claude/projects/[^/\s]+/memory(?:/|$)"
    r"|(?:^|/)(?:SKILL|CLAUDE|AGENTS|MEMORY)\.md\b"
)
PATH_FIELDS = ("file_path", "path", "pattern", "notebook_path")
TOKEN = re.compile(r"[^\s'\";|&<>()]+")


def builtin_skills() -> set[str]:
    data = json.loads(BUILTIN.read_text(encoding="utf-8"))
    return set(data["claude_code"]) | set(data["claude_ai_account"])


def run_transcripts(agents_dir: Path, agent: str) -> list[Path]:
    """The agent's transcript and those of every agent it spawned, at any depth."""
    children: dict[str, list[str]] = {}
    for meta in agents_dir.glob("agent-*.meta.json"):
        try:
            parent = json.loads(meta.read_text(encoding="utf-8")).get("parentAgentId")
        except (OSError, json.JSONDecodeError):
            continue
        if parent:
            children.setdefault(parent, []).append(meta.name[len("agent-"):-len(".meta.json")])
    out, todo = [], [agent]
    while todo:
        current = todo.pop()
        path = agents_dir / f"agent-{current}.jsonl"
        if path.is_file():
            out.append(path)
        todo.extend(children.get(current, []))
    return out


def _records(path: Path):
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            yield record


def _texts(content):
    if isinstance(content, str):
        yield content
    elif isinstance(content, list):
        for part in content:
            if isinstance(part, dict):
                if isinstance(part.get("text"), str):
                    yield part["text"]
                if isinstance(part.get("content"), (str, list)):
                    yield from _texts(part["content"])


def _locations(tool_input: dict) -> list[str]:
    """Skill, rule, command, plugin or memory locations a tool call reads or runs on."""
    found = []
    for field in PATH_FIELDS:
        value = tool_input.get(field)
        if isinstance(value, str) and LOCATION.search(value):
            found.append(value)
    command = tool_input.get("command")
    if isinstance(command, str):
        found.extend(t for t in TOKEN.findall(command) if LOCATION.search(t))
    return found


def scan(paths: list[Path]) -> dict:
    """Listed skill names, Skill calls and locations touched, over all transcripts of a run."""
    listed: set[str] = set()
    calls: list[str] = []
    contacts: set[str] = set()
    records = 0
    saw_listing = False
    for path in paths:
        for record in _records(path):
            records += 1
            attachment = record.get("attachment")
            if isinstance(attachment, dict) and attachment.get("type") == "skill_listing":
                saw_listing = True
                listed.update(n for n in attachment.get("names") or [] if isinstance(n, str))
            message = record.get("message") if isinstance(record.get("message"), dict) else {}
            for text in _texts(message.get("content")):
                for block in LISTING_BLOCK.finditer(text):
                    saw_listing = True
                    listed.update(LISTING_NAME.findall(block.group(1)))
            if message.get("role") != "assistant":
                continue
            for part in message.get("content") or []:
                if not (isinstance(part, dict) and part.get("type") == "tool_use"):
                    continue
                tool_input = part.get("input") if isinstance(part.get("input"), dict) else {}
                if part.get("name") == "Skill":
                    calls.append(str(tool_input.get("skill") or ""))
                contacts.update(_locations(tool_input))
    return {"transcripts": len(paths), "records": records, "saw_listing": saw_listing,
            "listed": sorted(listed), "skill_calls": calls, "contacts": sorted(contacts)}


def _components(path: str) -> list[str]:
    return [c for c in path.replace("\\", "/").split("/") if c and c != "."]


def path_allowed(contact: str, allow_paths: list[str]) -> bool:
    """True when an allowed path's components appear, in order and whole, inside the contact."""
    parts = _components(contact)
    for allowed in allow_paths:
        want = _components(allowed)
        if want and any(parts[i:i + len(want)] == want for i in range(len(parts) - len(want) + 1)):
            return True
    return False


def verdict(found: dict, allow: set[str], allow_paths: list[str]) -> dict:
    allowed_names = allow | builtin_skills()
    unexpected_listed = [n for n in found["listed"] if n not in allowed_names]
    unexpected_calls = [n for n in found["skill_calls"] if n not in allowed_names]
    unexpected_contacts = [c for c in found["contacts"] if not path_allowed(c, allow_paths)]
    if not found["records"] or not found["saw_listing"]:
        level, code = "unassessable", 3
    elif unexpected_calls or unexpected_contacts:
        level, code = "contaminated", 2
    elif unexpected_listed:
        level, code = "exposed", 1
    else:
        level, code = "clean", 0
    return {**found, "unexpected_listed": unexpected_listed, "unexpected_calls": unexpected_calls,
            "unexpected_contacts": unexpected_contacts, "verdict": level, "exit": code}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("transcripts", type=Path, nargs="*")
    parser.add_argument("--agents-dir", type=Path, help="folder of agent-*.jsonl and agent-*.meta.json")
    parser.add_argument("--agent", help="the run agent's id; its nested agents are read too")
    parser.add_argument("--allow", action="append", default=[], help="a skill the arm brings (exact name, repeatable)")
    parser.add_argument("--allow-path", action="append", default=[], help="a path the arm may touch (whole components)")
    parser.add_argument("--json", action="store_true", help="print the full result as JSON")
    args = parser.parse_args(argv)
    paths = list(args.transcripts)
    if args.agents_dir and args.agent:
        paths += run_transcripts(args.agents_dir, args.agent)
    result = verdict(scan(paths), set(args.allow), args.allow_path)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['verdict']}: {result['transcripts']} transcripts, {len(result['unexpected_listed'])} skills listed "
              f"outside the allowlist, {len(result['unexpected_calls'])} calls, {len(result['unexpected_contacts'])} contacts")
    return result["exit"]


if __name__ == "__main__":
    sys.exit(main())
