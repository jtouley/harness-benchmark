"""Unit tests for the deterministic pieces: tokenizer pin, parsing, classification, pricing."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from pathlib import Path

from cbench import tokens
from cbench.context import Hook, frontmatter, matches
from cbench.hookrun import aggregate, classify
from cbench.install import Sandbox, _sort_manifest_files, canonicalize_host_text, normalizer
from cbench.lock import load_lock
from cbench.probes import _clean
from cbench.util import PRICING_PATH, canonical_json, load_json

PRICING = load_json(PRICING_PATH)


def test_tokenizer_is_pinned_and_stable():
    assert tokens.provenance()["sha256"] == tokens.TOKENIZER_SHA256
    assert tokens.count("") == 0
    first = tokens.count("Deterministic token counts for every framework.")
    assert first == tokens.count("Deterministic token counts for every framework.")
    assert first > 0


def test_canonical_json_is_order_independent():
    assert canonical_json({"b": 1, "a": Decimal("0.10")}) == canonical_json({"a": Decimal("0.10"), "b": 1})
    assert canonical_json({"a": Decimal("0.10")}) == '{\n  "a": "0.10"\n}\n'


@pytest.mark.parametrize(
    "text, expected",
    [
        ("---\nname: x\ndescription: plain words\n---\nbody", {"name": "x", "description": "plain words"}),
        ("---\nname: x\ndescription: \"quoted: colon\"\n---\n", {"name": "x", "description": "quoted: colon"}),
        ("---\ndescription: >-\n  folded\n  lines\nname: y\n---\n", {"description": "folded lines", "name": "y"}),
        ("---\ndescription: |\n  line one\n  line two\n---\n", {"description": "line one\n  line two"}),
        ("no front matter", {}),
    ],
)
def test_frontmatter(text, expected):
    assert frontmatter(text) == expected


def _hook(host="claude-code", fail_closed=False, matcher=None):
    return Hook(host, "PreToolUse", matcher, "true", "test", {}, fail_closed)


@pytest.mark.parametrize(
    "host, fail_closed, exit_code, stdout, expected",
    [
        ("claude-code", False, 2, "", ("block", "exit-2")),
        ("claude-code", False, 1, "", ("error", "exit-1")),
        ("claude-code", False, 0, json.dumps({"decision": "block"}), ("block", "decision-block")),
        ("claude-code", False, 0, json.dumps({"continue": False}), ("block", "continue-false")),
        ("claude-code", False, 0, json.dumps({"hookSpecificOutput": {"permissionDecision": "deny"}}), ("block", "permission-deny")),
        ("claude-code", False, 0, json.dumps({"hookSpecificOutput": {"additionalContext": "hi"}}), ("advise", "context")),
        ("claude-code", False, 0, "plain text", ("allow", "default")),
        ("cursor", False, 0, json.dumps({"permission": "deny"}), ("block", "permission-deny")),
        ("cursor", False, 0, json.dumps({"followup_message": "keep going"}), ("block", "followup-message")),
        ("cursor", True, 1, "", ("block", "fail-closed:exit")),
        ("cursor", False, 1, "", ("error", "exit-1")),
        ("cursor", True, 0, "not json", ("block", "fail-closed:invalid-json")),
        ("cursor", False, 0, json.dumps({"permission": "allow"}), ("allow", "default")),
    ],
)
def test_classify_rules(host, fail_closed, exit_code, stdout, expected):
    hook = _hook(host, fail_closed)
    assert classify(hook, {"exit": exit_code, "stdout": stdout, "stderr": ""}) == expected


def test_aggregate_precedence():
    assert aggregate([]) == "no_hook"
    assert aggregate(["allow", "advise"]) == "advise"
    assert aggregate(["allow", "block", "ask"]) == "block"


def test_matcher_is_full_regex():
    assert matches(_hook(matcher="Write|Edit"), "Write")
    assert not matches(_hook(matcher="Write|Edit"), "MultiEdit")
    assert matches(_hook(matcher=None), "Bash")


def test_normalize_hides_macos_tmp_realpath_and_baked_node_path():
    """Installed bytes must not depend on where /tmp resolves or where node lives.

    macOS realpath(/tmp) is /private/tmp. GSD also bakes process.execPath into
    hook commands. Both move footprint.json off the committed Linux result.
    """
    text = (
        "@/private/tmp/cbench/gsd-core/proj/.claude/gsd-core/references/x.md\n"
        '"$(for n in "/Users/a/.cache/cadence-bench/node-v22/bin/node" '
        '"$(command -v node)" /usr/local/bin/node /usr/bin/node; do true; done)"'
    )
    out = normalizer(load_lock())(text)
    assert "/private/tmp" not in out
    assert "/tmp/cbench/gsd-core/" in out
    assert "/Users/" not in out
    assert "/opt/node22/bin/node" in out


def test_probe_stderr_drops_bash_setlocale_warning():
    """Homebrew bash warns when LC_ALL=C.UTF-8 is unset on macOS. Verdicts ignore stderr."""
    sb = Sandbox(
        root=Path("/tmp/cbench/cadence"),
        home=Path("/tmp/cbench/cadence/home"),
        proj=Path("/tmp/cbench/cadence/proj"),
        src=None,
        plugin_dirs=(),
    )
    raw = "bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8): No such file or directory\n"
    assert _clean(raw, sb, 200) == ""


def test_canonicalize_rewrites_this_machines_cache_dir():
    """Plugin metadata stores the checkout under the bench cache. Home differs per host."""
    from cbench.util import cache_dir

    baked = f'{{"path": "{cache_dir()}/src/superpowers@abc"}}'
    out = canonicalize_host_text(baked)
    assert str(cache_dir()) not in out
    assert "<CACHE>/src/superpowers@abc" in out


def test_sort_manifest_files_is_independent_of_directory_order():
    raw = json.dumps(
        {"integration": "claude", "files": {"b.md": "2", "a.md": "1"}},
        indent=2,
    ) + "\n"
    once = _sort_manifest_files(raw)
    twice = _sort_manifest_files(once)
    assert once == twice
    assert list(json.loads(once)["files"]) == ["a.md", "b.md"]
