"""scripts/clean_room_check.py: a run is graded only when it saw and used only its own skills."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("clean_room_check", ROOT / "scripts" / "clean_room_check.py")
crc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(crc)


def _transcript(tmp_path: Path, *records: dict) -> Path:
    path = tmp_path / "t.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    return path


def _listing(*names: str) -> dict:
    return {"type": "attachment", "attachment": {"type": "skill_listing", "names": list(names)}}


def _call(name: str, **tool_input) -> dict:
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "name": name, "input": tool_input}]}}


def _user(text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": text}]}}


def test_a_run_with_no_listing_and_no_contact_is_clean(tmp_path):
    t = _transcript(tmp_path, _user("Add budgets"), _call("Bash", command="pytest -q"))
    assert crc.main([str(t)]) == 0


def test_a_listing_of_other_skills_is_exposure(tmp_path):
    t = _transcript(tmp_path, _listing("spec-driven", "test-benchmark"), _call("Bash", command="pytest -q"))
    result = crc.verdict(crc.scan(t), set(), [])
    assert result["verdict"] == "exposed"
    assert result["unexpected_listed"] == ["spec-driven", "test-benchmark"]
    assert crc.main([str(t)]) == 1


def test_the_plain_text_listing_is_read_too(tmp_path):
    text = "<system-reminder>\nThe following skills are available for use with the Skill tool:\n\n- spec-driven: Execute with strict TDD.\n- cadence: Gated pipeline.\n"
    t = _transcript(tmp_path, _user(text))
    assert crc.scan(t)["listed"] == ["cadence", "spec-driven"]


def test_a_skill_call_outside_the_allowlist_is_contamination(tmp_path):
    t = _transcript(tmp_path, _listing("spec-driven"), _call("Skill", skill="spec-driven"))
    assert crc.main([str(t)]) == 2


@pytest.mark.parametrize("tool_input", [
    {"file_path": "/Users/x/.claude/skills/spec-driven/SKILL.md"},
    {"command": "cat ~/.cursor/rules/001-core-tdd-protocol.mdc"},
    {"command": "sed -n 1,40p /Users/x/.cursor/skills/ship-feature/SKILL.md"},
    {"file_path": "/repo/CLAUDE.md"},
])
def test_reading_a_skill_rule_or_memory_file_is_contamination(tmp_path, tool_input):
    t = _transcript(tmp_path, _call("Read" if "file_path" in tool_input else "Bash", **tool_input))
    assert crc.verdict(crc.scan(t), set(), [])["verdict"] == "contaminated"


def test_an_arm_may_list_call_and_read_its_own_harness(tmp_path):
    t = _transcript(tmp_path, _listing("cadence"), _call("Skill", skill="cadence"),
                    _call("Read", file_path="/Users/x/Projects/cadence-wt/main-eval/SKILL.md"))
    result = crc.verdict(crc.scan(t), {"cadence"}, ["cadence-wt/main-eval/"])
    assert result["verdict"] == "clean"


def test_a_plugin_prefixed_name_matches_its_allowlisted_base(tmp_path):
    t = _transcript(tmp_path, _listing("cadence:pr-review-local"))
    assert crc.verdict(crc.scan(t), {"pr-review-local"}, [])["verdict"] == "clean"


def test_a_harness_arm_that_loads_a_user_level_peer_is_contamination(tmp_path):
    """cadence#53: a user-level skill with a peer's name ran in place of the harness's own peer."""
    t = _transcript(tmp_path, _listing("cadence", "test-benchmark"), _call("Skill", skill="test-benchmark"))
    result = crc.verdict(crc.scan(t), {"cadence"}, [])
    assert result["verdict"] == "contaminated" and result["unexpected_calls"] == ["test-benchmark"]
