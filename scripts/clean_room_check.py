#!/usr/bin/env python3
"""Check that an agent run saw and used only the skills its arm is allowed.

A run is graded only when it ran in a clean room: no user-level skill, rule, command or
memory that its arm did not bring. Every Claude Code session is shown a list of skills,
and their descriptions can prime a model ("strict TDD discipline") or be invoked on a
wake word, so a one-shot baseline that can see them is not neutral (criteria v1 section 2).

Input: a run's transcripts. For a top-level session, give `<session>.jsonl`: the agents
in `<session>/subagents/` are read too. For a run that is itself a subagent, give
`--agents-dir DIR` with the run agent's id: every agent it spawned (found through
`parentAgentId` in `agent-*.meta.json`) is read too. Nested peers are where a user-level
skill can stand in for a harness's own.

The check reads three things in every transcript:

- exposure: `skill_listing` attachments, the plain-text form "The following skills
  are available ...", and subagent types in `agent_listing_delta` that the host does
  not build in;
- use: `Skill` tool calls, and `Task`/`Agent` calls with a subagent type that the host
  does not build in (a user-level or plugin agent runs a user-level prompt);
- contact: a path field of a tool call (file_path, path, notebook_path, and Glob's
  path joined with its pattern) or a shell command token that names a host config
  directory (.claude, .cursor, .codex, .agents) or an instruction file (SKILL, CLAUDE,
  AGENTS, MEMORY .md); and every instruction file the host loads into the session
  (`instructions` attachments, "Contents of <path>" text). Text that a tool writes
  (content, new_string) is not a contact.

Skills and agent types the host always lists (scripts/clean_room_builtin_skills.json)
may appear in the listing of any arm. Calling a built-in skill needs `--allow` like any
other skill; spawning a built-in agent type does not. `--allow-path` values must be
absolute. A contact is allowed only when its normalised path lies under one of them. A
relative path resolves against `--cwd`, except in a shell command that changes
directory, where the cwd is unknown and the path is never allowed.

The check reads Claude Code transcripts only. A transcript of another host has no skill
listing, so it is unassessable.

Verdicts (exit code): clean (0), exposed (1: skills outside the allowlist were listed,
none used), contaminated (2: a skill outside the allowlist was called, or a location
outside the allowed paths was touched), unassessable (3: no transcript records, or no
skill listing at all, so the check cannot tell what the run was offered).

usage: clean_room_check.py TRANSCRIPT [TRANSCRIPT ...] [--agents-dir DIR --agent ID]
       [--allow SKILL ...] [--allow-path PATH ...] [--cwd DIR] [--json]
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
from pathlib import Path

BUILTIN = Path(__file__).with_name("clean_room_builtin_skills.json")
LISTING_BLOCK = re.compile(r"The following skills are available[^\n]*\n(.*?)(?:</system-reminder>|\Z)", re.S)
LISTING_NAME = re.compile(r"^- ([^:\s]+(?::[^:\s]+)*)(?::|[ \t]*$)", re.M)
LOCATION = re.compile(
    r"(?:^|/)\.(?:claude|cursor|codex|agents)(?:/|$|(?=[\s'\"]))"
    r"|(?:^|/)(?:SKILL|CLAUDE|AGENTS|MEMORY)\.md\b"
)
PATH_FIELDS = ("file_path", "path", "notebook_path")  # Grep's `pattern` is a regex, not a path
TOKEN = re.compile(r"[^\s'\";|&<>()]+")
CHANGES_DIR = re.compile(r"(?:^|[\s;&|(])(?:cd|pushd)(?:\s|$)")
LOADED_FILE = re.compile(r"Contents of (\S+?\.md)\b")
AGENT_TOOLS = ("Task", "Agent")
SAVED_OUTPUT = re.compile(r"\.claude/projects/[^/]+/[^/]+/tool-results/[^/]+$")  # the session's own large tool outputs


def builtin_skills() -> set[str]:
    data = json.loads(BUILTIN.read_text(encoding="utf-8"))
    return set(data["claude_code"]) | set(data["claude_ai_account"])


def builtin_agents() -> set[str]:
    return set(json.loads(BUILTIN.read_text(encoding="utf-8"))["claude_code_agents"])


def session_agents(transcript: Path) -> list[Path]:
    """Agents of a top-level session: `<session>.jsonl` keeps them in `<session>/subagents/`.

    Direct peers of a top-level session carry no parentAgentId, so they are found here.
    """
    folder = transcript.with_suffix("") / "subagents"
    return sorted(folder.glob("agent-*.jsonl")) if folder.is_dir() else []


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


def _resolve(path: str, cwd: str | None) -> str:
    """An absolute path is normalised, so `..` cannot climb out of an allowed folder.

    A relative path names a file under the run's cwd. Without a cwd it stays relative,
    and a relative path is never allowed. `~` and `$` paths stay as they are.
    """
    if path.startswith("/"):
        return posixpath.normpath(path)
    if cwd is None or path.startswith(("~", "$")):
        return path
    return posixpath.normpath(f"{cwd.rstrip('/')}/{path}")


def _locations(tool_name: str, tool_input: dict, cwd: str | None = None) -> list[str]:
    """Host config and instruction-file locations a tool call reads or runs on."""
    values = [tool_input.get(field) for field in PATH_FIELDS]
    if tool_name == "Glob" and isinstance(tool_input.get("pattern"), str):
        values.append(posixpath.join(tool_input.get("path") or "", tool_input["pattern"]))
    found = [_resolve(v, cwd) for v in values if _is_location(v)]
    command = tool_input.get("command")
    return found + (_command_locations(command, cwd) if isinstance(command, str) else [])


def _command_locations(command: str, cwd: str | None) -> list[str]:
    # After a cd the shell's directory is unknown, so a relative token stays unresolved.
    base = None if CHANGES_DIR.search(command) else cwd
    return [_resolve(t, base) for t in TOKEN.findall(command) if _is_location(t)]


def _is_location(value) -> bool:
    return isinstance(value, str) and bool(LOCATION.search(value)) and not SAVED_OUTPUT.search(value)


def _loaded_files(attachment: dict) -> list[str]:
    """Instruction files the host loaded into the session (CLAUDE.md, AGENTS.md, memory)."""
    if attachment.get("type") != "instructions":
        return []
    return [f["path"] for f in attachment.get("files") or [] if isinstance(f, dict) and isinstance(f.get("path"), str)]


def _user_level_agents(listing: dict) -> list[str]:
    built_in = set(listing.get("builtInTypes") or []) | builtin_agents()
    return [n for n in listing.get("addedTypes") or [] if isinstance(n, str) and n not in built_in]


class _Run:
    """What one run was offered and what it did, gathered record by record."""

    def __init__(self, cwd: str | None):
        self.cwd = cwd
        self.listed: set[str] = set()
        self.calls: list[str] = []
        self.agent_calls: list[str] = []
        self.contacts: set[str] = set()
        self.records = 0
        self.saw_listing = False

    def read(self, record: dict) -> None:
        self.records += 1
        attachment = record.get("attachment") if isinstance(record.get("attachment"), dict) else {}
        self._attachment(attachment)
        message = record.get("message") if isinstance(record.get("message"), dict) else {}
        for text in _texts(message.get("content")):
            self._text(text)
        if message.get("role") == "assistant":
            for part in message.get("content") or []:
                if isinstance(part, dict) and part.get("type") == "tool_use":
                    self._tool_use(str(part.get("name")), part.get("input") if isinstance(part.get("input"), dict) else {})

    def _attachment(self, attachment: dict) -> None:
        kind = attachment.get("type")
        if kind == "skill_listing":
            self.saw_listing = True
            self.listed.update(n for n in attachment.get("names") or [] if isinstance(n, str))
        elif kind == "agent_listing_delta":
            self.listed.update(_user_level_agents(attachment))
        self.contacts.update(_resolve(p, self.cwd) for p in _loaded_files(attachment))

    def _text(self, text: str) -> None:
        for block in LISTING_BLOCK.finditer(text):
            self.saw_listing = True
            self.listed.update(LISTING_NAME.findall(block.group(1)))
        self.contacts.update(_resolve(p, self.cwd) for p in LOADED_FILE.findall(text) if LOCATION.search(p))

    def _tool_use(self, name: str, tool_input: dict) -> None:
        if name == "Skill":
            self.calls.append(str(tool_input.get("skill") or ""))
        if name in AGENT_TOOLS and tool_input.get("subagent_type"):
            self.agent_calls.append(str(tool_input["subagent_type"]))
        self.contacts.update(_locations(name, tool_input, self.cwd))


def scan(paths: list[Path], cwd: str | None = None) -> dict:
    """Listed skill names, Skill and agent calls and locations touched, over all transcripts of a run.

    With `cwd`, a relative path in a tool call is read as a file under the run's working
    directory, so `--allow-path` can allow the task repo's own CLAUDE.md or AGENTS.md.
    """
    run = _Run(cwd)
    for path in paths:
        for record in _records(path):
            run.read(record)
    return {"transcripts": len(paths), "records": run.records, "saw_listing": run.saw_listing,
            "listed": sorted(run.listed), "skill_calls": run.calls, "agent_calls": run.agent_calls,
            "contacts": sorted(run.contacts)}


def path_allowed(contact: str, allow_paths: list[str]) -> bool:
    """True when the contact is an absolute path at or under an allowed folder."""
    if not contact.startswith("/"):
        return False
    contact = posixpath.normpath(contact)
    for allowed in allow_paths:
        root = posixpath.normpath(allowed)
        if contact == root or contact.startswith(root.rstrip("/") + "/"):
            return True
    return False


def _require_absolute(allow_paths: list[str]) -> None:
    relative = [p for p in allow_paths if not p.startswith("/")]
    if relative:
        raise ValueError(f"--allow-path must be absolute: {relative}")


def _unexpected(found: dict, allow: set[str], allow_paths: list[str]) -> tuple[list, list, list]:
    # Built-in skills may be listed (no clean room can remove them), but calling one is use:
    # a call is clean only when the arm's own allowlist names it. Built-in agent types may be spawned.
    listed = [n for n in found["listed"] if n not in allow | builtin_skills()]
    calls = [n for n in found["skill_calls"] if n not in allow]
    calls += [n for n in found.get("agent_calls", []) if n not in allow | builtin_agents()]
    contacts = [c for c in found["contacts"] if not path_allowed(c, allow_paths)]
    return listed, calls, contacts


def verdict(found: dict, allow: set[str], allow_paths: list[str]) -> dict:
    _require_absolute(allow_paths)
    unexpected_listed, unexpected_calls, unexpected_contacts = _unexpected(found, allow, allow_paths)
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
    parser.add_argument("--allow-path", action="append", default=[], help="an absolute folder the arm may touch")
    parser.add_argument("--cwd", help="the run's working directory: relative paths in tool calls resolve against it")
    parser.add_argument("--json", action="store_true", help="print the full result as JSON")
    args = parser.parse_args(argv)
    if any(not p.startswith("/") for p in args.allow_path):
        parser.error("--allow-path must be absolute")
    paths = list(args.transcripts)
    for transcript in args.transcripts:
        paths += session_agents(transcript)
    if args.agents_dir and args.agent:
        paths += run_transcripts(args.agents_dir, args.agent)
    result = verdict(scan(paths, args.cwd), set(args.allow), args.allow_path)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['verdict']}: {result['transcripts']} transcripts, {len(result['unexpected_listed'])} skills listed "
              f"outside the allowlist, {len(result['unexpected_calls'])} calls, {len(result['unexpected_contacts'])} contacts")
    return result["exit"]


if __name__ == "__main__":
    sys.exit(main())
