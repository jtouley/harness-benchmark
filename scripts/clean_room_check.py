#!/usr/bin/env python3
"""Check that an agent run saw and used only the skills its arm is allowed.

A run is graded only when it ran in a clean room: no user-level skill, rule or command
that its arm did not bring. Global skills are listed to every Claude Code session, and
their descriptions can prime a model ("strict TDD discipline") or be invoked on a wake
word, so a one-shot baseline that can see them is not neutral (criteria v1 section 2).

Input: a Claude Code transcript (JSONL). The check reads three things:

- exposure: `skill_listing` attachments (the names the session was offered), and the
  plain-text form "The following skills are available ...";
- use: `Skill` tool calls;
- contact: any tool input that names a skill, rule or command file
  (`.claude/skills/`, `.cursor/skills/`, `.cursor/rules/`, `.claude/commands/`,
  `.cursor/commands/`, `SKILL.md`, `CLAUDE.md`, `AGENTS.md`).

Verdicts (exit code): clean (0), exposed (1: skills outside the allowlist were listed,
none used), contaminated (2: a skill outside the allowlist was called or a file outside
the allowed paths was touched).

usage: clean_room_check.py TRANSCRIPT [--allow SKILL ...] [--allow-path PREFIX ...] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LISTING_TEXT = re.compile(r"The following skills are available[^\n]*\n((?:\n?- [^\n]+)+)")
LISTING_NAME = re.compile(r"^- ([^:\s]+):", re.M)
CONTACT = re.compile(
    r"(?:\.claude/skills/|\.cursor/skills/|\.cursor/rules/|\.claude/commands/|\.cursor/commands/"
    r"|SKILL\.md|CLAUDE\.md|AGENTS\.md)"
)
PATHLIKE = re.compile(r"[\w~./$-]*(?:\.claude|\.cursor)/[\w./-]*|[\w~./$-]*(?:SKILL|CLAUDE|AGENTS)\.md")


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


def scan(path: Path) -> dict:
    """Listed skill names, Skill calls and file contacts in one transcript."""
    listed: set[str] = set()
    calls: list[str] = []
    contacts: list[str] = []
    for record in _records(path):
        attachment = record.get("attachment")
        if isinstance(attachment, dict) and attachment.get("type") == "skill_listing":
            listed.update(n for n in attachment.get("names") or [] if isinstance(n, str))
        message = record.get("message") if isinstance(record.get("message"), dict) else {}
        for text in _texts(message.get("content")):
            for block in LISTING_TEXT.finditer(text):
                listed.update(LISTING_NAME.findall(block.group(1)))
        if message.get("role") != "assistant":
            continue
        for part in message.get("content") or []:
            if not (isinstance(part, dict) and part.get("type") == "tool_use"):
                continue
            tool_input = part.get("input") if isinstance(part.get("input"), dict) else {}
            if part.get("name") == "Skill":
                calls.append(str(tool_input.get("skill") or ""))
            blob = json.dumps(tool_input)
            if CONTACT.search(blob):
                contacts.extend(PATHLIKE.findall(blob) or [blob[:160]])
    return {"listed": sorted(listed), "skill_calls": calls, "contacts": sorted(set(contacts))}


def verdict(found: dict, allow: set[str], allow_paths: list[str]) -> dict:
    def allowed_skill(name: str) -> bool:
        base = name.split(":")[-1]
        return name in allow or base in allow

    unexpected_listed = [n for n in found["listed"] if not allowed_skill(n)]
    unexpected_calls = [n for n in found["skill_calls"] if not allowed_skill(n)]
    unexpected_contacts = [c for c in found["contacts"] if not any(p in c for p in allow_paths)]
    if unexpected_calls or unexpected_contacts:
        level, code = "contaminated", 2
    elif unexpected_listed:
        level, code = "exposed", 1
    else:
        level, code = "clean", 0
    return {**found, "unexpected_listed": unexpected_listed, "unexpected_calls": unexpected_calls,
            "unexpected_contacts": unexpected_contacts, "verdict": level, "exit": code}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--allow", action="append", default=[], help="a skill the arm brings (repeatable)")
    parser.add_argument("--allow-path", action="append", default=[], help="a path fragment the arm may touch")
    parser.add_argument("--json", action="store_true", help="print the full result as JSON")
    args = parser.parse_args(argv)
    result = verdict(scan(args.transcript), set(args.allow), args.allow_path)
    if args.json:
        print(json.dumps({"transcript": str(args.transcript), **result}, indent=2))
    else:
        print(f"{result['verdict']}: {len(result['unexpected_listed'])} skills listed outside the allowlist, "
              f"{len(result['unexpected_calls'])} calls, {len(result['unexpected_contacts'])} file contacts")
    return result["exit"]


if __name__ == "__main__":
    sys.exit(main())
