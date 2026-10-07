"""What Claude Code would load from an installed sandbox.

Discovery follows Claude Code's documented locations: user and project
``.claude/{skills,commands,agents}``, ``CLAUDE.md`` memory files, hooks from
``settings.json`` / ``settings.local.json``, and the same trees inside each
``--plugin-dir``. Cursor hooks (``.cursor/hooks.json``) are read separately
for the Cursor host probes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .install import Sandbox, iter_files, read_text


@dataclass(frozen=True)
class Item:
    kind: str          # skill | command | agent | memory
    name: str          # how a user invokes it (plugin items are "plugin:name")
    description: str
    path: Path         # file loaded when the item is used
    root: Path | None  # skill package directory (skills only)
    origin: str        # user | project | plugin:<name>


@dataclass(frozen=True)
class Hook:
    host: str          # claude-code | cursor
    event: str
    matcher: str | None
    command: str
    origin: str        # file the hook was registered in
    env: dict = field(default_factory=dict)
    fail_closed: bool = False


_FM = re.compile(r"\A---\s*\n(.*?)\n---\s*(\n|\Z)", re.S)


def frontmatter(text: str) -> dict[str, str]:
    """Minimal YAML front-matter reader for flat string keys (incl. folded/literal blocks)."""
    match = _FM.match(text)
    if not match:
        return {}
    out: dict[str, str] = {}
    key = None
    style = None
    buf: list[str] = []

    def flush():
        if key is None:
            return
        if style == "|":
            value = "\n".join(buf).strip()
        else:
            value = " ".join(s.strip() for s in buf if s.strip())
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        out[key] = value

    for line in match.group(1).splitlines():
        top = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if top and not line.startswith((" ", "\t")):
            flush()
            key, rest = top.group(1), top.group(2)
            if rest in ("|", "|-", "|+", ">", ">-", ">+"):
                style, buf = rest[0], []
            else:
                style, buf = None, [rest]
        elif key is not None:
            buf.append(line)
    flush()
    return out


def _body(path: Path) -> str:
    return read_text(path) or ""


def _skill_items(base: Path, origin: str, prefix: str = "") -> list[Item]:
    items = []
    if not base.is_dir():
        return items
    for entry in sorted(base.iterdir(), key=lambda p: p.name):
        skill = entry / "SKILL.md"
        if not skill.is_file():
            continue
        fm = frontmatter(_body(skill))
        name = prefix + (fm.get("name") or entry.name)
        items.append(Item("skill", name, fm.get("description", ""), skill, entry, origin))
    return items


def _command_items(base: Path, origin: str, prefix: str = "") -> list[Item]:
    items = []
    if not base.is_dir():
        return items
    for path in sorted(base.rglob("*.md")):
        rel = path.relative_to(base).with_suffix("")
        name = prefix + ":".join(rel.parts)
        fm = frontmatter(_body(path))
        items.append(Item("command", name, fm.get("description", ""), path, None, origin))
    return items


def _agent_items(base: Path, origin: str, prefix: str = "") -> list[Item]:
    items = []
    if not base.is_dir():
        return items
    for path in sorted(base.glob("*.md")):
        fm = frontmatter(_body(path))
        name = prefix + (fm.get("name") or path.stem)
        items.append(Item("agent", name, fm.get("description", ""), path, None, origin))
    return items


def discover(sb: Sandbox) -> list[Item]:
    items: list[Item] = []
    for origin, base in (("user", sb.home / ".claude"), ("project", sb.proj / ".claude")):
        items += _skill_items(base / "skills", origin)
        items += _command_items(base / "commands", origin)
        items += _agent_items(base / "agents", origin)
    for plugin in sb.plugin_dirs:
        manifest = plugin / ".claude-plugin" / "plugin.json"
        pname = json.loads(manifest.read_text(encoding="utf-8"))["name"] if manifest.is_file() else plugin.name
        origin = f"plugin:{pname}"
        items += _skill_items(plugin / "skills", origin, f"{pname}:")
        items += _command_items(plugin / "commands", origin, f"{pname}:")
        items += _agent_items(plugin / "agents", origin, f"{pname}:")
    for origin, path in (
        ("user", sb.home / ".claude" / "CLAUDE.md"),
        ("project", sb.proj / "CLAUDE.md"),
        ("project", sb.proj / ".claude" / "CLAUDE.md"),
        ("project", sb.proj / "CLAUDE.local.md"),
    ):
        if path.is_file():
            items.append(Item("memory", str(path.relative_to(sb.root)), "", path, None, origin))
    return items


def find(items: list[Item], ref: str) -> Item:
    """Resolve 'skill:name' / 'command:name' (plugin prefix optional)."""
    kind, _, name = ref.partition(":")
    pool = [i for i in items if i.kind == kind]
    hits = [i for i in pool if i.name == name] or [
        i for i in pool if i.origin.startswith("plugin:") and i.name.split(":", 1)[1] == name
    ]
    if len(hits) != 1:
        raise LookupError(f"{ref}: {len(hits)} matches among installed {kind}s")
    return hits[0]


def _settings_hooks(path: Path, origin: str, extra_env: dict) -> list[Hook]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    hooks = []
    for event, groups in sorted((data.get("hooks") or {}).items()):
        for group in groups:
            for h in group.get("hooks", []):
                if h.get("type", "command") != "command":
                    continue
                hooks.append(Hook("claude-code", event, group.get("matcher"), h["command"], origin, dict(extra_env)))
    return hooks


def claude_hooks(sb: Sandbox) -> list[Hook]:
    hooks: list[Hook] = []
    for origin, path in (
        ("home/.claude/settings.json", sb.home / ".claude" / "settings.json"),
        ("proj/.claude/settings.json", sb.proj / ".claude" / "settings.json"),
        ("proj/.claude/settings.local.json", sb.proj / ".claude" / "settings.local.json"),
    ):
        hooks += _settings_hooks(path, origin, {})
    for plugin in sb.plugin_dirs:
        hooks += _settings_hooks(plugin / "hooks" / "hooks.json", f"plugin:{plugin.name}/hooks/hooks.json",
                                 {"CLAUDE_PLUGIN_ROOT": str(plugin)})
    return hooks


def cursor_hooks(sb: Sandbox) -> list[Hook]:
    hooks: list[Hook] = []
    for origin, path in (("home/.cursor/hooks.json", sb.home / ".cursor" / "hooks.json"),
                         ("proj/.cursor/hooks.json", sb.proj / ".cursor" / "hooks.json")):
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for event, entries in sorted((data.get("hooks") or {}).items()):
            for h in entries:
                hooks.append(Hook("cursor", event, h.get("matcher"), h["command"], origin, {},
                                  bool(h.get("failClosed"))))
    return hooks


def matches(hook: Hook, tool_name: str | None) -> bool:
    if not hook.matcher or hook.matcher == "*" or tool_name is None:
        return True
    return re.fullmatch(hook.matcher, tool_name) is not None


_AT_REF = re.compile(r"(?<![\w`@])@((?:~|/|\.{1,2}/|[\w.-]+/)[^\s`)\]\"'<>,;]*)")


def expand_at_refs(text: str, sb: Sandbox, base: Path, depth: int = 0, seen: set | None = None) -> tuple[str, list[str]]:
    """Inline Claude Code @file references (recursive, each file once per expansion)."""
    seen = set() if seen is None else seen
    included: list[str] = []
    if depth > 5:
        return text, included
    parts = [text]
    for ref in _AT_REF.findall(text):
        ref = ref.rstrip(".:")
        if ref.startswith("~/"):
            cand = [sb.home / ref[2:]]
        elif ref.startswith("/"):
            cand = [Path(ref)]
        else:
            cand = [base / ref, sb.proj / ref]
        target = next((c for c in cand if c.is_file()), None)
        if target is None:
            continue
        key = str(target.resolve())
        if key in seen:
            continue
        seen.add(key)
        body = read_text(target)
        if body is None:
            continue
        rel = _logical(target, sb)
        included.append(rel)
        sub, sub_inc = expand_at_refs(body, sb, target.parent, depth + 1, seen)
        parts.append(sub)
        included += sub_inc
    return "\n".join(parts), included


def _logical(path: Path, sb: Sandbox) -> str:
    try:
        return "root/" + str(path.relative_to(sb.root))
    except ValueError:
        return str(path)


def package_text(item: Item, sb: Sandbox) -> list[tuple[str, str]]:
    """Every text file in a skill package (upper bound of what invoking it can pull in)."""
    if item.root is None:
        return [(_logical(item.path, sb), read_text(item.path) or "")]
    out = []
    for logical, real in iter_files(item.root, item.root.name):
        if real.suffix.lower() not in {".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".xml", ".csv"}:
            continue
        if {"tests", "test", "fixtures"} & set(logical.split("/")[1:-1]):
            continue
        text = read_text(real)
        if text is not None:
            out.append((logical, text))
    return out
