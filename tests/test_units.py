"""Unit tests for the deterministic pieces: tokenizer pin, parsing, classification, pricing."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from cbench import tokens
from cbench.context import Hook, frontmatter, matches
from cbench.hookrun import aggregate, classify
from cbench.usage import cost_usd, parse_transcript, price_key
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


TRANSCRIPT = "\n".join(json.dumps(e) for e in [
    {"type": "system", "subtype": "init"},
    {"type": "assistant", "message": {"id": "m1", "model": "claude-sonnet-5-5",
                                      "usage": {"input_tokens": 10, "cache_creation_input_tokens": 1000,
                                                "cache_read_input_tokens": 0, "output_tokens": 5},
                                      "content": [{"type": "tool_use", "name": "Skill"}]}},
    {"type": "assistant", "message": {"id": "m1", "model": "claude-sonnet-5-5",
                                      "usage": {"input_tokens": 10, "cache_creation_input_tokens": 1000,
                                                "cache_read_input_tokens": 0, "output_tokens": 5},
                                      "content": [{"type": "tool_use", "name": "Edit"}]}},
    {"type": "result", "subtype": "success", "num_turns": 1, "total_cost_usd": 0.01, "is_error": False,
     "modelUsage": {"claude-sonnet-5-5[1m]": {"inputTokens": 10, "outputTokens": 5,
                                              "cacheCreationInputTokens": 1000, "cacheReadInputTokens": 0}}},
])


def test_parse_transcript_prefers_model_usage():
    usage = parse_transcript(TRANSCRIPT)
    assert usage["totals"] == {"input_tokens": 10, "output_tokens": 5,
                               "cache_creation_input_tokens": 1000, "cache_read_input_tokens": 0}
    assert usage["first_request_input_tokens"] == 1010
    assert usage["tool_uses"] == {"Edit": 1, "Skill": 1}
    assert usage["reported_cost_usd"] == 0.01


def test_cost_matches_hand_calculation():
    usage = parse_transcript(TRANSCRIPT)
    # 10*2 + 5*10 + 1000*2.5 + 0*0.2 = 2570 per million
    assert cost_usd(usage["by_model"], PRICING) == "0.002570"
    assert price_key("claude-sonnet-5-5[1m]", PRICING) == "claude-sonnet-5-5"
    assert cost_usd({"some-other-model": usage["totals"]}, PRICING) is None
