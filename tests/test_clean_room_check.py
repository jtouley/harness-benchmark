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

BUILTIN = sorted(crc.builtin_skills())


def _write(path: Path, *records: dict) -> Path:
    path.write_text("\n".join(json.dumps(r) for r in records) + ("\n" if records else ""), encoding="utf-8")
    return path


def _transcript(tmp_path: Path, *records: dict) -> Path:
    return _write(tmp_path / "t.jsonl", *records)


def _listing(*names: str) -> dict:
    return {"type": "attachment", "attachment": {"type": "skill_listing", "names": list(names)}}


def _call(name: str, **tool_input) -> dict:
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "name": name, "input": tool_input}]}}


def _user(text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": text}]}}


def _verdict(paths, allow=(), allow_paths=()):
    return crc.verdict(crc.scan(list(paths)), set(allow), list(allow_paths))


def test_only_built_in_skills_listed_and_no_contact_is_clean(tmp_path):
    t = _transcript(tmp_path, _listing(*BUILTIN), _user("Add budgets"), _call("Bash", command="pytest -q"))
    assert crc.main([str(t)]) == 0


def test_an_empty_transcript_is_unassessable(tmp_path):
    """R1 on PR #8: an empty transcript was graded clean."""
    t = _transcript(tmp_path)
    assert crc.main([str(t)]) == 3


def test_a_transcript_with_no_skill_listing_is_unassessable(tmp_path):
    t = _transcript(tmp_path, _call("Bash", command="pytest -q"))
    assert _verdict([t])["verdict"] == "unassessable"


def test_a_listing_of_other_skills_is_exposure(tmp_path):
    t = _transcript(tmp_path, _listing("spec-driven", "test-benchmark", *BUILTIN), _call("Bash", command="pytest -q"))
    result = _verdict([t])
    assert result["verdict"] == "exposed"
    assert result["unexpected_listed"] == ["spec-driven", "test-benchmark"]
    assert crc.main([str(t)]) == 1


def test_the_plain_text_listing_is_read_with_multi_line_descriptions(tmp_path):
    text = ("<system-reminder>\nThe following skills are available for use with the Skill tool:\n\n"
            "- spec-driven: Execute with strict TDD.\n  More text on a second line.\n"
            "- cadence: Gated pipeline.\n</system-reminder>")
    t = _transcript(tmp_path, _user(text))
    assert crc.scan([t])["listed"] == ["cadence", "spec-driven"]


def test_a_skill_call_outside_the_allowlist_is_contamination(tmp_path):
    t = _transcript(tmp_path, _listing("spec-driven"), _call("Skill", skill="spec-driven"))
    assert crc.main([str(t)]) == 2


@pytest.mark.parametrize("tool, tool_input", [
    ("Read", {"file_path": "/Users/x/.claude/skills/spec-driven/SKILL.md"}),
    ("Bash", {"command": "cat ~/.cursor/rules/001-core-tdd-protocol.mdc"}),
    ("Bash", {"command": "sed -n 1,40p /Users/x/.cursor/skills/ship-feature/SKILL.md"}),
    ("Read", {"file_path": "/repo/CLAUDE.md"}),
    ("Read", {"file_path": "/Users/x/.claude/plugins/cache/every/ce/skills/tdd/references/steps.md"}),
    ("Read", {"file_path": "/Users/x/.claude/projects/-Users-x-repo/memory/MEMORY.md"}),
    ("Grep", {"pattern": "TDD", "path": "/Users/x/.claude/skills"}),
])
def test_touching_a_skill_rule_plugin_or_memory_location_is_contamination(tmp_path, tool, tool_input):
    t = _transcript(tmp_path, _listing(*BUILTIN), _call(tool, **tool_input))
    assert _verdict([t])["verdict"] == "contaminated"


def test_text_that_a_tool_writes_is_not_a_contact(tmp_path):
    """R1 on PR #8: a Write whose content mentions .cursor/rules/ was counted as contamination."""
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Write", file_path="/repo/README.md",
                                                       content="Never read ~/.cursor/rules/ in this repo"))
    assert _verdict([t])["verdict"] == "clean"


def test_an_arm_may_list_call_and_read_its_own_harness(tmp_path):
    t = _transcript(tmp_path, _listing("cadence", *BUILTIN), _call("Skill", skill="cadence"),
                    _call("Read", file_path="/Users/x/Projects/cadence-wt/main-eval/SKILL.md"))
    assert _verdict([t], {"cadence"}, ["cadence-wt/main-eval"])["verdict"] == "clean"


def test_an_allowed_path_matches_whole_components_only(tmp_path):
    """R1 on PR #8: cadence-wt/main-eval also allowed cadence-wt/main-eval-old/."""
    t = _transcript(tmp_path, _listing("cadence", *BUILTIN),
                    _call("Read", file_path="/Users/x/Projects/cadence-wt/main-eval-old/skills/x/SKILL.md"))
    assert _verdict([t], {"cadence"}, ["cadence-wt/main-eval"])["verdict"] == "contaminated"


def test_a_plugin_prefixed_name_needs_its_own_allowlist_entry(tmp_path):
    """R1 on PR #8: any <plugin>:cadence passed an allowlist of cadence."""
    t = _transcript(tmp_path, _listing("other-plugin:cadence", *BUILTIN))
    assert _verdict([t], {"cadence"})["verdict"] == "exposed"
    assert _verdict([t], {"other-plugin:cadence"})["verdict"] == "clean"


def test_nested_agents_of_the_run_are_read(tmp_path):
    """cadence#53 happened in a nested peer: its transcript must be part of the run."""
    agents = tmp_path / "subagents"
    agents.mkdir()
    _write(agents / "agent-run.jsonl", _listing("cadence", *BUILTIN), _call("Agent", prompt="/test-benchmark 1"))
    (agents / "agent-run.meta.json").write_text(json.dumps({"spawnDepth": 1}))
    _write(agents / "agent-peer.jsonl", _listing("cadence", "test-benchmark", *BUILTIN),
           _call("Skill", skill="test-benchmark"))
    (agents / "agent-peer.meta.json").write_text(json.dumps({"parentAgentId": "run", "spawnDepth": 2}))
    _write(agents / "agent-other.jsonl", _call("Skill", skill="spec-driven"))
    (agents / "agent-other.meta.json").write_text(json.dumps({"spawnDepth": 1}))
    paths = crc.run_transcripts(agents, "run")
    assert sorted(p.name for p in paths) == ["agent-peer.jsonl", "agent-run.jsonl"]
    result = _verdict(paths, {"cadence"})
    assert result["verdict"] == "contaminated" and result["unexpected_calls"] == ["test-benchmark"]
    assert crc.main(["--agents-dir", str(agents), "--agent", "run", "--allow", "cadence"]) == 2


def test_direct_peers_of_a_top_level_session_are_read(tmp_path):
    """R1 re-review on PR #8: depth-1 agents have no parentAgentId; they live in <session>/subagents/."""
    session = _write(tmp_path / "S.jsonl", _listing(*BUILTIN), _call("Agent", prompt="/test-benchmark 1"))
    (tmp_path / "S" / "subagents").mkdir(parents=True)
    _write(tmp_path / "S" / "subagents" / "agent-p.jsonl", _listing("test-benchmark", *BUILTIN),
           _call("Skill", skill="test-benchmark"))
    assert crc.main([str(session)]) == 2


def test_calling_a_built_in_skill_needs_the_allowlist(tmp_path):
    """R1 re-review on PR #8: built-ins may be listed, but a call is use."""
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Skill", skill="code-review"))
    assert _verdict([t])["verdict"] == "contaminated"
    assert _verdict([t], {"code-review"})["verdict"] == "clean"


def test_a_listing_entry_without_a_description_and_a_three_part_name_are_read(tmp_path):
    text = ("<system-reminder>\nThe following skills are available for use with the Skill tool:\n\n"
            "- bare-skill\n- org:pack:tool: A three-part name.\n</system-reminder>")
    t = _transcript(tmp_path, _user(text))
    assert crc.scan([t])["listed"] == ["bare-skill", "org:pack:tool"]


def test_a_relative_path_resolves_against_the_run_cwd(tmp_path):
    """Pilot 2026-10-13: `cat README* CLAUDE.md` in the task repo is the repo's own file, not a user-level one."""
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Bash", command="cat README* CLAUDE.md"))
    assert _verdict([t])["verdict"] == "contaminated"
    found = crc.scan([t], cwd="/runs/a/repo")
    assert found["contacts"] == ["/runs/a/repo/CLAUDE.md"]
    assert crc.verdict(found, set(), ["/runs/a/repo"])["verdict"] == "clean"
    assert crc.main([str(t), "--cwd", "/runs/a/repo", "--allow-path", "/runs/a/repo"]) == 0


def test_a_home_path_does_not_resolve_against_the_cwd(tmp_path):
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Bash", command="cat ~/.claude/skills/x/SKILL.md"))
    found = crc.scan([t], cwd="/runs/a/repo")
    assert crc.verdict(found, set(), ["/runs/a/repo"])["verdict"] == "contaminated"


def test_a_grep_pattern_is_not_a_path(tmp_path):
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Grep", pattern="SKILL.md", path="/repo/src"))
    assert _verdict([t])["verdict"] == "clean"
